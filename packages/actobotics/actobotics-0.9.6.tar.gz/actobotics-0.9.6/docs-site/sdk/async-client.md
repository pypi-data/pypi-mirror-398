# AsyncACTOClient

Asynchronous client for the ACTO API using `asyncio`.

## Usage

```python
import asyncio
from acto.client import AsyncACTOClient

async def main():
    async with AsyncACTOClient(
        api_key="acto_abc123...",
        wallet_address="5K8vK..."
    ) as client:
        # Verify proof
        result = await client.verify(envelope)
        print(f"Valid: {result.valid}")
        
        # Submit proof
        proof_id = await client.submit_proof(envelope)
        print(f"Submitted: {proof_id}")

asyncio.run(main())
```

## Constructor

```python
AsyncACTOClient(
    api_key: str,
    wallet_address: str,
    *,
    base_url: str = "https://api.actobotics.net",
    timeout: float = 30.0
)
```

Same parameters as [ACTOClient](/sdk/client).

## Methods

All methods from `ACTOClient` are available as async versions:

```python
# Proof operations
proof_id = await client.submit_proof(envelope)
envelope = await client.get_proof(proof_id)
proofs = await client.list_proofs(limit=50)
results = await client.search_proofs(robot_id="robot-001")

# Verification
result = await client.verify(envelope)
results = await client.verify_batch([env1, env2, env3])

# Statistics
stats = await client.get_wallet_stats()

# Access control
result = await client.check_access(owner, mint, minimum)

# Fleet management
fleet = await client.fleet.get_overview()
device = await client.fleet.get_device("robot-001")
await client.fleet.report_health("robot-001", cpu_percent=45.2)
```

## Concurrent Operations

Run multiple operations concurrently:

```python
import asyncio
from acto.client import AsyncACTOClient

async def verify_all(envelopes):
    async with AsyncACTOClient(api_key="...", wallet_address="...") as client:
        # Verify all concurrently
        tasks = [client.verify(env) for env in envelopes]
        results = await asyncio.gather(*tasks)
        
        valid = sum(1 for r in results if r.valid)
        print(f"Valid: {valid}/{len(results)}")

asyncio.run(verify_all(envelopes))
```

## Context Manager

Always use as context manager for proper cleanup:

```python
async with AsyncACTOClient(...) as client:
    # Use client
    pass
# Connection automatically closed
```

Or manually close:

```python
client = AsyncACTOClient(...)
try:
    result = await client.verify(envelope)
finally:
    await client.close()
```

## Error Handling

Same exceptions as sync client:

```python
from acto.client.exceptions import (
    AuthenticationError,
    RateLimitError,
)

try:
    result = await client.verify(envelope)
except RateLimitError as e:
    await asyncio.sleep(e.retry_after or 1)
    result = await client.verify(envelope)
```

## Performance Tips

### Connection Pooling

The client automatically uses connection pooling. Reuse the same client instance:

```python
# ✅ Good - reuse client
async with AsyncACTOClient(...) as client:
    for envelope in envelopes:
        await client.verify(envelope)

# ❌ Bad - new client per request
for envelope in envelopes:
    async with AsyncACTOClient(...) as client:
        await client.verify(envelope)
```

### Batching

Use batch endpoints when possible:

```python
# ✅ Good - single batch request
results = await client.verify_batch(envelopes)

# ❌ Less efficient - many requests
results = await asyncio.gather(*[client.verify(e) for e in envelopes])
```

### Semaphore for Concurrency Control

Limit concurrent requests:

```python
semaphore = asyncio.Semaphore(10)  # Max 10 concurrent

async def verify_limited(envelope):
    async with semaphore:
        return await client.verify(envelope)

results = await asyncio.gather(*[verify_limited(e) for e in envelopes])
```

