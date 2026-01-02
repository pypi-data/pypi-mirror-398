"""Redis cache implementation."""

from __future__ import annotations

import json
from typing import Any

from subscriptionkore.ports.cache import CachePort


class RedisCache(CachePort):
    """
    Redis cache implementation.

    Requires redis[hiredis] package.
    """

    def __init__(self, redis_url: str) -> None:
        self._redis_url = redis_url
        self._client: Any = None

    async def _get_client(self) -> Any:
        """Get or create Redis client."""
        if self._client is None:
            try:
                import redis.asyncio as redis
            except ImportError as e:
                raise ImportError(
                    "Redis package not installed. Install with: pip install redis[hiredis]"
                ) from e

            self._client = redis.from_url(
                self._redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
        return self._client

    async def get(self, key: str) -> Any | None:
        client = await self._get_client()
        value = await client.get(key)
        if value is None:
            return None
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value

    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: int | None = None,
    ) -> None:
        client = await self._get_client()
        serialized = json.dumps(value, default=str)
        if ttl_seconds is not None:
            await client.setex(key, ttl_seconds, serialized)
        else:
            await client.set(key, serialized)

    async def delete(self, key: str) -> bool:
        client = await self._get_client()
        result = await client.delete(key)
        return result > 0

    async def delete_pattern(self, pattern: str) -> int:
        client = await self._get_client()
        cursor = 0
        deleted = 0

        while True:
            cursor, keys = await client.scan(cursor=cursor, match=pattern, count=100)
            if keys:
                deleted += await client.delete(*keys)
            if cursor == 0:
                break

        return deleted

    async def exists(self, key: str) -> bool:
        client = await self._get_client()
        return await client.exists(key) > 0

    async def incr(self, key: str, amount: int = 1) -> int:
        client = await self._get_client()
        return await client.incrby(key, amount)

    async def expire(self, key: str, ttl_seconds: int) -> bool:
        client = await self._get_client()
        return await client.expire(key, ttl_seconds)

    async def close(self) -> None:
        """Close Redis connection."""
        if self._client is not None:
            await self._client.close()
            self._client = None
