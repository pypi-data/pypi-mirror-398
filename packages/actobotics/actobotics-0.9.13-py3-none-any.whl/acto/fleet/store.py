# ACTO Fleet Store
# Database operations for fleet management with full persistence

from __future__ import annotations

import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import text

from acto.config.settings import Settings
from acto.registry.db import make_engine, make_session_factory
from acto.registry.models import Base

from .models import DeviceRecord, DeviceGroupRecord, DeviceHealthRecord


class FleetStore:
    """
    Database-backed fleet store for device and group management.
    All health/capability data is optional to support various device types.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self.engine = make_engine(settings)
        self.Session = make_session_factory(self.engine)
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        """Ensure database tables exist and apply migrations."""
        # Import models to ensure they're registered with Base
        from .models import DeviceRecord, DeviceGroupRecord, DeviceHealthRecord, DeviceGroupMemberRecord  # noqa: F401
        Base.metadata.create_all(self.engine)
        
        # Migrate: Add sort_order column if it doesn't exist
        self._migrate_add_sort_order()

    def _migrate_add_sort_order(self) -> None:
        """Add new columns to fleet_devices if they don't exist."""
        # First check if the table exists at all
        with self.Session() as session:
            try:
                session.execute(text("SELECT 1 FROM fleet_devices LIMIT 1"))
            except Exception:
                session.rollback()
                # Table doesn't exist yet, will be created by create_all
                return
        
        # Add sort_order column if it doesn't exist
        with self.Session() as session:
            try:
                session.execute(text("SELECT sort_order FROM fleet_devices LIMIT 1"))
            except Exception:
                session.rollback()
                try:
                    session.execute(text("ALTER TABLE fleet_devices ADD COLUMN sort_order INTEGER DEFAULT 0"))
                    session.commit()
                except Exception:
                    session.rollback()
        
        # Add is_hidden column if it doesn't exist
        with self.Session() as session:
            try:
                session.execute(text("SELECT is_hidden FROM fleet_devices LIMIT 1"))
            except Exception:
                session.rollback()
                try:
                    # Use INTEGER for cross-database compatibility (SQLite, PostgreSQL)
                    session.execute(text("ALTER TABLE fleet_devices ADD COLUMN is_hidden INTEGER DEFAULT 0"))
                    session.commit()
                except Exception:
                    session.rollback()

    # ============================================================
    # Device Operations
    # ============================================================

    def get_device(self, device_id: str, user_id: str | None = None) -> dict[str, Any] | None:
        """Get device data by ID."""
        with self.Session() as session:
            query = session.query(DeviceRecord).filter(DeviceRecord.device_id == device_id)
            if user_id:
                query = query.filter(DeviceRecord.user_id == user_id)
            record = query.first()
            
            if record:
                return self._device_to_dict(record)
        return None

    def get_or_create_device(self, device_id: str, user_id: str | None = None) -> dict[str, Any]:
        """Get device data or create a new record if it doesn't exist."""
        existing = self.get_device(device_id, user_id)
        if existing:
            return existing
        
        now = datetime.now(timezone.utc).isoformat()
        
        with self.Session() as session:
            record = DeviceRecord(
                device_id=device_id,
                user_id=user_id,
                custom_name=None,
                description=None,
                device_type=None,
                group_id=None,
                created_at=now,
                updated_at=now,
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return self._device_to_dict(record)

    def update_device(
        self,
        device_id: str,
        user_id: str | None = None,
        custom_name: str | None = None,
        description: str | None = None,
        device_type: str | None = None,
        group_id: str | None = None,
    ) -> dict[str, Any] | None:
        """Update device data. Creates record if it doesn't exist."""
        now = datetime.now(timezone.utc).isoformat()
        
        with self.Session() as session:
            query = session.query(DeviceRecord).filter(DeviceRecord.device_id == device_id)
            if user_id:
                query = query.filter(DeviceRecord.user_id == user_id)
            record = query.first()
            
            if not record:
                # Create new record
                record = DeviceRecord(
                    device_id=device_id,
                    user_id=user_id,
                    custom_name=custom_name,
                    description=description,
                    device_type=device_type,
                    group_id=group_id,
                    created_at=now,
                    updated_at=now,
                )
                session.add(record)
            else:
                # Update existing record
                if custom_name is not None:
                    record.custom_name = custom_name
                if description is not None:
                    record.description = description
                if device_type is not None:
                    record.device_type = device_type
                if group_id is not None:
                    # Allow setting to None to remove from group
                    record.group_id = group_id if group_id != "" else None
                record.updated_at = now
            
            session.commit()
            session.refresh(record)
            return self._device_to_dict(record)

    def rename_device(self, device_id: str, name: str, user_id: str | None = None) -> dict[str, Any] | None:
        """Rename a device with a custom name."""
        return self.update_device(device_id, user_id=user_id, custom_name=name)

    def list_devices(self, user_id: str | None = None, group_id: str | None = None) -> list[dict[str, Any]]:
        """List all devices, optionally filtered by user or group."""
        with self.Session() as session:
            query = session.query(DeviceRecord)
            if user_id:
                query = query.filter(DeviceRecord.user_id == user_id)
            if group_id:
                query = query.filter(DeviceRecord.group_id == group_id)
            
            records = query.order_by(DeviceRecord.updated_at.desc()).all()
            return [self._device_to_dict(r) for r in records]

    def delete_device(self, device_id: str, user_id: str | None = None) -> dict[str, Any]:
        """
        Hide a device from the fleet list (soft delete).
        The device's proofs are preserved, but it won't appear in the fleet.
        """
        now = datetime.now(timezone.utc).isoformat()
        
        with self.Session() as session:
            query = session.query(DeviceRecord).filter(DeviceRecord.device_id == device_id)
            if user_id:
                query = query.filter(DeviceRecord.user_id == user_id)
            record = query.first()
            
            if not record:
                # Device might not have a record yet - create one and mark as hidden
                record = DeviceRecord(
                    device_id=device_id,
                    user_id=user_id,
                    is_hidden=1,
                    created_at=now,
                    updated_at=now,
                )
                session.add(record)
            else:
                record.is_hidden = 1
                record.updated_at = now
            
            session.commit()
            return {"success": True, "device_id": device_id}

    def _device_to_dict(self, record: DeviceRecord) -> dict[str, Any]:
        """Convert device record to dictionary."""
        # Handle sort_order safely (may be None or missing in older records)
        sort_order = getattr(record, "sort_order", None)
        if sort_order is None:
            sort_order = 0
        
        # Handle is_hidden safely (stored as int: 0=visible, 1=hidden)
        is_hidden_val = getattr(record, "is_hidden", 0)
        is_hidden = bool(is_hidden_val) if is_hidden_val is not None else False
        
        return {
            "device_id": record.device_id,
            "user_id": record.user_id,
            "custom_name": record.custom_name,
            "description": record.description,
            "device_type": record.device_type,
            "group_id": record.group_id,
            "sort_order": sort_order,
            "is_hidden": is_hidden,
            "created_at": record.created_at,
            "updated_at": record.updated_at,
        }

    def update_device_order(
        self,
        device_orders: list[dict[str, Any]],
        user_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Update the sort order of multiple devices.
        
        Args:
            device_orders: List of {"device_id": str, "sort_order": int}
            user_id: Optional user ID for ownership verification
            
        Returns:
            Success status and updated count
        """
        now = datetime.now(timezone.utc).isoformat()
        updated = 0
        
        with self.Session() as session:
            for item in device_orders:
                device_id = item.get("device_id")
                sort_order = item.get("sort_order", 0)
                
                if not device_id:
                    continue
                
                query = session.query(DeviceRecord).filter(DeviceRecord.device_id == device_id)
                if user_id:
                    query = query.filter(DeviceRecord.user_id == user_id)
                
                device = query.first()
                if device:
                    device.sort_order = sort_order
                    device.updated_at = now
                    updated += 1
            
            session.commit()
        
        return {"success": True, "updated": updated}

    # ============================================================
    # Group Operations
    # ============================================================

    def create_group(
        self,
        name: str,
        user_id: str | None = None,
        description: str | None = None,
        color: str | None = None,
        icon: str | None = None,
    ) -> dict[str, Any]:
        """Create a new device group."""
        group_id = f"grp_{secrets.token_urlsafe(12)}"
        now = datetime.now(timezone.utc).isoformat()
        
        with self.Session() as session:
            record = DeviceGroupRecord(
                group_id=group_id,
                user_id=user_id,
                name=name,
                description=description,
                color=color,
                icon=icon,
                created_at=now,
                updated_at=now,
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return self._group_to_dict(record)

    def get_group(self, group_id: str, user_id: str | None = None) -> dict[str, Any] | None:
        """Get group data by ID."""
        with self.Session() as session:
            query = session.query(DeviceGroupRecord).filter(DeviceGroupRecord.group_id == group_id)
            if user_id:
                query = query.filter(DeviceGroupRecord.user_id == user_id)
            record = query.first()
            
            if record:
                return self._group_to_dict(record, include_devices=True)
        return None

    def update_group(
        self,
        group_id: str,
        user_id: str | None = None,
        name: str | None = None,
        description: str | None = None,
        color: str | None = None,
        icon: str | None = None,
    ) -> dict[str, Any] | None:
        """Update group data."""
        now = datetime.now(timezone.utc).isoformat()
        
        with self.Session() as session:
            query = session.query(DeviceGroupRecord).filter(DeviceGroupRecord.group_id == group_id)
            if user_id:
                query = query.filter(DeviceGroupRecord.user_id == user_id)
            record = query.first()
            
            if not record:
                return None
            
            if name is not None:
                record.name = name
            if description is not None:
                record.description = description
            if color is not None:
                record.color = color
            if icon is not None:
                record.icon = icon
            record.updated_at = now
            
            session.commit()
            session.refresh(record)
            return self._group_to_dict(record)

    def delete_group(self, group_id: str, user_id: str | None = None) -> dict[str, Any]:
        """Delete a group. Returns info about unassigned devices."""
        with self.Session() as session:
            query = session.query(DeviceGroupRecord).filter(DeviceGroupRecord.group_id == group_id)
            if user_id:
                query = query.filter(DeviceGroupRecord.user_id == user_id)
            record = query.first()
            
            if not record:
                return {"success": False, "group_id": group_id, "devices_unassigned": 0}
            
            # Count devices in group
            device_count = session.query(DeviceRecord).filter(DeviceRecord.group_id == group_id).count()
            
            # Delete group (devices will have group_id set to NULL via ON DELETE SET NULL)
            session.delete(record)
            session.commit()
            
            return {
                "success": True,
                "group_id": group_id,
                "devices_unassigned": device_count,
            }

    def list_groups(self, user_id: str | None = None) -> list[dict[str, Any]]:
        """List all groups, optionally filtered by user."""
        with self.Session() as session:
            query = session.query(DeviceGroupRecord)
            if user_id:
                query = query.filter(DeviceGroupRecord.user_id == user_id)
            
            records = query.order_by(DeviceGroupRecord.name).all()
            return [self._group_to_dict(r, include_device_count=True, session=session) for r in records]

    def assign_devices_to_group(
        self,
        group_id: str,
        device_ids: list[str],
        user_id: str | None = None,
    ) -> dict[str, Any]:
        """Assign devices to a group."""
        now = datetime.now(timezone.utc).isoformat()
        
        with self.Session() as session:
            # Verify group exists
            query = session.query(DeviceGroupRecord).filter(DeviceGroupRecord.group_id == group_id)
            if user_id:
                query = query.filter(DeviceGroupRecord.user_id == user_id)
            group = query.first()
            
            if not group:
                return {"success": False, "error": "Group not found", "assigned": []}
            
            assigned = []
            for device_id in device_ids:
                # Get or create device record
                device = session.query(DeviceRecord).filter(DeviceRecord.device_id == device_id).first()
                
                if not device:
                    # Create device record
                    device = DeviceRecord(
                        device_id=device_id,
                        user_id=user_id,
                        group_id=group_id,
                        created_at=now,
                        updated_at=now,
                    )
                    session.add(device)
                else:
                    device.group_id = group_id
                    device.updated_at = now
                
                assigned.append(device_id)
            
            group.updated_at = now
            session.commit()
            
            return {
                "success": True,
                "group_id": group_id,
                "assigned": assigned,
            }

    def unassign_devices_from_group(
        self,
        group_id: str,
        device_ids: list[str],
        user_id: str | None = None,
    ) -> dict[str, Any]:
        """Remove devices from a group."""
        now = datetime.now(timezone.utc).isoformat()
        
        with self.Session() as session:
            # Verify group exists
            query = session.query(DeviceGroupRecord).filter(DeviceGroupRecord.group_id == group_id)
            if user_id:
                query = query.filter(DeviceGroupRecord.user_id == user_id)
            group = query.first()
            
            if not group:
                return {"success": False, "error": "Group not found", "unassigned": []}
            
            unassigned = []
            for device_id in device_ids:
                device = session.query(DeviceRecord).filter(
                    DeviceRecord.device_id == device_id,
                    DeviceRecord.group_id == group_id,
                ).first()
                
                if device:
                    device.group_id = None
                    device.updated_at = now
                    unassigned.append(device_id)
            
            group.updated_at = now
            session.commit()
            
            return {
                "success": True,
                "group_id": group_id,
                "unassigned": unassigned,
            }

    def _group_to_dict(
        self,
        record: DeviceGroupRecord,
        include_devices: bool = False,
        include_device_count: bool = False,
        session=None,
    ) -> dict[str, Any]:
        """Convert group record to dictionary."""
        result = {
            "id": record.group_id,
            "group_id": record.group_id,
            "user_id": record.user_id,
            "name": record.name,
            "description": record.description,
            "color": record.color,
            "icon": record.icon,
            "created_at": record.created_at,
            "updated_at": record.updated_at,
        }
        
        if include_devices:
            result["device_ids"] = [d.device_id for d in record.devices] if record.devices else []
        
        if include_device_count and session:
            count = session.query(DeviceRecord).filter(DeviceRecord.group_id == record.group_id).count()
            result["device_count"] = count
            result["device_ids"] = []  # Empty list for compatibility
        
        return result

    # ============================================================
    # Health Operations
    # ============================================================

    def record_health(
        self,
        device_id: str,
        user_id: str | None = None,
        cpu_percent: float | None = None,
        cpu_temperature: float | None = None,
        memory_percent: float | None = None,
        memory_used_mb: int | None = None,
        memory_total_mb: int | None = None,
        battery_percent: float | None = None,
        battery_charging: bool | None = None,
        battery_voltage: float | None = None,
        disk_percent: float | None = None,
        disk_used_gb: float | None = None,
        disk_total_gb: float | None = None,
        network_connected: bool | None = None,
        network_signal_strength: int | None = None,
        network_type: str | None = None,
        uptime_seconds: int | None = None,
        load_average: float | None = None,
        temperature: float | None = None,
        custom_metrics: dict | None = None,
    ) -> dict[str, Any]:
        """
        Record health metrics for a device.
        All parameters are optional - only provided metrics will be stored.
        """
        now = datetime.now(timezone.utc).isoformat()
        
        with self.Session() as session:
            # Ensure device record exists
            device = session.query(DeviceRecord).filter(DeviceRecord.device_id == device_id).first()
            if not device:
                device = DeviceRecord(
                    device_id=device_id,
                    user_id=user_id,
                    created_at=now,
                    updated_at=now,
                )
                session.add(device)
                session.flush()
            
            # Create health record
            health = DeviceHealthRecord(
                device_id=device_id,
                cpu_percent=cpu_percent,
                cpu_temperature=cpu_temperature,
                memory_percent=memory_percent,
                memory_used_mb=memory_used_mb,
                memory_total_mb=memory_total_mb,
                battery_percent=battery_percent,
                battery_charging=battery_charging,
                battery_voltage=battery_voltage,
                disk_percent=disk_percent,
                disk_used_gb=disk_used_gb,
                disk_total_gb=disk_total_gb,
                network_connected=network_connected,
                network_signal_strength=network_signal_strength,
                network_type=network_type,
                uptime_seconds=uptime_seconds,
                load_average=load_average,
                temperature=temperature,
                custom_metrics=json.dumps(custom_metrics) if custom_metrics else None,
                recorded_at=now,
            )
            session.add(health)
            session.commit()
            session.refresh(health)
            
            return self._health_to_dict(health)

    def get_latest_health(self, device_id: str) -> dict[str, Any] | None:
        """Get the most recent health record for a device."""
        with self.Session() as session:
            record = session.query(DeviceHealthRecord).filter(
                DeviceHealthRecord.device_id == device_id
            ).order_by(DeviceHealthRecord.recorded_at.desc()).first()
            
            if record:
                return self._health_to_dict(record)
        return None

    def get_health_history(
        self,
        device_id: str,
        hours: int = 24,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get health history for a device within the specified time range."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        cutoff_str = cutoff.isoformat()
        
        with self.Session() as session:
            records = session.query(DeviceHealthRecord).filter(
                DeviceHealthRecord.device_id == device_id,
                DeviceHealthRecord.recorded_at >= cutoff_str,
            ).order_by(DeviceHealthRecord.recorded_at.desc()).limit(limit).all()
            
            return [self._health_to_dict(r) for r in records]

    def cleanup_old_health_records(self, days: int = 30) -> int:
        """Delete health records older than specified days. Returns count deleted."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        cutoff_str = cutoff.isoformat()
        
        with self.Session() as session:
            result = session.query(DeviceHealthRecord).filter(
                DeviceHealthRecord.recorded_at < cutoff_str
            ).delete()
            session.commit()
            return result

    def _health_to_dict(self, record: DeviceHealthRecord) -> dict[str, Any]:
        """Convert health record to dictionary."""
        return {
            "id": record.id,
            "device_id": record.device_id,
            "cpu_percent": record.cpu_percent,
            "cpu_temperature": record.cpu_temperature,
            "memory_percent": record.memory_percent,
            "memory_used_mb": record.memory_used_mb,
            "memory_total_mb": record.memory_total_mb,
            "battery_percent": record.battery_percent,
            "battery_charging": record.battery_charging,
            "battery_voltage": record.battery_voltage,
            "disk_percent": record.disk_percent,
            "disk_used_gb": record.disk_used_gb,
            "disk_total_gb": record.disk_total_gb,
            "network_connected": record.network_connected,
            "network_signal_strength": record.network_signal_strength,
            "network_type": record.network_type,
            "uptime_seconds": record.uptime_seconds,
            "load_average": record.load_average,
            "temperature": record.temperature,
            "custom_metrics": json.loads(record.custom_metrics) if record.custom_metrics else None,
            "recorded_at": record.recorded_at,
            "last_updated": record.recorded_at,  # Alias for frontend compatibility
        }

    # ============================================================
    # Aggregated Fleet Data
    # ============================================================

    def get_fleet_data(
        self,
        user_id: str | None,
        all_proofs: list[dict],
    ) -> dict[str, Any]:
        """
        Get complete fleet data combining proof data with stored device/group data.
        This merges device info from proofs with custom names and groups from DB.
        
        Note: For optimized access, use get_fleet_data_optimized() instead.
        """
        # Build device map from proofs
        devices_map: dict[str, dict] = {}
        total_proofs = 0
        all_tasks = set()
        
        for proof in all_proofs:
            robot_id = proof.get("robot_id", "unknown")
            if robot_id == "unknown":
                continue
            
            if robot_id not in devices_map:
                devices_map[robot_id] = {
                    "id": robot_id,
                    "proof_count": 0,
                    "task_ids": set(),
                    "last_activity": None,
                    "first_activity": None,
                }
            
            device = devices_map[robot_id]
            device["proof_count"] += 1
            total_proofs += 1
            
            task_id = proof.get("task_id")
            if task_id:
                device["task_ids"].add(task_id)
                all_tasks.add(task_id)
            
            created_at = proof.get("created_at")
            if created_at:
                if not device["last_activity"] or created_at > device["last_activity"]:
                    device["last_activity"] = created_at
                if not device["first_activity"] or created_at < device["first_activity"]:
                    device["first_activity"] = created_at
        
        # Get stored device data and groups
        stored_devices = {d["device_id"]: d for d in self.list_devices(user_id)}
        groups_list = self.list_groups(user_id)
        groups_map = {g["group_id"]: g for g in groups_list}
        
        # Build final device list
        device_list = []
        now = datetime.now(timezone.utc)
        one_hour_ago = now - timedelta(hours=1)
        one_day_ago = now - timedelta(hours=24)
        
        active_count = 0
        warning_count = 0
        
        for device_id, device_data in devices_map.items():
            stored = stored_devices.get(device_id, {})
            
            # Skip hidden (soft-deleted) devices
            if stored.get("is_hidden"):
                continue
            
            # Get default name
            default_name = device_id.replace("-", " ").replace("_", " ").title()
            custom_name = stored.get("custom_name")
            
            # Get group info
            group_id = stored.get("group_id")
            group_name = None
            if group_id and group_id in groups_map:
                group_name = groups_map[group_id].get("name")
            
            # Get health data
            health = self.get_latest_health(device_id)
            
            # Calculate status
            status = "offline"
            if device_data["last_activity"]:
                try:
                    last_dt = datetime.fromisoformat(device_data["last_activity"].replace("Z", "+00:00"))
                    if last_dt > one_hour_ago:
                        status = "online"
                        active_count += 1
                    elif last_dt > one_day_ago:
                        status = "warning"
                        warning_count += 1
                except (ValueError, TypeError):
                    pass
            
            device_list.append({
                "id": device_id,
                "name": custom_name or default_name,
                "custom_name": custom_name,
                "description": stored.get("description"),
                "device_type": stored.get("device_type"),
                "group_id": group_id,
                "group_name": group_name,
                "proof_count": device_data["proof_count"],
                "task_count": len(device_data["task_ids"]),
                "last_activity": device_data["last_activity"],
                "first_activity": device_data["first_activity"],
                "status": status,
                "health": health,
            })
        
        # Sort by last activity
        device_list.sort(key=lambda d: d["last_activity"] or "", reverse=True)
        
        return {
            "devices": device_list,
            "groups": groups_list,
            "summary": {
                "total_devices": len(device_list),
                "active_devices": active_count,
                "warning_devices": warning_count,
                "offline_devices": len(device_list) - active_count - warning_count,
                "total_proofs": total_proofs,
                "total_tasks": len(all_tasks),
                "total_groups": len(groups_list),
            }
        }

    def get_fleet_data_optimized(
        self,
        user_id: str | None,
        aggregated_data: dict[str, Any],
        registry: Any,
    ) -> dict[str, Any]:
        """
        Get complete fleet data using pre-aggregated SQL data.
        This is much more efficient than get_fleet_data() for large datasets.
        
        Args:
            user_id: User ID for filtering stored device data
            aggregated_data: Dict containing:
                - robot_ids: List of unique robot IDs
                - proofs_by_robot: Dict mapping robot_id to proof count
            registry: ProofRegistry instance for additional queries
        """
        robot_ids = aggregated_data.get("robot_ids", [])
        proofs_by_robot = aggregated_data.get("proofs_by_robot", {})
        
        # Get stored device data and groups
        stored_devices = {d["device_id"]: d for d in self.list_devices(user_id)}
        groups_list = self.list_groups(user_id)
        groups_map = {g["group_id"]: g for g in groups_list}
        
        # Calculate total proofs and tasks using SQL aggregations
        total_proofs = sum(proofs_by_robot.values())
        task_counts = registry.count_by_task()
        all_tasks = list(task_counts.keys())
        
        # Build final device list
        device_list = []
        now = datetime.now(timezone.utc)
        one_hour_ago = now - timedelta(hours=1)
        one_day_ago = now - timedelta(hours=24)
        
        active_count = 0
        warning_count = 0
        
        for device_id in robot_ids:
            if device_id == "unknown":
                continue
            
            stored = stored_devices.get(device_id, {})
            
            # Skip hidden (soft-deleted) devices
            if stored.get("is_hidden"):
                continue
            
            # Get device stats from registry (uses SQL aggregation)
            device_stats = registry.get_device_stats(device_id)
            
            # Get default name
            default_name = device_id.replace("-", " ").replace("_", " ").title()
            custom_name = stored.get("custom_name")
            
            # Get group info
            group_id = stored.get("group_id")
            group_name = None
            if group_id and group_id in groups_map:
                group_name = groups_map[group_id].get("name")
            
            # Get health data
            health = self.get_latest_health(device_id)
            
            # Calculate status based on last activity
            status = "offline"
            last_activity = device_stats.get("last_activity")
            first_activity = device_stats.get("first_activity")
            
            if last_activity:
                try:
                    last_dt = datetime.fromisoformat(last_activity.replace("Z", "+00:00"))
                    if last_dt > one_hour_ago:
                        status = "online"
                        active_count += 1
                    elif last_dt > one_day_ago:
                        status = "warning"
                        warning_count += 1
                except (ValueError, TypeError):
                    pass
            
            device_list.append({
                "id": device_id,
                "name": custom_name or default_name,
                "custom_name": custom_name,
                "description": stored.get("description"),
                "device_type": stored.get("device_type"),
                "group_id": group_id,
                "group_name": group_name,
                "proof_count": device_stats.get("proof_count", 0),
                "task_count": device_stats.get("task_count", 0),
                "last_activity": last_activity,
                "first_activity": first_activity,
                "status": status,
                "health": health,
            })
        
        # Sort by last activity
        device_list.sort(key=lambda d: d["last_activity"] or "", reverse=True)
        
        return {
            "devices": device_list,
            "groups": groups_list,
            "summary": {
                "total_devices": len(device_list),
                "active_devices": active_count,
                "warning_devices": warning_count,
                "offline_devices": len(device_list) - active_count - warning_count,
                "total_proofs": total_proofs,
                "total_tasks": len(all_tasks),
                "total_groups": len(groups_list),
            }
        }

