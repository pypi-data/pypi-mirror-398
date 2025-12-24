"""
Layer 1: Primitives - Opinionated helper methods for runpod
These helpers provide higher-level abstractions over the raw API client.
Each method wraps a Layer 0 operation with the _structured suffix.
"""
from typing import Any, Dict, List, Literal, Optional, Type, TypeVar, Union
from pydantic import BaseModel
from .raw import *

T = TypeVar('T', bound=BaseModel)


class RunpodPrimitives:
    """
    Opinionated helper methods for runpod.

    Generated Layer 1 primitives for 37 operations.
    """

    def __init__(self, docs_client: DocsClient, pods_client: PodsClient, endpoints_client: EndpointsClient, templates_client: TemplatesClient, network_volumes_client: NetworkVolumesClient, container_registry_auths_client: ContainerRegistryAuthsClient, billing_client: BillingClient):
        self.docs_client = docs_client
        self.pods_client = pods_client
        self.endpoints_client = endpoints_client
        self.templates_client = templates_client
        self.network_volumes_client = network_volumes_client
        self.container_registry_auths_client = container_registry_auths_client
        self.billing_client = billing_client

    async def get_open_api_structured(
        self,
        
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        The OpenAPI 3.0 schema.
        This is a Layer 1 primitive that wraps the Layer 0 get_open_api() method.
        If response_model is provided, the response will be parsed into that Pydantic model.

        Args:
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        # Call Layer 0 method
        response = await self.docs_client.get_open_api(
            
        )

        # If no response model specified, return raw response
        if response_model is None:
            return response

        # Parse response into Pydantic model
        try:
            return response_model.model_validate(response)
        except Exception as e:
            raise ValueError(f"Failed to parse response as {response_model.__name__}: {e}")

    async def get_docs_structured(
        self,
        
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Interactive API documentation.
        This is a Layer 1 primitive that wraps the Layer 0 get_docs() method.
        If response_model is provided, the response will be parsed into that Pydantic model.

        Args:
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        # Call Layer 0 method
        response = await self.docs_client.get_docs(
            
        )

        # If no response model specified, return raw response
        if response_model is None:
            return response

        # Parse response into Pydantic model
        try:
            return response_model.model_validate(response)
        except Exception as e:
            raise ValueError(f"Failed to parse response as {response_model.__name__}: {e}")

    async def list_pods_structured(
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
        template_id: str = None,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Returns a list of Pods.
        This is a Layer 1 primitive that wraps the Layer 0 list_pods() method.
        If response_model is provided, the response will be parsed into that Pydantic model.

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
        # Call Layer 0 method
        response = await self.pods_client.list_pods(
            compute_type=compute_type,
            cpu_flavor_id=cpu_flavor_id,
            data_center_id=data_center_id,
            desired_status=desired_status,
            endpoint_id=endpoint_id,
            gpu_type_id=gpu_type_id,
            id_=id_,
            image_name=image_name,
            include_machine=include_machine,
            include_network_volume=include_network_volume,
            include_savings_plans=include_savings_plans,
            include_template=include_template,
            include_workers=include_workers,
            name=name,
            network_volume_id=network_volume_id,
            template_id=template_id
        )

        # If no response model specified, return raw response
        if response_model is None:
            return response

        # Parse response into Pydantic model
        try:
            return response_model.model_validate(response)
        except Exception as e:
            raise ValueError(f"Failed to parse response as {response_model.__name__}: {e}")

    async def create_pod_structured(
        self,
        body: Dict[str, Any],
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Creates a new [Pod](#/components/schemas/Pod) and optionally deploys it.
        This is a Layer 1 primitive that wraps the Layer 0 create_pod() method.
        If response_model is provided, the response will be parsed into that Pydantic model.

        Args:
            body: Request body
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        # Call Layer 0 method
        response = await self.pods_client.create_pod(
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

    async def get_pod_structured(
        self,
        pod_id: str,
        include_machine: bool = None,
        include_network_volume: bool = None,
        include_savings_plans: bool = None,
        include_template: bool = None,
        include_workers: bool = None,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Returns a single Pod.
        This is a Layer 1 primitive that wraps the Layer 0 get_pod() method.
        If response_model is provided, the response will be parsed into that Pydantic model.

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
        # Call Layer 0 method
        response = await self.pods_client.get_pod(
            pod_id=pod_id,
            include_machine=include_machine,
            include_network_volume=include_network_volume,
            include_savings_plans=include_savings_plans,
            include_template=include_template,
            include_workers=include_workers
        )

        # If no response model specified, return raw response
        if response_model is None:
            return response

        # Parse response into Pydantic model
        try:
            return response_model.model_validate(response)
        except Exception as e:
            raise ValueError(f"Failed to parse response as {response_model.__name__}: {e}")

    async def delete_pod_structured(
        self,
        pod_id: str,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Delete a Pod.
        This is a Layer 1 primitive that wraps the Layer 0 delete_pod() method.
        If response_model is provided, the response will be parsed into that Pydantic model.

        Args:
            pod_id: Pod ID to delete.
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        # Call Layer 0 method
        response = await self.pods_client.delete_pod(
            pod_id=pod_id
        )

        # If no response model specified, return raw response
        if response_model is None:
            return response

        # Parse response into Pydantic model
        try:
            return response_model.model_validate(response)
        except Exception as e:
            raise ValueError(f"Failed to parse response as {response_model.__name__}: {e}")

    async def update_pod_structured(
        self,
        pod_id: str,
        body: Dict[str, Any],
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Update a Pod, potentially triggering a reset.
        This is a Layer 1 primitive that wraps the Layer 0 update_pod() method.
        If response_model is provided, the response will be parsed into that Pydantic model.

        Args:
            pod_id: ID of Pod that needs to be updated.
            body: Request body
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        # Call Layer 0 method
        response = await self.pods_client.update_pod(
            pod_id=pod_id,
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

    async def update_pod_structured(
        self,
        pod_id: str,
        body: Dict[str, Any],
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Update a Pod - synonym for PATCH /pods/{podId}.
        This is a Layer 1 primitive that wraps the Layer 0 update_pod() method.
        If response_model is provided, the response will be parsed into that Pydantic model.

        Args:
            pod_id: ID of Pod that needs to be updated.
            body: Request body
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        # Call Layer 0 method
        response = await self.pods_client.update_pod(
            pod_id=pod_id,
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

    async def start_pod_structured(
        self,
        pod_id: str,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Start or resume a Pod.
        This is a Layer 1 primitive that wraps the Layer 0 start_pod() method.
        If response_model is provided, the response will be parsed into that Pydantic model.

        Args:
            pod_id: Pod ID to start.
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        # Call Layer 0 method
        response = await self.pods_client.start_pod(
            pod_id=pod_id
        )

        # If no response model specified, return raw response
        if response_model is None:
            return response

        # Parse response into Pydantic model
        try:
            return response_model.model_validate(response)
        except Exception as e:
            raise ValueError(f"Failed to parse response as {response_model.__name__}: {e}")

    async def stop_pod_structured(
        self,
        pod_id: str,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Stop a Pod.
        This is a Layer 1 primitive that wraps the Layer 0 stop_pod() method.
        If response_model is provided, the response will be parsed into that Pydantic model.

        Args:
            pod_id: Pod ID to stop.
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        # Call Layer 0 method
        response = await self.pods_client.stop_pod(
            pod_id=pod_id
        )

        # If no response model specified, return raw response
        if response_model is None:
            return response

        # Parse response into Pydantic model
        try:
            return response_model.model_validate(response)
        except Exception as e:
            raise ValueError(f"Failed to parse response as {response_model.__name__}: {e}")

    async def reset_pod_structured(
        self,
        pod_id: str,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Reset a Pod.
        This is a Layer 1 primitive that wraps the Layer 0 reset_pod() method.
        If response_model is provided, the response will be parsed into that Pydantic model.

        Args:
            pod_id: Pod ID to reset.
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        # Call Layer 0 method
        response = await self.pods_client.reset_pod(
            pod_id=pod_id
        )

        # If no response model specified, return raw response
        if response_model is None:
            return response

        # Parse response into Pydantic model
        try:
            return response_model.model_validate(response)
        except Exception as e:
            raise ValueError(f"Failed to parse response as {response_model.__name__}: {e}")

    async def restart_pod_structured(
        self,
        pod_id: str,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Restart a Pod.
        This is a Layer 1 primitive that wraps the Layer 0 restart_pod() method.
        If response_model is provided, the response will be parsed into that Pydantic model.

        Args:
            pod_id: Pod ID to restart.
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        # Call Layer 0 method
        response = await self.pods_client.restart_pod(
            pod_id=pod_id
        )

        # If no response model specified, return raw response
        if response_model is None:
            return response

        # Parse response into Pydantic model
        try:
            return response_model.model_validate(response)
        except Exception as e:
            raise ValueError(f"Failed to parse response as {response_model.__name__}: {e}")

    async def list_endpoints_structured(
        self,
        include_template: bool = None,
        include_workers: bool = None,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Returns a list of endpoints.
        This is a Layer 1 primitive that wraps the Layer 0 list_endpoints() method.
        If response_model is provided, the response will be parsed into that Pydantic model.

        Args:
            include_template: include_template
            include_workers: include_workers
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        # Call Layer 0 method
        response = await self.endpoints_client.list_endpoints(
            include_template=include_template,
            include_workers=include_workers
        )

        # If no response model specified, return raw response
        if response_model is None:
            return response

        # Parse response into Pydantic model
        try:
            return response_model.model_validate(response)
        except Exception as e:
            raise ValueError(f"Failed to parse response as {response_model.__name__}: {e}")

    async def create_endpoint_structured(
        self,
        body: Dict[str, Any],
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Create a new endpoint.
        This is a Layer 1 primitive that wraps the Layer 0 create_endpoint() method.
        If response_model is provided, the response will be parsed into that Pydantic model.

        Args:
            body: Request body
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        # Call Layer 0 method
        response = await self.endpoints_client.create_endpoint(
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

    async def get_endpoint_structured(
        self,
        endpoint_id: str,
        include_template: bool = None,
        include_workers: bool = None,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Returns a single endpoint.
        This is a Layer 1 primitive that wraps the Layer 0 get_endpoint() method.
        If response_model is provided, the response will be parsed into that Pydantic model.

        Args:
            endpoint_id: ID of endpoint to return.
            include_template: include_template
            include_workers: include_workers
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        # Call Layer 0 method
        response = await self.endpoints_client.get_endpoint(
            endpoint_id=endpoint_id,
            include_template=include_template,
            include_workers=include_workers
        )

        # If no response model specified, return raw response
        if response_model is None:
            return response

        # Parse response into Pydantic model
        try:
            return response_model.model_validate(response)
        except Exception as e:
            raise ValueError(f"Failed to parse response as {response_model.__name__}: {e}")

    async def delete_endpoint_structured(
        self,
        endpoint_id: str,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Delete an endpoint.
        This is a Layer 1 primitive that wraps the Layer 0 delete_endpoint() method.
        If response_model is provided, the response will be parsed into that Pydantic model.

        Args:
            endpoint_id: Endpoint ID to delete.
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        # Call Layer 0 method
        response = await self.endpoints_client.delete_endpoint(
            endpoint_id=endpoint_id
        )

        # If no response model specified, return raw response
        if response_model is None:
            return response

        # Parse response into Pydantic model
        try:
            return response_model.model_validate(response)
        except Exception as e:
            raise ValueError(f"Failed to parse response as {response_model.__name__}: {e}")

    async def update_endpoint_structured(
        self,
        endpoint_id: str,
        body: Dict[str, Any],
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Update an endpoint.
        This is a Layer 1 primitive that wraps the Layer 0 update_endpoint() method.
        If response_model is provided, the response will be parsed into that Pydantic model.

        Args:
            endpoint_id: ID of endpoint that needs to be updated.
            body: Request body
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        # Call Layer 0 method
        response = await self.endpoints_client.update_endpoint(
            endpoint_id=endpoint_id,
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

    async def update_endpoint_structured(
        self,
        endpoint_id: str,
        body: Dict[str, Any],
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Update an endpoint - synonym for PATCH /endpoints/{endpointId}.
        This is a Layer 1 primitive that wraps the Layer 0 update_endpoint() method.
        If response_model is provided, the response will be parsed into that Pydantic model.

        Args:
            endpoint_id: ID of endpoint that needs to be updated.
            body: Request body
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        # Call Layer 0 method
        response = await self.endpoints_client.update_endpoint(
            endpoint_id=endpoint_id,
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

    async def list_templates_structured(
        self,
        include_endpoint_bound_templates: bool = None,
        include_public_templates: bool = None,
        include_runpod_templates: bool = None,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Returns a list of templates.
        This is a Layer 1 primitive that wraps the Layer 0 list_templates() method.
        If response_model is provided, the response will be parsed into that Pydantic model.

        Args:
            include_endpoint_bound_templates: include_endpoint_bound_templates
            include_public_templates: include_public_templates
            include_runpod_templates: include_runpod_templates
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        # Call Layer 0 method
        response = await self.templates_client.list_templates(
            include_endpoint_bound_templates=include_endpoint_bound_templates,
            include_public_templates=include_public_templates,
            include_runpod_templates=include_runpod_templates
        )

        # If no response model specified, return raw response
        if response_model is None:
            return response

        # Parse response into Pydantic model
        try:
            return response_model.model_validate(response)
        except Exception as e:
            raise ValueError(f"Failed to parse response as {response_model.__name__}: {e}")

    async def create_template_structured(
        self,
        body: Dict[str, Any],
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Create a new template.
        This is a Layer 1 primitive that wraps the Layer 0 create_template() method.
        If response_model is provided, the response will be parsed into that Pydantic model.

        Args:
            body: Request body
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        # Call Layer 0 method
        response = await self.templates_client.create_template(
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

    async def get_template_structured(
        self,
        template_id: str,
        include_endpoint_bound_templates: bool = None,
        include_public_templates: bool = None,
        include_runpod_templates: bool = None,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Returns a single template.
        This is a Layer 1 primitive that wraps the Layer 0 get_template() method.
        If response_model is provided, the response will be parsed into that Pydantic model.

        Args:
            template_id: ID of template to return.
            include_endpoint_bound_templates: include_endpoint_bound_templates
            include_public_templates: include_public_templates
            include_runpod_templates: include_runpod_templates
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        # Call Layer 0 method
        response = await self.templates_client.get_template(
            template_id=template_id,
            include_endpoint_bound_templates=include_endpoint_bound_templates,
            include_public_templates=include_public_templates,
            include_runpod_templates=include_runpod_templates
        )

        # If no response model specified, return raw response
        if response_model is None:
            return response

        # Parse response into Pydantic model
        try:
            return response_model.model_validate(response)
        except Exception as e:
            raise ValueError(f"Failed to parse response as {response_model.__name__}: {e}")

    async def delete_template_structured(
        self,
        template_id: str,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Delete a template.
        This is a Layer 1 primitive that wraps the Layer 0 delete_template() method.
        If response_model is provided, the response will be parsed into that Pydantic model.

        Args:
            template_id: Template ID to delete.
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        # Call Layer 0 method
        response = await self.templates_client.delete_template(
            template_id=template_id
        )

        # If no response model specified, return raw response
        if response_model is None:
            return response

        # Parse response into Pydantic model
        try:
            return response_model.model_validate(response)
        except Exception as e:
            raise ValueError(f"Failed to parse response as {response_model.__name__}: {e}")

    async def update_template_structured(
        self,
        template_id: str,
        body: Dict[str, Any],
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Update a template.
        This is a Layer 1 primitive that wraps the Layer 0 update_template() method.
        If response_model is provided, the response will be parsed into that Pydantic model.

        Args:
            template_id: ID of template that needs to be updated.
            body: Request body
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        # Call Layer 0 method
        response = await self.templates_client.update_template(
            template_id=template_id,
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

    async def update_template_structured(
        self,
        template_id: str,
        body: Dict[str, Any],
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Update a template - synonym for PATCH /templates/{templateId}.
        This is a Layer 1 primitive that wraps the Layer 0 update_template() method.
        If response_model is provided, the response will be parsed into that Pydantic model.

        Args:
            template_id: ID of template that needs to be updated.
            body: Request body
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        # Call Layer 0 method
        response = await self.templates_client.update_template(
            template_id=template_id,
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

    async def list_network_volumes_structured(
        self,
        
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Returns a list of network volumes.
        This is a Layer 1 primitive that wraps the Layer 0 list_network_volumes() method.
        If response_model is provided, the response will be parsed into that Pydantic model.

        Args:
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        # Call Layer 0 method
        response = await self.network_volumes_client.list_network_volumes(
            
        )

        # If no response model specified, return raw response
        if response_model is None:
            return response

        # Parse response into Pydantic model
        try:
            return response_model.model_validate(response)
        except Exception as e:
            raise ValueError(f"Failed to parse response as {response_model.__name__}: {e}")

    async def create_network_volume_structured(
        self,
        body: Dict[str, Any],
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Create a new network volume.
        This is a Layer 1 primitive that wraps the Layer 0 create_network_volume() method.
        If response_model is provided, the response will be parsed into that Pydantic model.

        Args:
            body: Request body
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        # Call Layer 0 method
        response = await self.network_volumes_client.create_network_volume(
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

    async def get_network_volume_structured(
        self,
        network_volume_id: str,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Returns a single network volume.
        This is a Layer 1 primitive that wraps the Layer 0 get_network_volume() method.
        If response_model is provided, the response will be parsed into that Pydantic model.

        Args:
            network_volume_id: ID of network volume to return.
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        # Call Layer 0 method
        response = await self.network_volumes_client.get_network_volume(
            network_volume_id=network_volume_id
        )

        # If no response model specified, return raw response
        if response_model is None:
            return response

        # Parse response into Pydantic model
        try:
            return response_model.model_validate(response)
        except Exception as e:
            raise ValueError(f"Failed to parse response as {response_model.__name__}: {e}")

    async def delete_network_volume_structured(
        self,
        network_volume_id: str,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Delete a network volume.
        This is a Layer 1 primitive that wraps the Layer 0 delete_network_volume() method.
        If response_model is provided, the response will be parsed into that Pydantic model.

        Args:
            network_volume_id: Network volume ID to delete.
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        # Call Layer 0 method
        response = await self.network_volumes_client.delete_network_volume(
            network_volume_id=network_volume_id
        )

        # If no response model specified, return raw response
        if response_model is None:
            return response

        # Parse response into Pydantic model
        try:
            return response_model.model_validate(response)
        except Exception as e:
            raise ValueError(f"Failed to parse response as {response_model.__name__}: {e}")

    async def update_network_volume_structured(
        self,
        network_volume_id: str,
        body: Dict[str, Any],
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Update a network volume.
        This is a Layer 1 primitive that wraps the Layer 0 update_network_volume() method.
        If response_model is provided, the response will be parsed into that Pydantic model.

        Args:
            network_volume_id: ID of network volume that needs to be updated.
            body: Request body
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        # Call Layer 0 method
        response = await self.network_volumes_client.update_network_volume(
            network_volume_id=network_volume_id,
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

    async def update_network_volume_structured(
        self,
        network_volume_id: str,
        body: Dict[str, Any],
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Update a network volume - synonym for PATCH /networkvolumes/{networkVolumeId}.
        This is a Layer 1 primitive that wraps the Layer 0 update_network_volume() method.
        If response_model is provided, the response will be parsed into that Pydantic model.

        Args:
            network_volume_id: ID of network volume that needs to be updated.
            body: Request body
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        # Call Layer 0 method
        response = await self.network_volumes_client.update_network_volume(
            network_volume_id=network_volume_id,
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

    async def list_container_registry_auths_structured(
        self,
        
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Returns a list of container registry auths.
        This is a Layer 1 primitive that wraps the Layer 0 list_container_registry_auths() method.
        If response_model is provided, the response will be parsed into that Pydantic model.

        Args:
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        # Call Layer 0 method
        response = await self.container_registry_auths_client.list_container_registry_auths(
            
        )

        # If no response model specified, return raw response
        if response_model is None:
            return response

        # Parse response into Pydantic model
        try:
            return response_model.model_validate(response)
        except Exception as e:
            raise ValueError(f"Failed to parse response as {response_model.__name__}: {e}")

    async def create_container_registry_auth_structured(
        self,
        body: Dict[str, Any],
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Create a new container registry auth.
        This is a Layer 1 primitive that wraps the Layer 0 create_container_registry_auth() method.
        If response_model is provided, the response will be parsed into that Pydantic model.

        Args:
            body: Request body
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        # Call Layer 0 method
        response = await self.container_registry_auths_client.create_container_registry_auth(
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

    async def get_container_registry_auth_structured(
        self,
        container_registry_auth_id: str,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Returns a single container registry auth.
        This is a Layer 1 primitive that wraps the Layer 0 get_container_registry_auth() method.
        If response_model is provided, the response will be parsed into that Pydantic model.

        Args:
            container_registry_auth_id: ID of container registry auth to return.
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        # Call Layer 0 method
        response = await self.container_registry_auths_client.get_container_registry_auth(
            container_registry_auth_id=container_registry_auth_id
        )

        # If no response model specified, return raw response
        if response_model is None:
            return response

        # Parse response into Pydantic model
        try:
            return response_model.model_validate(response)
        except Exception as e:
            raise ValueError(f"Failed to parse response as {response_model.__name__}: {e}")

    async def delete_container_registry_auth_structured(
        self,
        container_registry_auth_id: str,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Delete a container registry auth.
        This is a Layer 1 primitive that wraps the Layer 0 delete_container_registry_auth() method.
        If response_model is provided, the response will be parsed into that Pydantic model.

        Args:
            container_registry_auth_id: Container registry auth ID to delete.
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        # Call Layer 0 method
        response = await self.container_registry_auths_client.delete_container_registry_auth(
            container_registry_auth_id=container_registry_auth_id
        )

        # If no response model specified, return raw response
        if response_model is None:
            return response

        # Parse response into Pydantic model
        try:
            return response_model.model_validate(response)
        except Exception as e:
            raise ValueError(f"Failed to parse response as {response_model.__name__}: {e}")

    async def pod_billing_structured(
        self,
        bucket_size: Literal["hour", "day", "week", "month", "year"] = None,
        end_time: str = None,
        gpu_type_id: Literal["NVIDIA GeForce RTX 4090", "NVIDIA A40", "NVIDIA RTX A5000", "NVIDIA GeForce RTX 5090", "NVIDIA H100 80GB HBM3", "NVIDIA GeForce RTX 3090", "NVIDIA RTX A4500", "NVIDIA L40S", "NVIDIA H200", "NVIDIA L4", "NVIDIA RTX 6000 Ada Generation", "NVIDIA A100-SXM4-80GB", "NVIDIA RTX 4000 Ada Generation", "NVIDIA RTX A6000", "NVIDIA A100 80GB PCIe", "NVIDIA RTX 2000 Ada Generation", "NVIDIA RTX A4000", "NVIDIA RTX PRO 6000 Blackwell Server Edition", "NVIDIA H100 PCIe", "NVIDIA H100 NVL", "NVIDIA L40", "NVIDIA B200", "NVIDIA GeForce RTX 3080 Ti", "NVIDIA RTX PRO 6000 Blackwell Workstation Edition", "NVIDIA GeForce RTX 3080", "NVIDIA GeForce RTX 3070", "AMD Instinct MI300X OAM", "NVIDIA GeForce RTX 4080 SUPER", "Tesla V100-PCIE-16GB", "Tesla V100-SXM2-32GB", "NVIDIA RTX 5000 Ada Generation", "NVIDIA GeForce RTX 4070 Ti", "NVIDIA RTX 4000 SFF Ada Generation", "NVIDIA GeForce RTX 3090 Ti", "NVIDIA RTX A2000", "NVIDIA GeForce RTX 4080", "NVIDIA A30", "NVIDIA GeForce RTX 5080", "Tesla V100-FHHL-16GB", "NVIDIA H200 NVL", "Tesla V100-SXM2-16GB", "NVIDIA RTX PRO 6000 Blackwell Max-Q Workstation Edition", "NVIDIA A5000 Ada", "Tesla V100-PCIE-32GB", "NVIDIA  RTX A4500", "NVIDIA  A30", "NVIDIA GeForce RTX 3080TI", "Tesla T4", "NVIDIA RTX A30"] = None,
        grouping: Literal["podId", "gpuTypeId"] = None,
        pod_id: str = None,
        start_time: str = None,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Retrieve billing information about your Pods.
        This is a Layer 1 primitive that wraps the Layer 0 pod_billing() method.
        If response_model is provided, the response will be parsed into that Pydantic model.

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
        # Call Layer 0 method
        response = await self.billing_client.pod_billing(
            bucket_size=bucket_size,
            end_time=end_time,
            gpu_type_id=gpu_type_id,
            grouping=grouping,
            pod_id=pod_id,
            start_time=start_time
        )

        # If no response model specified, return raw response
        if response_model is None:
            return response

        # Parse response into Pydantic model
        try:
            return response_model.model_validate(response)
        except Exception as e:
            raise ValueError(f"Failed to parse response as {response_model.__name__}: {e}")

    async def endpoint_billing_structured(
        self,
        bucket_size: Literal["hour", "day", "week", "month", "year"] = None,
        data_center_id: List[Literal["EU-RO-1", "CA-MTL-1", "EU-SE-1", "US-IL-1", "EUR-IS-1", "EU-CZ-1", "US-TX-3", "EUR-IS-2", "US-KS-2", "US-GA-2", "US-WA-1", "US-TX-1", "CA-MTL-3", "EU-NL-1", "US-TX-4", "US-CA-2", "US-NC-1", "OC-AU-1", "US-DE-1", "EUR-IS-3", "CA-MTL-2", "AP-JP-1", "EUR-NO-1", "EU-FR-1", "US-KS-3", "US-GA-1"]] = None,
        endpoint_id: str = None,
        end_time: str = None,
        gpu_type_id: List[Literal["NVIDIA GeForce RTX 4090", "NVIDIA A40", "NVIDIA RTX A5000", "NVIDIA GeForce RTX 5090", "NVIDIA H100 80GB HBM3", "NVIDIA GeForce RTX 3090", "NVIDIA RTX A4500", "NVIDIA L40S", "NVIDIA H200", "NVIDIA L4", "NVIDIA RTX 6000 Ada Generation", "NVIDIA A100-SXM4-80GB", "NVIDIA RTX 4000 Ada Generation", "NVIDIA RTX A6000", "NVIDIA A100 80GB PCIe", "NVIDIA RTX 2000 Ada Generation", "NVIDIA RTX A4000", "NVIDIA RTX PRO 6000 Blackwell Server Edition", "NVIDIA H100 PCIe", "NVIDIA H100 NVL", "NVIDIA L40", "NVIDIA B200", "NVIDIA GeForce RTX 3080 Ti", "NVIDIA RTX PRO 6000 Blackwell Workstation Edition", "NVIDIA GeForce RTX 3080", "NVIDIA GeForce RTX 3070", "AMD Instinct MI300X OAM", "NVIDIA GeForce RTX 4080 SUPER", "Tesla V100-PCIE-16GB", "Tesla V100-SXM2-32GB", "NVIDIA RTX 5000 Ada Generation", "NVIDIA GeForce RTX 4070 Ti", "NVIDIA RTX 4000 SFF Ada Generation", "NVIDIA GeForce RTX 3090 Ti", "NVIDIA RTX A2000", "NVIDIA GeForce RTX 4080", "NVIDIA A30", "NVIDIA GeForce RTX 5080", "Tesla V100-FHHL-16GB", "NVIDIA H200 NVL", "Tesla V100-SXM2-16GB", "NVIDIA RTX PRO 6000 Blackwell Max-Q Workstation Edition", "NVIDIA A5000 Ada", "Tesla V100-PCIE-32GB", "NVIDIA  RTX A4500", "NVIDIA  A30", "NVIDIA GeForce RTX 3080TI", "Tesla T4", "NVIDIA RTX A30"]] = None,
        grouping: Literal["endpointId", "podId", "gpuTypeId"] = None,
        image_name: str = None,
        start_time: str = None,
        template_id: str = None,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Retrieve billing information about your Serverless endpoints.
        This is a Layer 1 primitive that wraps the Layer 0 endpoint_billing() method.
        If response_model is provided, the response will be parsed into that Pydantic model.

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
        # Call Layer 0 method
        response = await self.billing_client.endpoint_billing(
            bucket_size=bucket_size,
            data_center_id=data_center_id,
            endpoint_id=endpoint_id,
            end_time=end_time,
            gpu_type_id=gpu_type_id,
            grouping=grouping,
            image_name=image_name,
            start_time=start_time,
            template_id=template_id
        )

        # If no response model specified, return raw response
        if response_model is None:
            return response

        # Parse response into Pydantic model
        try:
            return response_model.model_validate(response)
        except Exception as e:
            raise ValueError(f"Failed to parse response as {response_model.__name__}: {e}")

    async def network_volume_billing_structured(
        self,
        bucket_size: Literal["hour", "day", "week", "month", "year"] = None,
        end_time: str = None,
        start_time: str = None,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Retrieve billing information about your network volumes.
        This is a Layer 1 primitive that wraps the Layer 0 network_volume_billing() method.
        If response_model is provided, the response will be parsed into that Pydantic model.

        Args:
            bucket_size: bucket_size
            end_time: end_time
            start_time: start_time
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        # Call Layer 0 method
        response = await self.billing_client.network_volume_billing(
            bucket_size=bucket_size,
            end_time=end_time,
            start_time=start_time
        )

        # If no response model specified, return raw response
        if response_model is None:
            return response

        # Parse response into Pydantic model
        try:
            return response_model.model_validate(response)
        except Exception as e:
            raise ValueError(f"Failed to parse response as {response_model.__name__}: {e}")
