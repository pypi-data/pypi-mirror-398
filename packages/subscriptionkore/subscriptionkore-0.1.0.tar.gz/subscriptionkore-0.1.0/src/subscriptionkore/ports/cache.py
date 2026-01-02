"""Cache port interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class CachePort(ABC):
    """Abstract interface for caching."""

    @abstractmethod
    async def get(self, key: str) -> Any | None:
        """Get value from cache."""
        ...

    @abstractmethod
    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: int | None = None,
    ) -> None:
        """Set value in cache with optional TTL."""
        ...

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete value from cache.  Returns True if deleted."""
        ...

    @abstractmethod
    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern.  Returns count deleted."""
        ...

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        ...

    @abstractmethod
    async def incr(self, key: str, amount: int = 1) -> int:
        """Increment value.  Returns new value."""
        ...

    @abstractmethod
    async def expire(self, key: str, ttl_seconds: int) -> bool:
        """Set expiration on key. Returns True if key exists."""
        ...
