"""Pydantic models for Insider Activity API responses."""

from typing import Any

from pydantic import BaseModel, Field


class InsiderUpdate(BaseModel):
    """A single insider transaction update."""

    symbol: str = Field(description="Stock ticker symbol")
    exchange: str = Field(description="Stock exchange")
    position: str = Field(description="Insider's position (e.g., 'CEO', 'Director')")
    date: str = Field(description="Transaction date (YYYY-MM-DD)")
    type: str = Field(description="Transaction type: 'S' (Sell) or 'P' (Purchase)")
    trans_share: int = Field(description="Number of shares transacted")
    final_share: int = Field(description="Final share count after transaction")
    price: float = Field(description="Transaction price per share")
    cost: float = Field(description="Total transaction cost (in thousands)")
    insider: str = Field(description="Insider name")
    file_date: str = Field(description="SEC filing date")
    add_date: str = Field(description="Date added to database")


class InsiderUpdatesResponse(BaseModel):
    """Response for insider updates endpoint."""

    updates: list[InsiderUpdate] = Field(
        default_factory=list, description="List of insider updates"
    )

    @classmethod
    def from_api_response(cls, data: list[dict[str, Any]]) -> "InsiderUpdatesResponse":
        """Create InsiderUpdatesResponse from raw API response."""
        updates = []
        for item in data:
            if isinstance(item, dict):
                updates.append(
                    InsiderUpdate(
                        symbol=item.get("symbol", ""),
                        exchange=item.get("exchange", ""),
                        position=item.get("position", ""),
                        date=item.get("date", ""),
                        type=item.get("type", ""),
                        trans_share=int(item.get("trans_share", 0)),
                        final_share=int(item.get("final_share", 0)),
                        price=float(item.get("price", 0)),
                        cost=float(item.get("cost", 0)),
                        insider=item.get("insider", ""),
                        file_date=item.get("file_date", ""),
                        add_date=item.get("add_date", ""),
                    )
                )
        return cls(updates=updates)


class InsiderBuyTransaction(BaseModel):
    """A single insider buy transaction (CEO/CFO buys)."""

    exchange: str = Field(description="Stock exchange")
    symbol: str = Field(description="Stock ticker symbol")
    company: str = Field(description="Company name")
    name: str = Field(description="Insider name")
    position: str = Field(description="Insider's position")
    date: str = Field(description="Transaction date")
    type: str = Field(description="Transaction type: 'S' or 'P'")
    trans_share: int = Field(description="Number of shares transacted")
    shares_change: float = Field(description="Percentage change in shares")
    trade_price: float = Field(description="Trade price per share")
    cost: float = Field(description="Total transaction cost")
    final_share: int = Field(description="Final share count")
    change_from_insider_trade: float = Field(description="Price change from insider trade")
    file_date: str = Field(description="SEC filing date")


class PaginatedResponse(BaseModel):
    """Base model for paginated API responses."""

    total: int = Field(description="Total number of records")
    per_page: int = Field(description="Records per page")
    current_page: int = Field(description="Current page number")
    last_page: int = Field(description="Last page number")
    from_record: int = Field(alias="from", description="Starting record number")
    to_record: int = Field(alias="to", description="Ending record number")


class InsiderBuysResponse(BaseModel):
    """Response for insider CEO/CFO buys endpoints."""

    total: int = Field(description="Total number of records")
    per_page: int = Field(description="Records per page")
    current_page: int = Field(description="Current page number")
    last_page: int = Field(description="Last page number")
    data: list[InsiderBuyTransaction] = Field(default_factory=list)

    @classmethod
    def from_api_response(cls, response: dict[str, Any]) -> "InsiderBuysResponse":
        """Create InsiderBuysResponse from raw API response."""
        data = []
        for item in response.get("data", []):
            if isinstance(item, dict):
                data.append(
                    InsiderBuyTransaction(
                        exchange=item.get("exchange", ""),
                        symbol=item.get("symbol", ""),
                        company=item.get("company", ""),
                        name=item.get("name", ""),
                        position=item.get("position", ""),
                        date=item.get("date", ""),
                        type=item.get("type", ""),
                        trans_share=int(item.get("trans_share", 0)),
                        shares_change=float(item.get("shares_change", 0)),
                        trade_price=float(item.get("trade_price", 0)),
                        cost=float(item.get("cost", 0)),
                        final_share=int(item.get("final_share", 0)),
                        change_from_insider_trade=float(item.get("change_from_insider_trade", 0)),
                        file_date=item.get("file_date", ""),
                    )
                )
        return cls(
            total=response.get("total", 0),
            per_page=response.get("per_page", 0),
            current_page=response.get("current_page", 0),
            last_page=response.get("last_page", 0),
            data=data,
        )


class ClusterBuySignal(BaseModel):
    """A cluster buy signal - multiple insiders buying."""

    exchange: str = Field(description="Stock exchange")
    symbol: str = Field(description="Stock ticker symbol")
    company: str = Field(description="Company name")
    insider_buy_count: int = Field(description="Total insider buy transactions")
    insider_buy_count_unique: int = Field(description="Unique insiders buying")
    buy_total_shares: int = Field(description="Total shares bought")
    buy_price_avg: float = Field(description="Average buy price")
    buy_price_value: float = Field(description="Total value of buys")
    buy_change_from_average: float = Field(description="Price change from average")
    buy_company_held_shares: float = Field(description="Percentage of company shares held")


