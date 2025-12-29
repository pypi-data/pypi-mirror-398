# Device Monitoring

Monitor individual devices in your fleet.

## Device Overview

View all devices in the Fleet dashboard:

```python
from acto.client import ACTOClient

client = ACTOClient(api_key="...", wallet_address="...")

fleet = client.fleet.get_overview()

for device in fleet.devices:
    print(f"Device: {device.id}")
    print(f"  Status: {device.status}")
    print(f"  Proofs: {device.proof_count}")
    print(f"  Tasks: {device.task_count}")
    print(f"  Last activity: {device.last_activity}")
    print()
```

## Device Details

Get detailed information about a specific device:

```python
device = client.fleet.get_device("robot-001")

print(f"ID: {device.id}")
print(f"Display Name: {device.display_name}")
print(f"Status: {device.status}")
print(f"First Activity: {device.first_activity}")
print(f"Last Activity: {device.last_activity}")
print(f"Total Proofs: {device.proof_count}")
print(f"Task Types: {device.task_history}")

# Health metrics
if device.health:
    print(f"CPU: {device.health.cpu_percent}%")
    print(f"Memory: {device.health.memory_percent}%")
    print(f"Battery: {device.health.battery_percent}%")

# Recent logs
print("\nRecent Activity:")
for log in device.recent_logs:
    print(f"  [{log.timestamp}] {log.message}")
```

## Renaming Devices

Assign custom names for easier identification:

```python
# Rename a device
client.fleet.rename_device("robot-alpha-01", "Warehouse Bot #1")

# View the new name
device = client.fleet.get_device("robot-alpha-01")
print(device.display_name)  # "Warehouse Bot #1"
```

The original ID is preserved for API calls, but the display name is shown in the dashboard.

## Device Status Indicators

| Status | Icon | Condition |
|--------|------|-----------|
| Active | 🟢 | Activity in last hour |
| Idle | 🟡 | Activity in last 24 hours |
| Inactive | 🔴 | No activity in 24+ hours |
| Unknown | ⚪ | Never seen activity |

## Activity Logs

Each device maintains an activity log:

```python
device = client.fleet.get_device("robot-001")

for log in device.recent_logs:
    print(f"[{log.timestamp}] [{log.level}] {log.message}")
    if log.proof_id:
        print(f"  Proof: {log.proof_id}")
    if log.task_id:
        print(f"  Task: {log.task_id}")
```

Log levels:
- `success` - Successful operations
- `info` - General information
- `warning` - Potential issues
- `error` - Failed operations

## Task History

View which tasks a device has performed:

```python
device = client.fleet.get_device("robot-001")

print("Tasks performed:")
for task in device.task_history:
    print(f"  - {task}")
```

## Dashboard Features

The web dashboard provides:

### Device List View

- Sortable by name, status, activity
- Filter by status or group
- Search by name or ID

### Device Detail Modal

- Complete activity timeline
- Health metrics visualization
- Task history
- Rename functionality

### Grid View

- Visual overview of all devices
- Status at a glance
- Quick actions

## Deleting Devices

Remove devices from the fleet (soft delete - proofs are preserved):

```python
# Via API
response = requests.delete(
    f"{API_URL}/v1/fleet/devices/robot-001",
    headers={"Authorization": f"Bearer {jwt_token}"}
)
```

In the dashboard, click the trash icon on any device card and confirm deletion.

> **Note:** Deleted devices won't appear in the fleet list, but their historical proofs remain in the database.

## Reordering Devices

Customize the device order in your fleet list:

```python
# Via API
response = requests.patch(
    f"{API_URL}/v1/fleet/devices/order",
    headers={"Authorization": f"Bearer {jwt_token}"},
    json={
        "device_orders": [
            {"device_id": "robot-001", "sort_order": 0},
            {"device_id": "robot-002", "sort_order": 1}
        ]
    }
)
```

In the dashboard, drag devices up/down to reorder them. The order is saved automatically.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/fleet/devices/{id}` | Get device details |
| PATCH | `/v1/fleet/devices/{id}/name` | Rename device |
| DELETE | `/v1/fleet/devices/{id}` | Delete device (soft delete) |
| PATCH | `/v1/fleet/devices/order` | Reorder devices |
| POST | `/v1/fleet/devices/{id}/health` | Report health |
| GET | `/v1/fleet/devices/{id}/health` | Get health |

## Best Practices

### Use Descriptive Robot IDs

```python
# Good - descriptive and consistent
robot_id = "warehouse-a-robot-01"
robot_id = "assembly-line-2-arm-03"

# Avoid - ambiguous
robot_id = "robot1"
robot_id = "test"
```

### Set Custom Names

Use custom names that your team understands:

```python
# Original ID: robot-alpha-01-2024-serial-xyz
# Custom name: Picker Bot #3
client.fleet.rename_device(
    "robot-alpha-01-2024-serial-xyz",
    "Picker Bot #3"
)
```

### Monitor Critical Devices

Set up alerts for important robots:

```python
device = client.fleet.get_device("critical-robot")

if device.status == "inactive":
    send_alert(f"Critical robot offline: {device.display_name}")

if device.health and device.health.battery_percent < 20:
    send_alert(f"Low battery: {device.display_name}")
```

