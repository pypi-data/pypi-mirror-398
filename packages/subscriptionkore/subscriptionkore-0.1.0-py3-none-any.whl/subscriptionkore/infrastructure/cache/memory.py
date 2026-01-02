"""In-memory cache implementation."""

from __future__ import annotations

import asyncio
import fnmatch
import time
from dataclasses import dataclass
from typing import Any

from subscriptionkore.ports.cache import CachePort


@dataclass
class CacheEntry:
    """Cache entry with expiration."""

    value: Any
    expires_at: float | None = None

    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at


class InMemoryCache(CachePort):
    """
    In-memory cache implementation.

    Suitable for development and single-process applications.
    For production, use RedisCache.
    """

    def __init__(self) -> None:
        self._cache: dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Any | None:
        async with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None
            if entry.is_expired():
                del self._cache[key]
                return None
            return entry.value

    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: int | None = None,
    ) -> None:
        async with self._lock:
            expires_at = None
            if ttl_seconds is not None:
                expires_at = time.time() + ttl_seconds
            self._cache[key] = CacheEntry(value=value, expires_at=expires_at)

    async def delete(self, key: str) -> bool:
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    async def delete_pattern(self, pattern: str) -> int:
        async with self._lock:
            keys_to_delete = [k for k in self._cache.keys() if fnmatch.fnmatch(k, pattern)]
            for key in keys_to_delete:
                del self._cache[key]
            return len(keys_to_delete)

    async def exists(self, key: str) -> bool:
        value = await self.get(key)
        return value is not None

    async def incr(self, key: str, amount: int = 1) -> int:
        async with self._lock:
            entry = self._cache.get(key)
            if entry is None or entry.is_expired():
                self._cache[key] = CacheEntry(value=amount)
                return amount
            new_value = int(entry.value) + amount
            entry.value = new_value
            return new_value

    async def expire(self, key: str, ttl_seconds: int) -> bool:
        async with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return False
            entry.expires_at = time.time() + ttl_seconds
            return True

    async def clear(self) -> None:
        """Clear all cache entries."""
        async with self._lock:
            self._cache.clear()
