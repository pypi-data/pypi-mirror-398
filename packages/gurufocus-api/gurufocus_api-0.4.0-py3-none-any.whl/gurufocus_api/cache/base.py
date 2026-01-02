"""Abstract base class for cache backends."""

from abc import ABC, abstractmethod
from typing import Any


class CacheBackend(ABC):
    """Abstract interface for cache backends.

    All cache implementations must inherit from this class and implement
    the required methods. This allows swapping cache backends without
    changing the rest of the codebase.
    """

    @abstractmethod
    async def get(self, key: str) -> Any | None:
        """Retrieve a value from the cache.

        Args:
            key: The cache key to look up

        Returns:
            The cached value, or None if not found or expired
        """
        ...

    @abstractmethod
    async def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        """Store a value in the cache.

        Args:
            key: The cache key
            value: The value to cache (must be JSON-serializable)
            ttl_seconds: Time-to-live in seconds. None means use default.
        """
        ...

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete a value from the cache.

        Args:
            key: The cache key to delete

        Returns:
            True if the key existed and was deleted, False otherwise
        """
        ...

    @abstractmethod
    async def clear(self) -> None:
        """Clear all entries from the cache."""
        ...

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if a key exists in the cache.

        Args:
            key: The cache key to check

        Returns:
            True if the key exists and hasn't expired
        """
        ...

    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        """Retrieve multiple values from the cache.

        Default implementation calls get() for each key.
        Backends may override for better performance.

        Args:
            keys: List of cache keys to look up

        Returns:
            Dictionary of key -> value for keys that were found
        """
        result = {}
        for key in keys:
            value = await self.get(key)
            if value is not None:
                result[key] = value
        return result

    async def set_many(self, items: dict[str, Any], ttl_seconds: int | None = None) -> None:
        """Store multiple values in the cache.

        Default implementation calls set() for each item.
        Backends may override for better performance.

        Args:
            items: Dictionary of key -> value to cache
            ttl_seconds: Time-to-live in seconds for all items
        """
        for key, value in items.items():
            await self.set(key, value, ttl_seconds)

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern.

        Default implementation does nothing. Backends that support
        pattern matching should override this.

        Args:
            pattern: Glob-style pattern (e.g., "stock:AAPL:*")

        Returns:
            Number of keys deleted
        """
        return 0

    async def close(self) -> None:
        """Close the cache connection and release resources.

        Default implementation does nothing. Override if the backend
        needs cleanup.
        """
        return None
