# CLI Overview

The ACTO CLI provides command-line tools for proof management, key generation, and server operations.

## Installation

The CLI is included with the SDK:

```bash
pip install actobotics
```

Verify installation:

```bash
acto --version
```

## Command Structure

```bash
acto [OPTIONS] COMMAND [ARGS]
```

### Global Options

| Option | Description |
|--------|-------------|
| `--log-level` | Override log level (DEBUG, INFO, WARNING, ERROR) |
| `--json-logs` | Enable JSON log format |
| `--help` | Show help message |
| `--version` | Show version |

## Available Commands

| Command | Description |
|---------|-------------|
| `acto keys` | Key management (generate, list, export) |
| `acto proof` | Proof creation and management |
| `acto registry` | Local registry operations |
| `acto access` | Token access control |
| `acto server` | Run the ACTO server |
| `acto interactive` | Interactive menu mode |
| `acto plugins` | Plugin management |
| `acto pipeline` | Pipeline operations |
| `acto completion` | Shell completion setup |

## Quick Examples

### Generate Keys

```bash
acto keys generate
```

### Create Proof

```bash
acto proof create \
  --task-id "task-001" \
  --source telemetry.jsonl \
  --output proof.json
```

### Interactive Mode

```bash
acto interactive
```

### Check Access

```bash
# Simple (uses configured ACTO token)
acto access check --owner WALLET_ADDRESS

# With explicit parameters
acto access check \
  --owner WALLET_ADDRESS \
  --mint TOKEN_MINT \
  --minimum 50000
```

## Getting Help

Each command has built-in help:

```bash
# General help
acto --help

# Command-specific help
acto keys --help
acto proof create --help
```

## Configuration

The CLI reads from `~/.acto/config.toml`:

```toml
# ~/.acto/config.toml
log_level = "INFO"
default_robot_id = "robot-001"
```

## Next Steps

- [Installation](/cli/installation) - Detailed installation guide
- [acto keys](/cli/commands/keys) - Key management
- [acto proof](/cli/commands/proof) - Proof operations
- [Shell Completion](/cli/completion) - Tab completion setup

