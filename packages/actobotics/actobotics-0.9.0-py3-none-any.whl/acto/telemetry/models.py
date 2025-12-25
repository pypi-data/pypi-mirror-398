from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class TelemetryEvent(BaseModel):
    ts: str = Field(..., description="ISO timestamp")
    topic: str = Field(..., description="Source channel/topic name")
    data: dict[str, Any] = Field(default_factory=dict, description="Event payload")


class TelemetryBundle(BaseModel):
    task_id: str
    robot_id: str | None = None
    run_id: str | None = None
    events: list[TelemetryEvent] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)
