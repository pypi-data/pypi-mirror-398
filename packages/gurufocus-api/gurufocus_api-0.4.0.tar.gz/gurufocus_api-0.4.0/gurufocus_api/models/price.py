"""Pydantic models for price history data."""

from typing import Any

from pydantic import BaseModel, Field


class PricePoint(BaseModel):
    """A single historical price point."""

    date: str = Field(description="Date (YYYY-MM-DD)")
    price: float = Field(description="Closing price")


class PriceHistory(BaseModel):
    """Historical price data for a stock.

    Contains daily closing prices.
    """

    symbol: str = Field(description="Stock ticker symbol")

    # Price points (oldest first as returned by API)
    prices: list[PricePoint] = Field(default_factory=list, description="Historical price points")

    @classmethod
    def from_api_response(
        cls,
        data: dict[str, Any],
        symbol: str,
    ) -> "PriceHistory":
        """Create PriceHistory from raw API response.

        Args:
            data: Raw JSON response from the API - may contain price data nested
            symbol: Stock ticker symbol

        Returns:
            Populated PriceHistory instance
        """
        prices: list[PricePoint] = []

        # Handle different API response structures
        price_data: list[list[Any]] = []
        if isinstance(data, list):
            price_data = data
        elif isinstance(data, dict):
            # Try common keys where price data might be nested
            price_data = (
                data.get("prices", [])
                or data.get("data", [])
                or data.get("price", [])
                or (next(iter(data.values())) if data else [])
            )
            if not isinstance(price_data, list):
                price_data = []

        for item in price_data:
            if isinstance(item, list) and len(item) >= 2:
                date_str = item[0]
                price_val = item[1]

                # Convert MM-DD-YYYY to YYYY-MM-DD
                converted_date = _convert_date(date_str)

                try:
                    prices.append(
                        PricePoint(
                            date=converted_date,
                            price=float(price_val),
                        )
                    )
                except (TypeError, ValueError):
                    continue

        return cls(
            symbol=symbol,
            prices=prices,
        )


def _convert_date(date_str: str) -> str:
    """Convert MM-DD-YYYY to YYYY-MM-DD format.

    Args:
        date_str: Date string in MM-DD-YYYY format

    Returns:
        Date string in YYYY-MM-DD format
    """
    try:
        parts = date_str.split("-")
        if len(parts) == 3:
            month, day, year = parts
            return f"{year}-{month}-{day}"
    except (AttributeError, ValueError):
        pass
    return date_str
