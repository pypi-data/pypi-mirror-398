# ProofEnvelope

The `ProofEnvelope` is the core data structure for ACTO proofs.

## Definition

```python
from acto.proof.models import ProofEnvelope, ProofPayload, ProofSubject
```

## Structure

```python
class ProofEnvelope:
    payload: ProofPayload
    signer_public_key_b64: str
    signature_b64: str
    anchor_ref: str | None
```

### ProofPayload

```python
class ProofPayload:
    version: str                    # "1"
    subject: ProofSubject
    created_at: str                 # ISO 8601
    telemetry_normalized: dict
    telemetry_hash: str
    payload_hash: str
    hash_alg: str                   # "blake3"
    signature_alg: str              # "ed25519"
    meta: dict
```

### ProofSubject

```python
class ProofSubject:
    task_id: str
    robot_id: str | None
    run_id: str | None
```

## Creating Envelopes

Use `create_proof()` to create envelopes:

```python
from acto.proof import create_proof

envelope = create_proof(
    bundle,
    keypair.private_key_b64,
    keypair.public_key_b64
)
```

## Serialization

### To Dict

```python
data = envelope.model_dump()
```

### To JSON

```python
import json
json_str = envelope.model_dump_json()
```

### From Dict

```python
envelope = ProofEnvelope.model_validate(data)
```

## Accessing Fields

```python
# Subject info
print(envelope.payload.subject.task_id)
print(envelope.payload.subject.robot_id)

# Hashes
print(envelope.payload.payload_hash)
print(envelope.payload.telemetry_hash)

# Signature
print(envelope.signature_b64)
print(envelope.signer_public_key_b64)
```

