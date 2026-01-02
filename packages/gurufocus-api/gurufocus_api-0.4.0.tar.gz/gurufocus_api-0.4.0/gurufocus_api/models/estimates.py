"""Pydantic models for analyst estimates data."""

from typing import Any

from pydantic import BaseModel, Field


class EstimatePeriod(BaseModel):
    """Analyst estimates for a single period (quarter or year)."""

    period: str = Field(description="Period in YYYYMM format (e.g., '202609')")

    # Revenue and income estimates
    revenue_estimate: float | None = Field(default=None, description="Revenue estimate")
    ebit_estimate: float | None = Field(default=None, description="EBIT estimate")
    ebitda_estimate: float | None = Field(default=None, description="EBITDA estimate")
    net_income_estimate: float | None = Field(default=None, description="Net income estimate")
    pretax_income_estimate: float | None = Field(
        default=None, description="Pre-tax income estimate"
    )

    # Per-share estimates
    eps_estimate: float | None = Field(default=None, description="EPS estimate")
    eps_nri_estimate: float | None = Field(default=None, description="EPS without NRI estimate")
    dividend_estimate: float | None = Field(default=None, description="Dividend per share estimate")
    book_value_per_share_estimate: float | None = Field(
        default=None, description="Book value per share estimate"
    )
    operating_cash_flow_per_share_estimate: float | None = Field(
        default=None, description="Operating cash flow per share estimate"
    )

    # Ratios and margins
    roa_estimate: float | None = Field(default=None, description="ROA estimate (%)")
    roe_estimate: float | None = Field(default=None, description="ROE estimate (%)")
    gross_margin_estimate: float | None = Field(
        default=None, description="Gross margin estimate (%)"
    )
    pe_ttm_estimate: float | None = Field(default=None, description="Trailing PE estimate")


class GrowthEstimates(BaseModel):
    """Future growth rate estimates."""

    long_term_growth_rate: float | None = Field(
        default=None, description="Long-term EPS growth rate estimate (%)"
    )
    long_term_revenue_growth_rate: float | None = Field(
        default=None, description="Long-term revenue growth rate estimate (%)"
    )
    eps_growth: float | None = Field(default=None, description="Future EPS growth (%)")
    eps_nri_growth: float | None = Field(
        default=None, description="Future EPS without NRI growth (%)"
    )
    revenue_growth: float | None = Field(default=None, description="Future revenue growth (%)")
    ebit_growth: float | None = Field(default=None, description="Future EBIT growth (%)")
    ebitda_growth: float | None = Field(default=None, description="Future EBITDA growth (%)")
    dividend_growth: float | None = Field(default=None, description="Future dividend growth (%)")
    net_income_growth: float | None = Field(
        default=None, description="Future net income growth (%)"
    )
    book_value_growth: float | None = Field(
        default=None, description="Future book value growth (%)"
    )


