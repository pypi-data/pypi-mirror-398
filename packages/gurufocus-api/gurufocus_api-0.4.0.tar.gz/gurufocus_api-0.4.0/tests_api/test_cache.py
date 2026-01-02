"""Tests for caching infrastructure."""

import tempfile
from collections.abc import Generator
from contextlib import suppress
from pathlib import Path

import pytest
import respx
from httpx import Response

from gurufocus_api import GuruFocusClient
from gurufocus_api.cache import CacheCategory, CacheManager, DiskCacheBackend, get_cache_config


class TestCacheConfig:
    """Tests for cache configuration."""

    def test_get_cache_config(self) -> None:
        """Test getting cache config for a category."""
        config = get_cache_config(CacheCategory.SUMMARY)
        assert config.ttl.total_seconds() > 0

    def test_cache_tiers(self) -> None:
        """Test different cache tiers have different TTLs."""
        summary_config = get_cache_config(CacheCategory.SUMMARY)
        financials_config = get_cache_config(CacheCategory.FINANCIALS)
        profile_config = get_cache_config(CacheCategory.PROFILE)

        # Financials should have longer TTL than summary (quarterly vs daily)
        assert financials_config.ttl > summary_config.ttl

        # Profile should have longer TTL (static data)
        assert profile_config.ttl.days >= 30


