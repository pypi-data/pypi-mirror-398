"""Pydantic models for OHLC price data."""

from contextlib import suppress
from typing import Any

from pydantic import BaseModel, Field


class OHLCBar(BaseModel):
    """A single OHLC price bar."""

    date: str = Field(description="Date (YYYY-MM-DD)")
    open: float | None = Field(default=None, description="Opening price")
    high: float | None = Field(default=None, description="Highest price")
    low: float | None = Field(default=None, description="Lowest price")
    close: float | None = Field(default=None, description="Closing price")
    volume: int | None = Field(default=None, description="Trading volume")
    unadjusted_close: float | None = Field(default=None, description="Unadjusted closing price")


class OHLCHistory(BaseModel):
    """OHLC price history for a stock.

    Contains daily OHLC bars with volume data.
    """

    symbol: str = Field(description="Stock ticker symbol")
    bars: list[OHLCBar] = Field(default_factory=list, description="OHLC price bars")

    @classmethod
    def from_api_response(cls, data: list[dict[str, Any]], symbol: str) -> "OHLCHistory":
        """Create OHLCHistory from raw API response.

        Args:
            data: Raw JSON response from the API (list of OHLC objects)
            symbol: Stock ticker symbol

        Returns:
            Populated OHLCHistory instance
        """
        bars: list[OHLCBar] = []

        for item in data:
            if isinstance(item, dict):
                bars.append(_parse_ohlc_bar(item))

        return cls(
            symbol=symbol.upper().strip(),
            bars=bars,
        )


def _parse_float(value: Any) -> float | None:
    """Parse a float value, handling None and string values."""
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        if value in ("", "N/A", "-"):
            return None
    with suppress(TypeError, ValueError):
        return float(value)
    return None


def _parse_int(value: Any) -> int | None:
    """Parse an int value, handling None and string values."""
    if value is None:
        return None
    with suppress(TypeError, ValueError):
        return int(value)
    return None


def _parse_ohlc_bar(data: dict[str, Any]) -> OHLCBar:
    """Parse a single OHLC bar from API data."""
    return OHLCBar(
        date=data.get("date", ""),
        open=_parse_float(data.get("open")),
        high=_parse_float(data.get("high")),
        low=_parse_float(data.get("low")),
        close=_parse_float(data.get("close")),
        volume=_parse_int(data.get("volume")),
        unadjusted_close=_parse_float(data.get("unadjusted_close")),
    )


class VolumePoint(BaseModel):
    """A single volume data point."""

    date: str = Field(description="Date (MM-DD-YYYY)")
    volume: int = Field(description="Trading volume")


class VolumeHistory(BaseModel):
    """Volume history for a stock."""

    symbol: str = Field(description="Stock ticker symbol")
    data: list[VolumePoint] = Field(default_factory=list, description="Volume data points")

    @classmethod
    def from_api_response(cls, data: list[list[Any]], symbol: str) -> "VolumeHistory":
        """Create VolumeHistory from raw API response.

        Args:
            data: Raw JSON response (list of [date, volume] arrays)
            symbol: Stock ticker symbol

        Returns:
            Populated VolumeHistory instance
        """
        points: list[VolumePoint] = []

        for item in data:
            if isinstance(item, list) and len(item) >= 2:
                volume = _parse_int(item[1])
                if volume is not None:
                    points.append(VolumePoint(date=str(item[0]), volume=volume))

        return cls(
            symbol=symbol.upper().strip(),
            data=points,
        )


class UnadjustedPricePoint(BaseModel):
    """A single unadjusted price data point."""

    date: str = Field(description="Date (MM-DD-YYYY)")
    price: float = Field(description="Unadjusted price")


class UnadjustedPriceHistory(BaseModel):
    """Unadjusted price history for a stock."""

    symbol: str = Field(description="Stock ticker symbol")
    prices: list[UnadjustedPricePoint] = Field(
        default_factory=list, description="Unadjusted price data points"
    )

    @classmethod
    def from_api_response(cls, data: list[list[Any]], symbol: str) -> "UnadjustedPriceHistory":
        """Create UnadjustedPriceHistory from raw API response.

        Args:
            data: Raw JSON response (list of [date, price] arrays)
            symbol: Stock ticker symbol

        Returns:
            Populated UnadjustedPriceHistory instance
        """
        points: list[UnadjustedPricePoint] = []

        for item in data:
            if isinstance(item, list) and len(item) >= 2:
                price = _parse_float(item[1])
                if price is not None:
                    points.append(UnadjustedPricePoint(date=str(item[0]), price=price))

        return cls(
            symbol=symbol.upper().strip(),
            prices=points,
        )