class AnalystEstimates(BaseModel):
    """Comprehensive analyst estimates for a stock.

    Contains EPS/revenue estimates for upcoming periods from the
    GuruFocus analyst_estimate endpoint. Data is column-oriented
    with parallel arrays for each metric.
    """

    symbol: str = Field(description="Stock ticker symbol")

    # Estimates by period
    annual_estimates: list[EstimatePeriod] = Field(
        default_factory=list, description="Annual estimates (next 1-3 fiscal years)"
    )
    quarterly_estimates: list[EstimatePeriod] = Field(
        default_factory=list, description="Quarterly estimates (next 4-8 quarters)"
    )

    # Growth estimates
    growth_estimates: GrowthEstimates | None = Field(
        default=None, description="Future growth rate estimates"
    )

    @classmethod
    def from_api_response(cls, data: dict[str, Any], symbol: str) -> "AnalystEstimates":
        """Create AnalystEstimates from raw API response.

        Args:
            data: Raw JSON response from the API with columns:
                  annual: {date: [...], revenue_estimate: [...], ...}
                  quarterly: {date: [...], revenue_estimate: [...], ...}
            symbol: Stock ticker symbol

        Returns:
            Populated AnalystEstimates instance
        """
        annual_data = data.get("annual", {})
        quarterly_data = data.get("quarterly", {})

        # Parse annual estimates (transpose columns to rows)
        annual_estimates = _parse_estimates_columns(annual_data)

        # Parse quarterly estimates (transpose columns to rows)
        quarterly_estimates = _parse_estimates_columns(quarterly_data)

        # Extract growth estimates (use annual data, fall back to quarterly)
        growth_data = annual_data if annual_data else quarterly_data
        growth_estimates = GrowthEstimates(
            long_term_growth_rate=_parse_float(growth_data.get("long_term_growth_rate_mean")),
            long_term_revenue_growth_rate=_parse_float(
                growth_data.get("long_term_revenue_growth_rate_mean")
            ),
            eps_growth=_parse_float(growth_data.get("future_per_share_eps_estimate_growth")),
            eps_nri_growth=_parse_float(growth_data.get("future_eps_nri_estimate_growth")),
            revenue_growth=_parse_float(growth_data.get("future_revenue_estimate_growth")),
            ebit_growth=_parse_float(growth_data.get("future_ebit_estimate_growth")),
            ebitda_growth=_parse_float(growth_data.get("future_ebitda_estimate_growth")),
            dividend_growth=_parse_float(growth_data.get("future_dividend_estimate_growth")),
            net_income_growth=_parse_float(growth_data.get("future_net_income_estimate_growth")),
            book_value_growth=_parse_float(
                growth_data.get("future_book_value_per_share_estimate_growth")
            ),
        )

        return cls(
            symbol=symbol,
            annual_estimates=annual_estimates,
            quarterly_estimates=quarterly_estimates,
            growth_estimates=growth_estimates,
        )


def _parse_estimates_columns(data: dict[str, Any]) -> list[EstimatePeriod]:
    """Parse column-oriented estimate data into list of EstimatePeriod.

    Args:
        data: Dictionary with parallel arrays (date, revenue_estimate, etc.)

    Returns:
        List of EstimatePeriod objects
    """
    dates = data.get("date", [])
    if not dates or not isinstance(dates, list):
        return []

    estimates = []
    for i, date in enumerate(dates):
        estimates.append(
            EstimatePeriod(
                period=str(date),
                revenue_estimate=_safe_index(data.get("revenue_estimate"), i),
                ebit_estimate=_safe_index(data.get("ebit_estimate"), i),
                ebitda_estimate=_safe_index(data.get("ebitda_estimate"), i),
                net_income_estimate=_safe_index(data.get("net_income_estimate"), i),
                pretax_income_estimate=_safe_index(data.get("pretax_income_estimate"), i),
                eps_estimate=_safe_index(data.get("per_share_eps_estimate"), i),
                eps_nri_estimate=_safe_index(data.get("eps_nri_estimate"), i),
                dividend_estimate=_safe_index(data.get("dividend_estimate"), i),
                book_value_per_share_estimate=_safe_index(
                    data.get("book_value_per_share_estimate"), i
                ),
                operating_cash_flow_per_share_estimate=_safe_index(
                    data.get("operating_cash_flow_per_share_estimate"), i
                ),
                roa_estimate=_safe_index(data.get("roa_estimate"), i),
                roe_estimate=_safe_index(data.get("roe_estimate"), i),
                gross_margin_estimate=_safe_index(data.get("gross_margin_estimate"), i),
                pe_ttm_estimate=_safe_index(data.get("pettm_estimate"), i),
            )
        )

    return estimates


def _safe_index(arr: list[Any] | None, idx: int) -> float | None:
    """Safely get a float value from an array by index.

    Args:
        arr: Array to index into (may be None)
        idx: Index to retrieve

    Returns:
        Float value or None if index out of bounds or value is None/null
    """
    if arr is None or not isinstance(arr, list):
        return None
    if idx < 0 or idx >= len(arr):
        return None

    value = arr[idx]
    return _parse_float(value)


def _parse_float(value: Any) -> float | None:
    """Parse a float value, handling None and string values.

    Args:
        value: Value to parse

    Returns:
        Float value or None if parsing fails
    """
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None
