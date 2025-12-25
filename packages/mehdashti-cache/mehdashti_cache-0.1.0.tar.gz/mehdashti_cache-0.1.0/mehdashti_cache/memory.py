"""
Memory Cache Provider

In-memory cache implementation with TTL support.
"""

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Optional

from mehdashti_cache.base import CacheProvider


@dataclass
class CacheEntry:
    """Cache entry with value and expiration."""

    value: Any
    expires_at: Optional[float] = None

    def is_expired(self) -> bool:
        """Check if entry is expired."""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at


class MemoryCache(CacheProvider):
    """
    In-memory cache implementation.

    Thread-safe cache with TTL support. Suitable for single-server deployments.
    """

    def __init__(self, cleanup_interval: int = 60):
        """
        Initialize memory cache.

        Args:
            cleanup_interval: Interval in seconds for cleaning up expired entries
        """
        self._cache: dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()
        self._cleanup_interval = cleanup_interval
        self._cleanup_task: Optional[asyncio.Task] = None

    async def start_cleanup(self) -> None:
        """Start background cleanup task."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop_cleanup(self) -> None:
        """Stop background cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None

    async def _cleanup_loop(self) -> None:
        """Background task to clean up expired entries."""
        while True:
            try:
                await asyncio.sleep(self._cleanup_interval)
                await self._cleanup_expired()
            except asyncio.CancelledError:
                break

    async def _cleanup_expired(self) -> None:
        """Remove expired entries from cache."""
        async with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items() if entry.is_expired()
            ]
            for key in expired_keys:
                del self._cache[key]

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
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
        ttl: Optional[int] = None,
    ) -> None:
        """Set value in cache."""
        expires_at = time.time() + ttl if ttl else None
        async with self._lock:
            self._cache[key] = CacheEntry(value=value, expires_at=expires_at)

    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        value = await self.get(key)
        return value is not None

    async def clear(self) -> None:
        """Clear all cache entries."""
        async with self._lock:
            self._cache.clear()

    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        """Get multiple values from cache."""
        result = {}
        for key in keys:
            value = await self.get(key)
            if value is not None:
                result[key] = value
        return result

    async def set_many(
        self,
        items: dict[str, Any],
        ttl: Optional[int] = None,
    ) -> None:
        """Set multiple values in cache."""
        for key, value in items.items():
            await self.set(key, value, ttl)

    async def delete_many(self, keys: list[str]) -> int:
        """Delete multiple values from cache."""
        count = 0
        for key in keys:
            if await self.delete(key):
                count += 1
        return count

    async def get_ttl(self, key: str) -> Optional[int]:
        """Get remaining TTL for a key."""
        async with self._lock:
            entry = self._cache.get(key)
            if entry is None or entry.expires_at is None:
                return None
            remaining = int(entry.expires_at - time.time())
            return max(0, remaining)

    def size(self) -> int:
        """Get number of entries in cache."""
        return len(self._cache)
