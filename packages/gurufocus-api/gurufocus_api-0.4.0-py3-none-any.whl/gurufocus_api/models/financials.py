"""Pydantic models for financial statements."""

from typing import Any

from pydantic import BaseModel, Field


class FinancialPeriod(BaseModel):
    """Financial data for a single period (annual or quarterly).

    Contains key metrics from income statement, balance sheet, and cash flow.
    All monetary values are in the company's reporting currency (typically millions).
    """

    period: str = Field(description="Fiscal period (e.g., '2024-09' or 'TTM')")
    is_preliminary: bool = Field(default=False, description="Whether data is preliminary")

    # Per-share data
    revenue_per_share: float | None = Field(default=None, description="Revenue per share")
    ebitda_per_share: float | None = Field(default=None, description="EBITDA per share")
    ebit_per_share: float | None = Field(default=None, description="EBIT per share")
    eps_diluted: float | None = Field(default=None, description="Diluted EPS")
    eps_without_nri: float | None = Field(
        default=None, description="EPS without non-recurring items"
    )
    fcf_per_share: float | None = Field(default=None, description="Free cash flow per share")
    operating_cf_per_share: float | None = Field(
        default=None, description="Operating cash flow per share"
    )
    dividends_per_share: float | None = Field(default=None, description="Dividends per share")
    book_value_per_share: float | None = Field(default=None, description="Book value per share")

    # Income statement
    revenue: float | None = Field(default=None, description="Total revenue")
    cost_of_goods_sold: float | None = Field(default=None, description="Cost of goods sold")
    gross_profit: float | None = Field(default=None, description="Gross profit")
    operating_income: float | None = Field(default=None, description="Operating income (EBIT)")
    pretax_income: float | None = Field(default=None, description="Pre-tax income")
    net_income: float | None = Field(default=None, description="Net income")
    ebitda: float | None = Field(default=None, description="EBITDA")

    # Balance sheet
    total_assets: float | None = Field(default=None, description="Total assets")
    total_liabilities: float | None = Field(default=None, description="Total liabilities")
    total_equity: float | None = Field(default=None, description="Total shareholders' equity")
    total_debt: float | None = Field(default=None, description="Total debt")
    cash_and_equivalents: float | None = Field(default=None, description="Cash and equivalents")
    total_current_assets: float | None = Field(default=None, description="Total current assets")
    total_current_liabilities: float | None = Field(
        default=None, description="Total current liabilities"
    )

    # Cash flow
    operating_cash_flow: float | None = Field(default=None, description="Cash from operations")
    capital_expenditures: float | None = Field(default=None, description="Capital expenditures")
    free_cash_flow: float | None = Field(default=None, description="Free cash flow")
    dividends_paid: float | None = Field(default=None, description="Dividends paid")

    # Margins
    gross_margin: float | None = Field(default=None, description="Gross margin (%)")
    operating_margin: float | None = Field(default=None, description="Operating margin (%)")
    net_margin: float | None = Field(default=None, description="Net margin (%)")


class FinancialStatements(BaseModel):
    """Collection of financial statements for a company.

    Contains historical financial data from the GuruFocus financials endpoint.
    Data is organized by period with both annual and quarterly options.
    """

    symbol: str = Field(description="Stock ticker symbol")
    currency: str | None = Field(default=None, description="Reporting currency")
    period_type: str = Field(default="annual", description="'annual' or 'quarterly'")
    report_frequency: str | None = Field(default=None, description="Financial report frequency")

    # Historical periods (most recent first after TTM)
    periods: list[FinancialPeriod] = Field(
        default_factory=list, description="Financial data by period"
    )

    @classmethod
    def from_api_response(
        cls,
        data: dict[str, Any],
        symbol: str,
        period_type: str = "annual",
    ) -> "FinancialStatements":
        """Create FinancialStatements from raw API response.

        Args:
            data: Raw JSON response from the API with structure:
                  {financials: {financial_template_parameters: {...},
                   annuals: {Fiscal Year: [...], income_statement: {...}, ...}}}
            symbol: Stock ticker symbol
            period_type: 'annual' or 'quarterly'

        Returns:
            Populated FinancialStatements instance
        """
        financials = data.get("financials", data)
        params = financials.get("financial_template_parameters", {})

        # Select annual or quarterly data
        period_data = financials.get("annuals" if period_type == "annual" else "quarterly", {})

        # Parse periods from column-oriented data
        periods = _parse_financial_periods(period_data)

        # Reverse to get most recent first (API returns oldest first)
        periods = list(reversed(periods))

        return cls(
            symbol=symbol,
            currency=params.get("currency"),
            period_type=period_type,
            report_frequency=params.get("financial_report_frequency"),
            periods=periods,
        )


