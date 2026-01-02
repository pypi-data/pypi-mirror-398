"""DiskCache-based cache backend.

Uses the diskcache library for persistent, file-based caching.
This is ideal for development and single-server deployments.

Note on async implementation:
    Operations are executed synchronously to ensure all SQLite connections
    are created in the same thread, enabling proper cleanup on close().
    Each async method yields control back to the event loop via
    `await asyncio.sleep(0)` after completing the sync operation.
    This allows other coroutines to run between cache operations while
    keeping all database connections in a single thread.

    SQLite operations are typically sub-millisecond, so the brief blocking
    is acceptable for most use cases. For high-concurrency scenarios
    requiring true non-blocking behavior, consider a Redis-based backend.
"""

import asyncio
import fnmatch
from contextlib import suppress
from pathlib import Path
from types import TracebackType
from typing import Any

import diskcache
import structlog

from .base import CacheBackend

logger = structlog.stdlib.get_logger(__name__)


class DiskCacheBackend(CacheBackend):
    """Cache backend using diskcache for persistent storage.

    This backend stores cached data in SQLite databases on disk,
    providing persistence across restarts and efficient storage.

    Attributes:
        cache_dir: Directory where cache files are stored
        default_ttl: Default TTL in seconds if not specified

    Example:
        cache = DiskCacheBackend(cache_dir=".cache/gurufocus")
        await cache.set("stock:AAPL:summary", data, ttl_seconds=3600)
        data = await cache.get("stock:AAPL:summary")
    """

    def __init__(
        self,
        cache_dir: str | Path = ".cache/gurufocus",
        default_ttl: int = 3600,
        size_limit: int = 1024 * 1024 * 1024,  # 1GB default
    ) -> None:
        """Initialize the disk cache backend.

        Args:
            cache_dir: Directory for cache storage
            default_ttl: Default TTL in seconds (1 hour default)
            size_limit: Maximum cache size in bytes (1GB default)
        """
        self._cache_dir = Path(cache_dir)
        self._default_ttl = default_ttl
        self._size_limit = size_limit

        # Create cache directory if it doesn't exist
        self._cache_dir.mkdir(parents=True, exist_ok=True)

        # Initialize diskcache
        self._cache = diskcache.Cache(
            str(self._cache_dir),
            size_limit=size_limit,
            eviction_policy="least-recently-used",
        )

        logger.debug("Initialized disk cache at %s", self._cache_dir)

    @property
    def cache_dir(self) -> Path:
        """Get the cache directory path."""
        return self._cache_dir

    @property
    def size(self) -> int:
        """Get the current cache size in bytes."""
        return int(self._cache.volume())

    @property
    def count(self) -> int:
        """Get the number of items in the cache."""
        return len(self._cache)

    async def get(self, key: str) -> Any | None:
        """Retrieve a value from the cache.

        Args:
            key: The cache key to look up

        Returns:
            The cached value, or None if not found or expired
        """
        result = self._get_sync(key)
        await asyncio.sleep(0)  # Yield to event loop
        return result

    def _get_sync(self, key: str) -> Any | None:
        """Synchronous get operation."""
        try:
            value = self._cache.get(key, default=None)
            if value is not None:
                logger.debug("Cache hit: %s", key)
            else:
                logger.debug("Cache miss: %s", key)
            return value
        except Exception as e:
            logger.warning("Cache get error for %s: %s", key, e)
            return None

    async def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        """Store a value in the cache.

        Args:
            key: The cache key
            value: The value to cache
            ttl_seconds: Time-to-live in seconds. None uses default.
        """
        ttl = ttl_seconds if ttl_seconds is not None else self._default_ttl
        self._set_sync(key, value, ttl)
        await asyncio.sleep(0)  # Yield to event loop

    def _set_sync(self, key: str, value: Any, ttl: int) -> None:
        """Synchronous set operation."""
        try:
            self._cache.set(key, value, expire=ttl)
            logger.debug("Cache set: %s (TTL: %ds)", key, ttl)
        except Exception as e:
            logger.warning("Cache set error for %s: %s", key, e)

    async def delete(self, key: str) -> bool:
        """Delete a value from the cache.

        Args:
            key: The cache key to delete

        Returns:
            True if the key existed and was deleted
        """
        result = self._delete_sync(key)
        await asyncio.sleep(0)  # Yield to event loop
        return result

    def _delete_sync(self, key: str) -> bool:
        """Synchronous delete operation."""
        try:
            existed = key in self._cache
            if existed:
                del self._cache[key]
                logger.debug("Cache delete: %s", key)
            return existed
        except Exception as e:
            logger.warning("Cache delete error for %s: %s", key, e)
            return False

    async def clear(self) -> None:
        """Clear all entries from the cache."""
        self._clear_sync()
        await asyncio.sleep(0)  # Yield to event loop

    def _clear_sync(self) -> None:
        """Synchronous clear operation."""
        try:
            self._cache.clear()
            logger.info("Cache cleared")
        except Exception as e:
            logger.warning("Cache clear error: %s", e)

    async def exists(self, key: str) -> bool:
        """Check if a key exists in the cache.

        Args:
            key: The cache key to check

        Returns:
            True if the key exists and hasn't expired
        """
        result = self._exists_sync(key)
        await asyncio.sleep(0)  # Yield to event loop
        return result

    def _exists_sync(self, key: str) -> bool:
        """Synchronous exists check."""
        try:
            return key in self._cache
        except Exception as e:
            logger.warning("Cache exists error for %s: %s", key, e)
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a glob pattern.

        Args:
            pattern: Glob-style pattern (e.g., "summary:AAPL:*")

        Returns:
            Number of keys deleted
        """
        result = self._delete_pattern_sync(pattern)
        await asyncio.sleep(0)  # Yield to event loop
        return result

    def _delete_pattern_sync(self, pattern: str) -> int:
        """Synchronous pattern delete."""
        deleted = 0
        try:
            # Iterate through all keys and match pattern
            keys_to_delete = []
            for key in self._cache.iterkeys():
                if fnmatch.fnmatch(key, pattern):
                    keys_to_delete.append(key)

            for key in keys_to_delete:
                del self._cache[key]
                deleted += 1

            if deleted > 0:
                logger.debug("Cache delete pattern %s: %d keys", pattern, deleted)
        except Exception as e:
            logger.warning("Cache delete pattern error for %s: %s", pattern, e)

        return deleted

    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        """Retrieve multiple values from the cache.

        Args:
            keys: List of cache keys to look up

        Returns:
            Dictionary of key -> value for keys that were found
        """
        result = self._get_many_sync(keys)
        await asyncio.sleep(0)  # Yield to event loop
        return result

    def _get_many_sync(self, keys: list[str]) -> dict[str, Any]:
        """Synchronous get_many operation."""
        result = {}
        for key in keys:
            value = self._get_sync(key)
            if value is not None:
                result[key] = value
        return result

    async def close(self) -> None:
        """Close the cache and release resources."""
        # Close synchronously in the current thread to properly clean up
        # thread-local connections. Using run_in_executor would run in a
        # different thread and miss the connections created in this thread.
        self._close_sync()
        await asyncio.sleep(0)  # Yield to event loop

    def _close_sync(self) -> None:
        """Synchronous close operation."""
        try:
            self._cache.close()
            # Clear thread-local storage to prevent ResourceWarnings
            # about unclosed sqlite3.Connection objects
            if hasattr(self._cache, "_local"):
                local = self._cache._local
                if hasattr(local, "con"):
                    with suppress(Exception):
                        local.con.close()
                local.__dict__.clear()
            logger.debug("Cache closed")
        except Exception as e:
            logger.warning("Cache close error: %s", e)

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        return {
            "cache_dir": str(self._cache_dir),
            "size_bytes": self.size,
            "size_mb": round(self.size / (1024 * 1024), 2),
            "item_count": self.count,
            "size_limit_bytes": self._size_limit,
            "size_limit_mb": round(self._size_limit / (1024 * 1024), 2),
        }

    async def __aenter__(self) -> "DiskCacheBackend":
        """Enter async context manager."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit async context manager, closing cache."""
        await self.close()
