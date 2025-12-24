"""Tests for cache backends."""

import asyncio
from pathlib import Path

import pytest

from crossref_cite.cache import (
    JsonFileCache,
    MemoryCache,
    create_cache,
    make_cache_key,
)


class TestMemoryCache:
    """Tests for in-memory cache."""

    @pytest.mark.asyncio
    async def test_set_and_get(self):
        cache = MemoryCache()
        await cache.set("key1", {"data": "value"}, ttl=3600)
        result = await cache.get("key1")
        assert result == {"data": "value"}

    @pytest.mark.asyncio
    async def test_get_missing_key(self):
        cache = MemoryCache()
        result = await cache.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_expiration(self):
        cache = MemoryCache()
        await cache.set("key1", "value", ttl=1)

        # Should exist immediately
        assert await cache.get("key1") == "value"

        # Wait for expiration
        await asyncio.sleep(1.1)
        assert await cache.get("key1") is None

    @pytest.mark.asyncio
    async def test_delete(self):
        cache = MemoryCache()
        await cache.set("key1", "value", ttl=3600)
        await cache.delete("key1")
        assert await cache.get("key1") is None

    @pytest.mark.asyncio
    async def test_clear(self):
        cache = MemoryCache()
        await cache.set("key1", "value1", ttl=3600)
        await cache.set("key2", "value2", ttl=3600)
        await cache.clear()
        assert await cache.get("key1") is None
        assert await cache.get("key2") is None

    @pytest.mark.asyncio
    async def test_cleanup_expired(self):
        cache = MemoryCache()
        await cache.set("expires", "value", ttl=1)
        await cache.set("keeps", "value", ttl=3600)

        await asyncio.sleep(1.1)
        removed = await cache.cleanup_expired()

        assert removed == 1
        assert await cache.get("expires") is None
        assert await cache.get("keeps") == "value"


class TestJsonFileCache:
    """Tests for JSON file-based cache."""

    @pytest.mark.asyncio
    async def test_set_and_get(self, temp_cache_path: Path):
        cache = JsonFileCache(temp_cache_path)
        await cache.set("key1", {"data": "value"}, ttl=3600)
        result = await cache.get("key1")
        assert result == {"data": "value"}

    @pytest.mark.asyncio
    async def test_persistence(self, temp_cache_path: Path):
        # Write with one cache instance
        cache1 = JsonFileCache(temp_cache_path)
        await cache1.set("key1", "persisted", ttl=3600)

        # Read with a new instance
        cache2 = JsonFileCache(temp_cache_path)
        result = await cache2.get("key1")
        assert result == "persisted"

    @pytest.mark.asyncio
    async def test_creates_parent_dirs(self, tmp_path: Path):
        deep_path = tmp_path / "a" / "b" / "c" / "cache.json"
        cache = JsonFileCache(deep_path)
        await cache.set("key1", "value", ttl=3600)

        assert deep_path.exists()
        assert await cache.get("key1") == "value"

    @pytest.mark.asyncio
    async def test_expiration(self, temp_cache_path: Path):
        cache = JsonFileCache(temp_cache_path)
        await cache.set("key1", "value", ttl=1)

        await asyncio.sleep(1.1)
        assert await cache.get("key1") is None

    @pytest.mark.asyncio
    async def test_handles_corrupt_file(self, temp_cache_path: Path):
        # Write invalid JSON
        temp_cache_path.write_text("not valid json {{{")

        cache = JsonFileCache(temp_cache_path)
        # Should not crash, should return None
        result = await cache.get("key1")
        assert result is None

        # Should be able to write new data
        await cache.set("key1", "value", ttl=3600)
        assert await cache.get("key1") == "value"


class TestCacheFactory:
    """Tests for cache factory function."""

    def test_create_memory_cache(self):
        cache = create_cache("memory")
        assert isinstance(cache, MemoryCache)

    def test_create_json_cache(self, temp_cache_path: Path):
        cache = create_cache("json", temp_cache_path)
        assert isinstance(cache, JsonFileCache)

    def test_default_to_memory(self):
        cache = create_cache("unknown")
        assert isinstance(cache, MemoryCache)


class TestMakeCacheKey:
    """Tests for cache key generation."""

    def test_basic_key(self):
        key = make_cache_key("10.1038/nature12373", "bibtex", "apa", "en-US")
        assert "10.1038/nature12373" in key
        assert "bibtex" in key

    def test_normalizes_case(self):
        key1 = make_cache_key("10.1038/NATURE12373", "BibTeX", "APA", "en-US")
        key2 = make_cache_key("10.1038/nature12373", "bibtex", "apa", "en-us")
        assert key1 == key2

    def test_different_formats_different_keys(self):
        key1 = make_cache_key("10.1038/nature12373", "bibtex", "apa", "en-US")
        key2 = make_cache_key("10.1038/nature12373", "ris", "apa", "en-US")
        assert key1 != key2
