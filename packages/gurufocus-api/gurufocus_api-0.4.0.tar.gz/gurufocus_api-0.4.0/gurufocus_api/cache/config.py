"""Cache configuration with three-tier TTL strategy.

Financial data has different freshness requirements:
- Price-dependent data changes daily with stock prices
- Earnings-dependent data changes quarterly after earnings reports
- Static data rarely changes (company info, sector, etc.)

This module defines the cache tiers and TTL configuration for each
type of data to optimize API usage while keeping data fresh.
"""

from dataclasses import dataclass
from datetime import timedelta
from enum import Enum


class CacheTier(Enum):
    """Cache tier based on data freshness requirements.

    PRICE_DEPENDENT: Changes with stock price (P/E, market cap, etc.)
    EARNINGS_DEPENDENT: Changes quarterly after earnings reports
    STATIC: Rarely changes (company profile, sector, etc.)
    """

    PRICE_DEPENDENT = "price_dependent"
    EARNINGS_DEPENDENT = "earnings_dependent"
    STATIC = "static"


class CacheCategory(Enum):
    """Categories of cached data mapped to API endpoints."""

    # Price-dependent (refresh daily or more frequently)
    QUOTE = "quote"
    VALUATION_RATIOS = "valuation_ratios"
    MARKET_DATA = "market_data"
    PRICE_HISTORY = "price_history"
    PRICE_OHLC = "price_ohlc"
    VOLUME = "volume"
    UNADJUSTED_PRICE = "unadjusted_price"

    # Price-dependent (short TTL as it changes with stock price)
    CURRENT_DIVIDEND = "current_dividend"

    # Earnings-dependent (refresh quarterly or after earnings)
    SUMMARY = "summary"
    FINANCIALS = "financials"
    KEY_RATIOS = "key_ratios"
    FUNDAMENTAL_RATIOS = "fundamental_ratios"
    GROWTH_METRICS = "growth_metrics"
    ESTIMATES = "estimates"
    GF_SCORE = "gf_score"
    DIVIDENDS = "dividends"
    INSIDERS = "insiders"

    # Insider activity (refresh daily as new SEC filings arrive)
    INSIDER_UPDATES = "insider_updates"
    INSIDER_CEO_BUYS = "insider_ceo_buys"
    INSIDER_CFO_BUYS = "insider_cfo_buys"
    INSIDER_CLUSTER_BUY = "insider_cluster_buy"
    INSIDER_DOUBLE = "insider_double"
    INSIDER_TRIPLE = "insider_triple"
    INSIDER_LIST = "insider_list"

    # Static (refresh monthly)
    PROFILE = "profile"
    GURUS = "gurus"
    GURU_LIST = "guru_list"
    EXECUTIVES = "executives"
    TRADES_HISTORY = "trades_history"


@dataclass(frozen=True)
class CacheConfig:
    """Configuration for a cache category."""

    tier: CacheTier
    ttl: timedelta
    invalidate_on_earnings: bool = False


