from __future__ import annotations

from typing import Any

from acto.proof.models import ProofEnvelope
from acto.telemetry.models import TelemetryBundle, TelemetryEvent


def merge_proofs(
    proofs: list[ProofEnvelope],
    signer_private_key_b64: str,
    signer_public_key_b64: str,
    merged_task_id: str | None = None,
    meta: dict[str, Any] | None = None,
) -> ProofEnvelope:
    """Merge multiple proofs into a single proof."""
    from acto.proof.engine import create_proof

    if not proofs:
        raise ValueError("Cannot merge empty list of proofs")

    # Collect all events from all proofs
    all_events: list[TelemetryEvent] = []
    source_proofs: list[str] = []

    for proof in proofs:
        # Extract events from normalized telemetry
        telemetry_norm = proof.payload.telemetry_normalized
        if "events" in telemetry_norm:
            for event_dict in telemetry_norm["events"]:
                all_events.append(
                    TelemetryEvent(
                        ts=event_dict.get("ts", ""),
                        topic=event_dict.get("topic", ""),
                        data=event_dict.get("data", {}),
                    )
                )
        source_proofs.append(proof.payload.payload_hash)

    # Sort events by timestamp
    all_events.sort(key=lambda e: e.ts)

    # Create merged bundle
    first_proof = proofs[0]
    merged_bundle = TelemetryBundle(
        task_id=merged_task_id or f"merged-{first_proof.payload.subject.task_id}",
        robot_id=first_proof.payload.subject.robot_id,
        run_id=first_proof.payload.subject.run_id,
        events=all_events,
        meta={"merged": True, "source_proofs": source_proofs, "source_count": len(proofs)},
    )

    # Add meta information
    merged_meta = meta or {}
    merged_meta["merged"] = True
    merged_meta["source_proofs"] = source_proofs
    merged_meta["source_count"] = len(proofs)
    merged_meta["event_count"] = len(all_events)

    return create_proof(merged_bundle, signer_private_key_b64, signer_public_key_b64, meta=merged_meta)


def merge_proofs_by_task(
    proofs: list[ProofEnvelope],
    signer_private_key_b64: str,
    signer_public_key_b64: str,
    meta: dict[str, Any] | None = None,
) -> dict[str, ProofEnvelope]:
    """Merge proofs grouped by task ID."""
    from collections import defaultdict

    grouped: dict[str, list[ProofEnvelope]] = defaultdict(list)
    for proof in proofs:
        task_id = proof.payload.subject.task_id
        grouped[task_id].append(proof)

    merged: dict[str, ProofEnvelope] = {}
    for task_id, task_proofs in grouped.items():
        merged[task_id] = merge_proofs(
            task_proofs, signer_private_key_b64, signer_public_key_b64, merged_task_id=task_id, meta=meta
        )

    return merged

