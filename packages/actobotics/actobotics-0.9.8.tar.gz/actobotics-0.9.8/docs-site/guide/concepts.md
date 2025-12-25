# Core Concepts

Understanding the key concepts behind ACTO will help you use it effectively.

## Proof Envelope

A **Proof Envelope** is the core data structure in ACTO. It contains everything needed to verify an execution proof.

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
    "telemetry_hash": "abc123...",
    "payload_hash": "def456...",
    "hash_alg": "blake3",
    "signature_alg": "ed25519",
    "meta": {}
  },
  "signer_public_key_b64": "...",
  "signature_b64": "...",
  "anchor_ref": null
}
```

### Components

| Field | Description |
|-------|-------------|
| `payload` | The proof data being signed |
| `subject` | Identifies what this proof is about |
| `telemetry_normalized` | Canonicalized telemetry data |
| `telemetry_hash` | BLAKE3 hash of telemetry |
| `payload_hash` | BLAKE3 hash of the entire payload |
| `signature_b64` | Ed25519 signature over payload_hash |
| `signer_public_key_b64` | Public key of the signer |
| `anchor_ref` | Optional Solana transaction reference |

## Telemetry Bundle

A **Telemetry Bundle** is the input data used to create a proof. It contains timestamped events from your robot.

```python
bundle = TelemetryBundle(
    task_id="pick-and-place-001",
    robot_id="robot-alpha-01",
    run_id="run-001",  # optional
    events=[
        TelemetryEvent(
            ts="2025-01-15T10:30:00Z",
            topic="sensor",
            data={"temperature": 42.5}
        ),
        # ... more events
    ]
)
```

### Telemetry Events

Each event has:

- `ts` - ISO 8601 timestamp
- `topic` - Category/source of the event
- `data` - Arbitrary JSON data

## Cryptographic Primitives

### BLAKE3 Hashing

ACTO uses [BLAKE3](https://github.com/BLAKE3-team/BLAKE3) for hashing because it's:

- **Fast** - Optimized for modern CPUs
- **Secure** - Based on ChaCha20
- **Deterministic** - Same input = same hash

### Ed25519 Signatures

[Ed25519](https://ed25519.cr.yp.to/) is used for signing because it's:

- **Small** - 64-byte signatures
- **Fast** - ~15,000 signatures/second
- **Secure** - No known vulnerabilities

## Verification Flow

```
┌────────────────────────────────────────────────────────────────┐
│                     Verification Process                        │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Extract payload_hash from envelope                          │
│                    ▼                                            │
│  2. Recompute hash from payload                                 │
│                    ▼                                            │
│  3. Compare hashes (integrity check)                            │
│                    ▼                                            │
│  4. Verify Ed25519 signature using public key                   │
│                    ▼                                            │
│  5. Return valid/invalid with reason                            │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

::: info Why API-Only Verification?
Starting from v0.9.1, all verification must go through the ACTO API. This ensures:
- **Integrity** - Centralized verification prevents tampering
- **Compliance** - Enables audit trails
- **Fleet Tracking** - Automatic device discovery
- **Token Gating** - Only authorized users can verify
:::

## Signing Keys

### KeyPair

A `KeyPair` contains both private and public keys:

```python
from acto.crypto import KeyPair

# Generate new keypair
keypair = KeyPair.generate()

# Access keys (base64 encoded)
print(keypair.private_key_b64)  # Keep secret!
print(keypair.public_key_b64)   # Share publicly

# Save to file
keypair.save("my_keys.json")

# Load from file
loaded = KeyPair.load("my_keys.json")
```

::: danger Private Key Security
Never share your private key. Anyone with the private key can sign proofs as you.
:::

## Subject Identifiers

The `subject` field identifies what a proof is about:

| Field | Required | Description |
|-------|----------|-------------|
| `task_id` | Yes | Unique task identifier |
| `robot_id` | No | Robot/device identifier |
| `run_id` | No | Specific execution run |

Best practices:
- Use consistent naming conventions
- Include timestamps in run_id
- Use robot_id for fleet tracking

## Metadata

The `meta` field stores arbitrary metadata:

```python
bundle = TelemetryBundle(
    task_id="inspection-001",
    robot_id="inspector-01",
    events=[...],
    meta={
        "operator": "John Doe",
        "location": "Warehouse A",
        "batch_number": "B-2025-001"
    }
)
```

This data is included in the proof but not individually hashed.

## Proof Chaining

Proofs can be chained together for sequential operations:

```python
from acto.proof.chaining import ProofChain

chain = ProofChain()

# Add proofs in sequence
chain.add(proof_1)
chain.add(proof_2)
chain.add(proof_3)

# Verify the entire chain
is_valid = chain.verify(client)
```

## Anchoring (Optional)

Proofs can be anchored to Solana for additional immutability:

```python
from acto.anchor import anchor_proof

# Anchor to Solana (requires solana extra)
tx_signature = anchor_proof(envelope, wallet_keypair)

# The anchor_ref field is updated
print(envelope.anchor_ref)  # Solana transaction signature
```

::: tip When to Anchor
Anchoring is optional and costs a small transaction fee. Use it for:
- High-value operations
- Regulatory compliance
- Maximum immutability
:::