def _parse_financial_periods(data: dict[str, Any]) -> list[FinancialPeriod]:
    """Parse column-oriented financial data into list of FinancialPeriod.

    Args:
        data: Dictionary with parallel arrays for each metric

    Returns:
        List of FinancialPeriod objects (oldest first)
    """
    fiscal_years = data.get("Fiscal Year", [])
    if not fiscal_years or not isinstance(fiscal_years, list):
        return []

    # Get nested sections
    per_share = data.get("per_share_data_array", {})
    income = data.get("income_statement", {})
    balance = data.get("balance_sheet", {})
    cashflow = data.get("cashflow_statement", {})
    ratios = data.get("common_size_ratios", {})
    preliminary = data.get("Preliminary", [])

    periods = []
    for i, period in enumerate(fiscal_years):
        periods.append(
            FinancialPeriod(
                period=str(period),
                is_preliminary=bool(_safe_index(preliminary, i)),
                # Per-share data
                revenue_per_share=_safe_index(per_share.get("Revenue per Share"), i),
                ebitda_per_share=_safe_index(per_share.get("EBITDA per Share"), i),
                ebit_per_share=_safe_index(per_share.get("EBIT per Share"), i),
                eps_diluted=_safe_index(per_share.get("Earnings per Share (Diluted)"), i),
                eps_without_nri=_safe_index(per_share.get("EPS without NRI"), i),
                fcf_per_share=_safe_index(per_share.get("Free Cash Flow per Share"), i),
                operating_cf_per_share=_safe_index(
                    per_share.get("Operating Cash Flow per Share"), i
                ),
                dividends_per_share=_safe_index(per_share.get("Dividends per Share"), i),
                book_value_per_share=_safe_index(per_share.get("Book Value per Share"), i),
                # Income statement
                revenue=_safe_index(income.get("Revenue"), i),
                cost_of_goods_sold=_safe_index(income.get("Cost of Goods Sold"), i),
                gross_profit=_safe_index(income.get("Gross Profit"), i),
                operating_income=_safe_index(income.get("Operating Income"), i),
                pretax_income=_safe_index(income.get("Pretax Income"), i),
                net_income=_safe_index(income.get("Net Income"), i),
                ebitda=_safe_index(income.get("EBITDA"), i),
                # Balance sheet
                total_assets=_safe_index(balance.get("Total Assets"), i),
                total_liabilities=_safe_index(balance.get("Total Liabilities"), i),
                total_equity=_safe_index(balance.get("Total Stockholders Equity"), i),
                total_debt=_safe_index(balance.get("Total Debt"), i),
                cash_and_equivalents=_safe_index(balance.get("Cash and Cash Equivalents"), i),
                total_current_assets=_safe_index(balance.get("Total Current Assets"), i),
                total_current_liabilities=_safe_index(balance.get("Total Current Liabilities"), i),
                # Cash flow
                operating_cash_flow=_safe_index(cashflow.get("Cash Flow from Operations"), i),
                capital_expenditures=_safe_index(
                    cashflow.get("Purchase Of Property, Plant, Equipment"), i
                ),
                free_cash_flow=_safe_index(cashflow.get("Free Cash Flow"), i),
                dividends_paid=_safe_index(cashflow.get("Common Stock Dividends Paid"), i),
                # Margins (from common_size_ratios)
                gross_margin=_safe_index(ratios.get("Gross Margin"), i),
                operating_margin=_safe_index(ratios.get("Operating Margin"), i),
                net_margin=_safe_index(ratios.get("Net Margin"), i),
            )
        )

    return periods


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

    if isinstance(value, str):
        value = value.strip()
        if value in ("", "N/A", "-"):
            return None
        value = value.replace(",", "")

    try:
        return float(value)
    except (TypeError, ValueError):
        return None
