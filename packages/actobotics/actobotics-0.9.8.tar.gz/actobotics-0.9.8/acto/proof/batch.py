from __future__ import annotations

from typing import Any

from acto.proof.models import ProofEnvelope
from acto.telemetry.models import TelemetryBundle


def create_batch_proofs(
    bundles: list[TelemetryBundle],
    signer_private_key_b64: str,
    signer_public_key_b64: str,
    meta: dict[str, Any] | None = None,
) -> list[ProofEnvelope]:
    """Create multiple proofs in a batch."""
    from acto.proof.engine import create_proof

    proofs: list[ProofEnvelope] = []
    batch_meta = meta or {}
    batch_meta["batch_size"] = len(bundles)
    batch_meta["batch_index"] = 0

    for idx, bundle in enumerate(bundles):
        bundle_meta = batch_meta.copy()
        bundle_meta["batch_index"] = idx
        proof = create_proof(bundle, signer_private_key_b64, signer_public_key_b64, meta=bundle_meta)
        proofs.append(proof)

    return proofs


def create_batch_proof_with_links(
    bundles: list[TelemetryBundle],
    signer_private_key_b64: str,
    signer_public_key_b64: str,
    meta: dict[str, Any] | None = None,
) -> tuple[list[ProofEnvelope], ProofEnvelope]:
    """Create a batch proof with links to all individual proofs."""
    from acto.proof.engine import create_proof

    # Create all individual proofs
    individual_proofs = create_batch_proofs(bundles, signer_private_key_b64, signer_public_key_b64, meta)

    # Create a combined bundle for the batch proof
    all_events: list[Any] = []
    for bundle in bundles:
        all_events.extend(bundle.events)

    combined_bundle = TelemetryBundle(
        task_id=f"batch-{bundles[0].task_id}",
        robot_id=bundles[0].robot_id if bundles else None,
        run_id=bundles[0].run_id if bundles else None,
        events=all_events,
        meta={"batch": True, "individual_count": len(bundles)},
    )

    # Create batch proof with links to individual proofs
    batch_meta = meta or {}
    batch_meta["individual_proofs"] = [p.payload.payload_hash for p in individual_proofs]
    batch_meta["batch_size"] = len(bundles)

    batch_proof = create_proof(combined_bundle, signer_private_key_b64, signer_public_key_b64, meta=batch_meta)

    return individual_proofs, batch_proof