class ClusterBuyResponse(BaseModel):
    """Response for cluster buy endpoint."""

    total: int = Field(description="Total number of records")
    per_page: int = Field(description="Records per page")
    current_page: int = Field(description="Current page number")
    last_page: int = Field(description="Last page number")
    data: list[ClusterBuySignal] = Field(default_factory=list)

    @classmethod
    def from_api_response(cls, response: dict[str, Any]) -> "ClusterBuyResponse":
        """Create ClusterBuyResponse from raw API response."""
        data = []
        for item in response.get("data", []):
            if isinstance(item, dict):
                data.append(
                    ClusterBuySignal(
                        exchange=item.get("exchange", ""),
                        symbol=item.get("symbol", ""),
                        company=item.get("company", ""),
                        insider_buy_count=int(item.get("insider_buy_count", 0)),
                        insider_buy_count_unique=int(item.get("insider_buy_count_unique", 0)),
                        buy_total_shares=int(item.get("buy_total_shares", 0)),
                        buy_price_avg=float(item.get("buy_price_avg", 0)),
                        buy_price_value=float(item.get("buy_price_value", 0)),
                        buy_change_from_average=float(item.get("buy_change_from_average", 0)),
                        buy_company_held_shares=float(item.get("buy_company_held_shares", 0)),
                    )
                )
        return cls(
            total=response.get("total", 0),
            per_page=response.get("per_page", 0),
            current_page=response.get("current_page", 0),
            last_page=response.get("last_page", 0),
            data=data,
        )


class DoubleBuySignal(BaseModel):
    """A double-down buy signal."""

    exchange: str = Field(description="Stock exchange")
    symbol: str = Field(description="Stock ticker symbol")
    company: str = Field(description="Company name")
    buy_add_count: int = Field(description="Additional buy count")
    insider_buy_count: int = Field(description="Total insider buy count")
    insider_buy_shares: int = Field(description="Total shares bought by insiders")


class DoubleBuyResponse(BaseModel):
    """Response for double buy endpoint."""

    total: int = Field(description="Total number of records")
    per_page: int = Field(description="Records per page")
    current_page: int = Field(description="Current page number")
    last_page: int = Field(description="Last page number")
    data: list[DoubleBuySignal] = Field(default_factory=list)

    @classmethod
    def from_api_response(cls, response: dict[str, Any]) -> "DoubleBuyResponse":
        """Create DoubleBuyResponse from raw API response."""
        data = []
        for item in response.get("data", []):
            if isinstance(item, dict):
                data.append(
                    DoubleBuySignal(
                        exchange=item.get("exchange", ""),
                        symbol=item.get("symbol", ""),
                        company=item.get("company", ""),
                        buy_add_count=int(item.get("buy_add_count", 0)),
                        insider_buy_count=int(item.get("insider_buy_count", 0)),
                        insider_buy_shares=int(item.get("insider_buy_shares", 0)),
                    )
                )
        return cls(
            total=response.get("total", 0),
            per_page=response.get("per_page", 0),
            current_page=response.get("current_page", 0),
            last_page=response.get("last_page", 0),
            data=data,
        )


class TripleBuySignal(BaseModel):
    """A triple-down buy signal."""

    exchange: str = Field(description="Stock exchange")
    symbol: str = Field(description="Stock ticker symbol")
    company: str = Field(description="Company name")
    buy_add_count: int = Field(description="Additional buy count")
    insider_buy_count: int = Field(description="Total insider buy count")
    total_buyback_1y: str = Field(description="Total buyback in 1 year (percentage)")


class TripleBuyResponse(BaseModel):
    """Response for triple buy endpoint."""

    total: int = Field(description="Total number of records")
    per_page: int = Field(description="Records per page")
    current_page: int = Field(description="Current page number")
    last_page: int = Field(description="Last page number")
    data: list[TripleBuySignal] = Field(default_factory=list)

    @classmethod
    def from_api_response(cls, response: dict[str, Any]) -> "TripleBuyResponse":
        """Create TripleBuyResponse from raw API response."""
        data = []
        for item in response.get("data", []):
            if isinstance(item, dict):
                data.append(
                    TripleBuySignal(
                        exchange=item.get("exchange", ""),
                        symbol=item.get("symbol", ""),
                        company=item.get("company", ""),
                        buy_add_count=int(item.get("buy_add_count", 0)),
                        insider_buy_count=int(item.get("insider_buy_count", 0)),
                        total_buyback_1y=str(item.get("total_buyback_1y", "")),
                    )
                )
        return cls(
            total=response.get("total", 0),
            per_page=response.get("per_page", 0),
            current_page=response.get("current_page", 0),
            last_page=response.get("last_page", 0),
            data=data,
        )


class InsiderInfo(BaseModel):
    """Information about an insider."""

    cik: str = Field(description="SEC CIK identifier")
    name: str = Field(description="Insider name")
    address: str | None = Field(default=None, description="Insider address")
    latest_transaction_date: str = Field(description="Date of latest transaction")
    companies: list[str] = Field(default_factory=list, description="Associated company symbols")


class InsiderListResponse(BaseModel):
    """Response for insider list endpoint."""

    data: list[InsiderInfo] = Field(default_factory=list)
    current_page: int = Field(default=1, description="Current page number")
    last_page: int = Field(default=1, description="Last page number")

    @classmethod
    def from_api_response(cls, response: dict[str, Any]) -> "InsiderListResponse":
        """Create InsiderListResponse from raw API response."""
        data = []
        for item in response.get("data", []):
            if isinstance(item, dict):
                companies = item.get("Companys", [])
                if not isinstance(companies, list):
                    companies = []
                data.append(
                    InsiderInfo(
                        cik=str(item.get("cik", "")),
                        name=item.get("name", ""),
                        address=item.get("address"),
                        latest_transaction_date=item.get("latest_transaction_date", ""),
                        companies=companies,
                    )
                )
        return cls(
            data=data,
            current_page=response.get("currentPage", 1),
            last_page=response.get("lastPage", 1),
        )
