"""Pydantic models for stock summary data."""

from typing import Any

from pydantic import BaseModel, Field


class GeneralInfo(BaseModel):
    """General company information."""

    company_name: str | None = Field(default=None, description="Full company name")
    current_price: float | None = Field(default=None, description="Current stock price")
    currency: str | None = Field(default=None, description="Currency symbol")
    country: str | None = Field(default=None, description="Country of domicile")
    exchange: str | None = Field(default=None, description="Stock exchange")
    sector: str | None = Field(default=None, description="Business sector")
    industry: str | None = Field(default=None, description="Industry")
    industry_group: str | None = Field(default=None, description="Industry group")
    subindustry: str | None = Field(default=None, description="Sub-industry")
    description: str | None = Field(default=None, description="Company description")
    short_description: str | None = Field(default=None, description="Short description")
    market_cap: float | None = Field(default=None, description="Market capitalization in millions")


class PriceInfo(BaseModel):
    """Current price and change information."""

    current: float | None = Field(default=None, description="Current stock price")
    change: float | None = Field(default=None, description="Price change (absolute)")
    change_pct: float | None = Field(default=None, description="Price change (percentage)")


class QualityScores(BaseModel):
    """GuruFocus quality scores and rankings."""

    gf_score: int | None = Field(default=None, description="Overall GF Score (0-100)")
    financial_strength: int | None = Field(
        default=None, description="Financial strength rank (0-10)"
    )
    profitability_rank: int | None = Field(default=None, description="Profitability rank (0-10)")
    growth_rank: int | None = Field(default=None, description="Growth rank (0-10)")
    gf_value_rank: int | None = Field(default=None, description="GF Value rank (0-10)")
    momentum_rank: int | None = Field(default=None, description="Momentum rank (0-10)")
    risk_assessment: str | None = Field(default=None, description="Risk assessment summary")
    valuation_status: str | None = Field(
        default=None, description="Valuation status (e.g., 'Modestly Overvalued')"
    )


class ValuationMetrics(BaseModel):
    """Valuation metrics from the chart section."""

    gf_value: float | None = Field(default=None, description="GuruFocus intrinsic value")
    earnings_power_value: float | None = Field(default=None, description="Earnings power value")
    tangible_book: float | None = Field(default=None, description="Tangible book value")
    projected_fcf: float | None = Field(default=None, description="Projected FCF value")
    dcf_fcf_based: float | None = Field(default=None, description="DCF (FCF based)")
    dcf_earnings_based: float | None = Field(default=None, description="DCF (Earnings based)")
    median_ps_value: float | None = Field(default=None, description="Median P/S value")
    graham_number: float | None = Field(default=None, description="Graham Number")
    peter_lynch_value: float | None = Field(default=None, description="Peter Lynch value")
    # Simple valuation ratios from company_data
    pe_ratio: float | None = Field(default=None, description="P/E ratio (TTM)")
    pb_ratio: float | None = Field(default=None, description="P/B ratio")
    ps_ratio: float | None = Field(default=None, description="P/S ratio")
    peg_ratio: float | None = Field(default=None, description="PEG ratio")
    ev_ebitda: float | None = Field(default=None, description="EV/EBITDA")
    discount_to_gf_value: float | None = Field(default=None, description="Discount to GF Value (%)")


class RatioHistory(BaseModel):
    """Historical values for a ratio."""

    low: float | None = Field(default=None, description="Historical low")
    high: float | None = Field(default=None, description="Historical high")
    med: float | None = Field(default=None, description="Historical median")


class RatioIndustry(BaseModel):
    """Industry comparison data for a ratio."""

    global_rank: int | None = Field(default=None, description="Rank within industry globally")
    indu_med: float | None = Field(default=None, description="Industry median")
    indu_tot: int | None = Field(default=None, description="Total companies in industry comparison")


class RatioValue(BaseModel):
    """A single financial ratio with history and industry comparison."""

    value: float | None = Field(default=None, description="Current ratio value")
    status: int | None = Field(default=None, description="Status indicator from API")
    his: RatioHistory | None = Field(default=None, description="Historical values")
    indu: RatioIndustry | None = Field(default=None, description="Industry comparison")


class FinancialRatios(BaseModel):
    """Key financial ratios."""

    pe_ttm: RatioValue | None = Field(default=None, description="P/E ratio (TTM)")
    forward_pe: RatioValue | None = Field(default=None, description="Forward P/E ratio")
    pb_ratio: RatioValue | None = Field(default=None, description="P/B ratio")
    ps_ratio: RatioValue | None = Field(default=None, description="P/S ratio")
    peg_ratio: RatioValue | None = Field(default=None, description="PEG ratio")
    ev_ebitda: RatioValue | None = Field(default=None, description="EV/EBITDA")
    current_ratio: RatioValue | None = Field(default=None, description="Current ratio")
    quick_ratio: RatioValue | None = Field(default=None, description="Quick ratio")
    cash_ratio: RatioValue | None = Field(default=None, description="Cash ratio")
    piotroski_score: RatioValue | None = Field(default=None, description="Piotroski F-Score")
    roe: RatioValue | None = Field(default=None, description="Return on equity")
    roa: RatioValue | None = Field(default=None, description="Return on assets")
    roic: RatioValue | None = Field(default=None, description="Return on invested capital")


