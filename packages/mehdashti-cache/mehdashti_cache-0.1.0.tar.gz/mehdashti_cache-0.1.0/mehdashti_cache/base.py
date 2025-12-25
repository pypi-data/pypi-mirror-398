"""
Base Cache Provider

Abstract base class for cache providers.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class CacheProvider(ABC):
    """Abstract base class for cache providers."""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        pass

    @abstractmethod
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> None:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (None = no expiration)
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        Delete value from cache.

        Args:
            key: Cache key

        Returns:
            True if deleted, False if key didn't exist
        """
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if exists, False otherwise
        """
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all cache entries."""
        pass

    @abstractmethod
    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        """
        Get multiple values from cache.

        Args:
            keys: List of cache keys

        Returns:
            Dictionary of key-value pairs (only existing keys)
        """
        pass

    @abstractmethod
    async def set_many(
        self,
        items: dict[str, Any],
        ttl: Optional[int] = None,
    ) -> None:
        """
        Set multiple values in cache.

        Args:
            items: Dictionary of key-value pairs
            ttl: Time to live in seconds (None = no expiration)
        """
        pass

    @abstractmethod
    async def delete_many(self, keys: list[str]) -> int:
        """
        Delete multiple values from cache.

        Args:
            keys: List of cache keys

        Returns:
            Number of keys deleted
        """
        pass

    @abstractmethod
    async def get_ttl(self, key: str) -> Optional[int]:
        """
        Get remaining TTL for a key.

        Args:
            key: Cache key

        Returns:
            Remaining TTL in seconds, None if no expiration or key doesn't exist
        """
        pass
