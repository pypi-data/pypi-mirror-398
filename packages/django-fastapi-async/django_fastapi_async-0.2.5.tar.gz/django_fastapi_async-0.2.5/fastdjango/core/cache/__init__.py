"""
FastDjango Cache Framework.
Async-first caching with multiple backends.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import pickle
import time
from abc import ABC, abstractmethod
from typing import Any, Callable, TypeVar
from functools import wraps

T = TypeVar("T")


class BaseCache(ABC):
    """
    Abstract base class for cache backends.

    All cache operations are async.
    """

    def __init__(
        self,
        timeout: int = 300,
        key_prefix: str = "",
        version: int = 1,
        **kwargs: Any,
    ):
        self.default_timeout = timeout
        self.key_prefix = key_prefix
        self.version = version

    def make_key(self, key: str, version: int | None = None) -> str:
        """Construct the full cache key."""
        v = version if version is not None else self.version
        return f"{self.key_prefix}:{v}:{key}"

    @abstractmethod
    async def get(self, key: str, default: Any = None, version: int | None = None) -> Any:
        """Get a value from the cache."""
        pass

    @abstractmethod
    async def set(
        self, key: str, value: Any, timeout: int | None = None, version: int | None = None
    ) -> bool:
        """Set a value in the cache."""
        pass

    @abstractmethod
    async def delete(self, key: str, version: int | None = None) -> bool:
        """Delete a key from the cache."""
        pass

    @abstractmethod
    async def clear(self) -> bool:
        """Clear all keys from the cache."""
        pass

    async def get_or_set(
        self,
        key: str,
        default: Any | Callable[[], Any],
        timeout: int | None = None,
        version: int | None = None,
    ) -> Any:
        """Get a value, or set it if not present."""
        value = await self.get(key, version=version)
        if value is None:
            if callable(default):
                value = default()
                if asyncio.iscoroutine(value):
                    value = await value
            else:
                value = default
            await self.set(key, value, timeout=timeout, version=version)
        return value

    async def get_many(self, keys: list[str], version: int | None = None) -> dict[str, Any]:
        """Get multiple values from the cache."""
        result = {}
        for key in keys:
            value = await self.get(key, version=version)
            if value is not None:
                result[key] = value
        return result

    async def set_many(
        self, mapping: dict[str, Any], timeout: int | None = None, version: int | None = None
    ) -> list[str]:
        """Set multiple values in the cache."""
        failed = []
        for key, value in mapping.items():
            if not await self.set(key, value, timeout=timeout, version=version):
                failed.append(key)
        return failed

    async def delete_many(self, keys: list[str], version: int | None = None) -> bool:
        """Delete multiple keys from the cache."""
        for key in keys:
            await self.delete(key, version=version)
        return True

    async def has_key(self, key: str, version: int | None = None) -> bool:
        """Check if a key exists in the cache."""
        return await self.get(key, version=version) is not None

    async def incr(self, key: str, delta: int = 1, version: int | None = None) -> int:
        """Increment a value in the cache."""
        value = await self.get(key, version=version)
        if value is None:
            raise ValueError(f"Key '{key}' not found")
        new_value = int(value) + delta
        await self.set(key, new_value, version=version)
        return new_value

    async def decr(self, key: str, delta: int = 1, version: int | None = None) -> int:
        """Decrement a value in the cache."""
        return await self.incr(key, -delta, version=version)

    async def touch(self, key: str, timeout: int | None = None, version: int | None = None) -> bool:
        """Update the timeout of a key."""
        value = await self.get(key, version=version)
        if value is None:
            return False
        return await self.set(key, value, timeout=timeout, version=version)

    async def close(self) -> None:
        """Close the cache connection."""
        pass


class MemoryCache(BaseCache):
    """
    In-memory cache backend.
    Good for development and single-process applications.
    """

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self._cache: dict[str, tuple[Any, float | None]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str, default: Any = None, version: int | None = None) -> Any:
        full_key = self.make_key(key, version)
        async with self._lock:
            if full_key not in self._cache:
                return default

            value, expires = self._cache[full_key]

            if expires is not None and time.time() > expires:
                del self._cache[full_key]
                return default

            return value

    async def set(
        self, key: str, value: Any, timeout: int | None = None, version: int | None = None
    ) -> bool:
        full_key = self.make_key(key, version)
        timeout = timeout if timeout is not None else self.default_timeout

        expires = time.time() + timeout if timeout else None

        async with self._lock:
            self._cache[full_key] = (value, expires)
        return True

    async def delete(self, key: str, version: int | None = None) -> bool:
        full_key = self.make_key(key, version)
        async with self._lock:
            if full_key in self._cache:
                del self._cache[full_key]
                return True
        return False

    async def clear(self) -> bool:
        async with self._lock:
            self._cache.clear()
        return True


class FileCache(BaseCache):
    """
    File-based cache backend.
    Stores cached data in files on disk.
    """

    def __init__(self, location: str = ".cache", **kwargs: Any):
        super().__init__(**kwargs)
        self.location = location
        import os
        os.makedirs(location, exist_ok=True)

    def _get_path(self, key: str) -> str:
        """Get file path for a key."""
        import os
        hashed = hashlib.md5(key.encode()).hexdigest()
        return os.path.join(self.location, hashed)

    async def get(self, key: str, default: Any = None, version: int | None = None) -> Any:
        import os
        import aiofiles

        full_key = self.make_key(key, version)
        path = self._get_path(full_key)

        if not os.path.exists(path):
            return default

        try:
            async with aiofiles.open(path, "rb") as f:
                data = await f.read()

            expires, value = pickle.loads(data)

            if expires is not None and time.time() > expires:
                os.unlink(path)
                return default

            return value
        except Exception:
            return default

    async def set(
        self, key: str, value: Any, timeout: int | None = None, version: int | None = None
    ) -> bool:
        import aiofiles

        full_key = self.make_key(key, version)
        path = self._get_path(full_key)
        timeout = timeout if timeout is not None else self.default_timeout

        expires = time.time() + timeout if timeout else None

        try:
            data = pickle.dumps((expires, value))
            async with aiofiles.open(path, "wb") as f:
                await f.write(data)
            return True
        except Exception:
            return False

    async def delete(self, key: str, version: int | None = None) -> bool:
        import os

        full_key = self.make_key(key, version)
        path = self._get_path(full_key)

        if os.path.exists(path):
            os.unlink(path)
            return True
        return False

    async def clear(self) -> bool:
        import os
        import shutil

        if os.path.exists(self.location):
            shutil.rmtree(self.location)
            os.makedirs(self.location)
        return True


class RedisCache(BaseCache):
    """
    Redis cache backend.
    Requires redis-py[hiredis] package.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: str | None = None,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self._client = None

    async def _get_client(self):
        """Get or create Redis client."""
        if self._client is None:
            import redis.asyncio as redis
            self._client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
            )
        return self._client

    async def get(self, key: str, default: Any = None, version: int | None = None) -> Any:
        client = await self._get_client()
        full_key = self.make_key(key, version)

        try:
            value = await client.get(full_key)
            if value is None:
                return default
            return pickle.loads(value)
        except Exception:
            return default

    async def set(
        self, key: str, value: Any, timeout: int | None = None, version: int | None = None
    ) -> bool:
        client = await self._get_client()
        full_key = self.make_key(key, version)
        timeout = timeout if timeout is not None else self.default_timeout

        try:
            data = pickle.dumps(value)
            if timeout:
                await client.setex(full_key, timeout, data)
            else:
                await client.set(full_key, data)
            return True
        except Exception:
            return False

    async def delete(self, key: str, version: int | None = None) -> bool:
        client = await self._get_client()
        full_key = self.make_key(key, version)

        try:
            result = await client.delete(full_key)
            return result > 0
        except Exception:
            return False

    async def clear(self) -> bool:
        client = await self._get_client()
        try:
            await client.flushdb()
            return True
        except Exception:
            return False

    async def close(self) -> None:
        if self._client:
            await self._client.close()
            self._client = None


