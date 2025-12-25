# Basic Usage

Learn the essential patterns for using the ACTO SDK.

## Workflow Overview

```
1. Install SDK     ──▶  pip install actobotics
2. Get API Key     ──▶  api.actobotics.net/dashboard
3. Create Proof    ──▶  create_proof(bundle, keys)
4. Verify via API  ──▶  client.verify(envelope)
5. Submit Proof    ──▶  client.submit_proof(envelope)
```

## Complete Example

```python
from acto.client import ACTOClient
from acto.proof import create_proof
from acto.crypto import KeyPair
from acto.telemetry.models import TelemetryBundle, TelemetryEvent

# ============================================
# 1. Setup: Generate or load keypair
# ============================================

# Generate new keypair
keypair = KeyPair.generate()

# Or load existing keypair
# keypair = KeyPair.load("my_keypair.json")

# Save for later use
keypair.save("my_keypair.json")

# ============================================
# 2. Create telemetry data
# ============================================

# Simulate robot task execution
bundle = TelemetryBundle(
    task_id="pick-and-place-widget",
    robot_id="robot-arm-01",
    run_id="run-2025-01-15-001",
    events=[
        TelemetryEvent(
            ts="2025-01-15T10:30:00Z",
            topic="task_start",
            data={"task": "pick-and-place", "target": "widget-A"}
        ),
        TelemetryEvent(
            ts="2025-01-15T10:30:01Z",
            topic="arm_move",
            data={"position": [0.5, 0.3, 0.2], "velocity": 0.5}
        ),
        TelemetryEvent(
            ts="2025-01-15T10:30:02Z",
            topic="gripper",
            data={"action": "close", "force": 15.2}
        ),
        TelemetryEvent(
            ts="2025-01-15T10:30:03Z",
            topic="arm_move",
            data={"position": [0.8, 0.5, 0.4], "velocity": 0.3}
        ),
        TelemetryEvent(
            ts="2025-01-15T10:30:04Z",
            topic="gripper",
            data={"action": "open", "force": 0.0}
        ),
        TelemetryEvent(
            ts="2025-01-15T10:30:05Z",
            topic="task_complete",
            data={"status": "success", "duration_ms": 5000}
        ),
    ]
)

# ============================================
# 3. Create the proof
# ============================================

envelope = create_proof(
    bundle,
    keypair.private_key_b64,
    keypair.public_key_b64,
    meta={
        "operator": "John Doe",
        "shift": "morning"
    }
)

print(f"Created proof with hash: {envelope.payload.payload_hash[:16]}...")

# ============================================
# 4. Connect to API and verify
# ============================================

client = ACTOClient(
    api_key="acto_your_api_key_here",
    wallet_address="YOUR_SOLANA_WALLET"
)

# Verify the proof
result = client.verify(envelope)

if result.valid:
    print("✅ Proof is valid!")
else:
    print(f"❌ Invalid proof: {result.reason}")
    exit(1)

# ============================================
# 5. Submit to registry
# ============================================

proof_id = client.submit_proof(envelope)
print(f"📝 Submitted with ID: {proof_id}")

# ============================================
# 6. Retrieve and search
# ============================================

# Get the proof back
retrieved = client.get_proof(proof_id)
print(f"Retrieved: {retrieved.payload.subject.task_id}")

# Search for proofs
results = client.search_proofs(
    robot_id="robot-arm-01",
    limit=10
)
print(f"Found {results.total} proofs for this robot")

# ============================================
# 7. Check wallet statistics
# ============================================

stats = client.get_wallet_stats()
print(f"\n📊 Wallet Statistics:")
print(f"   Total proofs: {stats.total_proofs_submitted}")
print(f"   Verifications: {stats.total_verifications}")
print(f"   Success rate: {stats.verification_success_rate}%")
```

## Key Patterns

### Pattern 1: Verify Before Submit

Always verify proofs before submitting:

```python
result = client.verify(envelope)

if result.valid:
    proof_id = client.submit_proof(envelope)
else:
    logger.error(f"Proof invalid: {result.reason}")
```

### Pattern 2: Context Manager

Use context manager for automatic cleanup:

```python
with ACTOClient(api_key="...", wallet_address="...") as client:
    result = client.verify(envelope)
    proof_id = client.submit_proof(envelope)
# Connection automatically closed
```

### Pattern 3: Batch Operations

Process multiple proofs efficiently:

```python
# Create multiple proofs
envelopes = []
for task in tasks:
    bundle = TelemetryBundle(
        task_id=task["id"],
        robot_id=task["robot"],
        events=task["events"]
    )
    envelope = create_proof(bundle, keypair.private_key_b64, keypair.public_key_b64)
    envelopes.append(envelope)

# Batch verify
results = client.verify_batch(envelopes)
print(f"Valid: {results.valid_count}/{results.total}")

# Submit valid proofs
for i, r in enumerate(results.results):
    if r.valid:
        proof_id = client.submit_proof(envelopes[i])
```

### Pattern 4: Error Handling

Handle errors gracefully:

```python
from acto.client.exceptions import (
    AuthenticationError,
    RateLimitError,
    ServerError,
)

try:
    result = client.verify(envelope)
except AuthenticationError:
    print("Check your API key")
except RateLimitError as e:
    print(f"Wait {e.retry_after}s before retrying")
except ServerError:
    print("Server error - try again later")
```

### Pattern 5: Fleet Health Reporting

Report robot health periodically:

```python
import psutil

def report_health():
    client.fleet.report_health(
        "robot-arm-01",
        cpu_percent=psutil.cpu_percent(),
        memory_percent=psutil.virtual_memory().percent,
        custom_metrics={
            "arm_temperature": get_arm_temp(),
            "gripper_force": get_gripper_force(),
        }
    )
```

## Integration Examples

### ROS Integration

```python
import rospy
from sensor_msgs.msg import JointState

events = []

def joint_callback(msg):
    events.append(TelemetryEvent(
        ts=rospy.Time.now().to_sec(),
        topic="joint_state",
        data={
            "positions": list(msg.position),
            "velocities": list(msg.velocity),
        }
    ))

rospy.Subscriber("/joint_states", JointState, joint_callback)

# After task completion
bundle = TelemetryBundle(
    task_id="ros-task-001",
    robot_id="ros-robot",
    events=events
)
envelope = create_proof(bundle, keypair.private_key_b64, keypair.public_key_b64)
```

### Async Usage

```python
import asyncio
from acto.client import AsyncACTOClient

async def main():
    async with AsyncACTOClient(api_key="...", wallet_address="...") as client:
        # Async verification
        result = await client.verify(envelope)
        
        # Async submit
        proof_id = await client.submit_proof(envelope)
        
        # Concurrent operations
        results = await asyncio.gather(
            client.verify(envelope1),
            client.verify(envelope2),
            client.verify(envelope3),
        )

asyncio.run(main())
```

