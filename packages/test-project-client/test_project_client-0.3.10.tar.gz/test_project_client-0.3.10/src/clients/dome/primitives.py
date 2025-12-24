"""
Layer 1: Primitives - Opinionated helper methods for dome
These helpers provide higher-level abstractions over the raw API client.
Each method wraps a Layer 0 operation with the _structured suffix.
"""
from typing import Any, Dict, List, Literal, Optional, Type, TypeVar, Union
from pydantic import BaseModel
from .raw import *

T = TypeVar('T', bound=BaseModel)


class DomePrimitives:
    """
    Opinionated helper methods for dome.

    Generated Layer 1 primitives for 2 operations.
    """

    def __init__(self, default_client: DefaultClient):
        self.default_client = default_client

    async def get_matching_markets_sports_structured(
        self,
        polymarket_market_slug: List[str] = None,
        kalshi_event_ticker: List[str] = None,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Find equivalent markets across different prediction market platforms (Polymarket, Kalshi, etc.) for sports events. Provide either one or more Polymarket market slugs or Kalshi event tickers.
        This is a Layer 1 primitive that wraps the Layer 0 get_matching_markets_sports() method.
        If response_model is provided, the response will be parsed into that Pydantic model.

        Args:
            polymarket_market_slug: The Polymarket market slug(s) to find matching markets for. To get multiple markets at once, provide the query param multiple times with different slugs. Can not be combined with kalshi_event_ticker.
            kalshi_event_ticker: The Kalshi event ticker(s) to find matching markets for. To get multiple markets at once, provide the query param multiple times with different tickers. Can not be combined with polymarket_market_slug.
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        # Call Layer 0 method
        response = await self.default_client.get_matching_markets_sports(
            polymarket_market_slug=polymarket_market_slug,
            kalshi_event_ticker=kalshi_event_ticker
        )

        # If no response model specified, return raw response
        if response_model is None:
            return response

        # Parse response into Pydantic model
        try:
            return response_model.model_validate(response)
        except Exception as e:
            raise ValueError(f"Failed to parse response as {response_model.__name__}: {e}")

    async def get_matching_markets_sports_by_sport_structured(
        self,
        sport: Literal["nfl", "mlb", "cfb", "nba", "nhl"],
        date: str,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Find equivalent markets across different prediction market platforms (Polymarket, Kalshi, etc.) for sports events by sport and date.
        This is a Layer 1 primitive that wraps the Layer 0 get_matching_markets_sports_by_sport() method.
        If response_model is provided, the response will be parsed into that Pydantic model.

        Args:
            sport: The sport to find matching markets for
            date: The date to find matching markets for in YYYY-MM-DD format
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        # Call Layer 0 method
        response = await self.default_client.get_matching_markets_sports_by_sport(
            sport=sport,
            date=date
        )

        # If no response model specified, return raw response
        if response_model is None:
            return response

        # Parse response into Pydantic model
        try:
            return response_model.model_validate(response)
        except Exception as e:
            raise ValueError(f"Failed to parse response as {response_model.__name__}: {e}")
