# Creating Proofs

Learn how to create execution proofs from robot telemetry.

## Basic Proof Creation

```python
from acto.proof import create_proof
from acto.telemetry.models import TelemetryBundle, TelemetryEvent
from acto.crypto import KeyPair

# 1. Generate or load a keypair
keypair = KeyPair.generate()

# 2. Create a telemetry bundle
bundle = TelemetryBundle(
    task_id="pick-and-place-001",
    robot_id="robot-alpha-01",
    events=[
        TelemetryEvent(
            ts="2025-01-15T10:30:00Z",
            topic="gripper",
            data={"action": "close", "force": 12.5}
        ),
        TelemetryEvent(
            ts="2025-01-15T10:30:01Z",
            topic="sensor",
            data={"temperature": 42.5}
        ),
    ]
)

# 3. Create the proof
envelope = create_proof(
    bundle,
    keypair.private_key_b64,
    keypair.public_key_b64
)

print(f"Created proof with hash: {envelope.payload.payload_hash}")
```

## Function Signature

```python
def create_proof(
    bundle: TelemetryBundle,
    private_key_b64: str,
    public_key_b64: str,
    *,
    meta: dict | None = None,
    anchor_ref: str | None = None,
) -> ProofEnvelope:
    ...
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `bundle` | `TelemetryBundle` | Yes | Telemetry data |
| `private_key_b64` | `str` | Yes | Base64-encoded private key |
| `public_key_b64` | `str` | Yes | Base64-encoded public key |
| `meta` | `dict` | No | Additional metadata |
| `anchor_ref` | `str` | No | Solana anchor reference |

### Returns

`ProofEnvelope` - The signed proof envelope

## What Happens Internally

When you call `create_proof()`, the SDK:

1. **Normalizes telemetry** - Sorts events, canonicalizes JSON
2. **Computes telemetry hash** - BLAKE3 hash of normalized telemetry
3. **Creates payload** - Assembles the proof payload
4. **Computes payload hash** - BLAKE3 hash of the payload
5. **Signs the hash** - Ed25519 signature over payload_hash
6. **Returns envelope** - Complete proof envelope

```
TelemetryBundle
      │
      ▼
┌─────────────────┐
│   Normalize     │ ─── Sort events, canonicalize JSON
└─────────────────┘
      │
      ▼
┌─────────────────┐
│  Hash (BLAKE3)  │ ─── telemetry_hash
└─────────────────┘
      │
      ▼
┌─────────────────┐
│ Create Payload  │ ─── version, subject, timestamps, hashes
└─────────────────┘
      │
      ▼
┌─────────────────┐
│  Hash (BLAKE3)  │ ─── payload_hash
└─────────────────┘
      │
      ▼
┌─────────────────┐
│ Sign (Ed25519)  │ ─── signature_b64
└─────────────────┘
      │
      ▼
ProofEnvelope
```

## Adding Metadata

Include arbitrary metadata in your proof:

```python
envelope = create_proof(
    bundle,
    keypair.private_key_b64,
    keypair.public_key_b64,
    meta={
        "operator": "John Doe",
        "location": "Warehouse A",
        "batch_number": "B-2025-001",
        "environment": {
            "temperature": 22.5,
            "humidity": 45.0
        }
    }
)
```

## From Telemetry Files

Create proofs from JSONL telemetry files:

```python
from acto.telemetry.parsers import parse_jsonl

# Parse telemetry file
events = parse_jsonl("telemetry.jsonl")

# Create bundle
bundle = TelemetryBundle(
    task_id="inspection-001",
    robot_id="inspector-01",
    events=events
)

# Create proof
envelope = create_proof(bundle, keypair.private_key_b64, keypair.public_key_b64)
```

### JSONL Format

```jsonl
{"ts": "2025-01-15T10:30:00Z", "topic": "sensor", "data": {"value": 42}}
{"ts": "2025-01-15T10:30:01Z", "topic": "motor", "data": {"rpm": 1500}}
{"ts": "2025-01-15T10:30:02Z", "topic": "sensor", "data": {"value": 43}}
```

## Batch Proof Creation

Create multiple proofs efficiently:

```python
proofs = []
for task_data in tasks:
    bundle = TelemetryBundle(
        task_id=task_data["id"],
        robot_id=task_data["robot"],
        events=task_data["events"]
    )
    envelope = create_proof(bundle, keypair.private_key_b64, keypair.public_key_b64)
    proofs.append(envelope)

# Batch verify
results = client.verify_batch(proofs)
print(f"Valid: {results.valid_count}/{results.total}")
```

## Saving and Loading Proofs

### Save to JSON

```python
import json

# Save
with open("proof.json", "w") as f:
    json.dump(envelope.model_dump(), f, indent=2)

# Load
from acto.proof.models import ProofEnvelope

with open("proof.json") as f:
    data = json.load(f)
    envelope = ProofEnvelope.model_validate(data)
```

### Save to File (CLI)

```bash
acto proof create \
  --task-id "task-001" \
  --source telemetry.jsonl \
  --output proof.json
```

## Best Practices

### Use Consistent Task IDs

```python
# Good - descriptive and consistent
task_id = "pick-and-place-widget-assembly"
task_id = "quality-inspection-batch-001"

# Bad - ambiguous
task_id = "task1"
task_id = "test"
```

### Include Robot IDs for Fleet Tracking

```python
bundle = TelemetryBundle(
    task_id="inspection-001",
    robot_id="robot-warehouse-a-01",  # Enables fleet tracking
    events=[...]
)
```

### Use Run IDs for Repeated Tasks

```python
from datetime import datetime

run_id = f"run-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

bundle = TelemetryBundle(
    task_id="daily-inspection",
    robot_id="inspector-01",
    run_id=run_id,  # Unique per execution
    events=[...]
)
```

### Validate Before Submitting

```python
# Always verify before submitting
result = client.verify(envelope)

if result.valid:
    proof_id = client.submit_proof(envelope)
else:
    print(f"Invalid proof: {result.reason}")
```

