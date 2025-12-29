# ACTO Fleet - Database Models
# All fields are optional where appropriate to support varying device capabilities

from __future__ import annotations

from sqlalchemy import String, Integer, Float, Boolean, Text, Index, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from acto.registry.models import Base


class DeviceRecord(Base):
    """
    Database model for device custom data.
    Stores user-defined names and metadata for devices.
    Device ID is derived from robot_id in proofs.
    """
    __tablename__ = "fleet_devices"

    # Primary key is the device/robot ID from proofs
    device_id: Mapped[str] = mapped_column(String(256), primary_key=True)
    
    # User who owns this device (from JWT wallet)
    user_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    
    # Custom name set by user (optional)
    custom_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    
    # Description/notes (optional)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Device type/category (optional)
    device_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    
    # Current group assignment (optional)
    group_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("fleet_groups.group_id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Sort order for manual ordering (lower = first, default 0)
    sort_order: Mapped[int | None] = mapped_column(Integer, default=0, nullable=True)
    
    # Hidden flag for soft-delete (device still has proofs but shouldn't appear in fleet)
    # Using Integer for cross-database compatibility (0=visible, 1=hidden)
    is_hidden: Mapped[int | None] = mapped_column(Integer, default=0, nullable=True)
    
    # Timestamps
    created_at: Mapped[str] = mapped_column(String(64), index=True)
    updated_at: Mapped[str] = mapped_column(String(64))
    
    # Relationship to group
    group: Mapped["DeviceGroupRecord | None"] = relationship("DeviceGroupRecord", back_populates="devices")
    
    # Relationship to health records
    health_records: Mapped[list["DeviceHealthRecord"]] = relationship(
        "DeviceHealthRecord", 
        back_populates="device",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_fleet_device_user", "user_id"),
        Index("idx_fleet_device_group", "group_id"),
    )


class DeviceGroupRecord(Base):
    """
    Database model for device groups.
    Groups allow organizing devices by location, function, etc.
    """
    __tablename__ = "fleet_groups"

    group_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    
    # User who owns this group
    user_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    
    # Group name (required)
    name: Mapped[str] = mapped_column(String(256))
    
    # Description (optional)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Group color for UI (optional, hex code)
    color: Mapped[str | None] = mapped_column(String(7), nullable=True)
    
    # Group icon (optional, icon name)
    icon: Mapped[str | None] = mapped_column(String(64), nullable=True)
    
    # Timestamps
    created_at: Mapped[str] = mapped_column(String(64), index=True)
    updated_at: Mapped[str] = mapped_column(String(64))
    
    # Relationship to devices
    devices: Mapped[list["DeviceRecord"]] = relationship(
        "DeviceRecord", 
        back_populates="group",
        passive_deletes=True
    )

    __table_args__ = (
        Index("idx_fleet_group_user", "user_id"),
    )


class DeviceGroupMemberRecord(Base):
    """
    Junction table for many-to-many device-group relationships.
    This allows a device to potentially be in multiple groups in the future.
    Currently not used but provides flexibility.
    """
    __tablename__ = "fleet_group_members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(String(256), ForeignKey("fleet_devices.device_id", ondelete="CASCADE"), index=True)
    group_id: Mapped[str] = mapped_column(String(64), ForeignKey("fleet_groups.group_id", ondelete="CASCADE"), index=True)
    added_at: Mapped[str] = mapped_column(String(64))

    __table_args__ = (
        Index("idx_fleet_member_device_group", "device_id", "group_id", unique=True),
    )


class DeviceHealthRecord(Base):
    """
    Database model for device health metrics.
    All metrics are optional since not all devices support all sensors.
    Stores historical health data with timestamps.
    """
    __tablename__ = "fleet_health"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Device reference
    device_id: Mapped[str] = mapped_column(
        String(256), 
        ForeignKey("fleet_devices.device_id", ondelete="CASCADE"), 
        index=True
    )
    
    # CPU metrics (optional)
    cpu_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    cpu_temperature: Mapped[float | None] = mapped_column(Float, nullable=True)  # Celsius
    
    # Memory metrics (optional)
    memory_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    memory_used_mb: Mapped[int | None] = mapped_column(Integer, nullable=True)
    memory_total_mb: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Battery metrics (optional)
    battery_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    battery_charging: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    battery_voltage: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Disk metrics (optional)
    disk_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    disk_used_gb: Mapped[float | None] = mapped_column(Float, nullable=True)
    disk_total_gb: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Network metrics (optional)
    network_connected: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    network_signal_strength: Mapped[int | None] = mapped_column(Integer, nullable=True)  # dBm or percentage
    network_type: Mapped[str | None] = mapped_column(String(32), nullable=True)  # wifi, ethernet, cellular, etc.
    
    # System metrics (optional)
    uptime_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    load_average: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # General temperature (optional, for robots with external temp sensors)
    temperature: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Custom metrics as JSON (optional, for device-specific data)
    custom_metrics: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Timestamp
    recorded_at: Mapped[str] = mapped_column(String(64), index=True)
    
    # Relationship to device
    device: Mapped["DeviceRecord"] = relationship("DeviceRecord", back_populates="health_records")

    __table_args__ = (
        Index("idx_fleet_health_device_time", "device_id", "recorded_at"),
    )

