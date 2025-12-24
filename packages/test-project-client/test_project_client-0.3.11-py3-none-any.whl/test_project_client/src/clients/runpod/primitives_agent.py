"""
Layer 1 Agent: Environment-based primitives wrapper for runpod
Composes RawAgent and provides access to Layer 1 primitives (structured helpers).
Automatically loads credentials from environment variables for easy integration
with AI Agent frameworks (LangChain, CrewAI, Madison, etc.)
"""
import os
from typing import Any, Dict, List, Literal, Optional, Type, TypeVar, Union
from pydantic import BaseModel
from .raw_agent import RawAgent
from .primitives import RunpodPrimitives

T = TypeVar('T', bound=BaseModel)

class PrimitivesAgent:
    """
    Agent-ready wrapper for runpod primitives (Layer 1).

    Composes RawAgent and provides access to structured helper methods.

    Automatically loads credentials from environment variables:
    - RUNPOD_API_KEY: API key/token for authentication
    - RUNPOD_BASE_URL: Base URL for the API (optional, has default)

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
        self.api_key = api_key or os.environ.get("RUNPOD_API_KEY")
        self.base_url = base_url or os.environ.get("RUNPOD_BASE_URL", "https://rest.runpod.io/v1")

        if not self.api_key:
            raise ValueError(
                "API key is required. Set RUNPOD_API_KEY environment variable "
                "or pass api_key parameter."
            )

        # Initialize RawAgent (Layer 0)
        self.raw = RawAgent(api_key=self.api_key, base_url=self.base_url)

        # Initialize Primitives (Layer 1)
        # Primitives need the raw client instances
        self._primitives = RunpodPrimitives(
            docs_client=self.raw._docs,
            pods_client=self.raw._pods,
            endpoints_client=self.raw._endpoints,
            templates_client=self.raw._templates,
            network_volumes_client=self.raw._network_volumes,
            container_registry_auths_client=self.raw._container_registry_auths,
            billing_client=self.raw._billing
        )

    # ─────────────────────────────────────────────────────────────────────────────
    # Primitive operations (Layer 1)
    # ─────────────────────────────────────────────────────────────────────────────

    async def get_open_api_structured(
        self,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        The OpenAPI 3.0 schema.
        Args:
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        return await self._primitives.get_open_api_structured(
            
            response_model=response_model
        )

    async def get_docs_structured(
        self,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Interactive API documentation.
        Args:
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        return await self._primitives.get_docs_structured(
            
            response_model=response_model
        )

    async def list_pods_structured(
        self,
        compute_type: Literal["GPU", "CPU"] = None, cpu_flavor_id: List[str] = None, data_center_id: List[str] = None, desired_status: Literal["RUNNING", "EXITED", "TERMINATED"] = None, endpoint_id: str = None, gpu_type_id: List[str] = None, id_: str = None, image_name: str = None, include_machine: bool = None, include_network_volume: bool = None, include_savings_plans: bool = None, include_template: bool = None, include_workers: bool = None, name: str = None, network_volume_id: str = None, template_id: str = None,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Returns a list of Pods.
        Args:
            compute_type: compute_type
            cpu_flavor_id: cpu_flavor_id
            data_center_id: data_center_id
            desired_status: desired_status
            endpoint_id: endpoint_id
            gpu_type_id: gpu_type_id
            id_: id_
            image_name: image_name
            include_machine: include_machine
            include_network_volume: include_network_volume
            include_savings_plans: include_savings_plans
            include_template: include_template
            include_workers: include_workers
            name: name
            network_volume_id: network_volume_id
            template_id: template_id
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        return await self._primitives.list_pods_structured(
            compute_type=compute_type, cpu_flavor_id=cpu_flavor_id, data_center_id=data_center_id, desired_status=desired_status, endpoint_id=endpoint_id, gpu_type_id=gpu_type_id, id_=id_, image_name=image_name, include_machine=include_machine, include_network_volume=include_network_volume, include_savings_plans=include_savings_plans, include_template=include_template, include_workers=include_workers, name=name, network_volume_id=network_volume_id, template_id=template_id,
            response_model=response_model
        )

    async def create_pod_structured(
        self,
        body: Dict[str, Any],
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Creates a new [Pod](#/components/schemas/Pod) and optionally deploys it.
        Args:
            body: Request body
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        return await self._primitives.create_pod_structured(
            body=body,
            response_model=response_model
        )

    async def get_pod_structured(
        self,
        pod_id: str, include_machine: bool = None, include_network_volume: bool = None, include_savings_plans: bool = None, include_template: bool = None, include_workers: bool = None,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Returns a single Pod.
        Args:
            pod_id: ID of Pod to return.
            include_machine: include_machine
            include_network_volume: include_network_volume
            include_savings_plans: include_savings_plans
            include_template: include_template
            include_workers: include_workers
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        return await self._primitives.get_pod_structured(
            pod_id=pod_id, include_machine=include_machine, include_network_volume=include_network_volume, include_savings_plans=include_savings_plans, include_template=include_template, include_workers=include_workers,
            response_model=response_model
        )

    async def delete_pod_structured(
        self,
        pod_id: str,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Delete a Pod.
        Args:
            pod_id: Pod ID to delete.
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        return await self._primitives.delete_pod_structured(
            pod_id=pod_id,
            response_model=response_model
        )

    async def update_pod_structured(
        self,
        pod_id: str, body: Dict[str, Any],
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Update a Pod, potentially triggering a reset.
        Args:
            pod_id: ID of Pod that needs to be updated.
            body: Request body
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        return await self._primitives.update_pod_structured(
            pod_id=pod_id, body=body,
            response_model=response_model
        )

    async def update_pod_structured(
        self,
        pod_id: str, body: Dict[str, Any],
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Update a Pod - synonym for PATCH /pods/{podId}.
        Args:
            pod_id: ID of Pod that needs to be updated.
            body: Request body
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        return await self._primitives.update_pod_structured(
            pod_id=pod_id, body=body,
            response_model=response_model
        )

    async def start_pod_structured(
        self,
        pod_id: str,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Start or resume a Pod.
        Args:
            pod_id: Pod ID to start.
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        return await self._primitives.start_pod_structured(
            pod_id=pod_id,
            response_model=response_model
        )

    async def stop_pod_structured(
        self,
        pod_id: str,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Stop a Pod.
        Args:
            pod_id: Pod ID to stop.
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        return await self._primitives.stop_pod_structured(
            pod_id=pod_id,
            response_model=response_model
        )

    async def reset_pod_structured(
        self,
        pod_id: str,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Reset a Pod.
        Args:
            pod_id: Pod ID to reset.
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        return await self._primitives.reset_pod_structured(
            pod_id=pod_id,
            response_model=response_model
        )

    async def restart_pod_structured(
        self,
        pod_id: str,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Restart a Pod.
        Args:
            pod_id: Pod ID to restart.
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        return await self._primitives.restart_pod_structured(
            pod_id=pod_id,
            response_model=response_model
        )

    async def list_endpoints_structured(
        self,
        include_template: bool = None, include_workers: bool = None,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Returns a list of endpoints.
        Args:
            include_template: include_template
            include_workers: include_workers
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        return await self._primitives.list_endpoints_structured(
            include_template=include_template, include_workers=include_workers,
            response_model=response_model
        )

    async def create_endpoint_structured(
        self,
        body: Dict[str, Any],
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Create a new endpoint.
        Args:
            body: Request body
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        return await self._primitives.create_endpoint_structured(
            body=body,
            response_model=response_model
        )

    async def get_endpoint_structured(
        self,
        endpoint_id: str, include_template: bool = None, include_workers: bool = None,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Returns a single endpoint.
        Args:
            endpoint_id: ID of endpoint to return.
            include_template: include_template
            include_workers: include_workers
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        return await self._primitives.get_endpoint_structured(
            endpoint_id=endpoint_id, include_template=include_template, include_workers=include_workers,
            response_model=response_model
        )

    async def delete_endpoint_structured(
        self,
        endpoint_id: str,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Delete an endpoint.
        Args:
            endpoint_id: Endpoint ID to delete.
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        return await self._primitives.delete_endpoint_structured(
            endpoint_id=endpoint_id,
            response_model=response_model
        )

    async def update_endpoint_structured(
        self,
        endpoint_id: str, body: Dict[str, Any],
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Update an endpoint.
        Args:
            endpoint_id: ID of endpoint that needs to be updated.
            body: Request body
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        return await self._primitives.update_endpoint_structured(
            endpoint_id=endpoint_id, body=body,
            response_model=response_model
        )

    async def update_endpoint_structured(
        self,
        endpoint_id: str, body: Dict[str, Any],
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Update an endpoint - synonym for PATCH /endpoints/{endpointId}.
        Args:
            endpoint_id: ID of endpoint that needs to be updated.
            body: Request body
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        return await self._primitives.update_endpoint_structured(
            endpoint_id=endpoint_id, body=body,
            response_model=response_model
        )

    async def list_templates_structured(
        self,
        include_endpoint_bound_templates: bool = None, include_public_templates: bool = None, include_runpod_templates: bool = None,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Returns a list of templates.
        Args:
            include_endpoint_bound_templates: include_endpoint_bound_templates
            include_public_templates: include_public_templates
            include_runpod_templates: include_runpod_templates
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        return await self._primitives.list_templates_structured(
            include_endpoint_bound_templates=include_endpoint_bound_templates, include_public_templates=include_public_templates, include_runpod_templates=include_runpod_templates,
            response_model=response_model
        )

    async def create_template_structured(
        self,
        body: Dict[str, Any],
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Create a new template.
        Args:
            body: Request body
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        return await self._primitives.create_template_structured(
            body=body,
            response_model=response_model
        )

    async def get_template_structured(
        self,
        template_id: str, include_endpoint_bound_templates: bool = None, include_public_templates: bool = None, include_runpod_templates: bool = None,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Returns a single template.
        Args:
            template_id: ID of template to return.
            include_endpoint_bound_templates: include_endpoint_bound_templates
            include_public_templates: include_public_templates
            include_runpod_templates: include_runpod_templates
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        return await self._primitives.get_template_structured(
            template_id=template_id, include_endpoint_bound_templates=include_endpoint_bound_templates, include_public_templates=include_public_templates, include_runpod_templates=include_runpod_templates,
            response_model=response_model
        )

    async def delete_template_structured(
        self,
        template_id: str,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Delete a template.
        Args:
            template_id: Template ID to delete.
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        return await self._primitives.delete_template_structured(
            template_id=template_id,
            response_model=response_model
        )

    async def update_template_structured(
        self,
        template_id: str, body: Dict[str, Any],
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Update a template.
        Args:
            template_id: ID of template that needs to be updated.
            body: Request body
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        return await self._primitives.update_template_structured(
            template_id=template_id, body=body,
            response_model=response_model
        )

    async def update_template_structured(
        self,
        template_id: str, body: Dict[str, Any],
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Update a template - synonym for PATCH /templates/{templateId}.
        Args:
            template_id: ID of template that needs to be updated.
            body: Request body
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        return await self._primitives.update_template_structured(
            template_id=template_id, body=body,
            response_model=response_model
        )

    async def list_network_volumes_structured(
        self,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Returns a list of network volumes.
        Args:
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        return await self._primitives.list_network_volumes_structured(
            
            response_model=response_model
        )

    async def create_network_volume_structured(
        self,
        body: Dict[str, Any],
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Create a new network volume.
        Args:
            body: Request body
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        return await self._primitives.create_network_volume_structured(
            body=body,
            response_model=response_model
        )

    async def get_network_volume_structured(
        self,
        network_volume_id: str,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Returns a single network volume.
        Args:
            network_volume_id: ID of network volume to return.
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        return await self._primitives.get_network_volume_structured(
            network_volume_id=network_volume_id,
            response_model=response_model
        )

    async def delete_network_volume_structured(
        self,
        network_volume_id: str,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Delete a network volume.
        Args:
            network_volume_id: Network volume ID to delete.
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        return await self._primitives.delete_network_volume_structured(
            network_volume_id=network_volume_id,
            response_model=response_model
        )

    async def update_network_volume_structured(
        self,
        network_volume_id: str, body: Dict[str, Any],
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Update a network volume.
        Args:
            network_volume_id: ID of network volume that needs to be updated.
            body: Request body
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        return await self._primitives.update_network_volume_structured(
            network_volume_id=network_volume_id, body=body,
            response_model=response_model
        )

    async def update_network_volume_structured(
        self,
        network_volume_id: str, body: Dict[str, Any],
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Update a network volume - synonym for PATCH /networkvolumes/{networkVolumeId}.
        Args:
            network_volume_id: ID of network volume that needs to be updated.
            body: Request body
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        return await self._primitives.update_network_volume_structured(
            network_volume_id=network_volume_id, body=body,
            response_model=response_model
        )

    async def list_container_registry_auths_structured(
        self,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Returns a list of container registry auths.
        Args:
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        return await self._primitives.list_container_registry_auths_structured(
            
            response_model=response_model
        )

    async def create_container_registry_auth_structured(
        self,
        body: Dict[str, Any],
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Create a new container registry auth.
        Args:
            body: Request body
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        return await self._primitives.create_container_registry_auth_structured(
            body=body,
            response_model=response_model
        )

    async def get_container_registry_auth_structured(
        self,
        container_registry_auth_id: str,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Returns a single container registry auth.
        Args:
            container_registry_auth_id: ID of container registry auth to return.
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        return await self._primitives.get_container_registry_auth_structured(
            container_registry_auth_id=container_registry_auth_id,
            response_model=response_model
        )

    async def delete_container_registry_auth_structured(
        self,
        container_registry_auth_id: str,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Delete a container registry auth.
        Args:
            container_registry_auth_id: Container registry auth ID to delete.
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        return await self._primitives.delete_container_registry_auth_structured(
            container_registry_auth_id=container_registry_auth_id,
            response_model=response_model
        )

    async def pod_billing_structured(
        self,
        bucket_size: Literal["hour", "day", "week", "month", "year"] = None, end_time: str = None, gpu_type_id: Literal["NVIDIA GeForce RTX 4090", "NVIDIA A40", "NVIDIA RTX A5000", "NVIDIA GeForce RTX 5090", "NVIDIA H100 80GB HBM3", "NVIDIA GeForce RTX 3090", "NVIDIA RTX A4500", "NVIDIA L40S", "NVIDIA H200", "NVIDIA L4", "NVIDIA RTX 6000 Ada Generation", "NVIDIA A100-SXM4-80GB", "NVIDIA RTX 4000 Ada Generation", "NVIDIA RTX A6000", "NVIDIA A100 80GB PCIe", "NVIDIA RTX 2000 Ada Generation", "NVIDIA RTX A4000", "NVIDIA RTX PRO 6000 Blackwell Server Edition", "NVIDIA H100 PCIe", "NVIDIA H100 NVL", "NVIDIA L40", "NVIDIA B200", "NVIDIA GeForce RTX 3080 Ti", "NVIDIA RTX PRO 6000 Blackwell Workstation Edition", "NVIDIA GeForce RTX 3080", "NVIDIA GeForce RTX 3070", "AMD Instinct MI300X OAM", "NVIDIA GeForce RTX 4080 SUPER", "Tesla V100-PCIE-16GB", "Tesla V100-SXM2-32GB", "NVIDIA RTX 5000 Ada Generation", "NVIDIA GeForce RTX 4070 Ti", "NVIDIA RTX 4000 SFF Ada Generation", "NVIDIA GeForce RTX 3090 Ti", "NVIDIA RTX A2000", "NVIDIA GeForce RTX 4080", "NVIDIA A30", "NVIDIA GeForce RTX 5080", "Tesla V100-FHHL-16GB", "NVIDIA H200 NVL", "Tesla V100-SXM2-16GB", "NVIDIA RTX PRO 6000 Blackwell Max-Q Workstation Edition", "NVIDIA A5000 Ada", "Tesla V100-PCIE-32GB", "NVIDIA  RTX A4500", "NVIDIA  A30", "NVIDIA GeForce RTX 3080TI", "Tesla T4", "NVIDIA RTX A30"] = None, grouping: Literal["podId", "gpuTypeId"] = None, pod_id: str = None, start_time: str = None,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Retrieve billing information about your Pods.
        Args:
            bucket_size: bucket_size
            end_time: end_time
            gpu_type_id: gpu_type_id
            grouping: grouping
            pod_id: pod_id
            start_time: start_time
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        return await self._primitives.pod_billing_structured(
            bucket_size=bucket_size, end_time=end_time, gpu_type_id=gpu_type_id, grouping=grouping, pod_id=pod_id, start_time=start_time,
            response_model=response_model
        )

    async def endpoint_billing_structured(
        self,
        bucket_size: Literal["hour", "day", "week", "month", "year"] = None, data_center_id: List[Literal["EU-RO-1", "CA-MTL-1", "EU-SE-1", "US-IL-1", "EUR-IS-1", "EU-CZ-1", "US-TX-3", "EUR-IS-2", "US-KS-2", "US-GA-2", "US-WA-1", "US-TX-1", "CA-MTL-3", "EU-NL-1", "US-TX-4", "US-CA-2", "US-NC-1", "OC-AU-1", "US-DE-1", "EUR-IS-3", "CA-MTL-2", "AP-JP-1", "EUR-NO-1", "EU-FR-1", "US-KS-3", "US-GA-1"]] = None, endpoint_id: str = None, end_time: str = None, gpu_type_id: List[Literal["NVIDIA GeForce RTX 4090", "NVIDIA A40", "NVIDIA RTX A5000", "NVIDIA GeForce RTX 5090", "NVIDIA H100 80GB HBM3", "NVIDIA GeForce RTX 3090", "NVIDIA RTX A4500", "NVIDIA L40S", "NVIDIA H200", "NVIDIA L4", "NVIDIA RTX 6000 Ada Generation", "NVIDIA A100-SXM4-80GB", "NVIDIA RTX 4000 Ada Generation", "NVIDIA RTX A6000", "NVIDIA A100 80GB PCIe", "NVIDIA RTX 2000 Ada Generation", "NVIDIA RTX A4000", "NVIDIA RTX PRO 6000 Blackwell Server Edition", "NVIDIA H100 PCIe", "NVIDIA H100 NVL", "NVIDIA L40", "NVIDIA B200", "NVIDIA GeForce RTX 3080 Ti", "NVIDIA RTX PRO 6000 Blackwell Workstation Edition", "NVIDIA GeForce RTX 3080", "NVIDIA GeForce RTX 3070", "AMD Instinct MI300X OAM", "NVIDIA GeForce RTX 4080 SUPER", "Tesla V100-PCIE-16GB", "Tesla V100-SXM2-32GB", "NVIDIA RTX 5000 Ada Generation", "NVIDIA GeForce RTX 4070 Ti", "NVIDIA RTX 4000 SFF Ada Generation", "NVIDIA GeForce RTX 3090 Ti", "NVIDIA RTX A2000", "NVIDIA GeForce RTX 4080", "NVIDIA A30", "NVIDIA GeForce RTX 5080", "Tesla V100-FHHL-16GB", "NVIDIA H200 NVL", "Tesla V100-SXM2-16GB", "NVIDIA RTX PRO 6000 Blackwell Max-Q Workstation Edition", "NVIDIA A5000 Ada", "Tesla V100-PCIE-32GB", "NVIDIA  RTX A4500", "NVIDIA  A30", "NVIDIA GeForce RTX 3080TI", "Tesla T4", "NVIDIA RTX A30"]] = None, grouping: Literal["endpointId", "podId", "gpuTypeId"] = None, image_name: str = None, start_time: str = None, template_id: str = None,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Retrieve billing information about your Serverless endpoints.
        Args:
            bucket_size: bucket_size
            data_center_id: data_center_id
            endpoint_id: endpoint_id
            end_time: end_time
            gpu_type_id: gpu_type_id
            grouping: grouping
            image_name: image_name
            start_time: start_time
            template_id: template_id
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        return await self._primitives.endpoint_billing_structured(
            bucket_size=bucket_size, data_center_id=data_center_id, endpoint_id=endpoint_id, end_time=end_time, gpu_type_id=gpu_type_id, grouping=grouping, image_name=image_name, start_time=start_time, template_id=template_id,
            response_model=response_model
        )

    async def network_volume_billing_structured(
        self,
        bucket_size: Literal["hour", "day", "week", "month", "year"] = None, end_time: str = None, start_time: str = None,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Retrieve billing information about your network volumes.
        Args:
            bucket_size: bucket_size
            end_time: end_time
            start_time: start_time
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        return await self._primitives.network_volume_billing_structured(
            bucket_size=bucket_size, end_time=end_time, start_time=start_time,
            response_model=response_model
        )
