# Quick Start

Get up and running with ACTO in under 5 minutes.

## Prerequisites

- Python 3.9+
- Solana wallet (Phantom, Solflare, etc.)
- 50,000 ACTO tokens for API access

## Installation

Install the SDK from PyPI:

```bash
pip install actobotics
```

### Optional Dependencies

```bash
# With Solana integration
pip install actobotics[solana]

# With all features
pip install actobotics[full]
```

## Step 1: Get Your API Key

1. Visit [api.actobotics.net/dashboard](https://api.actobotics.net/dashboard)
2. Connect your Solana wallet
3. Click **"Create API Key"**
4. Copy the key (it's only shown once!)

::: warning Important
Store your API key securely. Never commit it to version control.
:::

## Step 2: Create Your First Proof

```python
from acto.proof import create_proof
from acto.telemetry.models import TelemetryBundle, TelemetryEvent
from acto.crypto import KeyPair

# Generate a signing keypair
keypair = KeyPair.generate()

# Create telemetry data from your robot
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
            topic="arm",
            data={"position": [0.5, 0.2, 0.8]}
        ),
        TelemetryEvent(
            ts="2025-01-15T10:30:02Z",
            topic="gripper",
            data={"action": "open", "force": 0.0}
        ),
    ]
)

# Create the proof (signs and hashes the telemetry)
envelope = create_proof(
    bundle,
    keypair.private_key_b64,
    keypair.public_key_b64
)

print(f"Proof created!")
print(f"Payload hash: {envelope.payload.payload_hash}")
```

## Step 3: Verify and Submit

All proofs must be verified through the ACTO API:

```python
from acto.client import ACTOClient

# Initialize the client
client = ACTOClient(
    api_key="acto_your_api_key_here",
    wallet_address="YOUR_SOLANA_WALLET_ADDRESS"
)

# Verify the proof
result = client.verify(envelope)
print(f"Valid: {result.valid}")
print(f"Reason: {result.reason}")

# Submit to the registry
proof_id = client.submit_proof(envelope)
print(f"Submitted! Proof ID: {proof_id}")
```

## Step 4: Search and Retrieve

```python
# List recent proofs
proofs = client.list_proofs(limit=10)
for proof in proofs.items:
    print(f"- {proof.task_id} ({proof.created_at})")

# Search with filters
results = client.search_proofs(
    robot_id="robot-alpha-01",
    created_after="2025-01-01T00:00:00Z",
    limit=50
)
print(f"Found {results.total} proofs")

# Get a specific proof
proof = client.get_proof(proof_id)
```

## Using the CLI

The SDK also includes a CLI for quick operations:

```bash
# Generate a keypair
acto keys generate

# Create a proof from telemetry file
acto proof create \
  --task-id "task-001" \
  --source telemetry.jsonl \
  --output proof.json

# Interactive mode
acto interactive
```

## Environment Variables

For convenience, set environment variables:

```bash
export ACTO_API_KEY="acto_xxx..."
export ACTO_WALLET_ADDRESS="YOUR_WALLET"
```

Then use the client without explicit credentials:

```python
import os
from acto.client import ACTOClient

client = ACTOClient(
    api_key=os.environ["ACTO_API_KEY"],
    wallet_address=os.environ["ACTO_WALLET_ADDRESS"]
)
```

## Next Steps

- [Core Concepts](/guide/concepts) - Understand how ACTO works
- [SDK Reference](/sdk/client) - Full API documentation
- [Fleet Management](/guide/fleet/overview) - Monitor your robots
- [API Reference](/api/overview) - REST API documentation

