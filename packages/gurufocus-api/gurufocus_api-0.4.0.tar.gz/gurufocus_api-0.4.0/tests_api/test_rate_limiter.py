"""Tests for rate limiting."""

import asyncio
import time

import pytest
import respx
from httpx import Response

from gurufocus_api import GuruFocusClient, RateLimitConfig, RateLimiter
from gurufocus_api.exceptions import RateLimitError
from gurufocus_api.rate_limiter import NullRateLimiter


class TestRateLimitConfig:
    """Tests for rate limit configuration."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        config = RateLimitConfig()
        assert config.requests_per_minute == 10.0
        assert config.requests_per_day == 0  # unlimited
        assert config.burst_size == 5

    def test_custom_config(self) -> None:
        """Test custom configuration values."""
        config = RateLimitConfig(
            requests_per_minute=60.0,
            requests_per_day=1000,
            burst_size=10,
        )
        assert config.requests_per_minute == 60.0
        assert config.requests_per_day == 1000
        assert config.burst_size == 10


class TestRateLimiter:
    """Tests for the token bucket rate limiter."""

    def test_initial_tokens(self) -> None:
        """Test that limiter starts with full burst of tokens."""
        config = RateLimitConfig(burst_size=5)
        limiter = RateLimiter(config)
        assert limiter.tokens == 5.0

    def test_can_acquire_with_tokens(self) -> None:
        """Test can_acquire returns True when tokens available."""
        config = RateLimitConfig(burst_size=5)
        limiter = RateLimiter(config)
        assert limiter.can_acquire() is True

    @pytest.mark.asyncio
    async def test_acquire_consumes_token(self) -> None:
        """Test that acquire consumes a token."""
        config = RateLimitConfig(burst_size=5)
        limiter = RateLimiter(config)

        initial_tokens = limiter.tokens
        result = await limiter.acquire()

        assert result is True
        # Token count should have decreased by 1
        # (may have slightly refilled, so check it decreased)
        assert limiter.tokens < initial_tokens

    @pytest.mark.asyncio
    async def test_acquire_increments_daily_count(self) -> None:
        """Test that acquire increments daily count."""
        config = RateLimitConfig()
        limiter = RateLimiter(config)

        assert limiter.daily_count == 0
        await limiter.acquire()
        assert limiter.daily_count == 1

    @pytest.mark.asyncio
    async def test_burst_limit(self) -> None:
        """Test that burst size limits immediate requests."""
        config = RateLimitConfig(burst_size=3, requests_per_minute=60.0)
        limiter = RateLimiter(config)

        # Should be able to acquire burst_size tokens immediately
        for _ in range(3):
            assert limiter.can_acquire() is True
            result = await limiter.acquire(timeout=0.001)
            assert result is True

        # Next one should require waiting (can_acquire = False)
        assert limiter.can_acquire() is False

    @pytest.mark.asyncio
    async def test_tokens_refill_over_time(self) -> None:
        """Test that tokens refill based on rate."""
        # 60 requests per minute = 1 per second
        config = RateLimitConfig(burst_size=2, requests_per_minute=60.0)
        limiter = RateLimiter(config)

        # Consume all tokens
        await limiter.acquire()
        await limiter.acquire()
        assert limiter.can_acquire() is False

        # Wait for token to refill (1 second = 1 token at 60 rpm)
        await asyncio.sleep(0.1)  # Wait 0.1s = 0.1 tokens

        # Should have partially refilled
        limiter._refill_tokens()
        assert limiter.tokens > 0

    @pytest.mark.asyncio
    async def test_daily_limit_blocks_requests(self) -> None:
        """Test that daily limit blocks requests when exceeded."""
        config = RateLimitConfig(
            burst_size=10,
            requests_per_minute=1000.0,  # High rate so we don't wait
            requests_per_day=3,
        )
        limiter = RateLimiter(config)

        # Use up daily limit
        for _ in range(3):
            result = await limiter.acquire()
            assert result is True

        # Daily limit should be reached
        assert limiter.daily_count == 3
        assert limiter.daily_remaining == 0

        # Next acquire should fail
        result = await limiter.acquire(timeout=0.001)
        assert result is False

    def test_daily_remaining_unlimited(self) -> None:
        """Test daily_remaining returns None when unlimited."""
        config = RateLimitConfig(requests_per_day=0)
        limiter = RateLimiter(config)
        assert limiter.daily_remaining is None

    def test_daily_remaining_with_limit(self) -> None:
        """Test daily_remaining returns correct count."""
        config = RateLimitConfig(requests_per_day=100)
        limiter = RateLimiter(config)
        assert limiter.daily_remaining == 100

    def test_time_until_available_immediate(self) -> None:
        """Test time_until_available returns 0 when tokens available."""
        config = RateLimitConfig(burst_size=5)
        limiter = RateLimiter(config)
        assert limiter.time_until_available() == 0.0

    def test_time_until_available_waiting(self) -> None:
        """Test time_until_available returns positive time when no tokens."""
        config = RateLimitConfig(burst_size=1, requests_per_minute=60.0)
        limiter = RateLimiter(config)

        # Consume all tokens
        limiter._tokens = 0.0
        limiter._last_update = time.monotonic()

        wait_time = limiter.time_until_available()
        # At 60 rpm, need ~1 second for 1 token
        assert 0.5 < wait_time < 1.5

    @pytest.mark.asyncio
    async def test_acquire_or_raise_success(self) -> None:
        """Test acquire_or_raise succeeds when tokens available."""
        config = RateLimitConfig(burst_size=5)
        limiter = RateLimiter(config)

        # Should not raise
        await limiter.acquire_or_raise()
        assert limiter.daily_count == 1

    @pytest.mark.asyncio
    async def test_acquire_or_raise_timeout(self) -> None:
        """Test acquire_or_raise raises on timeout."""
        config = RateLimitConfig(burst_size=1, requests_per_minute=6.0)
        limiter = RateLimiter(config)

        # Consume token
        await limiter.acquire()

        # Should raise RateLimitError
        with pytest.raises(RateLimitError) as exc_info:
            await limiter.acquire_or_raise(timeout=0.001)

        assert exc_info.value.retry_after is not None
        assert exc_info.value.retry_after > 0

    @pytest.mark.asyncio
    async def test_acquire_or_raise_daily_exceeded(self) -> None:
        """Test acquire_or_raise raises when daily limit exceeded."""
        config = RateLimitConfig(
            burst_size=10,
            requests_per_minute=1000.0,
            requests_per_day=1,
        )
        limiter = RateLimiter(config)

        # Use up daily limit
        await limiter.acquire()

        # Should raise RateLimitError with long retry_after
        with pytest.raises(RateLimitError) as exc_info:
            await limiter.acquire_or_raise(timeout=0.001)

        assert "Daily API rate limit exceeded" in str(exc_info.value)

    def test_reset(self) -> None:
        """Test reset clears all state."""
        config = RateLimitConfig(burst_size=5)
        limiter = RateLimiter(config)

        # Modify state
        limiter._tokens = 0.0
        limiter._daily_count = 100

        # Reset
        limiter.reset()

        assert limiter.tokens == 5.0
        assert limiter.daily_count == 0

    def test_get_stats(self) -> None:
        """Test get_stats returns expected keys."""
        config = RateLimitConfig()
        limiter = RateLimiter(config)

        stats = limiter.get_stats()

        assert "tokens" in stats
        assert "burst_size" in stats
        assert "requests_per_minute" in stats
        assert "daily_count" in stats
        assert "daily_limit" in stats
        assert "daily_remaining" in stats
        assert "time_until_available" in stats


class TestNullRateLimiter:
    """Tests for the null rate limiter."""

    def test_can_acquire_always_true(self) -> None:
        """Test can_acquire always returns True."""
        limiter = NullRateLimiter()
        assert limiter.can_acquire() is True

    def test_time_until_available_always_zero(self) -> None:
        """Test time_until_available always returns 0."""
        limiter = NullRateLimiter()
        assert limiter.time_until_available() == 0.0

    @pytest.mark.asyncio
    async def test_acquire_always_succeeds(self) -> None:
        """Test acquire always succeeds."""
        limiter = NullRateLimiter()

        # Should never block, even with many requests
        for _ in range(100):
            result = await limiter.acquire()
            assert result is True


# Sample API response fixture
SAMPLE_SUMMARY_RESPONSE = {
    "summary": {
        "general": {
            "company": "Apple Inc.",
            "symbol": "AAPL",
            "exchange": "NAS",
            "currency": "USD",
        },
        "price": {"current": 175.43},
    }
}


class TestRateLimiterIntegration:
    """Tests for rate limiter integrated with the client."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_rate_limiter_enabled_by_default(self) -> None:
        """Test that rate limiter is enabled by default."""
        api_token = "test-token"
        respx.get(f"https://api.gurufocus.com/public/user/{api_token}/stock/AAPL/summary").mock(
            return_value=Response(200, json=SAMPLE_SUMMARY_RESPONSE)
        )

        async with GuruFocusClient(api_token=api_token) as client:
            assert isinstance(client.rate_limiter, RateLimiter)
            assert not isinstance(client.rate_limiter, NullRateLimiter)

    @pytest.mark.asyncio
    @respx.mock
    async def test_rate_limiter_disabled(self) -> None:
        """Test that rate limiter can be disabled."""
        async with GuruFocusClient(
            api_token="test-token",
            rate_limit_enabled=False,
        ) as client:
            assert isinstance(client.rate_limiter, NullRateLimiter)

    @pytest.mark.asyncio
    @respx.mock
    async def test_custom_rate_limit_config(self) -> None:
        """Test that custom rate limit config is applied."""
        async with GuruFocusClient(
            api_token="test-token",
            rate_limit_rpm=100.0,
            rate_limit_daily=5000,
            rate_limit_burst=20,
        ) as client:
            config = client.rate_limiter.config
            assert config.requests_per_minute == 100.0
            assert config.requests_per_day == 5000
            assert config.burst_size == 20

    @pytest.mark.asyncio
    @respx.mock
    async def test_rate_limiter_consumes_token_on_request(self) -> None:
        """Test that making a request consumes a rate limit token."""
        api_token = "test-token"
        respx.get(f"https://api.gurufocus.com/public/user/{api_token}/stock/AAPL/summary").mock(
            return_value=Response(200, json=SAMPLE_SUMMARY_RESPONSE)
        )

        async with GuruFocusClient(
            api_token=api_token,
            rate_limit_burst=10,
        ) as client:
            initial_tokens = client.rate_limiter.tokens
            await client.stocks.get_summary("AAPL", bypass_cache=True)

            # Token count should have decreased
            assert client.rate_limiter.tokens < initial_tokens
            assert client.rate_limiter.daily_count == 1

    @pytest.mark.asyncio
    @respx.mock
    async def test_rate_limiter_stats_accessible(self) -> None:
        """Test that rate limiter stats are accessible from client."""
        async with GuruFocusClient(api_token="test-token") as client:
            stats = client.rate_limiter.get_stats()
            assert "tokens" in stats
            assert "daily_count" in stats
