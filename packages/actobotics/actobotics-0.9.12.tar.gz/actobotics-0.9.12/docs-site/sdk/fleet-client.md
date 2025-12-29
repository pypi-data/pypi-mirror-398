# FleetClient

The `FleetClient` provides methods for managing your robot fleet.

## Accessing the Fleet Client

The fleet client is available as a sub-client on `ACTOClient`:

```python
from acto.client import ACTOClient

client = ACTOClient(api_key="...", wallet_address="...")

# Access fleet methods
fleet = client.fleet.get_overview()
```

## Methods

### `get_overview()`

Get a complete overview of your fleet including devices, groups, and summary statistics.

```python
fleet = client.fleet.get_overview()

print(f"Total devices: {fleet.summary.total_devices}")
print(f"Active devices: {fleet.summary.active_devices}")
print(f"Total proofs: {fleet.summary.total_proofs}")

# List all devices
for device in fleet.devices:
    print(f"- {device.id}: {device.status} ({device.proof_count} proofs)")

# List all groups
for group in fleet.groups:
    print(f"- {group.name}: {group.device_count} devices")
```

**Returns:** `FleetOverviewResponse`

---

### `get_device(device_id)`

Get detailed information about a specific device.

```python
device = client.fleet.get_device("robot-alpha-01")

print(f"Name: {device.display_name}")
print(f"Status: {device.status}")
print(f"Proofs: {device.proof_count}")
print(f"Tasks: {device.task_count}")
print(f"First activity: {device.first_activity}")
print(f"Last activity: {device.last_activity}")

# Recent activity logs
for log in device.recent_logs:
    print(f"  [{log.level}] {log.message}")

# Task history
print(f"Tasks performed: {device.task_history}")
```

**Parameters:**
- `device_id` (`str`) - The device ID (robot_id)

**Returns:** `DeviceDetailResponse`

---

### `rename_device(device_id, name)`

Set a custom name for a device.

```python
result = client.fleet.rename_device("robot-alpha-01", "Warehouse Bot 1")
print(f"Renamed to: {result.name}")
```

**Parameters:**
- `device_id` (`str`) - The device ID
- `name` (`str`) - New custom name

**Returns:** `RenameDeviceResponse`

---

### `delete_device(device_id)`

Delete (hide) a device from the fleet. This is a soft delete - the device's proofs are preserved, but it won't appear in the fleet list.

```python
result = client.fleet.delete_device("robot-alpha-01")
print(f"Deleted: {result.device_id}")
```

**Parameters:**
- `device_id` (`str`) - The device ID to delete

**Returns:** `DeleteDeviceResponse`

> **Note:** Deleted devices can't be restored via the SDK. Contact support if you need to restore a device.

---

### `reorder_devices(device_orders)`

Update the sort order of multiple devices. This allows custom ordering in the fleet list.

```python
result = client.fleet.reorder_devices([
    {"device_id": "robot-alpha-01", "sort_order": 0},
    {"device_id": "robot-beta-02", "sort_order": 1},
    {"device_id": "robot-gamma-03", "sort_order": 2},
])
print(f"Updated {result.updated} devices")
```

**Parameters:**
- `device_orders` (`list[dict]`) - List of dicts with `device_id` and `sort_order`

**Returns:** `ReorderDevicesResponse`

> **Tip:** In the dashboard, you can drag devices up/down to reorder them visually.

---

### `report_health(device_id, **metrics)`

Report health metrics for a device. All parameters are optional - only send metrics your device supports.

