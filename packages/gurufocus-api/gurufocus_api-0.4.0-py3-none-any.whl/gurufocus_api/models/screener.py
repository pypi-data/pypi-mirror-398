"""Pydantic models for stock screener data."""

from collections.abc import Sequence
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class FilterOperator(str, Enum):
    """Operators for screener filters."""

    EQUALS = "eq"
    NOT_EQUALS = "ne"
    GREATER_THAN = "gt"
    GREATER_THAN_OR_EQUAL = "gte"
    LESS_THAN = "lt"
    LESS_THAN_OR_EQUAL = "lte"
    BETWEEN = "between"
    IN = "in"
    NOT_IN = "not_in"


class ScreenerFilter(BaseModel):
    """A single filter criterion for screening stocks."""

    field: str = Field(description="Field to filter on (e.g., 'pe_ratio', 'market_cap')")
    operator: FilterOperator = Field(description="Comparison operator")
    value: float | str | list[float | str] = Field(description="Value(s) to compare against")

    def to_api_format(self) -> dict[str, Any]:
        """Convert filter to API request format.

        Returns:
            Dictionary in the format expected by GuruFocus API
        """
        return {
            "field": self.field,
            "op": self.operator.value,
            "value": self.value,
        }


class ScreenerSort(BaseModel):
    """Sort configuration for screener results."""

    field: str = Field(description="Field to sort by")
    ascending: bool = Field(default=False, description="Sort in ascending order")

    def to_api_format(self) -> dict[str, Any]:
        """Convert sort to API request format."""
        return {
            "field": self.field,
            "order": "asc" if self.ascending else "desc",
        }


class ScreenerRequest(BaseModel):
    """Request parameters for running a stock screener."""

    filters: list[ScreenerFilter] = Field(
        default_factory=list, description="List of filter criteria"
    )
    sort: ScreenerSort | None = Field(default=None, description="Sort configuration")
    limit: int = Field(default=100, ge=1, le=1000, description="Maximum results to return")
    offset: int = Field(default=0, ge=0, description="Results offset for pagination")

    # Optional filters
    exchange: str | None = Field(default=None, description="Filter by exchange (NYSE, NASDAQ)")
    sector: str | None = Field(default=None, description="Filter by sector")
    industry: str | None = Field(default=None, description="Filter by industry")
    country: str | None = Field(default=None, description="Filter by country")
    market_cap_min: float | None = Field(default=None, description="Minimum market cap")
    market_cap_max: float | None = Field(default=None, description="Maximum market cap")

    def to_api_format(self) -> dict[str, Any]:
        """Convert request to API format.

        Returns:
            Dictionary in the format expected by GuruFocus API
        """
        request: dict[str, Any] = {
            "filters": [f.to_api_format() for f in self.filters],
            "limit": self.limit,
            "offset": self.offset,
        }

        if self.sort:
            request["sort"] = self.sort.to_api_format()

        if self.exchange:
            request["exchange"] = self.exchange
        if self.sector:
            request["sector"] = self.sector
        if self.industry:
            request["industry"] = self.industry
        if self.country:
            request["country"] = self.country
        if self.market_cap_min is not None:
            request["market_cap_min"] = self.market_cap_min
        if self.market_cap_max is not None:
            request["market_cap_max"] = self.market_cap_max

        return request


