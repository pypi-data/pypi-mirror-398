"""
Smart Cache

Caching utilities with Redis and Memory providers for Smart Platform.
"""

from mehdashti_cache.base import CacheProvider
from mehdashti_cache.memory import MemoryCache
from mehdashti_cache.redis import RedisCache
from mehdashti_cache.decorators import cached, cache_key

__version__ = "0.1.0"

__all__ = [
    "CacheProvider",
    "MemoryCache",
    "RedisCache",
    "cached",
    "cache_key",
]
