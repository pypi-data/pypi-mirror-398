from typing import Any, Dict, List, Literal, Optional, Union
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict

class Pods(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class Pod(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    adjusted_cost_per_hr: float = Field(
        None, alias="adjustedCostPerHr"
    )
    ai_api_id: str = Field(
        None, alias="aiApiId"
    )
    consumer_user_id: str = Field(
        None, alias="consumerUserId"
    )
    container_disk_in_gb: int = Field(
        None, alias="containerDiskInGb"
    )
    container_registry_auth_id: str = Field(
        None, alias="containerRegistryAuthId"
    )
    cost_per_hr: float = Field(
        None, alias="costPerHr"
    )
    cpu_flavor_id: str = Field(
        None, alias="cpuFlavorId"
    )
    desired_status: Literal["RUNNING", "EXITED", "TERMINATED"] = Field(
        None, alias="desiredStatus"
    )
    docker_entrypoint: List[str] = Field(
        None, alias="dockerEntrypoint"
    )
    docker_start_cmd: List[str] = Field(
        None, alias="dockerStartCmd"
    )
    endpoint_id: str = Field(
        None, alias="endpointId"
    )
    env: Dict[str, Any] = Field(
        None
    )
    gpu: Dict[str, Any] = Field(
        None
    )
    id_: str = Field(
        None, alias="id"
    )
    image: str = Field(
        None
    )
    interruptible: bool = Field(
        None
    )
    last_started_at: str = Field(
        None, alias="lastStartedAt"
    )
    last_status_change: str = Field(
        None, alias="lastStatusChange"
    )
    locked: bool = Field(
        None
    )
    machine: Dict[str, Any] = Field(
        None
    )
    machine_id: str = Field(
        None, alias="machineId"
    )
    memory_in_gb: float = Field(
        None, alias="memoryInGb"
    )
    name: str = Field(
        None
    )
    network_volume: Dict[str, Any] = Field(
        None, alias="networkVolume"
    )
    port_mappings: Optional[Dict[str, Any]] = Field(
        None, alias="portMappings"
    )
    ports: List[str] = Field(
        None
    )
    public_ip: Optional[str] = Field(
        None, alias="publicIp"
    )
    savings_plans: List[Dict[str, Any]] = Field(
        None, alias="savingsPlans"
    )
    sls_version: int = Field(
        None, alias="slsVersion"
    )
    template_id: str = Field(
        None, alias="templateId"
    )
    vcpu_count: float = Field(
        None, alias="vcpuCount"
    )
    volume_encrypted: bool = Field(
        None, alias="volumeEncrypted"
    )
    volume_in_gb: int = Field(
        None, alias="volumeInGb"
    )
    volume_mount_path: str = Field(
        None, alias="volumeMountPath"
    )

class PodUpdateInPlaceInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    locked: bool = Field(
        None
    )
    name: str = Field(
        None
    )

class PodUpdateInput(BaseModel):
    """Input for updating a Pod which will trigger a reset."""
    model_config = ConfigDict(populate_by_name=True)

    container_disk_in_gb: Optional[int] = Field(
        None, alias="containerDiskInGb"
    )
    container_registry_auth_id: str = Field(
        None, alias="containerRegistryAuthId"
    )
    docker_entrypoint: List[str] = Field(
        None, alias="dockerEntrypoint"
    )
    docker_start_cmd: List[str] = Field(
        None, alias="dockerStartCmd"
    )
    env: Dict[str, Any] = Field(
        None
    )
    global_networking: bool = Field(
        None, alias="globalNetworking"
    )
    image_name: str = Field(
        None, alias="imageName"
    )
    locked: bool = Field(
        None
    )
    name: str = Field(
        None
    )
    ports: List[str] = Field(
        None
    )
    volume_in_gb: Optional[int] = Field(
        None, alias="volumeInGb"
    )
    volume_mount_path: str = Field(
        None, alias="volumeMountPath"
    )

class PodCreateInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    allowed_cuda_versions: List[Literal["12.9", "12.8", "12.7", "12.6", "12.5", "12.4", "12.3", "12.2", "12.1", "12.0", "11.8"]] = Field(
        None, alias="allowedCudaVersions"
    )
    cloud_type: Literal["SECURE", "COMMUNITY"] = Field(
        None, alias="cloudType"
    )
    compute_type: Literal["GPU", "CPU"] = Field(
        None, alias="computeType"
    )
    container_disk_in_gb: Optional[int] = Field(
        None, alias="containerDiskInGb"
    )
    container_registry_auth_id: str = Field(
        None, alias="containerRegistryAuthId"
    )
    country_codes: List[str] = Field(
        None, alias="countryCodes"
    )
    cpu_flavor_ids: List[Literal["cpu3c", "cpu3g", "cpu3m", "cpu5c", "cpu5g", "cpu5m"]] = Field(
        None, alias="cpuFlavorIds"
    )
    cpu_flavor_priority: Literal["availability", "custom"] = Field(
        None, alias="cpuFlavorPriority"
    )
    data_center_ids: List[Literal["EU-RO-1", "CA-MTL-1", "EU-SE-1", "US-IL-1", "EUR-IS-1", "EU-CZ-1", "US-TX-3", "EUR-IS-2", "US-KS-2", "US-GA-2", "US-WA-1", "US-TX-1", "CA-MTL-3", "EU-NL-1", "US-TX-4", "US-CA-2", "US-NC-1", "OC-AU-1", "US-DE-1", "EUR-IS-3", "CA-MTL-2", "AP-JP-1", "EUR-NO-1", "EU-FR-1", "US-KS-3", "US-GA-1"]] = Field(
        None, alias="dataCenterIds"
    )
    data_center_priority: Literal["availability", "custom"] = Field(
        None, alias="dataCenterPriority"
    )
    docker_entrypoint: List[str] = Field(
        None, alias="dockerEntrypoint"
    )
    docker_start_cmd: List[str] = Field(
        None, alias="dockerStartCmd"
    )
    env: Dict[str, Any] = Field(
        None
    )
    global_networking: bool = Field(
        None, alias="globalNetworking"
    )
    gpu_count: int = Field(
        None, alias="gpuCount"
    )
    gpu_type_ids: List[Literal["NVIDIA GeForce RTX 4090", "NVIDIA A40", "NVIDIA RTX A5000", "NVIDIA GeForce RTX 5090", "NVIDIA H100 80GB HBM3", "NVIDIA GeForce RTX 3090", "NVIDIA RTX A4500", "NVIDIA L40S", "NVIDIA H200", "NVIDIA L4", "NVIDIA RTX 6000 Ada Generation", "NVIDIA A100-SXM4-80GB", "NVIDIA RTX 4000 Ada Generation", "NVIDIA RTX A6000", "NVIDIA A100 80GB PCIe", "NVIDIA RTX 2000 Ada Generation", "NVIDIA RTX A4000", "NVIDIA RTX PRO 6000 Blackwell Server Edition", "NVIDIA H100 PCIe", "NVIDIA H100 NVL", "NVIDIA L40", "NVIDIA B200", "NVIDIA GeForce RTX 3080 Ti", "NVIDIA RTX PRO 6000 Blackwell Workstation Edition", "NVIDIA GeForce RTX 3080", "NVIDIA GeForce RTX 3070", "AMD Instinct MI300X OAM", "NVIDIA GeForce RTX 4080 SUPER", "Tesla V100-PCIE-16GB", "Tesla V100-SXM2-32GB", "NVIDIA RTX 5000 Ada Generation", "NVIDIA GeForce RTX 4070 Ti", "NVIDIA RTX 4000 SFF Ada Generation", "NVIDIA GeForce RTX 3090 Ti", "NVIDIA RTX A2000", "NVIDIA GeForce RTX 4080", "NVIDIA A30", "NVIDIA GeForce RTX 5080", "Tesla V100-FHHL-16GB", "NVIDIA H200 NVL", "Tesla V100-SXM2-16GB", "NVIDIA RTX PRO 6000 Blackwell Max-Q Workstation Edition", "NVIDIA A5000 Ada", "Tesla V100-PCIE-32GB", "NVIDIA  RTX A4500", "NVIDIA  A30", "NVIDIA GeForce RTX 3080TI", "Tesla T4", "NVIDIA RTX A30"]] = Field(
        None, alias="gpuTypeIds"
    )
    gpu_type_priority: Literal["availability", "custom"] = Field(
        None, alias="gpuTypePriority"
    )
    image_name: str = Field(
        None, alias="imageName"
    )
    interruptible: bool = Field(
        None
    )
    locked: bool = Field(
        None
    )
    min_disk_bandwidth_m_bps: float = Field(
        None, alias="minDiskBandwidthMBps"
    )
    min_download_mbps: float = Field(
        None, alias="minDownloadMbps"
    )
    min_ram_per_gpu: int = Field(
        None, alias="minRAMPerGPU"
    )
    min_upload_mbps: float = Field(
        None, alias="minUploadMbps"
    )
    min_vcpu_per_gpu: int = Field(
        None, alias="minVCPUPerGPU"
    )
    name: str = Field(
        None
    )
    network_volume_id: str = Field(
        None, alias="networkVolumeId"
    )
    ports: List[str] = Field(
        None
    )
    support_public_ip: bool = Field(
        None, alias="supportPublicIp"
    )
    template_id: str = Field(
        None, alias="templateId"
    )
    vcpu_count: int = Field(
        None, alias="vcpuCount"
    )
    volume_in_gb: Optional[int] = Field(
        None, alias="volumeInGb"
    )
    volume_mount_path: str = Field(
        None, alias="volumeMountPath"
    )

class NetworkVolumes(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class NetworkVolume(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    data_center_id: str = Field(
        None, alias="dataCenterId"
    )
    id_: str = Field(
        None, alias="id"
    )
    name: str = Field(
        None
    )
    size: int = Field(
        None
    )

class NetworkVolumeCreateInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    data_center_id: str = Field(
        ..., alias="dataCenterId"
    )
    name: str = Field(
        ...
    )
    size: int = Field(
        ...
    )

class NetworkVolumeUpdateInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(
        None
    )
    size: int = Field(
        None
    )

class Templates(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class Template(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    category: str = Field(
        None
    )
    container_disk_in_gb: int = Field(
        None, alias="containerDiskInGb"
    )
    container_registry_auth_id: str = Field(
        None, alias="containerRegistryAuthId"
    )
    docker_entrypoint: List[str] = Field(
        None, alias="dockerEntrypoint"
    )
    docker_start_cmd: List[str] = Field(
        None, alias="dockerStartCmd"
    )
    earned: float = Field(
        None
    )
    env: Dict[str, Any] = Field(
        None
    )
    id_: str = Field(
        None, alias="id"
    )
    image_name: str = Field(
        None, alias="imageName"
    )
    is_public: bool = Field(
        None, alias="isPublic"
    )
    is_runpod: bool = Field(
        None, alias="isRunpod"
    )
    is_serverless: bool = Field(
        None, alias="isServerless"
    )
    name: str = Field(
        None
    )
    ports: List[str] = Field(
        None
    )
    readme: str = Field(
        None
    )
    runtime_in_min: int = Field(
        None, alias="runtimeInMin"
    )
    volume_in_gb: int = Field(
        None, alias="volumeInGb"
    )
    volume_mount_path: str = Field(
        None, alias="volumeMountPath"
    )

class TemplateCreateInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    category: Literal["NVIDIA", "AMD", "CPU"] = Field(
        None
    )
    container_disk_in_gb: int = Field(
        None, alias="containerDiskInGb"
    )
    container_registry_auth_id: str = Field(
        None, alias="containerRegistryAuthId"
    )
    docker_entrypoint: List[str] = Field(
        None, alias="dockerEntrypoint"
    )
    docker_start_cmd: List[str] = Field(
        None, alias="dockerStartCmd"
    )
    env: Dict[str, Any] = Field(
        None
    )
    image_name: str = Field(
        ..., alias="imageName"
    )
    is_public: bool = Field(
        None, alias="isPublic"
    )
    is_serverless: bool = Field(
        None, alias="isServerless"
    )
    name: str = Field(
        ...
    )
    ports: List[str] = Field(
        None
    )
    readme: str = Field(
        None
    )
    volume_in_gb: int = Field(
        None, alias="volumeInGb"
    )
    volume_mount_path: str = Field(
        None, alias="volumeMountPath"
    )

class TemplateUpdateInPlaceInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    is_public: bool = Field(
        None, alias="isPublic"
    )
    name: str = Field(
        None
    )
    readme: str = Field(
        None
    )
    volume_in_gb: int = Field(
        None, alias="volumeInGb"
    )
    volume_mount_path: str = Field(
        None, alias="volumeMountPath"
    )

class TemplateUpdateInput(BaseModel):
    """Input for updating a Template which will trigger a rolling release for any associated endpoints."""
    model_config = ConfigDict(populate_by_name=True)

    container_disk_in_gb: int = Field(
        None, alias="containerDiskInGb"
    )
    container_registry_auth_id: str = Field(
        None, alias="containerRegistryAuthId"
    )
    docker_entrypoint: List[str] = Field(
        None, alias="dockerEntrypoint"
    )
    docker_start_cmd: List[str] = Field(
        None, alias="dockerStartCmd"
    )
    env: Dict[str, Any] = Field(
        None
    )
    image_name: str = Field(
        None, alias="imageName"
    )
    is_public: bool = Field(
        None, alias="isPublic"
    )
    name: str = Field(
        None
    )
    ports: List[str] = Field(
        None
    )
    readme: str = Field(
        None
    )
    volume_in_gb: int = Field(
        None, alias="volumeInGb"
    )
    volume_mount_path: str = Field(
        None, alias="volumeMountPath"
    )

class Endpoints(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class Endpoint(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    allowed_cuda_versions: List[Literal["12.9", "12.8", "12.7", "12.6", "12.5", "12.4", "12.3", "12.2", "12.1", "12.0", "11.8"]] = Field(
        None, alias="allowedCudaVersions"
    )
    compute_type: Literal["CPU", "GPU"] = Field(
        None, alias="computeType"
    )
    created_at: str = Field(
        None, alias="createdAt"
    )
    data_center_ids: List[Literal["EU-RO-1", "CA-MTL-1", "EU-SE-1", "US-IL-1", "EUR-IS-1", "EU-CZ-1", "US-TX-3", "EUR-IS-2", "US-KS-2", "US-GA-2", "US-WA-1", "US-TX-1", "CA-MTL-3", "EU-NL-1", "US-TX-4", "US-CA-2", "US-NC-1", "OC-AU-1", "US-DE-1", "EUR-IS-3", "CA-MTL-2", "AP-JP-1", "EUR-NO-1", "EU-FR-1", "US-KS-3", "US-GA-1"]] = Field(
        None, alias="dataCenterIds"
    )
    env: Dict[str, Any] = Field(
        None
    )
    execution_timeout_ms: int = Field(
        None, alias="executionTimeoutMs"
    )
    gpu_count: int = Field(
        None, alias="gpuCount"
    )
    gpu_type_ids: List[Literal["NVIDIA GeForce RTX 4090", "NVIDIA A40", "NVIDIA RTX A5000", "NVIDIA GeForce RTX 5090", "NVIDIA H100 80GB HBM3", "NVIDIA GeForce RTX 3090", "NVIDIA RTX A4500", "NVIDIA L40S", "NVIDIA H200", "NVIDIA L4", "NVIDIA RTX 6000 Ada Generation", "NVIDIA A100-SXM4-80GB", "NVIDIA RTX 4000 Ada Generation", "NVIDIA RTX A6000", "NVIDIA A100 80GB PCIe", "NVIDIA RTX 2000 Ada Generation", "NVIDIA RTX A4000", "NVIDIA RTX PRO 6000 Blackwell Server Edition", "NVIDIA H100 PCIe", "NVIDIA H100 NVL", "NVIDIA L40", "NVIDIA B200", "NVIDIA GeForce RTX 3080 Ti", "NVIDIA RTX PRO 6000 Blackwell Workstation Edition", "NVIDIA GeForce RTX 3080", "NVIDIA GeForce RTX 3070", "AMD Instinct MI300X OAM", "NVIDIA GeForce RTX 4080 SUPER", "Tesla V100-PCIE-16GB", "Tesla V100-SXM2-32GB", "NVIDIA RTX 5000 Ada Generation", "NVIDIA GeForce RTX 4070 Ti", "NVIDIA RTX 4000 SFF Ada Generation", "NVIDIA GeForce RTX 3090 Ti", "NVIDIA RTX A2000", "NVIDIA GeForce RTX 4080", "NVIDIA A30", "NVIDIA GeForce RTX 5080", "Tesla V100-FHHL-16GB", "NVIDIA H200 NVL", "Tesla V100-SXM2-16GB", "NVIDIA RTX PRO 6000 Blackwell Max-Q Workstation Edition", "NVIDIA A5000 Ada", "Tesla V100-PCIE-32GB", "NVIDIA  RTX A4500", "NVIDIA  A30", "NVIDIA GeForce RTX 3080TI", "Tesla T4", "NVIDIA RTX A30"]] = Field(
        None, alias="gpuTypeIds"
    )
    id_: str = Field(
        None, alias="id"
    )
    idle_timeout: int = Field(
        None, alias="idleTimeout"
    )
    instance_ids: List[str] = Field(
        None, alias="instanceIds"
    )
    name: str = Field(
        None
    )
    network_volume_id: str = Field(
        None, alias="networkVolumeId"
    )
    scaler_type: Literal["QUEUE_DELAY", "REQUEST_COUNT"] = Field(
        None, alias="scalerType"
    )
    scaler_value: int = Field(
        None, alias="scalerValue"
    )
    template: Dict[str, Any] = Field(
        None
    )
    template_id: str = Field(
        None, alias="templateId"
    )
    user_id: str = Field(
        None, alias="userId"
    )
    version: int = Field(
        None
    )
    workers: List[Dict[str, Any]] = Field(
        None
    )
    workers_max: int = Field(
        None, alias="workersMax"
    )
    workers_min: int = Field(
        None, alias="workersMin"
    )

class EndpointUpdateInPlaceInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    execution_timeout_ms: int = Field(
        None, alias="executionTimeoutMs"
    )
    flashboot: bool = Field(
        None
    )
    idle_timeout: int = Field(
        None, alias="idleTimeout"
    )
    name: str = Field(
        None
    )
    scaler_type: Literal["QUEUE_DELAY", "REQUEST_COUNT"] = Field(
        None, alias="scalerType"
    )
    scaler_value: int = Field(
        None, alias="scalerValue"
    )
    workers_max: int = Field(
        None, alias="workersMax"
    )
    workers_min: int = Field(
        None, alias="workersMin"
    )

class EndpointUpdateInput(BaseModel):
    """Input for updating an endpoint which will trigger a rolling release on the endpoint."""
    model_config = ConfigDict(populate_by_name=True)

    allowed_cuda_versions: List[Literal["12.9", "12.8", "12.7", "12.6", "12.5", "12.4", "12.3", "12.2", "12.1", "12.0", "11.8"]] = Field(
        None, alias="allowedCudaVersions"
    )
    cpu_flavor_ids: List[Literal["cpu3c", "cpu3g", "cpu5c", "cpu5g"]] = Field(
        None, alias="cpuFlavorIds"
    )
    data_center_ids: List[Literal["EU-RO-1", "CA-MTL-1", "EU-SE-1", "US-IL-1", "EUR-IS-1", "EU-CZ-1", "US-TX-3", "EUR-IS-2", "US-KS-2", "US-GA-2", "US-WA-1", "US-TX-1", "CA-MTL-3", "EU-NL-1", "US-TX-4", "US-CA-2", "US-NC-1", "OC-AU-1", "US-DE-1", "EUR-IS-3", "CA-MTL-2", "AP-JP-1", "EUR-NO-1", "EU-FR-1", "US-KS-3", "US-GA-1"]] = Field(
        None, alias="dataCenterIds"
    )
    execution_timeout_ms: int = Field(
        None, alias="executionTimeoutMs"
    )
    flashboot: bool = Field(
        None
    )
    gpu_count: int = Field(
        None, alias="gpuCount"
    )
    gpu_type_ids: List[Literal["NVIDIA GeForce RTX 4090", "NVIDIA A40", "NVIDIA RTX A5000", "NVIDIA GeForce RTX 5090", "NVIDIA H100 80GB HBM3", "NVIDIA GeForce RTX 3090", "NVIDIA RTX A4500", "NVIDIA L40S", "NVIDIA H200", "NVIDIA L4", "NVIDIA RTX 6000 Ada Generation", "NVIDIA A100-SXM4-80GB", "NVIDIA RTX 4000 Ada Generation", "NVIDIA RTX A6000", "NVIDIA A100 80GB PCIe", "NVIDIA RTX 2000 Ada Generation", "NVIDIA RTX A4000", "NVIDIA RTX PRO 6000 Blackwell Server Edition", "NVIDIA H100 PCIe", "NVIDIA H100 NVL", "NVIDIA L40", "NVIDIA B200", "NVIDIA GeForce RTX 3080 Ti", "NVIDIA RTX PRO 6000 Blackwell Workstation Edition", "NVIDIA GeForce RTX 3080", "NVIDIA GeForce RTX 3070", "AMD Instinct MI300X OAM", "NVIDIA GeForce RTX 4080 SUPER", "Tesla V100-PCIE-16GB", "Tesla V100-SXM2-32GB", "NVIDIA RTX 5000 Ada Generation", "NVIDIA GeForce RTX 4070 Ti", "NVIDIA RTX 4000 SFF Ada Generation", "NVIDIA GeForce RTX 3090 Ti", "NVIDIA RTX A2000", "NVIDIA GeForce RTX 4080", "NVIDIA A30", "NVIDIA GeForce RTX 5080", "Tesla V100-FHHL-16GB", "NVIDIA H200 NVL", "Tesla V100-SXM2-16GB", "NVIDIA RTX PRO 6000 Blackwell Max-Q Workstation Edition", "NVIDIA A5000 Ada", "Tesla V100-PCIE-32GB", "NVIDIA  RTX A4500", "NVIDIA  A30", "NVIDIA GeForce RTX 3080TI", "Tesla T4", "NVIDIA RTX A30"]] = Field(
        None, alias="gpuTypeIds"
    )
    idle_timeout: int = Field(
        None, alias="idleTimeout"
    )
    name: str = Field(
        None
    )
    network_volume_id: str = Field(
        None, alias="networkVolumeId"
    )
    scaler_type: Literal["QUEUE_DELAY", "REQUEST_COUNT"] = Field(
        None, alias="scalerType"
    )
    scaler_value: int = Field(
        None, alias="scalerValue"
    )
    template_id: str = Field(
        None, alias="templateId"
    )
    vcpu_count: int = Field(
        None, alias="vcpuCount"
    )
    workers_max: int = Field(
        None, alias="workersMax"
    )
    workers_min: int = Field(
        None, alias="workersMin"
    )

class EndpointCreateInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    allowed_cuda_versions: List[Literal["12.9", "12.8", "12.7", "12.6", "12.5", "12.4", "12.3", "12.2", "12.1", "12.0", "11.8"]] = Field(
        None, alias="allowedCudaVersions"
    )
    compute_type: Literal["GPU", "CPU"] = Field(
        None, alias="computeType"
    )
    cpu_flavor_ids: List[Literal["cpu3c", "cpu3g", "cpu5c", "cpu5g"]] = Field(
        None, alias="cpuFlavorIds"
    )
    data_center_ids: List[Literal["EU-RO-1", "CA-MTL-1", "EU-SE-1", "US-IL-1", "EUR-IS-1", "EU-CZ-1", "US-TX-3", "EUR-IS-2", "US-KS-2", "US-GA-2", "US-WA-1", "US-TX-1", "CA-MTL-3", "EU-NL-1", "US-TX-4", "US-CA-2", "US-NC-1", "OC-AU-1", "US-DE-1", "EUR-IS-3", "CA-MTL-2", "AP-JP-1", "EUR-NO-1", "EU-FR-1", "US-KS-3", "US-GA-1"]] = Field(
        None, alias="dataCenterIds"
    )
    execution_timeout_ms: int = Field(
        None, alias="executionTimeoutMs"
    )
    flashboot: bool = Field(
        None
    )
    gpu_count: int = Field(
        None, alias="gpuCount"
    )
    gpu_type_ids: List[Literal["NVIDIA GeForce RTX 4090", "NVIDIA A40", "NVIDIA RTX A5000", "NVIDIA GeForce RTX 5090", "NVIDIA H100 80GB HBM3", "NVIDIA GeForce RTX 3090", "NVIDIA RTX A4500", "NVIDIA L40S", "NVIDIA H200", "NVIDIA L4", "NVIDIA RTX 6000 Ada Generation", "NVIDIA A100-SXM4-80GB", "NVIDIA RTX 4000 Ada Generation", "NVIDIA RTX A6000", "NVIDIA A100 80GB PCIe", "NVIDIA RTX 2000 Ada Generation", "NVIDIA RTX A4000", "NVIDIA RTX PRO 6000 Blackwell Server Edition", "NVIDIA H100 PCIe", "NVIDIA H100 NVL", "NVIDIA L40", "NVIDIA B200", "NVIDIA GeForce RTX 3080 Ti", "NVIDIA RTX PRO 6000 Blackwell Workstation Edition", "NVIDIA GeForce RTX 3080", "NVIDIA GeForce RTX 3070", "AMD Instinct MI300X OAM", "NVIDIA GeForce RTX 4080 SUPER", "Tesla V100-PCIE-16GB", "Tesla V100-SXM2-32GB", "NVIDIA RTX 5000 Ada Generation", "NVIDIA GeForce RTX 4070 Ti", "NVIDIA RTX 4000 SFF Ada Generation", "NVIDIA GeForce RTX 3090 Ti", "NVIDIA RTX A2000", "NVIDIA GeForce RTX 4080", "NVIDIA A30", "NVIDIA GeForce RTX 5080", "Tesla V100-FHHL-16GB", "NVIDIA H200 NVL", "Tesla V100-SXM2-16GB", "NVIDIA RTX PRO 6000 Blackwell Max-Q Workstation Edition", "NVIDIA A5000 Ada", "Tesla V100-PCIE-32GB", "NVIDIA  RTX A4500", "NVIDIA  A30", "NVIDIA GeForce RTX 3080TI", "Tesla T4", "NVIDIA RTX A30"]] = Field(
        None, alias="gpuTypeIds"
    )
    idle_timeout: int = Field(
        None, alias="idleTimeout"
    )
    name: str = Field(
        None
    )
    network_volume_id: str = Field(
        None, alias="networkVolumeId"
    )
    scaler_type: Literal["QUEUE_DELAY", "REQUEST_COUNT"] = Field(
        None, alias="scalerType"
    )
    scaler_value: int = Field(
        None, alias="scalerValue"
    )
    template_id: str = Field(
        ..., alias="templateId"
    )
    vcpu_count: int = Field(
        None, alias="vcpuCount"
    )
    workers_max: int = Field(
        None, alias="workersMax"
    )
    workers_min: int = Field(
        None, alias="workersMin"
    )

class User(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class SavingsPlan(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    cost_per_hr: float = Field(
        None, alias="costPerHr"
    )
    end_time: str = Field(
        None, alias="endTime"
    )
    gpu_type_id: str = Field(
        None, alias="gpuTypeId"
    )
    id_: str = Field(
        None, alias="id"
    )
    pod_id: str = Field(
        None, alias="podId"
    )
    start_time: str = Field(
        None, alias="startTime"
    )

class Machine(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    cost_per_hr: float = Field(
        None, alias="costPerHr"
    )
    cpu_count: int = Field(
        None, alias="cpuCount"
    )
    cpu_type: Dict[str, Any] = Field(
        None, alias="cpuType"
    )
    cpu_type_id: str = Field(
        None, alias="cpuTypeId"
    )
    current_price_per_gpu: float = Field(
        None, alias="currentPricePerGpu"
    )
    data_center_id: str = Field(
        None, alias="dataCenterId"
    )
    disk_throughput_m_bps: int = Field(
        None, alias="diskThroughputMBps"
    )
    gpu_available: int = Field(
        None, alias="gpuAvailable"
    )
    gpu_display_name: str = Field(
        None, alias="gpuDisplayName"
    )
    gpu_type: Dict[str, Any] = Field(
        None, alias="gpuType"
    )
    gpu_type_id: str = Field(
        None, alias="gpuTypeId"
    )
    location: str = Field(
        None
    )
    maintenance_end: str = Field(
        None, alias="maintenanceEnd"
    )
    maintenance_note: str = Field(
        None, alias="maintenanceNote"
    )
    maintenance_start: str = Field(
        None, alias="maintenanceStart"
    )
    max_download_speed_mbps: int = Field(
        None, alias="maxDownloadSpeedMbps"
    )
    max_upload_speed_mbps: int = Field(
        None, alias="maxUploadSpeedMbps"
    )
    min_pod_gpu_count: int = Field(
        None, alias="minPodGpuCount"
    )
    note: str = Field(
        None
    )
    secure_cloud: bool = Field(
        None, alias="secureCloud"
    )
    support_public_ip: bool = Field(
        None, alias="supportPublicIp"
    )

class DataCenter(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        None, alias="id"
    )

class UnauthorizedError(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    message: str = Field(
        None
    )

class CudaVersions(str, Enum):
    _12_4 = "12.4"
    _12_3 = "12.3"
    _12_2 = "12.2"
    _12_1 = "12.1"
    _12_0 = "12.0"
    _11_8 = "11.8"

class GpuTypeId(str, Enum):
    NVIDIA_GEFORCE_RTX_4090 = "NVIDIA GeForce RTX 4090"
    NVIDIA_RTX_A5000 = "NVIDIA RTX A5000"
    NVIDIA_RTX_A4000 = "NVIDIA RTX A4000"
    NVIDIA_GEFORCE_RTX_3090 = "NVIDIA GeForce RTX 3090"
    NVIDIA_RTX_A6000 = "NVIDIA RTX A6000"
    NVIDIA_A40 = "NVIDIA A40"
    NVIDIA_RTX_A4500 = "NVIDIA RTX A4500"
    NVIDIA_A100_80GB_PCIE = "NVIDIA A100 80GB PCIe"
    NVIDIA_L4 = "NVIDIA L4"
    NVIDIA_RTX_4000_ADA_GENERATION = "NVIDIA RTX 4000 Ada Generation"
    NVIDIA_RTX_6000_ADA_GENERATION = "NVIDIA RTX 6000 Ada Generation"
    NVIDIA_A100_SXM4_80GB = "NVIDIA A100-SXM4-80GB"
    NVIDIA_H100_80GB_HBM3 = "NVIDIA H100 80GB HBM3"
    NVIDIA_L40 = "NVIDIA L40"
    NVIDIA_H100_PCIE = "NVIDIA H100 PCIe"
    NVIDIA_L40S = "NVIDIA L40S"
    NVIDIA_GEFORCE_RTX_3080 = "NVIDIA GeForce RTX 3080"
    NVIDIA_GEFORCE_RTX_3070 = "NVIDIA GeForce RTX 3070"
    NVIDIA_GEFORCE_RTX_3080_TI = "NVIDIA GeForce RTX 3080 Ti"
    NVIDIA_A30 = "NVIDIA A30"
    NVIDIA_GEFORCE_RTX_4080 = "NVIDIA GeForce RTX 4080"
    NVIDIA_RTX_A2000 = "NVIDIA RTX A2000"
    NVIDIA_GEFORCE_RTX_3090_TI = "NVIDIA GeForce RTX 3090 Ti"
    TESLA_V100_SXM2_32GB = "Tesla V100-SXM2-32GB"
    NVIDIA_GEFORCE_RTX_4070_TI = "NVIDIA GeForce RTX 4070 Ti"
    NVIDIA_RTX_4000_SFF_ADA_GENERATION = "NVIDIA RTX 4000 SFF Ada Generation"
    NVIDIA_RTX_5000_ADA_GENERATION = "NVIDIA RTX 5000 Ada Generation"
    TESLA_V100_SXM2_16GB = "Tesla V100-SXM2-16GB"
    TESLA_V100_FHHL_16GB = "Tesla V100-FHHL-16GB"
    TESLA_V100_PCIE_16GB = "Tesla V100-PCIE-16GB"
    NVIDIA_RTX_2000_ADA_GENERATION = "NVIDIA RTX 2000 Ada Generation"
    NVIDIA_H100_NVL = "NVIDIA H100 NVL"
    AMD_INSTINCT_MI300X_OAM = "AMD Instinct MI300X OAM"
    NVIDIA_A100_SXM4_40GB = "NVIDIA A100-SXM4-40GB"

class ContainerRegistryAuth(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        None, alias="id"
    )
    name: str = Field(
        None
    )

class ContainerRegistryAuths(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class ContainerRegistryAuthCreateInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(
        ...
    )
    password: str = Field(
        ...
    )
    username: str = Field(
        ...
    )

class BillingRecord(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    amount: float = Field(
        None
    )
    disk_space_billed_gb: int = Field(
        None, alias="diskSpaceBilledGb"
    )
    endpoint_id: str = Field(
        None, alias="endpointId"
    )
    gpu_type_id: str = Field(
        None, alias="gpuTypeId"
    )
    pod_id: str = Field(
        None, alias="podId"
    )
    time: str = Field(
        None
    )
    time_billed_ms: int = Field(
        None, alias="timeBilledMs"
    )

class BillingRecords(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class NetworkVolumeBillingRecord(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    amount: float = Field(
        None
    )
    disk_space_billed_gb: int = Field(
        None, alias="diskSpaceBilledGb"
    )
    high_performance_storage_amount: float = Field(
        None, alias="highPerformanceStorageAmount"
    )
    high_performance_storage_disk_space_billed_gb: int = Field(
        None, alias="highPerformanceStorageDiskSpaceBilledGb"
    )
    time: str = Field(
        None
    )

class NetworkVolumeBillingRecords(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass
