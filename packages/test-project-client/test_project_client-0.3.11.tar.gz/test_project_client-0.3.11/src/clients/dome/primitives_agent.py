"""
Layer 1 Agent: Environment-based primitives wrapper for dome
Composes RawAgent and provides access to Layer 1 primitives (structured helpers).
Automatically loads credentials from environment variables for easy integration
with AI Agent frameworks (LangChain, CrewAI, Madison, etc.)
"""
import os
from typing import Any, Dict, List, Literal, Optional, Type, TypeVar, Union
from pydantic import BaseModel
from .raw_agent import RawAgent
from .primitives import DomePrimitives

T = TypeVar('T', bound=BaseModel)

class PrimitivesAgent:
    """
    Agent-ready wrapper for dome primitives (Layer 1).

    Composes RawAgent and provides access to structured helper methods.

    Automatically loads credentials from environment variables:
    - DOME_API_KEY: API key/token for authentication
    - DOME_BASE_URL: Base URL for the API (optional, has default)

    Usage:
        agent = PrimitivesAgent()  # Uses env vars
        agent = PrimitivesAgent(api_key="...", base_url="...")  # Explicit

        # Access raw methods via .raw
        await agent.raw.get_markets(...)

        # Access primitive methods directly
        await agent.get_markets_structured(...)
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

        # Initialize RawAgent (Layer 0)
        self.raw = RawAgent(api_key=self.api_key, base_url=self.base_url)

        # Initialize Primitives (Layer 1)
        # Primitives need the raw client instances
        self._primitives = DomePrimitives(
            default_client=self.raw._default
        )

    # ─────────────────────────────────────────────────────────────────────────────
    # Primitive operations (Layer 1)
    # ─────────────────────────────────────────────────────────────────────────────

    async def get_market_price_structured(
        self,
        token_id: str, at_time: int = None,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Fetches the current market price for a market by `token_id`. When `at_time` is not provided, returns the most real-time price available. When `at_time` is provided, returns the historical market price at that specific timestamp.

**Example Request (with historical timestamp):**
```bash
curl 'https://api.domeapi.io/v1/polymarket/market-price/19701256321759583954581192053894521654935987478209343000964756587964612528044?at_time=1762164600'
```

**Example Request (real-time price):**
```bash
curl 'https://api.domeapi.io/v1/polymarket/market-price/19701256321759583954581192053894521654935987478209343000964756587964612528044'
```
        Args:
            token_id: The token ID for the Polymarket market
            at_time: Optional Unix timestamp (in seconds) to fetch a historical market price. If not provided, returns the most real-time price available.
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        return await self._primitives.get_market_price_structured(
            token_id=token_id, at_time=at_time,
            response_model=response_model
        )

    async def get_matching_markets_sports_structured(
        self,
        polymarket_market_slug: List[str] = None, kalshi_event_ticker: List[str] = None,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Find equivalent markets across different prediction market platforms (Polymarket, Kalshi, etc.) for sports events. Provide either one or more Polymarket market slugs or Kalshi event tickers.
        Args:
            polymarket_market_slug: The Polymarket market slug(s) to find matching markets for. To get multiple markets at once, provide the query param multiple times with different slugs. Can not be combined with kalshi_event_ticker.
            kalshi_event_ticker: The Kalshi event ticker(s) to find matching markets for. To get multiple markets at once, provide the query param multiple times with different tickers. Can not be combined with polymarket_market_slug.
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        return await self._primitives.get_matching_markets_sports_structured(
            polymarket_market_slug=polymarket_market_slug, kalshi_event_ticker=kalshi_event_ticker,
            response_model=response_model
        )

    async def get_matching_markets_sports_by_sport_structured(
        self,
        sport: Literal["nfl", "mlb", "cfb", "nba", "nhl"], date: str,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Find equivalent markets across different prediction market platforms (Polymarket, Kalshi, etc.) for sports events by sport and date.
        Args:
            sport: The sport to find matching markets for
            date: The date to find matching markets for in YYYY-MM-DD format
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        return await self._primitives.get_matching_markets_sports_by_sport_structured(
            sport=sport, date=date,
            response_model=response_model
        )
