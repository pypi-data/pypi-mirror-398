"""Insider activity API endpoints."""

from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any, cast

from ..cache.config import CacheCategory
from ..models.insider_updates import (
    ClusterBuyResponse,
    ClusterBuySignal,
    DoubleBuyResponse,
    DoubleBuySignal,
    InsiderBuysResponse,
    InsiderBuyTransaction,
    InsiderInfo,
    InsiderListResponse,
    InsiderUpdate,
    InsiderUpdatesResponse,
    TripleBuyResponse,
    TripleBuySignal,
)

if TYPE_CHECKING:
    from ..client import GuruFocusClient


class InsidersEndpoint:
    """Endpoints for insider trading activity data.

    This class provides methods for fetching insider trading signals
    from the GuruFocus API including CEO/CFO buys, cluster buys,
    double/triple-down signals, and insider lists.

    Example:
        async with GuruFocusClient() as client:
            updates = await client.insiders.get_updates()
            print(f"Recent updates: {len(updates.updates)}")

            ceo_buys = await client.insiders.get_ceo_buys()
            print(f"CEO buys: {ceo_buys.total} total")
    """

    def __init__(self, client: "GuruFocusClient") -> None:
        """Initialize the insiders endpoint.

        Args:
            client: The parent GuruFocusClient instance
        """
        self._client = client

    async def get_updates(
        self,
        page: int = 1,
        date: str | None = None,
        region: str | None = None,
        file_date: str | None = None,
        sort: str | None = None,
        order: str | None = None,
        bypass_cache: bool = False,
    ) -> InsiderUpdatesResponse:
        """Get recent insider transaction updates.

        Retrieves paginated list of recent insider transactions
        filed with the SEC.

        Args:
            page: Page number (default 1)
            date: Filter by transaction date (YYYYMMDD)
            region: Filter by region
            file_date: Filter by SEC filing date (YYYYMMDD)
            sort: Sort field
            order: Sort order ('asc' or 'desc')
            bypass_cache: If True, skip cache and fetch fresh data

        Returns:
            InsiderUpdatesResponse with list of insider updates

        Example:
            updates = await client.insiders.get_updates()
            for update in updates.updates[:5]:
                print(f"{update.symbol}: {update.insider} {update.type}")
        """
        data = await self.get_updates_raw(
            page=page,
            date=date,
            region=region,
            file_date=file_date,
            sort=sort,
            order=order,
            bypass_cache=bypass_cache,
        )
        return InsiderUpdatesResponse.from_api_response(data)

    async def get_updates_raw(
        self,
        page: int = 1,
        date: str | None = None,
        region: str | None = None,
        file_date: str | None = None,
        sort: str | None = None,
        order: str | None = None,
        bypass_cache: bool = False,
    ) -> list[dict[str, Any]]:
        """Get raw insider updates data.

        Same as get_updates() but returns the raw API response.

        Args:
            page: Page number (default 1)
            date: Filter by transaction date (YYYYMMDD)
            region: Filter by region
            file_date: Filter by SEC filing date (YYYYMMDD)
            sort: Sort field
            order: Sort order ('asc' or 'desc')
            bypass_cache: If True, skip cache and fetch fresh data

        Returns:
            Raw JSON response as a list of dictionaries
        """
        cache = self._client.cache
        cache_key = (
            f"{page}:{date or ''}:{region or ''}:{file_date or ''}:{sort or ''}:{order or ''}"
        )

        # Try cache first
        if not bypass_cache:
            cached_data = await cache.get(CacheCategory.INSIDER_UPDATES, cache_key)
            if cached_data is not None:
                return cast(list[dict[str, Any]], cached_data)

        # Build params
        params: dict[str, str | int] = {"page": page}
        if date:
            params["date"] = date
        if region:
            params["region"] = region
        if file_date:
            params["file_date"] = file_date
        if sort:
            params["sort"] = sort
        if order:
            params["order"] = order

        # Fetch from API
        data = await self._client.get("insider_updates", params=params)

        # Cache the response
        await cache.set(CacheCategory.INSIDER_UPDATES, cache_key, value=data)

        return cast(list[dict[str, Any]], data)

    async def get_ceo_buys(
        self,
        page: int = 1,
        within_days: int | None = None,
        bypass_cache: bool = False,
    ) -> InsiderBuysResponse:
        """Get CEO buy transactions.

        Retrieves paginated list of stocks where the CEO has
        been buying shares - a bullish signal.

        Args:
            page: Page number (default 1)
            within_days: Filter to transactions within N days
            bypass_cache: If True, skip cache and fetch fresh data

        Returns:
            InsiderBuysResponse with CEO buy transactions

        Example:
            ceo_buys = await client.insiders.get_ceo_buys()
            for buy in ceo_buys.data[:5]:
                print(f"{buy.symbol}: {buy.name} bought {buy.trans_share} shares")
        """
        data = await self.get_ceo_buys_raw(
            page=page, within_days=within_days, bypass_cache=bypass_cache
        )
        return InsiderBuysResponse.from_api_response(data)

    async def get_ceo_buys_raw(
        self,
        page: int = 1,
        within_days: int | None = None,
        bypass_cache: bool = False,
    ) -> dict[str, Any]:
        """Get raw CEO buy transactions data.

        Same as get_ceo_buys() but returns the raw API response.

        Args:
            page: Page number (default 1)
            within_days: Filter to transactions within N days
            bypass_cache: If True, skip cache and fetch fresh data

        Returns:
            Raw JSON response as a dictionary
        """
        cache = self._client.cache
        cache_key = f"{page}:{within_days or ''}"

        if not bypass_cache:
            cached_data = await cache.get(CacheCategory.INSIDER_CEO_BUYS, cache_key)
            if cached_data is not None:
                return cast(dict[str, Any], cached_data)

        params: dict[str, str | int] = {"page": page}
        if within_days:
            params["within_days"] = within_days

        data = await self._client.get("insider_buys/insider_ceo", params=params)

        await cache.set(CacheCategory.INSIDER_CEO_BUYS, cache_key, value=data)

        return cast(dict[str, Any], data)

    async def get_cfo_buys(
        self,
        page: int = 1,
        within_days: int | None = None,
        bypass_cache: bool = False,
    ) -> InsiderBuysResponse:
        """Get CFO buy transactions.

        Retrieves paginated list of stocks where the CFO has
        been buying shares - a bullish signal.

        Args:
            page: Page number (default 1)
            within_days: Filter to transactions within N days
            bypass_cache: If True, skip cache and fetch fresh data

        Returns:
            InsiderBuysResponse with CFO buy transactions

        Example:
            cfo_buys = await client.insiders.get_cfo_buys()
            for buy in cfo_buys.data[:5]:
                print(f"{buy.symbol}: {buy.name} bought {buy.trans_share} shares")
        """
        data = await self.get_cfo_buys_raw(
            page=page, within_days=within_days, bypass_cache=bypass_cache
        )
        return InsiderBuysResponse.from_api_response(data)

    async def get_cfo_buys_raw(
        self,
        page: int = 1,
        within_days: int | None = None,
        bypass_cache: bool = False,
    ) -> dict[str, Any]:
        """Get raw CFO buy transactions data.

        Same as get_cfo_buys() but returns the raw API response.

        Args:
            page: Page number (default 1)
            within_days: Filter to transactions within N days
            bypass_cache: If True, skip cache and fetch fresh data

        Returns:
            Raw JSON response as a dictionary
        """
        cache = self._client.cache
        cache_key = f"{page}:{within_days or ''}"

        if not bypass_cache:
            cached_data = await cache.get(CacheCategory.INSIDER_CFO_BUYS, cache_key)
            if cached_data is not None:
                return cast(dict[str, Any], cached_data)

        params: dict[str, str | int] = {"page": page}
        if within_days:
            params["within_days"] = within_days

        data = await self._client.get("insider_buys/insider_cfo", params=params)

        await cache.set(CacheCategory.INSIDER_CFO_BUYS, cache_key, value=data)

        return cast(dict[str, Any], data)

    async def get_cluster_buys(
        self,
        page: int = 1,
        within_days: int | None = None,
        bypass_cache: bool = False,
    ) -> ClusterBuyResponse:
        """Get cluster buy signals.

        Retrieves stocks where multiple insiders are buying shares
        simultaneously - a strong bullish signal.

        Args:
            page: Page number (default 1)
            within_days: Filter to transactions within N days
            bypass_cache: If True, skip cache and fetch fresh data

        Returns:
            ClusterBuyResponse with cluster buy signals

        Example:
            cluster = await client.insiders.get_cluster_buys()
            for signal in cluster.data[:5]:
                print(f"{signal.symbol}: {signal.insider_buy_count_unique} insiders buying")
        """
        data = await self.get_cluster_buys_raw(
            page=page, within_days=within_days, bypass_cache=bypass_cache
        )
        return ClusterBuyResponse.from_api_response(data)

    async def get_cluster_buys_raw(
        self,
        page: int = 1,
        within_days: int | None = None,
        bypass_cache: bool = False,
    ) -> dict[str, Any]:
        """Get raw cluster buy signals data.

        Same as get_cluster_buys() but returns the raw API response.

        Args:
            page: Page number (default 1)
            within_days: Filter to transactions within N days
            bypass_cache: If True, skip cache and fetch fresh data

        Returns:
            Raw JSON response as a dictionary
        """
        cache = self._client.cache
        cache_key = f"{page}:{within_days or ''}"

        if not bypass_cache:
            cached_data = await cache.get(CacheCategory.INSIDER_CLUSTER_BUY, cache_key)
            if cached_data is not None:
                return cast(dict[str, Any], cached_data)

        params: dict[str, str | int] = {"page": page}
        if within_days:
            params["within_days"] = within_days

        data = await self._client.get("insider_buys/insider_cluster_buy", params=params)

        await cache.set(CacheCategory.INSIDER_CLUSTER_BUY, cache_key, value=data)

        return cast(dict[str, Any], data)

    async def get_double_buys(
        self,
        page: int = 1,
        within_days: int | None = None,
        bypass_cache: bool = False,
    ) -> DoubleBuyResponse:
        """Get double-down buy signals.

        Retrieves stocks where insiders are doubling down on their
        positions by making additional purchases.

        Args:
            page: Page number (default 1)
            within_days: Filter to transactions within N days
            bypass_cache: If True, skip cache and fetch fresh data

        Returns:
            DoubleBuyResponse with double-down buy signals

        Example:
            double = await client.insiders.get_double_buys()
            for signal in double.data[:5]:
                print(f"{signal.symbol}: {signal.buy_add_count} additional buys")
        """
        data = await self.get_double_buys_raw(
            page=page, within_days=within_days, bypass_cache=bypass_cache
        )
        return DoubleBuyResponse.from_api_response(data)

    async def get_double_buys_raw(
        self,
        page: int = 1,
        within_days: int | None = None,
        bypass_cache: bool = False,
    ) -> dict[str, Any]:
        """Get raw double-down buy signals data.

        Same as get_double_buys() but returns the raw API response.

        Args:
            page: Page number (default 1)
            within_days: Filter to transactions within N days
            bypass_cache: If True, skip cache and fetch fresh data

        Returns:
            Raw JSON response as a dictionary
        """
        cache = self._client.cache
        cache_key = f"{page}:{within_days or ''}"

        if not bypass_cache:
            cached_data = await cache.get(CacheCategory.INSIDER_DOUBLE, cache_key)
            if cached_data is not None:
                return cast(dict[str, Any], cached_data)

        params: dict[str, str | int] = {"page": page}
        if within_days:
            params["within_days"] = within_days

        data = await self._client.get("insider_buys/insider_double", params=params)

        await cache.set(CacheCategory.INSIDER_DOUBLE, cache_key, value=data)

        return cast(dict[str, Any], data)

    async def get_triple_buys(
        self,
        page: int = 1,
        within_days: int | None = None,
        bypass_cache: bool = False,
    ) -> TripleBuyResponse:
        """Get triple-down buy signals.

        Retrieves stocks where insiders are tripling down on their
        positions with multiple additional purchases.

        Args:
            page: Page number (default 1)
            within_days: Filter to transactions within N days
            bypass_cache: If True, skip cache and fetch fresh data

        Returns:
            TripleBuyResponse with triple-down buy signals

        Example:
            triple = await client.insiders.get_triple_buys()
            for signal in triple.data[:5]:
                print(f"{signal.symbol}: {signal.buy_add_count} additional buys")
        """
        data = await self.get_triple_buys_raw(
            page=page, within_days=within_days, bypass_cache=bypass_cache
        )
        return TripleBuyResponse.from_api_response(data)

    async def get_triple_buys_raw(
        self,
        page: int = 1,
        within_days: int | None = None,
        bypass_cache: bool = False,
    ) -> dict[str, Any]:
        """Get raw triple-down buy signals data.

        Same as get_triple_buys() but returns the raw API response.

        Args:
            page: Page number (default 1)
            within_days: Filter to transactions within N days
            bypass_cache: If True, skip cache and fetch fresh data

        Returns:
            Raw JSON response as a dictionary
        """
        cache = self._client.cache
        cache_key = f"{page}:{within_days or ''}"

        if not bypass_cache:
            cached_data = await cache.get(CacheCategory.INSIDER_TRIPLE, cache_key)
            if cached_data is not None:
                return cast(dict[str, Any], cached_data)

        params: dict[str, str | int] = {"page": page}
        if within_days:
            params["within_days"] = within_days

        data = await self._client.get("insider_buys/insider_triple", params=params)

        await cache.set(CacheCategory.INSIDER_TRIPLE, cache_key, value=data)

        return cast(dict[str, Any], data)

    async def get_list(
        self,
        page: int = 1,
        bypass_cache: bool = False,
    ) -> InsiderListResponse:
        """Get list of insiders.

        Retrieves paginated list of known insiders with their
        associated companies and transaction dates.

        Args:
            page: Page number (default 1)
            bypass_cache: If True, skip cache and fetch fresh data

        Returns:
            InsiderListResponse with list of insiders

        Example:
            insiders = await client.insiders.get_list()
            for insider in insiders.data[:5]:
                print(f"{insider.name}: {len(insider.companies)} companies")
        """
        data = await self.get_list_raw(page=page, bypass_cache=bypass_cache)
        return InsiderListResponse.from_api_response(data)

    async def get_list_raw(
        self,
        page: int = 1,
        bypass_cache: bool = False,
    ) -> dict[str, Any]:
        """Get raw insider list data.

        Same as get_list() but returns the raw API response.

        Args:
            page: Page number (default 1)
            bypass_cache: If True, skip cache and fetch fresh data

        Returns:
            Raw JSON response as a dictionary
        """
        cache = self._client.cache
        cache_key = str(page)

        if not bypass_cache:
            cached_data = await cache.get(CacheCategory.INSIDER_LIST, cache_key)
            if cached_data is not None:
                return cast(dict[str, Any], cached_data)

        params: dict[str, int] = {"page": page}

        data = await self._client.get("insider_list", params=params)

        await cache.set(CacheCategory.INSIDER_LIST, cache_key, value=data)

        return cast(dict[str, Any], data)

    # -------------------------------------------------------------------------
    # Async Iterator Methods - Iterate through all pages automatically
    # -------------------------------------------------------------------------

    async def iter_updates(
        self,
        date: str | None = None,
        region: str | None = None,
        file_date: str | None = None,
        sort: str | None = None,
        order: str | None = None,
        max_pages: int | None = None,
        bypass_cache: bool = False,
    ) -> AsyncIterator[InsiderUpdate]:
        """Iterate through all insider updates across all pages.

        Automatically paginates through results, yielding individual
        InsiderUpdate objects.

        Args:
            date: Filter by transaction date (YYYYMMDD)
            region: Filter by region
            file_date: Filter by SEC filing date (YYYYMMDD)
            sort: Sort field
            order: Sort order ('asc' or 'desc')
            max_pages: Maximum number of pages to fetch (None = all)
            bypass_cache: If True, skip cache and fetch fresh data

        Yields:
            InsiderUpdate objects one at a time

        Example:
            async for update in client.insiders.iter_updates():
                print(f"{update.symbol}: {update.insider} {update.type}")
        """
        page = 1
        while True:
            response = await self.get_updates(
                page=page,
                date=date,
                region=region,
                file_date=file_date,
                sort=sort,
                order=order,
                bypass_cache=bypass_cache,
            )
            for item in response.updates:
                yield item

            # Check if we've reached the end or max_pages limit
            # Note: insider_updates returns a list, not paginated response
            # So we need to check if we got any results
            if len(response.updates) == 0:
                break
            if max_pages is not None and page >= max_pages:
                break
            page += 1

    async def iter_ceo_buys(
        self,
        within_days: int | None = None,
        max_pages: int | None = None,
        bypass_cache: bool = False,
    ) -> AsyncIterator[InsiderBuyTransaction]:
        """Iterate through all CEO buy transactions across all pages.

        Automatically paginates through results, yielding individual
        InsiderBuyTransaction objects.

        Args:
            within_days: Filter to transactions within N days
            max_pages: Maximum number of pages to fetch (None = all)
            bypass_cache: If True, skip cache and fetch fresh data

        Yields:
            InsiderBuyTransaction objects one at a time

        Example:
            async for buy in client.insiders.iter_ceo_buys(within_days=30):
                print(f"{buy.symbol}: {buy.name} bought {buy.trans_share} shares")
        """
        page = 1
        while True:
            response = await self.get_ceo_buys(
                page=page, within_days=within_days, bypass_cache=bypass_cache
            )
            for item in response.data:
                yield item

            if page >= response.last_page:
                break
            if max_pages is not None and page >= max_pages:
                break
            page += 1

    async def iter_cfo_buys(
        self,
        within_days: int | None = None,
        max_pages: int | None = None,
        bypass_cache: bool = False,
    ) -> AsyncIterator[InsiderBuyTransaction]:
        """Iterate through all CFO buy transactions across all pages.

        Automatically paginates through results, yielding individual
        InsiderBuyTransaction objects.

        Args:
            within_days: Filter to transactions within N days
            max_pages: Maximum number of pages to fetch (None = all)
            bypass_cache: If True, skip cache and fetch fresh data

        Yields:
            InsiderBuyTransaction objects one at a time

        Example:
            async for buy in client.insiders.iter_cfo_buys():
                print(f"{buy.symbol}: {buy.name} bought {buy.trans_share} shares")
        """
        page = 1
        while True:
            response = await self.get_cfo_buys(
                page=page, within_days=within_days, bypass_cache=bypass_cache
            )
            for item in response.data:
                yield item

            if page >= response.last_page:
                break
            if max_pages is not None and page >= max_pages:
                break
            page += 1

    async def iter_cluster_buys(
        self,
        within_days: int | None = None,
        max_pages: int | None = None,
        bypass_cache: bool = False,
    ) -> AsyncIterator[ClusterBuySignal]:
        """Iterate through all cluster buy signals across all pages.

        Automatically paginates through results, yielding individual
        ClusterBuySignal objects.

        Args:
            within_days: Filter to transactions within N days
            max_pages: Maximum number of pages to fetch (None = all)
            bypass_cache: If True, skip cache and fetch fresh data

        Yields:
            ClusterBuySignal objects one at a time

        Example:
            async for signal in client.insiders.iter_cluster_buys():
                print(f"{signal.symbol}: {signal.insider_buy_count_unique} insiders")
        """
        page = 1
        while True:
            response = await self.get_cluster_buys(
                page=page, within_days=within_days, bypass_cache=bypass_cache
            )
            for item in response.data:
                yield item

            if page >= response.last_page:
                break
            if max_pages is not None and page >= max_pages:
                break
            page += 1

    async def iter_double_buys(
        self,
        within_days: int | None = None,
        max_pages: int | None = None,
        bypass_cache: bool = False,
    ) -> AsyncIterator[DoubleBuySignal]:
        """Iterate through all double-down buy signals across all pages.

        Automatically paginates through results, yielding individual
        DoubleBuySignal objects.

        Args:
            within_days: Filter to transactions within N days
            max_pages: Maximum number of pages to fetch (None = all)
            bypass_cache: If True, skip cache and fetch fresh data

        Yields:
            DoubleBuySignal objects one at a time

        Example:
            async for signal in client.insiders.iter_double_buys():
                print(f"{signal.symbol}: {signal.buy_add_count} additional buys")
        """
        page = 1
        while True:
            response = await self.get_double_buys(
                page=page, within_days=within_days, bypass_cache=bypass_cache
            )
            for item in response.data:
                yield item

            if page >= response.last_page:
                break
            if max_pages is not None and page >= max_pages:
                break
            page += 1

    async def iter_triple_buys(
        self,
        within_days: int | None = None,
        max_pages: int | None = None,
        bypass_cache: bool = False,
    ) -> AsyncIterator[TripleBuySignal]:
        """Iterate through all triple-down buy signals across all pages.

        Automatically paginates through results, yielding individual
        TripleBuySignal objects.

        Args:
            within_days: Filter to transactions within N days
            max_pages: Maximum number of pages to fetch (None = all)
            bypass_cache: If True, skip cache and fetch fresh data

        Yields:
            TripleBuySignal objects one at a time

        Example:
            async for signal in client.insiders.iter_triple_buys():
                print(f"{signal.symbol}: {signal.buy_add_count} additional buys")
        """
        page = 1
        while True:
            response = await self.get_triple_buys(
                page=page, within_days=within_days, bypass_cache=bypass_cache
            )
            for item in response.data:
                yield item

            if page >= response.last_page:
                break
            if max_pages is not None and page >= max_pages:
                break
            page += 1

    async def iter_list(
        self,
        max_pages: int | None = None,
        bypass_cache: bool = False,
    ) -> AsyncIterator[InsiderInfo]:
        """Iterate through all insiders across all pages.

        Automatically paginates through results, yielding individual
        InsiderInfo objects.

        Args:
            max_pages: Maximum number of pages to fetch (None = all)
            bypass_cache: If True, skip cache and fetch fresh data

        Yields:
            InsiderInfo objects one at a time

        Example:
            async for insider in client.insiders.iter_list():
                print(f"{insider.name}: {len(insider.companies)} companies")
        """
        page = 1
        while True:
            response = await self.get_list(page=page, bypass_cache=bypass_cache)
            for item in response.data:
                yield item

            if page >= response.last_page:
                break
            if max_pages is not None and page >= max_pages:
                break
            page += 1
