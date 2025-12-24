"""
Tests for cache framework.
"""

import pytest
import asyncio


class TestMemoryCache:
    """Test in-memory cache backend."""

    @pytest.mark.asyncio
    async def test_set_get(self):
        """Test basic set and get operations."""
        from fastdjango.core.cache import MemoryCache

        cache = MemoryCache()
        await cache.set("key1", "value1")
        result = await cache.get("key1")
        assert result == "value1"

    @pytest.mark.asyncio
    async def test_get_default(self):
        """Test get with default value."""
        from fastdjango.core.cache import MemoryCache

        cache = MemoryCache()
        result = await cache.get("nonexistent", default="default")
        assert result == "default"

    @pytest.mark.asyncio
    async def test_delete(self):
        """Test delete operation."""
        from fastdjango.core.cache import MemoryCache

        cache = MemoryCache()
        await cache.set("key1", "value1")
        await cache.delete("key1")
        result = await cache.get("key1")
        assert result is None

    @pytest.mark.asyncio
    async def test_clear(self):
        """Test clear operation."""
        from fastdjango.core.cache import MemoryCache

        cache = MemoryCache()
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.clear()
        assert await cache.get("key1") is None
        assert await cache.get("key2") is None

    @pytest.mark.asyncio
    async def test_expiration(self):
        """Test cache expiration."""
        from fastdjango.core.cache import MemoryCache
        import time

        cache = MemoryCache()
        await cache.set("key1", "value1", timeout=1)

        # Should exist immediately
        assert await cache.get("key1") == "value1"

        # Wait for expiration
        await asyncio.sleep(1.1)
        assert await cache.get("key1") is None

    @pytest.mark.asyncio
    async def test_get_or_set(self):
        """Test get_or_set operation."""
        from fastdjango.core.cache import MemoryCache

        cache = MemoryCache()

        # First call should set the value
        result = await cache.get_or_set("key1", "default_value")
        assert result == "default_value"

        # Second call should return cached value
        await cache.set("key1", "new_value")
        result = await cache.get_or_set("key1", "another_default")
        assert result == "new_value"

    @pytest.mark.asyncio
    async def test_get_many(self):
        """Test get_many operation."""
        from fastdjango.core.cache import MemoryCache

        cache = MemoryCache()
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")

        result = await cache.get_many(["key1", "key2", "key3"])
        assert result == {"key1": "value1", "key2": "value2"}

    @pytest.mark.asyncio
    async def test_set_many(self):
        """Test set_many operation."""
        from fastdjango.core.cache import MemoryCache

        cache = MemoryCache()
        await cache.set_many({"key1": "value1", "key2": "value2"})

        assert await cache.get("key1") == "value1"
        assert await cache.get("key2") == "value2"

    @pytest.mark.asyncio
    async def test_incr_decr(self):
        """Test increment and decrement operations."""
        from fastdjango.core.cache import MemoryCache

        cache = MemoryCache()
        await cache.set("counter", 10)

        result = await cache.incr("counter", 5)
        assert result == 15

        result = await cache.decr("counter", 3)
        assert result == 12


class TestCacheDecorator:
    """Test cache decorators."""

    @pytest.mark.asyncio
    async def test_cached_decorator(self):
        """Test @cached decorator."""
        from fastdjango.core.cache import cached, MemoryCache

        call_count = 0
        cache = MemoryCache()

        @cached(timeout=60, cache=cache)
        async def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        # First call - should execute function
        result = await expensive_function(5)
        assert result == 10
        assert call_count == 1

        # Second call - should use cache
        result = await expensive_function(5)
        assert result == 10
        assert call_count == 1  # Still 1, used cache

        # Different argument - should execute function
        result = await expensive_function(10)
        assert result == 20
        assert call_count == 2


class TestFileCache:
    """Test file-based cache backend."""

    @pytest.mark.asyncio
    async def test_set_get(self, tmp_path):
        """Test basic file cache operations."""
        from fastdjango.core.cache import FileCache

        cache = FileCache(location=str(tmp_path / ".cache"))
        await cache.set("key1", "value1")
        result = await cache.get("key1")
        assert result == "value1"

    @pytest.mark.asyncio
    async def test_complex_values(self, tmp_path):
        """Test caching complex values."""
        from fastdjango.core.cache import FileCache

        cache = FileCache(location=str(tmp_path / ".cache"))

        # Dict
        await cache.set("dict", {"a": 1, "b": [1, 2, 3]})
        result = await cache.get("dict")
        assert result == {"a": 1, "b": [1, 2, 3]}

        # List
        await cache.set("list", [1, 2, 3, "four"])
        result = await cache.get("list")
        assert result == [1, 2, 3, "four"]