class TestDiskCacheBackend:
    """Tests for disk cache backend."""

    @pytest.fixture
    def cache_dir(self) -> Path:
        """Create a temporary cache directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def cache(self, cache_dir: Path) -> Generator[DiskCacheBackend, None, None]:
        """Create a disk cache backend."""
        backend = DiskCacheBackend(cache_dir=cache_dir)
        yield backend
        # Close the cache and clear thread-local storage to prevent ResourceWarnings
        cache = backend._cache
        cache.close()
        # Clear thread-local connection storage
        if hasattr(cache, "_local"):
            if hasattr(cache._local, "con"):
                with suppress(Exception):
                    cache._local.con.close()
            cache._local.__dict__.clear()

    async def test_set_and_get(self, cache: DiskCacheBackend) -> None:
        """Test basic set and get operations."""
        await cache.set("test_key", {"value": 123}, ttl_seconds=3600)
        result = await cache.get("test_key")
        assert result == {"value": 123}

    async def test_get_missing_key(self, cache: DiskCacheBackend) -> None:
        """Test getting a non-existent key returns None."""
        result = await cache.get("nonexistent")
        assert result is None

    async def test_delete(self, cache: DiskCacheBackend) -> None:
        """Test deleting a key."""
        await cache.set("to_delete", "value")
        assert await cache.exists("to_delete")

        deleted = await cache.delete("to_delete")
        assert deleted is True
        assert not await cache.exists("to_delete")

    async def test_delete_nonexistent(self, cache: DiskCacheBackend) -> None:
        """Test deleting a non-existent key."""
        deleted = await cache.delete("nonexistent")
        assert deleted is False

    async def test_clear(self, cache: DiskCacheBackend) -> None:
        """Test clearing all entries."""
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")

        await cache.clear()

        assert not await cache.exists("key1")
        assert not await cache.exists("key2")

    async def test_exists(self, cache: DiskCacheBackend) -> None:
        """Test checking key existence."""
        assert not await cache.exists("test_key")
        await cache.set("test_key", "value")
        assert await cache.exists("test_key")

    async def test_get_many(self, cache: DiskCacheBackend) -> None:
        """Test getting multiple keys."""
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")

        result = await cache.get_many(["key1", "key2", "key3"])
        assert result == {"key1": "value1", "key2": "value2"}

    async def test_delete_pattern(self, cache: DiskCacheBackend) -> None:
        """Test deleting keys by pattern."""
        await cache.set("summary:AAPL", "data1")
        await cache.set("summary:MSFT", "data2")
        await cache.set("financials:AAPL", "data3")

        deleted = await cache.delete_pattern("summary:*")
        assert deleted == 2

        assert not await cache.exists("summary:AAPL")
        assert not await cache.exists("summary:MSFT")
        assert await cache.exists("financials:AAPL")

    def test_get_stats(self, cache: DiskCacheBackend) -> None:
        """Test getting cache statistics."""
        stats = cache.get_stats()
        assert "cache_dir" in stats
        assert "size_bytes" in stats
        assert "item_count" in stats


class TestCacheManager:
    """Tests for cache manager."""

    @pytest.fixture
    def cache_dir(self) -> Path:
        """Create a temporary cache directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def manager(self, cache_dir: Path) -> Generator[CacheManager, None, None]:
        """Create a cache manager."""
        mgr = CacheManager(cache_dir=cache_dir, enabled=True)
        yield mgr
        # Close the cache and clear thread-local storage to prevent ResourceWarnings
        if mgr._backend is not None and hasattr(mgr._backend, "_cache"):
            cache = mgr._backend._cache
            cache.close()
            # Clear thread-local connection storage
            if hasattr(cache, "_local"):
                if hasattr(cache._local, "con"):
                    with suppress(Exception):
                        cache._local.con.close()
                cache._local.__dict__.clear()

    async def test_set_and_get_by_category(self, manager: CacheManager) -> None:
        """Test set/get using cache categories."""
        data = {"symbol": "AAPL", "price": 175.0}
        await manager.set(CacheCategory.SUMMARY, "AAPL", value=data)

        result = await manager.get(CacheCategory.SUMMARY, "AAPL")
        assert result == data

    async def test_cache_miss(self, manager: CacheManager) -> None:
        """Test cache miss increments counter."""
        result = await manager.get(CacheCategory.SUMMARY, "NONEXISTENT")
        assert result is None
        assert manager.misses == 1

    async def test_cache_hit(self, manager: CacheManager) -> None:
        """Test cache hit increments counter."""
        await manager.set(CacheCategory.SUMMARY, "AAPL", value={"test": True})
        await manager.get(CacheCategory.SUMMARY, "AAPL")

        assert manager.hits == 1
        assert manager.misses == 0

    async def test_bypass_cache(self, manager: CacheManager) -> None:
        """Test bypassing cache."""
        await manager.set(CacheCategory.SUMMARY, "AAPL", value={"cached": True})

        # Bypass should return None even if data exists
        result = await manager.get(CacheCategory.SUMMARY, "AAPL", bypass=True)
        assert result is None
        assert manager.misses == 1

    async def test_invalidate_symbol(self, manager: CacheManager) -> None:
        """Test invalidating all data for a symbol."""
        await manager.set(CacheCategory.SUMMARY, "AAPL", value={"type": "summary"})
        await manager.set(CacheCategory.FINANCIALS, "AAPL", value={"type": "financials"})
        await manager.set(CacheCategory.SUMMARY, "MSFT", value={"type": "summary"})

        count = await manager.invalidate_symbol("AAPL")
        assert count == 2

        assert await manager.get(CacheCategory.SUMMARY, "AAPL") is None
        assert await manager.get(CacheCategory.FINANCIALS, "AAPL") is None
        # MSFT should still exist
        assert await manager.get(CacheCategory.SUMMARY, "MSFT") is not None

    async def test_disabled_cache(self, cache_dir: Path) -> None:
        """Test that disabled cache doesn't store anything."""
        manager = CacheManager(cache_dir=cache_dir, enabled=False)

        await manager.set(CacheCategory.SUMMARY, "AAPL", value={"test": True})
        result = await manager.get(CacheCategory.SUMMARY, "AAPL")

        assert result is None
        assert not manager.enabled

    def test_hit_rate(self, manager: CacheManager) -> None:
        """Test hit rate calculation."""
        assert manager.hit_rate == 0.0

        manager._hits = 3
        manager._misses = 1
        assert manager.hit_rate == 0.75

    def test_get_stats(self, manager: CacheManager) -> None:
        """Test getting manager statistics."""
        stats = manager.get_stats()
        assert "enabled" in stats
        assert "hits" in stats
        assert "misses" in stats
        assert "hit_rate" in stats


# Sample API response fixture using correct format from actual API
SAMPLE_SUMMARY_RESPONSE = {
    "summary": {
        "general": {
            "company": "Apple Inc",
            "price": 175.43,
            "currency": "$",
            "country": "USA",
            "sector": "Technology",
            "gf_score": "90",
            "rank_financial_strength": "7",
            "rank_profitability": "9",
        },
        "chart": {
            "GF Value": "200.00",
        },
        "ratio": {},
    }
}