class ScreenerStock(BaseModel):
    """A single stock result from the screener."""

    symbol: str = Field(description="Stock ticker symbol")
    company_name: str | None = Field(default=None, description="Company name")
    exchange: str | None = Field(default=None, description="Stock exchange")
    sector: str | None = Field(default=None, description="Business sector")
    industry: str | None = Field(default=None, description="Industry classification")
    country: str | None = Field(default=None, description="Country of incorporation")

    # Price data
    price: float | None = Field(default=None, description="Current stock price")
    market_cap: float | None = Field(default=None, description="Market capitalization")
    volume: int | None = Field(default=None, description="Trading volume")

    # Valuation metrics
    pe_ratio: float | None = Field(default=None, description="P/E ratio")
    pb_ratio: float | None = Field(default=None, description="P/B ratio")
    ps_ratio: float | None = Field(default=None, description="P/S ratio")
    peg_ratio: float | None = Field(default=None, description="PEG ratio")
    ev_ebitda: float | None = Field(default=None, description="EV/EBITDA")

    # Quality metrics
    gf_score: int | None = Field(default=None, description="GF Score (0-100)")
    gf_value: float | None = Field(default=None, description="GF Value estimate")
    financial_strength: int | None = Field(
        default=None, description="Financial Strength rank (1-10)"
    )
    profitability_rank: int | None = Field(default=None, description="Profitability rank (1-10)")

    # Profitability
    roe: float | None = Field(default=None, description="Return on Equity (%)")
    roic: float | None = Field(default=None, description="Return on Invested Capital (%)")
    gross_margin: float | None = Field(default=None, description="Gross margin (%)")
    operating_margin: float | None = Field(default=None, description="Operating margin (%)")
    net_margin: float | None = Field(default=None, description="Net profit margin (%)")

    # Growth
    revenue_growth: float | None = Field(default=None, description="Revenue growth YoY (%)")
    eps_growth: float | None = Field(default=None, description="EPS growth YoY (%)")

    # Dividend
    dividend_yield: float | None = Field(default=None, description="Dividend yield (%)")
    payout_ratio: float | None = Field(default=None, description="Dividend payout ratio (%)")

    # Additional data (dynamic fields from screener)
    extra_fields: dict[str, Any] = Field(
        default_factory=dict, description="Additional fields returned by screener"
    )


class ScreenerResults(BaseModel):
    """Results from running a stock screener."""

    stocks: list[ScreenerStock] = Field(default_factory=list, description="List of matching stocks")
    total_count: int = Field(default=0, description="Total number of matching stocks")
    offset: int = Field(default=0, description="Current offset in results")
    limit: int = Field(default=100, description="Results limit used")
    has_more: bool = Field(default=False, description="Whether more results are available")

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "ScreenerResults":
        """Create ScreenerResults from API response.

        Args:
            data: Raw JSON response from the API

        Returns:
            Populated ScreenerResults instance
        """
        results_data = data.get("results", data.get("stocks", data))

        # Parse stocks list
        stocks_raw = (
            results_data if isinstance(results_data, list) else results_data.get("data", [])
        )
        stocks = [_parse_screener_stock(s) for s in stocks_raw]

        total_count = data.get("total_count", data.get("total", data.get("count", len(stocks))))
        offset = data.get("offset", 0)
        limit = data.get("limit", 100)

        return cls(
            stocks=stocks,
            total_count=total_count,
            offset=offset,
            limit=limit,
            has_more=(offset + len(stocks)) < total_count,
        )


# --- Filter Builder ---


class FilterBuilder:
    """Fluent builder for constructing screener filters.

    Example:
        filters = (
            FilterBuilder()
            .pe_ratio_less_than(20)
            .roe_greater_than(15)
            .market_cap_greater_than(1_000_000_000)
            .build()
        )
    """

    def __init__(self) -> None:
        """Initialize the filter builder."""
        self._filters: list[ScreenerFilter] = []

    def add_filter(
        self,
        field: str,
        operator: FilterOperator,
        value: float | str | Sequence[float | str],
    ) -> "FilterBuilder":
        """Add a custom filter.

        Args:
            field: Field name to filter on
            operator: Comparison operator
            value: Value(s) to compare against

        Returns:
            Self for method chaining
        """
        self._filters.append(ScreenerFilter(field=field, operator=operator, value=value))
        return self

    def build(self) -> list[ScreenerFilter]:
        """Build and return the list of filters.

        Returns:
            List of ScreenerFilter instances
        """
        return self._filters.copy()

    # --- Valuation Filters ---

    def pe_ratio_less_than(self, value: float) -> "FilterBuilder":
        """Filter for P/E ratio less than value."""
        return self.add_filter("pe_ratio", FilterOperator.LESS_THAN, value)

    def pe_ratio_greater_than(self, value: float) -> "FilterBuilder":
        """Filter for P/E ratio greater than value."""
        return self.add_filter("pe_ratio", FilterOperator.GREATER_THAN, value)

    def pe_ratio_between(self, min_val: float, max_val: float) -> "FilterBuilder":
        """Filter for P/E ratio between values."""
        return self.add_filter("pe_ratio", FilterOperator.BETWEEN, [min_val, max_val])

    def pb_ratio_less_than(self, value: float) -> "FilterBuilder":
        """Filter for P/B ratio less than value."""
        return self.add_filter("pb_ratio", FilterOperator.LESS_THAN, value)

    def pb_ratio_greater_than(self, value: float) -> "FilterBuilder":
        """Filter for P/B ratio greater than value."""
        return self.add_filter("pb_ratio", FilterOperator.GREATER_THAN, value)

    def ps_ratio_less_than(self, value: float) -> "FilterBuilder":
        """Filter for P/S ratio less than value."""
        return self.add_filter("ps_ratio", FilterOperator.LESS_THAN, value)

    def peg_ratio_less_than(self, value: float) -> "FilterBuilder":
        """Filter for PEG ratio less than value."""
        return self.add_filter("peg_ratio", FilterOperator.LESS_THAN, value)

    def ev_ebitda_less_than(self, value: float) -> "FilterBuilder":
        """Filter for EV/EBITDA less than value."""
        return self.add_filter("ev_ebitda", FilterOperator.LESS_THAN, value)

    # --- Market Cap Filters ---

    def market_cap_greater_than(self, value: float) -> "FilterBuilder":
        """Filter for market cap greater than value."""
        return self.add_filter("market_cap", FilterOperator.GREATER_THAN, value)

    def market_cap_less_than(self, value: float) -> "FilterBuilder":
        """Filter for market cap less than value."""
        return self.add_filter("market_cap", FilterOperator.LESS_THAN, value)

    def market_cap_between(self, min_val: float, max_val: float) -> "FilterBuilder":
        """Filter for market cap between values."""
        return self.add_filter("market_cap", FilterOperator.BETWEEN, [min_val, max_val])

    def large_cap(self) -> "FilterBuilder":
        """Filter for large cap stocks (>$10B)."""
        return self.market_cap_greater_than(10_000_000_000)

    def mid_cap(self) -> "FilterBuilder":
        """Filter for mid cap stocks ($2B-$10B)."""
        return self.market_cap_between(2_000_000_000, 10_000_000_000)

    def small_cap(self) -> "FilterBuilder":
        """Filter for small cap stocks (<$2B)."""
        return self.market_cap_less_than(2_000_000_000)

    # --- Quality Filters ---

    def gf_score_greater_than(self, value: int) -> "FilterBuilder":
        """Filter for GF Score greater than value."""
        return self.add_filter("gf_score", FilterOperator.GREATER_THAN, value)

    def financial_strength_greater_than(self, value: int) -> "FilterBuilder":
        """Filter for Financial Strength rank greater than value."""
        return self.add_filter("financial_strength", FilterOperator.GREATER_THAN, value)

    def profitability_rank_greater_than(self, value: int) -> "FilterBuilder":
        """Filter for Profitability rank greater than value."""
        return self.add_filter("profitability_rank", FilterOperator.GREATER_THAN, value)

    # --- Profitability Filters ---

    def roe_greater_than(self, value: float) -> "FilterBuilder":
        """Filter for ROE greater than value."""
        return self.add_filter("roe", FilterOperator.GREATER_THAN, value)

    def roic_greater_than(self, value: float) -> "FilterBuilder":
        """Filter for ROIC greater than value."""
        return self.add_filter("roic", FilterOperator.GREATER_THAN, value)

    def gross_margin_greater_than(self, value: float) -> "FilterBuilder":
        """Filter for gross margin greater than value."""
        return self.add_filter("gross_margin", FilterOperator.GREATER_THAN, value)

    def operating_margin_greater_than(self, value: float) -> "FilterBuilder":
        """Filter for operating margin greater than value."""
        return self.add_filter("operating_margin", FilterOperator.GREATER_THAN, value)

    def net_margin_greater_than(self, value: float) -> "FilterBuilder":
        """Filter for net margin greater than value."""
        return self.add_filter("net_margin", FilterOperator.GREATER_THAN, value)

    # --- Growth Filters ---

    def revenue_growth_greater_than(self, value: float) -> "FilterBuilder":
        """Filter for revenue growth greater than value."""
        return self.add_filter("revenue_growth", FilterOperator.GREATER_THAN, value)

    def eps_growth_greater_than(self, value: float) -> "FilterBuilder":
        """Filter for EPS growth greater than value."""
        return self.add_filter("eps_growth", FilterOperator.GREATER_THAN, value)

    # --- Dividend Filters ---

    def dividend_yield_greater_than(self, value: float) -> "FilterBuilder":
        """Filter for dividend yield greater than value."""
        return self.add_filter("dividend_yield", FilterOperator.GREATER_THAN, value)

    def dividend_yield_less_than(self, value: float) -> "FilterBuilder":
        """Filter for dividend yield less than value."""
        return self.add_filter("dividend_yield", FilterOperator.LESS_THAN, value)

    def payout_ratio_less_than(self, value: float) -> "FilterBuilder":
        """Filter for payout ratio less than value."""
        return self.add_filter("payout_ratio", FilterOperator.LESS_THAN, value)

    # --- Exchange/Region Filters ---

    def exchange_in(self, exchanges: list[str]) -> "FilterBuilder":
        """Filter for stocks in specific exchanges."""
        return self.add_filter("exchange", FilterOperator.IN, exchanges)

    def sector_equals(self, sector: str) -> "FilterBuilder":
        """Filter for stocks in a specific sector."""
        return self.add_filter("sector", FilterOperator.EQUALS, sector)

    def industry_equals(self, industry: str) -> "FilterBuilder":
        """Filter for stocks in a specific industry."""
        return self.add_filter("industry", FilterOperator.EQUALS, industry)

    def country_equals(self, country: str) -> "FilterBuilder":
        """Filter for stocks in a specific country."""
        return self.add_filter("country", FilterOperator.EQUALS, country)


