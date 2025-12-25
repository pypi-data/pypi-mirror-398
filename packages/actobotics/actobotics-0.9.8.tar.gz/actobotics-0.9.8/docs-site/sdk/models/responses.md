# Response Models

The SDK provides typed response models for all API operations.

## VerifyResponse

```python
class VerifyResponse:
    valid: bool      # Whether proof is valid
    reason: str      # "ok" or error description
```

## BatchVerifyResponse

```python
class BatchVerifyResponse:
    results: list[BatchVerifyResult]
    total: int
    valid_count: int
    invalid_count: int

class BatchVerifyResult:
    index: int
    valid: bool
    reason: str
    payload_hash: str | None
```

## ProofListResponse

```python
class ProofListResponse:
    items: list[ProofListItem]

class ProofListItem:
    proof_id: str
    task_id: str
    robot_id: str | None
    created_at: str
```

## ProofSearchResponse

```python
class ProofSearchResponse:
    items: list[ProofSearchItem]
    total: int
    limit: int
    offset: int
    has_more: bool
```

## WalletStatsResponse

```python
class WalletStatsResponse:
    wallet_address: str
    total_proofs_submitted: int
    total_verifications: int
    successful_verifications: int
    failed_verifications: int
    verification_success_rate: float
    average_reputation_score: float
    first_activity: str | None
    last_activity: str | None
    proofs_by_robot: dict[str, int]
    proofs_by_task: dict[str, int]
    activity_timeline: list[dict]
```

## FleetOverviewResponse

```python
class FleetOverviewResponse:
    devices: list[FleetDevice]
    groups: list[FleetGroup]
    summary: FleetSummary

class FleetSummary:
    total_devices: int
    active_devices: int
    warning_devices: int
    offline_devices: int
    total_proofs: int
    total_tasks: int
    total_groups: int
```

## AccessCheckResponse

```python
class AccessCheckResponse:
    allowed: bool
    reason: str
    balance: float
```

## HealthResponse

```python
class HealthResponse:
    ok: bool
    service: str
    version: str
```

