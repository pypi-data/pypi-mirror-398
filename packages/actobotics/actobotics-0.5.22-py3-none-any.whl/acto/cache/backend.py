"""Caching backend for ACTO with support for in-memory and Redis caching."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from acto.config.settings import Settings


class CacheBackend(ABC):
    """Abstract base class for cache backends."""

    @abstractmethod
    def get(self, key: str) -> Any | None:
        """Get a value from cache."""
        ...

    @abstractmethod
    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set a value in cache with optional TTL."""
        ...

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete a key from cache."""
        ...

    @abstractmethod
    def clear(self) -> None:
        """Clear all cache entries."""
        ...

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if a key exists in cache."""
        ...


class MemoryCacheBackend(CacheBackend):
    """In-memory cache backend using a simple dictionary."""

    def __init__(self, default_ttl: int = 3600):
        self._cache: dict[str, tuple[Any, float | None]] = {}
        self._default_ttl = default_ttl

    def _is_expired(self, key: str) -> bool:
        """Check if a cache entry is expired."""
        if key not in self._cache:
            return True
        _, expire_at = self._cache[key]
        if expire_at is None:
            return False
        import time
        return time.time() > expire_at

    def get(self, key: str) -> Any | None:
        """Get a value from cache."""
        if self._is_expired(key):
            self._cache.pop(key, None)
            return None
        value, _ = self._cache[key]
        return value

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set a value in cache with optional TTL."""
        import time

        expire_at = None
        if ttl is not None:
            expire_at = time.time() + ttl
        elif self._default_ttl > 0:
            expire_at = time.time() + self._default_ttl

        self._cache[key] = (value, expire_at)

    def delete(self, key: str) -> None:
        """Delete a key from cache."""
        self._cache.pop(key, None)

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()

    def exists(self, key: str) -> bool:
        """Check if a key exists in cache."""
        return not self._is_expired(key)


class RedisCacheBackend(CacheBackend):
    """Redis cache backend."""

    def __init__(self, settings: Settings):
        try:
            import redis
        except ImportError as e:
            raise ImportError(
                "Redis dependencies are not installed. Install with: pip install -e '.[redis]'"
            ) from e

        self._client = redis.from_url(
            settings.redis_url,
            password=settings.redis_password,
            decode_responses=False,  # We'll handle serialization ourselves
        )
        self._default_ttl = settings.cache_ttl

    def get(self, key: str) -> Any | None:
        """Get a value from cache."""
        import orjson

        data = self._client.get(key)
        if data is None:
            return None
        return orjson.loads(data)

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set a value in cache with optional TTL."""
        import orjson

        ttl = ttl if ttl is not None else self._default_ttl
        data = orjson.dumps(value)
        self._client.setex(key, ttl, data)

    def delete(self, key: str) -> None:
        """Delete a key from cache."""
        self._client.delete(key)

    def clear(self) -> None:
        """Clear all cache entries (flush database)."""
        self._client.flushdb()

    def exists(self, key: str) -> bool:
        """Check if a key exists in cache."""
        return bool(self._client.exists(key))


def get_cache_backend(settings: Settings) -> CacheBackend | None:
    """Get the appropriate cache backend based on settings."""
    if not settings.cache_enabled:
        return None

    if settings.cache_backend == "redis":
        return RedisCacheBackend(settings)
    elif settings.cache_backend == "memory":
        return MemoryCacheBackend(default_ttl=settings.cache_ttl)
    else:
        raise ValueError(f"Unknown cache backend: {settings.cache_backend}")

