# ACTOClient

The `ACTOClient` is the main interface for interacting with the ACTO API.

## Constructor

```python
from acto.client import ACTOClient

client = ACTOClient(
    api_key: str,
    wallet_address: str,
    *,
    base_url: str = "https://api.actobotics.net",
    timeout: float = 30.0
)
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `api_key` | `str` | Yes | Your ACTO API key |
| `wallet_address` | `str` | Yes | Your Solana wallet address |
| `base_url` | `str` | No | API base URL |
| `timeout` | `float` | No | Request timeout in seconds |

### Example

```python
from acto.client import ACTOClient

client = ACTOClient(
    api_key="acto_abc123...",
    wallet_address="5K8vK..."
)
```

## Context Manager

The client can be used as a context manager to ensure proper cleanup:

```python
with ACTOClient(api_key="...", wallet_address="...") as client:
    result = client.verify(envelope)
    # Connection is automatically closed
```

## Methods

### Proof Operations

#### `submit_proof(envelope)`

Submit a proof to the ACTO registry.

```python
proof_id = client.submit_proof(envelope)
print(f"Submitted: {proof_id}")
```

**Parameters:**
- `envelope` (`ProofEnvelope`) - The proof envelope to submit

**Returns:** `str` - The proof ID

---

#### `get_proof(proof_id)`

Retrieve a proof by ID.

```python
envelope = client.get_proof("abc123...")
print(envelope.payload.subject.task_id)
```

**Parameters:**
- `proof_id` (`str`) - The proof ID

**Returns:** `ProofEnvelope`

---

#### `list_proofs(limit=50)`

List recent proofs.

```python
response = client.list_proofs(limit=10)
for item in response.items:
    print(f"- {item.task_id}")
```

**Parameters:**
- `limit` (`int`) - Maximum results (default: 50)

**Returns:** `ProofListResponse`

---

#### `search_proofs(...)`

Search and filter proofs with pagination.

```python
results = client.search_proofs(
    robot_id="robot-alpha-01",
    created_after="2025-01-01T00:00:00Z",
    created_before="2025-12-31T23:59:59Z",
    search_text="warehouse",
    limit=50,
    offset=0,
    sort_field="created_at",
    sort_order="desc"
)

print(f"Found {results.total} proofs")
for proof in results.items:
    print(f"  {proof.task_id} - {proof.created_at}")
```

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `task_id` | `str` | Filter by task ID |
| `robot_id` | `str` | Filter by robot ID |
| `run_id` | `str` | Filter by run ID |
| `signer_public_key` | `str` | Filter by signer |
| `created_after` | `str` | ISO 8601 start date |
| `created_before` | `str` | ISO 8601 end date |
| `search_text` | `str` | Full-text search |
| `limit` | `int` | Results per page |
| `offset` | `int` | Pagination offset |
| `sort_field` | `str` | Field to sort by |
| `sort_order` | `str` | "asc" or "desc" |

**Returns:** `ProofSearchResponse`

### Verification

#### `verify(envelope)`

Verify a proof's cryptographic signature.

```python
result = client.verify(envelope)

if result.valid:
    print("✅ Proof is valid!")
else:
    print(f"❌ Invalid: {result.reason}")
```

**Parameters:**
- `envelope` (`ProofEnvelope`) - The proof to verify

**Returns:** `VerifyResponse` with fields:
- `valid` (`bool`) - Whether the proof is valid
- `reason` (`str`) - Explanation

---

#### `verify_batch(envelopes)`

Verify multiple proofs in a single request.

```python
results = client.verify_batch([env1, env2, env3])

print(f"Valid: {results.valid_count}/{results.total}")
for r in results.results:
    status = "✅" if r.valid else "❌"
    print(f"  {status} Index {r.index}: {r.reason}")
```

**Parameters:**
- `envelopes` (`list[ProofEnvelope]`) - List of proofs to verify

**Returns:** `BatchVerifyResponse`

### Statistics

#### `get_wallet_stats(wallet_address=None)`

Get statistics for a wallet.

```python
stats = client.get_wallet_stats()

print(f"Total proofs: {stats.total_proofs_submitted}")
print(f"Success rate: {stats.verification_success_rate}%")
print(f"Avg reputation: {stats.average_reputation_score}")
```

**Parameters:**
- `wallet_address` (`str`, optional) - Wallet to query (default: your wallet)

**Returns:** `WalletStatsResponse`

### Access Control

#### `check_access(owner, mint, minimum=50000, rpc_url="")`

Check if a wallet has sufficient token balance.

```python
result = client.check_access(
    owner="5K8vK...",
    mint="ACTO_MINT_ADDRESS",
    minimum=50000
)

if result.allowed:
    print(f"Access granted! Balance: {result.balance}")
else:
    print(f"Access denied: {result.reason}")
```

**Parameters:**
- `owner` (`str`) - Wallet address to check
- `mint` (`str`) - Token mint address
- `minimum` (`float`) - Required balance
- `rpc_url` (`str`) - Optional custom RPC URL

**Returns:** `AccessCheckResponse`

### Health Check

#### `health()`

Check API health status.

```python
health = client.health()
print(f"Service: {health.service}")
print(f"Version: {health.version}")
print(f"OK: {health.ok}")
```

**Returns:** `HealthResponse`

## Fleet Sub-Client

The client includes a `fleet` sub-client for fleet management:

```python
# Get fleet overview
fleet = client.fleet.get_overview()

# Get device details
device = client.fleet.get_device("robot-001")

# Report health
client.fleet.report_health(
    "robot-001",
    cpu_percent=45.2,
    battery_percent=85.0
)
```

See [FleetClient](/sdk/fleet-client) for full documentation.

## Error Handling

The client raises specific exceptions for different error types:

```python
from acto.client.exceptions import (
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ValidationError,
    RateLimitError,
    ServerError,
)

try:
    result = client.verify(envelope)
except AuthenticationError:
    print("Invalid API key")
except AuthorizationError:
    print("Insufficient token balance")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after}s")
except ServerError:
    print("Server error - try again later")
```

See [Error Handling](/sdk/exceptions) for details.

