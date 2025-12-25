from __future__ import annotations

from acto.errors import ProofError
from acto.proof.models import ProofEnvelope, ProofPayload


class ProofVersionMigrator:
    """Migrates proofs between different versions."""

    def __init__(self):
        self.migrators: dict[str, dict[str, callable]] = {
            "1": {"2": self._migrate_v1_to_v2},
            "2": {"3": self._migrate_v2_to_v3},
        }

    def migrate(self, proof: ProofEnvelope, target_version: str) -> ProofEnvelope:
        """Migrate a proof to a target version."""
        current_version = proof.payload.version

        if current_version == target_version:
            return proof

        if current_version not in self.migrators:
            raise ProofError(f"Unknown source version: {current_version}")

        if target_version not in self.migrators[current_version]:
            raise ProofError(f"Cannot migrate from version {current_version} to {target_version}")

        migrator = self.migrators[current_version][target_version]
        return migrator(proof)

    def _migrate_v1_to_v2(self, proof: ProofEnvelope) -> ProofEnvelope:
        """Migrate from version 1 to version 2."""
        # Example: Add new fields or change structure
        payload_dict = proof.payload.model_dump()
        payload_dict["version"] = "2"

        # Add migration metadata
        if "meta" not in payload_dict:
            payload_dict["meta"] = {}
        payload_dict["meta"]["migrated_from"] = "1"
        payload_dict["meta"]["migrated_at"] = self._now_iso()

        # Create new payload
        new_payload = ProofPayload(**payload_dict)

        # IMPORTANT: The payload hash must be recalculated
        # Since the payload has changed, the signature must also be recreated
        # In a real implementation, one would create a new signature here
        # For now, we return a warning
        return ProofEnvelope(
            payload=new_payload,
            signer_public_key_b64=proof.signer_public_key_b64,
            signature_b64=proof.signature_b64,  # Old signature - should be recreated
            anchor_ref=proof.anchor_ref,
        )

    def _migrate_v2_to_v3(self, proof: ProofEnvelope) -> ProofEnvelope:
        """Migrate from version 2 to version 3."""
        payload_dict = proof.payload.model_dump()
        payload_dict["version"] = "3"

        if "meta" not in payload_dict:
            payload_dict["meta"] = {}
        payload_dict["meta"]["migrated_from"] = "2"
        payload_dict["meta"]["migrated_at"] = self._now_iso()

        new_payload = ProofPayload(**payload_dict)

        return ProofEnvelope(
            payload=new_payload,
            signer_public_key_b64=proof.signer_public_key_b64,
            signature_b64=proof.signature_b64,
            anchor_ref=proof.anchor_ref,
        )

    def _now_iso(self) -> str:
        """Return current ISO timestamp."""
        from acto.utils.time import now_utc_iso

        return now_utc_iso()


def get_proof_version(proof: ProofEnvelope) -> str:
    """Return the version of a proof."""
    return proof.payload.version


def is_version_compatible(proof: ProofEnvelope, required_version: str) -> bool:
    """Check if a proof is compatible with a required version."""
    current_version = proof.payload.version
    # Simple implementation: exact match
    # In a full implementation, one would use SemVer
    return current_version == required_version


def migrate_proof_to_latest(proof: ProofEnvelope) -> ProofEnvelope:
    """Migrate a proof to the latest version."""
    migrator = ProofVersionMigrator()
    latest_version = "3"  # Current latest version
    return migrator.migrate(proof, latest_version)

