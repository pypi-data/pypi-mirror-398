"""Configuration management for the GuruFocus API client."""

from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class GuruFocusSettings(BaseSettings):
    """Configuration settings for the GuruFocus API client.

    Settings can be provided via environment variables or passed directly.
    Environment variables are prefixed with GURUFOCUS_.

    Example:
        export GURUFOCUS_API_TOKEN=your-token-here
        export GURUFOCUS_BASE_URL=https://api.gurufocus.com
    """

    model_config = SettingsConfigDict(
        env_prefix="GURUFOCUS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_token: SecretStr = Field(
        default=...,
        description="GuruFocus API token for authentication",
    )

    base_url: str = Field(
        default="https://api.gurufocus.com/public/user",
        description="Base URL for the GuruFocus API",
    )

    timeout: float = Field(
        default=30.0,
        ge=1.0,
        le=300.0,
        description="Request timeout in seconds",
    )

    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum number of retry attempts for failed requests",
    )

    retry_delay: float = Field(
        default=1.0,
        ge=0.1,
        le=60.0,
        description="Initial delay between retries in seconds (exponential backoff)",
    )

    cache_enabled: bool = Field(
        default=True,
        description="Enable response caching",
    )

    cache_dir: str = Field(
        default=".cache/gurufocus",
        description="Directory for cache storage",
    )

    rate_limit_enabled: bool = Field(
        default=True,
        description="Enable rate limiting",
    )

    rate_limit_rpm: float = Field(
        default=10.0,
        ge=0.1,
        le=1000.0,
        description="Maximum requests per minute",
    )

    rate_limit_daily: int = Field(
        default=0,
        ge=0,
        description="Maximum requests per day (0 = unlimited)",
    )

    rate_limit_burst: int = Field(
        default=5,
        ge=1,
        le=100,
        description="Maximum burst size for rate limiting",
    )

    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )

    log_format: Literal["json", "console"] = Field(
        default="console",
        description="Log output format: 'json' for production, 'console' for development",
    )
