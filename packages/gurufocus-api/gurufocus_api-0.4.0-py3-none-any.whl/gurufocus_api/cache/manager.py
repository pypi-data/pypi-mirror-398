"""Cache manager with tier-aware caching and bypass options.

The CacheManager provides a high-level interface for caching API responses
with support for:
- Category-based TTL configuration
- Cache bypass for fresh data
- Symbol-based cache invalidation
- Statistics and monitoring
"""

from pathlib import Path
from types import TracebackType
from typing import Any

import structlog

from .base import CacheBackend
from .config import CacheCategory, build_cache_key, get_ttl_seconds
from .disk import DiskCacheBackend

logger = structlog.stdlib.get_logger(__name__)


class CacheManager:
    """High-level cache manager for GuruFocus API responses.

    This manager handles cache operations with category-aware TTLs,
    providing a clean interface for the API client.

    Attributes:
        enabled: Whether caching is enabled
        backend: The underlying cache backend

    Example:
        manager = CacheManager(cache_dir=".cache/gurufocus")

        # Get with automatic TTL
        data = await manager.get(CacheCategory.SUMMARY, "AAPL")

        # Set with automatic TTL
        await manager.set(CacheCategory.SUMMARY, "AAPL", summary_data)

        # Bypass cache for fresh data
        data = await manager.get(CacheCategory.SUMMARY, "AAPL", bypass=True)
    """

    def __init__(
        self,
        cache_dir: str | Path = ".cache/gurufocus",
        enabled: bool = True,
        backend: CacheBackend | None = None,
    ) -> None:
        """Initialize the cache manager.

        Args:
            cache_dir: Directory for cache storage (if using default backend)
            enabled: Whether caching is enabled
            backend: Custom cache backend. If None, uses DiskCacheBackend.
        """
        self._enabled = enabled
        self._cache_dir = Path(cache_dir)

        self._backend: CacheBackend | None
        if backend is not None:
            self._backend = backend
        elif enabled:
            self._backend = DiskCacheBackend(cache_dir=cache_dir)
        else:
            self._backend = None

        # Track statistics
        self._hits = 0
        self._misses = 0

    @property
    def enabled(self) -> bool:
        """Check if caching is enabled."""
        return self._enabled and self._backend is not None

    @property
    def hits(self) -> int:
        """Get the number of cache hits."""
        return self._hits

    @property
    def misses(self) -> int:
        """Get the number of cache misses."""
        return self._misses

    @property
    def hit_rate(self) -> float:
        """Get the cache hit rate (0.0 to 1.0)."""
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0

    async def get(
        self,
        category: CacheCategory,
        *key_parts: str,
        bypass: bool = False,
    ) -> Any | None:
        """Get a value from the cache.

        Args:
            category: The cache category (determines TTL)
            *key_parts: Additional key parts (e.g., symbol)
            bypass: If True, skip cache and return None

        Returns:
            Cached value or None if not found/bypassed
        """
        if not self.enabled or bypass:
            self._misses += 1
            return None

        key = build_cache_key(category, *key_parts)
        value = await self._backend.get(key)  # type: ignore[union-attr]

        if value is not None:
            self._hits += 1
            logger.debug("Cache hit: %s", key)
        else:
            self._misses += 1
            logger.debug("Cache miss: %s", key)

        return value

    async def set(
        self,
        category: CacheCategory,
        *key_parts: str,
        value: Any,
        ttl_override: int | None = None,
    ) -> None:
        """Store a value in the cache.

        Args:
            category: The cache category (determines TTL)
            *key_parts: Additional key parts (e.g., symbol)
            value: The value to cache
            ttl_override: Override the category's default TTL (seconds)
        """
        if not self.enabled:
            return

        key = build_cache_key(category, *key_parts)
        ttl = ttl_override if ttl_override is not None else get_ttl_seconds(category)

        await self._backend.set(key, value, ttl_seconds=ttl)  # type: ignore[union-attr]
        logger.debug("Cache set: %s (TTL: %ds)", key, ttl)

    async def delete(
        self,
        category: CacheCategory,
        *key_parts: str,
    ) -> bool:
        """Delete a specific cache entry.

        Args:
            category: The cache category
            *key_parts: Additional key parts

        Returns:
            True if the entry was deleted
        """
        if not self.enabled:
            return False

        key = build_cache_key(category, *key_parts)
        return await self._backend.delete(key)  # type: ignore[union-attr]

    async def invalidate_symbol(self, symbol: str) -> int:
        """Invalidate all cached data for a symbol.

        Useful when you know a stock's data has changed
        (e.g., after earnings).

        Args:
            symbol: The stock symbol to invalidate

        Returns:
            Number of cache entries deleted
        """
        if not self.enabled:
            return 0

        symbol = symbol.upper()
        pattern = f"*:{symbol}*"
        count = await self._backend.delete_pattern(pattern)  # type: ignore[union-attr]

        logger.info("Invalidated %d cache entries for %s", count, symbol)
        return count

    async def invalidate_category(self, category: CacheCategory) -> int:
        """Invalidate all cached data for a category.

        Args:
            category: The cache category to invalidate

        Returns:
            Number of cache entries deleted
        """
        if not self.enabled:
            return 0

        pattern = f"{category.value}:*"
        count = await self._backend.delete_pattern(pattern)  # type: ignore[union-attr]

        logger.info("Invalidated %d cache entries for category %s", count, category.value)
        return count

    async def clear(self) -> None:
        """Clear all cached data."""
        if not self.enabled:
            return

        await self._backend.clear()  # type: ignore[union-attr]
        self._hits = 0
        self._misses = 0
        logger.info("Cache cleared")

    async def close(self) -> None:
        """Close the cache manager and release resources."""
        if self._backend is not None:
            await self._backend.close()

    def reset_stats(self) -> None:
        """Reset hit/miss statistics."""
        self._hits = 0
        self._misses = 0

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        stats = {
            "enabled": self.enabled,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self.hit_rate, 3),
        }

        if self.enabled and isinstance(self._backend, DiskCacheBackend):
            stats.update(self._backend.get_stats())

        return stats

    async def __aenter__(self) -> "CacheManager":
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


class NullCacheManager(CacheManager):
    """A cache manager that doesn't cache anything.

    Useful for testing or when caching should be completely disabled.
    """

    def __init__(self) -> None:
        """Initialize null cache manager."""
        super().__init__(enabled=False)

    async def get(
        self,
        category: CacheCategory,
        *key_parts: str,
        bypass: bool = False,
    ) -> None:
        """Always returns None."""
        return None

    async def set(
        self,
        category: CacheCategory,
        *key_parts: str,
        value: Any,
        ttl_override: int | None = None,
    ) -> None:
        """Does nothing."""
        pass

    async def delete(
        self,
        category: CacheCategory,
        *key_parts: str,
    ) -> bool:
        """Always returns False."""
        return False