class InstitutionalActivity(BaseModel):
    """Institutional and guru activity summary."""

    guru_buys_pct: float | None = Field(default=None, description="% of premium gurus buying")
    guru_sells_pct: float | None = Field(default=None, description="% of premium gurus selling")
    guru_holds_pct: float | None = Field(default=None, description="% of premium gurus holding")
    fund_buys_pct: float | None = Field(default=None, description="% of mutual funds buying")
    fund_sells_pct: float | None = Field(default=None, description="% of mutual funds selling")
    etf_buys_pct: float | None = Field(default=None, description="% of ETFs buying")
    etf_sells_pct: float | None = Field(default=None, description="% of ETFs selling")


class StockSummary(BaseModel):
    """Comprehensive stock summary from the GuruFocus summary endpoint.

    Contains general info, quality scores, valuation metrics, financial ratios,
    and institutional activity.
    """

    symbol: str = Field(description="Stock ticker symbol")

    # Main sections
    general: GeneralInfo | None = Field(default=None, description="General company info")
    quality: QualityScores | None = Field(default=None, description="Quality scores and rankings")
    valuation: ValuationMetrics | None = Field(default=None, description="Valuation metrics")
    ratios: FinancialRatios | None = Field(default=None, description="Financial ratios")
    institutional: InstitutionalActivity | None = Field(
        default=None, description="Institutional activity"
    )
    price: PriceInfo | None = Field(default=None, description="Current price information")

    # Convenience properties for easy access
    @property
    def company_name(self) -> str | None:
        """Get company name."""
        return self.general.company_name if self.general else None

    @property
    def exchange(self) -> str | None:
        """Get stock exchange."""
        return self.general.exchange if self.general else None

    @property
    def sector(self) -> str | None:
        """Get business sector."""
        return self.general.sector if self.general else None

    @property
    def industry(self) -> str | None:
        """Get industry."""
        return self.general.industry if self.general else None

    @property
    def market_cap(self) -> float | None:
        """Get market capitalization."""
        return self.general.market_cap if self.general else None

    @property
    def gf_score(self) -> QualityScores | None:
        """Get quality scores (alias for quality)."""
        return self.quality

    @classmethod
    def from_api_response(cls, data: dict[str, Any], symbol: str) -> "StockSummary":
        """Create StockSummary from raw API response.

        Args:
            data: Raw JSON response from the API with structure:
                  {summary: {general: {...}, chart: {...}, ratio: {...}, company_data: {...}, ...}}
            symbol: Stock ticker symbol

        Returns:
            Populated StockSummary instance
        """
        summary = data.get("summary", data)

        # Extract sections
        general_data = summary.get("general", {})
        chart_data = summary.get("chart", {})
        ratio_data = summary.get("ratio", {})
        company_data = summary.get("company_data", {})

        # Get current price from general or company_data
        current_price = _parse_float(general_data.get("price")) or _parse_float(
            company_data.get("price")
        )

        # Parse general info (merge general and company_data)
        general = GeneralInfo(
            company_name=general_data.get("company") or company_data.get("company"),
            current_price=current_price,
            currency=general_data.get("currency") or company_data.get("currency"),
            country=general_data.get("country") or company_data.get("country"),
            exchange=company_data.get("exchange"),
            sector=general_data.get("sector") or company_data.get("sector"),
            industry=general_data.get("group") or company_data.get("industry"),
            industry_group=general_data.get("group") or company_data.get("group"),
            subindustry=general_data.get("subindustry"),
            description=general_data.get("desc"),
            short_description=general_data.get("short_desc"),
            market_cap=_parse_float(company_data.get("mktcap")),
        )

        # Parse quality scores
        quality = QualityScores(
            gf_score=_parse_int(general_data.get("gf_score")),
            financial_strength=_parse_int(general_data.get("rank_financial_strength")),
            profitability_rank=_parse_int(general_data.get("rank_profitability")),
            growth_rank=_parse_int(general_data.get("rank_growth")),
            gf_value_rank=_parse_int(general_data.get("rank_gf_value")),
            momentum_rank=_parse_int(general_data.get("rank_momentum")),
            risk_assessment=general_data.get("risk_assessment"),
            valuation_status=general_data.get("gf_valuation"),
        )

        # Get GF Value for discount calculation
        gf_value = _parse_float(chart_data.get("GF Value"))

        # Calculate discount to GF Value
        discount_to_gf_value = None
        if gf_value and current_price and gf_value > 0:
            discount_to_gf_value = round(((gf_value - current_price) / gf_value) * 100, 2)

        # Parse valuation metrics from chart and company_data
        valuation = ValuationMetrics(
            gf_value=gf_value,
            earnings_power_value=_parse_float(chart_data.get("Earnings Power Value")),
            tangible_book=_parse_float(chart_data.get("Tangible Book")),
            projected_fcf=_parse_float(chart_data.get("Projected FCF")),
            dcf_fcf_based=_parse_float(chart_data.get("DCF (FCF Based)")),
            dcf_earnings_based=_parse_float(chart_data.get("DCF (Earnings Based)")),
            median_ps_value=_parse_float(chart_data.get("Median P/S Value")),
            graham_number=_parse_float(chart_data.get("Graham Number")),
            peter_lynch_value=_parse_float(chart_data.get("Peter Lynch Value")),
            # Simple valuation ratios from company_data
            pe_ratio=_parse_float(company_data.get("pe")),
            pb_ratio=_parse_float(company_data.get("pb")),
            ps_ratio=_parse_float(company_data.get("ps")),
            peg_ratio=_parse_float(company_data.get("peg")),
            ev_ebitda=_parse_float(company_data.get("ev2ebitda")),
            discount_to_gf_value=discount_to_gf_value,
        )

        # Parse financial ratios
        ratios = FinancialRatios(
            pe_ttm=_parse_ratio(ratio_data.get("P/E(ttm)")),
            forward_pe=_parse_ratio(ratio_data.get("Forward P/E")),
            pb_ratio=_parse_ratio(ratio_data.get("P/B")),
            ps_ratio=_parse_ratio(ratio_data.get("P/S")),
            peg_ratio=_parse_ratio(ratio_data.get("PEG")),
            ev_ebitda=_parse_ratio(ratio_data.get("EV-to-EBITDA")),
            current_ratio=_parse_ratio(ratio_data.get("Current Ratio")),
            quick_ratio=_parse_ratio(ratio_data.get("Quick Ratio")),
            cash_ratio=_parse_ratio(ratio_data.get("Cash Ratio")),
            piotroski_score=_parse_ratio(ratio_data.get("F-Score")),
            roe=_parse_ratio(ratio_data.get("ROE (%)")),
            roa=_parse_ratio(ratio_data.get("ROA (%)")),
            roic=_parse_ratio(ratio_data.get("ROIC (%)")),
        )

        # Parse institutional activity
        institutional = InstitutionalActivity(
            guru_buys_pct=_parse_float(general_data.get("percentage_of_premium_guru_buys")),
            guru_sells_pct=_parse_float(general_data.get("percentage_of_premium_guru_sells")),
            guru_holds_pct=_parse_float(general_data.get("percentage_of_premium_guru_holds")),
            fund_buys_pct=_parse_float(general_data.get("percentage_of_mutual_fund_buys")),
            fund_sells_pct=_parse_float(general_data.get("percentage_of_mutual_fund_sells")),
            etf_buys_pct=_parse_float(general_data.get("percentage_of_etf_buys")),
            etf_sells_pct=_parse_float(general_data.get("percentage_of_etf_sells")),
        )

        # Parse price info from company_data
        price = PriceInfo(
            current=current_price,
            change=_parse_float(company_data.get("p_change")),
            change_pct=_parse_float(company_data.get("p_pct_change")),
        )

        return cls(
            symbol=symbol,
            general=general,
            quality=quality,
            valuation=valuation,
            ratios=ratios,
            institutional=institutional,
            price=price,
        )