class TestCachingIntegration:
    """Tests for caching integrated with the client."""

    @pytest.fixture
    def cache_dir(self) -> Path:
        """Create a temporary cache directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @respx.mock
    async def test_cache_hit_avoids_api_call(self, cache_dir: Path) -> None:
        """Test that cache hit doesn't make API call."""
        api_token = "test-token"
        route = respx.get(
            f"https://api.gurufocus.com/public/user/{api_token}/stock/AAPL/summary"
        ).mock(return_value=Response(200, json=SAMPLE_SUMMARY_RESPONSE))

        async with GuruFocusClient(
            api_token=api_token,
            cache_dir=str(cache_dir),
        ) as client:
            # First call - should hit API
            summary1 = await client.stocks.get_summary("AAPL")
            assert route.call_count == 1

            # Second call - should use cache
            summary2 = await client.stocks.get_summary("AAPL")
            assert route.call_count == 1  # No additional API call

            assert summary1.symbol == summary2.symbol
            assert client.cache.hits == 1
            assert client.cache.misses == 1

    @respx.mock
    async def test_bypass_cache_makes_api_call(self, cache_dir: Path) -> None:
        """Test that bypass_cache always makes API call."""
        api_token = "test-token"
        route = respx.get(
            f"https://api.gurufocus.com/public/user/{api_token}/stock/AAPL/summary"
        ).mock(return_value=Response(200, json=SAMPLE_SUMMARY_RESPONSE))

        async with GuruFocusClient(
            api_token=api_token,
            cache_dir=str(cache_dir),
        ) as client:
            # First call with bypass
            await client.stocks.get_summary("AAPL", bypass_cache=True)
            assert route.call_count == 1

            # Second call with bypass - should still hit API
            await client.stocks.get_summary("AAPL", bypass_cache=True)
            assert route.call_count == 2

    @respx.mock
    async def test_cache_disabled(self, cache_dir: Path) -> None:
        """Test that cache_enabled=False doesn't cache."""
        api_token = "test-token"
        route = respx.get(
            f"https://api.gurufocus.com/public/user/{api_token}/stock/AAPL/summary"
        ).mock(return_value=Response(200, json=SAMPLE_SUMMARY_RESPONSE))

        async with GuruFocusClient(
            api_token=api_token,
            cache_enabled=False,
        ) as client:
            # Both calls should hit API
            await client.stocks.get_summary("AAPL")
            await client.stocks.get_summary("AAPL")
            assert route.call_count == 2

    @respx.mock
    async def test_different_symbols_cached_separately(self, cache_dir: Path) -> None:
        """Test that different symbols are cached separately."""
        api_token = "test-token"

        respx.get(f"https://api.gurufocus.com/public/user/{api_token}/stock/AAPL/summary").mock(
            return_value=Response(200, json=SAMPLE_SUMMARY_RESPONSE)
        )

        msft_response = {
            "summary": {
                "general": {
                    "company": "Microsoft Corp",
                    "price": 350.0,
                    "currency": "$",
                },
                "chart": {},
                "ratio": {},
            }
        }
        respx.get(f"https://api.gurufocus.com/public/user/{api_token}/stock/MSFT/summary").mock(
            return_value=Response(200, json=msft_response)
        )

        async with GuruFocusClient(
            api_token=api_token,
            cache_dir=str(cache_dir),
        ) as client:
            aapl = await client.stocks.get_summary("AAPL")
            msft = await client.stocks.get_summary("MSFT")

            assert aapl.symbol == "AAPL"
            assert msft.symbol == "MSFT"
            assert aapl.general.company_name != msft.general.company_name

    async def test_cache_stats_accessible(self, cache_dir: Path) -> None:
        """Test that cache stats are accessible from client."""
        async with GuruFocusClient(
            api_token="test-token",
            cache_dir=str(cache_dir),
        ) as client:
            stats = client.cache.get_stats()
            assert "enabled" in stats
            assert stats["enabled"] is True
