# Device Groups

Organize your robot fleet into logical groups.

## Overview

Groups help you organize robots by:
- **Location** - Warehouse A, Factory Floor, Lab
- **Function** - Pickers, Inspectors, Transporters
- **Team** - Team Alpha, Night Shift
- **Project** - Project X, Pilot Program

## Creating Groups

### Python SDK

```python
from acto.client import ACTOClient

client = ACTOClient(api_key="...", wallet_address="...")

# Create a group
result = client.fleet.create_group(
    name="Warehouse A",
    description="Robots in warehouse section A"
)

print(f"Created group: {result.group.id}")
```

### Dashboard

1. Go to **Fleet** tab
2. Click **Manage Groups**
3. Click **Create Group**
4. Enter name and description
5. Click **Create**

## Assigning Devices

### Python SDK

```python
# Assign devices to a group
client.fleet.assign_devices(
    group_id="grp_abc123",
    device_ids=["robot-001", "robot-002", "robot-003"]
)
```

### Dashboard (Drag-and-Drop)

The easiest way to assign devices to groups:

1. Open the **Fleet** tab in the dashboard
2. **Drag** a device card from the device list
3. **Drop** it onto a group card on the left sidebar
4. The device is instantly assigned to that group

> **Tip:** To remove a device from a group, drag it onto "All Devices"

### Dashboard (Modal)

1. Click on a device
2. Select **Assign to Group**
3. Choose the group
4. Click **Assign**

## Listing Groups

```python
groups = client.fleet.list_groups()

for group in groups.groups:
    print(f"{group.name} ({group.device_count} devices)")
    print(f"  ID: {group.id}")
    print(f"  Description: {group.description}")
```

## Removing Devices from Groups

```python
# Remove devices from a group
client.fleet.unassign_devices(
    group_id="grp_abc123",
    device_ids=["robot-003"]
)
```

## Deleting Groups

```python
# Delete a group (devices are unassigned, not deleted)
result = client.fleet.delete_group("grp_abc123")
print(f"Devices unassigned: {result.devices_unassigned}")
```

## Filtering by Group

### Dashboard

Use the group filter dropdown to show only devices in a specific group.

### SDK

```python
fleet = client.fleet.get_overview()

# Filter devices by group
warehouse_a = [d for d in fleet.devices if d.group_id == "grp_abc123"]

for device in warehouse_a:
    print(f"- {device.display_name}: {device.status}")
```

## Group Examples

### By Location

```python
# Create location-based groups
locations = [
    ("Warehouse A", "Main warehouse robots"),
    ("Warehouse B", "Secondary warehouse robots"),
    ("Factory Floor", "Production line robots"),
    ("Lab", "R&D and testing robots"),
]

for name, desc in locations:
    client.fleet.create_group(name=name, description=desc)
```

### By Function

```python
# Create function-based groups
functions = [
    ("Pickers", "Pick and place robots"),
    ("Inspectors", "Quality inspection robots"),
    ("Transporters", "Material transport robots"),
    ("Welders", "Welding robots"),
]

for name, desc in functions:
    client.fleet.create_group(name=name, description=desc)
```

### By Shift

```python
# Create shift-based groups
shifts = [
    ("Day Shift", "6 AM - 2 PM robots"),
    ("Evening Shift", "2 PM - 10 PM robots"),
    ("Night Shift", "10 PM - 6 AM robots"),
]

for name, desc in shifts:
    client.fleet.create_group(name=name, description=desc)
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/fleet/groups` | List all groups |
| POST | `/v1/fleet/groups` | Create group |
| PATCH | `/v1/fleet/groups/{id}` | Update group |
| DELETE | `/v1/fleet/groups/{id}` | Delete group |
| POST | `/v1/fleet/groups/{id}/assign` | Assign devices |
| POST | `/v1/fleet/groups/{id}/unassign` | Remove devices |

## Best Practices

### Consistent Naming

```python
# Good - clear and consistent
"Warehouse A - Section 1"
"Warehouse A - Section 2"

# Avoid - inconsistent
"WH-A"
"Warehouse section 1"
```

### Meaningful Descriptions

```python
# Good
description="Assembly line robots for Product X manufacturing"

# Avoid
description="robots"
```

### Hierarchical Organization

For large fleets, consider a hierarchical approach:

```
Production
├── Assembly Line 1
│   ├── Welding Robots
│   └── Assembly Robots
├── Assembly Line 2
│   ├── Welding Robots
│   └── Assembly Robots
└── Quality Control
    └── Inspection Robots
```

Use descriptions or naming conventions to indicate hierarchy.

