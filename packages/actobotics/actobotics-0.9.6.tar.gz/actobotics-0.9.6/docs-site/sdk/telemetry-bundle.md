# TelemetryBundle

The `TelemetryBundle` model represents telemetry data for proof creation.

## Definition

```python
from acto.telemetry.models import TelemetryBundle, TelemetryEvent

bundle = TelemetryBundle(
    task_id="pick-and-place-001",      # Required
    robot_id="robot-alpha-01",          # Optional
    run_id="run-2025-01-15",            # Optional
    events=[...],                       # Required
    meta={}                             # Optional
)
```

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `task_id` | `str` | Yes | Unique task identifier |
| `robot_id` | `str` | No | Robot/device identifier |
| `run_id` | `str` | No | Specific execution run |
| `events` | `list[TelemetryEvent]` | Yes | Telemetry events |
| `meta` | `dict` | No | Arbitrary metadata |

## TelemetryEvent

```python
event = TelemetryEvent(
    ts="2025-01-15T10:30:00Z",      # ISO 8601 timestamp
    topic="sensor/temperature",      # Event topic
    data={"value": 42.5}            # Event payload
)
```

## Creating Bundles

### From Events

```python
events = [
    TelemetryEvent(ts="2025-01-15T10:30:00Z", topic="start", data={"task": "pick"}),
    TelemetryEvent(ts="2025-01-15T10:30:01Z", topic="sensor", data={"value": 42}),
    TelemetryEvent(ts="2025-01-15T10:30:02Z", topic="end", data={"status": "ok"}),
]

bundle = TelemetryBundle(
    task_id="task-001",
    robot_id="robot-001",
    events=events
)
```

### From JSONL File

```python
from acto.telemetry.parsers import parse_jsonl

events = parse_jsonl("telemetry.jsonl")
bundle = TelemetryBundle(
    task_id="task-001",
    events=events
)
```

## With Metadata

```python
bundle = TelemetryBundle(
    task_id="inspection-001",
    robot_id="inspector-01",
    events=events,
    meta={
        "operator": "John Doe",
        "location": "Warehouse A",
        "batch": "B-2025-001"
    }
)
```

## Validation

The bundle is validated when used with `create_proof()`:

- `task_id` must be non-empty
- `events` must have at least one event
- Each event must have valid `ts`, `topic`, and `data`

