# Configuration

Configure the ACTO SDK using environment variables or configuration files.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ACTO_API_KEY` | Your API key | - |
| `ACTO_WALLET_ADDRESS` | Your Solana wallet | - |
| `ACTO_BASE_URL` | API base URL | `https://api.actobotics.net` |
| `ACTO_LOG_LEVEL` | Logging level | `INFO` |
| `ACTO_JSON_LOGS` | JSON log format | `false` |

### Setting Environment Variables

**Linux/Mac:**
```bash
export ACTO_API_KEY="acto_xxx..."
export ACTO_WALLET_ADDRESS="5K8vK..."
```

**Windows (PowerShell):**
```powershell
$env:ACTO_API_KEY = "acto_xxx..."
$env:ACTO_WALLET_ADDRESS = "5K8vK..."
```

**Windows (CMD):**
```cmd
set ACTO_API_KEY=acto_xxx...
set ACTO_WALLET_ADDRESS=5K8vK...
```

### Using with Client

```python
import os
from acto.client import ACTOClient

client = ACTOClient(
    api_key=os.environ.get("ACTO_API_KEY", ""),
    wallet_address=os.environ.get("ACTO_WALLET_ADDRESS", "")
)
```

## Configuration File

The SDK supports a TOML configuration file at `~/.acto/config.toml`:

```toml
# ~/.acto/config.toml

# API Configuration
api_key = "acto_xxx..."
wallet_address = "5K8vK..."
base_url = "https://api.actobotics.net"

# Logging
log_level = "INFO"
json_logs = false

# Defaults
default_robot_id = "robot-001"

# Optional: Helius RPC for token checks
helius_api_key = "your-helius-key"
```

### Loading Configuration

```python
from acto.config import Settings

settings = Settings()
print(settings.api_key)
print(settings.wallet_address)
```

## SDK Settings

The `Settings` class loads configuration from multiple sources:

1. Environment variables (highest priority)
2. Configuration file (`~/.acto/config.toml`)
3. Default values

```python
from acto.config import Settings

# Load settings
settings = Settings()

# Access values
print(settings.log_level)
print(settings.base_url)

# Override with env vars
# ACTO_LOG_LEVEL=DEBUG python script.py
```

## Client Configuration

### Custom Base URL

For contributors running a local development server:

```python
# Local development only - not for production use
client = ACTOClient(
    api_key="...",
    wallet_address="...",
    base_url="http://localhost:8080"  # Local dev server
)
```

::: tip
Regular users should always use the default (`https://api.actobotics.net`). The `base_url` parameter is only for ACTO contributors testing locally.
:::

### Custom Timeout

Increase timeout for slow connections:

```python
client = ACTOClient(
    api_key="...",
    wallet_address="...",
    timeout=60.0  # 60 seconds
)
```

## Logging Configuration

### Basic Logging

```python
import logging
from acto.logging import configure_logging

# Configure ACTO logging
configure_logging(level="DEBUG")

# Or configure Python logging directly
logging.basicConfig(level=logging.DEBUG)
```

### JSON Logging

For production environments:

```python
from acto.logging import configure_logging

configure_logging(level="INFO", json_logs=True)
```

Output:
```json
{"timestamp": "2025-01-15T10:30:00Z", "level": "INFO", "message": "Proof submitted", "proof_id": "abc123"}
```

### Log Levels

| Level | Description |
|-------|-------------|
| `DEBUG` | Detailed debugging information |
| `INFO` | General operational messages |
| `WARNING` | Potential issues |
| `ERROR` | Error conditions |
| `CRITICAL` | Severe errors |

## Security Configuration

For production deployments, use secrets management:

```python
# Using environment variables (recommended)
import os

client = ACTOClient(
    api_key=os.environ["ACTO_API_KEY"],
    wallet_address=os.environ["ACTO_WALLET_ADDRESS"]
)
```

::: danger Never Hardcode Secrets
Never commit API keys or secrets to version control.
:::

### Using .env Files

With python-dotenv:

```bash
pip install python-dotenv
```

```python
from dotenv import load_dotenv
import os

load_dotenv()  # Load from .env file

client = ACTOClient(
    api_key=os.environ["ACTO_API_KEY"],
    wallet_address=os.environ["ACTO_WALLET_ADDRESS"]
)
```

`.env` file:
```
ACTO_API_KEY=acto_xxx...
ACTO_WALLET_ADDRESS=5K8vK...
```

Add `.env` to `.gitignore`:
```
.env
```