```python
client.fleet.report_health(
    "robot-alpha-01",
    cpu_percent=45.2,
    cpu_temperature=52.0,
    memory_percent=68.0,
    memory_used_mb=2048,
    memory_total_mb=4096,
    battery_percent=85.0,
    battery_charging=True,
    disk_percent=42.0,
    network_connected=True,
    network_type="wifi",
    uptime_seconds=86400,
    temperature=42.5,
    custom_metrics={
        "motor_temp": 38.0,
        "sensor_status": "ok",
        "arm_position": [0.5, 0.2, 0.8]
    }
)
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `device_id` | `str` | The device ID |
| `cpu_percent` | `float` | CPU usage (0-100) |
| `cpu_temperature` | `float` | CPU temperature (°C) |
| `memory_percent` | `float` | Memory usage (0-100) |
| `memory_used_mb` | `float` | Memory used (MB) |
| `memory_total_mb` | `float` | Total memory (MB) |
| `battery_percent` | `float` | Battery level (0-100) |
| `battery_charging` | `bool` | Charging status |
| `disk_percent` | `float` | Disk usage (0-100) |
| `network_connected` | `bool` | Network status |
| `network_type` | `str` | wifi/ethernet/cellular |
| `uptime_seconds` | `int` | Uptime in seconds |
| `temperature` | `float` | Ambient temperature |
| `custom_metrics` | `dict` | Custom key-value metrics |

**Returns:** `HealthReportResponse`

---

### `get_health(device_id)`

Get the latest health metrics for a device.

```python
health = client.fleet.get_health("robot-alpha-01")

print(f"CPU: {health.cpu_percent}%")
print(f"Memory: {health.memory_percent}%")
print(f"Battery: {health.battery_percent}%")
print(f"Last updated: {health.last_updated}")
```

**Parameters:**
- `device_id` (`str`) - The device ID

**Returns:** `DeviceHealth`

---

### `list_groups()`

List all device groups.

```python
groups = client.fleet.list_groups()

for group in groups.groups:
    print(f"- {group.name} ({group.device_count} devices)")
    print(f"  ID: {group.id}")
    print(f"  Description: {group.description}")
```

**Returns:** `GroupListResponse`

---

### `create_group(name, description=None)`

Create a new device group.

```python
result = client.fleet.create_group(
    name="Warehouse A",
    description="Robots in warehouse section A"
)

print(f"Created group: {result.group.id}")
```

**Parameters:**
- `name` (`str`) - Group name
- `description` (`str`, optional) - Group description

**Returns:** `CreateGroupResponse`

---

### `assign_devices(group_id, device_ids)`

Assign devices to a group.

```python
result = client.fleet.assign_devices(
    "grp_abc123",
    ["robot-alpha-01", "robot-alpha-02"]
)

print(f"Assigned: {result.assigned}")
```

**Parameters:**
- `group_id` (`str`) - The group ID
- `device_ids` (`list[str]`) - Device IDs to assign

**Returns:** `AssignDevicesResponse`

---

### `unassign_devices(group_id, device_ids)`

Remove devices from a group.

```python
result = client.fleet.unassign_devices(
    "grp_abc123",
    ["robot-alpha-01"]
)
```

**Parameters:**
- `group_id` (`str`) - The group ID
- `device_ids` (`list[str]`) - Device IDs to remove

**Returns:** `AssignDevicesResponse`

---

### `delete_group(group_id)`

Delete a device group.

```python
result = client.fleet.delete_group("grp_abc123")
print(f"Deleted. Devices unassigned: {result.devices_unassigned}")
```

**Parameters:**
- `group_id` (`str`) - The group ID to delete

**Returns:** `DeleteGroupResponse`

## Example: Health Monitoring Daemon

```python
import time
import psutil
from acto.client import ACTOClient

client = ACTOClient(api_key="...", wallet_address="...")
DEVICE_ID = "robot-001"

def report_health():
    """Report current device health metrics."""
    client.fleet.report_health(
        DEVICE_ID,
        cpu_percent=psutil.cpu_percent(),
        memory_percent=psutil.virtual_memory().percent,
        disk_percent=psutil.disk_usage('/').percent,
        network_connected=True,
    )

# Report health every 60 seconds
while True:
    try:
        report_health()
        print("Health reported successfully")
    except Exception as e:
        print(f"Error reporting health: {e}")
    time.sleep(60)
```

