"""Async HTTP client for the GuruFocus API."""

from __future__ import annotations

import asyncio
import time
import uuid
from collections.abc import Generator
from contextlib import contextmanager
from types import TracebackType
from typing import TYPE_CHECKING, Any, Self

import httpx
import structlog
from structlog.contextvars import bind_contextvars, clear_contextvars

from .config import GuruFocusSettings
from .exceptions import (
    APIError,
    AuthenticationError,
    InvalidSymbolError,
    NetworkError,
    NotFoundError,
    RateLimitError,
)

# Optional OpenTelemetry support
_OTEL_AVAILABLE = False
_tracer = None
try:
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode

    _OTEL_AVAILABLE = True
    _tracer = trace.get_tracer("gurufocus_api")
except ImportError:
    trace = None  # type: ignore[assignment]
    Status = None  # type: ignore[assignment, misc]
    StatusCode = None  # type: ignore[assignment, misc]

if TYPE_CHECKING:
    from .cache import CacheManager
    from .endpoints.insiders import InsidersEndpoint
    from .endpoints.stocks import StocksEndpoint
    from .rate_limiter import RateLimiter

logger = structlog.stdlib.get_logger(__name__)


@contextmanager
def _create_span(
    name: str,
    attributes: dict[str, Any] | None = None,
) -> Generator[Any, None, None]:
    """Create an OpenTelemetry span if available, otherwise a no-op context.

    Args:
        name: Span name
        attributes: Initial span attributes

    Yields:
        The span object if OpenTelemetry is available, otherwise None
    """
    if not _OTEL_AVAILABLE or _tracer is None:
        yield None
        return

    with _tracer.start_as_current_span(name, attributes=attributes) as span:
        yield span