# Default TTL configurations for each category
_CACHE_CONFIGS: dict[CacheCategory, CacheConfig] = {
    # TIER 1: Price-Dependent (daily refresh)
    CacheCategory.QUOTE: CacheConfig(
        tier=CacheTier.PRICE_DEPENDENT,
        ttl=timedelta(minutes=15),
    ),
    CacheCategory.VALUATION_RATIOS: CacheConfig(
        tier=CacheTier.PRICE_DEPENDENT,
        ttl=timedelta(days=1),
    ),
    CacheCategory.MARKET_DATA: CacheConfig(
        tier=CacheTier.PRICE_DEPENDENT,
        ttl=timedelta(days=1),
    ),
    # TIER 2: Earnings-Dependent (quarterly, invalidate after earnings)
    CacheCategory.SUMMARY: CacheConfig(
        tier=CacheTier.EARNINGS_DEPENDENT,
        ttl=timedelta(days=1),  # Summary includes price data, so daily
        invalidate_on_earnings=True,
    ),
    CacheCategory.FINANCIALS: CacheConfig(
        tier=CacheTier.EARNINGS_DEPENDENT,
        ttl=timedelta(days=95),  # ~quarterly
        invalidate_on_earnings=True,
    ),
    CacheCategory.KEY_RATIOS: CacheConfig(
        tier=CacheTier.EARNINGS_DEPENDENT,
        ttl=timedelta(days=95),
        invalidate_on_earnings=True,
    ),
    CacheCategory.FUNDAMENTAL_RATIOS: CacheConfig(
        tier=CacheTier.EARNINGS_DEPENDENT,
        ttl=timedelta(days=95),
        invalidate_on_earnings=True,
    ),
    CacheCategory.GROWTH_METRICS: CacheConfig(
        tier=CacheTier.EARNINGS_DEPENDENT,
        ttl=timedelta(days=95),
        invalidate_on_earnings=True,
    ),
    CacheCategory.ESTIMATES: CacheConfig(
        tier=CacheTier.EARNINGS_DEPENDENT,
        ttl=timedelta(days=7),
        invalidate_on_earnings=True,
    ),
    CacheCategory.GF_SCORE: CacheConfig(
        tier=CacheTier.EARNINGS_DEPENDENT,
        ttl=timedelta(days=1),  # GF Score can change with price
        invalidate_on_earnings=True,
    ),
    CacheCategory.DIVIDENDS: CacheConfig(
        tier=CacheTier.EARNINGS_DEPENDENT,
        ttl=timedelta(days=30),  # Dividend data changes infrequently
        invalidate_on_earnings=True,
    ),
    CacheCategory.INSIDERS: CacheConfig(
        tier=CacheTier.EARNINGS_DEPENDENT,
        ttl=timedelta(days=7),  # Insider trades filed within days
    ),
    # Insider activity endpoints (daily refresh for fresh SEC filings)
    CacheCategory.INSIDER_UPDATES: CacheConfig(
        tier=CacheTier.EARNINGS_DEPENDENT,
        ttl=timedelta(days=1),  # New updates arrive daily
    ),
    CacheCategory.INSIDER_CEO_BUYS: CacheConfig(
        tier=CacheTier.EARNINGS_DEPENDENT,
        ttl=timedelta(days=1),  # CEO buys are time-sensitive signals
    ),
    CacheCategory.INSIDER_CFO_BUYS: CacheConfig(
        tier=CacheTier.EARNINGS_DEPENDENT,
        ttl=timedelta(days=1),  # CFO buys are time-sensitive signals
    ),
    CacheCategory.INSIDER_CLUSTER_BUY: CacheConfig(
        tier=CacheTier.EARNINGS_DEPENDENT,
        ttl=timedelta(days=1),  # Cluster buys are time-sensitive signals
    ),
    CacheCategory.INSIDER_DOUBLE: CacheConfig(
        tier=CacheTier.EARNINGS_DEPENDENT,
        ttl=timedelta(days=1),  # Double-down buys are time-sensitive signals
    ),
    CacheCategory.INSIDER_TRIPLE: CacheConfig(
        tier=CacheTier.EARNINGS_DEPENDENT,
        ttl=timedelta(days=1),  # Triple-down buys are time-sensitive signals
    ),
    CacheCategory.INSIDER_LIST: CacheConfig(
        tier=CacheTier.STATIC,
        ttl=timedelta(days=7),  # Insider list changes infrequently
    ),
    CacheCategory.PRICE_HISTORY: CacheConfig(
        tier=CacheTier.PRICE_DEPENDENT,
        ttl=timedelta(days=1),  # Price data updates daily
    ),
    CacheCategory.PRICE_OHLC: CacheConfig(
        tier=CacheTier.PRICE_DEPENDENT,
        ttl=timedelta(days=1),  # OHLC data updates daily
    ),
    CacheCategory.VOLUME: CacheConfig(
        tier=CacheTier.PRICE_DEPENDENT,
        ttl=timedelta(days=1),  # Volume data updates daily
    ),
    CacheCategory.UNADJUSTED_PRICE: CacheConfig(
        tier=CacheTier.PRICE_DEPENDENT,
        ttl=timedelta(days=1),  # Unadjusted prices update daily
    ),
    CacheCategory.CURRENT_DIVIDEND: CacheConfig(
        tier=CacheTier.PRICE_DEPENDENT,
        ttl=timedelta(days=1),  # Yield changes with price
    ),
    # TIER 3: Static (monthly+)
    CacheCategory.PROFILE: CacheConfig(
        tier=CacheTier.STATIC,
        ttl=timedelta(days=30),
    ),
    CacheCategory.GURUS: CacheConfig(
        tier=CacheTier.STATIC,
        ttl=timedelta(days=14),
    ),
    CacheCategory.GURU_LIST: CacheConfig(
        tier=CacheTier.STATIC,
        ttl=timedelta(days=7),
    ),
    CacheCategory.EXECUTIVES: CacheConfig(
        tier=CacheTier.STATIC,
        ttl=timedelta(days=30),
    ),
    CacheCategory.TRADES_HISTORY: CacheConfig(
        tier=CacheTier.STATIC,
        ttl=timedelta(days=7),  # Guru trades update with SEC filings
    ),
}


def get_cache_config(category: CacheCategory) -> CacheConfig:
    """Get cache configuration for a category.

    Args:
        category: The cache category to look up

    Returns:
        CacheConfig with tier, TTL, and invalidation settings
    """
    return _CACHE_CONFIGS[category]


def get_ttl_seconds(category: CacheCategory) -> int:
    """Get TTL in seconds for a cache category.

    Args:
        category: The cache category

    Returns:
        TTL in seconds
    """
    config = get_cache_config(category)
    return int(config.ttl.total_seconds())


def build_cache_key(category: CacheCategory, *parts: str) -> str:
    """Build a cache key from category and parts.

    Args:
        category: The cache category
        *parts: Additional key parts (e.g., symbol)

    Returns:
        Cache key string like "summary:AAPL"

    Example:
        >>> build_cache_key(CacheCategory.SUMMARY, "AAPL")
        "summary:AAPL"
        >>> build_cache_key(CacheCategory.FINANCIALS, "AAPL", "annual")
        "financials:AAPL:annual"
    """
    return ":".join([category.value, *parts])


# Metrics classification for reference
PRICE_DEPENDENT_METRICS = {
    "pe_ratio",
    "ps_ratio",
    "pb_ratio",
    "peg_ratio",
    "ev_ebitda",
    "ev_sales",
    "ev_fcf",
    "market_cap",
    "enterprise_value",
    "dividend_yield",
    "discount_to_gf_value",
    "discount_to_dcf",
    "momentum_score",
    "valuation_rank",
    "current_price",
}

EARNINGS_DEPENDENT_METRICS = {
    "eps",
    "revenue_per_share",
    "fcf_per_share",
    "book_value_per_share",
    "roe",
    "roic",
    "roa",
    "roce",
    "gross_margin",
    "operating_margin",
    "net_margin",
    "fcf_margin",
    "revenue_growth_yoy",
    "eps_growth_yoy",
    "debt_to_equity",
    "current_ratio",
    "piotroski_score",
}

STATIC_METRICS = {
    "company_name",
    "sector",
    "industry",
    "exchange",
    "currency",
    "description",
}