# --- Pre-built Filter Sets ---


def quality_filters() -> list[ScreenerFilter]:
    """Pre-built filters for high-quality stocks.

    Criteria:
    - GF Score > 80
    - Financial Strength > 6
    - Profitability rank > 6
    - ROE > 15%

    Returns:
        List of filters for quality screening
    """
    return (
        FilterBuilder()
        .gf_score_greater_than(80)
        .financial_strength_greater_than(6)
        .profitability_rank_greater_than(6)
        .roe_greater_than(15)
        .build()
    )


def value_filters() -> list[ScreenerFilter]:
    """Pre-built filters for value stocks.

    Criteria:
    - P/E ratio < 15
    - P/B ratio < 2
    - PEG ratio < 1.5

    Returns:
        List of filters for value screening
    """
    return (
        FilterBuilder()
        .pe_ratio_less_than(15)
        .pb_ratio_less_than(2)
        .peg_ratio_less_than(1.5)
        .build()
    )


def growth_filters() -> list[ScreenerFilter]:
    """Pre-built filters for growth stocks.

    Criteria:
    - Revenue growth > 20%
    - EPS growth > 20%
    - Gross margin > 40%

    Returns:
        List of filters for growth screening
    """
    return (
        FilterBuilder()
        .revenue_growth_greater_than(20)
        .eps_growth_greater_than(20)
        .gross_margin_greater_than(40)
        .build()
    )


def dividend_filters() -> list[ScreenerFilter]:
    """Pre-built filters for dividend stocks.

    Criteria:
    - Dividend yield > 3%
    - Payout ratio < 70%
    - Financial Strength > 5

    Returns:
        List of filters for dividend screening
    """
    return (
        FilterBuilder()
        .dividend_yield_greater_than(3)
        .payout_ratio_less_than(70)
        .financial_strength_greater_than(5)
        .build()
    )