class GuruFocusClient:
    """Async client for the GuruFocus API.

    This client handles authentication, rate limiting, retries, and caching
    for all GuruFocus API requests.

    Example:
        async with GuruFocusClient() as client:
            data = await client.request("GET", "/stock/AAPL/summary")
            print(data)

        # Or with explicit token:
        async with GuruFocusClient(api_token="your-token") as client:
            data = await client.request("GET", "/stock/AAPL/summary")
    """

    def __init__(
        self,
        api_token: str | None = None,
        base_url: str | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
        cache_enabled: bool | None = None,
        cache_dir: str | None = None,
        rate_limit_enabled: bool | None = None,
        rate_limit_rpm: float | None = None,
        rate_limit_daily: int | None = None,
        rate_limit_burst: int | None = None,
        settings: GuruFocusSettings | None = None,
    ) -> None:
        """Initialize the GuruFocus API client.

        Args:
            api_token: API token for authentication. If not provided, reads from
                       GURUFOCUS_API_TOKEN environment variable.
            base_url: Base URL for the API. Defaults to GuruFocus production API.
            timeout: Request timeout in seconds.
            max_retries: Maximum number of retry attempts.
            cache_enabled: Enable response caching. Defaults to True.
            cache_dir: Directory for cache storage.
            rate_limit_enabled: Enable rate limiting. Defaults to True.
            rate_limit_rpm: Maximum requests per minute.
            rate_limit_daily: Maximum requests per day (0 = unlimited).
            rate_limit_burst: Maximum burst size for rate limiting.
            settings: Pre-configured settings object. If provided, other args
                      are used as overrides.
        """
        # Load settings from environment if not provided
        if settings is None:
            # Build kwargs for settings, only including non-None values
            settings_kwargs: dict[str, Any] = {}
            if api_token is not None:
                settings_kwargs["api_token"] = api_token
            settings = GuruFocusSettings(**settings_kwargs)

        self._settings = settings

        # Allow parameter overrides
        self._api_token = api_token or settings.api_token.get_secret_value()
        self._base_url = base_url or settings.base_url
        self._timeout = timeout or settings.timeout
        self._max_retries = max_retries if max_retries is not None else settings.max_retries
        self._retry_delay = settings.retry_delay

        # Cache settings
        self._cache_enabled = cache_enabled if cache_enabled is not None else settings.cache_enabled
        self._cache_dir = cache_dir or settings.cache_dir

        # Rate limit settings
        self._rate_limit_enabled = (
            rate_limit_enabled if rate_limit_enabled is not None else settings.rate_limit_enabled
        )
        self._rate_limit_rpm = rate_limit_rpm or settings.rate_limit_rpm
        self._rate_limit_daily = (
            rate_limit_daily if rate_limit_daily is not None else settings.rate_limit_daily
        )
        self._rate_limit_burst = rate_limit_burst or settings.rate_limit_burst

        # HTTP client (created on first use or context entry)
        self._client: httpx.AsyncClient | None = None
        self._owns_client = True

        # Cache manager (lazily initialized)
        self._cache: CacheManager | None = None

        # Rate limiter (lazily initialized)
        self._rate_limiter: RateLimiter | None = None

        # Endpoint instances (lazily initialized)
        self._stocks: StocksEndpoint | None = None
        self._insiders: InsidersEndpoint | None = None

    @property
    def cache(self) -> CacheManager:
        """Access the cache manager.

        Returns:
            CacheManager instance for caching API responses

        Example:
            stats = client.cache.get_stats()
            await client.cache.invalidate_symbol("AAPL")
        """
        if self._cache is None:
            from .cache import CacheManager

            self._cache = CacheManager(
                cache_dir=self._cache_dir,
                enabled=self._cache_enabled,
            )
        return self._cache

    @property
    def rate_limiter(self) -> RateLimiter:
        """Access the rate limiter.

        Returns:
            RateLimiter instance for controlling API request rate

        Example:
            stats = client.rate_limiter.get_stats()
            if client.rate_limiter.can_acquire():
                await client.request(...)
        """
        if self._rate_limiter is None:
            from .rate_limiter import NullRateLimiter, RateLimitConfig, RateLimiter

            if not self._rate_limit_enabled:
                self._rate_limiter = NullRateLimiter()
            else:
                config = RateLimitConfig(
                    requests_per_minute=self._rate_limit_rpm,
                    requests_per_day=self._rate_limit_daily,
                    burst_size=self._rate_limit_burst,
                )
                self._rate_limiter = RateLimiter(config)
        return self._rate_limiter

    @property
    def stocks(self) -> StocksEndpoint:
        """Access stock-related endpoints.

        Returns:
            StocksEndpoint instance for fetching stock data

        Example:
            summary = await client.stocks.get_summary("AAPL")
        """
        if self._stocks is None:
            from .endpoints.stocks import StocksEndpoint

            self._stocks = StocksEndpoint(self)
        return self._stocks

    @property
    def insiders(self) -> InsidersEndpoint:
        """Access insider activity endpoints.

        Returns:
            InsidersEndpoint instance for fetching insider trading data

        Example:
            updates = await client.insiders.get_updates()
            ceo_buys = await client.insiders.get_ceo_buys()
        """
        if self._insiders is None:
            from .endpoints.insiders import InsidersEndpoint

            self._insiders = InsidersEndpoint(self)
        return self._insiders

    @property
    def is_connected(self) -> bool:
        """Check if the client has an active HTTP connection."""
        return self._client is not None and not self._client.is_closed

    async def __aenter__(self) -> Self:
        """Enter async context manager."""
        await self._ensure_client()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit async context manager."""
        await self.close()

    async def _ensure_client(self) -> httpx.AsyncClient:
        """Ensure HTTP client is initialized."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self._timeout),
                follow_redirects=True,
            )
            self._owns_client = True
        return self._client

    async def close(self) -> None:
        """Close the HTTP client and cache connections."""
        if self._client is not None and self._owns_client:
            await self._client.aclose()
            self._client = None

        if self._cache is not None:
            await self._cache.close()
            self._cache = None

    def _build_url(self, endpoint: str) -> str:
        """Build full URL for an API endpoint.

        The GuruFocus API uses the token in the URL path:
        https://api.gurufocus.com/public/user/{token}/stock/{symbol}/summary
        """
        # Remove leading slash if present
        endpoint = endpoint.lstrip("/")
        return f"{self._base_url}/{self._api_token}/{endpoint}"

    def _extract_symbol_from_endpoint(self, endpoint: str) -> str | None:
        """Extract stock symbol from endpoint path if present."""
        parts = endpoint.lstrip("/").split("/")
        if len(parts) >= 2 and parts[0] == "stock":
            return parts[1].upper()
        return None

    async def request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
    ) -> Any:
        """Make an HTTP request to the GuruFocus API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path (e.g., "/stock/AAPL/summary")
            params: Query parameters
            json_data: JSON body data for POST requests

        Returns:
            Parsed JSON response data

        Raises:
            AuthenticationError: Invalid or missing API token
            RateLimitError: API rate limit exceeded
            InvalidSymbolError: Invalid stock symbol
            NotFoundError: Resource not found
            APIError: Other API errors
            NetworkError: Network connectivity issues
        """
        client = await self._ensure_client()
        url = self._build_url(endpoint)

        request_id = str(uuid.uuid4())[:8]
        symbol = self._extract_symbol_from_endpoint(endpoint)
        start_time = time.perf_counter()

        # Set up span attributes for OpenTelemetry
        span_attributes = {
            "http.method": method,
            "http.url": endpoint,
            "gurufocus.request_id": request_id,
        }
        if symbol:
            span_attributes["gurufocus.symbol"] = symbol

        bind_contextvars(
            request_id=request_id,
            endpoint=endpoint,
            symbol=symbol,
            method=method,
        )

        last_exception: Exception | None = None

        with _create_span(f"gurufocus.{method} {endpoint}", span_attributes) as span:
            try:
                for attempt in range(self._max_retries + 1):
                    try:
                        # Acquire rate limit token before making request
                        await self.rate_limiter.acquire_or_raise()

                        logger.debug(
                            "api_request_attempt",
                            attempt=attempt + 1,
                            max_attempts=self._max_retries + 1,
                        )

                        response = await client.request(
                            method=method,
                            url=url,
                            params=params,
                            json=json_data,
                        )

                        duration_ms = (time.perf_counter() - start_time) * 1000

                        # Set span attributes for successful response
                        if span is not None:
                            span.set_attribute("http.status_code", response.status_code)
                            span.set_attribute("gurufocus.duration_ms", round(duration_ms, 2))
                            if _OTEL_AVAILABLE and Status is not None:
                                span.set_status(Status(StatusCode.OK))

                        logger.info(
                            "api_request_success",
                            status_code=response.status_code,
                            duration_ms=round(duration_ms, 2),
                        )

                        return self._handle_response(response, endpoint)

                    except httpx.TimeoutException as e:
                        last_exception = NetworkError(f"Request timed out: {e}")
                        logger.warning(
                            "api_request_timeout",
                            attempt=attempt + 1,
                            error=str(e),
                        )

                    except httpx.NetworkError as e:
                        last_exception = NetworkError(f"Network error: {e}")
                        logger.warning(
                            "api_request_network_error",
                            attempt=attempt + 1,
                            error=str(e),
                        )

                    except RateLimitError as e:
                        last_exception = e
                        if span is not None:
                            span.set_attribute("http.status_code", 429)
                            span.record_exception(e)
                            if _OTEL_AVAILABLE and Status is not None:
                                span.set_status(Status(StatusCode.ERROR, "Rate limited"))
                        logger.warning(
                            "api_request_rate_limited",
                            retry_after=e.retry_after,
                        )
                        raise

                    except (AuthenticationError, InvalidSymbolError, NotFoundError) as e:
                        if span is not None:
                            span.record_exception(e)
                            if _OTEL_AVAILABLE and Status is not None:
                                span.set_status(Status(StatusCode.ERROR, str(e)))
                        raise

                    except APIError as e:
                        last_exception = e
                        if e.status_code and e.status_code < 500:
                            if span is not None:
                                span.set_attribute("http.status_code", e.status_code)
                                span.record_exception(e)
                                if _OTEL_AVAILABLE and Status is not None:
                                    span.set_status(Status(StatusCode.ERROR, str(e)))
                            raise
                        logger.warning(
                            "api_request_server_error",
                            attempt=attempt + 1,
                            status_code=e.status_code,
                            error=str(e),
                        )

                    # Exponential backoff before retry
                    if attempt < self._max_retries:
                        delay = self._retry_delay * (2**attempt)
                        logger.debug("api_request_retry_wait", delay_seconds=delay)
                        await asyncio.sleep(delay)

                # All retries exhausted
                duration_ms = (time.perf_counter() - start_time) * 1000

                if span is not None:
                    span.set_attribute("gurufocus.duration_ms", round(duration_ms, 2))
                    span.set_attribute("gurufocus.retry_count", self._max_retries + 1)
                    if last_exception:
                        span.record_exception(last_exception)
                    if _OTEL_AVAILABLE and Status is not None:
                        span.set_status(Status(StatusCode.ERROR, "All retries exhausted"))

                logger.error(
                    "api_request_failed",
                    duration_ms=round(duration_ms, 2),
                    total_attempts=self._max_retries + 1,
                    error=str(last_exception),
                )

                if last_exception:
                    raise last_exception
                raise NetworkError("Request failed after all retries")
            finally:
                clear_contextvars()

    def _handle_response(self, response: httpx.Response, endpoint: str) -> Any:
        """Handle API response and raise appropriate exceptions.

        Args:
            response: HTTP response object
            endpoint: Original endpoint for error context

        Returns:
            Parsed JSON response data

        Raises:
            Appropriate exception based on response status
        """
        # Check for rate limiting
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(
                message="API rate limit exceeded",
                retry_after=int(retry_after) if retry_after else None,
            )

        # Check for authentication errors
        if response.status_code == 401:
            raise AuthenticationError("Invalid or missing API token")

        if response.status_code == 403:
            raise AuthenticationError("Access forbidden - check API token permissions")

        # Check for not found
        if response.status_code == 404:
            # Try to determine if it's an invalid symbol
            # Handle both "stock/SYMBOL/..." and "/stock/SYMBOL/..."
            if "stock/" in endpoint:
                # Extract symbol from endpoint
                parts = endpoint.lstrip("/").split("/")
                if len(parts) >= 2 and parts[0] == "stock":
                    symbol = parts[1]
                    raise InvalidSymbolError(symbol)
            raise NotFoundError(f"Resource not found: {endpoint}")

        # Check for other client errors
        if response.status_code >= 400 and response.status_code < 500:
            raise APIError(
                message=f"Client error: {response.status_code}",
                status_code=response.status_code,
                details={"response_text": response.text[:500]},
            )

        # Check for server errors
        if response.status_code >= 500:
            raise APIError(
                message=f"Server error: {response.status_code}",
                status_code=response.status_code,
                details={"response_text": response.text[:500]},
            )

        # Parse JSON response
        try:
            return response.json()
        except ValueError as e:
            raise APIError(
                message=f"Invalid JSON response: {e}",
                status_code=response.status_code,
                details={"response_text": response.text[:500]},
            ) from e

    async def get(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Make a GET request to the API.

        Args:
            endpoint: API endpoint path
            params: Query parameters

        Returns:
            Parsed JSON response data
        """
        return await self.request("GET", endpoint, params=params)

    async def post(
        self,
        endpoint: str,
        json_data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Make a POST request to the API.

        Args:
            endpoint: API endpoint path
            json_data: JSON body data
            params: Query parameters

        Returns:
            Parsed JSON response data
        """
        return await self.request("POST", endpoint, params=params, json_data=json_data)
