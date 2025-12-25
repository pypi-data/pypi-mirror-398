# Error Handling

The ACTO SDK provides specific exception types for different error scenarios.

## Exception Hierarchy

```
ACTOClientError (base)
├── AuthenticationError (401)
├── AuthorizationError (403)
├── NotFoundError (404)
├── ValidationError (400, 422)
├── RateLimitError (429)
├── ServerError (5xx)
└── NetworkError (connection issues)
```

## Usage

```python
from acto.client import ACTOClient
from acto.client.exceptions import (
    ACTOClientError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ValidationError,
    RateLimitError,
    ServerError,
    NetworkError,
)

client = ACTOClient(api_key="...", wallet_address="...")

try:
    result = client.verify(envelope)
except AuthenticationError as e:
    print(f"Invalid API key: {e}")
except AuthorizationError as e:
    print(f"Access denied (insufficient tokens?): {e}")
except NotFoundError as e:
    print(f"Resource not found: {e}")
except ValidationError as e:
    print(f"Invalid request data: {e}")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after} seconds")
except ServerError as e:
    print(f"Server error: {e}")
except NetworkError as e:
    print(f"Network error: {e}")
except ACTOClientError as e:
    print(f"Unknown client error: {e}")
```

## Exception Details

### ACTOClientError

Base exception for all client errors.

**Attributes:**
- `message` (`str`) - Error message
- `status_code` (`int | None`) - HTTP status code
- `response` (`httpx.Response | None`) - Raw response

```python
try:
    result = client.verify(envelope)
except ACTOClientError as e:
    print(f"Status: {e.status_code}")
    print(f"Message: {e.message}")
```

---

### AuthenticationError

Raised when authentication fails (HTTP 401).

**Common causes:**
- Invalid API key
- Expired API key
- Missing Authorization header

```python
try:
    client = ACTOClient(api_key="invalid", wallet_address="...")
    client.health()
except AuthenticationError:
    print("Please check your API key")
```

---

### AuthorizationError

Raised when access is denied (HTTP 403).

**Common causes:**
- Insufficient token balance (< 50,000 ACTO)
- Wallet address mismatch
- Feature not available

```python
try:
    result = client.verify(envelope)
except AuthorizationError:
    print("Insufficient token balance. Need 50,000 ACTO tokens.")
```

---

### NotFoundError

Raised when a resource doesn't exist (HTTP 404).

**Common causes:**
- Invalid proof ID
- Invalid device ID
- Invalid group ID

```python
try:
    proof = client.get_proof("nonexistent-id")
except NotFoundError:
    print("Proof not found")
```

---

### ValidationError

Raised when request data is invalid (HTTP 400, 422).

**Common causes:**
- Missing required fields
- Invalid data types
- Malformed proof envelope

```python
try:
    client.submit_proof(invalid_envelope)
except ValidationError as e:
    print(f"Validation error: {e.message}")
```

---

### RateLimitError

Raised when rate limits are exceeded (HTTP 429).

**Attributes:**
- `retry_after` (`float | None`) - Seconds until retry is allowed

```python
import time

try:
    result = client.verify(envelope)
except RateLimitError as e:
    if e.retry_after:
        print(f"Sleeping for {e.retry_after} seconds...")
        time.sleep(e.retry_after)
        result = client.verify(envelope)  # Retry
```

---

### ServerError

Raised for server-side errors (HTTP 5xx).

**Common causes:**
- Server maintenance
- Internal errors
- Database issues

```python
import time

def verify_with_retry(envelope, max_retries=3):
    for attempt in range(max_retries):
        try:
            return client.verify(envelope)
        except ServerError:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
            raise
```

---

### NetworkError

Raised for network-level issues.

**Common causes:**
- Connection refused
- DNS resolution failure
- Timeout
- SSL errors

```python
try:
    result = client.verify(envelope)
except NetworkError as e:
    print(f"Network error: {e}")
    print("Check your internet connection")
```

## Retry Strategy

Implement exponential backoff for transient errors:

```python
import time
from acto.client.exceptions import RateLimitError, ServerError, NetworkError

def verify_with_backoff(client, envelope, max_retries=5):
    """Verify with exponential backoff for retryable errors."""
    for attempt in range(max_retries):
        try:
            return client.verify(envelope)
        
        except RateLimitError as e:
            # Use retry_after if provided
            wait = e.retry_after or (2 ** attempt)
            print(f"Rate limited. Waiting {wait}s...")
            time.sleep(wait)
        
        except (ServerError, NetworkError) as e:
            # Exponential backoff for server/network errors
            wait = 2 ** attempt
            print(f"Error: {e}. Retrying in {wait}s...")
            time.sleep(wait)
        
        except Exception:
            # Don't retry for other errors
            raise
    
    raise Exception("Max retries exceeded")
```

## Logging Errors

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    result = client.verify(envelope)
except ACTOClientError as e:
    logger.error(
        "API error",
        extra={
            "status_code": e.status_code,
            "message": str(e),
            "proof_hash": envelope.payload.payload_hash,
        }
    )
    raise
```

