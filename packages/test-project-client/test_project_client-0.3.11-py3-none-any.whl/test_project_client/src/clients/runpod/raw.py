import httpx
from typing import Any, Dict, List, Literal, Optional, Union
from .types import *

class DocsClient:
    def __init__(self, base_url: str, token: str):
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token}"}
        )

    async def get_open_api(
        self,
        
    ) -> Dict[str, Any]:
        """The OpenAPI 3.0 schema."""
        url = f"/openapi.json"

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

        return response.json()

    async def get_docs(
        self,
        
    ) -> Dict[str, Any]:
        """Interactive API documentation."""
        url = f"/docs"

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


class PodsClient:
    def __init__(self, base_url: str, token: str):
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token}"}
        )

    async def list_pods(
        self,
        compute_type: Literal["GPU", "CPU"] = None,
        cpu_flavor_id: List[str] = None,
        data_center_id: List[str] = None,
        desired_status: Literal["RUNNING", "EXITED", "TERMINATED"] = None,
        endpoint_id: str = None,
        gpu_type_id: List[str] = None,
        id_: str = None,
        image_name: str = None,
        include_machine: bool = None,
        include_network_volume: bool = None,
        include_savings_plans: bool = None,
        include_template: bool = None,
        include_workers: bool = None,
        name: str = None,
        network_volume_id: str = None,
        template_id: str = None
    ) -> List[Dict[str, Any]]:
        """Returns a list of Pods."""
        url = f"/pods"

        params = {
            "computeType": compute_type,
            "cpuFlavorId": cpu_flavor_id,
            "dataCenterId": data_center_id,
            "desiredStatus": desired_status,
            "endpointId": endpoint_id,
            "gpuTypeId": gpu_type_id,
            "id": id_,
            "imageName": image_name,
            "includeMachine": include_machine,
            "includeNetworkVolume": include_network_volume,
            "includeSavingsPlans": include_savings_plans,
            "includeTemplate": include_template,
            "includeWorkers": include_workers,
            "name": name,
            "networkVolumeId": network_volume_id,
            "templateId": template_id,
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

    async def create_pod(
        self,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Creates a new [Pod](#/components/schemas/Pod) and optionally deploys it."""
        url = f"/pods"

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

        return response.json()

    async def get_pod(
        self,
        pod_id: str,
        include_machine: bool = None,
        include_network_volume: bool = None,
        include_savings_plans: bool = None,
        include_template: bool = None,
        include_workers: bool = None
    ) -> Dict[str, Any]:
        """Returns a single Pod."""
        url = f"/pods/{podId}"

        params = {
            "includeMachine": include_machine,
            "includeNetworkVolume": include_network_volume,
            "includeSavingsPlans": include_savings_plans,
            "includeTemplate": include_template,
            "includeWorkers": include_workers,
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

    async def delete_pod(
        self,
        pod_id: str
    ) -> Dict[str, Any]:
        """Delete a Pod."""
        url = f"/pods/{podId}"

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

    async def update_pod(
        self,
        pod_id: str,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a Pod, potentially triggering a reset."""
        url = f"/pods/{podId}"

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

        return response.json()

    async def update_pod(
        self,
        pod_id: str,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a Pod - synonym for PATCH /pods/{podId}."""
        url = f"/pods/{podId}/update"

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

        return response.json()

    async def start_pod(
        self,
        pod_id: str
    ) -> Dict[str, Any]:
        """Start or resume a Pod."""
        url = f"/pods/{podId}/start"

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
        )
        response.raise_for_status()

        return None

    async def stop_pod(
        self,
        pod_id: str
    ) -> Dict[str, Any]:
        """Stop a Pod."""
        url = f"/pods/{podId}/stop"

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
        )
        response.raise_for_status()

        return None

    async def reset_pod(
        self,
        pod_id: str
    ) -> Dict[str, Any]:
        """Reset a Pod."""
        url = f"/pods/{podId}/reset"

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
        )
        response.raise_for_status()

        return None

    async def restart_pod(
        self,
        pod_id: str
    ) -> Dict[str, Any]:
        """Restart a Pod."""
        url = f"/pods/{podId}/restart"

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
        )
        response.raise_for_status()

        return None


class EndpointsClient:
    def __init__(self, base_url: str, token: str):
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token}"}
        )

    async def list_endpoints(
        self,
        include_template: bool = None,
        include_workers: bool = None
    ) -> List[Dict[str, Any]]:
        """Returns a list of endpoints."""
        url = f"/endpoints"

        params = {
            "includeTemplate": include_template,
            "includeWorkers": include_workers,
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

    async def create_endpoint(
        self,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new endpoint."""
        url = f"/endpoints"

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

        return response.json()

    async def get_endpoint(
        self,
        endpoint_id: str,
        include_template: bool = None,
        include_workers: bool = None
    ) -> Dict[str, Any]:
        """Returns a single endpoint."""
        url = f"/endpoints/{endpointId}"

        params = {
            "includeTemplate": include_template,
            "includeWorkers": include_workers,
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

    async def delete_endpoint(
        self,
        endpoint_id: str
    ) -> Dict[str, Any]:
        """Delete an endpoint."""
        url = f"/endpoints/{endpointId}"

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

    async def update_endpoint(
        self,
        endpoint_id: str,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update an endpoint."""
        url = f"/endpoints/{endpointId}"

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

        return response.json()

    async def update_endpoint(
        self,
        endpoint_id: str,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update an endpoint - synonym for PATCH /endpoints/{endpointId}."""
        url = f"/endpoints/{endpointId}/update"

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

        return response.json()


class TemplatesClient:
    def __init__(self, base_url: str, token: str):
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token}"}
        )

    async def list_templates(
        self,
        include_endpoint_bound_templates: bool = None,
        include_public_templates: bool = None,
        include_runpod_templates: bool = None
    ) -> List[Dict[str, Any]]:
        """Returns a list of templates."""
        url = f"/templates"

        params = {
            "includeEndpointBoundTemplates": include_endpoint_bound_templates,
            "includePublicTemplates": include_public_templates,
            "includeRunpodTemplates": include_runpod_templates,
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

    async def create_template(
        self,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new template."""
        url = f"/templates"

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

        return response.json()

    async def get_template(
        self,
        template_id: str,
        include_endpoint_bound_templates: bool = None,
        include_public_templates: bool = None,
        include_runpod_templates: bool = None
    ) -> Dict[str, Any]:
        """Returns a single template."""
        url = f"/templates/{templateId}"

        params = {
            "includeEndpointBoundTemplates": include_endpoint_bound_templates,
            "includePublicTemplates": include_public_templates,
            "includeRunpodTemplates": include_runpod_templates,
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

    async def delete_template(
        self,
        template_id: str
    ) -> Dict[str, Any]:
        """Delete a template."""
        url = f"/templates/{templateId}"

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

    async def update_template(
        self,
        template_id: str,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a template."""
        url = f"/templates/{templateId}"

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

        return response.json()

    async def update_template(
        self,
        template_id: str,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a template - synonym for PATCH /templates/{templateId}."""
        url = f"/templates/{templateId}/update"

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

        return response.json()


class NetworkVolumesClient:
    def __init__(self, base_url: str, token: str):
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token}"}
        )

    async def list_network_volumes(
        self,
        
    ) -> List[Dict[str, Any]]:
        """Returns a list of network volumes."""
        url = f"/networkvolumes"

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

        return response.json()

    async def create_network_volume(
        self,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new network volume."""
        url = f"/networkvolumes"

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

        return response.json()

    async def get_network_volume(
        self,
        network_volume_id: str
    ) -> Dict[str, Any]:
        """Returns a single network volume."""
        url = f"/networkvolumes/{networkVolumeId}"

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

        return response.json()

    async def delete_network_volume(
        self,
        network_volume_id: str
    ) -> Dict[str, Any]:
        """Delete a network volume."""
        url = f"/networkvolumes/{networkVolumeId}"

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

    async def update_network_volume(
        self,
        network_volume_id: str,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a network volume."""
        url = f"/networkvolumes/{networkVolumeId}"

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

        return response.json()

    async def update_network_volume(
        self,
        network_volume_id: str,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a network volume - synonym for PATCH /networkvolumes/{networkVolumeId}."""
        url = f"/networkvolumes/{networkVolumeId}/update"

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

        return response.json()


class ContainerRegistryAuthsClient:
    def __init__(self, base_url: str, token: str):
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token}"}
        )

    async def list_container_registry_auths(
        self,
        
    ) -> List[Dict[str, Any]]:
        """Returns a list of container registry auths."""
        url = f"/containerregistryauth"

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

        return response.json()

    async def create_container_registry_auth(
        self,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new container registry auth."""
        url = f"/containerregistryauth"

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

        return response.json()

    async def get_container_registry_auth(
        self,
        container_registry_auth_id: str
    ) -> Dict[str, Any]:
        """Returns a single container registry auth."""
        url = f"/containerregistryauth/{containerRegistryAuthId}"

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

        return response.json()

    async def delete_container_registry_auth(
        self,
        container_registry_auth_id: str
    ) -> Dict[str, Any]:
        """Delete a container registry auth."""
        url = f"/containerregistryauth/{containerRegistryAuthId}"

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


class BillingClient:
    def __init__(self, base_url: str, token: str):
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token}"}
        )

    async def pod_billing(
        self,
        bucket_size: Literal["hour", "day", "week", "month", "year"] = None,
        end_time: str = None,
        gpu_type_id: Literal["NVIDIA GeForce RTX 4090", "NVIDIA A40", "NVIDIA RTX A5000", "NVIDIA GeForce RTX 5090", "NVIDIA H100 80GB HBM3", "NVIDIA GeForce RTX 3090", "NVIDIA RTX A4500", "NVIDIA L40S", "NVIDIA H200", "NVIDIA L4", "NVIDIA RTX 6000 Ada Generation", "NVIDIA A100-SXM4-80GB", "NVIDIA RTX 4000 Ada Generation", "NVIDIA RTX A6000", "NVIDIA A100 80GB PCIe", "NVIDIA RTX 2000 Ada Generation", "NVIDIA RTX A4000", "NVIDIA RTX PRO 6000 Blackwell Server Edition", "NVIDIA H100 PCIe", "NVIDIA H100 NVL", "NVIDIA L40", "NVIDIA B200", "NVIDIA GeForce RTX 3080 Ti", "NVIDIA RTX PRO 6000 Blackwell Workstation Edition", "NVIDIA GeForce RTX 3080", "NVIDIA GeForce RTX 3070", "AMD Instinct MI300X OAM", "NVIDIA GeForce RTX 4080 SUPER", "Tesla V100-PCIE-16GB", "Tesla V100-SXM2-32GB", "NVIDIA RTX 5000 Ada Generation", "NVIDIA GeForce RTX 4070 Ti", "NVIDIA RTX 4000 SFF Ada Generation", "NVIDIA GeForce RTX 3090 Ti", "NVIDIA RTX A2000", "NVIDIA GeForce RTX 4080", "NVIDIA A30", "NVIDIA GeForce RTX 5080", "Tesla V100-FHHL-16GB", "NVIDIA H200 NVL", "Tesla V100-SXM2-16GB", "NVIDIA RTX PRO 6000 Blackwell Max-Q Workstation Edition", "NVIDIA A5000 Ada", "Tesla V100-PCIE-32GB", "NVIDIA  RTX A4500", "NVIDIA  A30", "NVIDIA GeForce RTX 3080TI", "Tesla T4", "NVIDIA RTX A30"] = None,
        grouping: Literal["podId", "gpuTypeId"] = None,
        pod_id: str = None,
        start_time: str = None
    ) -> List[Dict[str, Any]]:
        """Retrieve billing information about your Pods."""
        url = f"/billing/pods"

        params = {
            "bucketSize": bucket_size,
            "endTime": end_time,
            "gpuTypeId": gpu_type_id,
            "grouping": grouping,
            "podId": pod_id,
            "startTime": start_time,
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

    async def endpoint_billing(
        self,
        bucket_size: Literal["hour", "day", "week", "month", "year"] = None,
        data_center_id: List[Literal["EU-RO-1", "CA-MTL-1", "EU-SE-1", "US-IL-1", "EUR-IS-1", "EU-CZ-1", "US-TX-3", "EUR-IS-2", "US-KS-2", "US-GA-2", "US-WA-1", "US-TX-1", "CA-MTL-3", "EU-NL-1", "US-TX-4", "US-CA-2", "US-NC-1", "OC-AU-1", "US-DE-1", "EUR-IS-3", "CA-MTL-2", "AP-JP-1", "EUR-NO-1", "EU-FR-1", "US-KS-3", "US-GA-1"]] = None,
        endpoint_id: str = None,
        end_time: str = None,
        gpu_type_id: List[Literal["NVIDIA GeForce RTX 4090", "NVIDIA A40", "NVIDIA RTX A5000", "NVIDIA GeForce RTX 5090", "NVIDIA H100 80GB HBM3", "NVIDIA GeForce RTX 3090", "NVIDIA RTX A4500", "NVIDIA L40S", "NVIDIA H200", "NVIDIA L4", "NVIDIA RTX 6000 Ada Generation", "NVIDIA A100-SXM4-80GB", "NVIDIA RTX 4000 Ada Generation", "NVIDIA RTX A6000", "NVIDIA A100 80GB PCIe", "NVIDIA RTX 2000 Ada Generation", "NVIDIA RTX A4000", "NVIDIA RTX PRO 6000 Blackwell Server Edition", "NVIDIA H100 PCIe", "NVIDIA H100 NVL", "NVIDIA L40", "NVIDIA B200", "NVIDIA GeForce RTX 3080 Ti", "NVIDIA RTX PRO 6000 Blackwell Workstation Edition", "NVIDIA GeForce RTX 3080", "NVIDIA GeForce RTX 3070", "AMD Instinct MI300X OAM", "NVIDIA GeForce RTX 4080 SUPER", "Tesla V100-PCIE-16GB", "Tesla V100-SXM2-32GB", "NVIDIA RTX 5000 Ada Generation", "NVIDIA GeForce RTX 4070 Ti", "NVIDIA RTX 4000 SFF Ada Generation", "NVIDIA GeForce RTX 3090 Ti", "NVIDIA RTX A2000", "NVIDIA GeForce RTX 4080", "NVIDIA A30", "NVIDIA GeForce RTX 5080", "Tesla V100-FHHL-16GB", "NVIDIA H200 NVL", "Tesla V100-SXM2-16GB", "NVIDIA RTX PRO 6000 Blackwell Max-Q Workstation Edition", "NVIDIA A5000 Ada", "Tesla V100-PCIE-32GB", "NVIDIA  RTX A4500", "NVIDIA  A30", "NVIDIA GeForce RTX 3080TI", "Tesla T4", "NVIDIA RTX A30"]] = None,
        grouping: Literal["endpointId", "podId", "gpuTypeId"] = None,
        image_name: str = None,
        start_time: str = None,
        template_id: str = None
    ) -> List[Dict[str, Any]]:
        """Retrieve billing information about your Serverless endpoints."""
        url = f"/billing/endpoints"

        params = {
            "bucketSize": bucket_size,
            "dataCenterId": data_center_id,
            "endpointId": endpoint_id,
            "endTime": end_time,
            "gpuTypeId": gpu_type_id,
            "grouping": grouping,
            "imageName": image_name,
            "startTime": start_time,
            "templateId": template_id,
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

    async def network_volume_billing(
        self,
        bucket_size: Literal["hour", "day", "week", "month", "year"] = None,
        end_time: str = None,
        start_time: str = None
    ) -> List[Dict[str, Any]]:
        """Retrieve billing information about your network volumes."""
        url = f"/billing/networkvolumes"

        params = {
            "bucketSize": bucket_size,
            "endTime": end_time,
            "startTime": start_time,
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