class DatabaseCache(BaseCache):
    """
    Database cache backend using Tortoise ORM.
    Stores cache in a database table.
    """

    def __init__(self, table_name: str = "cache_table", **kwargs: Any):
        super().__init__(**kwargs)
        self.table_name = table_name

    async def _get_model(self):
        """Get or create cache model."""
        from tortoise import fields
        from tortoise.models import Model

        # Dynamic model creation
        class CacheEntry(Model):
            key = fields.CharField(max_length=255, pk=True)
            value = fields.BinaryField()
            expires = fields.DatetimeField(null=True)

            class Meta:
                table = self.table_name

        return CacheEntry

    async def get(self, key: str, default: Any = None, version: int | None = None) -> Any:
        from datetime import datetime

        CacheEntry = await self._get_model()
        full_key = self.make_key(key, version)

        try:
            entry = await CacheEntry.get_or_none(key=full_key)
            if entry is None:
                return default

            if entry.expires and datetime.now() > entry.expires:
                await entry.delete()
                return default

            return pickle.loads(entry.value)
        except Exception:
            return default

    async def set(
        self, key: str, value: Any, timeout: int | None = None, version: int | None = None
    ) -> bool:
        from datetime import datetime, timedelta

        CacheEntry = await self._get_model()
        full_key = self.make_key(key, version)
        timeout = timeout if timeout is not None else self.default_timeout

        expires = datetime.now() + timedelta(seconds=timeout) if timeout else None

        try:
            data = pickle.dumps(value)
            await CacheEntry.update_or_create(
                key=full_key,
                defaults={"value": data, "expires": expires}
            )
            return True
        except Exception:
            return False

    async def delete(self, key: str, version: int | None = None) -> bool:
        CacheEntry = await self._get_model()
        full_key = self.make_key(key, version)

        try:
            deleted = await CacheEntry.filter(key=full_key).delete()
            return deleted > 0
        except Exception:
            return False

    async def clear(self) -> bool:
        CacheEntry = await self._get_model()
        try:
            await CacheEntry.all().delete()
            return True
        except Exception:
            return False


