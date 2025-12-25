from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from acto.crypto import load_keypair
from acto.proof import ProofEnvelope, create_proof, verify_proof
from acto.registry import ProofRegistry
from acto.telemetry import CsvTelemetryParser, JsonlTelemetryParser
from acto.telemetry.models import TelemetryBundle


def _select_parser(source: str):
    p = Path(source)
    if p.suffix.lower() == ".jsonl":
        return JsonlTelemetryParser()
    if p.suffix.lower() == ".csv":
        return CsvTelemetryParser()
    raise ValueError("Unsupported telemetry file type. Use .jsonl or .csv")


@dataclass
class TelemetryLoadStep:
    name: str = "telemetry.load"

    def run(self, ctx: dict[str, Any]) -> dict[str, Any]:
        parser = _select_parser(str(ctx["source"]))
        bundle = parser.parse(
            str(ctx["source"]),
            task_id=str(ctx["task_id"]),
            robot_id=ctx.get("robot_id"),
            run_id=ctx.get("run_id"),
        )
        ctx["bundle"] = bundle
        return ctx


@dataclass
class TelemetryNormalizeStep:
    name: str = "telemetry.normalize"

    def run(self, ctx: dict[str, Any]) -> dict[str, Any]:
        bundle: TelemetryBundle = ctx["bundle"]
        ctx["events_count"] = len(bundle.events)
        return ctx


@dataclass
class ProofCreateStep:
    name: str = "proof.create"

    def run(self, ctx: dict[str, Any]) -> dict[str, Any]:
        kp = load_keypair(str(ctx.get("keypair", "data/keys/acto_keypair.json")))
        bundle: TelemetryBundle = ctx["bundle"]
        env = create_proof(bundle, kp.private_key_b64, kp.public_key_b64, meta=ctx.get("meta"))
        ctx["envelope"] = env
        return ctx


@dataclass
class ProofVerifyStep:
    name: str = "proof.verify"

    def run(self, ctx: dict[str, Any]) -> dict[str, Any]:
        env: ProofEnvelope = ctx["envelope"]
        verify_proof(env)
        ctx["verified"] = True
        return ctx


@dataclass
class RegistryUpsertStep:
    name: str = "registry.upsert"

    def run(self, ctx: dict[str, Any]) -> dict[str, Any]:
        reg = ProofRegistry()
        env: ProofEnvelope = ctx["envelope"]
        ctx["proof_id"] = reg.upsert(env)
        return ctx
