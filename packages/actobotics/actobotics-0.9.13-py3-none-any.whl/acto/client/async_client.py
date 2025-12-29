"""
ACTO Asynchronous API Client.

An async client for interacting with the ACTO API.
"""

from __future__ import annotations

from typing import Any

import httpx

from acto import __version__
from acto.proof.models import ProofEnvelope

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
    CreateGroupResponse,
    DeleteDeviceResponse,
    DeleteGroupResponse,
    DeviceDetailResponse,
    DeviceHealth,
    FleetOverviewResponse,
    GroupListResponse,
    HealthReportResponse,
    HealthResponse,
    ProofListResponse,
    ProofSearchResponse,
    ProofSubmitResponse,
    RenameDeviceResponse,
    ReorderDevicesResponse,
    ScoreResponse,
    VerifyResponse,
    WalletStatsResponse,
)


DEFAULT_BASE_URL = "https://api.actobotics.net"
DEFAULT_TIMEOUT = 30.0


class AsyncFleetClient:
    """
    Async Fleet Management client.
    
    Provides async methods for managing robot fleet through the ACTO API.
    """

    def __init__(self, parent: "AsyncACTOClient"):
        self._parent = parent

    async def get_overview(self) -> FleetOverviewResponse:
        """Get fleet overview with all devices, groups, and summary."""
        data = await self._parent._request("GET", "/v1/fleet")
        return FleetOverviewResponse.model_validate(data)

    async def get_device(self, device_id: str) -> DeviceDetailResponse:
        """Get detailed information about a specific device."""
        data = await self._parent._request("GET", f"/v1/fleet/devices/{device_id}")
        return DeviceDetailResponse.model_validate(data)

    async def rename_device(self, device_id: str, name: str) -> RenameDeviceResponse:
        """Set a custom name for a device."""
        data = await self._parent._request(
            "PATCH",
            f"/v1/fleet/devices/{device_id}/name",
            json={"name": name},
        )
        return RenameDeviceResponse.model_validate(data)

    async def delete_device(self, device_id: str) -> DeleteDeviceResponse:
        """
        Delete (hide) a device from the fleet.
        
        This is a soft delete - the device's proofs are preserved,
        but it won't appear in the fleet list.
        """
        data = await self._parent._request("DELETE", f"/v1/fleet/devices/{device_id}")
        return DeleteDeviceResponse.model_validate(data)

    async def reorder_devices(self, device_orders: list[dict[str, Any]]) -> ReorderDevicesResponse:
        """
        Update the sort order of multiple devices.
        
        Args:
            device_orders: List of dicts with device_id and sort_order
                Example: [{"device_id": "robot-001", "sort_order": 0},
                          {"device_id": "robot-002", "sort_order": 1}]
        """
        data = await self._parent._request(
            "PATCH",
            "/v1/fleet/devices/order",
            json={"device_orders": device_orders},
        )
        return ReorderDevicesResponse.model_validate(data)

    async def report_health(
        self,
        device_id: str,
        *,
        cpu_percent: float | None = None,
        cpu_temperature: float | None = None,
        memory_percent: float | None = None,
        memory_used_mb: float | None = None,
        memory_total_mb: float | None = None,
        battery_percent: float | None = None,
        battery_charging: bool | None = None,
        disk_percent: float | None = None,
        network_connected: bool | None = None,
        network_type: str | None = None,
        uptime_seconds: int | None = None,
        temperature: float | None = None,
        custom_metrics: dict[str, Any] | None = None,
    ) -> HealthReportResponse:
        """
        Report health metrics for a device.
        
        All parameters are optional - only send metrics your device supports.
        """
        payload: dict[str, Any] = {}
        
        if cpu_percent is not None:
            payload["cpu_percent"] = cpu_percent
        if cpu_temperature is not None:
            payload["cpu_temperature"] = cpu_temperature
        if memory_percent is not None:
            payload["memory_percent"] = memory_percent
        if memory_used_mb is not None:
            payload["memory_used_mb"] = memory_used_mb
        if memory_total_mb is not None:
            payload["memory_total_mb"] = memory_total_mb
        if battery_percent is not None:
            payload["battery_percent"] = battery_percent
        if battery_charging is not None:
            payload["battery_charging"] = battery_charging
        if disk_percent is not None:
            payload["disk_percent"] = disk_percent
        if network_connected is not None:
            payload["network_connected"] = network_connected
        if network_type is not None:
            payload["network_type"] = network_type
        if uptime_seconds is not None:
            payload["uptime_seconds"] = uptime_seconds
        if temperature is not None:
            payload["temperature"] = temperature
        if custom_metrics is not None:
            payload["custom_metrics"] = custom_metrics

        data = await self._parent._request(
            "POST",
            f"/v1/fleet/devices/{device_id}/health",
            json=payload,
        )
        return HealthReportResponse.model_validate(data)

    async def get_health(self, device_id: str) -> DeviceHealth:
        """Get the latest health metrics for a device."""
        data = await self._parent._request("GET", f"/v1/fleet/devices/{device_id}/health")
        return DeviceHealth.model_validate(data.get("health", {}))

    async def list_groups(self) -> GroupListResponse:
        """List all device groups."""
        data = await self._parent._request("GET", "/v1/fleet/groups")
        return GroupListResponse.model_validate(data)

    async def create_group(self, name: str, description: str | None = None) -> CreateGroupResponse:
        """Create a new device group."""
        payload: dict[str, Any] = {"name": name}
        if description:
            payload["description"] = description
            
        data = await self._parent._request("POST", "/v1/fleet/groups", json=payload)
        return CreateGroupResponse.model_validate(data)

    async def assign_devices(self, group_id: str, device_ids: list[str]) -> AssignDevicesResponse:
        """Assign devices to a group."""
        data = await self._parent._request(
            "POST",
            f"/v1/fleet/groups/{group_id}/assign",
            json={"device_ids": device_ids},
        )
        return AssignDevicesResponse.model_validate(data)

    async def unassign_devices(self, group_id: str, device_ids: list[str]) -> AssignDevicesResponse:
        """Remove devices from a group."""
        data = await self._parent._request(
            "POST",
            f"/v1/fleet/groups/{group_id}/unassign",
            json={"device_ids": device_ids},
        )
        return AssignDevicesResponse.model_validate(data)

    async def delete_group(self, group_id: str) -> DeleteGroupResponse:
        """Delete a device group."""
        data = await self._parent._request("DELETE", f"/v1/fleet/groups/{group_id}")
        return DeleteGroupResponse.model_validate(data)