# Cache decorators
def cached(
    timeout: int = 300,
    key_func: Callable[..., str] | None = None,
    cache: BaseCache | None = None,
):
    """
    Decorator to cache function results.

    Usage:
        @cached(timeout=3600)
        async def get_user(user_id: int):
            return await User.get(pk=user_id)

        @cached(key_func=lambda user_id: f"user:{user_id}")
        async def get_user(user_id: int):
            return await User.get(pk=user_id)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            nonlocal cache
            if cache is None:
                cache = get_cache()

            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                key_parts = [func.__module__, func.__name__]
                key_parts.extend(str(a) for a in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = ":".join(key_parts)

            # Try to get from cache
            result = await cache.get(cache_key)
            if result is not None:
                return result

            # Call function and cache result
            result = await func(*args, **kwargs)
            await cache.set(cache_key, result, timeout=timeout)
            return result

        return wrapper
    return decorator


def cache_page(timeout: int = 300, key_prefix: str = "page"):
    """
    Decorator to cache entire page responses.

    Usage:
        @router.get("/")
        @cache_page(timeout=3600)
        async def home(request: Request):
            return {"message": "Hello"}
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any):
            cache = get_cache()

            # Extract request to build cache key
            request = kwargs.get("request") or (args[0] if args else None)
            if request and hasattr(request, "url"):
                cache_key = f"{key_prefix}:{request.url.path}:{request.url.query}"
            else:
                cache_key = f"{key_prefix}:{func.__name__}"

            # Try cache
            cached_response = await cache.get(cache_key)
            if cached_response is not None:
                return cached_response

            # Call function
            response = await func(*args, **kwargs)
            await cache.set(cache_key, response, timeout=timeout)
            return response

        return wrapper
    return decorator


# Default cache instance
_default_cache: BaseCache | None = None


def get_cache(backend: str | None = None) -> BaseCache:
    """
    Get cache instance.

    Args:
        backend: Cache backend to use (memory, file, redis, database)

    Returns:
        Cache instance
    """
    global _default_cache

    if backend is None and _default_cache is not None:
        return _default_cache

    # Get from settings
    from fastdjango.conf import settings

    cache_config = getattr(settings, "CACHES", {}).get("default", {})
    backend = backend or cache_config.get("BACKEND", "memory")

    backends = {
        "memory": MemoryCache,
        "file": FileCache,
        "redis": RedisCache,
        "database": DatabaseCache,
    }

    cache_class = backends.get(backend, MemoryCache)
    cache_instance = cache_class(**cache_config)

    if _default_cache is None:
        _default_cache = cache_instance

    return cache_instance


def clear_cache() -> None:
    """Clear the default cache."""
    global _default_cache
    _default_cache = None


# Convenience aliases
cache = get_cache


__all__ = [
    "BaseCache",
    "MemoryCache",
    "FileCache",
    "RedisCache",
    "DatabaseCache",
    "cached",
    "cache_page",
    "get_cache",
    "clear_cache",
    "cache",
]
