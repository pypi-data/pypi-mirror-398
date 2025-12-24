import httpx
from typing import Any, Dict, List, Literal, Optional, Union
from .types import *

class DefaultClient:
    def __init__(self, base_url: str, token: str):
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token}"}
        )

    async def get_market_price(
        self,
        token_id: str,
        at_time: int = None
    ) -> Dict[str, Any]:
        """Fetches the current market price for a market by `token_id`. When `at_time` is not provided, returns the most real-time price available. When `at_time` is provided, returns the historical market price at that specific timestamp.

**Example Request (with historical timestamp):**
```bash
curl 'https://api.domeapi.io/v1/polymarket/market-price/19701256321759583954581192053894521654935987478209343000964756587964612528044?at_time=1762164600'
```

**Example Request (real-time price):**
```bash
curl 'https://api.domeapi.io/v1/polymarket/market-price/19701256321759583954581192053894521654935987478209343000964756587964612528044'
```"""
        url = f"/polymarket/market-price/{token_id}"

        params = {
            "at_time": at_time,
        }

        headers = {
        }
        # Filter None
        params = {k: v for k, v in params.items() if v is not None}
        headers = {k: v for k, v in headers.items() if v is not None}

        response = await self.client.request(
            method="GET",
            url=url,
            params=params,
            headers=headers,
        )
        response.raise_for_status()

        return response.json()

    async def get_candlesticks(
        self,
        condition_id: str,
        start_time: int = None,
        end_time: int = None,
        interval: int = None
    ) -> Dict[str, Any]:
        """Fetches historical candlestick data for a market identified by `condition_id`, over a specified interval."""
        url = f"/polymarket/candlesticks/{condition_id}"

        params = {
            "start_time": start_time,
            "end_time": end_time,
            "interval": interval,
        }

        headers = {
        }
        # Filter None
        params = {k: v for k, v in params.items() if v is not None}
        headers = {k: v for k, v in headers.items() if v is not None}

        response = await self.client.request(
            method="GET",
            url=url,
            params=params,
            headers=headers,
        )
        response.raise_for_status()

        return response.json()

    async def get_wallet_pnl(
        self,
        wallet_address: str,
        granularity: Literal["day", "week", "month", "year", "all"] = None,
        start_time: int = None,
        end_time: int = None
    ) -> Dict[str, Any]:
        """Fetches the REALIZED profit and loss (PnL) for a specific wallet address over a specified time range and granularity. **Note:** This will differ to what you see on Polymarket's dashboard since Polymarket showcases historical unrealized PnL. This API tracks realized gains only - from either confirmed sells or redeems. We do not realize a gain/loss until a finished market is redeemed."""
        url = f"/polymarket/wallet/pnl/{wallet_address}"

        params = {
            "granularity": granularity,
            "start_time": start_time,
            "end_time": end_time,
        }

        headers = {
        }
        # Filter None
        params = {k: v for k, v in params.items() if v is not None}
        headers = {k: v for k, v in headers.items() if v is not None}

        response = await self.client.request(
            method="GET",
            url=url,
            params=params,
            headers=headers,
        )
        response.raise_for_status()

        return response.json()

    async def get_wallet(
        self,
        eoa: str = None,
        proxy: str = None,
        with_metrics: Literal["true", "false"] = None,
        start_time: int = None,
        end_time: int = None
    ) -> Dict[str, Any]:
        """Fetches wallet information by providing either an EOA (Externally Owned Account) address or a proxy wallet address. Returns the associated EOA, proxy, and wallet type information. Optionally returns trading metrics when `with_metrics=true`."""
        url = f"/polymarket/wallet"

        params = {
            "eoa": eoa,
            "proxy": proxy,
            "with_metrics": with_metrics,
            "start_time": start_time,
            "end_time": end_time,
        }

        headers = {
        }
        # Filter None
        params = {k: v for k, v in params.items() if v is not None}
        headers = {k: v for k, v in headers.items() if v is not None}

        response = await self.client.request(
            method="GET",
            url=url,
            params=params,
            headers=headers,
        )
        response.raise_for_status()

        return response.json()

    async def get_orders(
        self,
        market_slug: str = None,
        condition_id: str = None,
        token_id: str = None,
        start_time: int = None,
        end_time: int = None,
        limit: int = None,
        offset: int = None,
        user: str = None
    ) -> Dict[str, Any]:
        """Fetches order data with optional filtering by market, condition, token, time range, and user. Returns orders that match either primary or secondary token IDs for markets. If no filters provided, fetches the latest trades happening in real-time. Only one of market_slug, token_id, or condition_id can be provided."""
        url = f"/polymarket/orders"

        params = {
            "market_slug": market_slug,
            "condition_id": condition_id,
            "token_id": token_id,
            "start_time": start_time,
            "end_time": end_time,
            "limit": limit,
            "offset": offset,
            "user": user,
        }

        headers = {
        }
        # Filter None
        params = {k: v for k, v in params.items() if v is not None}
        headers = {k: v for k, v in headers.items() if v is not None}

        response = await self.client.request(
            method="GET",
            url=url,
            params=params,
            headers=headers,
        )
        response.raise_for_status()

        return response.json()

    async def get_orderbooks(
        self,
        token_id: str = None,
        start_time: int = None,
        end_time: int = None,
        limit: int = None,
        pagination_key: str = None
    ) -> Dict[str, Any]:
        """Fetches historical orderbook snapshots for a specific asset (token ID) over a specified time range. Returns snapshots of the order book including bids, asks, and market metadata in order. All timestamps are in milliseconds. Orderbook data has history starting from October 14th, 2025."""
        url = f"/polymarket/orderbooks"

        params = {
            "token_id": token_id,
            "start_time": start_time,
            "end_time": end_time,
            "limit": limit,
            "pagination_key": pagination_key,
        }

        headers = {
        }
        # Filter None
        params = {k: v for k, v in params.items() if v is not None}
        headers = {k: v for k, v in headers.items() if v is not None}

        response = await self.client.request(
            method="GET",
            url=url,
            params=params,
            headers=headers,
        )
        response.raise_for_status()

        return response.json()

    async def get_markets(
        self,
        market_slug: List[str] = None,
        event_slug: List[str] = None,
        condition_id: List[str] = None,
        tags: List[str] = None,
        status: Literal["open", "closed"] = None,
        min_volume: float = None,
        limit: int = None,
        offset: int = None,
        start_time: int = None,
        end_time: int = None
    ) -> Dict[str, Any]:
        """Fetches market data with optional filtering and search functionality. Supports filtering by market slug, condition ID, or tags, as well as fuzzy search across market titles and descriptions. Returns markets ordered by volume (most popular first) when filters are applied, or by start_time (most recent first) when no filters are provided."""
        url = f"/polymarket/markets"

        params = {
            "market_slug": market_slug,
            "event_slug": event_slug,
            "condition_id": condition_id,
            "tags": tags,
            "status": status,
            "min_volume": min_volume,
            "limit": limit,
            "offset": offset,
            "start_time": start_time,
            "end_time": end_time,
        }

        headers = {
        }
        # Filter None
        params = {k: v for k, v in params.items() if v is not None}
        headers = {k: v for k, v in headers.items() if v is not None}

        response = await self.client.request(
            method="GET",
            url=url,
            params=params,
            headers=headers,
        )
        response.raise_for_status()

        return response.json()

    async def get_kalshi_markets(
        self,
        market_ticker: List[str] = None,
        event_ticker: List[str] = None,
        status: Literal["open", "closed"] = None,
        min_volume: float = None,
        limit: int = None,
        offset: int = None
    ) -> Dict[str, Any]:
        """Fetches Kalshi market data with optional filtering by market ticker, event ticker, status, and volume. Returns markets with details including pricing, volume, and status information."""
        url = f"/kalshi/markets"

        params = {
            "market_ticker": market_ticker,
            "event_ticker": event_ticker,
            "status": status,
            "min_volume": min_volume,
            "limit": limit,
            "offset": offset,
        }

        headers = {
        }
        # Filter None
        params = {k: v for k, v in params.items() if v is not None}
        headers = {k: v for k, v in headers.items() if v is not None}

        response = await self.client.request(
            method="GET",
            url=url,
            params=params,
            headers=headers,
        )
        response.raise_for_status()

        return response.json()

    async def get_kalshi_trades(
        self,
        ticker: str = None,
        start_time: int = None,
        end_time: int = None,
        limit: int = None,
        offset: int = None
    ) -> Dict[str, Any]:
        """Fetches historical trade data for Kalshi markets with optional filtering by ticker and time range. Returns executed trades with pricing, volume, and taker side information. All timestamps are in seconds."""
        url = f"/kalshi/trades"

        params = {
            "ticker": ticker,
            "start_time": start_time,
            "end_time": end_time,
            "limit": limit,
            "offset": offset,
        }

        headers = {
        }
        # Filter None
        params = {k: v for k, v in params.items() if v is not None}
        headers = {k: v for k, v in headers.items() if v is not None}

        response = await self.client.request(
            method="GET",
            url=url,
            params=params,
            headers=headers,
        )
        response.raise_for_status()

        return response.json()

    async def get_kalshi_orderbooks(
        self,
        ticker: str = None,
        start_time: int = None,
        end_time: int = None,
        limit: int = None
    ) -> Dict[str, Any]:
        """Fetches historical orderbook snapshots for a specific Kalshi market (ticker) over a specified time range. Returns snapshots of the order book including yes/no bids and asks with prices in both cents and dollars. All timestamps are in milliseconds. Orderbook data has history starting from October 29th, 2025."""
        url = f"/kalshi/orderbooks"

        params = {
            "ticker": ticker,
            "start_time": start_time,
            "end_time": end_time,
            "limit": limit,
        }

        headers = {
        }
        # Filter None
        params = {k: v for k, v in params.items() if v is not None}
        headers = {k: v for k, v in headers.items() if v is not None}

        response = await self.client.request(
            method="GET",
            url=url,
            params=params,
            headers=headers,
        )
        response.raise_for_status()

        return response.json()

    async def get_activity(
        self,
        user: str = None,
        start_time: int = None,
        end_time: int = None,
        market_slug: str = None,
        condition_id: str = None,
        limit: int = None,
        offset: int = None
    ) -> Dict[str, Any]:
        """Fetches activity data for a specific user with optional filtering by market, condition, and time range. Returns trading activity including `MERGES`, `SPLITS`, and `REDEEMS`."""
        url = f"/polymarket/activity"

        params = {
            "user": user,
            "start_time": start_time,
            "end_time": end_time,
            "market_slug": market_slug,
            "condition_id": condition_id,
            "limit": limit,
            "offset": offset,
        }

        headers = {
        }
        # Filter None
        params = {k: v for k, v in params.items() if v is not None}
        headers = {k: v for k, v in headers.items() if v is not None}

        response = await self.client.request(
            method="GET",
            url=url,
            params=params,
            headers=headers,
        )
        response.raise_for_status()

        return response.json()

    async def get_matching_markets_sports(
        self,
        polymarket_market_slug: List[str] = None,
        kalshi_event_ticker: List[str] = None
    ) -> Dict[str, Any]:
        """Find equivalent markets across different prediction market platforms (Polymarket, Kalshi, etc.) for sports events. Provide either one or more Polymarket market slugs or Kalshi event tickers."""
        url = f"/matching-markets/sports"

        params = {
            "polymarket_market_slug": polymarket_market_slug,
            "kalshi_event_ticker": kalshi_event_ticker,
        }

        headers = {
        }
        # Filter None
        params = {k: v for k, v in params.items() if v is not None}
        headers = {k: v for k, v in headers.items() if v is not None}

        response = await self.client.request(
            method="GET",
            url=url,
            params=params,
            headers=headers,
        )
        response.raise_for_status()

        return response.json()

    async def get_matching_markets_sports_by_sport(
        self,
        sport: Literal["nfl", "mlb", "cfb", "nba", "nhl"],
        date: str = None
    ) -> Dict[str, Any]:
        """Find equivalent markets across different prediction market platforms (Polymarket, Kalshi, etc.) for sports events by sport and date."""
        url = f"/matching-markets/sports/{sport}"

        params = {
            "date": date,
        }

        headers = {
        }
        # Filter None
        params = {k: v for k, v in params.items() if v is not None}
        headers = {k: v for k, v in headers.items() if v is not None}

        response = await self.client.request(
            method="GET",
            url=url,
            params=params,
            headers=headers,
        )
        response.raise_for_status()

        return response.json()

