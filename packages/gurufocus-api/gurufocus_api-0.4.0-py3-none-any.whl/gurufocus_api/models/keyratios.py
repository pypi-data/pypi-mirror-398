"""Pydantic models for key financial ratios."""

from typing import Any

from pydantic import BaseModel, Field


class ProfitabilityRatios(BaseModel):
    """Profitability and return metrics."""

    roe: float | None = Field(default=None, description="Return on Equity (%)")
    roa: float | None = Field(default=None, description="Return on Assets (%)")
    roic: float | None = Field(default=None, description="Return on Invested Capital (%)")
    roce: float | None = Field(default=None, description="Return on Capital Employed (%)")
    gross_margin: float | None = Field(default=None, description="Gross Margin (%)")
    operating_margin: float | None = Field(default=None, description="Operating Margin (%)")
    net_margin: float | None = Field(default=None, description="Net Profit Margin (%)")
    fcf_margin: float | None = Field(default=None, description="Free Cash Flow Margin (%)")
    ebitda_margin: float | None = Field(default=None, description="EBITDA Margin (%)")


class LiquidityRatios(BaseModel):
    """Liquidity and short-term solvency metrics."""

    current_ratio: float | None = Field(
        default=None, description="Current Assets / Current Liabilities"
    )
    quick_ratio: float | None = Field(
        default=None, description="(Current Assets - Inventory) / Current Liabilities"
    )
    cash_ratio: float | None = Field(default=None, description="Cash / Current Liabilities")


class SolvencyRatios(BaseModel):
    """Solvency and leverage metrics."""

    debt_to_equity: float | None = Field(
        default=None, description="Total Debt / Shareholder Equity"
    )
    debt_to_asset: float | None = Field(default=None, description="Total Debt / Total Assets")
    debt_to_ebitda: float | None = Field(default=None, description="Total Debt / EBITDA")
    interest_coverage: float | None = Field(default=None, description="EBIT / Interest Expense")
    equity_to_asset: float | None = Field(
        default=None, description="Shareholder Equity / Total Assets"
    )


class EfficiencyRatios(BaseModel):
    """Efficiency and turnover metrics."""

    asset_turnover: float | None = Field(default=None, description="Revenue / Average Total Assets")
    inventory_turnover: float | None = Field(default=None, description="COGS / Average Inventory")
    receivables_turnover: float | None = Field(
        default=None, description="Revenue / Average Receivables"
    )
    days_sales_outstanding: float | None = Field(
        default=None, description="365 / Receivables Turnover"
    )
    days_inventory: float | None = Field(default=None, description="365 / Inventory Turnover")
    days_payable: float | None = Field(default=None, description="365 / Payables Turnover")
    cash_conversion_cycle: float | None = Field(
        default=None, description="Days Inventory + DSO - Days Payable"
    )


class GrowthRatios(BaseModel):
    """Growth metrics (year-over-year and multi-year)."""

    revenue_growth_1y: float | None = Field(default=None, description="Revenue growth YoY (%)")
    revenue_growth_3y: float | None = Field(default=None, description="Revenue 3-year CAGR (%)")
    revenue_growth_5y: float | None = Field(default=None, description="Revenue 5-year CAGR (%)")
    revenue_growth_10y: float | None = Field(default=None, description="Revenue 10-year CAGR (%)")
    eps_growth_1y: float | None = Field(default=None, description="EPS growth YoY (%)")
    eps_growth_3y: float | None = Field(default=None, description="EPS 3-year CAGR (%)")
    eps_growth_5y: float | None = Field(default=None, description="EPS 5-year CAGR (%)")
    eps_growth_10y: float | None = Field(default=None, description="EPS 10-year CAGR (%)")
    fcf_growth_1y: float | None = Field(default=None, description="FCF growth YoY (%)")
    fcf_growth_3y: float | None = Field(default=None, description="FCF 3-year CAGR (%)")
    fcf_growth_5y: float | None = Field(default=None, description="FCF 5-year CAGR (%)")


class PerShareData(BaseModel):
    """Per-share metrics."""

    eps_ttm: float | None = Field(default=None, description="Earnings Per Share (TTM)")
    eps_without_nri: float | None = Field(
        default=None, description="EPS without Non-Recurring Items"
    )
    book_value_per_share: float | None = Field(default=None, description="Book value per share")
    tangible_book_per_share: float | None = Field(
        default=None, description="Tangible book value per share"
    )
    fcf_per_share: float | None = Field(default=None, description="Free cash flow per share (TTM)")
    dividends_per_share_ttm: float | None = Field(
        default=None, description="Dividends per share (TTM)"
    )


