# Telemetry Format

ACTO uses a standardized telemetry format for proof creation.

## TelemetryBundle

A bundle contains task metadata and a list of events:

```python
from acto.telemetry.models import TelemetryBundle, TelemetryEvent

bundle = TelemetryBundle(
    task_id="pick-and-place-001",      # Required
    robot_id="robot-alpha-01",          # Optional, enables fleet tracking
    run_id="run-2025-01-15-001",        # Optional, identifies specific run
    events=[...],                       # Required, list of events
    meta={}                             # Optional metadata
)
```

## TelemetryEvent

Each event represents a single data point:

```python
event = TelemetryEvent(
    ts="2025-01-15T10:30:00.123Z",      # ISO 8601 timestamp
    topic="sensor/temperature",          # Topic/category
    data={"value": 42.5, "unit": "C"}   # Arbitrary JSON data
)
```

### Field Details

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `ts` | string | Yes | ISO 8601 timestamp |
| `topic` | string | Yes | Event category/source |
| `data` | dict | Yes | Event payload |

## Timestamp Format

Use ISO 8601 format:

```python
# Valid formats
"2025-01-15T10:30:00Z"           # UTC
"2025-01-15T10:30:00.123Z"       # With milliseconds
"2025-01-15T10:30:00+00:00"      # With timezone

# Convert from Python datetime
from datetime import datetime, timezone
dt = datetime.now(timezone.utc)
ts = dt.isoformat()
```

## Topics

Topics categorize events. Use descriptive, hierarchical names:

```python
# Good topics
"sensor/temperature"
"motor/velocity"
"gripper/force"
"navigation/position"
"task/started"
"task/completed"

# Avoid
"data"           # Too generic
"temp"           # Abbreviated
"sensor_temp_1"  # Inconsistent format
```

## Data Payload

The `data` field accepts any JSON-serializable object:

```python
# Simple value
data = {"value": 42}

# Nested object
data = {
    "position": {"x": 0.5, "y": 0.3, "z": 0.2},
    "velocity": {"x": 0.1, "y": 0.0, "z": -0.05}
}

# Array
data = {"joint_angles": [0.0, 1.57, -0.78, 0.0, 0.0, 0.0]}

# Mixed
data = {
    "status": "ok",
    "temperature": 42.5,
    "errors": [],
    "metadata": {"source": "sensor_001"}
}
```

## File Formats

### JSONL (Recommended)

One event per line:

```jsonl
{"ts": "2025-01-15T10:30:00Z", "topic": "sensor", "data": {"value": 42}}
{"ts": "2025-01-15T10:30:01Z", "topic": "motor", "data": {"rpm": 1500}}
{"ts": "2025-01-15T10:30:02Z", "topic": "sensor", "data": {"value": 43}}
```

Parse with:

```python
from acto.telemetry.parsers import parse_jsonl

events = parse_jsonl("telemetry.jsonl")
```

### JSON Array

```json
[
  {"ts": "2025-01-15T10:30:00Z", "topic": "sensor", "data": {"value": 42}},
  {"ts": "2025-01-15T10:30:01Z", "topic": "motor", "data": {"rpm": 1500}}
]
```

## Normalization

Before hashing, telemetry is normalized:

1. **Sort events** by timestamp
2. **Canonicalize JSON** - Consistent key ordering
3. **Remove whitespace** - Deterministic output

This ensures identical input always produces identical hash.

## Example: Complete Telemetry

```python
from acto.telemetry.models import TelemetryBundle, TelemetryEvent
from datetime import datetime, timezone

def record_task_telemetry():
    events = []
    
    # Task start
    events.append(TelemetryEvent(
        ts=datetime.now(timezone.utc).isoformat(),
        topic="task/started",
        data={"task_type": "pick-and-place", "target": "widget-A"}
    ))
    
    # Sensor readings
    events.append(TelemetryEvent(
        ts=datetime.now(timezone.utc).isoformat(),
        topic="sensor/position",
        data={"x": 0.5, "y": 0.3, "z": 0.2}
    ))
    
    # Motor data
    events.append(TelemetryEvent(
        ts=datetime.now(timezone.utc).isoformat(),
        topic="motor/gripper",
        data={"action": "close", "force": 12.5}
    ))
    
    # Task complete
    events.append(TelemetryEvent(
        ts=datetime.now(timezone.utc).isoformat(),
        topic="task/completed",
        data={"status": "success", "duration_ms": 5230}
    ))
    
    return TelemetryBundle(
        task_id="pick-and-place-001",
        robot_id="robot-alpha-01",
        run_id=f"run-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        events=events
    )
```

## Best Practices

1. **Use UTC timestamps** - Avoid timezone confusion
2. **Include milliseconds** - For precise ordering
3. **Consistent topics** - Use a naming convention
4. **Reasonable granularity** - Don't over-log
5. **Meaningful data** - Include context

