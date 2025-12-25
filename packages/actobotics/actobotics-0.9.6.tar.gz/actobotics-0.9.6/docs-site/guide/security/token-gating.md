# Token Gating

ACTO uses SPL token-based access control to gate API access.

## Requirements

To use the ACTO API, you must:

1. **Hold 50,000 ACTO tokens** in your Solana wallet
2. **Provide your wallet address** with each API request

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                    API Request Flow                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Client sends request with wallet address                 │
│                    │                                         │
│                    ▼                                         │
│  2. Server queries Solana for token balance                  │
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

## Checking Your Balance

### Via SDK

```python
from acto.client import ACTOClient

client = ACTOClient(api_key="...", wallet_address="...")

result = client.check_access(
    owner="YOUR_WALLET_ADDRESS",
    mint="ACTO_TOKEN_MINT_ADDRESS",
    minimum=50000
)

print(f"Allowed: {result.allowed}")
print(f"Balance: {result.balance}")
print(f"Reason: {result.reason}")
```

### Via CLI

```bash
acto access check \
  --owner YOUR_WALLET_ADDRESS \
  --mint ACTO_TOKEN_MINT \
  --minimum 50000
```

### Via API

```bash
curl -X POST https://api.actobotics.net/v1/access/check \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "X-Wallet-Address: YOUR_WALLET" \
  -H "Content-Type: application/json" \
  -d '{
    "owner": "YOUR_WALLET_ADDRESS",
    "mint": "ACTO_TOKEN_MINT",
    "minimum": 50000
  }'
```

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

