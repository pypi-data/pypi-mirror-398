# Smart Cache

Caching utilities with Redis and Memory providers for Smart Platform.

## Features

- **Multiple Providers**: Redis and in-memory caching
- **Async/Await**: Full async support
- **TTL Support**: Time-based expiration
- **Decorators**: Easy function caching
- **Type Safe**: Full type hints

## Installation

```bash
pip install smart-cache
```

## Usage

### Memory Cache

```python
from mehdashti_cache import MemoryCache, cached

# Initialize cache
cache = MemoryCache(cleanup_interval=60)
await cache.start_cleanup()

# Use directly
await cache.set("user:1", {"name": "John"}, ttl=300)
user = await cache.get("user:1")

# Use as decorator
@cached(cache, ttl=300)
async def get_user(user_id: int):
    # Expensive operation
    return await db.get_user(user_id)
```

### Redis Cache

```python
from mehdashti_cache import RedisCache, cached

# Initialize cache
cache = RedisCache(redis_url="redis://localhost:6379/0")

# Use directly
await cache.set("user:1", {"name": "John"}, ttl=300)
user = await cache.get("user:1")

# Use as decorator
@cached(cache, ttl=300, key_prefix="user")
async def get_user(user_id: int):
    return await db.get_user(user_id)
```

## API

### CacheProvider

Base interface for all cache providers.

- `get(key)`: Get value
- `set(key, value, ttl)`: Set value
- `delete(key)`: Delete value
- `exists(key)`: Check if exists
- `clear()`: Clear all
- `get_many(keys)`: Get multiple values
- `set_many(items, ttl)`: Set multiple values
- `delete_many(keys)`: Delete multiple values
- `get_ttl(key)`: Get remaining TTL

## License

MIT
