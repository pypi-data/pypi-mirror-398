# acto keys

Manage cryptographic signing keys.

## Commands

| Command | Description |
|---------|-------------|
| `acto keys generate` | Generate a new keypair |
| `acto keys list` | List stored keys |
| `acto keys export` | Export a key |
| `acto keys import` | Import a key |

## Generate Key

Generate a new Ed25519 keypair.

```bash
acto keys generate [OPTIONS]
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--output`, `-o` | Output file path | `~/.acto/keys/default.json` |
| `--name`, `-n` | Key name | `default` |
| `--force`, `-f` | Overwrite existing | `false` |

### Examples

```bash
# Generate default key
acto keys generate

# Generate with custom name
acto keys generate --name production

# Generate to specific file
acto keys generate --output ./my-key.json

# Overwrite existing
acto keys generate --name default --force
```

### Output

```
✅ Generated new keypair: default
   Public key: abc123...
   Saved to: ~/.acto/keys/default.json
```

## List Keys

List all stored keys.

```bash
acto keys list
```

### Output

```
Stored Keys:
┌──────────────┬────────────────────────────────────────┬─────────────────────┐
│ Name         │ Public Key                             │ Created             │
├──────────────┼────────────────────────────────────────┼─────────────────────┤
│ default      │ abc123...                              │ 2025-01-15 10:30:00 │
│ production   │ def456...                              │ 2025-01-14 08:15:00 │
│ test         │ ghi789...                              │ 2025-01-13 14:45:00 │
└──────────────┴────────────────────────────────────────┴─────────────────────┘
```

## Export Key

Export a key to file or stdout.

```bash
acto keys export [OPTIONS] NAME
```

### Options

| Option | Description |
|--------|-------------|
| `--output`, `-o` | Output file (default: stdout) |
| `--public-only` | Export only public key |
| `--format` | Output format (json, pem) |

### Examples

```bash
# Export to stdout
acto keys export default

# Export to file
acto keys export default --output key-backup.json

# Export public key only
acto keys export default --public-only
```

## Import Key

Import a key from file.

```bash
acto keys import [OPTIONS] FILE
```

### Options

| Option | Description |
|--------|-------------|
| `--name`, `-n` | Key name (default: filename) |
| `--force`, `-f` | Overwrite existing |

### Examples

```bash
# Import key
acto keys import ./backup-key.json

# Import with custom name
acto keys import ./key.json --name restored

# Overwrite existing
acto keys import ./key.json --name default --force
```

## Key File Format

Keys are stored as JSON:

```json
{
  "name": "default",
  "public_key_b64": "base64_encoded_public_key",
  "private_key_b64": "base64_encoded_private_key",
  "created_at": "2025-01-15T10:30:00Z"
}
```

::: danger Private Key Security
Never share or commit private keys. Use environment variables or secrets management in production.
:::

## Storage Location

Keys are stored in:

- **Linux/Mac**: `~/.acto/keys/`
- **Windows**: `%USERPROFILE%\.acto\keys\`

## Programmatic Access

Use the SDK for programmatic key management:

```python
from acto.crypto import KeyPair

# Generate
keypair = KeyPair.generate()

# Save
keypair.save("my-key.json")

# Load
loaded = KeyPair.load("my-key.json")
```

