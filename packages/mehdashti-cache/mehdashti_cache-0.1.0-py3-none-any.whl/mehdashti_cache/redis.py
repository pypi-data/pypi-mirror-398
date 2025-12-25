"""
Redis Cache Provider

Redis-based cache implementation for distributed caching.
"""

import json
from typing import Any, Optional

from redis.asyncio import Redis
from redis.exceptions import RedisError

from mehdashti_cache.base import CacheProvider


class RedisCache(CacheProvider):
    """
    Redis cache implementation.

    Distributed cache with Redis. Suitable for multi-server deployments.
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        prefix: str = "smart:",
        encoding: str = "utf-8",
    ):
        """
        Initialize Redis cache.

        Args:
            redis_url: Redis connection URL
            prefix: Key prefix for namespacing
            encoding: String encoding
        """
        self.redis = Redis.from_url(redis_url, decode_responses=False)
        self.prefix = prefix
        self.encoding = encoding

    def _make_key(self, key: str) -> str:
        """Add prefix to key."""
        return f"{self.prefix}{key}"

    def _serialize(self, value: Any) -> bytes:
        """Serialize value to bytes."""
        return json.dumps(value).encode(self.encoding)

    def _deserialize(self, data: bytes) -> Any:
        """Deserialize bytes to value."""
        return json.loads(data.decode(self.encoding))

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            data = await self.redis.get(self._make_key(key))
            if data is None:
                return None
            return self._deserialize(data)
        except RedisError as e:
            print(f"Redis error in get: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> None:
        """Set value in cache."""
        try:
            data = self._serialize(value)
            await self.redis.set(self._make_key(key), data, ex=ttl)
        except RedisError as e:
            print(f"Redis error in set: {e}")

    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        try:
            count = await self.redis.delete(self._make_key(key))
            return count > 0
        except RedisError as e:
            print(f"Redis error in delete: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            return await self.redis.exists(self._make_key(key)) > 0
        except RedisError as e:
            print(f"Redis error in exists: {e}")
            return False

    async def clear(self) -> None:
        """Clear all cache entries with the prefix."""
        try:
            keys = await self.redis.keys(f"{self.prefix}*")
            if keys:
                await self.redis.delete(*keys)
        except RedisError as e:
            print(f"Redis error in clear: {e}")

    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        """Get multiple values from cache."""
        if not keys:
            return {}

        try:
            redis_keys = [self._make_key(k) for k in keys]
            values = await self.redis.mget(redis_keys)

            result = {}
            for key, value in zip(keys, values):
                if value is not None:
                    result[key] = self._deserialize(value)
            return result
        except RedisError as e:
            print(f"Redis error in get_many: {e}")
            return {}

    async def set_many(
        self,
        items: dict[str, Any],
        ttl: Optional[int] = None,
    ) -> None:
        """Set multiple values in cache."""
        try:
            pipe = self.redis.pipeline()
            for key, value in items.items():
                data = self._serialize(value)
                pipe.set(self._make_key(key), data, ex=ttl)
            await pipe.execute()
        except RedisError as e:
            print(f"Redis error in set_many: {e}")

    async def delete_many(self, keys: list[str]) -> int:
        """Delete multiple values from cache."""
        if not keys:
            return 0

        try:
            redis_keys = [self._make_key(k) for k in keys]
            return await self.redis.delete(*redis_keys)
        except RedisError as e:
            print(f"Redis error in delete_many: {e}")
            return 0

    async def get_ttl(self, key: str) -> Optional[int]:
        """Get remaining TTL for a key."""
        try:
            ttl = await self.redis.ttl(self._make_key(key))
            if ttl < 0:  # -1 = no expiration, -2 = key doesn't exist
                return None
            return ttl
        except RedisError as e:
            print(f"Redis error in get_ttl: {e}")
            return None

    async def ping(self) -> bool:
        """Check Redis connection."""
        try:
            return await self.redis.ping()
        except RedisError:
            return False

    async def close(self) -> None:
        """Close Redis connection."""
        await self.redis.aclose()
