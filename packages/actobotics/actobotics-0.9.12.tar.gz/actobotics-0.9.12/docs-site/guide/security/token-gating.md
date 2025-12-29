# Token Gating

ACTO uses SPL token-based access control to gate API access.

## Requirements

To use the ACTO API, you must:

1. **Hold 50,000 ACTO tokens** in your Solana wallet
2. **Provide your wallet address** with each API request (via `X-Wallet-Address` header)

## How It Works

::: tip Server-Side Verification
Token verification is **enforced server-side**. The token mint address, minimum balance, and RPC endpoint are configured on the server and **cannot be manipulated by clients**.
:::

```
┌─────────────────────────────────────────────────────────────┐
│                    API Request Flow                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Client sends request with wallet address                 │
│     (X-Wallet-Address header)                                │
│                    │                                         │
│                    ▼                                         │
│  2. Server verifies token balance using:                     │
│     • Fixed ACTO token mint (server config)                  │
│     • Fixed minimum: 50,000 tokens (server config)           │
│     • Helius RPC (server config)                             │
│                    │                                         │
│                    ▼                                         │
│  3. Is balance >= 50,000 ACTO?                               │
│         │                    │                               │
│         │ Yes                │ No                            │
│         ▼                    ▼                               │
│  4a. Process request    4b. Return 403 Forbidden             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Check Your Balance (Optional)

These tools let you **check** if you have enough tokens. They don't grant access - that's always verified server-side.

### Via CLI

```bash
# Check if your wallet has enough ACTO tokens
acto access check --owner YOUR_WALLET_ADDRESS
```

### Via SDK

```python
from acto.client import ACTOClient

client = ACTOClient(api_key="...", wallet_address="...")

# Check your own balance
result = client.check_access(owner="YOUR_WALLET_ADDRESS")

if result.allowed:
    print(f"✅ You have {result.balance} tokens - access granted!")
else:
    print(f"❌ Insufficient balance: {result.balance} tokens")
```

### Via API

```bash
curl -X POST https://api.actobotics.net/v1/access/check \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "X-Wallet-Address: YOUR_WALLET" \
  -H "Content-Type: application/json" \
  -d '{"owner": "YOUR_WALLET_ADDRESS"}'
```

::: warning Balance Check ≠ Access
The `/v1/access/check` endpoint is a convenience tool for checking balances. The actual access control on protected endpoints (like `/v1/verify`) uses server-configured values that cannot be overridden.
:::

## Response Examples

### Access Granted

```json
{
  "allowed": true,
  "reason": "Sufficient balance",
  "balance": 125000.0
}
```

### Access Denied

```json
{
  "allowed": false,
  "reason": "Insufficient balance. Required: 50000, Found: 25000",
  "balance": 25000.0
}
```

## RPC Integration

ACTO uses [Helius](https://helius.xyz/) RPC for reliable token balance queries:

- **Rate limits** - Higher limits than public RPC
- **Reliability** - Enterprise-grade infrastructure
- **Speed** - Optimized for quick responses

The `rpc_url` parameter is optional - the server uses its configured Helius endpoint by default.

## Caching

Token balances are cached briefly to reduce RPC calls:

- **Cache duration**: 60 seconds
- **Cache scope**: Per wallet address

This means:
- Acquiring tokens may take up to 60 seconds to reflect
- Transferring tokens away may allow continued access for up to 60 seconds

## Error Handling

### In SDK

```python
from acto.client.exceptions import AuthorizationError

try:
    result = client.verify(envelope)
except AuthorizationError as e:
    print(f"Access denied: {e}")
    print("Please ensure you have at least 50,000 ACTO tokens")
```

### HTTP Response

```http
HTTP/1.1 403 Forbidden
Content-Type: application/json

{
  "detail": "Insufficient token balance. Required: 50000 ACTO"
}
```

## Getting ACTO Tokens

Options to acquire ACTO tokens:

1. **DEX** - Trade on supported decentralized exchanges
2. **Community** - Participate in community programs
3. **Partners** - Check for partner integrations

::: info Token Contract
For the official ACTO token mint address, visit [actobotics.net](https://actobotics.net)
:::

## FAQ

### Why 50,000 tokens?

This threshold was chosen to:
- Ensure meaningful network participation
- Prevent spam and abuse
- Create sustainable economics

### Can I use multiple wallets?

Yes, each API key is tied to a specific wallet. Create separate keys for different wallets.

### What if my balance drops below 50,000?

Your API requests will be rejected with a 403 error until your balance is restored.

### Is the balance check on every request?

Yes, but results are cached for 60 seconds for efficiency.