class ValuationRatios(BaseModel):
    """Valuation metrics."""

    pe_ratio: float | None = Field(default=None, description="Price to Earnings ratio")
    pb_ratio: float | None = Field(default=None, description="Price to Book ratio")
    ps_ratio: float | None = Field(default=None, description="Price to Sales ratio")
    peg_ratio: float | None = Field(default=None, description="PE to Growth ratio")
    price_to_fcf: float | None = Field(default=None, description="Price to Free Cash Flow")
    ev_to_ebitda: float | None = Field(default=None, description="EV to EBITDA")
    ev_to_ebit: float | None = Field(default=None, description="EV to EBIT")
    ev_to_revenue: float | None = Field(default=None, description="EV to Revenue")
    gf_value: float | None = Field(default=None, description="GuruFocus intrinsic value")
    forward_pe: float | None = Field(default=None, description="Forward PE ratio")


class PriceMetrics(BaseModel):
    """Price and return metrics."""

    current_price: float | None = Field(default=None, description="Current stock price")
    high_52week: float | None = Field(default=None, description="52-week high")
    low_52week: float | None = Field(default=None, description="52-week low")
    beta: float | None = Field(default=None, description="Beta vs market")
    volatility_1y: float | None = Field(default=None, description="1-year price volatility (%)")
    return_1y: float | None = Field(default=None, description="1-year total return (%)")
    return_3y: float | None = Field(default=None, description="3-year annualized return (%)")
    return_5y: float | None = Field(default=None, description="5-year annualized return (%)")


class DividendMetrics(BaseModel):
    """Dividend metrics."""

    dividend_yield: float | None = Field(default=None, description="Current dividend yield (%)")
    forward_dividend_yield: float | None = Field(
        default=None, description="Forward dividend yield (%)"
    )
    payout_ratio: float | None = Field(default=None, description="Dividend payout ratio")
    dividend_growth_1y: float | None = Field(default=None, description="1-year dividend growth (%)")
    dividend_growth_3y: float | None = Field(default=None, description="3-year dividend CAGR (%)")
    dividend_growth_5y: float | None = Field(default=None, description="5-year dividend CAGR (%)")
    years_of_growth: int | None = Field(
        default=None, description="Consecutive years of dividend growth"
    )


