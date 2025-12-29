# acto proof

Create and manage execution proofs.

## Commands

| Command | Description |
|---------|-------------|
| `acto proof create` | Create a proof from telemetry |
| `acto proof verify` | Verify a proof (via API) |
| `acto proof show` | Display proof details |

## Create Proof

Create a signed proof from telemetry data.

```bash
acto proof create [OPTIONS]
```

### Options

| Option | Description | Required |
|--------|-------------|----------|
| `--task-id`, `-t` | Task identifier | Yes |
| `--source`, `-s` | Telemetry source file (JSONL) | Yes |
| `--output`, `-o` | Output file | No |
| `--robot-id`, `-r` | Robot identifier | No |
| `--run-id` | Run identifier | No |
| `--key`, `-k` | Key name to use | No (default: "default") |
| `--meta`, `-m` | Metadata (key=value) | No |

### Examples

```bash
# Basic usage
acto proof create \
  --task-id "pick-and-place-001" \
  --source telemetry.jsonl

# With all options
acto proof create \
  --task-id "quality-inspection" \
  --robot-id "robot-alpha-01" \
  --run-id "run-2025-01-15" \
  --source telemetry.jsonl \
  --output proof.json \
  --key production \
  --meta operator=john \
  --meta location=warehouse-a

# From stdin
cat telemetry.jsonl | acto proof create \
  --task-id "task-001" \
  --source -
```

### Output

```
✅ Proof created successfully!
   Task ID: pick-and-place-001
   Robot ID: robot-alpha-01
   Payload Hash: abc123def456...
   Saved to: proof.json
```

### Telemetry Format (JSONL)

```jsonl
{"ts": "2025-01-15T10:30:00Z", "topic": "gripper", "data": {"action": "close"}}
{"ts": "2025-01-15T10:30:01Z", "topic": "arm", "data": {"position": [0.5, 0.2, 0.8]}}
{"ts": "2025-01-15T10:30:02Z", "topic": "gripper", "data": {"action": "open"}}
```

## Verify Proof

Verify a proof via the ACTO API.

```bash
acto proof verify [OPTIONS] FILE
```

### Options

| Option | Description |
|--------|-------------|
| `--api-key` | API key (or ACTO_API_KEY env) |
| `--wallet` | Wallet address (or ACTO_WALLET_ADDRESS env) |

### Examples

```bash
# Verify proof file
acto proof verify proof.json

# With explicit credentials
acto proof verify proof.json \
  --api-key acto_abc123... \
  --wallet 5K8vK...
```

### Output

```
✅ Proof is VALID
   Payload Hash: abc123def456...
   Task ID: pick-and-place-001
   Robot ID: robot-alpha-01
```

Or if invalid:

```
❌ Proof is INVALID
   Reason: Invalid signature
```

## Show Proof

Display proof details.

```bash
acto proof show FILE
```

### Examples

```bash
acto proof show proof.json
```

### Output

```
Proof Details
═══════════════════════════════════════════════════════════════

Subject:
  Task ID:  pick-and-place-001
  Robot ID: robot-alpha-01
  Run ID:   run-2025-01-15

Timestamps:
  Created:  2025-01-15T10:30:00Z

Hashes:
  Telemetry: abc123...
  Payload:   def456...
  Algorithm: blake3

Signature:
  Algorithm: ed25519
  Signer:    ghi789...

Telemetry Events: 25

Metadata:
  operator: john
  location: warehouse-a
```

## Batch Operations

### Create Multiple Proofs

```bash
# Process multiple telemetry files
for file in telemetry/*.jsonl; do
  task_id=$(basename "$file" .jsonl)
  acto proof create \
    --task-id "$task_id" \
    --source "$file" \
    --output "proofs/${task_id}.json"
done
```

### Verify Multiple Proofs

```bash
# Verify all proofs in directory
for proof in proofs/*.json; do
  echo "Verifying: $proof"
  acto proof verify "$proof"
done
```

## Integration with SDK

```python
from acto.proof import create_proof
from acto.telemetry.parsers import parse_jsonl
from acto.crypto import KeyPair

# Load keypair
keypair = KeyPair.load("~/.acto/keys/default.json")

# Parse telemetry
events = parse_jsonl("telemetry.jsonl")

# Create bundle
bundle = TelemetryBundle(
    task_id="task-001",
    robot_id="robot-001",
    events=events
)

# Create proof
envelope = create_proof(bundle, keypair.private_key_b64, keypair.public_key_b64)
```