def deep_value_filters() -> list[ScreenerFilter]:
    """Pre-built filters for deep value (Graham-style) stocks.

    Criteria:
    - P/E ratio < 10
    - P/B ratio < 1.5
    - Financial Strength > 5

    Returns:
        List of filters for deep value screening
    """
    return (
        FilterBuilder()
        .pe_ratio_less_than(10)
        .pb_ratio_less_than(1.5)
        .financial_strength_greater_than(5)
        .build()
    )


# --- Helper Functions ---


def _parse_screener_stock(data: dict[str, Any]) -> ScreenerStock:
    """Parse a single screener stock from API data."""
    # Standard fields
    standard_fields = {
        "symbol",
        "company_name",
        "exchange",
        "sector",
        "industry",
        "country",
        "price",
        "market_cap",
        "volume",
        "pe_ratio",
        "pb_ratio",
        "ps_ratio",
        "peg_ratio",
        "ev_ebitda",
        "gf_score",
        "gf_value",
        "financial_strength",
        "profitability_rank",
        "roe",
        "roic",
        "gross_margin",
        "operating_margin",
        "net_margin",
        "revenue_growth",
        "eps_growth",
        "dividend_yield",
        "payout_ratio",
    }

    # Extract extra fields (anything not in standard set)
    extra = {k: v for k, v in data.items() if k not in standard_fields}

    return ScreenerStock(
        symbol=data.get("symbol", data.get("ticker", "")),
        company_name=data.get("company_name", data.get("company", data.get("name"))),
        exchange=data.get("exchange"),
        sector=data.get("sector"),
        industry=data.get("industry"),
        country=data.get("country"),
        price=_get_float(data, "price", "current_price"),
        market_cap=_get_float(data, "market_cap", "marketCap"),
        volume=_get_int(data, "volume", "avg_volume"),
        pe_ratio=_get_float(data, "pe_ratio", "pe", "peRatio"),
        pb_ratio=_get_float(data, "pb_ratio", "pb", "pbRatio"),
        ps_ratio=_get_float(data, "ps_ratio", "ps", "psRatio"),
        peg_ratio=_get_float(data, "peg_ratio", "peg", "pegRatio"),
        ev_ebitda=_get_float(data, "ev_ebitda", "evEbitda"),
        gf_score=_get_int(data, "gf_score", "gfScore"),
        gf_value=_get_float(data, "gf_value", "gfValue"),
        financial_strength=_get_int(data, "financial_strength", "financialStrength"),
        profitability_rank=_get_int(data, "profitability_rank", "profitabilityRank"),
        roe=_get_float(data, "roe", "ROE"),
        roic=_get_float(data, "roic", "ROIC"),
        gross_margin=_get_float(data, "gross_margin", "grossMargin"),
        operating_margin=_get_float(data, "operating_margin", "operatingMargin"),
        net_margin=_get_float(data, "net_margin", "netMargin"),
        revenue_growth=_get_float(data, "revenue_growth", "revenueGrowth"),
        eps_growth=_get_float(data, "eps_growth", "epsGrowth"),
        dividend_yield=_get_float(data, "dividend_yield", "dividendYield"),
        payout_ratio=_get_float(data, "payout_ratio", "payoutRatio"),
        extra_fields=extra,
    )


def _get_float(data: dict[str, Any], *keys: str) -> float | None:
    """Get a float value from dict, trying multiple possible keys."""
    for key in keys:
        value = data.get(key)
        if value is not None:
            try:
                return float(value)
            except (TypeError, ValueError):
                continue
    return None


def _get_int(data: dict[str, Any], *keys: str) -> int | None:
    """Get an int value from dict, trying multiple possible keys."""
    for key in keys:
        value = data.get(key)
        if value is not None:
            try:
                return int(float(value))
            except (TypeError, ValueError):
                continue
    return None
