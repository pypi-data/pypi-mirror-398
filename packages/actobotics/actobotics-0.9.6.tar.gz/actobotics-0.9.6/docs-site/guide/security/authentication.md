# Authentication

ACTO uses multiple authentication mechanisms for different scenarios.

## Authentication Methods

| Method | Used For | How It Works |
|--------|----------|--------------|
| **API Key** | SDK/API access | Bearer token in header |
| **JWT** | Dashboard/Fleet | Wallet signature verification |
| **Token Gating** | Access control | SPL token balance check |

## API Key Authentication

Used for programmatic API access (SDK, scripts).

### Getting an API Key

1. Visit [api.actobotics.net/dashboard](https://api.actobotics.net/dashboard)
2. Connect your Solana wallet
3. Click **"Create API Key"**
4. Copy the key immediately

### Using API Keys

```python
from acto.client import ACTOClient

client = ACTOClient(
    api_key="acto_abc123...",
    wallet_address="5K8vK..."
)
```

HTTP requests:
```http
Authorization: Bearer acto_abc123...
X-Wallet-Address: 5K8vK...
```

### Key Management

- **One key per use case** - Development, staging, production
- **Rotate regularly** - Delete old keys, create new ones
- **Monitor usage** - Check statistics in dashboard
- **Never share** - Treat as secrets

## JWT Authentication

Used for dashboard and fleet management (wallet-based sessions).

### How It Works

1. **Connect wallet** - Dashboard prompts wallet connection
2. **Sign challenge** - Wallet signs a unique message
3. **Receive JWT** - Server verifies signature, issues JWT
4. **Use token** - Subsequent requests use JWT

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│    Wallet    │     │   Dashboard  │     │   Server     │
└──────────────┘     └──────────────┘     └──────────────┘
       │                    │                    │
       │  1. Connect        │                    │
       │◄───────────────────│                    │
       │                    │                    │
       │                    │  2. Get challenge  │
       │                    │───────────────────▶│
       │                    │                    │
       │                    │  3. Challenge      │
       │                    │◄───────────────────│
       │                    │                    │
       │  4. Sign message   │                    │
       │◄───────────────────│                    │
       │                    │                    │
       │  5. Signature      │                    │
       │───────────────────▶│                    │
       │                    │                    │
       │                    │  6. Verify sig     │
       │                    │───────────────────▶│
       │                    │                    │
       │                    │  7. JWT token      │
       │                    │◄───────────────────│
       │                    │                    │
```

### JWT Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /v1/auth/wallet/connect` | Get signature challenge |
| `POST /v1/auth/wallet/verify` | Verify signature, get JWT |
| `GET /v1/auth/me` | Get current user info |

## Token Gating

Access requires holding **50,000 ACTO tokens**.

### How It Works

1. API request includes wallet address
2. Server queries token balance (via Helius RPC)
3. If balance < 50,000, request is rejected (403)

### Checking Balance

```python
result = client.check_access(
    owner="YOUR_WALLET",
    mint="ACTO_TOKEN_MINT",
    minimum=50000
)

if result.allowed:
    print(f"Access granted. Balance: {result.balance}")
else:
    print(f"Access denied: {result.reason}")
```

### Why Token Gating?

- **Network sustainability** - Value alignment
- **Spam prevention** - Economic barrier
- **Community building** - Token holder benefits

## Best Practices

### Secure Storage

```python
import os

# ✅ Use environment variables
api_key = os.environ["ACTO_API_KEY"]

# ❌ Never hardcode
api_key = "acto_abc123..."  # BAD!
```

### Key Rotation

1. Create new API key
2. Update applications
3. Test with new key
4. Delete old key

### Different Keys per Environment

```bash
# Development
export ACTO_API_KEY="acto_dev_..."

# Production
export ACTO_API_KEY="acto_prod_..."
```

### Monitor for Anomalies

- Unexpected usage spikes
- Requests from unknown IPs
- Failed authentication attempts

## Troubleshooting

### Invalid API Key

```json
{"detail": "Invalid API key"}
```

**Solutions:**
- Verify key is correct
- Check key hasn't been deleted
- Ensure header format: `Bearer YOUR_KEY`

### Insufficient Token Balance

```json
{"detail": "Insufficient token balance. Required: 50000 ACTO"}
```

**Solutions:**
- Check wallet balance
- Verify wallet address is correct
- Acquire more ACTO tokens

### JWT Expired

```json
{"detail": "Token expired"}
```

**Solutions:**
- Re-connect wallet in dashboard
- Refresh the page
- Clear browser storage and reconnect

