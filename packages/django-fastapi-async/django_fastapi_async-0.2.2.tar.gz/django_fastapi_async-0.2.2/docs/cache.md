# Cache Framework

FastDjango provides an async-first caching framework with multiple backends.

## Configuration

Configure caching in `settings.py`:

```python
# Memory cache (default)
CACHES = {
    "default": {
        "BACKEND": "memory",
        "timeout": 300,  # 5 minutes
        "key_prefix": "myapp",
    }
}

# Redis cache
CACHES = {
    "default": {
        "BACKEND": "redis",
        "host": "localhost",
        "port": 6379,
        "db": 0,
        "password": "secret",
        "timeout": 300,
    }
}

# File cache
CACHES = {
    "default": {
        "BACKEND": "file",
        "location": ".cache",
        "timeout": 300,
    }
}
```

## Basic Usage

```python
from fastdjango.core.cache import cache

# Get cache instance
c = cache()

# Set a value
await c.set("my_key", "my_value", timeout=60)

# Get a value
value = await c.get("my_key")
value = await c.get("my_key", default="fallback")

# Delete a value
await c.delete("my_key")

# Clear all cache
await c.clear()
```

## Advanced Operations

```python
from fastdjango.core.cache import get_cache

cache = get_cache()

# Get or set (atomic)
value = await cache.get_or_set("key", "default_value", timeout=60)

# With callable default
async def fetch_data():
    return await expensive_operation()

value = await cache.get_or_set("key", fetch_data, timeout=60)

# Multiple operations
await cache.set_many({"key1": "val1", "key2": "val2"})
values = await cache.get_many(["key1", "key2", "key3"])

# Increment/Decrement
await cache.set("counter", 0)
await cache.incr("counter")  # 1
await cache.incr("counter", 5)  # 6
await cache.decr("counter", 2)  # 4

# Check existence
exists = await cache.has_key("my_key")

# Touch (update expiration)
await cache.touch("my_key", timeout=120)
```

## Decorators

### @cached

Cache function results:

```python
from fastdjango.core.cache import cached

@cached(timeout=3600)
async def get_user(user_id: int):
    return await User.objects.get(pk=user_id)

# Custom cache key
@cached(timeout=3600, key_func=lambda user_id: f"user:{user_id}")
async def get_user(user_id: int):
    return await User.objects.get(pk=user_id)
```

### @cache_page

Cache entire page responses:

```python
from fastdjango.core.cache import cache_page

@router.get("/")
@cache_page(timeout=3600)
async def home(request: Request):
    return {"message": "Hello, cached!"}
```

## Cache Backends

### MemoryCache

In-memory cache for single-process applications:

```python
from fastdjango.core.cache import MemoryCache

cache = MemoryCache(timeout=300)
```

### FileCache

File-based cache for persistence:

```python
from fastdjango.core.cache import FileCache

cache = FileCache(location=".cache", timeout=300)
```

### RedisCache

Redis-based cache for distributed systems:

```python
from fastdjango.core.cache import RedisCache

cache = RedisCache(
    host="localhost",
    port=6379,
    db=0,
    password="secret",
)
```

Requires: `pip install redis[hiredis]`

### DatabaseCache

Database-backed cache using Tortoise ORM:

```python
from fastdjango.core.cache import DatabaseCache

cache = DatabaseCache(table_name="cache_table")
```

## Custom Backend

Create a custom cache backend:

```python
from fastdjango.core.cache import BaseCache

class MyCache(BaseCache):
    async def get(self, key, default=None, version=None):
        # Implementation
        pass

    async def set(self, key, value, timeout=None, version=None):
        # Implementation
        pass

    async def delete(self, key, version=None):
        # Implementation
        pass

    async def clear(self):
        # Implementation
        pass
```

## Cache Versioning

Use versioning to invalidate cache:

```python
cache = get_cache()

# Set with version
await cache.set("key", "value", version=1)

# Get with version
value = await cache.get("key", version=1)

# Incrementing version invalidates old cache
value = await cache.get("key", version=2)  # None
```

## Best Practices

1. **Set appropriate timeouts** - Don't cache forever
2. **Use key prefixes** - Avoid collisions between apps
3. **Cache expensive operations** - DB queries, API calls
4. **Invalidate on updates** - Keep cache consistent
5. **Use Redis for production** - Memory cache doesn't persist
