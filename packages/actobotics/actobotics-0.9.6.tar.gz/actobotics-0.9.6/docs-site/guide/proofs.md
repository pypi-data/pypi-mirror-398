# How Proofs Work

Understanding the proof protocol is key to using ACTO effectively.

## What Is a Proof?

An ACTO proof is a cryptographically signed attestation that a specific task was executed with specific telemetry data.

A proof proves:
- **What** - The task that was executed
- **When** - Timestamp of execution
- **Who** - The signing entity
- **Data** - The telemetry recorded

## Proof Structure

```json
{
  "payload": {
    "version": "1",
    "subject": {
      "task_id": "pick-and-place-001",
      "robot_id": "robot-alpha-01",
      "run_id": "run-2025-01-15"
    },
    "created_at": "2025-01-15T10:30:00Z",
    "telemetry_normalized": { ... },
    "telemetry_hash": "blake3:abc123...",
    "payload_hash": "blake3:def456...",
    "hash_alg": "blake3",
    "signature_alg": "ed25519",
    "meta": {}
  },
  "signer_public_key_b64": "base64...",
  "signature_b64": "base64...",
  "anchor_ref": null
}
```

## Properties

### Deterministic

Given the same input (telemetry + keys), the same proof is always produced:

```python
# Same input = same output
proof1 = create_proof(bundle, private_key, public_key)
proof2 = create_proof(bundle, private_key, public_key)

assert proof1.payload.payload_hash == proof2.payload.payload_hash
```

### Signed

Ed25519 signatures ensure authenticity:

```python
# Only the private key holder can create this signature
signature = sign(payload_hash, private_key)

# Anyone can verify with the public key
is_valid = verify(payload_hash, signature, public_key)
```

### Portable

JSON format works everywhere:

```python
# Save to file
with open("proof.json", "w") as f:
    json.dump(envelope.model_dump(), f)

# Send over network
response = httpx.post(url, json={"envelope": envelope.model_dump()})

# Store in database
db.execute("INSERT INTO proofs VALUES (?)", json.dumps(envelope.model_dump()))
```

### Verifiable

Verify without trusting the source:

```python
result = client.verify(envelope)
# Verification is based on cryptographic math, not trust
```

## Creating a Proof

```python
from acto.proof import create_proof
from acto.telemetry.models import TelemetryBundle, TelemetryEvent
from acto.crypto import KeyPair

# 1. Generate or load keypair
keypair = KeyPair.generate()

# 2. Collect telemetry
bundle = TelemetryBundle(
    task_id="pick-and-place",
    robot_id="robot-001",
    events=[
        TelemetryEvent(ts="2025-01-15T10:30:00Z", topic="sensor", data={"value": 42})
    ]
)

# 3. Create proof
envelope = create_proof(bundle, keypair.private_key_b64, keypair.public_key_b64)
```

## Verification

All proofs must be verified via the ACTO API:

```python
from acto.client import ACTOClient

client = ACTOClient(api_key="...", wallet_address="...")
result = client.verify(envelope)

if result.valid:
    print("Proof is valid!")
```

## Proof Lifecycle

```
1. CREATED     - Proof generated locally
      │
      ▼
2. VERIFIED    - Signature verified via API
      │
      ▼
3. SUBMITTED   - Stored in ACTO registry
      │
      ▼
4. SEARCHABLE  - Can be queried and retrieved
      │
      ▼
5. [OPTIONAL]  - Anchored to Solana for immutability
```

## Best Practices

1. **Include robot_id** - Enables fleet tracking
2. **Use consistent task_ids** - Makes searching easier
3. **Add metadata** - Operator, location, context
4. **Verify before submit** - Catch errors early
5. **Store proof IDs** - For future reference

