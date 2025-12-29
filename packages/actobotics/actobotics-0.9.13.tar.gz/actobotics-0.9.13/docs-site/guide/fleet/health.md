# Health Reporting

Report device health metrics to monitor your fleet's status.

## Overview

Health reporting enables:
- Real-time monitoring of device resources
- Historical trend analysis
- Proactive maintenance alerts

## Supported Metrics

All metrics are **optional** - only report what your device supports.

| Metric | Type | Description |
|--------|------|-------------|
| `cpu_percent` | float | CPU usage (0-100) |
| `cpu_temperature` | float | CPU temperature (°C) |
| `memory_percent` | float | Memory usage (0-100) |
| `memory_used_mb` | float | Memory used (MB) |
| `memory_total_mb` | float | Total memory (MB) |
| `battery_percent` | float | Battery level (0-100) |
| `battery_charging` | bool | Is charging |
| `disk_percent` | float | Disk usage (0-100) |
| `network_connected` | bool | Network status |
| `network_type` | string | wifi/ethernet/cellular |
| `uptime_seconds` | int | Device uptime |
| `temperature` | float | Ambient temperature |
| `custom_metrics` | dict | Custom key-value metrics |

## Basic Usage

### Python SDK

```python
from acto.client import ACTOClient

client = ACTOClient(api_key="...", wallet_address="...")

# Report basic metrics
client.fleet.report_health(
    "robot-001",
    cpu_percent=45.2,
    memory_percent=68.0,
    battery_percent=85.0
)
```

### With Custom Metrics

```python
client.fleet.report_health(
    "robot-001",
    cpu_percent=45.2,
    memory_percent=68.0,
    custom_metrics={
        "arm_temperature": 38.5,
        "gripper_force": 12.0,
        "sensor_status": "ok",
        "error_count": 0
    }
)
```

### HTTP API

```bash
curl -X POST https://api.actobotics.net/v1/fleet/devices/robot-001/health \
  -H "Authorization: Bearer JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "cpu_percent": 45.2,
    "memory_percent": 68.0,
    "battery_percent": 85.0
  }'
```

## Periodic Reporting

Report health at regular intervals:

```python
import time
import psutil
from acto.client import ACTOClient

client = ACTOClient(api_key="...", wallet_address="...")
DEVICE_ID = "robot-001"
INTERVAL = 60  # seconds

def get_health_metrics():
    return {
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent,
    }

while True:
    try:
        metrics = get_health_metrics()
        client.fleet.report_health(DEVICE_ID, **metrics)
        print(f"Reported: CPU={metrics['cpu_percent']}%")
    except Exception as e:
        print(f"Error: {e}")
    
    time.sleep(INTERVAL)
```

## Retrieving Health

Get the latest health for a device:

```python
health = client.fleet.get_health("robot-001")

print(f"CPU: {health.cpu_percent}%")
print(f"Memory: {health.memory_percent}%")
print(f"Battery: {health.battery_percent}%")
print(f"Last updated: {health.last_updated}")
```

## Health History

Health data is stored for 30 days. View history in the dashboard:

1. Go to **Fleet** tab
2. Click on a device
3. View **Health History** section

## Health Thresholds

The dashboard uses color-coded indicators:

| Resource | 🟢 Good | 🟡 Warning | 🔴 Critical |
|----------|---------|------------|-------------|
| CPU | < 70% | 70-90% | > 90% |
| Memory | < 75% | 75-90% | > 90% |
| Battery | > 30% | 15-30% | < 15% |
| Disk | < 80% | 80-95% | > 95% |

## Best Practices

### Report Frequency

- **Production**: Every 60 seconds
- **Development**: Every 5-10 minutes
- **Low-power devices**: Every 5-15 minutes

### Handle Errors Gracefully

```python
from acto.client.exceptions import NetworkError, ServerError

def report_health_safe(client, device_id, **metrics):
    try:
        client.fleet.report_health(device_id, **metrics)
        return True
    except (NetworkError, ServerError) as e:
        # Log but don't crash
        logger.warning(f"Health report failed: {e}")
        return False
```

### Include Relevant Custom Metrics

```python
# Robot-specific metrics
custom_metrics = {
    "arm_joint_temps": [35.2, 36.1, 34.8, 35.5, 36.0, 35.3],
    "gripper_cycles": 15420,
    "navigation_errors": 0,
    "task_queue_length": 3
}
```

## Integration Examples

### ROS Node

```python
#!/usr/bin/env python
import rospy
from diagnostic_msgs.msg import DiagnosticArray
from acto.client import ACTOClient

client = ACTOClient(api_key="...", wallet_address="...")

def diagnostics_callback(msg):
    metrics = {}
    for status in msg.status:
        if status.name == "cpu":
            metrics["cpu_percent"] = float(status.values[0].value)
        elif status.name == "memory":
            metrics["memory_percent"] = float(status.values[0].value)
    
    if metrics:
        client.fleet.report_health("ros-robot", **metrics)

rospy.init_node('acto_health_reporter')
rospy.Subscriber('/diagnostics', DiagnosticArray, diagnostics_callback)
rospy.spin()
```

### Systemd Service

```ini
# /etc/systemd/system/acto-health.service
[Unit]
Description=ACTO Health Reporter
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /opt/acto/health_reporter.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

