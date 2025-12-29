# Security Best Practices

Follow these practices to secure your ACTO implementation.

## API Key Security

### Do's ✅

```python
import os

# Use environment variables
api_key = os.environ["ACTO_API_KEY"]

# Or use a secrets manager
from acto.security.secrets import get_secrets_manager
secrets = get_secrets_manager(backend="vault")
api_key = secrets.get_secret("acto_api_key")
```

### Don'ts ❌

```python
# Never hardcode credentials
api_key = "acto_abc123..."  # BAD!

# Never commit to version control
# .env files should be in .gitignore
```

## Key Management

### Separate Keys per Environment

```bash
# Development
export ACTO_API_KEY_DEV="acto_dev_..."

# Staging
export ACTO_API_KEY_STAGING="acto_staging_..."

# Production
export ACTO_API_KEY_PROD="acto_prod_..."
```

### Rotate Keys Regularly

1. Create new key in dashboard
2. Update all applications
3. Verify new key works
4. Delete old key

Schedule key rotation:
- **Development**: Monthly
- **Production**: Quarterly

### Limit Key Scope

Use different keys for different purposes:
- One for proof submission
- One for fleet management
- One for monitoring

## Private Key Security

### Generate Keys Securely

```python
from acto.crypto import KeyPair

# Generate in secure environment
keypair = KeyPair.generate()

# Save encrypted or in secure storage
keypair.save("/secure/path/key.json")
```

### Protect Private Keys

- **Never share** private keys
- **Never log** private keys
- **Never commit** to version control
- **Use hardware** security modules (HSM) for production

### Key Storage Options

| Option | Security | Use Case |
|--------|----------|----------|
| Environment variables | Medium | Development, CI/CD |
| AWS Secrets Manager | High | Production (recommended) |
| HashiCorp Vault | High | Enterprise |
| Hardware Security Module | Highest | Critical systems |

## Network Security

### Use HTTPS

Always use HTTPS for API communication:

```python
# ✅ Correct
base_url = "https://api.actobotics.net"

# ❌ Never use HTTP
base_url = "http://api.actobotics.net"  # BAD!
```

### Certificate Validation

Don't disable SSL verification:

```python
# ❌ Never disable SSL verification
import httpx
client = httpx.Client(verify=False)  # BAD!

# ✅ Use proper certificates
client = httpx.Client()  # SSL enabled by default
```

## Data Protection

### PII in Telemetry

Enable PII detection and masking:

```python
from acto.telemetry.pii import PIIMasker

masker = PIIMasker(mask_char="*", preserve_length=True)
masked_bundle = masker.mask_bundle(telemetry_bundle)
```

### Sensitive Metadata

Don't include sensitive data in proof metadata:

```python
# ❌ Bad - sensitive data in metadata
meta = {
    "operator_ssn": "123-45-6789",
    "api_key": "secret_key"
}

# ✅ Good - only necessary metadata
meta = {
    "operator_id": "OP-001",
    "shift": "morning"
}
```

## Error Handling

### Don't Expose Internal Errors

```python
try:
    result = client.verify(envelope)
except Exception as e:
    # ✅ Log internally
    logger.error(f"Verification failed: {e}")
    
    # ✅ Return generic message to users
    raise UserError("Verification failed")
    
    # ❌ Don't expose internal details
    # raise Exception(f"Database error: {e}")
```

### Audit Logging

Enable audit logging for security events:

```python
from acto.security.audit import AuditLogger

audit = AuditLogger(backend="file", file_path="audit.log")

# Log security events
audit.log("proof_submitted", user=user_id, proof_id=proof_id)
audit.log("key_created", user=user_id)
audit.log("access_denied", user=user_id, reason="insufficient_balance")
```

## Rate Limiting

### Implement Client-Side Limits

```python
import time
from collections import deque

class RateLimitedClient:
    def __init__(self, client, rate=5):
        self.client = client
        self.rate = rate
        self.requests = deque()
    
    def request(self, *args, **kwargs):
        self._wait_if_needed()
        return self.client.request(*args, **kwargs)
    
    def _wait_if_needed(self):
        now = time.time()
        while self.requests and now - self.requests[0] > 1:
            self.requests.popleft()
        
        if len(self.requests) >= self.rate:
            time.sleep(1 - (now - self.requests[0]))
        
        self.requests.append(time.time())
```

## Deployment Security

### Production Checklist

- [ ] API keys from secrets manager
- [ ] Private keys in secure storage
- [ ] HTTPS only
- [ ] Audit logging enabled
- [ ] Rate limiting configured
- [ ] Error handling doesn't expose internals
- [ ] PII masking enabled
- [ ] Key rotation schedule set
- [ ] Monitoring and alerting configured

### Docker Security

```dockerfile
# Don't run as root
USER nobody

# Don't include secrets in image
# Use environment variables or mounted secrets

# Minimize attack surface
FROM python:3.11-slim
```

## Incident Response

### If Keys Are Compromised

1. **Immediately** delete the compromised key in dashboard
2. Generate new key
3. Update all applications
4. Review audit logs for unauthorized access
5. Assess impact

### Security Contacts

For security issues, contact:
- **Email**: security@actobotics.net
- **Do not** open public GitHub issues for security vulnerabilities

