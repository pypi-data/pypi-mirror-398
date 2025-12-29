from __future__ import annotations

import time
from dataclasses import dataclass, field

from acto.errors import AccessError


@dataclass
class TokenBucketRateLimiter:
    """
    Token bucket rate limiter with automatic cleanup of stale entries.

    Uses a token bucket algorithm where:
    - Each bucket starts with `burst` tokens
    - Tokens regenerate at `rps` tokens per second
    - Each request costs 1 token (configurable)
    - Buckets expire after `bucket_ttl` seconds of inactivity

    The cleanup mechanism prevents memory leaks from accumulating bucket entries
    for clients that are no longer active.

    Example:
        >>> limiter = TokenBucketRateLimiter.create(rps=10.0, burst=20)
        >>> try:
        ...     limiter.check("client-ip:/v1/proofs")
        ... except AccessError:
        ...     print("Rate limited!")
    """

    rps: float
    burst: int
    bucket_ttl: float = 3600.0  # Bucket expiry time in seconds (default: 1 hour)
    cleanup_interval: int = 1000  # Run cleanup every N requests
    buckets: dict[str, tuple[float, float]] = field(default_factory=dict)
    _request_count: int = field(default=0, repr=False)

    @staticmethod
    def create(
        rps: float,
        burst: int,
        bucket_ttl: float = 3600.0,
        cleanup_interval: int = 1000,
    ) -> TokenBucketRateLimiter:
        """
        Create a new rate limiter instance.

        Args:
            rps: Requests per second (token refill rate)
            burst: Maximum tokens (burst capacity)
            bucket_ttl: Time in seconds after which inactive buckets expire (default: 1 hour)
            cleanup_interval: Run cleanup after this many requests (default: 1000)

        Returns:
            TokenBucketRateLimiter: Configured rate limiter instance
        """
        return TokenBucketRateLimiter(
            rps=rps,
            burst=burst,
            bucket_ttl=bucket_ttl,
            cleanup_interval=cleanup_interval,
        )

    def check(self, key: str, cost: float = 1.0) -> None:
        """
        Check if a request is allowed under the rate limit.

        Args:
            key: Unique identifier for the rate limit bucket (e.g., "ip:path")
            cost: Token cost for this request (default: 1.0)

        Raises:
            AccessError: If rate limit is exceeded
        """
        now = time.time()

        # Periodic cleanup of stale buckets to prevent memory growth
        self._request_count += 1
        if self._request_count >= self.cleanup_interval:
            self._cleanup_stale_buckets(now)
            self._request_count = 0

        # Get existing bucket or initialize new one
        bucket_data = self.buckets.get(key)

        if bucket_data is None:
            # New client: start with full bucket
            tokens = float(self.burst)
            last = now
        else:
            tokens, last = bucket_data
            # Check if bucket has expired (client was inactive too long)
            if now - last > self.bucket_ttl:
                # Treat as new client: reset to full bucket
                tokens = float(self.burst)
                last = now

        # Refill tokens based on time elapsed (token bucket algorithm)
        elapsed = now - last
        tokens = min(float(self.burst), tokens + elapsed * self.rps)

        # Check if enough tokens available
        if tokens < cost:
            # Update bucket state even on rejection (to track last access time)
            self.buckets[key] = (tokens, now)
            raise AccessError("Rate limit exceeded.")

        # Deduct cost and update bucket
        tokens -= cost
        self.buckets[key] = (tokens, now)

    def _cleanup_stale_buckets(self, now: float) -> None:
        """
        Remove buckets that haven't been accessed within the TTL.

        This prevents unbounded memory growth from accumulating entries
        for clients that are no longer making requests.
        """
        stale_keys = [
            key
            for key, (_, last_ts) in self.buckets.items()
            if now - last_ts > self.bucket_ttl
        ]
        for key in stale_keys:
            del self.buckets[key]

    def get_stats(self) -> dict[str, int | float]:
        """
        Get current rate limiter statistics for monitoring.

        Returns:
            dict: Statistics including bucket count and configuration
        """
        return {
            "bucket_count": len(self.buckets),
            "rps": self.rps,
            "burst": self.burst,
            "bucket_ttl": self.bucket_ttl,
            "cleanup_interval": self.cleanup_interval,
        }
