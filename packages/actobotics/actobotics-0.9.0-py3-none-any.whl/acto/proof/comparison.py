from __future__ import annotations

from typing import Any

from acto.proof.models import ProofEnvelope


class ProofDiff:
    """Represents differences between two proofs."""

    def __init__(self, proof1_id: str, proof2_id: str):
        self.proof1_id = proof1_id
        self.proof2_id = proof2_id
        self.differences: list[dict[str, Any]] = []

    def add_difference(self, field: str, value1: Any, value2: Any, path: str = "") -> None:
        """Add a difference."""
        self.differences.append(
            {
                "field": field,
                "path": path,
                "value1": value1,
                "value2": value2,
            }
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to a dict."""
        return {
            "proof1_id": self.proof1_id,
            "proof2_id": self.proof2_id,
            "differences": self.differences,
            "total_differences": len(self.differences),
        }

    def is_identical(self) -> bool:
        """Check if the proofs are identical."""
        return len(self.differences) == 0


def compare_proofs(proof1: ProofEnvelope, proof2: ProofEnvelope) -> ProofDiff:
    """Compare two proofs and return differences."""
    diff = ProofDiff(
        proof1_id=proof1.payload.payload_hash[:16],
        proof2_id=proof2.payload.payload_hash[:16],
    )

    # Compare payload hashes
    if proof1.payload.payload_hash != proof2.payload.payload_hash:
        diff.add_difference("payload_hash", proof1.payload.payload_hash, proof2.payload.payload_hash)

    # Compare versions
    if proof1.payload.version != proof2.payload.version:
        diff.add_difference("version", proof1.payload.version, proof2.payload.version)

    # Compare subjects
    subj1 = proof1.payload.subject
    subj2 = proof2.payload.subject
    if subj1.task_id != subj2.task_id:
        diff.add_difference("subject.task_id", subj1.task_id, subj2.task_id)
    if subj1.robot_id != subj2.robot_id:
        diff.add_difference("subject.robot_id", subj1.robot_id, subj2.robot_id)
    if subj1.run_id != subj2.run_id:
        diff.add_difference("subject.run_id", subj1.run_id, subj2.run_id)

    # Compare timestamps
    if proof1.payload.created_at != proof2.payload.created_at:
        diff.add_difference("created_at", proof1.payload.created_at, proof2.payload.created_at)

    # Compare telemetry hashes
    if proof1.payload.telemetry_hash != proof2.payload.telemetry_hash:
        diff.add_difference("telemetry_hash", proof1.payload.telemetry_hash, proof2.payload.telemetry_hash)

    # Compare metadata
    _compare_dicts(proof1.payload.meta, proof2.payload.meta, "meta", diff)

    # Compare signatures
    if proof1.signature_b64 != proof2.signature_b64:
        diff.add_difference("signature", proof1.signature_b64[:32], proof2.signature_b64[:32])

    if proof1.signer_public_key_b64 != proof2.signer_public_key_b64:
        diff.add_difference("signer", proof1.signer_public_key_b64[:32], proof2.signer_public_key_b64[:32])

    # Compare anchor references
    if proof1.anchor_ref != proof2.anchor_ref:
        diff.add_difference("anchor_ref", proof1.anchor_ref, proof2.anchor_ref)

    return diff


def _compare_dicts(dict1: dict[str, Any], dict2: dict[str, Any], path: str, diff: ProofDiff) -> None:
    """Recursively compare dictionaries."""
    all_keys = set(dict1.keys()) | set(dict2.keys())
    for key in all_keys:
        current_path = f"{path}.{key}" if path else key
        val1 = dict1.get(key)
        val2 = dict2.get(key)

        if key not in dict1:
            diff.add_difference(key, None, val2, current_path)
        elif key not in dict2:
            diff.add_difference(key, val1, None, current_path)
        elif isinstance(val1, dict) and isinstance(val2, dict):
            _compare_dicts(val1, val2, current_path, diff)
        elif val1 != val2:
            diff.add_difference(key, val1, val2, current_path)

