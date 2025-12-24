"""
Layer 1: Primitives - Opinionated helper methods for middesk
These helpers provide higher-level abstractions over the raw API client.
Each method wraps a Layer 0 operation with the _structured suffix.
"""
from typing import Any, Dict, List, Literal, Optional, Type, TypeVar, Union
from pydantic import BaseModel
from .raw import *

T = TypeVar('T', bound=BaseModel)


class MiddeskPrimitives:
    """
    Opinionated helper methods for middesk.

    Generated Layer 1 primitives for 14 operations.
    """

    def __init__(self, sandbox_client: SandboxClient, production_client: ProductionClient):
        self.sandbox_client = sandbox_client
        self.production_client = production_client

    async def list_businesses_structured(
        self,
        
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        List Businesses
        This is a Layer 1 primitive that wraps the Layer 0 list_businesses() method.
        If response_model is provided, the response will be parsed into that Pydantic model.

        Args:
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        # Call Layer 0 method
        response = await self.sandbox_client.list_businesses(
            
        )

        # If no response model specified, return raw response
        if response_model is None:
            return response

        # Parse response into Pydantic model
        try:
            return response_model.model_validate(response)
        except Exception as e:
            raise ValueError(f"Failed to parse response as {response_model.__name__}: {e}")

    async def create_business_structured(
        self,
        body: Dict[str, Any],
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Create Business
        This is a Layer 1 primitive that wraps the Layer 0 create_business() method.
        If response_model is provided, the response will be parsed into that Pydantic model.

        Args:
            body: Request body
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        # Call Layer 0 method
        response = await self.sandbox_client.create_business(
            body=body
        )

        # If no response model specified, return raw response
        if response_model is None:
            return response

        # Parse response into Pydantic model
        try:
            return response_model.model_validate(response)
        except Exception as e:
            raise ValueError(f"Failed to parse response as {response_model.__name__}: {e}")

    async def update_business_structured(
        self,
        business_id: str,
        body: Dict[str, Any],
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Update Business
        This is a Layer 1 primitive that wraps the Layer 0 update_business() method.
        If response_model is provided, the response will be parsed into that Pydantic model.

        Args:
            business_id: business_id
            body: Request body
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        # Call Layer 0 method
        response = await self.sandbox_client.update_business(
            business_id=business_id,
            body=body
        )

        # If no response model specified, return raw response
        if response_model is None:
            return response

        # Parse response into Pydantic model
        try:
            return response_model.model_validate(response)
        except Exception as e:
            raise ValueError(f"Failed to parse response as {response_model.__name__}: {e}")

    async def create_orders_structured(
        self,
        business_id: str,
        body: Dict[str, Any],
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Create Orders
        This is a Layer 1 primitive that wraps the Layer 0 create_orders() method.
        If response_model is provided, the response will be parsed into that Pydantic model.

        Args:
            business_id: business_id
            body: Request body
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        # Call Layer 0 method
        response = await self.sandbox_client.create_orders(
            business_id=business_id,
            body=body
        )

        # If no response model specified, return raw response
        if response_model is None:
            return response

        # Parse response into Pydantic model
        try:
            return response_model.model_validate(response)
        except Exception as e:
            raise ValueError(f"Failed to parse response as {response_model.__name__}: {e}")

    async def retrieve_a_monitor_structured(
        self,
        business_id: str,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Retrieve a Monitor
        This is a Layer 1 primitive that wraps the Layer 0 retrieve_a_monitor() method.
        If response_model is provided, the response will be parsed into that Pydantic model.

        Args:
            business_id: business_id
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        # Call Layer 0 method
        response = await self.sandbox_client.retrieve_a_monitor(
            business_id=business_id
        )

        # If no response model specified, return raw response
        if response_model is None:
            return response

        # Parse response into Pydantic model
        try:
            return response_model.model_validate(response)
        except Exception as e:
            raise ValueError(f"Failed to parse response as {response_model.__name__}: {e}")

    async def create_a_monitor_structured(
        self,
        business_id: str,
        body: Dict[str, Any],
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Create a Monitor
        This is a Layer 1 primitive that wraps the Layer 0 create_a_monitor() method.
        If response_model is provided, the response will be parsed into that Pydantic model.

        Args:
            business_id: business_id
            body: Request body
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        # Call Layer 0 method
        response = await self.sandbox_client.create_a_monitor(
            business_id=business_id,
            body=body
        )

        # If no response model specified, return raw response
        if response_model is None:
            return response

        # Parse response into Pydantic model
        try:
            return response_model.model_validate(response)
        except Exception as e:
            raise ValueError(f"Failed to parse response as {response_model.__name__}: {e}")

    async def list_webhooks_structured(
        self,
        
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        List Webhooks
        This is a Layer 1 primitive that wraps the Layer 0 list_webhooks() method.
        If response_model is provided, the response will be parsed into that Pydantic model.

        Args:
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        # Call Layer 0 method
        response = await self.sandbox_client.list_webhooks(
            
        )

        # If no response model specified, return raw response
        if response_model is None:
            return response

        # Parse response into Pydantic model
        try:
            return response_model.model_validate(response)
        except Exception as e:
            raise ValueError(f"Failed to parse response as {response_model.__name__}: {e}")

    async def create_webhook_structured(
        self,
        body: Dict[str, Any],
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Create Webhook
        This is a Layer 1 primitive that wraps the Layer 0 create_webhook() method.
        If response_model is provided, the response will be parsed into that Pydantic model.

        Args:
            body: Request body
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        # Call Layer 0 method
        response = await self.sandbox_client.create_webhook(
            body=body
        )

        # If no response model specified, return raw response
        if response_model is None:
            return response

        # Parse response into Pydantic model
        try:
            return response_model.model_validate(response)
        except Exception as e:
            raise ValueError(f"Failed to parse response as {response_model.__name__}: {e}")

    async def update_webook_structured(
        self,
        body: Dict[str, Any],
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Update Webook
        This is a Layer 1 primitive that wraps the Layer 0 update_webook() method.
        If response_model is provided, the response will be parsed into that Pydantic model.

        Args:
            body: Request body
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        # Call Layer 0 method
        response = await self.sandbox_client.update_webook(
            body=body
        )

        # If no response model specified, return raw response
        if response_model is None:
            return response

        # Parse response into Pydantic model
        try:
            return response_model.model_validate(response)
        except Exception as e:
            raise ValueError(f"Failed to parse response as {response_model.__name__}: {e}")

    async def retrieve_webhook_structured(
        self,
        webhook_id: str,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Retrieve Webhook
        This is a Layer 1 primitive that wraps the Layer 0 retrieve_webhook() method.
        If response_model is provided, the response will be parsed into that Pydantic model.

        Args:
            webhook_id: webhook_id
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        # Call Layer 0 method
        response = await self.sandbox_client.retrieve_webhook(
            webhook_id=webhook_id
        )

        # If no response model specified, return raw response
        if response_model is None:
            return response

        # Parse response into Pydantic model
        try:
            return response_model.model_validate(response)
        except Exception as e:
            raise ValueError(f"Failed to parse response as {response_model.__name__}: {e}")

    async def delete_webhook_structured(
        self,
        webhook_id: str,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Delete Webhook
        This is a Layer 1 primitive that wraps the Layer 0 delete_webhook() method.
        If response_model is provided, the response will be parsed into that Pydantic model.

        Args:
            webhook_id: webhook_id
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        # Call Layer 0 method
        response = await self.sandbox_client.delete_webhook(
            webhook_id=webhook_id
        )

        # If no response model specified, return raw response
        if response_model is None:
            return response

        # Parse response into Pydantic model
        try:
            return response_model.model_validate(response)
        except Exception as e:
            raise ValueError(f"Failed to parse response as {response_model.__name__}: {e}")

    async def lien_filing_structured(
        self,
        business_id: str,
        body: Dict[str, Any],
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Lien Filing
        This is a Layer 1 primitive that wraps the Layer 0 lien_filing() method.
        If response_model is provided, the response will be parsed into that Pydantic model.

        Args:
            business_id: business_id
            body: Request body
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        # Call Layer 0 method
        response = await self.sandbox_client.lien_filing(
            business_id=business_id,
            body=body
        )

        # If no response model specified, return raw response
        if response_model is None:
            return response

        # Parse response into Pydantic model
        try:
            return response_model.model_validate(response)
        except Exception as e:
            raise ValueError(f"Failed to parse response as {response_model.__name__}: {e}")

    async def get_business_structured(
        self,
        business_id: str,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Get Business
        This is a Layer 1 primitive that wraps the Layer 0 get_business() method.
        If response_model is provided, the response will be parsed into that Pydantic model.

        Args:
            business_id: business_id
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        # Call Layer 0 method
        response = await self.production_client.get_business(
            business_id=business_id
        )

        # If no response model specified, return raw response
        if response_model is None:
            return response

        # Parse response into Pydantic model
        try:
            return response_model.model_validate(response)
        except Exception as e:
            raise ValueError(f"Failed to parse response as {response_model.__name__}: {e}")

    async def retrieve_a_business_pdf_structured(
        self,
        business_id: str,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Retrieve a Business PDF
        This is a Layer 1 primitive that wraps the Layer 0 retrieve_a_business_pdf() method.
        If response_model is provided, the response will be parsed into that Pydantic model.

        Args:
            business_id: business_id
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        # Call Layer 0 method
        response = await self.production_client.retrieve_a_business_pdf(
            business_id=business_id
        )

        # If no response model specified, return raw response
        if response_model is None:
            return response

        # Parse response into Pydantic model
        try:
            return response_model.model_validate(response)
        except Exception as e:
            raise ValueError(f"Failed to parse response as {response_model.__name__}: {e}")
