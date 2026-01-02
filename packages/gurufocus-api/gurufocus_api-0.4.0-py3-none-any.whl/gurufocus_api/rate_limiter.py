"""Rate limiting for GuruFocus API requests.

Implements a token bucket algorithm to prevent exceeding API rate limits.
The token bucket allows bursts of requests while maintaining a sustainable
average rate.

GuruFocus API Rate Limits (approximate):
- Free: 100 requests/day, 10 requests/minute
- Premium: 10,000 requests/day, 100 requests/minute
- Professional: 50,000 requests/day, 500 requests/minute
"""

import asyncio
import time
from dataclasses import dataclass
from typing import Any

import structlog

logger = structlog.stdlib.get_logger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting.

    Attributes:
        requests_per_minute: Maximum requests allowed per minute
        requests_per_day: Maximum requests allowed per day (0 = unlimited)
        burst_size: Maximum burst size (tokens in bucket)
    """

    requests_per_minute: float = 10.0
    requests_per_day: int = 0  # 0 = unlimited
    burst_size: int = 5


class RateLimiter:
    """Token bucket rate limiter for API requests.

    The token bucket algorithm allows short bursts of requests while
    maintaining a sustainable average rate. Tokens are added to the
    bucket at a fixed rate, and each request consumes one token.

    Attributes:
        config: Rate limit configuration
        tokens: Current number of tokens in the bucket
        daily_count: Number of requests made today

    Example:
        limiter = RateLimiter(RateLimitConfig(requests_per_minute=10))

        # Before each request
        await limiter.acquire()  # Waits if necessary

        # Check if we can make a request without waiting
        if limiter.can_acquire():
            await limiter.acquire()
    """

    def __init__(self, config: RateLimitConfig | None = None) -> None:
        """Initialize the rate limiter.

        Args:
            config: Rate limit configuration. Uses defaults if not provided.
        """
        self._config = config or RateLimitConfig()

        # Token bucket state
        self._tokens = float(self._config.burst_size)
        self._last_update = time.monotonic()

        # Daily counter
        self._daily_count = 0
        self._daily_reset_time = time.time()

        # Lock for thread safety
        self._lock = asyncio.Lock()

    @property
    def config(self) -> RateLimitConfig:
        """Get the rate limit configuration."""
        return self._config

    @property
    def tokens(self) -> float:
        """Get current token count (may be stale, use for monitoring only)."""
        return self._tokens

    @property
    def daily_count(self) -> int:
        """Get the number of requests made today."""
        return self._daily_count

    @property
    def daily_remaining(self) -> int | None:
        """Get remaining daily requests, or None if unlimited."""
        if self._config.requests_per_day <= 0:
            return None
        return max(0, self._config.requests_per_day - self._daily_count)

    def _refill_tokens(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self._last_update
        self._last_update = now

        # Calculate tokens to add based on rate
        # requests_per_minute -> tokens per second = rpm / 60
        tokens_per_second = self._config.requests_per_minute / 60.0
        tokens_to_add = elapsed * tokens_per_second

        # Add tokens up to burst size
        self._tokens = min(self._config.burst_size, self._tokens + tokens_to_add)

    def _check_daily_reset(self) -> None:
        """Reset daily counter if a new day has started."""
        now = time.time()
        # Check if 24 hours have passed since last reset
        if now - self._daily_reset_time >= 86400:  # 24 hours in seconds
            self._daily_count = 0
            self._daily_reset_time = now
            logger.debug("Daily rate limit counter reset")

    def can_acquire(self) -> bool:
        """Check if a token can be acquired without waiting.

        Returns:
            True if a request can be made immediately
        """
        self._refill_tokens()
        self._check_daily_reset()

        # Check daily limit
        if self._config.requests_per_day > 0 and self._daily_count >= self._config.requests_per_day:
            return False

        return self._tokens >= 1.0

    def time_until_available(self) -> float:
        """Calculate time until a token will be available.

        Returns:
            Seconds until a token is available (0 if available now)
        """
        self._refill_tokens()

        if self._tokens >= 1.0:
            return 0.0

        # Calculate time to get 1 token
        tokens_needed = 1.0 - self._tokens
        tokens_per_second = self._config.requests_per_minute / 60.0

        if tokens_per_second <= 0:
            return float("inf")

        return tokens_needed / tokens_per_second

    async def acquire(self, timeout: float | None = None) -> bool:
        """Acquire a token, waiting if necessary.

        Args:
            timeout: Maximum time to wait in seconds. None = wait forever.

        Returns:
            True if token acquired, False if timeout exceeded

        Raises:
            RateLimitExceeded: If daily limit is exceeded (no waiting possible)
        """
        async with self._lock:
            start_time = time.monotonic()

            while True:
                self._refill_tokens()
                self._check_daily_reset()

                # Check daily limit first
                if (
                    self._config.requests_per_day > 0
                    and self._daily_count >= self._config.requests_per_day
                ):
                    logger.warning(
                        "Daily rate limit exceeded: %d/%d",
                        self._daily_count,
                        self._config.requests_per_day,
                    )
                    return False

                # Check if we have tokens
                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    self._daily_count += 1
                    logger.debug(
                        "Token acquired. Remaining: %.1f, Daily: %d",
                        self._tokens,
                        self._daily_count,
                    )
                    return True

                # Calculate wait time
                wait_time = self.time_until_available()

                # Check timeout
                if timeout is not None:
                    elapsed = time.monotonic() - start_time
                    remaining_timeout = timeout - elapsed
                    if remaining_timeout <= 0:
                        logger.debug("Rate limit acquire timeout")
                        return False
                    wait_time = min(wait_time, remaining_timeout)

                logger.debug("Rate limited, waiting %.2f seconds", wait_time)
                await asyncio.sleep(wait_time)

    async def acquire_or_raise(self, timeout: float | None = None) -> None:
        """Acquire a token or raise an exception.

        Args:
            timeout: Maximum time to wait in seconds

        Raises:
            RateLimitError: If token cannot be acquired within timeout
        """
        from .exceptions import RateLimitError

        acquired = await self.acquire(timeout=timeout)
        if not acquired:
            if self.daily_remaining == 0:
                raise RateLimitError(
                    message="Daily API rate limit exceeded",
                    retry_after=self._seconds_until_daily_reset(),
                )
            raise RateLimitError(
                message="Rate limit exceeded",
                retry_after=int(self.time_until_available()) + 1,
            )

    def _seconds_until_daily_reset(self) -> int:
        """Calculate seconds until daily counter resets."""
        elapsed = time.time() - self._daily_reset_time
        remaining = 86400 - elapsed
        return max(0, int(remaining))

    def reset(self) -> None:
        """Reset the rate limiter state."""
        self._tokens = float(self._config.burst_size)
        self._last_update = time.monotonic()
        self._daily_count = 0
        self._daily_reset_time = time.time()

    def get_stats(self) -> dict[str, Any]:
        """Get rate limiter statistics.

        Returns:
            Dictionary with current state and configuration
        """
        self._refill_tokens()
        return {
            "tokens": round(self._tokens, 2),
            "burst_size": self._config.burst_size,
            "requests_per_minute": self._config.requests_per_minute,
            "daily_count": self._daily_count,
            "daily_limit": self._config.requests_per_day or "unlimited",
            "daily_remaining": self.daily_remaining,
            "time_until_available": round(self.time_until_available(), 2),
        }


class NullRateLimiter(RateLimiter):
    """A rate limiter that doesn't limit anything.

    Useful for testing or when rate limiting should be disabled.
    """

    def __init__(self) -> None:
        """Initialize null rate limiter."""
        super().__init__(RateLimitConfig(requests_per_minute=float("inf")))

    def can_acquire(self) -> bool:
        """Always returns True."""
        return True

    def time_until_available(self) -> float:
        """Always returns 0."""
        return 0.0

    async def acquire(self, timeout: float | None = None) -> bool:
        """Always returns True immediately."""
        return True