def _parse_ratio(data: dict[str, Any] | None) -> RatioValue | None:
    """Parse a ratio object from API data.

    Args:
        data: Ratio data with value, status, his (history), indu (industry) sub-objects

    Returns:
        RatioValue or None if data is None
    """
    if not data or not isinstance(data, dict):
        return None

    his_data = data.get("his", {})
    indu_data = data.get("indu", {})

    his = (
        RatioHistory(
            low=_parse_float(his_data.get("low")),
            high=_parse_float(his_data.get("high")),
            med=_parse_float(his_data.get("med")),
        )
        if his_data
        else None
    )

    indu = (
        RatioIndustry(
            global_rank=_parse_int(indu_data.get("global_rank")),
            indu_med=_parse_float(indu_data.get("indu_med")),
            indu_tot=_parse_int(indu_data.get("indu_tot")),
        )
        if indu_data
        else None
    )

    return RatioValue(
        value=_parse_float(data.get("value")),
        status=_parse_int(data.get("status")),
        his=his,
        indu=indu,
    )


def _parse_float(value: Any) -> float | None:
    """Parse a float value, handling None and string values."""
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


def _parse_int(value: Any) -> int | None:
    """Parse an int value, handling None and string values."""
    float_val = _parse_float(value)
    if float_val is None:
        return None
    try:
        return int(float_val)
    except (TypeError, ValueError):
        return None
