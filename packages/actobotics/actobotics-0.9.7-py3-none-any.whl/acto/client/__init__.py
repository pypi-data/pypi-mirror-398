"""
ACTO API Client.

Provides HTTP clients for interacting with the hosted ACTO API.

Synchronous Usage:
    >>> from acto.client import ACTOClient
    >>> 
    >>> client = ACTOClient(
    ...     api_key="acto_xxx...",
    ...     wallet_address="ABC123..."
    ... )
    >>> 
    >>> # Submit a proof
    >>> envelope = create_proof(bundle, private_key, public_key)
    >>> proof_id = client.submit_proof(envelope)
    >>> 
    >>> # Search proofs
    >>> results = client.search_proofs(robot_id="robot-001")
    >>> 
    >>> # Fleet management
    >>> fleet = client.fleet.get_overview()
    >>> client.fleet.report_health("robot-001", cpu_percent=45.2)

Async Usage:
    >>> from acto.client import AsyncACTOClient
    >>> 
    >>> async with AsyncACTOClient(
    ...     api_key="acto_xxx...",
    ...     wallet_address="ABC123..."
    ... ) as client:
    ...     proof_id = await client.submit_proof(envelope)
    ...     fleet = await client.fleet.get_overview()
"""

from .async_client import AsyncACTOClient, AsyncFleetClient
from .exceptions import (
    ACTOClientError,
    AuthenticationError,
    AuthorizationError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
)
from .models import (
    AccessCheckResponse,
    AssignDevicesResponse,
    BatchVerifyResponse,
    BatchVerifyResult,
    CreateGroupResponse,
    DeleteGroupResponse,
    DeviceDetailResponse,
    DeviceGroup,
    DeviceHealth,
    DeviceInfo,
    FleetOverviewResponse,
    FleetSummary,
    GroupListResponse,
    HealthReportResponse,
    HealthResponse,
    ProofListItem,
    ProofListResponse,
    ProofSearchResponse,
    ProofSubmitResponse,
    RenameDeviceResponse,
    ScoreResponse,
    VerifyResponse,
    WalletStatsResponse,
)
from .sync_client import ACTOClient, FleetClient

__all__ = [
    # Clients
    "ACTOClient",
    "AsyncACTOClient",
    "FleetClient",
    "AsyncFleetClient",
    # Exceptions
    "ACTOClientError",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "ValidationError",
    "RateLimitError",
    "ServerError",
    "NetworkError",
    # Response Models
    "HealthResponse",
    "ProofSubmitResponse",
    "ProofListItem",
    "ProofListResponse",
    "ProofSearchResponse",
    "VerifyResponse",
    "BatchVerifyResult",
    "BatchVerifyResponse",
    "ScoreResponse",
    "WalletStatsResponse",
    "AccessCheckResponse",
    "DeviceHealth",
    "DeviceInfo",
    "DeviceDetailResponse",
    "DeviceGroup",
    "FleetSummary",
    "FleetOverviewResponse",
    "GroupListResponse",
    "HealthReportResponse",
    "RenameDeviceResponse",
    "CreateGroupResponse",
    "AssignDevicesResponse",
    "DeleteGroupResponse",
]

