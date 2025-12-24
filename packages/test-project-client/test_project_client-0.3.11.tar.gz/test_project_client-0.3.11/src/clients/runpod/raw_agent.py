"""
Layer 0 Agent: Environment-based client wrapper for runpod
Automatically loads credentials from environment variables for easy integration
with AI Agent frameworks (LangChain, CrewAI, Madison, etc.)
"""
import os
from typing import Any, Dict, List, Literal, Optional, Union
from .raw import *


class RawAgent:
    """
    Agent-ready wrapper for runpod raw API client.

    Automatically loads credentials from environment variables:
    - RUNPOD_API_KEY: API key/token for authentication
    - RUNPOD_BASE_URL: Base URL for the API (optional, has default)

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
        self.api_key = api_key or os.environ.get("RUNPOD_API_KEY")
        self.base_url = base_url or os.environ.get("RUNPOD_BASE_URL", "https://rest.runpod.io/v1")

        if not self.api_key:
            raise ValueError(
                "API key is required. Set RUNPOD_API_KEY environment variable "
                "or pass api_key parameter."
            )

        # Initialize raw client(s)
        self._docs = DocsClient(
            base_url=self.base_url,
            token=self.api_key
        )
        self._pods = PodsClient(
            base_url=self.base_url,
            token=self.api_key
        )
        self._endpoints = EndpointsClient(
            base_url=self.base_url,
            token=self.api_key
        )
        self._templates = TemplatesClient(
            base_url=self.base_url,
            token=self.api_key
        )
        self._network_volumes = NetworkVolumesClient(
            base_url=self.base_url,
            token=self.api_key
        )
        self._container_registry_auths = ContainerRegistryAuthsClient(
            base_url=self.base_url,
            token=self.api_key
        )
        self._billing = BillingClient(
            base_url=self.base_url,
            token=self.api_key
        )

    # ─────────────────────────────────────────────────────────────────────────────
    # docs operations
    # ─────────────────────────────────────────────────────────────────────────────

    async def get_open_api(self) -> Dict[str, Any]:
        """The OpenAPI 3.0 schema."""
        return await self._docs.get_open_api()

    async def get_docs(self) -> Dict[str, Any]:
        """Interactive API documentation."""
        return await self._docs.get_docs()

    # ─────────────────────────────────────────────────────────────────────────────
    # pods operations
    # ─────────────────────────────────────────────────────────────────────────────

    async def list_pods(self, compute_type: Literal["GPU", "CPU"] = None, cpu_flavor_id: List[str] = None, data_center_id: List[str] = None, desired_status: Literal["RUNNING", "EXITED", "TERMINATED"] = None, endpoint_id: str = None, gpu_type_id: List[str] = None, id_: str = None, image_name: str = None, include_machine: bool = None, include_network_volume: bool = None, include_savings_plans: bool = None, include_template: bool = None, include_workers: bool = None, name: str = None, network_volume_id: str = None, template_id: str = None) -> List[Dict[str, Any]]:
        """Returns a list of Pods."""
        return await self._pods.list_pods(compute_type=compute_type, cpu_flavor_id=cpu_flavor_id, data_center_id=data_center_id, desired_status=desired_status, endpoint_id=endpoint_id, gpu_type_id=gpu_type_id, id_=id_, image_name=image_name, include_machine=include_machine, include_network_volume=include_network_volume, include_savings_plans=include_savings_plans, include_template=include_template, include_workers=include_workers, name=name, network_volume_id=network_volume_id, template_id=template_id)

    async def create_pod(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Creates a new [Pod](#/components/schemas/Pod) and optionally deploys it."""
        return await self._pods.create_pod(body=body)

    async def get_pod(self, pod_id: str, include_machine: bool = None, include_network_volume: bool = None, include_savings_plans: bool = None, include_template: bool = None, include_workers: bool = None) -> Dict[str, Any]:
        """Returns a single Pod."""
        return await self._pods.get_pod(pod_id=pod_id, include_machine=include_machine, include_network_volume=include_network_volume, include_savings_plans=include_savings_plans, include_template=include_template, include_workers=include_workers)

    async def delete_pod(self, pod_id: str) -> Dict[str, Any]:
        """Delete a Pod."""
        return await self._pods.delete_pod(pod_id=pod_id)

    async def update_pod(self, pod_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """Update a Pod, potentially triggering a reset."""
        return await self._pods.update_pod(pod_id=pod_id, body=body)

    async def update_pod(self, pod_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """Update a Pod - synonym for PATCH /pods/{podId}."""
        return await self._pods.update_pod(pod_id=pod_id, body=body)

    async def start_pod(self, pod_id: str) -> Dict[str, Any]:
        """Start or resume a Pod."""
        return await self._pods.start_pod(pod_id=pod_id)

    async def stop_pod(self, pod_id: str) -> Dict[str, Any]:
        """Stop a Pod."""
        return await self._pods.stop_pod(pod_id=pod_id)

    async def reset_pod(self, pod_id: str) -> Dict[str, Any]:
        """Reset a Pod."""
        return await self._pods.reset_pod(pod_id=pod_id)

    async def restart_pod(self, pod_id: str) -> Dict[str, Any]:
        """Restart a Pod."""
        return await self._pods.restart_pod(pod_id=pod_id)

    # ─────────────────────────────────────────────────────────────────────────────
    # endpoints operations
    # ─────────────────────────────────────────────────────────────────────────────

    async def list_endpoints(self, include_template: bool = None, include_workers: bool = None) -> List[Dict[str, Any]]:
        """Returns a list of endpoints."""
        return await self._endpoints.list_endpoints(include_template=include_template, include_workers=include_workers)

    async def create_endpoint(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new endpoint."""
        return await self._endpoints.create_endpoint(body=body)

    async def get_endpoint(self, endpoint_id: str, include_template: bool = None, include_workers: bool = None) -> Dict[str, Any]:
        """Returns a single endpoint."""
        return await self._endpoints.get_endpoint(endpoint_id=endpoint_id, include_template=include_template, include_workers=include_workers)

    async def delete_endpoint(self, endpoint_id: str) -> Dict[str, Any]:
        """Delete an endpoint."""
        return await self._endpoints.delete_endpoint(endpoint_id=endpoint_id)

    async def update_endpoint(self, endpoint_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """Update an endpoint."""
        return await self._endpoints.update_endpoint(endpoint_id=endpoint_id, body=body)

    async def update_endpoint(self, endpoint_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """Update an endpoint - synonym for PATCH /endpoints/{endpointId}."""
        return await self._endpoints.update_endpoint(endpoint_id=endpoint_id, body=body)

    # ─────────────────────────────────────────────────────────────────────────────
    # templates operations
    # ─────────────────────────────────────────────────────────────────────────────

    async def list_templates(self, include_endpoint_bound_templates: bool = None, include_public_templates: bool = None, include_runpod_templates: bool = None) -> List[Dict[str, Any]]:
        """Returns a list of templates."""
        return await self._templates.list_templates(include_endpoint_bound_templates=include_endpoint_bound_templates, include_public_templates=include_public_templates, include_runpod_templates=include_runpod_templates)

    async def create_template(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new template."""
        return await self._templates.create_template(body=body)

    async def get_template(self, template_id: str, include_endpoint_bound_templates: bool = None, include_public_templates: bool = None, include_runpod_templates: bool = None) -> Dict[str, Any]:
        """Returns a single template."""
        return await self._templates.get_template(template_id=template_id, include_endpoint_bound_templates=include_endpoint_bound_templates, include_public_templates=include_public_templates, include_runpod_templates=include_runpod_templates)

    async def delete_template(self, template_id: str) -> Dict[str, Any]:
        """Delete a template."""
        return await self._templates.delete_template(template_id=template_id)

    async def update_template(self, template_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """Update a template."""
        return await self._templates.update_template(template_id=template_id, body=body)

    async def update_template(self, template_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """Update a template - synonym for PATCH /templates/{templateId}."""
        return await self._templates.update_template(template_id=template_id, body=body)

    # ─────────────────────────────────────────────────────────────────────────────
    # network volumes operations
    # ─────────────────────────────────────────────────────────────────────────────

    async def list_network_volumes(self) -> List[Dict[str, Any]]:
        """Returns a list of network volumes."""
        return await self._network_volumes.list_network_volumes()

    async def create_network_volume(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new network volume."""
        return await self._network_volumes.create_network_volume(body=body)

    async def get_network_volume(self, network_volume_id: str) -> Dict[str, Any]:
        """Returns a single network volume."""
        return await self._network_volumes.get_network_volume(network_volume_id=network_volume_id)

    async def delete_network_volume(self, network_volume_id: str) -> Dict[str, Any]:
        """Delete a network volume."""
        return await self._network_volumes.delete_network_volume(network_volume_id=network_volume_id)

    async def update_network_volume(self, network_volume_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """Update a network volume."""
        return await self._network_volumes.update_network_volume(network_volume_id=network_volume_id, body=body)

    async def update_network_volume(self, network_volume_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """Update a network volume - synonym for PATCH /networkvolumes/{networkVolumeId}."""
        return await self._network_volumes.update_network_volume(network_volume_id=network_volume_id, body=body)

    # ─────────────────────────────────────────────────────────────────────────────
    # container registry auths operations
    # ─────────────────────────────────────────────────────────────────────────────

    async def list_container_registry_auths(self) -> List[Dict[str, Any]]:
        """Returns a list of container registry auths."""
        return await self._container_registry_auths.list_container_registry_auths()

    async def create_container_registry_auth(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new container registry auth."""
        return await self._container_registry_auths.create_container_registry_auth(body=body)

    async def get_container_registry_auth(self, container_registry_auth_id: str) -> Dict[str, Any]:
        """Returns a single container registry auth."""
        return await self._container_registry_auths.get_container_registry_auth(container_registry_auth_id=container_registry_auth_id)

    async def delete_container_registry_auth(self, container_registry_auth_id: str) -> Dict[str, Any]:
        """Delete a container registry auth."""
        return await self._container_registry_auths.delete_container_registry_auth(container_registry_auth_id=container_registry_auth_id)

    # ─────────────────────────────────────────────────────────────────────────────
    # billing operations
    # ─────────────────────────────────────────────────────────────────────────────

    async def pod_billing(self, bucket_size: Literal["hour", "day", "week", "month", "year"] = None, end_time: str = None, gpu_type_id: Literal["NVIDIA GeForce RTX 4090", "NVIDIA A40", "NVIDIA RTX A5000", "NVIDIA GeForce RTX 5090", "NVIDIA H100 80GB HBM3", "NVIDIA GeForce RTX 3090", "NVIDIA RTX A4500", "NVIDIA L40S", "NVIDIA H200", "NVIDIA L4", "NVIDIA RTX 6000 Ada Generation", "NVIDIA A100-SXM4-80GB", "NVIDIA RTX 4000 Ada Generation", "NVIDIA RTX A6000", "NVIDIA A100 80GB PCIe", "NVIDIA RTX 2000 Ada Generation", "NVIDIA RTX A4000", "NVIDIA RTX PRO 6000 Blackwell Server Edition", "NVIDIA H100 PCIe", "NVIDIA H100 NVL", "NVIDIA L40", "NVIDIA B200", "NVIDIA GeForce RTX 3080 Ti", "NVIDIA RTX PRO 6000 Blackwell Workstation Edition", "NVIDIA GeForce RTX 3080", "NVIDIA GeForce RTX 3070", "AMD Instinct MI300X OAM", "NVIDIA GeForce RTX 4080 SUPER", "Tesla V100-PCIE-16GB", "Tesla V100-SXM2-32GB", "NVIDIA RTX 5000 Ada Generation", "NVIDIA GeForce RTX 4070 Ti", "NVIDIA RTX 4000 SFF Ada Generation", "NVIDIA GeForce RTX 3090 Ti", "NVIDIA RTX A2000", "NVIDIA GeForce RTX 4080", "NVIDIA A30", "NVIDIA GeForce RTX 5080", "Tesla V100-FHHL-16GB", "NVIDIA H200 NVL", "Tesla V100-SXM2-16GB", "NVIDIA RTX PRO 6000 Blackwell Max-Q Workstation Edition", "NVIDIA A5000 Ada", "Tesla V100-PCIE-32GB", "NVIDIA  RTX A4500", "NVIDIA  A30", "NVIDIA GeForce RTX 3080TI", "Tesla T4", "NVIDIA RTX A30"] = None, grouping: Literal["podId", "gpuTypeId"] = None, pod_id: str = None, start_time: str = None) -> List[Dict[str, Any]]:
        """Retrieve billing information about your Pods."""
        return await self._billing.pod_billing(bucket_size=bucket_size, end_time=end_time, gpu_type_id=gpu_type_id, grouping=grouping, pod_id=pod_id, start_time=start_time)

    async def endpoint_billing(self, bucket_size: Literal["hour", "day", "week", "month", "year"] = None, data_center_id: List[Literal["EU-RO-1", "CA-MTL-1", "EU-SE-1", "US-IL-1", "EUR-IS-1", "EU-CZ-1", "US-TX-3", "EUR-IS-2", "US-KS-2", "US-GA-2", "US-WA-1", "US-TX-1", "CA-MTL-3", "EU-NL-1", "US-TX-4", "US-CA-2", "US-NC-1", "OC-AU-1", "US-DE-1", "EUR-IS-3", "CA-MTL-2", "AP-JP-1", "EUR-NO-1", "EU-FR-1", "US-KS-3", "US-GA-1"]] = None, endpoint_id: str = None, end_time: str = None, gpu_type_id: List[Literal["NVIDIA GeForce RTX 4090", "NVIDIA A40", "NVIDIA RTX A5000", "NVIDIA GeForce RTX 5090", "NVIDIA H100 80GB HBM3", "NVIDIA GeForce RTX 3090", "NVIDIA RTX A4500", "NVIDIA L40S", "NVIDIA H200", "NVIDIA L4", "NVIDIA RTX 6000 Ada Generation", "NVIDIA A100-SXM4-80GB", "NVIDIA RTX 4000 Ada Generation", "NVIDIA RTX A6000", "NVIDIA A100 80GB PCIe", "NVIDIA RTX 2000 Ada Generation", "NVIDIA RTX A4000", "NVIDIA RTX PRO 6000 Blackwell Server Edition", "NVIDIA H100 PCIe", "NVIDIA H100 NVL", "NVIDIA L40", "NVIDIA B200", "NVIDIA GeForce RTX 3080 Ti", "NVIDIA RTX PRO 6000 Blackwell Workstation Edition", "NVIDIA GeForce RTX 3080", "NVIDIA GeForce RTX 3070", "AMD Instinct MI300X OAM", "NVIDIA GeForce RTX 4080 SUPER", "Tesla V100-PCIE-16GB", "Tesla V100-SXM2-32GB", "NVIDIA RTX 5000 Ada Generation", "NVIDIA GeForce RTX 4070 Ti", "NVIDIA RTX 4000 SFF Ada Generation", "NVIDIA GeForce RTX 3090 Ti", "NVIDIA RTX A2000", "NVIDIA GeForce RTX 4080", "NVIDIA A30", "NVIDIA GeForce RTX 5080", "Tesla V100-FHHL-16GB", "NVIDIA H200 NVL", "Tesla V100-SXM2-16GB", "NVIDIA RTX PRO 6000 Blackwell Max-Q Workstation Edition", "NVIDIA A5000 Ada", "Tesla V100-PCIE-32GB", "NVIDIA  RTX A4500", "NVIDIA  A30", "NVIDIA GeForce RTX 3080TI", "Tesla T4", "NVIDIA RTX A30"]] = None, grouping: Literal["endpointId", "podId", "gpuTypeId"] = None, image_name: str = None, start_time: str = None, template_id: str = None) -> List[Dict[str, Any]]:
        """Retrieve billing information about your Serverless endpoints."""
        return await self._billing.endpoint_billing(bucket_size=bucket_size, data_center_id=data_center_id, endpoint_id=endpoint_id, end_time=end_time, gpu_type_id=gpu_type_id, grouping=grouping, image_name=image_name, start_time=start_time, template_id=template_id)

    async def network_volume_billing(self, bucket_size: Literal["hour", "day", "week", "month", "year"] = None, end_time: str = None, start_time: str = None) -> List[Dict[str, Any]]:
        """Retrieve billing information about your network volumes."""
        return await self._billing.network_volume_billing(bucket_size=bucket_size, end_time=end_time, start_time=start_time)
