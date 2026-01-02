"""Pydantic models for dividend data."""

from contextlib import suppress
from typing import Any

from pydantic import BaseModel, Field


class DividendPayment(BaseModel):
    """A single dividend payment."""

    ex_date: str | None = Field(default=None, description="Ex-dividend date (YYYY-MM-DD)")
    record_date: str | None = Field(default=None, description="Record date (YYYY-MM-DD)")
    pay_date: str | None = Field(default=None, description="Payment date (YYYY-MM-DD)")
    amount: float | None = Field(default=None, description="Dividend amount per share")
    currency: str | None = Field(default=None, description="Currency of payment")
    dividend_type: str | None = Field(default=None, description="Type (e.g., 'Cash Div.')")


class DividendHistory(BaseModel):
    """Dividend history for a stock.

    Contains historical payment records (most recent first).
    """

    symbol: str = Field(description="Stock ticker symbol")

    # Historical payments
    payments: list[DividendPayment] = Field(
        default_factory=list, description="Historical dividend payments (most recent first)"
    )

    @classmethod
    def from_api_response(cls, data: dict[str, Any], symbol: str) -> "DividendHistory":
        """Create DividendHistory from raw API response.

        Args:
            data: Raw JSON response from the API - may contain dividend data nested
            symbol: Stock ticker symbol

        Returns:
            Populated DividendHistory instance
        """
        payments: list[DividendPayment] = []

        # Handle different API response structures
        dividend_data: list[dict[str, Any]] = []
        if isinstance(data, list):
            dividend_data = data
        elif isinstance(data, dict):
            # Try common keys where dividend data might be nested
            dividend_data = (
                data.get("dividends", [])
                or data.get("data", [])
                or (next(iter(data.values())) if data else [])
            )
            if not isinstance(dividend_data, list):
                dividend_data = []

        for item in dividend_data:
            if isinstance(item, dict):
                payments.append(_parse_dividend_payment(item))

        return cls(
            symbol=symbol,
            payments=payments,
        )


def _parse_dividend_payment(data: dict[str, Any]) -> DividendPayment:
    """Parse a single dividend payment from API data."""
    amount_str = data.get("amount")
    amount = None
    if amount_str is not None:
        with suppress(TypeError, ValueError):
            amount = float(amount_str)

    return DividendPayment(
        ex_date=data.get("ex_date"),
        record_date=data.get("record_date"),
        pay_date=data.get("pay_date"),
        amount=amount,
        currency=data.get("currency"),
        dividend_type=data.get("type"),
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
    with suppress(TypeError, ValueError):
        return float(value)
    return None


class CurrentDividend(BaseModel):
    """Current dividend information for a stock.

    Contains current yield, TTM dividend, and payment schedule.
    """

    symbol: str = Field(description="Stock ticker symbol")
    dividends_per_share_ttm: float | None = Field(
        default=None, description="Trailing twelve months dividends per share"
    )
    dividend_yield: float | None = Field(default=None, description="Current dividend yield (%)")
    dividend_yield_10y_range: str | None = Field(
        default=None, description="10-year yield range (e.g., '1.2 - 3.5')"
    )
    dividend_yield_10y_median: float | None = Field(
        default=None, description="10-year median dividend yield (%)"
    )
    next_payment_date: str | None = Field(
        default=None, description="Next dividend payment date (YYYY-MM-DD or N/A)"
    )
    frequency: str | None = Field(
        default=None, description="Payment frequency (e.g., Quarterly, Annual)"
    )
    currency: str | None = Field(default=None, description="Currency symbol (e.g., $)")

    @classmethod
    def from_api_response(cls, data: dict[str, Any], symbol: str) -> "CurrentDividend":
        """Create CurrentDividend from raw API response.

        Args:
            data: Raw JSON response from the API
            symbol: Stock ticker symbol

        Returns:
            Populated CurrentDividend instance
        """
        next_date = data.get("Next Dividend Payment Date")
        if next_date == "N/A":
            next_date = None

        return cls(
            symbol=symbol.upper().strip(),
            dividends_per_share_ttm=_parse_float(data.get("Dividends per Share (TTM)")),
            dividend_yield=_parse_float(data.get("Dividend Yield %")),
            dividend_yield_10y_range=data.get("Dividend Yield % (10y Range)"),
            dividend_yield_10y_median=_parse_float(data.get("Dividend Yield % (10y Median)")),
            next_payment_date=next_date,
            frequency=data.get("Dividend Frequency"),
            currency=data.get("Currency"),
        )