class KeyRatios(BaseModel):
    """Comprehensive collection of key financial ratios.

    This model aggregates all important financial ratios into logical
    categories for easy analysis. Data is sourced from the GuruFocus keyratios
    endpoint which organizes data into sections: Basic, Fundamental,
    Valuation Ratio, Profitability, Growth, Price, and Dividends.
    """

    symbol: str = Field(description="Stock ticker symbol")
    company_name: str | None = Field(default=None, description="Company name")
    currency: str | None = Field(default=None, description="Reporting currency")

    # Quality scores
    piotroski_score: int | None = Field(
        default=None, ge=0, le=9, description="Piotroski F-Score (0-9)"
    )
    altman_z_score: float | None = Field(
        default=None, description="Altman Z-Score (bankruptcy predictor)"
    )
    beneish_m_score: float | None = Field(
        default=None, description="Beneish M-Score (earnings manipulation)"
    )
    gf_score: int | None = Field(default=None, description="GuruFocus Score (0-100)")
    financial_strength: int | None = Field(default=None, description="Financial Strength rank")
    profitability_rank: int | None = Field(default=None, description="Profitability rank")
    growth_rank: int | None = Field(default=None, description="Growth rank")

    # Ratio categories
    profitability: ProfitabilityRatios | None = Field(
        default=None, description="Profitability ratios"
    )
    liquidity: LiquidityRatios | None = Field(default=None, description="Liquidity ratios")
    solvency: SolvencyRatios | None = Field(default=None, description="Solvency ratios")
    efficiency: EfficiencyRatios | None = Field(default=None, description="Efficiency ratios")
    growth: GrowthRatios | None = Field(default=None, description="Growth ratios")
    per_share: PerShareData | None = Field(default=None, description="Per-share data")
    valuation: ValuationRatios | None = Field(default=None, description="Valuation ratios")
    price: PriceMetrics | None = Field(default=None, description="Price metrics")
    dividends: DividendMetrics | None = Field(default=None, description="Dividend metrics")

    @classmethod
    def from_api_response(cls, data: dict[str, Any], symbol: str) -> "KeyRatios":
        """Create KeyRatios from raw API response.

        Args:
            data: Raw JSON response from the API with sections:
                  Basic, Fundamental, Valuation Ratio, Profitability,
                  Growth, Price, Dividends
            symbol: Stock ticker symbol

        Returns:
            Populated KeyRatios instance
        """
        # Extract sections
        basic = data.get("Basic", {})
        fundamental = data.get("Fundamental", {})
        valuation_section = data.get("Valuation Ratio", {})
        profitability_section = data.get("Profitability", {})
        growth_section = data.get("Growth", {})
        price_section = data.get("Price", {})
        dividends_section = data.get("Dividends", {})

        # Extract profitability ratios
        profitability = ProfitabilityRatios(
            roe=_parse_float(fundamental.get("ROE %")),
            roa=_parse_float(fundamental.get("ROA %")),
            roic=_parse_float(fundamental.get("ROIC %")),
            roce=_parse_float(fundamental.get("ROCE %")),
            gross_margin=_parse_float(profitability_section.get("Gross Margin %")),
            operating_margin=_parse_float(profitability_section.get("Operating Margin %")),
            net_margin=_parse_float(profitability_section.get("Net Margin %")),
            fcf_margin=_parse_float(profitability_section.get("FCF Margin %")),
            ebitda_margin=_parse_float(profitability_section.get("EBITDA Margin %")),
        )

        # Extract liquidity ratios
        liquidity = LiquidityRatios(
            current_ratio=_parse_float(fundamental.get("Current Ratio")),
            quick_ratio=_parse_float(fundamental.get("Quick Ratio")),
            cash_ratio=_parse_float(fundamental.get("Cash Ratio")),
        )

        # Extract solvency ratios
        solvency = SolvencyRatios(
            debt_to_equity=_parse_float(fundamental.get("Debt-to-Equity")),
            debt_to_asset=_parse_float(fundamental.get("Debt-to-Asset")),
            debt_to_ebitda=_parse_float(fundamental.get("Debt-to-EBITDA")),
            interest_coverage=_parse_float(fundamental.get("Interest Coverage")),
            equity_to_asset=_parse_float(fundamental.get("Equity-to-Asset")),
        )

        # Extract efficiency ratios
        efficiency = EfficiencyRatios(
            asset_turnover=_parse_float(fundamental.get("Asset Turnover")),
            inventory_turnover=_parse_float(fundamental.get("Inventory Turnover")),
            receivables_turnover=_parse_float(fundamental.get("Receivables Turnover")),
            days_sales_outstanding=_parse_float(fundamental.get("Days Sales Outstanding")),
            days_inventory=_parse_float(fundamental.get("Days Inventory")),
            days_payable=_parse_float(fundamental.get("Days Payable")),
            cash_conversion_cycle=_parse_float(fundamental.get("Cash Conversion Cycle")),
        )

        # Extract growth ratios
        growth = GrowthRatios(
            revenue_growth_1y=_parse_float(
                growth_section.get("1-Year Revenue Growth Rate (Per Share)")
            ),
            revenue_growth_3y=_parse_float(
                growth_section.get("3-Year Revenue Growth Rate (Per Share)")
            ),
            revenue_growth_5y=_parse_float(
                growth_section.get("5-Year Revenue Growth Rate (Per Share)")
            ),
            revenue_growth_10y=_parse_float(
                growth_section.get("10-Year Revenue Growth Rate (Per Share)")
            ),
            eps_growth_1y=_parse_float(growth_section.get("1-Year EPS without NRI Growth Rate")),
            eps_growth_3y=_parse_float(growth_section.get("3-Year EPS without NRI Growth Rate")),
            eps_growth_5y=_parse_float(growth_section.get("5-Year EPS without NRI Growth Rate")),
            eps_growth_10y=_parse_float(growth_section.get("10-Year EPS without NRI Growth Rate")),
            fcf_growth_1y=_parse_float(growth_section.get("1-Year FCF Growth Rate (Per Share)")),
            fcf_growth_3y=_parse_float(growth_section.get("3-Year FCF Growth Rate (Per Share)")),
            fcf_growth_5y=_parse_float(growth_section.get("5-Year FCF Growth Rate (Per Share)")),
        )

        # Extract per-share data
        per_share = PerShareData(
            eps_ttm=_parse_float(fundamental.get("EPS (TTM)")),
            eps_without_nri=_parse_float(fundamental.get("EPS without NRI")),
            book_value_per_share=_parse_float(fundamental.get("Book Value per Share")),
            tangible_book_per_share=_parse_float(valuation_section.get("Tangible Book per Share")),
            fcf_per_share=_parse_float(fundamental.get("Trailing 12-Month FCF per Share")),
            dividends_per_share_ttm=_parse_float(
                dividends_section.get("Dividends per Share (TTM)")
            ),
        )

        # Extract valuation ratios
        valuation = ValuationRatios(
            pe_ratio=_parse_float(valuation_section.get("PE Ratio")),
            pb_ratio=_parse_float(valuation_section.get("PB Ratio")),
            ps_ratio=_parse_float(valuation_section.get("PS Ratio")),
            peg_ratio=_parse_float(valuation_section.get("PEG Ratio")),
            price_to_fcf=_parse_float(valuation_section.get("Price-to-Free-Cash-Flow")),
            ev_to_ebitda=_parse_float(valuation_section.get("EV-to-EBITDA")),
            ev_to_ebit=_parse_float(valuation_section.get("EV-to-EBIT")),
            ev_to_revenue=_parse_float(valuation_section.get("EV-to-Revenue")),
            gf_value=_parse_float(valuation_section.get("GF Value")),
            forward_pe=_parse_float(valuation_section.get("Forward PE Ratio")),
        )

        # Extract price metrics
        price_metrics = PriceMetrics(
            current_price=_parse_float(price_section.get("Current Price")),
            high_52week=_parse_float(price_section.get("Price (52w High)")),
            low_52week=_parse_float(price_section.get("Price (52w Low)")),
            beta=_parse_float(price_section.get("Beta")),
            volatility_1y=_parse_float(price_section.get("1-Year Volatility %")),
            return_1y=_parse_float(price_section.get("12-Month Total Return %")),
            return_3y=_parse_float(price_section.get("3-Year Annualized Total Return %")),
            return_5y=_parse_float(price_section.get("5-Year Annualized Total Return %")),
        )

        # Extract dividend metrics
        dividend_metrics = DividendMetrics(
            dividend_yield=_parse_float(dividends_section.get("Dividend Yield %")),
            forward_dividend_yield=_parse_float(dividends_section.get("Forward Dividend Yield %")),
            payout_ratio=_parse_float(dividends_section.get("Dividend Payout Ratio")),
            dividend_growth_1y=_parse_float(
                growth_section.get("1-Year Dividend Growth Rate (Per Share)")
            ),
            dividend_growth_3y=_parse_float(
                growth_section.get("3-Year Dividend Growth Rate (Per Share)")
            ),
            dividend_growth_5y=_parse_float(
                growth_section.get("5-Year Dividend Growth Rate (Per Share)")
            ),
            years_of_growth=_parse_int(dividends_section.get("Increase Dividend Start Year")),
        )

        return cls(
            symbol=symbol,
            company_name=basic.get("Company"),
            currency=fundamental.get("Currency"),
            piotroski_score=_parse_int(fundamental.get("Piotroski F-Score")),
            altman_z_score=_parse_float(fundamental.get("Altman Z-Score")),
            beneish_m_score=_parse_float(fundamental.get("Beneish M-Score")),
            gf_score=_parse_int(fundamental.get("GF Score")),
            financial_strength=_parse_int(fundamental.get("Financial Strength")),
            profitability_rank=_parse_int(fundamental.get("Profitability Rank")),
            growth_rank=_parse_int(fundamental.get("Growth Rank")),
            profitability=profitability,
            liquidity=liquidity,
            solvency=solvency,
            efficiency=efficiency,
            growth=growth,
            per_share=per_share,
            valuation=valuation,
            price=price_metrics,
            dividends=dividend_metrics,
        )


def _parse_float(value: Any) -> float | None:
    """Parse a float value, handling N/A and string values.

    Args:
        value: Value to parse (may be string, int, float, or "N/A")

    Returns:
        Float value or None if parsing fails or value is N/A
    """
    if value is None:
        return None

    # Handle "N/A" or "-" values
    if isinstance(value, str):
        value = value.strip()
        if value in ("N/A", "N\\A", "-", "", "None"):
            return None
        # Remove commas from formatted numbers
        value = value.replace(",", "")

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_int(value: Any) -> int | None:
    """Parse an int value, handling N/A and string values.

    Args:
        value: Value to parse (may be string, int, float, or "N/A")

    Returns:
        Int value or None if parsing fails or value is N/A
    """
    float_val = _parse_float(value)
    if float_val is None:
        return None
    try:
        return int(float_val)
    except (TypeError, ValueError):
        return None
