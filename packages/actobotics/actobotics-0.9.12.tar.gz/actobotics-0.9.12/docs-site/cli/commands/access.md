# acto access

Check your token balance before making API requests.

::: warning This is a Convenience Tool
This command only **checks** your balance locally. It does **not** grant API access.

Actual access control is enforced **server-side** with fixed parameters (token mint, minimum balance) that cannot be manipulated.
:::

## Commands

| Command | Description |
|---------|-------------|
| `acto access check` | Check if wallet has sufficient ACTO tokens |

## Check Access

```bash
acto access check [OPTIONS]
```

### Options

| Option | Description | Required |
|--------|-------------|----------|
| `--owner`, `-o` | Wallet address to check | Yes |

Advanced options (usually not needed):

| Option | Description |
|--------|-------------|
| `--mint`, `-m` | Custom token mint (for testing) |
| `--minimum`, `-min` | Custom minimum (for testing) |
| `--rpc`, `-r` | Custom RPC URL (for testing) |

### Examples

```bash
# Check if your wallet has enough ACTO tokens
acto access check --owner 5K8vK...
```

### Output

```
✅ Access Allowed
   Wallet: 5K8vK...
   Balance: 125,000 tokens
   Required: 50,000 tokens
```

Or if insufficient:

```
❌ Access Denied
   Wallet: 5K8vK...
   Balance: 25,000 tokens
   Required: 50,000 tokens
   Reason: Insufficient balance
```


