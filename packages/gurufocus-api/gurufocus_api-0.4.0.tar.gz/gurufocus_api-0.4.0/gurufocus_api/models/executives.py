"""Pydantic models for company executives data."""

from typing import Any

from pydantic import BaseModel, Field


class Executive(BaseModel):
    """A company executive or director."""

    name: str = Field(description="Executive name")
    position: str = Field(description="Title/position (e.g., 'director, officer: CEO')")
    transaction_date: str = Field(description="Date of last transaction (YYYY-MM-DD)")


class ExecutiveList(BaseModel):
    """List of company executives and directors.

    Response from GET /stock/{symbol}/executives endpoint.
    """

    symbol: str = Field(description="Stock ticker symbol")
    executives: list[Executive] = Field(
        default_factory=list, description="List of executives and directors"
    )

    @classmethod
    def from_api_response(cls, data: list[dict[str, Any]], symbol: str) -> "ExecutiveList":
        """Create ExecutiveList from raw API response.

        Args:
            data: Raw JSON response from the API - list of executive dicts
                  e.g., [{"name": "...", "position": "...", "transaction_date": "..."}]
            symbol: Stock ticker symbol

        Returns:
            Populated ExecutiveList instance
        """
        symbol = symbol.upper().strip()

        # Parse executives list
        executives = [_parse_executive(e) for e in data if isinstance(e, dict)]

        return cls(
            symbol=symbol,
            executives=executives,
        )


def _parse_executive(data: dict[str, Any]) -> Executive:
    """Parse a single executive from API data."""
    return Executive(
        name=data.get("name", "Unknown"),
        position=data.get("position", ""),
        transaction_date=data.get("transaction_date", ""),
    )
