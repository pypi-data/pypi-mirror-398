from __future__ import annotations

import time
from dataclasses import dataclass

from acto.errors import AccessError


@dataclass
class TokenBucketRateLimiter:
    rps: float
    burst: int
    buckets: dict[str, tuple[float, float]]  # key -> (tokens, last_ts)

    @staticmethod
    def create(rps: float, burst: int) -> TokenBucketRateLimiter:
        return TokenBucketRateLimiter(rps=rps, burst=burst, buckets={})

    def check(self, key: str, cost: float = 1.0) -> None:
        now = time.time()
        tokens, last = self.buckets.get(key, (float(self.burst), now))
        tokens = min(float(self.burst), tokens + (now - last) * self.rps)
        if tokens < cost:
            self.buckets[key] = (tokens, now)
            raise AccessError("Rate limit exceeded.")
        tokens -= cost
        self.buckets[key] = (tokens, now)
