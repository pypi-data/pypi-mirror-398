"""
Layer 2 Agent: Environment-based business logic wrapper for dome
Composes PrimitivesAgent and provides access to user-implemented business actions.
Automatically loads credentials from environment variables for easy integration
with AI Agent frameworks (LangChain, CrewAI, Madison, etc.)
"""
import os
from typing import Any, Dict, List, Optional
from src.clients.dome.primitives_agent import PrimitivesAgent
from src.business.context import ServiceContext


class BusinessAgent:
    """
    Agent-ready wrapper for dome business logic (Layer 2).

    Composes PrimitivesAgent and provides access to user-implemented business actions.

    Automatically loads credentials from environment variables:
    - DOME_API_KEY: API key/token for authentication
    - DOME_BASE_URL: Base URL for the API (optional, has default)

    Usage:
        agent = BusinessAgent()  # Uses env vars
        agent = BusinessAgent(api_key="...", base_url="...")  # Explicit

        # Access raw methods via .primitives.raw
        await agent.primitives.raw.get_markets(...)

        # Access primitive methods via .primitives
        await agent.primitives.get_markets_structured(...)

        # Access business actions directly
        # (No business actions defined yet)
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

        # Initialize PrimitivesAgent (Layer 0 + Layer 1)
        self.primitives = PrimitivesAgent(api_key=self.api_key, base_url=self.base_url)

        # Create service context for business actions
        self._ctx = ServiceContext()
        # Wire up the client in context
        self._ctx.dome = self.primitives.raw

