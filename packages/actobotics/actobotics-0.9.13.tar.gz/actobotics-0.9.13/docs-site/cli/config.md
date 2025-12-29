# CLI Configuration

Configure the ACTO CLI with a config file.

## Config File Location

- **Linux/Mac**: `~/.acto/config.toml`
- **Windows**: `%USERPROFILE%\.acto\config.toml`

## Configuration Options

```toml
# ~/.acto/config.toml

# Logging
log_level = "INFO"  # DEBUG, INFO, WARNING, ERROR
json_logs = false

# Default values
default_robot_id = "robot-001"
default_key_name = "default"

# API settings (optional)
api_key = "acto_xxx..."
wallet_address = "5K8vK..."
base_url = "https://api.actobotics.net"

# Directories
keys_dir = "~/.acto/keys"
proofs_dir = "~/.acto/proofs"
```

## Environment Variable Override

Environment variables take precedence over config file:

```bash
export ACTO_LOG_LEVEL=DEBUG
export ACTO_API_KEY=acto_xxx...
export ACTO_WALLET_ADDRESS=5K8vK...
```

## Creating Config

### Manual

```bash
mkdir -p ~/.acto
cat > ~/.acto/config.toml << EOF
log_level = "INFO"
default_robot_id = "my-robot"
EOF
```

### Via CLI

```bash
acto config init
```

## Viewing Config

```bash
acto config show
```

Output:

```
Current Configuration:
  log_level: INFO
  json_logs: false
  default_robot_id: robot-001
  api_key: acto_abc... (set)
  wallet_address: 5K8vK... (set)
```

## Config Precedence

1. Command-line arguments (highest)
2. Environment variables
3. Config file
4. Default values (lowest)

Example:

```bash
# Config file says log_level = "INFO"
# But this overrides it:
acto --log-level DEBUG proof create ...
```

