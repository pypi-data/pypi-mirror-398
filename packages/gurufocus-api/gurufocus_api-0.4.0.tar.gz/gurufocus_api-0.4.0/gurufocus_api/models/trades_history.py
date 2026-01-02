"""Pydantic models for guru trades history data.

Models for the GET /stock/{symbol}/trades/history endpoint.
"""

from typing import Any

from pydantic import BaseModel, Field


class GuruTradeAction(BaseModel):
    """A single guru's buy or sell action in a period."""

    guru_id: int = Field(description="Unique identifier for the guru")
    guru_name: str = Field(description="Name of the guru or investment firm")
    share_change: int = Field(description="Number of shares changed (positive=buy, negative=sell)")


class TradesHistoryPeriod(BaseModel):
    """Trading activity for a single portfolio reporting period."""

    stockid: str = Field(description="Internal stock identifier")
    exchange: str = Field(description="Exchange code (e.g., NAS, NYSE)")
    symbol: str = Field(description="Stock ticker symbol")
    buy_count: int = Field(description="Number of gurus who bought in this period")
    buy_gurus: list[GuruTradeAction] = Field(
        default_factory=list, description="List of guru buy actions"
    )
    sell_count: int = Field(description="Number of gurus who sold in this period")
    sell_gurus: list[GuruTradeAction] = Field(
        default_factory=list, description="List of guru sell actions"
    )
    portdate: str = Field(description="Portfolio reporting date (YYYY-MM-DD)")
    display_symbol: str = Field(description="Display symbol")


class GuruTradesHistory(BaseModel):
    """Guru trades history for a stock.

    Contains a time series of trading activity organized by portfolio
    reporting periods, showing which gurus bought or sold shares.
    """

    symbol: str = Field(description="Stock ticker symbol")
    periods: list[TradesHistoryPeriod] = Field(
        default_factory=list, description="Trading activity by period"
    )

    @classmethod
    def from_api_response(cls, data: list[dict[str, Any]], symbol: str) -> "GuruTradesHistory":
        """Create a GuruTradesHistory from raw API response.

        Args:
            data: Raw API response (list of period records)
            symbol: Stock ticker symbol

        Returns:
            Parsed GuruTradesHistory model
        """
        symbol = symbol.upper().strip()
        periods = [_parse_period(p) for p in data if isinstance(p, dict)]
        return cls(symbol=symbol, periods=periods)


def _parse_guru_action(data: dict[str, Any]) -> GuruTradeAction:
    """Parse a single guru trade action."""
    return GuruTradeAction(
        guru_id=int(data.get("guru_id", 0)),
        guru_name=str(data.get("guru_name", "")),
        share_change=int(data.get("share_change", 0)),
    )


def _parse_period(data: dict[str, Any]) -> TradesHistoryPeriod:
    """Parse a single trading period record."""
    buy_gurus_raw = data.get("buy_gurus", [])
    sell_gurus_raw = data.get("sell_gurus", [])

    return TradesHistoryPeriod(
        stockid=str(data.get("stockid", "")),
        exchange=str(data.get("exchange", "")),
        symbol=str(data.get("symbol", "")),
        buy_count=int(data.get("buy_count", 0)),
        buy_gurus=[_parse_guru_action(g) for g in buy_gurus_raw if isinstance(g, dict)],
        sell_count=int(data.get("sell_count", 0)),
        sell_gurus=[_parse_guru_action(g) for g in sell_gurus_raw if isinstance(g, dict)],
        portdate=str(data.get("portdate", "")),
        display_symbol=str(data.get("display_symbol", "")),
    )
