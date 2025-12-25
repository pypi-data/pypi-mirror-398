# acto access

Check token balance for API access.

## Commands

| Command | Description |
|---------|-------------|
| `acto access check` | Check if wallet has sufficient tokens |

## Check Access

```bash
acto access check [OPTIONS]
```

### Options

| Option | Description | Required |
|--------|-------------|----------|
| `--owner`, `-o` | Wallet address to check | Yes |
| `--mint`, `-m` | Token mint address | Yes |
| `--minimum` | Minimum required balance | No (default: 50000) |

### Examples

```bash
# Basic check
acto access check \
  --owner 5K8vK... \
  --mint ACTO_TOKEN_MINT \
  --minimum 50000
```

### Output

```
✅ Access Allowed
   Wallet: 5K8vK...
   Balance: 125,000 ACTO
   Required: 50,000 ACTO
```

Or if insufficient:

```
❌ Access Denied
   Wallet: 5K8vK...
   Balance: 25,000 ACTO
   Required: 50,000 ACTO
```

