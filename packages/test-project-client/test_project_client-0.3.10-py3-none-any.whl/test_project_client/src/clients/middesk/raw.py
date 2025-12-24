import httpx
from typing import Any, Dict, List, Literal, Optional, Union
from .types import *

class SandboxClient:
    def __init__(self, base_url: str, token: str):
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token}"}
        )

    async def list_businesses(
        self,
        
    ) -> Dict[str, Any]:
        """List Businesses"""
        url = f"/businesses"

        params = {
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

        return None

    async def create_business(
        self,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create Business"""
        url = f"/businesses"

        params = {
        }

        headers = {
        }
        # Filter None
        params = {k: v for k, v in params.items() if v is not None}
        headers = {k: v for k, v in headers.items() if v is not None}

        response = await self.client.request(
            method="POST",
            url=url,
            params=params,
            headers=headers,
            json=body.model_dump(by_alias=True) if hasattr(body, 'model_dump') else body
        )
        response.raise_for_status()

        return None

    async def update_business(
        self,
        business_id: str,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update Business"""
        url = f"/businesses/{BUSINESS_ID}"

        params = {
        }

        headers = {
        }
        # Filter None
        params = {k: v for k, v in params.items() if v is not None}
        headers = {k: v for k, v in headers.items() if v is not None}

        response = await self.client.request(
            method="PATCH",
            url=url,
            params=params,
            headers=headers,
            json=body.model_dump(by_alias=True) if hasattr(body, 'model_dump') else body
        )
        response.raise_for_status()

        return None

    async def create_orders(
        self,
        business_id: str,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create Orders"""
        url = f"/businesses/{BUSINESS_ID}/orders"

        params = {
        }

        headers = {
        }
        # Filter None
        params = {k: v for k, v in params.items() if v is not None}
        headers = {k: v for k, v in headers.items() if v is not None}

        response = await self.client.request(
            method="POST",
            url=url,
            params=params,
            headers=headers,
            json=body.model_dump(by_alias=True) if hasattr(body, 'model_dump') else body
        )
        response.raise_for_status()

        return None

    async def retrieve_a_monitor(
        self,
        business_id: str
    ) -> Dict[str, Any]:
        """Retrieve a Monitor"""
        url = f"/businesses/{BUSINESS_ID}/monitor"

        params = {
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

        return None

    async def create_a_monitor(
        self,
        business_id: str,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a Monitor"""
        url = f"/businesses/{BUSINESS_ID}/monitor"

        params = {
        }

        headers = {
        }
        # Filter None
        params = {k: v for k, v in params.items() if v is not None}
        headers = {k: v for k, v in headers.items() if v is not None}

        response = await self.client.request(
            method="POST",
            url=url,
            params=params,
            headers=headers,
            json=body.model_dump(by_alias=True) if hasattr(body, 'model_dump') else body
        )
        response.raise_for_status()

        return None

    async def list_webhooks(
        self,
        
    ) -> Dict[str, Any]:
        """List Webhooks"""
        url = f"/webhooks"

        params = {
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

        return None

    async def create_webhook(
        self,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create Webhook"""
        url = f"/webhooks"

        params = {
        }

        headers = {
        }
        # Filter None
        params = {k: v for k, v in params.items() if v is not None}
        headers = {k: v for k, v in headers.items() if v is not None}

        response = await self.client.request(
            method="POST",
            url=url,
            params=params,
            headers=headers,
            json=body.model_dump(by_alias=True) if hasattr(body, 'model_dump') else body
        )
        response.raise_for_status()

        return None

    async def update_webook(
        self,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update Webook"""
        url = f"/webhooks"

        params = {
        }

        headers = {
        }
        # Filter None
        params = {k: v for k, v in params.items() if v is not None}
        headers = {k: v for k, v in headers.items() if v is not None}

        response = await self.client.request(
            method="PATCH",
            url=url,
            params=params,
            headers=headers,
            json=body.model_dump(by_alias=True) if hasattr(body, 'model_dump') else body
        )
        response.raise_for_status()

        return None

    async def retrieve_webhook(
        self,
        webhook_id: str
    ) -> Dict[str, Any]:
        """Retrieve Webhook"""
        url = f"/webhooks/{WEBHOOK_ID}"

        params = {
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

        return None

    async def delete_webhook(
        self,
        webhook_id: str
    ) -> Dict[str, Any]:
        """Delete Webhook"""
        url = f"/webhooks/{WEBHOOK_ID}"

        params = {
        }

        headers = {
        }
        # Filter None
        params = {k: v for k, v in params.items() if v is not None}
        headers = {k: v for k, v in headers.items() if v is not None}

        response = await self.client.request(
            method="DELETE",
            url=url,
            params=params,
            headers=headers,
        )
        response.raise_for_status()

        return None

    async def lien_filing(
        self,
        business_id: str,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Lien Filing"""
        url = f"/businesses/{BUSINESS_ID}/liens"

        params = {
        }

        headers = {
        }
        # Filter None
        params = {k: v for k, v in params.items() if v is not None}
        headers = {k: v for k, v in headers.items() if v is not None}

        response = await self.client.request(
            method="POST",
            url=url,
            params=params,
            headers=headers,
            json=body.model_dump(by_alias=True) if hasattr(body, 'model_dump') else body
        )
        response.raise_for_status()

        return None


class ProductionClient:
    def __init__(self, base_url: str, token: str):
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token}"}
        )

    async def get_business(
        self,
        business_id: str
    ) -> Dict[str, Any]:
        """Get Business"""
        url = f"/businesses/{BUSINESS_ID}"

        params = {
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

        return None

    async def retrieve_a_business_pdf(
        self,
        business_id: str
    ) -> Dict[str, Any]:
        """Retrieve a Business PDF"""
        url = f"/businesses/{BUSINESS_ID}/pdf"

        params = {
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

        return None

