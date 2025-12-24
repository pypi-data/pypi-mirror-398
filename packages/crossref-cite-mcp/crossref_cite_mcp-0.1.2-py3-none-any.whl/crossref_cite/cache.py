"""TTL-based caching with memory and JSON file backends."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger("crossref_cite.cache")


@dataclass
class CacheEntry:
    """A cached value with expiration timestamp."""

    value: Any
    expires_at: float  # Unix timestamp

    def is_expired(self) -> bool:
        """Check if this entry has expired."""
        return time.time() >= self.expires_at


class CacheBackend(ABC):
    """Abstract base class for cache backends."""

    @abstractmethod
    async def get(self, key: str) -> Any | None:
        """Get a value from cache, or None if not found/expired."""
        ...

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int) -> None:
        """Set a value in cache with TTL in seconds."""
        ...

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete a key from cache."""
        ...

    @abstractmethod
    async def clear(self) -> None:
        """Clear all cached values."""
        ...


class MemoryCache(CacheBackend):
    """In-memory TTL cache with async-safe access."""

    def __init__(self) -> None:
        self._store: dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Any | None:
        async with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            if entry.is_expired():
                del self._store[key]
                return None
            return entry.value

    async def set(self, key: str, value: Any, ttl: int) -> None:
        async with self._lock:
            self._store[key] = CacheEntry(
                value=value,
                expires_at=time.time() + ttl,
            )

    async def delete(self, key: str) -> None:
        async with self._lock:
            self._store.pop(key, None)

    async def clear(self) -> None:
        async with self._lock:
            self._store.clear()

    async def cleanup_expired(self) -> int:
        """Remove all expired entries. Returns count of removed entries."""
        async with self._lock:
            now = time.time()
            expired_keys = [k for k, v in self._store.items() if v.expires_at <= now]
            for key in expired_keys:
                del self._store[key]
            return len(expired_keys)


class JsonFileCache(CacheBackend):
    """
    JSON file-based persistent cache.

    Stores all cache entries in a single JSON file.
    Performs lazy cleanup of expired entries on read.
    """

    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = asyncio.Lock()
        self._dirty = False
        self._store: dict[str, dict[str, Any]] = {}
        self._loaded = False

    async def _ensure_loaded(self) -> None:
        """Load cache from disk if not already loaded."""
        if self._loaded:
            return

        if self._path.exists():
            try:
                content = self._path.read_text(encoding="utf-8")
                data = json.loads(content)
                # Validate structure
                if isinstance(data, dict):
                    self._store = data
                    logger.debug("Loaded %d entries from cache file", len(self._store))
            except (OSError, json.JSONDecodeError) as e:
                logger.warning("Failed to load cache file: %s", e)
                self._store = {}
        else:
            self._store = {}

        self._loaded = True

    async def _save(self) -> None:
        """Save cache to disk if dirty."""
        if not self._dirty:
            return

        try:
            # Ensure parent directory exists
            self._path.parent.mkdir(parents=True, exist_ok=True)

            # Write atomically via temp file
            temp_path = self._path.with_suffix(".tmp")
            temp_path.write_text(
                json.dumps(self._store, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            temp_path.rename(self._path)

            self._dirty = False
            logger.debug("Saved %d entries to cache file", len(self._store))
        except OSError as e:
            logger.error("Failed to save cache file: %s", e)

    async def get(self, key: str) -> Any | None:
        async with self._lock:
            await self._ensure_loaded()

            entry_data = self._store.get(key)
            if entry_data is None:
                return None

            entry = CacheEntry(
                value=entry_data["value"],
                expires_at=entry_data["expires_at"],
            )

            if entry.is_expired():
                del self._store[key]
                self._dirty = True
                await self._save()
                return None

            return entry.value

    async def set(self, key: str, value: Any, ttl: int) -> None:
        async with self._lock:
            await self._ensure_loaded()

            self._store[key] = {
                "value": value,
                "expires_at": time.time() + ttl,
            }
            self._dirty = True
            await self._save()

    async def delete(self, key: str) -> None:
        async with self._lock:
            await self._ensure_loaded()

            if key in self._store:
                del self._store[key]
                self._dirty = True
                await self._save()

    async def clear(self) -> None:
        async with self._lock:
            self._store = {}
            self._dirty = True
            await self._save()

    async def cleanup_expired(self) -> int:
        """Remove all expired entries. Returns count of removed entries."""
        async with self._lock:
            await self._ensure_loaded()

            now = time.time()
            expired_keys = [
                k for k, v in self._store.items() if v.get("expires_at", 0) <= now
            ]

            for key in expired_keys:
                del self._store[key]

            if expired_keys:
                self._dirty = True
                await self._save()

            return len(expired_keys)


def create_cache(backend: str, path: Path | None = None) -> CacheBackend:
    """
    Factory function to create appropriate cache backend.

    Args:
        backend: "memory" or "json"
        path: File path for json backend (ignored for memory)

    Returns:
        CacheBackend instance
    """
    if backend == "json":
        if path is None:
            path = Path.home() / ".crossref-cite" / "cache.json"
        return JsonFileCache(path)
    else:
        return MemoryCache()


def make_cache_key(doi: str, fmt: str, style: str, locale: str) -> str:
    """
    Generate a cache key for content negotiation results.

    Args:
        doi: The DOI being looked up
        fmt: Citation format (csl-json, bibtex, etc.)
        style: CSL style for formatted output
        locale: Locale for formatted output

    Returns:
        Cache key string
    """
    # Normalize inputs
    doi = doi.lower().strip()
    fmt = fmt.lower().strip()
    style = style.lower().strip()
    locale = locale.lower().strip()

    return f"cn::{doi}::{fmt}::{style}::{locale}"
