"""
Layer 1 Agent: Environment-based primitives wrapper for middesk
Composes RawAgent and provides access to Layer 1 primitives (structured helpers).
Automatically loads credentials from environment variables for easy integration
with AI Agent frameworks (LangChain, CrewAI, Madison, etc.)
"""
import os
from typing import Any, Dict, List, Literal, Optional, Type, TypeVar, Union
from pydantic import BaseModel
from .raw_agent import RawAgent
from .primitives import MiddeskPrimitives

T = TypeVar('T', bound=BaseModel)

class PrimitivesAgent:
    """
    Agent-ready wrapper for middesk primitives (Layer 1).

    Composes RawAgent and provides access to structured helper methods.

    Automatically loads credentials from environment variables:
    - MIDDESK_API_KEY: API key/token for authentication
    - MIDDESK_BASE_URL: Base URL for the API (optional, has default)

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
        self.api_key = api_key or os.environ.get("MIDDESK_API_KEY")
        self.base_url = base_url or os.environ.get("MIDDESK_BASE_URL", "https://api.middesk.com/v1")

        if not self.api_key:
            raise ValueError(
                "API key is required. Set MIDDESK_API_KEY environment variable "
                "or pass api_key parameter."
            )

        # Initialize RawAgent (Layer 0)
        self.raw = RawAgent(api_key=self.api_key, base_url=self.base_url)

        # Initialize Primitives (Layer 1)
        # Primitives need the raw client instances
        self._primitives = MiddeskPrimitives(
            sandbox_client=self.raw._sandbox,
            production_client=self.raw._production
        )

    # ─────────────────────────────────────────────────────────────────────────────
    # Primitive operations (Layer 1)
    # ─────────────────────────────────────────────────────────────────────────────

    async def list_businesses_structured(
        self,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        List Businesses
        Args:
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        return await self._primitives.list_businesses_structured(
            
            response_model=response_model
        )

    async def create_business_structured(
        self,
        body: Dict[str, Any],
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Create Business
        Args:
            body: Request body
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        return await self._primitives.create_business_structured(
            body=body,
            response_model=response_model
        )

    async def update_business_structured(
        self,
        business_id: str, body: Dict[str, Any],
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Update Business
        Args:
            business_id: business_id
            body: Request body
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        return await self._primitives.update_business_structured(
            business_id=business_id, body=body,
            response_model=response_model
        )

    async def create_orders_structured(
        self,
        business_id: str, body: Dict[str, Any],
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Create Orders
        Args:
            business_id: business_id
            body: Request body
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        return await self._primitives.create_orders_structured(
            business_id=business_id, body=body,
            response_model=response_model
        )

    async def retrieve_a_monitor_structured(
        self,
        business_id: str,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Retrieve a Monitor
        Args:
            business_id: business_id
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        return await self._primitives.retrieve_a_monitor_structured(
            business_id=business_id,
            response_model=response_model
        )

    async def create_a_monitor_structured(
        self,
        business_id: str, body: Dict[str, Any],
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Create a Monitor
        Args:
            business_id: business_id
            body: Request body
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        return await self._primitives.create_a_monitor_structured(
            business_id=business_id, body=body,
            response_model=response_model
        )

    async def list_webhooks_structured(
        self,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        List Webhooks
        Args:
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        return await self._primitives.list_webhooks_structured(
            
            response_model=response_model
        )

    async def create_webhook_structured(
        self,
        body: Dict[str, Any],
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Create Webhook
        Args:
            body: Request body
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        return await self._primitives.create_webhook_structured(
            body=body,
            response_model=response_model
        )

    async def update_webook_structured(
        self,
        body: Dict[str, Any],
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Update Webook
        Args:
            body: Request body
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        return await self._primitives.update_webook_structured(
            body=body,
            response_model=response_model
        )

    async def retrieve_webhook_structured(
        self,
        webhook_id: str,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Retrieve Webhook
        Args:
            webhook_id: webhook_id
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        return await self._primitives.retrieve_webhook_structured(
            webhook_id=webhook_id,
            response_model=response_model
        )

    async def delete_webhook_structured(
        self,
        webhook_id: str,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Delete Webhook
        Args:
            webhook_id: webhook_id
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        return await self._primitives.delete_webhook_structured(
            webhook_id=webhook_id,
            response_model=response_model
        )

    async def lien_filing_structured(
        self,
        business_id: str, body: Dict[str, Any],
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Lien Filing
        Args:
            business_id: business_id
            body: Request body
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        return await self._primitives.lien_filing_structured(
            business_id=business_id, body=body,
            response_model=response_model
        )

    async def get_business_structured(
        self,
        business_id: str,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Get Business
        Args:
            business_id: business_id
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        return await self._primitives.get_business_structured(
            business_id=business_id,
            response_model=response_model
        )

    async def retrieve_a_business_pdf_structured(
        self,
        business_id: str,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Retrieve a Business PDF
        Args:
            business_id: business_id
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        return await self._primitives.retrieve_a_business_pdf_structured(
            business_id=business_id,
            response_model=response_model
        )