class AsyncACTOClient:
    """
    Asynchronous client for the ACTO API.
    
    This client provides async methods for submitting proofs, verification,
    and fleet management through the hosted ACTO API.
    
    Args:
        api_key: Your ACTO API key (from dashboard)
        wallet_address: Your Solana wallet address
        base_url: API base URL (default: https://api.actobotics.net)
        timeout: Request timeout in seconds (default: 30)
        
    Example:
        >>> from acto.client import AsyncACTOClient
        >>> 
        >>> async with AsyncACTOClient(
        ...     api_key="acto_xxx...",
        ...     wallet_address="ABC123..."
        ... ) as client:
        ...     # Submit a proof
        ...     proof_id = await client.submit_proof(envelope)
        ...     
        ...     # Get fleet overview
        ...     fleet = await client.fleet.get_overview()
    """

    def __init__(
        self,
        api_key: str,
        wallet_address: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        self.api_key = api_key
        self.wallet_address = wallet_address
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            headers=self._build_headers(),
        )
        
        # Fleet management sub-client
        self.fleet = AsyncFleetClient(self)

    def _build_headers(self) -> dict[str, str]:
        """Build request headers with authentication."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "X-Wallet-Address": self.wallet_address,
            "Content-Type": "application/json",
            "User-Agent": f"acto-python-sdk/{__version__}",
        }

    def _handle_error(self, response: httpx.Response) -> None:
        """Handle HTTP error responses."""
        status = response.status_code
        
        try:
            detail = response.json().get("detail", response.text)
        except Exception:
            detail = response.text

        if status == 401:
            raise AuthenticationError(detail, status_code=status, response=response)
        elif status == 403:
            raise AuthorizationError(detail, status_code=status, response=response)
        elif status == 404:
            raise NotFoundError(detail, status_code=status, response=response)
        elif status == 422 or status == 400:
            raise ValidationError(detail, status_code=status, response=response)
        elif status == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(
                detail,
                retry_after=float(retry_after) if retry_after else None,
                response=response,
            )
        elif status >= 500:
            raise ServerError(detail, status_code=status, response=response)
        else:
            raise ACTOClientError(detail, status_code=status, response=response)

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make an async HTTP request to the API."""
        try:
            response = await self._client.request(
                method,
                path,
                json=json,
                params=params,
            )
        except httpx.ConnectError as e:
            raise NetworkError(f"Failed to connect to {self.base_url}: {e}") from e
        except httpx.TimeoutException as e:
            raise NetworkError(f"Request timed out: {e}") from e
        except httpx.RequestError as e:
            raise NetworkError(f"Request failed: {e}") from e

        if response.status_code >= 400:
            self._handle_error(response)

        return response.json()

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> "AsyncACTOClient":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    # =========================================================================
    # Health Check
    # =========================================================================

    async def health(self) -> HealthResponse:
        """Check API health status."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.base_url}/health")
        return HealthResponse.model_validate(response.json())

    # =========================================================================
    # Proof Operations
    # =========================================================================

    async def submit_proof(self, envelope: ProofEnvelope) -> str:
        """
        Submit a proof to the ACTO registry.
        
        Args:
            envelope: The proof envelope to submit
            
        Returns:
            str: The proof ID
        """
        data = await self._request(
            "POST",
            "/v1/proofs",
            json={"envelope": envelope.model_dump()},
        )
        return data["proof_id"]

    async def get_proof(self, proof_id: str) -> ProofEnvelope:
        """Get a proof by ID."""
        data = await self._request("GET", f"/v1/proofs/{proof_id}")
        # API returns {"proof_id": ..., "envelope": ...}
        envelope_data = data.get("envelope", data)
        return ProofEnvelope.model_validate(envelope_data)

    async def list_proofs(self, limit: int = 50) -> ProofListResponse:
        """List recent proofs."""
        data = await self._request("GET", "/v1/proofs", params={"limit": limit})
        return ProofListResponse.model_validate(data)

    async def search_proofs(
        self,
        *,
        task_id: str | None = None,
        robot_id: str | None = None,
        run_id: str | None = None,
        signer_public_key: str | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        search_text: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort_field: str = "created_at",
        sort_order: str = "desc",
    ) -> ProofSearchResponse:
        """Search and filter proofs."""
        payload: dict[str, Any] = {
            "limit": limit,
            "offset": offset,
            "sort_field": sort_field,
            "sort_order": sort_order,
        }
        
        if task_id:
            payload["task_id"] = task_id
        if robot_id:
            payload["robot_id"] = robot_id
        if run_id:
            payload["run_id"] = run_id
        if signer_public_key:
            payload["signer_public_key"] = signer_public_key
        if created_after:
            payload["created_after"] = created_after
        if created_before:
            payload["created_before"] = created_before
        if search_text:
            payload["search_text"] = search_text

        data = await self._request("POST", "/v1/proofs/search", json=payload)
        return ProofSearchResponse.model_validate(data)

    # =========================================================================
    # Verification
    # =========================================================================

    async def verify(self, envelope: ProofEnvelope) -> VerifyResponse:
        """Verify a proof's cryptographic signature remotely."""
        data = await self._request(
            "POST",
            "/v1/verify",
            json={"envelope": envelope.model_dump()},
        )
        return VerifyResponse.model_validate(data)

    async def verify_batch(self, envelopes: list[ProofEnvelope]) -> BatchVerifyResponse:
        """Verify multiple proofs in a single request."""
        data = await self._request(
            "POST",
            "/v1/verify/batch",
            json={"envelopes": [e.model_dump() for e in envelopes]},
        )
        return BatchVerifyResponse.model_validate(data)

    # =========================================================================
    # Scoring
    # =========================================================================

    async def score(self, envelope: ProofEnvelope) -> ScoreResponse:
        """Get reputation score for a proof."""
        data = await self._request(
            "POST",
            "/v1/score",
            json={"envelope": envelope.model_dump()},
        )
        return ScoreResponse.model_validate(data)

    # =========================================================================
    # Statistics
    # =========================================================================

    async def get_wallet_stats(self, wallet_address: str | None = None) -> WalletStatsResponse:
        """Get statistics for a wallet."""
        addr = wallet_address or self.wallet_address
        data = await self._request("GET", f"/v1/stats/wallet/{addr}")
        return WalletStatsResponse.model_validate(data)

    # =========================================================================
    # Access Control
    # =========================================================================

    async def check_access(
        self,
        owner: str,
        mint: str,
        minimum: float = 50000,
        rpc_url: str = "",  # Empty = use backend's configured RPC (Helius)
    ) -> AccessCheckResponse:
        """Check if a wallet has sufficient token balance."""
        data = await self._request(
            "POST",
            "/v1/access/check",
            json={
                "rpc_url": rpc_url,
                "owner": owner,
                "mint": mint,
                "minimum": minimum,
            },
        )
        return AccessCheckResponse.model_validate(data)

