from __future__ import annotations

from typing import Any

import orjson

from acto.config.settings import Settings
from acto.crypto.hashing import blake3_hash, sha256_hash
from acto.crypto.signing import sign_bytes, verify_bytes
from acto.errors import ProofError
from acto.proof.models import ProofEnvelope, ProofPayload, ProofSubject
from acto.telemetry.models import TelemetryBundle
from acto.telemetry.normalizer import normalize_bundle
from acto.utils.time import now_utc_iso


def _hash_bytes(alg: str, data: bytes) -> str:
    if alg == "blake3":
        return blake3_hash(data)
    if alg == "sha256":
        return sha256_hash(data)
    raise ProofError(f"Unsupported hash algorithm: {alg}")


def compute_payload_hash(payload_dict: dict[str, Any], alg: str) -> str:
    canonical = orjson.dumps(payload_dict, option=orjson.OPT_SORT_KEYS)
    return _hash_bytes(alg, canonical)


def create_proof(
    bundle: TelemetryBundle,
    signer_private_key_b64: str,
    signer_public_key_b64: str,
    settings: Settings | None = None,
    meta: dict[str, Any] | None = None,
) -> ProofEnvelope:
    """
    Create a signed proof envelope from telemetry bundle.

    Args:
        bundle: Telemetry bundle containing task and telemetry data
        signer_private_key_b64: Base64-encoded Ed25519 private key for signing
        signer_public_key_b64: Base64-encoded Ed25519 public key
        settings: Optional settings override (defaults to global Settings)
        meta: Optional metadata dictionary to include in proof

    Returns:
        ProofEnvelope: Signed proof envelope

    Raises:
        ProofError: If proof creation fails

    Example:
        ```python
        from acto.proof import create_proof
        from acto.telemetry.models import TelemetryBundle
        from acto.crypto import load_keypair

        # Load keypair
        kp = load_keypair("data/keys/acto_keypair.json")

        # Create telemetry bundle
        bundle = TelemetryBundle(
            task_id="cleaning-run-001",
            robot_id="robot-001",
            telemetry=[...]
        )

        # Create proof
        envelope = create_proof(
            bundle,
            kp.private_key_b64,
            kp.public_key_b64
        )
        ```
    """
    settings = settings or Settings()
    meta = meta or {}

    subject = ProofSubject(task_id=bundle.task_id, robot_id=bundle.robot_id, run_id=bundle.run_id)
    telemetry_norm = normalize_bundle(bundle)
    telemetry_bytes = orjson.dumps(telemetry_norm, option=orjson.OPT_SORT_KEYS)
    telemetry_hash = _hash_bytes(settings.proof_hash_alg, telemetry_bytes)

    payload_base: dict[str, Any] = {
        "version": settings.proof_version,
        "subject": subject.model_dump(),
        "created_at": now_utc_iso(),
        "telemetry_normalized": telemetry_norm,
        "telemetry_hash": telemetry_hash,
        "hash_alg": settings.proof_hash_alg,
        "signature_alg": settings.proof_signature_alg,
        "meta": meta,
    }
    payload_hash = compute_payload_hash(payload_base, settings.proof_hash_alg)

    payload = ProofPayload(
        version=settings.proof_version,
        subject=subject,
        created_at=payload_base["created_at"],
        telemetry_normalized=telemetry_norm,
        telemetry_hash=telemetry_hash,
        payload_hash=payload_hash,
        hash_alg=settings.proof_hash_alg,
        signature_alg=settings.proof_signature_alg,
        meta=meta,
    )

    signature = sign_bytes(signer_private_key_b64, payload_hash.encode("utf-8"))
    return ProofEnvelope(
        payload=payload,
        signer_public_key_b64=signer_public_key_b64,
        signature_b64=signature,
        anchor_ref=None,
    )


def _verify_proof_internal(envelope: ProofEnvelope) -> bool:
    """
    Internal proof verification - used by the server only.
    
    This function is NOT exported in the public API.
    SDK users must use ACTOClient.verify() instead.
    """
    payload = envelope.payload
    payload_base = {
        "version": payload.version,
        "subject": payload.subject.model_dump(),
        "created_at": payload.created_at,
        "telemetry_normalized": payload.telemetry_normalized,
        "telemetry_hash": payload.telemetry_hash,
        "hash_alg": payload.hash_alg,
        "signature_alg": payload.signature_alg,
        "meta": payload.meta,
    }
    recomputed = compute_payload_hash(payload_base, payload.hash_alg)
    if recomputed != payload.payload_hash:
        raise ProofError("Payload hash mismatch. Proof is tampered or inconsistent.")

    ok = verify_bytes(
        envelope.signer_public_key_b64, payload.payload_hash.encode("utf-8"), envelope.signature_b64
    )
    if not ok:
        raise ProofError("Invalid signature.")
    return True


def verify_proof(envelope: ProofEnvelope) -> bool:
    """
    Verify a proof envelope via the ACTO API.

    .. deprecated::
        Local verification has been removed for SDK users. All proof verification must
        be done through the ACTO API to ensure integrity and compliance.

    Args:
        envelope: Proof envelope to verify

    Raises:
        ProofError: Always raises - use ACTOClient.verify() instead

    Example:
        ```python
        from acto.client import ACTOClient

        client = ACTOClient(
            api_key="your-api-key",
            wallet_address="your-wallet-address"
        )

        # Verify proof via API
        result = client.verify(envelope)
        print(f"Proof valid: {result.valid}")
        ```
    """
    raise ProofError(
        "Local verification has been removed. "
        "Please use the ACTO API for verification:\n\n"
        "  from acto.client import ACTOClient\n"
        "  client = ACTOClient(api_key='...', wallet_address='...')\n"
        "  result = client.verify(envelope)\n\n"
        "Get your API key at: https://api.actobotics.net/dashboard"
    )
