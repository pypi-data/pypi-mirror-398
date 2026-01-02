"""Pydantic models for insider trading data."""

from typing import Any

from pydantic import BaseModel, Field


class InsiderTrade(BaseModel):
    """A single insider trading transaction."""

    trade_date: str | None = Field(default=None, description="Transaction date (YYYY-MM-DD)")
    insider_name: str | None = Field(default=None, description="Name of the insider")
    insider_title: str | None = Field(default=None, description="Title/position of the insider")
    transaction_type: str | None = Field(
        default=None, description="Type of transaction (S=Sell, B=Buy, etc.)"
    )
    shares: float | None = Field(default=None, description="Number of shares transacted")
    price: float | None = Field(default=None, description="Price per share")
    value: float | None = Field(default=None, description="Total transaction value (cost)")
    shares_owned_after: float | None = Field(
        default=None, description="Shares owned after transaction"
    )
    change: float | None = Field(default=None, description="Percent change")


class InsiderTrades(BaseModel):
    """Insider trading data for a stock.

    Contains transaction history (most recent first).
    """

    symbol: str = Field(description="Stock ticker symbol")

    # Transaction history
    trades: list[InsiderTrade] = Field(
        default_factory=list, description="Insider transactions (most recent first)"
    )

    @classmethod
    def from_api_response(cls, data: dict[str, Any], symbol: str) -> "InsiderTrades":
        """Create InsiderTrades from raw API response.

        Args:
            data: Raw JSON response from the API - dict with symbol as key
                  e.g., {"AAPL": [{...}, {...}]}
            symbol: Stock ticker symbol

        Returns:
            Populated InsiderTrades instance
        """
        # API returns {symbol: [trades]}
        trades_raw = data.get(symbol, [])
        if not isinstance(trades_raw, list):
            trades_raw = []

        trades = [_parse_insider_trade(item) for item in trades_raw if isinstance(item, dict)]

        return cls(
            symbol=symbol,
            trades=trades,
        )


def _parse_insider_trade(data: dict[str, Any]) -> InsiderTrade:
    """Parse a single insider trade from API data."""
    return InsiderTrade(
        trade_date=data.get("date"),
        insider_name=data.get("insider"),
        insider_title=data.get("position"),
        transaction_type=data.get("type"),
        shares=_parse_numeric(data.get("trans_share")),
        price=_parse_numeric(data.get("price")),
        value=_parse_numeric(data.get("cost")),
        shares_owned_after=_parse_numeric(data.get("final_share")),
        change=_parse_numeric(data.get("change")),
    )


def _parse_numeric(value: Any) -> float | None:
    """Parse a numeric value, handling comma-formatted strings.

    Args:
        value: Value to parse (may be string with commas like "129,963")

    Returns:
        Float value or None if parsing fails
    """
    if value is None:
        return None

    try:
        if isinstance(value, str):
            # Remove commas from formatted numbers
            value = value.replace(",", "")
        return float(value)
    except (TypeError, ValueError):
        return None
