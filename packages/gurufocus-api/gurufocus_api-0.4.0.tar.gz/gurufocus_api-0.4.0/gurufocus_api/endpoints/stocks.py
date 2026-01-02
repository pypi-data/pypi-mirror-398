"""Stock-related API endpoints."""

from typing import TYPE_CHECKING, Any, Literal, cast

from ..cache.config import CacheCategory
from ..models.dividends import CurrentDividend, DividendHistory
from ..models.estimates import AnalystEstimates
from ..models.executives import ExecutiveList
from ..models.financials import FinancialStatements
from ..models.gurus import StockGurusResponse
from ..models.insiders import InsiderTrades
from ..models.keyratios import KeyRatios
from ..models.ohlc import OHLCHistory, UnadjustedPriceHistory, VolumeHistory
from ..models.price import PriceHistory
from ..models.quote import StockQuote
from ..models.summary import StockSummary
from ..models.trades_history import GuruTradesHistory

if TYPE_CHECKING:
    from ..client import GuruFocusClient


class StocksEndpoint:
    """Endpoints for stock data retrieval.

    This class provides methods for fetching stock information
    from the GuruFocus API with automatic caching support.

    Example:
        async with GuruFocusClient() as client:
            summary = await client.stocks.get_summary("AAPL")
            print(f"{summary.company_name}: {summary.gf_score.gf_score}")

            # Force fresh data (bypass cache)
            fresh = await client.stocks.get_summary("AAPL", bypass_cache=True)
    """

    def __init__(self, client: "GuruFocusClient") -> None:
        """Initialize the stocks endpoint.

        Args:
            client: The parent GuruFocusClient instance
        """
        self._client = client

    async def get_summary(
        self,
        symbol: str,
        bypass_cache: bool = False,
    ) -> StockSummary:
        """Get comprehensive summary for a stock.

        Retrieves general information, current price, valuation metrics,
        and quality scores for the specified stock.

        Args:
            symbol: Stock ticker symbol (e.g., "AAPL", "MSFT")
            bypass_cache: If True, skip cache and fetch fresh data

        Returns:
            StockSummary with company info, price, valuation, and GF scores

        Raises:
            InvalidSymbolError: If the symbol is not found
            AuthenticationError: If the API token is invalid
            APIError: For other API errors

        Example:
            summary = await client.stocks.get_summary("AAPL")
            print(f"Company: {summary.company_name}")
            print(f"Price: ${summary.price.current}")
            print(f"GF Score: {summary.gf_score.gf_score}/100")
        """
        data = await self.get_summary_raw(symbol, bypass_cache=bypass_cache)
        return StockSummary.from_api_response(data, symbol.upper().strip())

    async def get_summary_raw(
        self,
        symbol: str,
        bypass_cache: bool = False,
    ) -> dict[str, Any]:
        """Get raw summary data for a stock.

        Same as get_summary() but returns the raw API response
        without parsing into a Pydantic model.

        Args:
            symbol: Stock ticker symbol
            bypass_cache: If True, skip cache and fetch fresh data

        Returns:
            Raw JSON response as a dictionary
        """
        symbol = symbol.upper().strip()
        cache = self._client.cache

        # Try to get from cache first
        if not bypass_cache:
            cached_data = await cache.get(CacheCategory.SUMMARY, symbol)
            if cached_data is not None:
                return cast(dict[str, Any], cached_data)

        # Fetch from API
        data = await self._client.get(f"stock/{symbol}/summary")

        # Cache the response
        await cache.set(CacheCategory.SUMMARY, symbol, value=data)

        return cast(dict[str, Any], data)

    async def get_quote(
        self,
        symbol: str,
        bypass_cache: bool = False,
    ) -> StockQuote:
        """Get real-time quote data for a stock.

        Retrieves current price, daily OHLV data, and price changes.
        This is a lightweight alternative to get_summary() when you
        only need current market data.

        Args:
            symbol: Stock ticker symbol (e.g., "AAPL", "MSFT")
            bypass_cache: If True, skip cache and fetch fresh data

        Returns:
            StockQuote with current price, OHLV, and change data

        Raises:
            InvalidSymbolError: If the symbol is not found
            AuthenticationError: If the API token is invalid
            APIError: For other API errors

        Example:
            quote = await client.stocks.get_quote("AAPL")
            print(f"Price: ${quote.current_price}")
            print(f"Change: {quote.price_change_pct}%")
            print(f"Volume: {quote.volume:,}")
        """
        data = await self.get_quote_raw(symbol, bypass_cache=bypass_cache)
        return StockQuote.from_api_response(data, symbol.upper().strip())

    async def get_quote_raw(
        self,
        symbol: str,
        bypass_cache: bool = False,
    ) -> dict[str, Any]:
        """Get raw quote data for a stock.

        Same as get_quote() but returns the raw API response
        without parsing into a Pydantic model.

        Args:
            symbol: Stock ticker symbol
            bypass_cache: If True, skip cache and fetch fresh data

        Returns:
            Raw JSON response as a dictionary
        """
        symbol = symbol.upper().strip()
        cache = self._client.cache

        # Try to get from cache first
        if not bypass_cache:
            cached_data = await cache.get(CacheCategory.QUOTE, symbol)
            if cached_data is not None:
                return cast(dict[str, Any], cached_data)

        # Fetch from API
        data = await self._client.get(f"stock/{symbol}/quote")

        # Cache the response
        await cache.set(CacheCategory.QUOTE, symbol, value=data)

        return cast(dict[str, Any], data)

    async def get_keyratios(
        self,
        symbol: str,
        bypass_cache: bool = False,
    ) -> KeyRatios:
        """Get key financial ratios for a stock.

        Retrieves comprehensive financial ratios including profitability,
        liquidity, solvency, efficiency, and growth metrics.

        Args:
            symbol: Stock ticker symbol (e.g., "AAPL", "MSFT")
            bypass_cache: If True, skip cache and fetch fresh data

        Returns:
            KeyRatios with categorized financial ratios

        Raises:
            InvalidSymbolError: If the symbol is not found
            AuthenticationError: If the API token is invalid
            APIError: For other API errors

        Example:
            ratios = await client.stocks.get_keyratios("AAPL")
            print(f"ROE: {ratios.profitability.roe}%")
            print(f"Current Ratio: {ratios.liquidity.current_ratio}")
            print(f"Debt/Equity: {ratios.solvency.debt_to_equity}")
        """
        data = await self.get_keyratios_raw(symbol, bypass_cache=bypass_cache)
        return KeyRatios.from_api_response(data, symbol.upper().strip())

    async def get_keyratios_raw(
        self,
        symbol: str,
        bypass_cache: bool = False,
    ) -> dict[str, Any]:
        """Get raw key ratios data for a stock.

        Same as get_keyratios() but returns the raw API response
        without parsing into a Pydantic model.

        Args:
            symbol: Stock ticker symbol
            bypass_cache: If True, skip cache and fetch fresh data

        Returns:
            Raw JSON response as a dictionary
        """
        symbol = symbol.upper().strip()
        cache = self._client.cache

        # Try to get from cache first
        if not bypass_cache:
            cached_data = await cache.get(CacheCategory.KEY_RATIOS, symbol)
            if cached_data is not None:
                return cast(dict[str, Any], cached_data)

        # Fetch from API
        data = await self._client.get(f"stock/{symbol}/keyratios")

        # Cache the response
        await cache.set(CacheCategory.KEY_RATIOS, symbol, value=data)

        return cast(dict[str, Any], data)

    async def get_financials(
        self,
        symbol: str,
        period_type: Literal["annual", "quarterly"] = "annual",
        bypass_cache: bool = False,
    ) -> FinancialStatements:
        """Get financial statements for a stock.

        Retrieves income statement, balance sheet, and cash flow statement
        data for multiple historical periods.

        Args:
            symbol: Stock ticker symbol (e.g., "AAPL", "MSFT")
            period_type: 'annual' for yearly data, 'quarterly' for quarterly
            bypass_cache: If True, skip cache and fetch fresh data

        Returns:
            FinancialStatements with income, balance, and cash flow data

        Raises:
            InvalidSymbolError: If the symbol is not found
            AuthenticationError: If the API token is invalid
            APIError: For other API errors

        Example:
            financials = await client.stocks.get_financials("AAPL")
            latest_income = financials.income_statements[0]
            print(f"Revenue: ${latest_income.revenue:,.0f}")
            print(f"Net Income: ${latest_income.net_income:,.0f}")

            # Get quarterly data
            quarterly = await client.stocks.get_financials("AAPL", period_type="quarterly")
        """
        data = await self.get_financials_raw(
            symbol, period_type=period_type, bypass_cache=bypass_cache
        )
        return FinancialStatements.from_api_response(data, symbol.upper().strip(), period_type)

    async def get_financials_raw(
        self,
        symbol: str,
        period_type: Literal["annual", "quarterly"] = "annual",
        bypass_cache: bool = False,
    ) -> dict[str, Any]:
        """Get raw financial statements data for a stock.

        Same as get_financials() but returns the raw API response
        without parsing into a Pydantic model.

        Args:
            symbol: Stock ticker symbol
            period_type: 'annual' for yearly data, 'quarterly' for quarterly
            bypass_cache: If True, skip cache and fetch fresh data

        Returns:
            Raw JSON response as a dictionary
        """
        symbol = symbol.upper().strip()
        cache = self._client.cache
        cache_key_suffix = f"{symbol}:{period_type}"

        # Try to get from cache first
        if not bypass_cache:
            cached_data = await cache.get(CacheCategory.FINANCIALS, cache_key_suffix)
            if cached_data is not None:
                return cast(dict[str, Any], cached_data)

        # Build API endpoint
        endpoint = f"stock/{symbol}/financials"
        params = {"type": period_type} if period_type == "quarterly" else None

        # Fetch from API
        data = await self._client.get(endpoint, params=params)

        # Cache the response
        await cache.set(CacheCategory.FINANCIALS, cache_key_suffix, value=data)

        return cast(dict[str, Any], data)

    async def get_analyst_estimates(
        self,
        symbol: str,
        bypass_cache: bool = False,
    ) -> AnalystEstimates:
        """Get analyst estimates and ratings for a stock.

        Retrieves analyst EPS/revenue estimates for upcoming periods
        and recommendation ratings.

        Args:
            symbol: Stock ticker symbol (e.g., "AAPL", "MSFT")
            bypass_cache: If True, skip cache and fetch fresh data

        Returns:
            AnalystEstimates with ratings and forward estimates

        Raises:
            InvalidSymbolError: If the symbol is not found
            AuthenticationError: If the API token is invalid
            APIError: For other API errors

        Example:
            estimates = await client.stocks.get_analyst_estimates("AAPL")
            print(f"Rating: {estimates.ratings.rating}")
            print(f"Target Price: ${estimates.ratings.target_price}")
            for est in estimates.annual_estimates:
                print(f"{est.period}: EPS ${est.eps_estimate}")
        """
        data = await self.get_analyst_estimates_raw(symbol, bypass_cache=bypass_cache)
        return AnalystEstimates.from_api_response(data, symbol.upper().strip())

    async def get_analyst_estimates_raw(
        self,
        symbol: str,
        bypass_cache: bool = False,
    ) -> dict[str, Any]:
        """Get raw analyst estimates data for a stock.

        Same as get_analyst_estimates() but returns the raw API response
        without parsing into a Pydantic model.

        Args:
            symbol: Stock ticker symbol
            bypass_cache: If True, skip cache and fetch fresh data

        Returns:
            Raw JSON response as a dictionary
        """
        symbol = symbol.upper().strip()
        cache = self._client.cache

        # Try to get from cache first
        if not bypass_cache:
            cached_data = await cache.get(CacheCategory.ESTIMATES, symbol)
            if cached_data is not None:
                return cast(dict[str, Any], cached_data)

        # Fetch from API
        data = await self._client.get(f"stock/{symbol}/analyst_estimate")

        # Cache the response
        await cache.set(CacheCategory.ESTIMATES, symbol, value=data)

        return cast(dict[str, Any], data)

    async def get_dividends(
        self,
        symbol: str,
        bypass_cache: bool = False,
    ) -> DividendHistory:
        """Get dividend history for a stock.

        Retrieves dividend payment history and summary metrics
        including yield, growth rates, and payout ratio.

        Args:
            symbol: Stock ticker symbol (e.g., "AAPL", "MSFT")
            bypass_cache: If True, skip cache and fetch fresh data

        Returns:
            DividendHistory with summary metrics and payment history

        Raises:
            InvalidSymbolError: If the symbol is not found
            AuthenticationError: If the API token is invalid
            APIError: For other API errors

        Example:
            dividends = await client.stocks.get_dividends("AAPL")
            print(f"Yield: {dividends.summary.dividend_yield}%")
            print(f"Years of Growth: {dividends.summary.years_of_growth}")
            for payment in dividends.payments[:5]:
                print(f"{payment.ex_date}: ${payment.amount}")
        """
        data = await self.get_dividends_raw(symbol, bypass_cache=bypass_cache)
        return DividendHistory.from_api_response(data, symbol.upper().strip())

    async def get_dividends_raw(
        self,
        symbol: str,
        bypass_cache: bool = False,
    ) -> dict[str, Any]:
        """Get raw dividend data for a stock.

        Same as get_dividends() but returns the raw API response
        without parsing into a Pydantic model.

        Args:
            symbol: Stock ticker symbol
            bypass_cache: If True, skip cache and fetch fresh data

        Returns:
            Raw JSON response as a dictionary
        """
        symbol = symbol.upper().strip()
        cache = self._client.cache

        # Try to get from cache first
        if not bypass_cache:
            cached_data = await cache.get(CacheCategory.DIVIDENDS, symbol)
            if cached_data is not None:
                return cast(dict[str, Any], cached_data)

        # Fetch from API
        data = await self._client.get(f"stock/{symbol}/dividend")

        # Cache the response
        await cache.set(CacheCategory.DIVIDENDS, symbol, value=data)

        return cast(dict[str, Any], data)

    async def get_current_dividend(
        self,
        symbol: str,
        bypass_cache: bool = False,
    ) -> CurrentDividend:
        """Get current dividend information for a stock.

        Retrieves current dividend yield, TTM dividend per share,
        payment schedule, and historical yield context.

        Args:
            symbol: Stock ticker symbol (e.g., "AAPL", "MSFT")
            bypass_cache: If True, skip cache and fetch fresh data

        Returns:
            CurrentDividend with yield, TTM dividend, and schedule info

        Raises:
            InvalidSymbolError: If the symbol is not found
            AuthenticationError: If the API token is invalid
            APIError: For other API errors

        Example:
            div = await client.stocks.get_current_dividend("AAPL")
            print(f"Yield: {div.dividend_yield}%")
            print(f"TTM Dividends: ${div.dividends_per_share_ttm}")
            print(f"Frequency: {div.frequency}")
        """
        data = await self.get_current_dividend_raw(symbol, bypass_cache=bypass_cache)
        return CurrentDividend.from_api_response(data, symbol.upper().strip())

    async def get_current_dividend_raw(
        self,
        symbol: str,
        bypass_cache: bool = False,
    ) -> dict[str, Any]:
        """Get raw current dividend data for a stock.

        Same as get_current_dividend() but returns the raw API response
        without parsing into a Pydantic model.

        Args:
            symbol: Stock ticker symbol
            bypass_cache: If True, skip cache and fetch fresh data

        Returns:
            Raw JSON response as a dictionary
        """
        symbol = symbol.upper().strip()
        cache = self._client.cache

        # Try to get from cache first
        if not bypass_cache:
            cached_data = await cache.get(CacheCategory.CURRENT_DIVIDEND, symbol)
            if cached_data is not None:
                return cast(dict[str, Any], cached_data)

        # Fetch from API
        data = await self._client.get(f"stock/{symbol}/current_dividend")

        # Cache the response
        await cache.set(CacheCategory.CURRENT_DIVIDEND, symbol, value=data)

        return cast(dict[str, Any], data)

    async def get_price_history(
        self,
        symbol: str,
        bypass_cache: bool = False,
    ) -> PriceHistory:
        """Get historical price data for a stock.

        Retrieves daily OHLCV price data and summary statistics
        including returns over various periods.

        Args:
            symbol: Stock ticker symbol (e.g., "AAPL", "MSFT")
            bypass_cache: If True, skip cache and fetch fresh data

        Returns:
            PriceHistory with statistics and daily price bars

        Raises:
            InvalidSymbolError: If the symbol is not found
            AuthenticationError: If the API token is invalid
            APIError: For other API errors

        Example:
            prices = await client.stocks.get_price_history("AAPL")
            print(f"Current: ${prices.statistics.current_price}")
            print(f"52-Week High: ${prices.statistics.high_52week}")
            print(f"YTD Return: {prices.statistics.change_ytd}%")
            for bar in prices.prices[:5]:
                print(f"{bar.date}: ${bar.close}")
        """
        data = await self.get_price_history_raw(symbol, bypass_cache=bypass_cache)
        return PriceHistory.from_api_response(data, symbol.upper().strip())

    async def get_price_history_raw(
        self,
        symbol: str,
        bypass_cache: bool = False,
    ) -> dict[str, Any]:
        """Get raw price history data for a stock.

        Same as get_price_history() but returns the raw API response
        without parsing into a Pydantic model.

        Args:
            symbol: Stock ticker symbol
            bypass_cache: If True, skip cache and fetch fresh data

        Returns:
            Raw JSON response as a dictionary
        """
        symbol = symbol.upper().strip()
        cache = self._client.cache

        # Try to get from cache first
        if not bypass_cache:
            cached_data = await cache.get(CacheCategory.PRICE_HISTORY, symbol)
            if cached_data is not None:
                return cast(dict[str, Any], cached_data)

        # Fetch from API
        data = await self._client.get(f"stock/{symbol}/price")

        # Cache the response
        await cache.set(CacheCategory.PRICE_HISTORY, symbol, value=data)

        return cast(dict[str, Any], data)

    async def get_insider_trades(
        self,
        symbol: str,
        bypass_cache: bool = False,
    ) -> InsiderTrades:
        """Get insider trading activity for a stock.

        Retrieves recent insider transactions including buys, sells,
        and option exercises by company insiders.

        Args:
            symbol: Stock ticker symbol (e.g., "AAPL", "MSFT")
            bypass_cache: If True, skip cache and fetch fresh data

        Returns:
            InsiderTrades with summary metrics and transaction history

        Raises:
            InvalidSymbolError: If the symbol is not found
            AuthenticationError: If the API token is invalid
            APIError: For other API errors

        Example:
            insiders = await client.stocks.get_insider_trades("AAPL")
            print(f"Net Shares (3M): {insiders.summary.net_shares_3m}")
            for trade in insiders.trades[:5]:
                print(f"{trade.trade_date}: {trade.insider_name} "
                      f"{trade.transaction_type} {trade.shares} shares")
        """
        data = await self.get_insider_trades_raw(symbol, bypass_cache=bypass_cache)
        return InsiderTrades.from_api_response(data, symbol.upper().strip())

    async def get_insider_trades_raw(
        self,
        symbol: str,
        bypass_cache: bool = False,
    ) -> dict[str, Any]:
        """Get raw insider trades data for a stock.

        Same as get_insider_trades() but returns the raw API response
        without parsing into a Pydantic model.

        Args:
            symbol: Stock ticker symbol
            bypass_cache: If True, skip cache and fetch fresh data

        Returns:
            Raw JSON response as a dictionary
        """
        symbol = symbol.upper().strip()
        cache = self._client.cache

        # Try to get from cache first
        if not bypass_cache:
            cached_data = await cache.get(CacheCategory.INSIDERS, symbol)
            if cached_data is not None:
                return cast(dict[str, Any], cached_data)

        # Fetch from API
        data = await self._client.get(f"stock/{symbol}/insider")

        # Cache the response
        await cache.set(CacheCategory.INSIDERS, symbol, value=data)

        return cast(dict[str, Any], data)

    async def get_gurus(
        self,
        symbol: str,
        bypass_cache: bool = False,
    ) -> StockGurusResponse:
        """Get guru holdings and trading activity for a stock.

        Retrieves institutional investor (guru) holdings and recent
        trading activity including buys, sells, and position changes.

        Args:
            symbol: Stock ticker symbol (e.g., "AAPL", "MSFT")
            bypass_cache: If True, skip cache and fetch fresh data

        Returns:
            StockGurusResponse with picks (trading activity) and holdings

        Raises:
            InvalidSymbolError: If the symbol is not found
            AuthenticationError: If the API token is invalid
            APIError: For other API errors

        Example:
            gurus = await client.stocks.get_gurus("AAPL")
            print(f"Number of guru holders: {len(gurus.holdings)}")
            for pick in gurus.picks[:5]:
                print(f"{pick.guru}: {pick.action} ({pick.comment})")
        """
        data = await self.get_gurus_raw(symbol, bypass_cache=bypass_cache)
        return StockGurusResponse.from_api_response(data, symbol.upper().strip())

    async def get_gurus_raw(
        self,
        symbol: str,
        bypass_cache: bool = False,
    ) -> dict[str, Any]:
        """Get raw guru holdings data for a stock.

        Same as get_gurus() but returns the raw API response
        without parsing into a Pydantic model.

        Args:
            symbol: Stock ticker symbol
            bypass_cache: If True, skip cache and fetch fresh data

        Returns:
            Raw JSON response as a dictionary
        """
        symbol = symbol.upper().strip()
        cache = self._client.cache

        # Try to get from cache first
        if not bypass_cache:
            cached_data = await cache.get(CacheCategory.GURUS, symbol)
            if cached_data is not None:
                return cast(dict[str, Any], cached_data)

        # Fetch from API
        data = await self._client.get(f"stock/{symbol}/gurus")

        # Cache the response
        await cache.set(CacheCategory.GURUS, symbol, value=data)

        return cast(dict[str, Any], data)

    async def get_executives(
        self,
        symbol: str,
        bypass_cache: bool = False,
    ) -> ExecutiveList:
        """Get company executives and directors for a stock.

        Retrieves a list of company officers and board directors
        with their positions and last transaction dates.

        Args:
            symbol: Stock ticker symbol (e.g., "AAPL", "MSFT")
            bypass_cache: If True, skip cache and fetch fresh data

        Returns:
            ExecutiveList with list of executives and directors

        Raises:
            InvalidSymbolError: If the symbol is not found
            AuthenticationError: If the API token is invalid
            APIError: For other API errors

        Example:
            execs = await client.stocks.get_executives("AAPL")
            print(f"Number of executives: {len(execs.executives)}")
            for exec in execs.executives[:5]:
                print(f"{exec.name}: {exec.position}")
        """
        data = await self.get_executives_raw(symbol, bypass_cache=bypass_cache)
        return ExecutiveList.from_api_response(data, symbol.upper().strip())

    async def get_executives_raw(
        self,
        symbol: str,
        bypass_cache: bool = False,
    ) -> list[dict[str, Any]]:
        """Get raw executives data for a stock.

        Same as get_executives() but returns the raw API response
        without parsing into a Pydantic model.

        Args:
            symbol: Stock ticker symbol
            bypass_cache: If True, skip cache and fetch fresh data

        Returns:
            Raw JSON response as a list of dictionaries
        """
        symbol = symbol.upper().strip()
        cache = self._client.cache

        # Try to get from cache first
        if not bypass_cache:
            cached_data = await cache.get(CacheCategory.EXECUTIVES, symbol)
            if cached_data is not None:
                return cast(list[dict[str, Any]], cached_data)

        # Fetch from API
        data = await self._client.get(f"stock/{symbol}/executives")

        # Cache the response
        await cache.set(CacheCategory.EXECUTIVES, symbol, value=data)

        return cast(list[dict[str, Any]], data)

    async def get_trades_history(
        self,
        symbol: str,
        bypass_cache: bool = False,
    ) -> GuruTradesHistory:
        """Get guru trades history for a stock.

        Retrieves historical guru trading activity organized by portfolio
        reporting periods, showing which institutional investors bought or
        sold shares and in what quantities.

        Args:
            symbol: Stock ticker symbol (e.g., "AAPL", "MSFT")
            bypass_cache: If True, skip cache and fetch fresh data

        Returns:
            GuruTradesHistory with trading activity by period

        Raises:
            InvalidSymbolError: If the symbol is not found
            AuthenticationError: If the API token is invalid
            APIError: For other API errors

        Example:
            trades = await client.stocks.get_trades_history("AAPL")
            for period in trades.periods[:3]:
                print(f"{period.portdate}: {period.buy_count} buys, {period.sell_count} sells")
                for buyer in period.buy_gurus:
                    print(f"  + {buyer.guru_name}: {buyer.share_change:,} shares")
        """
        data = await self.get_trades_history_raw(symbol, bypass_cache=bypass_cache)
        return GuruTradesHistory.from_api_response(data, symbol.upper().strip())

    async def get_trades_history_raw(
        self,
        symbol: str,
        bypass_cache: bool = False,
    ) -> list[dict[str, Any]]:
        """Get raw guru trades history data for a stock.

        Same as get_trades_history() but returns the raw API response
        without parsing into a Pydantic model.

        Args:
            symbol: Stock ticker symbol
            bypass_cache: If True, skip cache and fetch fresh data

        Returns:
            Raw JSON response as a list of dictionaries
        """
        symbol = symbol.upper().strip()
        cache = self._client.cache

        # Try to get from cache first
        if not bypass_cache:
            cached_data = await cache.get(CacheCategory.TRADES_HISTORY, symbol)
            if cached_data is not None:
                return cast(list[dict[str, Any]], cached_data)

        # Fetch from API
        data = await self._client.get(f"stock/{symbol}/trades/history")

        # Cache the response
        await cache.set(CacheCategory.TRADES_HISTORY, symbol, value=data)

        return cast(list[dict[str, Any]], data)

    async def get_price_ohlc(
        self,
        symbol: str,
        start_date: str | None = None,
        end_date: str | None = None,
        bypass_cache: bool = False,
    ) -> OHLCHistory:
        """Get OHLC price history for a stock.

        Retrieves daily Open-High-Low-Close price data with volume
        for the specified date range.

        Args:
            symbol: Stock ticker symbol (e.g., "AAPL", "MSFT")
            start_date: Start date in YYYYMMDD format (e.g., "20250101")
            end_date: End date in YYYYMMDD format (e.g., "20251231")
            bypass_cache: If True, skip cache and fetch fresh data

        Returns:
            OHLCHistory with daily OHLC bars and volume

        Raises:
            InvalidSymbolError: If the symbol is not found
            AuthenticationError: If the API token is invalid
            APIError: For other API errors

        Example:
            ohlc = await client.stocks.get_price_ohlc(
                "AAPL",
                start_date="20250101",
                end_date="20250131"
            )
            for bar in ohlc.bars[:5]:
                print(f"{bar.date}: O:{bar.open} H:{bar.high} L:{bar.low} C:{bar.close}")
        """
        data = await self.get_price_ohlc_raw(
            symbol, start_date=start_date, end_date=end_date, bypass_cache=bypass_cache
        )
        return OHLCHistory.from_api_response(data, symbol.upper().strip())

    async def get_price_ohlc_raw(
        self,
        symbol: str,
        start_date: str | None = None,
        end_date: str | None = None,
        bypass_cache: bool = False,
    ) -> list[dict[str, Any]]:
        """Get raw OHLC price history data for a stock.

        Same as get_price_ohlc() but returns the raw API response
        without parsing into a Pydantic model.

        Args:
            symbol: Stock ticker symbol
            start_date: Start date in YYYYMMDD format
            end_date: End date in YYYYMMDD format
            bypass_cache: If True, skip cache and fetch fresh data

        Returns:
            Raw JSON response as a list of dictionaries
        """
        symbol = symbol.upper().strip()
        cache = self._client.cache
        cache_key = f"{symbol}:{start_date or ''}:{end_date or ''}"

        # Try to get from cache first
        if not bypass_cache:
            cached_data = await cache.get(CacheCategory.PRICE_OHLC, cache_key)
            if cached_data is not None:
                return cast(list[dict[str, Any]], cached_data)

        # Build API endpoint with params
        params: dict[str, str] = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        # Fetch from API
        data = await self._client.get(
            f"stock/{symbol}/price_ohlc", params=params if params else None
        )

        # Cache the response
        await cache.set(CacheCategory.PRICE_OHLC, cache_key, value=data)

        return cast(list[dict[str, Any]], data)

    async def get_volume(
        self,
        symbol: str,
        start_date: str | None = None,
        end_date: str | None = None,
        bypass_cache: bool = False,
    ) -> VolumeHistory:
        """Get volume history for a stock.

        Retrieves daily trading volume data for the specified date range.

        Args:
            symbol: Stock ticker symbol (e.g., "AAPL", "MSFT")
            start_date: Start date in YYYYMMDD format (e.g., "20250101")
            end_date: End date in YYYYMMDD format (e.g., "20251231")
            bypass_cache: If True, skip cache and fetch fresh data

        Returns:
            VolumeHistory with daily volume data points

        Raises:
            InvalidSymbolError: If the symbol is not found
            AuthenticationError: If the API token is invalid
            APIError: For other API errors

        Example:
            volume = await client.stocks.get_volume(
                "AAPL",
                start_date="20250101",
                end_date="20250131"
            )
            for point in volume.data[:5]:
                print(f"{point.date}: {point.volume:,} shares")
        """
        data = await self.get_volume_raw(
            symbol, start_date=start_date, end_date=end_date, bypass_cache=bypass_cache
        )
        return VolumeHistory.from_api_response(data, symbol.upper().strip())

    async def get_volume_raw(
        self,
        symbol: str,
        start_date: str | None = None,
        end_date: str | None = None,
        bypass_cache: bool = False,
    ) -> list[list[Any]]:
        """Get raw volume history data for a stock.

        Same as get_volume() but returns the raw API response
        without parsing into a Pydantic model.

        Args:
            symbol: Stock ticker symbol
            start_date: Start date in YYYYMMDD format
            end_date: End date in YYYYMMDD format
            bypass_cache: If True, skip cache and fetch fresh data

        Returns:
            Raw JSON response as a list of [date, volume] arrays
        """
        symbol = symbol.upper().strip()
        cache = self._client.cache
        cache_key = f"{symbol}:{start_date or ''}:{end_date or ''}"

        # Try to get from cache first
        if not bypass_cache:
            cached_data = await cache.get(CacheCategory.VOLUME, cache_key)
            if cached_data is not None:
                return cast(list[list[Any]], cached_data)

        # Build API endpoint with params
        params: dict[str, str] = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        # Fetch from API
        data = await self._client.get(f"stock/{symbol}/volume", params=params if params else None)

        # Cache the response
        await cache.set(CacheCategory.VOLUME, cache_key, value=data)

        return cast(list[list[Any]], data)

    async def get_unadjusted_price(
        self,
        symbol: str,
        start_date: str | None = None,
        end_date: str | None = None,
        bypass_cache: bool = False,
    ) -> UnadjustedPriceHistory:
        """Get unadjusted price history for a stock.

        Retrieves daily unadjusted (pre-split) price data for the
        specified date range.

        Args:
            symbol: Stock ticker symbol (e.g., "AAPL", "MSFT")
            start_date: Start date in YYYYMMDD format (e.g., "20250101")
            end_date: End date in YYYYMMDD format (e.g., "20251231")
            bypass_cache: If True, skip cache and fetch fresh data

        Returns:
            UnadjustedPriceHistory with daily price points

        Raises:
            InvalidSymbolError: If the symbol is not found
            AuthenticationError: If the API token is invalid
            APIError: For other API errors

        Example:
            prices = await client.stocks.get_unadjusted_price(
                "AAPL",
                start_date="20250101",
                end_date="20250131"
            )
            for point in prices.prices[:5]:
                print(f"{point.date}: ${point.price}")
        """
        data = await self.get_unadjusted_price_raw(
            symbol, start_date=start_date, end_date=end_date, bypass_cache=bypass_cache
        )
        return UnadjustedPriceHistory.from_api_response(data, symbol.upper().strip())

    async def get_unadjusted_price_raw(
        self,
        symbol: str,
        start_date: str | None = None,
        end_date: str | None = None,
        bypass_cache: bool = False,
    ) -> list[list[Any]]:
        """Get raw unadjusted price history data for a stock.

        Same as get_unadjusted_price() but returns the raw API response
        without parsing into a Pydantic model.

        Args:
            symbol: Stock ticker symbol
            start_date: Start date in YYYYMMDD format
            end_date: End date in YYYYMMDD format
            bypass_cache: If True, skip cache and fetch fresh data

        Returns:
            Raw JSON response as a list of [date, price] arrays
        """
        symbol = symbol.upper().strip()
        cache = self._client.cache
        cache_key = f"{symbol}:{start_date or ''}:{end_date or ''}"

        # Try to get from cache first
        if not bypass_cache:
            cached_data = await cache.get(CacheCategory.UNADJUSTED_PRICE, cache_key)
            if cached_data is not None:
                return cast(list[list[Any]], cached_data)

        # Build API endpoint with params
        params: dict[str, str] = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        # Fetch from API
        data = await self._client.get(
            f"stock/{symbol}/unadjusted_price", params=params if params else None
        )

        # Cache the response
        await cache.set(CacheCategory.UNADJUSTED_PRICE, cache_key, value=data)

        return cast(list[list[Any]], data)
