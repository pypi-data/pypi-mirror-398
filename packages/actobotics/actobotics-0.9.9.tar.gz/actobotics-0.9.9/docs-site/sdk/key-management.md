# Key Management

Manage cryptographic keys for proof signing.

## KeyPair Class

```python
from acto.crypto import KeyPair
```

### Generate Keys

```python
# Generate new keypair
keypair = KeyPair.generate()

# Access keys (base64 encoded)
print(keypair.public_key_b64)   # Share publicly
print(keypair.private_key_b64)  # Keep secret!
```

### Save and Load

```python
# Save to file
keypair.save("my_keypair.json")

# Load from file
loaded = KeyPair.load("my_keypair.json")
```

### File Format

```json
{
  "public_key_b64": "base64_encoded_public_key",
  "private_key_b64": "base64_encoded_private_key"
}
```

## Using Keys

### With Proof Creation

```python
from acto.proof import create_proof

envelope = create_proof(
    bundle,
    keypair.private_key_b64,  # For signing
    keypair.public_key_b64    # Included in proof
)
```

### From Raw Bytes

```python
# From bytes
keypair = KeyPair.from_bytes(
    private_key_bytes=private_bytes,
    public_key_bytes=public_bytes
)

# Get raw bytes
private_bytes = keypair.private_key_bytes
public_bytes = keypair.public_key_bytes
```

## CLI Key Management

```bash
# Generate new key
acto keys generate

# Generate with name
acto keys generate --name production

# List keys
acto keys list

# Export key
acto keys export default --output backup.json

# Import key
acto keys import backup.json --name restored
```

## Key Storage

### Default Location

- **Linux/Mac**: `~/.acto/keys/`
- **Windows**: `%USERPROFILE%\.acto\keys\`

### Secure Storage Options

| Option | Security | Use Case |
|--------|----------|----------|
| File | Low | Development only |
| Encrypted file | Medium | Personal use |
| Environment variable | Medium | CI/CD |
| Secrets manager | High | Production |
| HSM | Highest | Enterprise |

### Environment Variables

```bash
export ACTO_PRIVATE_KEY_B64="base64_private_key"
export ACTO_PUBLIC_KEY_B64="base64_public_key"
```

```python
import os
from acto.crypto import KeyPair

keypair = KeyPair.from_b64(
    private_key_b64=os.environ["ACTO_PRIVATE_KEY_B64"],
    public_key_b64=os.environ["ACTO_PUBLIC_KEY_B64"]
)
```

## Key Rotation

### When to Rotate

- Scheduled rotation (e.g., quarterly)
- After key compromise
- Personnel changes
- Compliance requirements

### Rotation Process

```python
# 1. Generate new keypair
new_keypair = KeyPair.generate()
new_keypair.save("keys/new_key.json")

# 2. Update applications to use new key
# (deploy with new key)

# 3. Both keys valid during transition
# (old proofs still verifiable)

# 4. Archive old key (don't delete - needed for verification)
```

## Security Best Practices

### Do's ✅

```python
# Store keys securely
keypair.save("/secure/path/key.json", mode=0o600)

# Use environment variables in production
private_key = os.environ["ACTO_PRIVATE_KEY_B64"]

# Use secrets managers
from acto.security.secrets import get_secrets_manager
secrets = get_secrets_manager(backend="vault")
private_key = secrets.get_secret("acto_private_key")
```

### Don'ts ❌

```python
# Never log private keys
print(keypair.private_key_b64)  # BAD!

# Never commit to version control
# my_key.json should be in .gitignore

# Never hardcode
private_key = "base64key..."  # BAD!
```

## Multiple Keys

Use different keys for different purposes:

```python
# Development key
dev_keypair = KeyPair.load("~/.acto/keys/development.json")

# Production key (from secure storage)
prod_keypair = KeyPair.from_b64(
    private_key_b64=vault.get("prod_private_key"),
    public_key_b64=vault.get("prod_public_key")
)
```

