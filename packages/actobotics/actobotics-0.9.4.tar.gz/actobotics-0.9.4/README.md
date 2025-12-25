# ACTO

**Robotics-first proof-of-execution toolkit.**

Generate deterministic, signed execution proofs from robot telemetry and logs. Verify proofs via the ACTO API. Fast, gas-free verification.

[![PyPI version](https://img.shields.io/pypi/v/actobotics.svg)](https://pypi.org/project/actobotics/)
[![Python versions](https://img.shields.io/pypi/pyversions/actobotics.svg)](https://pypi.org/project/actobotics/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## 🌐 Links

| | |
|---|---|
| 🌍 **Website** | [actobotics.net](https://actobotics.net) |
| 📊 **Dashboard** | [api.actobotics.net/dashboard](https://api.actobotics.net/dashboard) |
| 🐦 **X (Twitter)** | [@actoboticsnet](https://x.com/actoboticsnet) |
| 📖 **API Docs** | [docs/API.md](docs/API.md) |
| 📦 **PyPI** | [pypi.org/project/actobotics](https://pypi.org/project/actobotics/) |

---

## ✨ Features

- **Python SDK** - Create execution proofs locally
- **API Verification** - Verify proofs via the hosted ACTO API
- **REST API** - FastAPI verification service at api.actobotics.net
- **Multi-Wallet Dashboard** - Phantom, Solflare, Backpack, Glow, Coinbase
- **Fleet Management** - Monitor and organize your robot fleet
- **Token Gating** - SPL token balance checks (off-chain)
- **Async Support** - Full async/await API
- **CLI Tools** - Interactive mode, shell completion

---

## 🚀 Quick Start

### Install the SDK

```bash
pip install actobotics
```

That's it! The SDK connects to the hosted API at `api.actobotics.net`.

### Optional Dependencies

```bash
# With Solana integration
pip install actobotics[solana]

# With all optional features (Solana, Redis, ROS, etc.)
pip install actobotics[full]
```

### Basic Usage

```bash
# Generate keypair
acto keys generate

# Create proof from telemetry
acto proof create \
  --task-id "task-001" \
  --source examples/telemetry/sample_telemetry.jsonl
```

---

## 📦 SDK Usage

### Create Proofs Locally

```python
from acto.proof import create_proof
from acto.telemetry.models import TelemetryBundle, TelemetryEvent
from acto.crypto import KeyPair

# Generate keypair
keypair = KeyPair.generate()

# Create telemetry bundle
bundle = TelemetryBundle(
    task_id="task-001",
    robot_id="robot-001",
    events=[TelemetryEvent(ts="2025-01-01T00:00:00Z", topic="sensor", data={"value": 42})]
)

# Create proof locally
envelope = create_proof(bundle, keypair.private_key_b64, keypair.public_key_b64)
```

### Verify & Submit via API

All proof verification must be done through the ACTO API. This ensures integrity, compliance, and enables fleet tracking.

```python
from acto.client import ACTOClient

# Connect to hosted API
client = ACTOClient(
    api_key="acto_xxx...",           # From dashboard
    wallet_address="ABC123..."        # Your Solana wallet
)

# Verify proof via API (required)
result = client.verify(envelope)
print(f"Proof valid: {result.valid}")

# Submit proof to registry
proof_id = client.submit_proof(envelope)
print(f"Submitted: {proof_id}")

# Search proofs
results = client.search_proofs(robot_id="robot-001", limit=10)
for proof in results.items:
    print(f"  - {proof.task_id}")

# Fleet management
fleet = client.fleet.get_overview()
print(f"Total devices: {fleet.summary.total_devices}")

# Report robot health
client.fleet.report_health(
    "robot-001",
    cpu_percent=45.2,
    battery_percent=85.0
)
```

---

## 🌐 API Access

Use the hosted API at `https://api.actobotics.net`:

1. **Get an API Key** at [api.actobotics.net/dashboard](https://api.actobotics.net/dashboard)
2. **Connect your Solana wallet** (requires 50,000 ACTO tokens)
3. **Use the SDK client** (recommended) or make direct API calls:

```python
# Recommended: Use the SDK client
from acto.client import ACTOClient
client = ACTOClient(api_key="...", wallet_address="...")
```

Or with curl:

```bash
curl -X POST https://api.actobotics.net/v1/proofs \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "X-Wallet-Address: YOUR_WALLET" \
  -H "Content-Type: application/json" \
  -d '{"envelope": {...}}'
```

### API Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /v1/proofs` | Submit a proof |
| `GET /v1/proofs` | List proofs |
| `POST /v1/proofs/search` | Search & filter proofs |
| `POST /v1/verify` | Verify a proof |
| `POST /v1/verify/batch` | Batch verify proofs |
| `GET /v1/stats/wallet/{addr}` | Wallet statistics |
| `POST /v1/access/check` | Check token balance |
| `GET /v1/fleet` | Fleet overview |
| `GET /v1/fleet/devices/{id}` | Device details |
| `GET /v1/fleet/groups` | List device groups |

📖 **Full API documentation:** [docs/API.md](docs/API.md)

---

## 🤖 Fleet Management

Monitor and manage your robot fleet from the dashboard:

- **Device Overview** - See all devices with status and activity
- **Custom Names** - Rename devices for easy identification
- **Device Groups** - Organize robots (e.g., "Warehouse A", "Production Line")
- **Health Monitoring** - CPU, RAM, battery status (optional)
- **Activity Logs** - View complete proof history per device

```python
# Report device health (all fields optional)
import httpx

httpx.post(
    "https://api.actobotics.net/v1/fleet/devices/robot-001/health",
    headers={"Authorization": f"Bearer {JWT_TOKEN}"},
    json={
        "cpu_percent": 45.2,
        "memory_percent": 68.0,
        "battery_percent": 85.0
    }
)
```

---

## 🔐 Token Gating

API requests automatically verify your wallet holds sufficient tokens (via Helius RPC).

For manual balance checks via CLI:

```bash
acto access check \
  --owner WALLET_ADDRESS \
  --mint TOKEN_MINT \
  --minimum 50000
```

> **Note:** The `--rpc` flag is optional. If omitted, defaults to the configured RPC.

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [API.md](docs/API.md) | REST API reference |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture |
| [PROTOCOL.md](docs/PROTOCOL.md) | Proof protocol specification |
| [SECURITY.md](docs/SECURITY.md) | Security features & configuration |
| [THREAT_MODEL.md](docs/THREAT_MODEL.md) | Security threat model |
| [CHANGELOG.md](CHANGELOG.md) | Version history & release notes |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contribution guidelines |

---

## 🛠️ Self-Hosted Setup (Contributors)

<details>
<summary>Click to expand self-hosted installation instructions</summary>

If you want to run your own ACTO server or contribute to development:

### Clone & Install

```bash
git clone https://github.com/actobotics/ACTO.git
cd ACTO

# Install with all dependencies including server
pip install -e ".[dev]"
```

### Run the Server

```bash
# Start API server
acto server run

# Or with uvicorn directly
uvicorn acto_server.app:app --reload --port 8080
```

### Run Tests

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=acto --cov-report=html

# Load tests
locust -f tests/load/locustfile.py
```

### Docker

```bash
# Run with docker-compose
docker-compose up -d

# Or build manually
docker build -t acto .
docker run -p 8080:8080 acto
```

### Project Structure

```
ACTO/
├── acto/              # SDK (published to PyPI)
│   ├── proof/         # Proof creation & verification
│   ├── crypto/        # Keys, signing, hashing
│   ├── telemetry/     # Telemetry parsing & normalization
│   ├── registry/      # Local proof storage
│   └── ...
├── acto_cli/          # CLI tools (published to PyPI)
├── acto_server/       # FastAPI server (NOT published)
├── api/               # Vercel serverless functions
├── tests/             # Test suite
└── docs/              # Documentation
```

</details>

---

## 📄 License

MIT. See [LICENSE](LICENSE).

---

<p align="center">
  <a href="https://actobotics.net">Website</a> •
  <a href="https://api.actobotics.net/dashboard">Dashboard</a> •
  <a href="https://x.com/actoboticsnet">X (Twitter)</a> •
  <a href="https://pypi.org/project/actobotics/">PyPI</a>
</p>
