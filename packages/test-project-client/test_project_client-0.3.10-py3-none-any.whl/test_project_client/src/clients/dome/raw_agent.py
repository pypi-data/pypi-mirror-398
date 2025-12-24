"""
Layer 0 Agent: Environment-based client wrapper for dome
Automatically loads credentials from environment variables for easy integration
with AI Agent frameworks (LangChain, CrewAI, Madison, etc.)
"""
import os
from typing import Any, Dict, List, Literal, Optional, Union
from .raw import *


class RawAgent:
    """
    Agent-ready wrapper for dome raw API client.

    Automatically loads credentials from environment variables:
    - DOME_API_KEY: API key/token for authentication
    - DOME_BASE_URL: Base URL for the API (optional, has default)

    Usage:
        agent = RawAgent()  # Uses env vars
        agent = RawAgent(api_key="...", base_url="...")  # Explicit
    """

    def __init__(
        self,
        api_key: str = None,
        base_url: str = None
    ):
        # Load from environment variables with fallbacks
        self.api_key = api_key or os.environ.get("DOME_API_KEY")
        self.base_url = base_url or os.environ.get("DOME_BASE_URL", "https://api.domeapi.io/v1")

        if not self.api_key:
            raise ValueError(
                "API key is required. Set DOME_API_KEY environment variable "
                "or pass api_key parameter."
            )

        # Initialize raw client(s)
        self._default = DefaultClient(
            base_url=self.base_url,
            token=self.api_key
        )

    # ─────────────────────────────────────────────────────────────────────────────
    # Default operations
    # ─────────────────────────────────────────────────────────────────────────────

    async def get_market_price(self, token_id: str, at_time: int = None) -> Dict[str, Any]:
        """Fetches the current market price for a market by `token_id`. When `at_time` is not provided, returns the most real-time price available. When `at_time` is provided, returns the historical market price at that specific timestamp.

**Example Request (with historical timestamp):**
```bash
curl 'https://api.domeapi.io/v1/polymarket/market-price/19701256321759583954581192053894521654935987478209343000964756587964612528044?at_time=1762164600'
```

**Example Request (real-time price):**
```bash
curl 'https://api.domeapi.io/v1/polymarket/market-price/19701256321759583954581192053894521654935987478209343000964756587964612528044'
```"""
        return await self._default.get_market_price(token_id=token_id, at_time=at_time)

    async def get_candlesticks(self, condition_id: str, start_time: int = None, end_time: int = None, interval: int = None) -> Dict[str, Any]:
        """Fetches historical candlestick data for a market identified by `condition_id`, over a specified interval."""
        return await self._default.get_candlesticks(condition_id=condition_id, start_time=start_time, end_time=end_time, interval=interval)

    async def get_wallet_pnl(self, wallet_address: str, granularity: Literal["day", "week", "month", "year", "all"] = None, start_time: int = None, end_time: int = None) -> Dict[str, Any]:
        """Fetches the REALIZED profit and loss (PnL) for a specific wallet address over a specified time range and granularity. **Note:** This will differ to what you see on Polymarket's dashboard since Polymarket showcases historical unrealized PnL. This API tracks realized gains only - from either confirmed sells or redeems. We do not realize a gain/loss until a finished market is redeemed."""
        return await self._default.get_wallet_pnl(wallet_address=wallet_address, granularity=granularity, start_time=start_time, end_time=end_time)

    async def get_wallet(self, eoa: str = None, proxy: str = None, with_metrics: Literal["true", "false"] = None, start_time: int = None, end_time: int = None) -> Dict[str, Any]:
        """Fetches wallet information by providing either an EOA (Externally Owned Account) address or a proxy wallet address. Returns the associated EOA, proxy, and wallet type information. Optionally returns trading metrics when `with_metrics=true`."""
        return await self._default.get_wallet(eoa=eoa, proxy=proxy, with_metrics=with_metrics, start_time=start_time, end_time=end_time)

    async def get_orders(self, market_slug: str = None, condition_id: str = None, token_id: str = None, start_time: int = None, end_time: int = None, limit: int = None, offset: int = None, user: str = None) -> Dict[str, Any]:
        """Fetches order data with optional filtering by market, condition, token, time range, and user. Returns orders that match either primary or secondary token IDs for markets. If no filters provided, fetches the latest trades happening in real-time. Only one of market_slug, token_id, or condition_id can be provided."""
        return await self._default.get_orders(market_slug=market_slug, condition_id=condition_id, token_id=token_id, start_time=start_time, end_time=end_time, limit=limit, offset=offset, user=user)

    async def get_orderbooks(self, token_id: str = None, start_time: int = None, end_time: int = None, limit: int = None, pagination_key: str = None) -> Dict[str, Any]:
        """Fetches historical orderbook snapshots for a specific asset (token ID) over a specified time range. Returns snapshots of the order book including bids, asks, and market metadata in order. All timestamps are in milliseconds. Orderbook data has history starting from October 14th, 2025."""
        return await self._default.get_orderbooks(token_id=token_id, start_time=start_time, end_time=end_time, limit=limit, pagination_key=pagination_key)

    async def get_markets(self, market_slug: List[str] = None, event_slug: List[str] = None, condition_id: List[str] = None, tags: List[str] = None, status: Literal["open", "closed"] = None, min_volume: float = None, limit: int = None, offset: int = None, start_time: int = None, end_time: int = None) -> Dict[str, Any]:
        """Fetches market data with optional filtering and search functionality. Supports filtering by market slug, condition ID, or tags, as well as fuzzy search across market titles and descriptions. Returns markets ordered by volume (most popular first) when filters are applied, or by start_time (most recent first) when no filters are provided."""
        return await self._default.get_markets(market_slug=market_slug, event_slug=event_slug, condition_id=condition_id, tags=tags, status=status, min_volume=min_volume, limit=limit, offset=offset, start_time=start_time, end_time=end_time)

    async def get_kalshi_markets(self, market_ticker: List[str] = None, event_ticker: List[str] = None, status: Literal["open", "closed"] = None, min_volume: float = None, limit: int = None, offset: int = None) -> Dict[str, Any]:
        """Fetches Kalshi market data with optional filtering by market ticker, event ticker, status, and volume. Returns markets with details including pricing, volume, and status information."""
        return await self._default.get_kalshi_markets(market_ticker=market_ticker, event_ticker=event_ticker, status=status, min_volume=min_volume, limit=limit, offset=offset)

    async def get_kalshi_trades(self, ticker: str = None, start_time: int = None, end_time: int = None, limit: int = None, offset: int = None) -> Dict[str, Any]:
        """Fetches historical trade data for Kalshi markets with optional filtering by ticker and time range. Returns executed trades with pricing, volume, and taker side information. All timestamps are in seconds."""
        return await self._default.get_kalshi_trades(ticker=ticker, start_time=start_time, end_time=end_time, limit=limit, offset=offset)

    async def get_kalshi_orderbooks(self, ticker: str = None, start_time: int = None, end_time: int = None, limit: int = None) -> Dict[str, Any]:
        """Fetches historical orderbook snapshots for a specific Kalshi market (ticker) over a specified time range. Returns snapshots of the order book including yes/no bids and asks with prices in both cents and dollars. All timestamps are in milliseconds. Orderbook data has history starting from October 29th, 2025."""
        return await self._default.get_kalshi_orderbooks(ticker=ticker, start_time=start_time, end_time=end_time, limit=limit)

    async def get_activity(self, user: str = None, start_time: int = None, end_time: int = None, market_slug: str = None, condition_id: str = None, limit: int = None, offset: int = None) -> Dict[str, Any]:
        """Fetches activity data for a specific user with optional filtering by market, condition, and time range. Returns trading activity including `MERGES`, `SPLITS`, and `REDEEMS`."""
        return await self._default.get_activity(user=user, start_time=start_time, end_time=end_time, market_slug=market_slug, condition_id=condition_id, limit=limit, offset=offset)

    async def get_matching_markets_sports(self, polymarket_market_slug: List[str] = None, kalshi_event_ticker: List[str] = None) -> Dict[str, Any]:
        """Find equivalent markets across different prediction market platforms (Polymarket, Kalshi, etc.) for sports events. Provide either one or more Polymarket market slugs or Kalshi event tickers."""
        return await self._default.get_matching_markets_sports(polymarket_market_slug=polymarket_market_slug, kalshi_event_ticker=kalshi_event_ticker)

    async def get_matching_markets_sports_by_sport(self, sport: Literal["nfl", "mlb", "cfb", "nba", "nhl"], date: str = None) -> Dict[str, Any]:
        """Find equivalent markets across different prediction market platforms (Polymarket, Kalshi, etc.) for sports events by sport and date."""
        return await self._default.get_matching_markets_sports_by_sport(sport=sport, date=date)
