# acto interactive

Launch an interactive menu-driven interface.

## Usage

```bash
acto interactive
```

## Features

The interactive mode provides a user-friendly menu for common operations:

```
╔═══════════════════════════════════════════════════════════════╗
║                    ACTO Interactive Mode                       ║
╠═══════════════════════════════════════════════════════════════╣
║  1. Generate new keypair                                       ║
║  2. List stored keys                                           ║
║  3. Create proof from telemetry                                ║
║  4. Verify proof                                               ║
║  5. Check token balance                                        ║
║  6. View registry stats                                        ║
║  7. Settings                                                   ║
║  8. Exit                                                       ║
╚═══════════════════════════════════════════════════════════════╝

Select option [1-8]:
```

## Menu Options

### 1. Generate New Keypair

Creates a new Ed25519 keypair for signing proofs.

```
Enter key name [default]: production
✅ Generated keypair: production
   Public key: abc123...
```

### 2. List Stored Keys

Shows all stored keypairs.

```
Stored Keys:
  • default (created: 2025-01-15)
  • production (created: 2025-01-14)
```

### 3. Create Proof from Telemetry

Interactive proof creation wizard.

```
Enter task ID: pick-and-place-001
Enter robot ID [optional]: robot-alpha-01
Enter telemetry file path: telemetry.jsonl
Enter output file [optional]: proof.json
Select signing key [default]: default

✅ Proof created!
   Payload hash: abc123...
```

### 4. Verify Proof

Verify a proof via the API.

```
Enter proof file path: proof.json

Verifying proof...
✅ Proof is VALID
   Task ID: pick-and-place-001
```

### 5. Check Token Balance

Check wallet token balance for API access.

```
Enter wallet address: 5K8vK...

Checking balance...
✅ Balance: 125,000 ACTO
   Status: Access allowed (minimum: 50,000)
```

### 6. View Registry Stats

Display local registry statistics.

```
Registry Statistics:
  Total proofs: 150
  Unique robots: 5
  Unique tasks: 12
  Date range: 2025-01-01 to 2025-01-15
```

### 7. Settings

Configure CLI settings.

```
Settings:
  1. Set log level
  2. Configure API credentials
  3. Set default robot ID
  4. Back to main menu
```

### 8. Exit

Exit interactive mode.

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `↑` / `↓` | Navigate menu |
| `Enter` | Select option |
| `q` | Quit |
| `Ctrl+C` | Exit |

## Use Cases

Interactive mode is ideal for:

- **Learning**: Explore ACTO features without memorizing commands
- **Quick tasks**: One-off operations without scripting
- **Debugging**: Step through workflows interactively
- **Demos**: Show ACTO capabilities

## Non-Interactive Usage

For scripts and automation, use direct commands:

```bash
# Instead of interactive
acto proof create --task-id task-001 --source telemetry.jsonl

# Or combine with shell scripts
./my-workflow.sh
```

