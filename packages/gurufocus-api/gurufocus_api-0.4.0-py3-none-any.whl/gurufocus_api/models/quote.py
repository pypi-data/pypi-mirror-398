"""Pydantic models for stock quote data."""

from typing import Any

from pydantic import BaseModel, Field


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
    """Parse an integer value, handling None and string values."""
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        if value in ("", "N/A", "-"):
            return None
        value = value.replace(",", "")
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


class StockQuote(BaseModel):
    """Real-time stock quote data.

    Contains current price, daily OHLV data, and price changes.
    This is a lightweight endpoint for getting current market data
    without the full summary information.
    """

    symbol: str = Field(description="Stock ticker symbol")
    exchange: str | None = Field(default=None, description="Stock exchange code")
    currency: str | None = Field(default=None, description="Currency code (e.g., USD)")
    timestamp: int | None = Field(default=None, description="Unix timestamp of price update")
    price_updated_time: str | None = Field(
        default=None, description="Human-readable price update time"
    )

    # Current price data
    current_price: float | None = Field(default=None, description="Current stock price")
    price_change: float | None = Field(
        default=None, description="Absolute price change from previous close"
    )
    price_change_pct: float | None = Field(
        default=None, description="Percentage price change from previous close"
    )

    # Daily OHLV data
    open: float | None = Field(default=None, description="Opening price for the day")
    high: float | None = Field(default=None, description="Highest price for the day")
    low: float | None = Field(default=None, description="Lowest price for the day")
    volume: int | None = Field(default=None, description="Trading volume for the day")

    @classmethod
    def from_api_response(cls, data: dict[str, Any], symbol: str) -> "StockQuote":
        """Parse raw API response into StockQuote model.

        Args:
            data: Raw API response dictionary
            symbol: Stock ticker symbol

        Returns:
            StockQuote instance with parsed data
        """
        symbol = symbol.upper().strip()

        return cls(
            symbol=data.get("Symbol", symbol),
            exchange=data.get("Exchange"),
            currency=data.get("Currency"),
            timestamp=_parse_int(data.get("timestamp")),
            price_updated_time=data.get("Price Updated Time"),
            current_price=_parse_float(data.get("Current Price") or data.get("Price")),
            price_change=_parse_float(data.get("Price Change")),
            price_change_pct=_parse_float(data.get("Day's Change %")),
            open=_parse_float(data.get("open")),
            high=_parse_float(data.get("high")),
            low=_parse_float(data.get("low")),
            volume=_parse_int(data.get("Day's Volume")),
        )
