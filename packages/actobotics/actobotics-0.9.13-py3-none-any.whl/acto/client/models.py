"""
ACTO API Response Models.

Pydantic models for API responses.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# =============================================================================
# Proof Models
# =============================================================================


class ProofSubmitResponse(BaseModel):
    """Response from submitting a proof."""

    proof_id: str


class ProofListItem(BaseModel):
    """Proof item in list responses."""

    proof_id: str
    task_id: str
    robot_id: str | None = None
    run_id: str | None = None
    created_at: str
    signer_public_key_b64: str | None = None


class ProofListResponse(BaseModel):
    """Response from listing proofs."""

    items: list[ProofListItem]


class ProofSearchResponse(BaseModel):
    """Response from searching proofs."""

    items: list[ProofListItem]
    total: int
    limit: int
    offset: int
    has_more: bool


class VerifyResponse(BaseModel):
    """Response from verifying a proof."""

    valid: bool
    reason: str


class BatchVerifyResult(BaseModel):
    """Single result in batch verification."""

    index: int
    valid: bool
    reason: str
    payload_hash: str | None = None


class BatchVerifyResponse(BaseModel):
    """Response from batch verification."""

    results: list[BatchVerifyResult]
    total: int
    valid_count: int
    invalid_count: int


class ScoreResponse(BaseModel):
    """Response from scoring a proof."""

    score: float
    breakdown: dict[str, Any] = Field(default_factory=dict)


# =============================================================================
# Statistics Models
# =============================================================================


class WalletStatsResponse(BaseModel):
    """Response from wallet statistics."""

    wallet_address: str
    total_proofs_submitted: int = 0
    total_verifications: int = 0
    successful_verifications: int = 0
    failed_verifications: int = 0
    verification_success_rate: float = 0.0
    average_reputation_score: float = 0.0
    first_activity: str | None = None
    last_activity: str | None = None
    proofs_by_robot: dict[str, int] = Field(default_factory=dict)
    proofs_by_task: dict[str, int] = Field(default_factory=dict)
    activity_timeline: list[dict[str, Any]] = Field(default_factory=list)


# =============================================================================
# Access Control Models
# =============================================================================


class AccessCheckRequest(BaseModel):
    """Request for checking token access."""

    rpc_url: str = ""  # Empty = use backend's configured RPC (Helius)
    owner: str
    mint: str
    minimum: float = 50000


class AccessCheckResponse(BaseModel):
    """Response from access check."""

    allowed: bool
    reason: str
    balance: float | None = None


# =============================================================================
# Fleet Models
# =============================================================================


class DeviceHealth(BaseModel):
    """Device health metrics."""

    cpu_percent: float | None = None
    cpu_temperature: float | None = None
    memory_percent: float | None = None
    memory_used_mb: float | None = None
    memory_total_mb: float | None = None
    battery_percent: float | None = None
    battery_charging: bool | None = None
    disk_percent: float | None = None
    network_connected: bool | None = None
    network_type: str | None = None
    uptime_seconds: int | None = None
    temperature: float | None = None
    custom_metrics: dict[str, Any] = Field(default_factory=dict)
    last_updated: str | None = None


class DeviceInfo(BaseModel):
    """Device information."""

    id: str
    name: str | None = None
    custom_name: str | None = None
    display_name: str | None = None
    group_id: str | None = None
    group_name: str | None = None
    proof_count: int = 0
    task_count: int = 0
    last_activity: str | None = None
    first_activity: str | None = None
    status: str = "unknown"
    health: DeviceHealth | None = None


class DeviceDetailResponse(BaseModel):
    """Detailed device information."""

    id: str
    name: str | None = None
    custom_name: str | None = None
    display_name: str | None = None
    group_id: str | None = None
    group_name: str | None = None
    proof_count: int = 0
    task_count: int = 0
    last_activity: str | None = None
    first_activity: str | None = None
    status: str = "unknown"
    health: DeviceHealth | None = None
    recent_logs: list[dict[str, Any]] = Field(default_factory=list)
    task_history: list[str] = Field(default_factory=list)


class DeviceGroup(BaseModel):
    """Device group information."""

    id: str
    name: str
    description: str | None = None
    device_count: int = 0
    device_ids: list[str] = Field(default_factory=list)
    created_at: str | None = None


class FleetSummary(BaseModel):
    """Fleet summary statistics."""

    total_devices: int = 0
    active_devices: int = 0
    warning_devices: int = 0
    offline_devices: int = 0
    total_proofs: int = 0
    total_tasks: int = 0
    total_groups: int = 0


class FleetOverviewResponse(BaseModel):
    """Response from fleet overview."""

    devices: list[DeviceInfo] = Field(default_factory=list)
    groups: list[DeviceGroup] = Field(default_factory=list)
    summary: FleetSummary = Field(default_factory=FleetSummary)


class GroupListResponse(BaseModel):
    """Response from listing groups."""

    groups: list[DeviceGroup]
    total: int


class HealthReportResponse(BaseModel):
    """Response from reporting health."""

    success: bool
    device_id: str
    health: DeviceHealth | None = None


class RenameDeviceResponse(BaseModel):
    """Response from renaming a device."""

    success: bool
    device_id: str
    name: str


class CreateGroupResponse(BaseModel):
    """Response from creating a group."""

    success: bool
    group: DeviceGroup


class AssignDevicesResponse(BaseModel):
    """Response from assigning devices to a group."""

    success: bool
    group_id: str
    assigned: list[str] = Field(default_factory=list)


class DeleteGroupResponse(BaseModel):
    """Response from deleting a group."""

    success: bool
    group_id: str
    devices_unassigned: int = 0


class DeleteDeviceResponse(BaseModel):
    """Response from deleting a device."""

    success: bool
    device_id: str


class DeviceOrderItem(BaseModel):
    """Single device order specification."""

    device_id: str
    sort_order: int


class ReorderDevicesResponse(BaseModel):
    """Response from reordering devices."""

    success: bool
    updated: int = 0


# =============================================================================
# Health Check
# =============================================================================


class HealthResponse(BaseModel):
    """Response from health check."""

    ok: bool
    service: str = "acto"
    version: str = ""

