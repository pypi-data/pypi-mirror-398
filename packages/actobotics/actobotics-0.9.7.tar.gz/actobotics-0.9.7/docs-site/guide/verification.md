# Verification

All proofs must be verified through the ACTO API.

## Why API Verification?

Starting from v0.9.1, local verification is no longer available. All verification must go through the API for:

- **Integrity** - Centralized verification ensures consistency
- **Compliance** - Audit trails for all verifications
- **Fleet Tracking** - Automatic device discovery
- **Token Gating** - Access control enforcement

## Basic Verification

```python
from acto.client import ACTOClient

client = ACTOClient(api_key="...", wallet_address="...")

# Verify a single proof
result = client.verify(envelope)

if result.valid:
    print("✅ Proof is valid!")
else:
    print(f"❌ Invalid: {result.reason}")
```

## Verification Response

```python
class VerifyResponse:
    valid: bool      # True if proof is valid
    reason: str      # "ok" or error description
```

### Possible Reasons

| Reason | Description |
|--------|-------------|
| `ok` | Proof is valid |
| `Invalid signature` | Signature doesn't match |
| `Hash mismatch` | Computed hash differs |
| `Invalid public key` | Malformed public key |

## Batch Verification

Verify multiple proofs efficiently:

```python
results = client.verify_batch([envelope1, envelope2, envelope3])

print(f"Valid: {results.valid_count}/{results.total}")

for r in results.results:
    status = "✅" if r.valid else "❌"
    print(f"  {status} Index {r.index}: {r.reason}")
```

## Verification Process

```
1. Client sends envelope to API
        │
        ▼
2. API extracts payload_hash
        │
        ▼
3. API canonicalizes payload
        │
        ▼
4. API computes BLAKE3 hash
        │
        ▼
5. API compares with claimed hash
        │ (if mismatch → invalid)
        ▼
6. API verifies Ed25519 signature
        │ (if invalid → invalid)
        ▼
7. API returns result
```

## Verify Before Submit

Always verify before submitting to the registry:

```python
# Verify first
result = client.verify(envelope)

if result.valid:
    # Then submit
    proof_id = client.submit_proof(envelope)
    print(f"Submitted: {proof_id}")
else:
    print(f"Cannot submit invalid proof: {result.reason}")
```

## Error Handling

```python
from acto.client.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ValidationError,
)

try:
    result = client.verify(envelope)
except AuthenticationError:
    print("Invalid API key")
except AuthorizationError:
    print("Insufficient token balance")
except ValidationError as e:
    print(f"Invalid request: {e}")
```

## Offline Scenarios

If you need offline operation, consider:

1. **Queue proofs locally** when offline
2. **Verify and submit** when connection is restored
3. **Use timestamps** to track when proofs were created

```python
import json
from pathlib import Path

QUEUE_FILE = Path("proof_queue.jsonl")

def queue_proof(envelope):
    """Store proof for later verification."""
    with open(QUEUE_FILE, "a") as f:
        f.write(json.dumps(envelope.model_dump()) + "\n")

def process_queue(client):
    """Verify and submit queued proofs."""
    if not QUEUE_FILE.exists():
        return
    
    with open(QUEUE_FILE) as f:
        proofs = [json.loads(line) for line in f]
    
    for proof_data in proofs:
        envelope = ProofEnvelope.model_validate(proof_data)
        result = client.verify(envelope)
        
        if result.valid:
            client.submit_proof(envelope)
    
    QUEUE_FILE.unlink()  # Clear queue
```

## Migration from Local Verification

If you're upgrading from pre-0.9.1:

**Before (0.9.0):**
```python
from acto.proof import verify_proof
is_valid = verify_proof(envelope)  # ❌ No longer available
```

**After (0.9.1+):**
```python
from acto.client import ACTOClient
client = ACTOClient(api_key="...", wallet_address="...")
result = client.verify(envelope)  # ✅ Use API
```

