"""
Layer 0 Agent: Environment-based client wrapper for middesk
Automatically loads credentials from environment variables for easy integration
with AI Agent frameworks (LangChain, CrewAI, Madison, etc.)
"""
import os
from typing import Any, Dict, List, Literal, Optional, Union
from .raw import *


class RawAgent:
    """
    Agent-ready wrapper for middesk raw API client.

    Automatically loads credentials from environment variables:
    - MIDDESK_API_KEY: API key/token for authentication
    - MIDDESK_BASE_URL: Base URL for the API (optional, has default)

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
        self.api_key = api_key or os.environ.get("MIDDESK_API_KEY")
        self.base_url = base_url or os.environ.get("MIDDESK_BASE_URL", "https://api.middesk.com/v1")

        if not self.api_key:
            raise ValueError(
                "API key is required. Set MIDDESK_API_KEY environment variable "
                "or pass api_key parameter."
            )

        # Initialize raw client(s)
        self._sandbox = SandboxClient(
            base_url=self.base_url,
            token=self.api_key
        )
        self._production = ProductionClient(
            base_url=self.base_url,
            token=self.api_key
        )

    # ─────────────────────────────────────────────────────────────────────────────
    # Sandbox operations
    # ─────────────────────────────────────────────────────────────────────────────

    async def list_businesses(self) -> Dict[str, Any]:
        """List Businesses"""
        return await self._sandbox.list_businesses()

    async def create_business(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Create Business"""
        return await self._sandbox.create_business(body=body)

    async def update_business(self, business_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """Update Business"""
        return await self._sandbox.update_business(business_id=business_id, body=body)

    async def create_orders(self, business_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """Create Orders"""
        return await self._sandbox.create_orders(business_id=business_id, body=body)

    async def retrieve_a_monitor(self, business_id: str) -> Dict[str, Any]:
        """Retrieve a Monitor"""
        return await self._sandbox.retrieve_a_monitor(business_id=business_id)

    async def create_a_monitor(self, business_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """Create a Monitor"""
        return await self._sandbox.create_a_monitor(business_id=business_id, body=body)

    async def list_webhooks(self) -> Dict[str, Any]:
        """List Webhooks"""
        return await self._sandbox.list_webhooks()

    async def create_webhook(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Create Webhook"""
        return await self._sandbox.create_webhook(body=body)

    async def update_webook(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Update Webook"""
        return await self._sandbox.update_webook(body=body)

    async def retrieve_webhook(self, webhook_id: str) -> Dict[str, Any]:
        """Retrieve Webhook"""
        return await self._sandbox.retrieve_webhook(webhook_id=webhook_id)

    async def delete_webhook(self, webhook_id: str) -> Dict[str, Any]:
        """Delete Webhook"""
        return await self._sandbox.delete_webhook(webhook_id=webhook_id)

    async def lien_filing(self, business_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """Lien Filing"""
        return await self._sandbox.lien_filing(business_id=business_id, body=body)

    # ─────────────────────────────────────────────────────────────────────────────
    # Production operations
    # ─────────────────────────────────────────────────────────────────────────────

    async def get_business(self, business_id: str) -> Dict[str, Any]:
        """Get Business"""
        return await self._production.get_business(business_id=business_id)

    async def retrieve_a_business_pdf(self, business_id: str) -> Dict[str, Any]:
        """Retrieve a Business PDF"""
        return await self._production.retrieve_a_business_pdf(business_id=business_id)
