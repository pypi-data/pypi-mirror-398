from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ProofSubject(BaseModel):
    task_id: str
    robot_id: str | None = None
    run_id: str | None = None


class ProofPayload(BaseModel):
    version: str = Field(..., description="Proof version")
    subject: ProofSubject
    created_at: str
    telemetry_normalized: dict[str, Any]
    telemetry_hash: str
    payload_hash: str
    hash_alg: str
    signature_alg: str
    meta: dict[str, Any] = Field(default_factory=dict)


class ProofEnvelope(BaseModel):
    payload: ProofPayload
    signer_public_key_b64: str
    signature_b64: str
    anchor_ref: str | None = None
