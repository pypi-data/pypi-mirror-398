from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from acto.logging import get_logger

log = get_logger("acto.pipeline")


class PipelineStep(Protocol):
    name: str

    def run(self, ctx: dict[str, Any]) -> dict[str, Any]:
        ...


@dataclass
class PipelineResult:
    ctx: dict[str, Any]
    steps: list[str]


class ProofPipeline:
    def __init__(self, steps: list[PipelineStep]):
        self.steps = steps

    def run(self, ctx: dict[str, Any]) -> PipelineResult:
        executed: list[str] = []
        for step in self.steps:
            log.debug("Running step=%s", step.name)
            ctx = step.run(ctx)
            executed.append(step.name)
        return PipelineResult(ctx=ctx, steps=executed)
