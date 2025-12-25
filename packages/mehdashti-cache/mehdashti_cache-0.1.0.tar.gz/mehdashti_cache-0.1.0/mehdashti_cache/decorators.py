"""
Cache Decorators

Decorators for easy caching of function results.
"""

import functools
import hashlib
import inspect
import json
from typing import Any, Callable, Optional, TypeVar

from mehdashti_cache.base import CacheProvider

F = TypeVar("F", bound=Callable[..., Any])


def cache_key(*args: Any, **kwargs: Any) -> str:
    """
    Generate cache key from function arguments.

    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        Cache key string
    """
    key_data = {"args": args, "kwargs": kwargs}
    key_str = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.md5(key_str.encode()).hexdigest()


def cached(
    cache: CacheProvider,
    ttl: Optional[int] = None,
    key_prefix: Optional[str] = None,
) -> Callable[[F], F]:
    """
    Decorator to cache function results.

    Args:
        cache: Cache provider instance
        ttl: Time to live in seconds
        key_prefix: Optional prefix for cache keys

    Returns:
        Decorated function

    Example:
        ```python
        memory_cache = MemoryCache()

        @cached(memory_cache, ttl=300)
        async def get_user(user_id: int):
            # Expensive database query
            return await db.get_user(user_id)
        ```
    """

    def decorator(func: F) -> F:
        is_async = inspect.iscoroutinefunction(func)
        func_name = func.__qualname__
        prefix = key_prefix or f"cache:{func_name}"

        if is_async:

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                # Generate cache key
                arg_key = cache_key(*args, **kwargs)
                full_key = f"{prefix}:{arg_key}"

                # Try to get from cache
                cached_value = await cache.get(full_key)
                if cached_value is not None:
                    return cached_value

                # Call function and cache result
                result = await func(*args, **kwargs)
                await cache.set(full_key, result, ttl)
                return result

            return async_wrapper  # type: ignore

        else:

            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                # Note: This is a synchronous wrapper, but cache operations are async
                # In practice, you'd need to run this in an async context
                raise NotImplementedError(
                    "Synchronous function caching not implemented. "
                    "Please use async functions with the @cached decorator."
                )

            return sync_wrapper  # type: ignore

    return decorator


def cache_invalidate(
    cache: CacheProvider,
    key_prefix: Optional[str] = None,
) -> Callable[[F], F]:
    """
    Decorator to invalidate cache after function execution.

    Args:
        cache: Cache provider instance
        key_prefix: Optional prefix for cache keys to invalidate

    Returns:
        Decorated function

    Example:
        ```python
        @cache_invalidate(memory_cache, key_prefix="cache:get_user")
        async def update_user(user_id: int, data: dict):
            await db.update_user(user_id, data)
        ```
    """

    def decorator(func: F) -> F:
        is_async = inspect.iscoroutinefunction(func)

        if is_async:

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                result = await func(*args, **kwargs)

                # Invalidate cache
                if key_prefix:
                    # If specific prefix provided, clear those keys
                    # This is a simplified version - in production you'd want
                    # pattern-based key deletion
                    arg_key = cache_key(*args, **kwargs)
                    await cache.delete(f"{key_prefix}:{arg_key}")
                else:
                    # Clear all cache
                    await cache.clear()

                return result

            return async_wrapper  # type: ignore

        else:

            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                raise NotImplementedError(
                    "Synchronous function cache invalidation not implemented"
                )

            return sync_wrapper  # type: ignore

    return decorator
