from __future__ import annotations

import json
from typing import Any

import orjson

from acto.telemetry.models import TelemetryBundle, TelemetryEvent


def _stable_json(obj: Any) -> bytes:
    return orjson.dumps(obj, option=orjson.OPT_SORT_KEYS)


def normalize_event(event: TelemetryEvent) -> dict[str, Any]:
    return {"ts": event.ts, "topic": event.topic, "data": json.loads(_stable_json(event.data))}


def normalize_bundle(bundle: TelemetryBundle) -> dict[str, Any]:
    return {
        "task_id": bundle.task_id,
        "robot_id": bundle.robot_id,
        "run_id": bundle.run_id,
        "meta": json.loads(_stable_json(bundle.meta)),
        "events": [normalize_event(e) for e in bundle.events],
    }
