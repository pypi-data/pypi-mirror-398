from typing import Any, Dict, List, Literal, Optional, Union
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict

class AddUploadPartRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    data: bytes = Field(
        ...
    )

class AdminApiKey(BaseModel):
    """Represents an individual Admin API key in an org."""
    model_config = ConfigDict(populate_by_name=True)

    object: str = Field(
        ...
    )
    id_: str = Field(
        ..., alias="id"
    )
    name: str = Field(
        ...
    )
    redacted_value: str = Field(
        ...
    )
    value: str = Field(
        None
    )
    created_at: int = Field(
        ...
    )
    last_used_at: int = Field(
        ...
    )
    owner: Dict[str, Any] = Field(
        ...
    )

class ApiKeyList(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    object: str = Field(
        None
    )
    data: List[Dict[str, Any]] = Field(
        None
    )
    has_more: bool = Field(
        None
    )
    first_id: str = Field(
        None
    )
    last_id: str = Field(
        None
    )

class AssignedRoleDetails(BaseModel):
    """Detailed information about a role assignment entry returned when listing assignments."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )
    name: str = Field(
        ...
    )
    permissions: List[str] = Field(
        ...
    )
    resource_type: str = Field(
        ...
    )
    predefined_role: bool = Field(
        ...
    )
    description: str = Field(
        ...
    )
    created_at: int = Field(
        ...
    )
    updated_at: int = Field(
        ...
    )
    created_by: str = Field(
        ...
    )
    created_by_user_obj: Dict[str, Any] = Field(
        ...
    )
    metadata: Dict[str, Any] = Field(
        ...
    )

class AssistantObject(BaseModel):
    """Represents an `assistant` that can call the model and use tools."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )
    object: Literal["assistant"] = Field(
        ...
    )
    created_at: int = Field(
        ...
    )
    name: str = Field(
        ...
    )
    description: str = Field(
        ...
    )
    model: str = Field(
        ...
    )
    instructions: str = Field(
        ...
    )
    tools: List[Union[CodeInterpreterTool, FileSearchTool, FunctionTool]] = Field(
        ...
    )
    tool_resources: Dict[str, Any] = Field(
        None
    )
    metadata: Dict[str, str] = Field(
        ...
    )
    temperature: float = Field(
        None
    )
    top_p: float = Field(
        None
    )
    response_format: Union[Literal["auto"], Text, JsonObject, JsonSchema] = Field(
        None
    )

class AssistantStreamEvent(BaseModel):
    """Represents an event emitted when streaming a Run.

Each event in a server-sent events stream has an `event` and `data` property:

```
event: thread.created
data: {"id": "thread_123", "object": "thread", ...}
```

We emit events whenever a new object is created, transitions to a new state, or is being
streamed in parts (deltas). For example, we emit `thread.run.created` when a new run
is created, `thread.run.completed` when a run completes, and so on. When an Assistant chooses
to create a message during a run, we emit a `thread.message.created event`, a
`thread.message.in_progress` event, many `thread.message.delta` events, and finally a
`thread.message.completed` event.

We may add additional events over time, so we recommend handling unknown events gracefully
in your code. See the [Assistants API quickstart](https://platform.openai.com/docs/assistants/overview) to learn how to
integrate the Assistants API with streaming."""
    model_config = ConfigDict(populate_by_name=True)

    pass

class AssistantSupportedModels(str, Enum):
    GPT_5 = "gpt-5"
    GPT_5_MINI = "gpt-5-mini"
    GPT_5_NANO = "gpt-5-nano"
    GPT_5_2025_08_07 = "gpt-5-2025-08-07"
    GPT_5_MINI_2025_08_07 = "gpt-5-mini-2025-08-07"
    GPT_5_NANO_2025_08_07 = "gpt-5-nano-2025-08-07"
    GPT_4_1 = "gpt-4.1"
    GPT_4_1_MINI = "gpt-4.1-mini"
    GPT_4_1_NANO = "gpt-4.1-nano"
    GPT_4_1_2025_04_14 = "gpt-4.1-2025-04-14"
    GPT_4_1_MINI_2025_04_14 = "gpt-4.1-mini-2025-04-14"
    GPT_4_1_NANO_2025_04_14 = "gpt-4.1-nano-2025-04-14"
    O3_MINI = "o3-mini"
    O3_MINI_2025_01_31 = "o3-mini-2025-01-31"
    O1 = "o1"
    O1_2024_12_17 = "o1-2024-12-17"
    GPT_4O = "gpt-4o"
    GPT_4O_2024_11_20 = "gpt-4o-2024-11-20"
    GPT_4O_2024_08_06 = "gpt-4o-2024-08-06"
    GPT_4O_2024_05_13 = "gpt-4o-2024-05-13"
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_4O_MINI_2024_07_18 = "gpt-4o-mini-2024-07-18"
    GPT_4_5_PREVIEW = "gpt-4.5-preview"
    GPT_4_5_PREVIEW_2025_02_27 = "gpt-4.5-preview-2025-02-27"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_4_TURBO_2024_04_09 = "gpt-4-turbo-2024-04-09"
    GPT_4_0125_PREVIEW = "gpt-4-0125-preview"
    GPT_4_TURBO_PREVIEW = "gpt-4-turbo-preview"
    GPT_4_1106_PREVIEW = "gpt-4-1106-preview"
    GPT_4_VISION_PREVIEW = "gpt-4-vision-preview"
    GPT_4 = "gpt-4"
    GPT_4_0314 = "gpt-4-0314"
    GPT_4_0613 = "gpt-4-0613"
    GPT_4_32K = "gpt-4-32k"
    GPT_4_32K_0314 = "gpt-4-32k-0314"
    GPT_4_32K_0613 = "gpt-4-32k-0613"
    GPT_3_5_TURBO = "gpt-3.5-turbo"
    GPT_3_5_TURBO_16K = "gpt-3.5-turbo-16k"
    GPT_3_5_TURBO_0613 = "gpt-3.5-turbo-0613"
    GPT_3_5_TURBO_1106 = "gpt-3.5-turbo-1106"
    GPT_3_5_TURBO_0125 = "gpt-3.5-turbo-0125"
    GPT_3_5_TURBO_16K_0613 = "gpt-3.5-turbo-16k-0613"

class AssistantToolsCode(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["code_interpreter"] = Field(
        ..., alias="type"
    )

class AssistantToolsFileSearch(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["file_search"] = Field(
        ..., alias="type"
    )
    file_search: Dict[str, Any] = Field(
        None
    )

class AssistantToolsFileSearchTypeOnly(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["file_search"] = Field(
        ..., alias="type"
    )

class AssistantToolsFunction(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["function"] = Field(
        ..., alias="type"
    )
    function: Dict[str, Any] = Field(
        ...
    )

class AssistantsApiResponseFormatOption(BaseModel):
    """Specifies the format that the model must output. Compatible with [GPT-4o](https://platform.openai.com/docs/models#gpt-4o), [GPT-4 Turbo](https://platform.openai.com/docs/models#gpt-4-turbo-and-gpt-4), and all GPT-3.5 Turbo models since `gpt-3.5-turbo-1106`.

Setting to `{ "type": "json_schema", "json_schema": {...} }` enables Structured Outputs which ensures the model will match your supplied JSON schema. Learn more in the [Structured Outputs guide](https://platform.openai.com/docs/guides/structured-outputs).

Setting to `{ "type": "json_object" }` enables JSON mode, which ensures the message the model generates is valid JSON.

**Important:** when using JSON mode, you **must** also instruct the model to produce JSON yourself via a system or user message. Without this, the model may generate an unending stream of whitespace until the generation reaches the token limit, resulting in a long-running and seemingly "stuck" request. Also note that the message content may be partially cut off if `finish_reason="length"`, which indicates the generation exceeded `max_tokens` or the conversation exceeded the max context length."""
    model_config = ConfigDict(populate_by_name=True)

    pass

class AssistantsApiToolChoiceOption(BaseModel):
    """Controls which (if any) tool is called by the model.
`none` means the model will not call any tools and instead generates a message.
`auto` is the default value and means the model can pick between generating a message or calling one or more tools.
`required` means the model must call one or more tools before responding to the user.
Specifying a particular tool like `{"type": "file_search"}` or `{"type": "function", "function": {"name": "my_function"}}` forces the model to call that tool."""
    model_config = ConfigDict(populate_by_name=True)

    pass

class AssistantsNamedToolChoice(BaseModel):
    """Specifies a tool the model should use. Use to force the model to call a specific tool."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["function", "code_interpreter", "file_search"] = Field(
        ..., alias="type"
    )
    function: Dict[str, Any] = Field(
        None
    )

class AudioResponseFormat(str, Enum):
    """The format of the output, in one of these options: `json`, `text`, `srt`, `verbose_json`, `vtt`, or `diarized_json`. For `gpt-4o-transcribe` and `gpt-4o-mini-transcribe`, the only supported format is `json`. For `gpt-4o-transcribe-diarize`, the supported formats are `json`, `text`, and `diarized_json`, with `diarized_json` required to receive speaker annotations."""
    JSON = "json"
    TEXT = "text"
    SRT = "srt"
    VERBOSE_JSON = "verbose_json"
    VTT = "vtt"
    DIARIZED_JSON = "diarized_json"

class AudioTranscription(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    model: Literal["whisper-1", "gpt-4o-mini-transcribe", "gpt-4o-transcribe", "gpt-4o-transcribe-diarize"] = Field(
        None
    )
    language: str = Field(
        None
    )
    prompt: str = Field(
        None
    )

class AuditLog(BaseModel):
    """A log of a user action or configuration change within this organization."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )
    type_: Literal["api_key.created", "api_key.updated", "api_key.deleted", "certificate.created", "certificate.updated", "certificate.deleted", "certificates.activated", "certificates.deactivated", "checkpoint.permission.created", "checkpoint.permission.deleted", "external_key.registered", "external_key.removed", "group.created", "group.updated", "group.deleted", "invite.sent", "invite.accepted", "invite.deleted", "ip_allowlist.created", "ip_allowlist.updated", "ip_allowlist.deleted", "ip_allowlist.config.activated", "ip_allowlist.config.deactivated", "login.succeeded", "login.failed", "logout.succeeded", "logout.failed", "organization.updated", "project.created", "project.updated", "project.archived", "project.deleted", "rate_limit.updated", "rate_limit.deleted", "resource.deleted", "tunnel.created", "tunnel.updated", "tunnel.deleted", "role.created", "role.updated", "role.deleted", "role.assignment.created", "role.assignment.deleted", "scim.enabled", "scim.disabled", "service_account.created", "service_account.updated", "service_account.deleted", "user.added", "user.updated", "user.deleted"] = Field(
        ..., alias="type"
    )
    effective_at: int = Field(
        ...
    )
    project: Dict[str, Any] = Field(
        None
    )
    actor: Dict[str, Any] = Field(
        ...
    )
    api_key_created: Dict[str, Any] = Field(
        None, alias="api_key.created"
    )
    api_key_updated: Dict[str, Any] = Field(
        None, alias="api_key.updated"
    )
    api_key_deleted: Dict[str, Any] = Field(
        None, alias="api_key.deleted"
    )
    checkpoint_permission_created: Dict[str, Any] = Field(
        None, alias="checkpoint.permission.created"
    )
    checkpoint_permission_deleted: Dict[str, Any] = Field(
        None, alias="checkpoint.permission.deleted"
    )
    external_key_registered: Dict[str, Any] = Field(
        None, alias="external_key.registered"
    )
    external_key_removed: Dict[str, Any] = Field(
        None, alias="external_key.removed"
    )
    group_created: Dict[str, Any] = Field(
        None, alias="group.created"
    )
    group_updated: Dict[str, Any] = Field(
        None, alias="group.updated"
    )
    group_deleted: Dict[str, Any] = Field(
        None, alias="group.deleted"
    )
    scim_enabled: Dict[str, Any] = Field(
        None, alias="scim.enabled"
    )
    scim_disabled: Dict[str, Any] = Field(
        None, alias="scim.disabled"
    )
    invite_sent: Dict[str, Any] = Field(
        None, alias="invite.sent"
    )
    invite_accepted: Dict[str, Any] = Field(
        None, alias="invite.accepted"
    )
    invite_deleted: Dict[str, Any] = Field(
        None, alias="invite.deleted"
    )
    ip_allowlist_created: Dict[str, Any] = Field(
        None, alias="ip_allowlist.created"
    )
    ip_allowlist_updated: Dict[str, Any] = Field(
        None, alias="ip_allowlist.updated"
    )
    ip_allowlist_deleted: Dict[str, Any] = Field(
        None, alias="ip_allowlist.deleted"
    )
    ip_allowlist_config_activated: Dict[str, Any] = Field(
        None, alias="ip_allowlist.config.activated"
    )
    ip_allowlist_config_deactivated: Dict[str, Any] = Field(
        None, alias="ip_allowlist.config.deactivated"
    )
    login_succeeded: Dict[str, Any] = Field(
        None, alias="login.succeeded"
    )
    login_failed: Dict[str, Any] = Field(
        None, alias="login.failed"
    )
    logout_succeeded: Dict[str, Any] = Field(
        None, alias="logout.succeeded"
    )
    logout_failed: Dict[str, Any] = Field(
        None, alias="logout.failed"
    )
    organization_updated: Dict[str, Any] = Field(
        None, alias="organization.updated"
    )
    project_created: Dict[str, Any] = Field(
        None, alias="project.created"
    )
    project_updated: Dict[str, Any] = Field(
        None, alias="project.updated"
    )
    project_archived: Dict[str, Any] = Field(
        None, alias="project.archived"
    )
    project_deleted: Dict[str, Any] = Field(
        None, alias="project.deleted"
    )
    rate_limit_updated: Dict[str, Any] = Field(
        None, alias="rate_limit.updated"
    )
    rate_limit_deleted: Dict[str, Any] = Field(
        None, alias="rate_limit.deleted"
    )
    role_created: Dict[str, Any] = Field(
        None, alias="role.created"
    )
    role_updated: Dict[str, Any] = Field(
        None, alias="role.updated"
    )
    role_deleted: Dict[str, Any] = Field(
        None, alias="role.deleted"
    )
    role_assignment_created: Dict[str, Any] = Field(
        None, alias="role.assignment.created"
    )
    role_assignment_deleted: Dict[str, Any] = Field(
        None, alias="role.assignment.deleted"
    )
    service_account_created: Dict[str, Any] = Field(
        None, alias="service_account.created"
    )
    service_account_updated: Dict[str, Any] = Field(
        None, alias="service_account.updated"
    )
    service_account_deleted: Dict[str, Any] = Field(
        None, alias="service_account.deleted"
    )
    user_added: Dict[str, Any] = Field(
        None, alias="user.added"
    )
    user_updated: Dict[str, Any] = Field(
        None, alias="user.updated"
    )
    user_deleted: Dict[str, Any] = Field(
        None, alias="user.deleted"
    )
    certificate_created: Dict[str, Any] = Field(
        None, alias="certificate.created"
    )
    certificate_updated: Dict[str, Any] = Field(
        None, alias="certificate.updated"
    )
    certificate_deleted: Dict[str, Any] = Field(
        None, alias="certificate.deleted"
    )
    certificates_activated: Dict[str, Any] = Field(
        None, alias="certificates.activated"
    )
    certificates_deactivated: Dict[str, Any] = Field(
        None, alias="certificates.deactivated"
    )

class AuditLogActor(BaseModel):
    """The actor who performed the audit logged action."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["session", "api_key"] = Field(
        None, alias="type"
    )
    session: Dict[str, Any] = Field(
        None
    )
    api_key: Dict[str, Any] = Field(
        None
    )

class AuditLogActorApiKey(BaseModel):
    """The API Key used to perform the audit logged action."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        None, alias="id"
    )
    type_: Literal["user", "service_account"] = Field(
        None, alias="type"
    )
    user: Dict[str, Any] = Field(
        None
    )
    service_account: Dict[str, Any] = Field(
        None
    )

class AuditLogActorServiceAccount(BaseModel):
    """The service account that performed the audit logged action."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        None, alias="id"
    )

class AuditLogActorSession(BaseModel):
    """The session in which the audit logged action was performed."""
    model_config = ConfigDict(populate_by_name=True)

    user: Dict[str, Any] = Field(
        None
    )
    ip_address: str = Field(
        None
    )

class AuditLogActorUser(BaseModel):
    """The user who performed the audit logged action."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        None, alias="id"
    )
    email: str = Field(
        None
    )

class AuditLogEventType(str, Enum):
    """The event type."""
    API_KEY_CREATED = "api_key.created"
    API_KEY_UPDATED = "api_key.updated"
    API_KEY_DELETED = "api_key.deleted"
    CERTIFICATE_CREATED = "certificate.created"
    CERTIFICATE_UPDATED = "certificate.updated"
    CERTIFICATE_DELETED = "certificate.deleted"
    CERTIFICATES_ACTIVATED = "certificates.activated"
    CERTIFICATES_DEACTIVATED = "certificates.deactivated"
    CHECKPOINT_PERMISSION_CREATED = "checkpoint.permission.created"
    CHECKPOINT_PERMISSION_DELETED = "checkpoint.permission.deleted"
    EXTERNAL_KEY_REGISTERED = "external_key.registered"
    EXTERNAL_KEY_REMOVED = "external_key.removed"
    GROUP_CREATED = "group.created"
    GROUP_UPDATED = "group.updated"
    GROUP_DELETED = "group.deleted"
    INVITE_SENT = "invite.sent"
    INVITE_ACCEPTED = "invite.accepted"
    INVITE_DELETED = "invite.deleted"
    IP_ALLOWLIST_CREATED = "ip_allowlist.created"
    IP_ALLOWLIST_UPDATED = "ip_allowlist.updated"
    IP_ALLOWLIST_DELETED = "ip_allowlist.deleted"
    IP_ALLOWLIST_CONFIG_ACTIVATED = "ip_allowlist.config.activated"
    IP_ALLOWLIST_CONFIG_DEACTIVATED = "ip_allowlist.config.deactivated"
    LOGIN_SUCCEEDED = "login.succeeded"
    LOGIN_FAILED = "login.failed"
    LOGOUT_SUCCEEDED = "logout.succeeded"
    LOGOUT_FAILED = "logout.failed"
    ORGANIZATION_UPDATED = "organization.updated"
    PROJECT_CREATED = "project.created"
    PROJECT_UPDATED = "project.updated"
    PROJECT_ARCHIVED = "project.archived"
    PROJECT_DELETED = "project.deleted"
    RATE_LIMIT_UPDATED = "rate_limit.updated"
    RATE_LIMIT_DELETED = "rate_limit.deleted"
    RESOURCE_DELETED = "resource.deleted"
    TUNNEL_CREATED = "tunnel.created"
    TUNNEL_UPDATED = "tunnel.updated"
    TUNNEL_DELETED = "tunnel.deleted"
    ROLE_CREATED = "role.created"
    ROLE_UPDATED = "role.updated"
    ROLE_DELETED = "role.deleted"
    ROLE_ASSIGNMENT_CREATED = "role.assignment.created"
    ROLE_ASSIGNMENT_DELETED = "role.assignment.deleted"
    SCIM_ENABLED = "scim.enabled"
    SCIM_DISABLED = "scim.disabled"
    SERVICE_ACCOUNT_CREATED = "service_account.created"
    SERVICE_ACCOUNT_UPDATED = "service_account.updated"
    SERVICE_ACCOUNT_DELETED = "service_account.deleted"
    USER_ADDED = "user.added"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"

class AutoChunkingStrategyRequestParam(BaseModel):
    """The default strategy. This strategy currently uses a `max_chunk_size_tokens` of `800` and `chunk_overlap_tokens` of `400`."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["auto"] = Field(
        ..., alias="type"
    )

class Batch(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )
    object: Literal["batch"] = Field(
        ...
    )
    endpoint: str = Field(
        ...
    )
    model: str = Field(
        None
    )
    errors: Dict[str, Any] = Field(
        None
    )
    input_file_id: str = Field(
        ...
    )
    completion_window: str = Field(
        ...
    )
    status: Literal["validating", "failed", "in_progress", "finalizing", "completed", "expired", "cancelling", "cancelled"] = Field(
        ...
    )
    output_file_id: str = Field(
        None
    )
    error_file_id: str = Field(
        None
    )
    created_at: int = Field(
        ...
    )
    in_progress_at: int = Field(
        None
    )
    expires_at: int = Field(
        None
    )
    finalizing_at: int = Field(
        None
    )
    completed_at: int = Field(
        None
    )
    failed_at: int = Field(
        None
    )
    expired_at: int = Field(
        None
    )
    cancelling_at: int = Field(
        None
    )
    cancelled_at: int = Field(
        None
    )
    request_counts: Dict[str, Any] = Field(
        None
    )
    usage: Dict[str, Any] = Field(
        None
    )
    metadata: Dict[str, str] = Field(
        None
    )

class BatchFileExpirationAfter(BaseModel):
    """The expiration policy for the output and/or error file that are generated for a batch."""
    model_config = ConfigDict(populate_by_name=True)

    anchor: Literal["created_at"] = Field(
        ...
    )
    seconds: int = Field(
        ...
    )

class BatchRequestInput(BaseModel):
    """The per-line object of the batch input file"""
    model_config = ConfigDict(populate_by_name=True)

    custom_id: str = Field(
        None
    )
    method: Literal["POST"] = Field(
        None
    )
    url: str = Field(
        None
    )

class BatchRequestOutput(BaseModel):
    """The per-line object of the batch output and error files"""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        None, alias="id"
    )
    custom_id: str = Field(
        None
    )
    response: Dict[str, Any] = Field(
        None
    )
    error: Dict[str, Any] = Field(
        None
    )

class Certificate(BaseModel):
    """Represents an individual `certificate` uploaded to the organization."""
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["certificate", "organization.certificate", "organization.project.certificate"] = Field(
        ...
    )
    id_: str = Field(
        ..., alias="id"
    )
    name: str = Field(
        ...
    )
    created_at: int = Field(
        ...
    )
    certificate_details: Dict[str, Any] = Field(
        ...
    )
    active: bool = Field(
        None
    )

class ChatCompletionAllowedTools(BaseModel):
    """Constrains the tools available to the model to a pre-defined set."""
    model_config = ConfigDict(populate_by_name=True)

    mode: Literal["auto", "required"] = Field(
        ...
    )
    tools: List[Dict[str, Any]] = Field(
        ...
    )

class ChatCompletionAllowedToolsChoice(BaseModel):
    """Constrains the tools available to the model to a pre-defined set."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["allowed_tools"] = Field(
        ..., alias="type"
    )
    allowed_tools: AllowedTools = Field(
        ...
    )

class ChatCompletionDeleted(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["chat.completion.deleted"] = Field(
        ...
    )
    id_: str = Field(
        ..., alias="id"
    )
    deleted: bool = Field(
        ...
    )

class ChatCompletionFunctionCallOption(BaseModel):
    """Specifying a particular function via `{"name": "my_function"}` forces the model to call that function."""
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(
        ...
    )

class ChatCompletionFunctions(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    description: str = Field(
        None
    )
    name: str = Field(
        ...
    )
    parameters: Dict[str, Any] = Field(
        None
    )

class ChatCompletionList(BaseModel):
    """An object representing a list of Chat Completions."""
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["list"] = Field(
        ...
    )
    data: List[Dict[str, Any]] = Field(
        ...
    )
    first_id: str = Field(
        ...
    )
    last_id: str = Field(
        ...
    )
    has_more: bool = Field(
        ...
    )

class ChatCompletionMessageCustomToolCall(BaseModel):
    """A call to a custom tool created by the model."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )
    type_: Literal["custom"] = Field(
        ..., alias="type"
    )
    custom: Dict[str, Any] = Field(
        ...
    )

class ChatCompletionMessageList(BaseModel):
    """An object representing a list of chat completion messages."""
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["list"] = Field(
        ...
    )
    data: List[Dict[str, Any]] = Field(
        ...
    )
    first_id: str = Field(
        ...
    )
    last_id: str = Field(
        ...
    )
    has_more: bool = Field(
        ...
    )

class ChatCompletionMessageToolCall(BaseModel):
    """A call to a function tool created by the model."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )
    type_: Literal["function"] = Field(
        ..., alias="type"
    )
    function: Dict[str, Any] = Field(
        ...
    )

class ChatCompletionMessageToolCallChunk(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    index: int = Field(
        ...
    )
    id_: str = Field(
        None, alias="id"
    )
    type_: Literal["function"] = Field(
        None, alias="type"
    )
    function: Dict[str, Any] = Field(
        None
    )

class ChatCompletionMessageToolCalls(BaseModel):
    """The tool calls generated by the model, such as function calls."""
    model_config = ConfigDict(populate_by_name=True)

    pass

class ChatCompletionModalities(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class ChatCompletionNamedToolChoice(BaseModel):
    """Specifies a tool the model should use. Use to force the model to call a specific function."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["function"] = Field(
        ..., alias="type"
    )
    function: Dict[str, Any] = Field(
        ...
    )

class ChatCompletionNamedToolChoiceCustom(BaseModel):
    """Specifies a tool the model should use. Use to force the model to call a specific custom tool."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["custom"] = Field(
        ..., alias="type"
    )
    custom: Dict[str, Any] = Field(
        ...
    )

class ChatCompletionRequestAssistantMessage(BaseModel):
    """Messages sent by the model in response to user messages."""
    model_config = ConfigDict(populate_by_name=True)

    content: Union[str, List[Union[TextContentPart, RefusalContentPart]]] = Field(
        None
    )
    refusal: str = Field(
        None
    )
    role: Literal["assistant"] = Field(
        ...
    )
    name: str = Field(
        None
    )
    audio: Dict[str, Any] = Field(
        None
    )
    tool_calls: List[Union[FunctionToolCall, CustomToolCall]] = Field(
        None
    )
    function_call: Dict[str, Any] = Field(
        None
    )

class ChatCompletionRequestAssistantMessageContentPart(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class ChatCompletionRequestDeveloperMessage(BaseModel):
    """Developer-provided instructions that the model should follow, regardless of
messages sent by the user. With o1 models and newer, `developer` messages
replace the previous `system` messages."""
    model_config = ConfigDict(populate_by_name=True)

    content: Union[str, List[TextContentPart]] = Field(
        ...
    )
    role: Literal["developer"] = Field(
        ...
    )
    name: str = Field(
        None
    )

class ChatCompletionRequestFunctionMessage(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    role: Literal["function"] = Field(
        ...
    )
    content: str = Field(
        ...
    )
    name: str = Field(
        ...
    )

class ChatCompletionRequestMessage(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class ChatCompletionRequestMessageContentPartAudio(BaseModel):
    """Learn about [audio inputs](https://platform.openai.com/docs/guides/audio)."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["input_audio"] = Field(
        ..., alias="type"
    )
    input_audio: Dict[str, Any] = Field(
        ...
    )

class ChatCompletionRequestMessageContentPartFile(BaseModel):
    """Learn about [file inputs](https://platform.openai.com/docs/guides/text) for text generation."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["file"] = Field(
        ..., alias="type"
    )
    file: Dict[str, Any] = Field(
        ...
    )

class ChatCompletionRequestMessageContentPartImage(BaseModel):
    """Learn about [image inputs](https://platform.openai.com/docs/guides/vision)."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["image_url"] = Field(
        ..., alias="type"
    )
    image_url: Dict[str, Any] = Field(
        ...
    )

class ChatCompletionRequestMessageContentPartRefusal(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["refusal"] = Field(
        ..., alias="type"
    )
    refusal: str = Field(
        ...
    )

class ChatCompletionRequestMessageContentPartText(BaseModel):
    """Learn about [text inputs](https://platform.openai.com/docs/guides/text-generation)."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["text"] = Field(
        ..., alias="type"
    )
    text: str = Field(
        ...
    )

class ChatCompletionRequestSystemMessage(BaseModel):
    """Developer-provided instructions that the model should follow, regardless of
messages sent by the user. With o1 models and newer, use `developer` messages
for this purpose instead."""
    model_config = ConfigDict(populate_by_name=True)

    content: Union[str, List[TextContentPart]] = Field(
        ...
    )
    role: Literal["system"] = Field(
        ...
    )
    name: str = Field(
        None
    )

class ChatCompletionRequestSystemMessageContentPart(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class ChatCompletionRequestToolMessage(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    role: Literal["tool"] = Field(
        ...
    )
    content: Union[str, List[TextContentPart]] = Field(
        ...
    )
    tool_call_id: str = Field(
        ...
    )

class ChatCompletionRequestToolMessageContentPart(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class ChatCompletionRequestUserMessage(BaseModel):
    """Messages sent by an end user, containing prompts or additional context
information."""
    model_config = ConfigDict(populate_by_name=True)

    content: Union[str, List[Union[TextContentPart, ImageContentPart, AudioContentPart, FileContentPart]]] = Field(
        ...
    )
    role: Literal["user"] = Field(
        ...
    )
    name: str = Field(
        None
    )

class ChatCompletionRequestUserMessageContentPart(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class ChatCompletionResponseMessage(BaseModel):
    """A chat completion message generated by the model."""
    model_config = ConfigDict(populate_by_name=True)

    content: str = Field(
        ...
    )
    refusal: str = Field(
        ...
    )
    tool_calls: List[Union[FunctionToolCall, CustomToolCall]] = Field(
        None
    )
    annotations: List[Dict[str, Any]] = Field(
        None
    )
    role: Literal["assistant"] = Field(
        ...
    )
    function_call: Dict[str, Any] = Field(
        None
    )
    audio: Dict[str, Any] = Field(
        None
    )

class ChatCompletionRole(str, Enum):
    """The role of the author of a message"""
    DEVELOPER = "developer"
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
    FUNCTION = "function"

class ChatCompletionStreamOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class ChatCompletionStreamResponseDelta(BaseModel):
    """A chat completion delta generated by streamed model responses."""
    model_config = ConfigDict(populate_by_name=True)

    content: str = Field(
        None
    )
    function_call: Dict[str, Any] = Field(
        None
    )
    tool_calls: List[Dict[str, Any]] = Field(
        None
    )
    role: Literal["developer", "system", "user", "assistant", "tool"] = Field(
        None
    )
    refusal: str = Field(
        None
    )

class ChatCompletionTokenLogprob(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    token: str = Field(
        ...
    )
    logprob: float = Field(
        ...
    )
    bytes: List[int] = Field(
        ...
    )
    top_logprobs: List[Dict[str, Any]] = Field(
        ...
    )

class ChatCompletionTool(BaseModel):
    """A function tool that can be used to generate a response."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["function"] = Field(
        ..., alias="type"
    )
    function: Dict[str, Any] = Field(
        ...
    )

class ChatCompletionToolChoiceOption(BaseModel):
    """Controls which (if any) tool is called by the model.
`none` means the model will not call any tool and instead generates a message.
`auto` means the model can pick between generating a message or calling one or more tools.
`required` means the model must call one or more tools.
Specifying a particular tool via `{"type": "function", "function": {"name": "my_function"}}` forces the model to call that tool.

`none` is the default when no tools are present. `auto` is the default if tools are present."""
    model_config = ConfigDict(populate_by_name=True)

    pass

class ChunkingStrategyRequestParam(BaseModel):
    """The chunking strategy used to chunk the file(s). If not set, will use the `auto` strategy. Only applicable if `file_ids` is non-empty."""
    model_config = ConfigDict(populate_by_name=True)

    pass

class CodeInterpreterFileOutput(BaseModel):
    """The output of a code interpreter tool call that is a file."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["files"] = Field(
        ..., alias="type"
    )
    files: List[Dict[str, Any]] = Field(
        ...
    )

class CodeInterpreterTextOutput(BaseModel):
    """The output of a code interpreter tool call that is text."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["logs"] = Field(
        ..., alias="type"
    )
    logs: str = Field(
        ...
    )

class CodeInterpreterTool(BaseModel):
    """A tool that runs Python code to help generate a response to a prompt."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["code_interpreter"] = Field(
        ..., alias="type"
    )
    container: Union[str, CodeInterpreterToolAuto] = Field(
        ...
    )

class CodeInterpreterToolCall(BaseModel):
    """A tool call to run code."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["code_interpreter_call"] = Field(
        ..., alias="type"
    )
    id_: str = Field(
        ..., alias="id"
    )
    status: Literal["in_progress", "completed", "incomplete", "interpreting", "failed"] = Field(
        ...
    )
    container_id: str = Field(
        ...
    )
    code: str = Field(
        ...
    )
    outputs: List[Union[CodeInterpreterOutputLogs, CodeInterpreterOutputImage]] = Field(
        ...
    )

class ComparisonFilter(BaseModel):
    """A filter used to compare a specified attribute key to a given value using a defined comparison operation."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["eq", "ne", "gt", "gte", "lt", "lte"] = Field(
        ..., alias="type"
    )
    key: str = Field(
        ...
    )
    value: Union[str, float, bool, List[Union[str, float]]] = Field(
        ...
    )

class CompleteUploadRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    part_ids: List[str] = Field(
        ...
    )
    md_5: str = Field(
        None, alias="md5"
    )

class CompletionUsage(BaseModel):
    """Usage statistics for the completion request."""
    model_config = ConfigDict(populate_by_name=True)

    completion_tokens: int = Field(
        ...
    )
    prompt_tokens: int = Field(
        ...
    )
    total_tokens: int = Field(
        ...
    )
    completion_tokens_details: Dict[str, Any] = Field(
        None
    )
    prompt_tokens_details: Dict[str, Any] = Field(
        None
    )

class CompoundFilter(BaseModel):
    """Combine multiple filters using `and` or `or`."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["and", "or"] = Field(
        ..., alias="type"
    )
    filters: List[ComparisonFilter] = Field(
        ...
    )

class ComputerAction(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class ComputerScreenshotImage(BaseModel):
    """A computer screenshot image used with the computer use tool."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["computer_screenshot"] = Field(
        ..., alias="type"
    )
    image_url: str = Field(
        None
    )
    file_id: str = Field(
        None
    )

class ComputerToolCall(BaseModel):
    """A tool call to a computer use tool. See the
[computer use guide](https://platform.openai.com/docs/guides/tools-computer-use) for more information."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["computer_call"] = Field(
        ..., alias="type"
    )
    id_: str = Field(
        ..., alias="id"
    )
    call_id: str = Field(
        ...
    )
    action: Union[Click, DoubleClick, Drag, KeyPress, Move, Screenshot, Scroll, Type, Wait] = Field(
        ...
    )
    pending_safety_checks: List[Dict[str, Any]] = Field(
        ...
    )
    status: Literal["in_progress", "completed", "incomplete"] = Field(
        ...
    )

class ComputerToolCallOutput(BaseModel):
    """The output of a computer tool call."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["computer_call_output"] = Field(
        ..., alias="type"
    )
    id_: str = Field(
        None, alias="id"
    )
    call_id: str = Field(
        ...
    )
    acknowledged_safety_checks: List[Dict[str, Any]] = Field(
        None
    )
    output: Dict[str, Any] = Field(
        ...
    )
    status: Literal["in_progress", "completed", "incomplete"] = Field(
        None
    )

class ComputerToolCallOutputResource(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class ContainerFileListResource(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    object: Any = Field(
        ...
    )
    data: List[TheContainerFileObject] = Field(
        ...
    )
    first_id: str = Field(
        ...
    )
    last_id: str = Field(
        ...
    )
    has_more: bool = Field(
        ...
    )

class ContainerFileResource(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )
    object: str = Field(
        ...
    )
    container_id: str = Field(
        ...
    )
    created_at: int = Field(
        ...
    )
    bytes: int = Field(
        ...
    )
    path: str = Field(
        ...
    )
    source: str = Field(
        ...
    )

class ContainerListResource(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    object: Any = Field(
        ...
    )
    data: List[TheContainerObject] = Field(
        ...
    )
    first_id: str = Field(
        ...
    )
    last_id: str = Field(
        ...
    )
    has_more: bool = Field(
        ...
    )

class ContainerResource(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )
    object: str = Field(
        ...
    )
    name: str = Field(
        ...
    )
    created_at: int = Field(
        ...
    )
    status: str = Field(
        ...
    )
    last_active_at: int = Field(
        None
    )
    expires_after: Dict[str, Any] = Field(
        None
    )
    memory_limit: Literal["1g", "4g", "16g", "64g"] = Field(
        None
    )

class Content(BaseModel):
    """Multi-modal input and output contents."""
    model_config = ConfigDict(populate_by_name=True)

    pass

class Conversation(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class ConversationItem(BaseModel):
    """A single item within a conversation. The set of possible types are the same as the `output` type of a [Response object](https://platform.openai.com/docs/api-reference/responses/object#responses/object-output)."""
    model_config = ConfigDict(populate_by_name=True)

    pass

class ConversationItemList(BaseModel):
    """A list of Conversation items."""
    model_config = ConfigDict(populate_by_name=True)

    object: Any = Field(
        ...
    )
    data: List[Union[Message, FunctionToolCall, FunctionToolCallOutput, FileSearchToolCall, WebSearchToolCall, ImageGenerationCall, ComputerToolCall, ComputerToolCallOutput, Reasoning, CodeInterpreterToolCall, LocalShellCall, LocalShellCallOutput, ShellToolCall, ShellCallOutput, ApplyPatchToolCall, ApplyPatchToolCallOutput, McpListTools, McpApprovalRequest, McpApprovalResponse, McpToolCall, CustomToolCall, CustomToolCallOutput]] = Field(
        ...
    )
    has_more: bool = Field(
        ...
    )
    first_id: str = Field(
        ...
    )
    last_id: str = Field(
        ...
    )

class ConversationParam(BaseModel):
    """The conversation that this response belongs to. Items from this conversation are prepended to `input_items` for this response request.
Input items and output items from this response are automatically added to this conversation after this response completes."""
    model_config = ConfigDict(populate_by_name=True)

    pass

class CostsResult(BaseModel):
    """The aggregated costs details of the specific time bucket."""
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["organization.costs.result"] = Field(
        ...
    )
    amount: Dict[str, Any] = Field(
        None
    )
    line_item: str = Field(
        None
    )
    project_id: str = Field(
        None
    )

class CreateAssistantRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    model: Union[str, Literal["gpt-5", "gpt-5-mini", "gpt-5-nano", "gpt-5-2025-08-07", "gpt-5-mini-2025-08-07", "gpt-5-nano-2025-08-07", "gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano", "gpt-4.1-2025-04-14", "gpt-4.1-mini-2025-04-14", "gpt-4.1-nano-2025-04-14", "o3-mini", "o3-mini-2025-01-31", "o1", "o1-2024-12-17", "gpt-4o", "gpt-4o-2024-11-20", "gpt-4o-2024-08-06", "gpt-4o-2024-05-13", "gpt-4o-mini", "gpt-4o-mini-2024-07-18", "gpt-4.5-preview", "gpt-4.5-preview-2025-02-27", "gpt-4-turbo", "gpt-4-turbo-2024-04-09", "gpt-4-0125-preview", "gpt-4-turbo-preview", "gpt-4-1106-preview", "gpt-4-vision-preview", "gpt-4", "gpt-4-0314", "gpt-4-0613", "gpt-4-32k", "gpt-4-32k-0314", "gpt-4-32k-0613", "gpt-3.5-turbo", "gpt-3.5-turbo-16k", "gpt-3.5-turbo-0613", "gpt-3.5-turbo-1106", "gpt-3.5-turbo-0125", "gpt-3.5-turbo-16k-0613"]] = Field(
        ...
    )
    name: str = Field(
        None
    )
    description: str = Field(
        None
    )
    instructions: str = Field(
        None
    )
    reasoning_effort: Literal["none", "minimal", "low", "medium", "high", "xhigh"] = Field(
        None
    )
    tools: List[Union[CodeInterpreterTool, FileSearchTool, FunctionTool]] = Field(
        None
    )
    tool_resources: Dict[str, Any] = Field(
        None
    )
    metadata: Dict[str, str] = Field(
        None
    )
    temperature: float = Field(
        None
    )
    top_p: float = Field(
        None
    )
    response_format: Union[Literal["auto"], Text, JsonObject, JsonSchema] = Field(
        None
    )

class CreateChatCompletionRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class CreateChatCompletionResponse(BaseModel):
    """Represents a chat completion response returned by model, based on the provided input."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )
    choices: List[Dict[str, Any]] = Field(
        ...
    )
    created: int = Field(
        ...
    )
    model: str = Field(
        ...
    )
    service_tier: Literal["auto", "default", "flex", "scale", "priority"] = Field(
        None
    )
    system_fingerprint: str = Field(
        None
    )
    object: Literal["chat.completion"] = Field(
        ...
    )
    usage: Dict[str, Any] = Field(
        None
    )

class CreateChatCompletionStreamResponse(BaseModel):
    """Represents a streamed chunk of a chat completion response returned
by the model, based on the provided input. 
[Learn more](https://platform.openai.com/docs/guides/streaming-responses)."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )
    choices: List[Dict[str, Any]] = Field(
        ...
    )
    created: int = Field(
        ...
    )
    model: str = Field(
        ...
    )
    service_tier: Literal["auto", "default", "flex", "scale", "priority"] = Field(
        None
    )
    system_fingerprint: str = Field(
        None
    )
    object: Literal["chat.completion.chunk"] = Field(
        ...
    )
    usage: Optional[Dict[str, Any]] = Field(
        None
    )

class CreateCompletionRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    model: Union[str, Literal["gpt-3.5-turbo-instruct", "davinci-002", "babbage-002"]] = Field(
        ...
    )
    prompt: Union[str, List[str], List[int], List[List[int]]] = Field(
        ...
    )
    best_of: Optional[int] = Field(
        None
    )
    echo: Optional[bool] = Field(
        None
    )
    frequency_penalty: Optional[float] = Field(
        None
    )
    logit_bias: Optional[Dict[str, int]] = Field(
        None
    )
    logprobs: Optional[int] = Field(
        None
    )
    max_tokens: Optional[int] = Field(
        None
    )
    n: Optional[int] = Field(
        None
    )
    presence_penalty: Optional[float] = Field(
        None
    )
    seed: Optional[int] = Field(
        None
    )
    stop: Union[Optional[str], List[str]] = Field(
        None
    )
    stream: Optional[bool] = Field(
        None
    )
    stream_options: Dict[str, Any] = Field(
        None
    )
    suffix: Optional[str] = Field(
        None
    )
    temperature: Optional[float] = Field(
        None
    )
    top_p: Optional[float] = Field(
        None
    )
    user: str = Field(
        None
    )

class CreateCompletionResponse(BaseModel):
    """Represents a completion response from the API. Note: both the streamed and non-streamed response objects share the same shape (unlike the chat endpoint)."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )
    choices: List[Dict[str, Any]] = Field(
        ...
    )
    created: int = Field(
        ...
    )
    model: str = Field(
        ...
    )
    system_fingerprint: str = Field(
        None
    )
    object: Literal["text_completion"] = Field(
        ...
    )
    usage: Dict[str, Any] = Field(
        None
    )

class CreateContainerBody(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(
        ...
    )
    file_ids: List[str] = Field(
        None
    )
    expires_after: Dict[str, Any] = Field(
        None
    )
    memory_limit: Literal["1g", "4g", "16g", "64g"] = Field(
        None
    )

class CreateContainerFileBody(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    file_id: str = Field(
        None
    )
    file: bytes = Field(
        None
    )

class CreateEmbeddingRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    input: Union[str, List[str], List[int], List[List[int]]] = Field(
        ...
    )
    model: Union[str, Literal["text-embedding-ada-002", "text-embedding-3-small", "text-embedding-3-large"]] = Field(
        ...
    )
    encoding_format: Literal["float", "base64"] = Field(
        None
    )
    dimensions: int = Field(
        None
    )
    user: str = Field(
        None
    )

class CreateEmbeddingResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    data: List[Dict[str, Any]] = Field(
        ...
    )
    model: str = Field(
        ...
    )
    object: Literal["list"] = Field(
        ...
    )
    usage: Dict[str, Any] = Field(
        ...
    )

class CreateEvalCompletionsRunDataSource(BaseModel):
    """A CompletionsRunDataSource object describing a model sampling configuration."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["completions"] = Field(
        ..., alias="type"
    )
    input_messages: Union[TemplateInputMessages, ItemReferenceInputMessages] = Field(
        None
    )
    sampling_params: Dict[str, Any] = Field(
        None
    )
    model: str = Field(
        None
    )
    source: Union[EvalJsonlFileContentSource, EvalJsonlFileIdSource, StoredCompletionsRunDataSource] = Field(
        ...
    )

class CreateEvalCustomDataSourceConfig(BaseModel):
    """A CustomDataSourceConfig object that defines the schema for the data source used for the evaluation runs.
This schema is used to define the shape of the data that will be:
- Used to define your testing criteria and
- What data is required when creating a run"""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["custom"] = Field(
        ..., alias="type"
    )
    item_schema: Dict[str, Any] = Field(
        ...
    )
    include_sample_schema: bool = Field(
        None
    )

class CreateEvalItem(BaseModel):
    """A chat message that makes up the prompt or context. May include variable references to the `item` namespace, ie {{item.name}}."""
    model_config = ConfigDict(populate_by_name=True)

    pass

class CreateEvalJsonlRunDataSource(BaseModel):
    """A JsonlRunDataSource object with that specifies a JSONL file that matches the eval"""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["jsonl"] = Field(
        ..., alias="type"
    )
    source: Union[EvalJsonlFileContentSource, EvalJsonlFileIdSource] = Field(
        ...
    )

class CreateEvalLabelModelGrader(BaseModel):
    """A LabelModelGrader object which uses a model to assign labels to each item
in the evaluation."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["label_model"] = Field(
        ..., alias="type"
    )
    name: str = Field(
        ...
    )
    model: str = Field(
        ...
    )
    input: List[Union[SimpleInputMessage, EvalItem]] = Field(
        ...
    )
    labels: List[str] = Field(
        ...
    )
    passing_labels: List[str] = Field(
        ...
    )

class CreateEvalLogsDataSourceConfig(BaseModel):
    """A data source config which specifies the metadata property of your logs query.
This is usually metadata like `usecase=chatbot` or `prompt-version=v2`, etc."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["logs"] = Field(
        ..., alias="type"
    )
    metadata: Dict[str, Any] = Field(
        None
    )

class CreateEvalRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(
        None
    )
    metadata: Dict[str, str] = Field(
        None
    )
    data_source_config: Union[CustomDataSourceConfig, LogsDataSourceConfig, StoredCompletionsDataSourceConfig] = Field(
        ...
    )
    testing_criteria: List[Union[LabelModelGrader, StringCheckGrader, TextSimilarityGrader, PythonGrader, ScoreModelGrader]] = Field(
        ...
    )

class CreateEvalResponsesRunDataSource(BaseModel):
    """A ResponsesRunDataSource object describing a model sampling configuration."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["responses"] = Field(
        ..., alias="type"
    )
    input_messages: Union[InputMessagesTemplate, InputMessagesItemReference] = Field(
        None
    )
    sampling_params: Dict[str, Any] = Field(
        None
    )
    model: str = Field(
        None
    )
    source: Union[EvalJsonlFileContentSource, EvalJsonlFileIdSource, EvalResponsesSource] = Field(
        ...
    )

class CreateEvalRunRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(
        None
    )
    metadata: Dict[str, str] = Field(
        None
    )
    data_source: Union[JsonlRunDataSource, CompletionsRunDataSource, CreateEvalResponsesRunDataSource] = Field(
        ...
    )

class CreateEvalStoredCompletionsDataSourceConfig(BaseModel):
    """Deprecated in favor of LogsDataSourceConfig."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["stored_completions"] = Field(
        ..., alias="type"
    )
    metadata: Dict[str, Any] = Field(
        None
    )

class CreateFileRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    file: bytes = Field(
        ...
    )
    purpose: Literal["assistants", "batch", "fine-tune", "vision", "user_data", "evals"] = Field(
        ...
    )
    expires_after: FileExpirationPolicy = Field(
        None
    )

class CreateFineTuningCheckpointPermissionRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    project_ids: List[str] = Field(
        ...
    )

class CreateFineTuningJobRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    model: Union[str, Literal["babbage-002", "davinci-002", "gpt-3.5-turbo", "gpt-4o-mini"]] = Field(
        ...
    )
    training_file: str = Field(
        ...
    )
    hyperparameters: Dict[str, Any] = Field(
        None
    )
    suffix: Optional[str] = Field(
        None
    )
    validation_file: Optional[str] = Field(
        None
    )
    integrations: Optional[List[Dict[str, Any]]] = Field(
        None
    )
    seed: Optional[int] = Field(
        None
    )
    method: Dict[str, Any] = Field(
        None
    )
    metadata: Dict[str, str] = Field(
        None
    )

class CreateGroupBody(BaseModel):
    """Request payload for creating a new group in the organization."""
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(
        ...
    )

class CreateGroupUserBody(BaseModel):
    """Request payload for adding a user to a group."""
    model_config = ConfigDict(populate_by_name=True)

    user_id: str = Field(
        ...
    )

class CreateImageEditRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    image: Union[bytes, List[bytes]] = Field(
        ...
    )
    prompt: str = Field(
        ...
    )
    mask: bytes = Field(
        None
    )
    background: Optional[Literal["transparent", "opaque", "auto"]] = Field(
        None
    )
    model: Union[str, Literal["gpt-image-1.5", "dall-e-2", "gpt-image-1", "gpt-image-1-mini"]] = Field(
        None
    )
    n: Optional[int] = Field(
        None
    )
    size: Optional[Literal["256x256", "512x512", "1024x1024", "1536x1024", "1024x1536", "auto"]] = Field(
        None
    )
    response_format: Optional[Literal["url", "b64_json"]] = Field(
        None
    )
    output_format: Optional[Literal["png", "jpeg", "webp"]] = Field(
        None
    )
    output_compression: Optional[int] = Field(
        None
    )
    user: str = Field(
        None
    )
    input_fidelity: Literal["high", "low"] = Field(
        None
    )
    stream: Optional[bool] = Field(
        None
    )
    partial_images: int = Field(
        None
    )
    quality: Optional[Literal["standard", "low", "medium", "high", "auto"]] = Field(
        None
    )

class CreateImageRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    prompt: str = Field(
        ...
    )
    model: Union[str, Literal["gpt-image-1.5", "dall-e-2", "dall-e-3", "gpt-image-1", "gpt-image-1-mini"]] = Field(
        None
    )
    n: Optional[int] = Field(
        None
    )
    quality: Optional[Literal["standard", "hd", "low", "medium", "high", "auto"]] = Field(
        None
    )
    response_format: Optional[Literal["url", "b64_json"]] = Field(
        None
    )
    output_format: Optional[Literal["png", "jpeg", "webp"]] = Field(
        None
    )
    output_compression: Optional[int] = Field(
        None
    )
    stream: Optional[bool] = Field(
        None
    )
    partial_images: int = Field(
        None
    )
    size: Optional[Literal["auto", "1024x1024", "1536x1024", "1024x1536", "256x256", "512x512", "1792x1024", "1024x1792"]] = Field(
        None
    )
    moderation: Optional[Literal["low", "auto"]] = Field(
        None
    )
    background: Optional[Literal["transparent", "opaque", "auto"]] = Field(
        None
    )
    style: Optional[Literal["vivid", "natural"]] = Field(
        None
    )
    user: str = Field(
        None
    )

class CreateImageVariationRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    image: bytes = Field(
        ...
    )
    model: Union[str, Literal["dall-e-2"]] = Field(
        None
    )
    n: Optional[int] = Field(
        None
    )
    response_format: Optional[Literal["url", "b64_json"]] = Field(
        None
    )
    size: Optional[Literal["256x256", "512x512", "1024x1024"]] = Field(
        None
    )
    user: str = Field(
        None
    )

class CreateMessageRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    role: Literal["user", "assistant"] = Field(
        ...
    )
    content: Union[str, List[Union[ImageFile, ImageUrl, Text]]] = Field(
        ...
    )
    attachments: List[Dict[str, Any]] = Field(
        None
    )
    metadata: Dict[str, str] = Field(
        None
    )

class CreateModelResponseProperties(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class CreateModerationRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    input: Union[str, List[str], List[Union[Dict[str, Any]]]] = Field(
        ...
    )
    model: Union[str, Literal["omni-moderation-latest", "omni-moderation-2024-09-26", "text-moderation-latest", "text-moderation-stable"]] = Field(
        None
    )

class CreateModerationResponse(BaseModel):
    """Represents if a given text input is potentially harmful."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )
    model: str = Field(
        ...
    )
    results: List[Dict[str, Any]] = Field(
        ...
    )

class CreateResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class CreateRunRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    assistant_id: str = Field(
        ...
    )
    model: Union[str, Literal["gpt-5", "gpt-5-mini", "gpt-5-nano", "gpt-5-2025-08-07", "gpt-5-mini-2025-08-07", "gpt-5-nano-2025-08-07", "gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano", "gpt-4.1-2025-04-14", "gpt-4.1-mini-2025-04-14", "gpt-4.1-nano-2025-04-14", "o3-mini", "o3-mini-2025-01-31", "o1", "o1-2024-12-17", "gpt-4o", "gpt-4o-2024-11-20", "gpt-4o-2024-08-06", "gpt-4o-2024-05-13", "gpt-4o-mini", "gpt-4o-mini-2024-07-18", "gpt-4.5-preview", "gpt-4.5-preview-2025-02-27", "gpt-4-turbo", "gpt-4-turbo-2024-04-09", "gpt-4-0125-preview", "gpt-4-turbo-preview", "gpt-4-1106-preview", "gpt-4-vision-preview", "gpt-4", "gpt-4-0314", "gpt-4-0613", "gpt-4-32k", "gpt-4-32k-0314", "gpt-4-32k-0613", "gpt-3.5-turbo", "gpt-3.5-turbo-16k", "gpt-3.5-turbo-0613", "gpt-3.5-turbo-1106", "gpt-3.5-turbo-0125", "gpt-3.5-turbo-16k-0613"]] = Field(
        None
    )
    reasoning_effort: Literal["none", "minimal", "low", "medium", "high", "xhigh"] = Field(
        None
    )
    instructions: Optional[str] = Field(
        None
    )
    additional_instructions: Optional[str] = Field(
        None
    )
    additional_messages: Optional[List[Dict[str, Any]]] = Field(
        None
    )
    tools: Optional[List[Union[CodeInterpreterTool, FileSearchTool, FunctionTool]]] = Field(
        None
    )
    metadata: Dict[str, str] = Field(
        None
    )
    temperature: Optional[float] = Field(
        None
    )
    top_p: Optional[float] = Field(
        None
    )
    stream: Optional[bool] = Field(
        None
    )
    max_prompt_tokens: Optional[int] = Field(
        None
    )
    max_completion_tokens: Optional[int] = Field(
        None
    )
    truncation_strategy: ThreadTruncationControls = Field(
        None
    )
    tool_choice: Union[Literal["none", "auto", "required"], Dict[str, Any]] = Field(
        None
    )
    parallel_tool_calls: bool = Field(
        None
    )
    response_format: Union[Literal["auto"], Text, JsonObject, JsonSchema] = Field(
        None
    )

class CreateSpeechRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    model: Union[str, Literal["tts-1", "tts-1-hd", "gpt-4o-mini-tts"]] = Field(
        ...
    )
    input: str = Field(
        ...
    )
    instructions: str = Field(
        None
    )
    voice: Union[str, Literal["alloy", "ash", "ballad", "coral", "echo", "sage", "shimmer", "verse", "marin", "cedar"]] = Field(
        ...
    )
    response_format: Literal["mp3", "opus", "aac", "flac", "wav", "pcm"] = Field(
        None
    )
    speed: float = Field(
        None
    )
    stream_format: Literal["sse", "audio"] = Field(
        None
    )

class CreateSpeechResponseStreamEvent(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class CreateThreadAndRunRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    assistant_id: str = Field(
        ...
    )
    thread: Dict[str, Any] = Field(
        None
    )
    model: Union[str, Literal["gpt-5", "gpt-5-mini", "gpt-5-nano", "gpt-5-2025-08-07", "gpt-5-mini-2025-08-07", "gpt-5-nano-2025-08-07", "gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano", "gpt-4.1-2025-04-14", "gpt-4.1-mini-2025-04-14", "gpt-4.1-nano-2025-04-14", "gpt-4o", "gpt-4o-2024-11-20", "gpt-4o-2024-08-06", "gpt-4o-2024-05-13", "gpt-4o-mini", "gpt-4o-mini-2024-07-18", "gpt-4.5-preview", "gpt-4.5-preview-2025-02-27", "gpt-4-turbo", "gpt-4-turbo-2024-04-09", "gpt-4-0125-preview", "gpt-4-turbo-preview", "gpt-4-1106-preview", "gpt-4-vision-preview", "gpt-4", "gpt-4-0314", "gpt-4-0613", "gpt-4-32k", "gpt-4-32k-0314", "gpt-4-32k-0613", "gpt-3.5-turbo", "gpt-3.5-turbo-16k", "gpt-3.5-turbo-0613", "gpt-3.5-turbo-1106", "gpt-3.5-turbo-0125", "gpt-3.5-turbo-16k-0613"]] = Field(
        None
    )
    instructions: Optional[str] = Field(
        None
    )
    tools: Optional[List[Union[CodeInterpreterTool, FileSearchTool, FunctionTool]]] = Field(
        None
    )
    tool_resources: Optional[Dict[str, Any]] = Field(
        None
    )
    metadata: Dict[str, str] = Field(
        None
    )
    temperature: Optional[float] = Field(
        None
    )
    top_p: Optional[float] = Field(
        None
    )
    stream: Optional[bool] = Field(
        None
    )
    max_prompt_tokens: Optional[int] = Field(
        None
    )
    max_completion_tokens: Optional[int] = Field(
        None
    )
    truncation_strategy: ThreadTruncationControls = Field(
        None
    )
    tool_choice: Union[Literal["none", "auto", "required"], Dict[str, Any]] = Field(
        None
    )
    parallel_tool_calls: bool = Field(
        None
    )
    response_format: Union[Literal["auto"], Text, JsonObject, JsonSchema] = Field(
        None
    )

class CreateThreadRequest(BaseModel):
    """Options to create a new thread. If no thread is provided when running a
request, an empty thread will be created."""
    model_config = ConfigDict(populate_by_name=True)

    messages: List[Dict[str, Any]] = Field(
        None
    )
    tool_resources: Dict[str, Any] = Field(
        None
    )
    metadata: Dict[str, str] = Field(
        None
    )

class CreateTranscriptionRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    file: bytes = Field(
        ...
    )
    model: Union[str, Literal["whisper-1", "gpt-4o-transcribe", "gpt-4o-mini-transcribe", "gpt-4o-transcribe-diarize"]] = Field(
        ...
    )
    language: str = Field(
        None
    )
    prompt: str = Field(
        None
    )
    response_format: Literal["json", "text", "srt", "verbose_json", "vtt", "diarized_json"] = Field(
        None
    )
    temperature: float = Field(
        None
    )
    include: List[Literal["logprobs"]] = Field(
        None
    )
    timestamp_granularities: List[Literal["word", "segment"]] = Field(
        None
    )
    stream: bool = Field(
        None
    )
    chunking_strategy: Union[Literal["auto"], Dict[str, Any]] = Field(
        None
    )
    known_speaker_names: List[str] = Field(
        None
    )
    known_speaker_references: List[str] = Field(
        None
    )

class CreateTranscriptionResponseDiarizedJson(BaseModel):
    """Represents a diarized transcription response returned by the model, including the combined transcript and speaker-segment annotations."""
    model_config = ConfigDict(populate_by_name=True)

    task: Literal["transcribe"] = Field(
        ...
    )
    duration: float = Field(
        ...
    )
    text: str = Field(
        ...
    )
    segments: List[Dict[str, Any]] = Field(
        ...
    )
    usage: Union[TokenUsage, DurationUsage] = Field(
        None
    )

class CreateTranscriptionResponseJson(BaseModel):
    """Represents a transcription response returned by model, based on the provided input."""
    model_config = ConfigDict(populate_by_name=True)

    text: str = Field(
        ...
    )
    logprobs: List[Dict[str, Any]] = Field(
        None
    )
    usage: Union[TokenUsage, DurationUsage] = Field(
        None
    )

class CreateTranscriptionResponseStreamEvent(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class CreateTranscriptionResponseVerboseJson(BaseModel):
    """Represents a verbose json transcription response returned by model, based on the provided input."""
    model_config = ConfigDict(populate_by_name=True)

    language: str = Field(
        ...
    )
    duration: float = Field(
        ...
    )
    text: str = Field(
        ...
    )
    words: List[Dict[str, Any]] = Field(
        None
    )
    segments: List[Dict[str, Any]] = Field(
        None
    )
    usage: TranscriptTextUsageDuration = Field(
        None
    )

class CreateTranslationRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    file: bytes = Field(
        ...
    )
    model: Union[str, Literal["whisper-1"]] = Field(
        ...
    )
    prompt: str = Field(
        None
    )
    response_format: Literal["json", "text", "srt", "verbose_json", "vtt"] = Field(
        None
    )
    temperature: float = Field(
        None
    )

class CreateTranslationResponseJson(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    text: str = Field(
        ...
    )

class CreateTranslationResponseVerboseJson(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    language: str = Field(
        ...
    )
    duration: float = Field(
        ...
    )
    text: str = Field(
        ...
    )
    segments: List[Dict[str, Any]] = Field(
        None
    )

class CreateUploadRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    filename: str = Field(
        ...
    )
    purpose: Literal["assistants", "batch", "fine-tune", "vision"] = Field(
        ...
    )
    bytes: int = Field(
        ...
    )
    mime_type: str = Field(
        ...
    )
    expires_after: FileExpirationPolicy = Field(
        None
    )

class CreateVectorStoreFileBatchRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    file_ids: List[str] = Field(
        None
    )
    files: List[Dict[str, Any]] = Field(
        None
    )
    chunking_strategy: Union[AutoChunkingStrategy, StaticChunkingStrategy] = Field(
        None
    )
    attributes: Dict[str, Union[str, float, bool]] = Field(
        None
    )

class CreateVectorStoreFileRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    file_id: str = Field(
        ...
    )
    chunking_strategy: Union[AutoChunkingStrategy, StaticChunkingStrategy] = Field(
        None
    )
    attributes: Dict[str, Union[str, float, bool]] = Field(
        None
    )

class CreateVectorStoreRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    file_ids: List[str] = Field(
        None
    )
    name: str = Field(
        None
    )
    description: str = Field(
        None
    )
    expires_after: VectorStoreExpirationPolicy = Field(
        None
    )
    chunking_strategy: Union[AutoChunkingStrategy, StaticChunkingStrategy] = Field(
        None
    )
    metadata: Dict[str, str] = Field(
        None
    )

class CreateVoiceConsentRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(
        ...
    )
    recording: bytes = Field(
        ...
    )
    language: str = Field(
        ...
    )

class CreateVoiceRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(
        ...
    )
    audio_sample: bytes = Field(
        ...
    )
    consent: str = Field(
        ...
    )

class CustomToolCall(BaseModel):
    """A call to a custom tool created by the model."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["custom_tool_call"] = Field(
        ..., alias="type"
    )
    id_: str = Field(
        None, alias="id"
    )
    call_id: str = Field(
        ...
    )
    name: str = Field(
        ...
    )
    input: str = Field(
        ...
    )

class CustomToolCallOutput(BaseModel):
    """The output of a custom tool call from your code, being sent back to the model."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["custom_tool_call_output"] = Field(
        ..., alias="type"
    )
    id_: str = Field(
        None, alias="id"
    )
    call_id: str = Field(
        ...
    )
    output: Union[str, List[Union[InputText, InputImage, InputFile]]] = Field(
        ...
    )

class CustomToolChatCompletions(BaseModel):
    """A custom tool that processes input using a specified format."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["custom"] = Field(
        ..., alias="type"
    )
    custom: CustomToolProperties = Field(
        ...
    )

class DeleteAssistantResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )
    deleted: bool = Field(
        ...
    )
    object: Literal["assistant.deleted"] = Field(
        ...
    )

class DeleteCertificateResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    object: Any = Field(
        ...
    )
    id_: str = Field(
        ..., alias="id"
    )

class DeleteFileResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )
    object: Literal["file"] = Field(
        ...
    )
    deleted: bool = Field(
        ...
    )

class DeleteFineTuningCheckpointPermissionResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )
    object: Literal["checkpoint.permission"] = Field(
        ...
    )
    deleted: bool = Field(
        ...
    )

class DeleteMessageResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )
    deleted: bool = Field(
        ...
    )
    object: Literal["thread.message.deleted"] = Field(
        ...
    )

class DeleteModelResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )
    deleted: bool = Field(
        ...
    )
    object: str = Field(
        ...
    )

class DeleteThreadResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )
    deleted: bool = Field(
        ...
    )
    object: Literal["thread.deleted"] = Field(
        ...
    )

class DeleteVectorStoreFileResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )
    deleted: bool = Field(
        ...
    )
    object: Literal["vector_store.file.deleted"] = Field(
        ...
    )

class DeleteVectorStoreResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )
    deleted: bool = Field(
        ...
    )
    object: Literal["vector_store.deleted"] = Field(
        ...
    )

class DeletedConversation(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class DeletedRoleAssignmentResource(BaseModel):
    """Confirmation payload returned after unassigning a role."""
    model_config = ConfigDict(populate_by_name=True)

    object: str = Field(
        ...
    )
    deleted: bool = Field(
        ...
    )

class DoneEvent(BaseModel):
    """Occurs when a stream ends."""
    model_config = ConfigDict(populate_by_name=True)

    event: Literal["done"] = Field(
        ...
    )
    data: Literal["[DONE]"] = Field(
        ...
    )

class Drag(BaseModel):
    """A drag action."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["drag"] = Field(
        ..., alias="type"
    )
    path: List[Coordinate] = Field(
        ...
    )

class EasyInputMessage(BaseModel):
    """A message input to the model with a role indicating instruction following
hierarchy. Instructions given with the `developer` or `system` role take
precedence over instructions given with the `user` role. Messages with the
`assistant` role are presumed to have been generated by the model in previous
interactions."""
    model_config = ConfigDict(populate_by_name=True)

    role: Literal["user", "assistant", "system", "developer"] = Field(
        ...
    )
    content: Union[str, List[Union[InputText, InputImage, InputFile]]] = Field(
        ...
    )
    type_: Literal["message"] = Field(
        None, alias="type"
    )

class Embedding(BaseModel):
    """Represents an embedding vector returned by embedding endpoint."""
    model_config = ConfigDict(populate_by_name=True)

    index: int = Field(
        ...
    )
    embedding: List[float] = Field(
        ...
    )
    object: Literal["embedding"] = Field(
        ...
    )

class Error(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    code: str = Field(
        ...
    )
    message: str = Field(
        ...
    )
    param: str = Field(
        ...
    )
    type_: str = Field(
        ..., alias="type"
    )

class ErrorEvent(BaseModel):
    """Occurs when an [error](https://platform.openai.com/docs/guides/error-codes#api-errors) occurs. This can happen due to an internal server error or a timeout."""
    model_config = ConfigDict(populate_by_name=True)

    event: Literal["error"] = Field(
        ...
    )
    data: Dict[str, Any] = Field(
        ...
    )

class ErrorResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    error: Dict[str, Any] = Field(
        ...
    )

class Eval(BaseModel):
    """An Eval object with a data source config and testing criteria.
An Eval represents a task to be done for your LLM integration.
Like:
 - Improve the quality of my chatbot
 - See how well my chatbot handles customer support
 - Check if o4-mini is better at my usecase than gpt-4o"""
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["eval"] = Field(
        ...
    )
    id_: str = Field(
        ..., alias="id"
    )
    name: str = Field(
        ...
    )
    data_source_config: Union[CustomDataSourceConfig, LogsDataSourceConfig, StoredCompletionsDataSourceConfig] = Field(
        ...
    )
    testing_criteria: List[Union[LabelModelGrader, StringCheckGrader, TextSimilarityGrader, PythonGrader, ScoreModelGrader]] = Field(
        ...
    )
    created_at: int = Field(
        ...
    )
    metadata: Dict[str, str] = Field(
        ...
    )

class EvalApiError(BaseModel):
    """An object representing an error response from the Eval API."""
    model_config = ConfigDict(populate_by_name=True)

    code: str = Field(
        ...
    )
    message: str = Field(
        ...
    )

class EvalCustomDataSourceConfig(BaseModel):
    """A CustomDataSourceConfig which specifies the schema of your `item` and optionally `sample` namespaces.
The response schema defines the shape of the data that will be:
- Used to define your testing criteria and
- What data is required when creating a run"""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["custom"] = Field(
        ..., alias="type"
    )
    schema: Dict[str, Any] = Field(
        ...
    )

class EvalGraderLabelModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class EvalGraderPython(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class EvalGraderScoreModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class EvalGraderStringCheck(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class EvalGraderTextSimilarity(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class EvalItem(BaseModel):
    """A message input to the model with a role indicating instruction following
hierarchy. Instructions given with the `developer` or `system` role take
precedence over instructions given with the `user` role. Messages with the
`assistant` role are presumed to have been generated by the model in previous
interactions."""
    model_config = ConfigDict(populate_by_name=True)

    role: Literal["user", "assistant", "system", "developer"] = Field(
        ...
    )
    content: Union[Union[str, InputText, OutputText, InputImage, InputAudio], List[Union[str, InputText, OutputText, InputImage, InputAudio]]] = Field(
        ...
    )
    type_: Literal["message"] = Field(
        None, alias="type"
    )

class EvalItemContent(BaseModel):
    """Inputs to the model - can contain template strings. Supports text, output text, input images, and input audio, either as a single item or an array of items."""
    model_config = ConfigDict(populate_by_name=True)

    pass

class EvalItemContentArray(BaseModel):
    """A list of inputs, each of which may be either an input text, output text, input
image, or input audio object."""
    model_config = ConfigDict(populate_by_name=True)

    pass

class EvalItemContentItem(BaseModel):
    """A single content item: input text, output text, input image, or input audio."""
    model_config = ConfigDict(populate_by_name=True)

    pass

class EvalItemContentOutputText(BaseModel):
    """A text output from the model."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["output_text"] = Field(
        ..., alias="type"
    )
    text: str = Field(
        ...
    )

class EvalItemContentText(BaseModel):
    """A text input to the model."""
    model_config = ConfigDict(populate_by_name=True)

    pass

class EvalItemInputImage(BaseModel):
    """An image input block used within EvalItem content arrays."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["input_image"] = Field(
        ..., alias="type"
    )
    image_url: str = Field(
        ...
    )
    detail: str = Field(
        None
    )

class EvalJsonlFileContentSource(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["file_content"] = Field(
        ..., alias="type"
    )
    content: List[Dict[str, Any]] = Field(
        ...
    )

class EvalJsonlFileIdSource(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["file_id"] = Field(
        ..., alias="type"
    )
    id_: str = Field(
        ..., alias="id"
    )

class EvalList(BaseModel):
    """An object representing a list of evals."""
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["list"] = Field(
        ...
    )
    data: List[Eval] = Field(
        ...
    )
    first_id: str = Field(
        ...
    )
    last_id: str = Field(
        ...
    )
    has_more: bool = Field(
        ...
    )

class EvalLogsDataSourceConfig(BaseModel):
    """A LogsDataSourceConfig which specifies the metadata property of your logs query.
This is usually metadata like `usecase=chatbot` or `prompt-version=v2`, etc.
The schema returned by this data source config is used to defined what variables are available in your evals.
`item` and `sample` are both defined when using this data source config."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["logs"] = Field(
        ..., alias="type"
    )
    metadata: Dict[str, str] = Field(
        None
    )
    schema: Dict[str, Any] = Field(
        ...
    )

class EvalResponsesSource(BaseModel):
    """A EvalResponsesSource object describing a run data source configuration."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["responses"] = Field(
        ..., alias="type"
    )
    metadata: Dict[str, Any] = Field(
        None
    )
    model: str = Field(
        None
    )
    instructions_search: str = Field(
        None
    )
    created_after: int = Field(
        None
    )
    created_before: int = Field(
        None
    )
    reasoning_effort: Literal["none", "minimal", "low", "medium", "high", "xhigh"] = Field(
        None
    )
    temperature: float = Field(
        None
    )
    top_p: float = Field(
        None
    )
    users: List[str] = Field(
        None
    )
    tools: List[str] = Field(
        None
    )

class EvalRun(BaseModel):
    """A schema representing an evaluation run."""
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["eval.run"] = Field(
        ...
    )
    id_: str = Field(
        ..., alias="id"
    )
    eval_id: str = Field(
        ...
    )
    status: str = Field(
        ...
    )
    model: str = Field(
        ...
    )
    name: str = Field(
        ...
    )
    created_at: int = Field(
        ...
    )
    report_url: str = Field(
        ...
    )
    result_counts: Dict[str, Any] = Field(
        ...
    )
    per_model_usage: List[Dict[str, Any]] = Field(
        ...
    )
    per_testing_criteria_results: List[Dict[str, Any]] = Field(
        ...
    )
    data_source: Union[JsonlRunDataSource, CompletionsRunDataSource, CreateEvalResponsesRunDataSource] = Field(
        ...
    )
    metadata: Dict[str, str] = Field(
        ...
    )
    error: EvalApiError = Field(
        ...
    )

class EvalRunList(BaseModel):
    """An object representing a list of runs for an evaluation."""
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["list"] = Field(
        ...
    )
    data: List[EvalRun] = Field(
        ...
    )
    first_id: str = Field(
        ...
    )
    last_id: str = Field(
        ...
    )
    has_more: bool = Field(
        ...
    )

class EvalRunOutputItem(BaseModel):
    """A schema representing an evaluation run output item."""
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["eval.run.output_item"] = Field(
        ...
    )
    id_: str = Field(
        ..., alias="id"
    )
    run_id: str = Field(
        ...
    )
    eval_id: str = Field(
        ...
    )
    created_at: int = Field(
        ...
    )
    status: str = Field(
        ...
    )
    datasource_item_id: int = Field(
        ...
    )
    datasource_item: Dict[str, Any] = Field(
        ...
    )
    results: List[Dict[str, Any]] = Field(
        ...
    )
    sample: Dict[str, Any] = Field(
        ...
    )

class EvalRunOutputItemList(BaseModel):
    """An object representing a list of output items for an evaluation run."""
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["list"] = Field(
        ...
    )
    data: List[EvalRunOutputItem] = Field(
        ...
    )
    first_id: str = Field(
        ...
    )
    last_id: str = Field(
        ...
    )
    has_more: bool = Field(
        ...
    )

class EvalRunOutputItemResult(BaseModel):
    """A single grader result for an evaluation run output item."""
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(
        ...
    )
    type_: str = Field(
        None, alias="type"
    )
    score: float = Field(
        ...
    )
    passed: bool = Field(
        ...
    )
    sample: Dict[str, Any] = Field(
        None
    )

class EvalStoredCompletionsDataSourceConfig(BaseModel):
    """Deprecated in favor of LogsDataSourceConfig."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["stored_completions"] = Field(
        ..., alias="type"
    )
    metadata: Dict[str, str] = Field(
        None
    )
    schema: Dict[str, Any] = Field(
        ...
    )

class EvalStoredCompletionsSource(BaseModel):
    """A StoredCompletionsRunDataSource configuration describing a set of filters"""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["stored_completions"] = Field(
        ..., alias="type"
    )
    metadata: Dict[str, str] = Field(
        None
    )
    model: str = Field(
        None
    )
    created_after: int = Field(
        None
    )
    created_before: int = Field(
        None
    )
    limit: int = Field(
        None
    )

class FileExpirationAfter(BaseModel):
    """The expiration policy for a file. By default, files with `purpose=batch` expire after 30 days and all other files are persisted until they are manually deleted."""
    model_config = ConfigDict(populate_by_name=True)

    anchor: Literal["created_at"] = Field(
        ...
    )
    seconds: int = Field(
        ...
    )

class FilePath(BaseModel):
    """A path to a file."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["file_path"] = Field(
        ..., alias="type"
    )
    file_id: str = Field(
        ...
    )
    index: int = Field(
        ...
    )

class FileSearchRanker(str, Enum):
    """The ranker to use for the file search. If not specified will use the `auto` ranker."""
    AUTO = "auto"
    DEFAULT_2024_08_21 = "default_2024_08_21"

class FileSearchRankingOptions(BaseModel):
    """The ranking options for the file search. If not specified, the file search tool will use the `auto` ranker and a score_threshold of 0.

See the [file search tool documentation](https://platform.openai.com/docs/assistants/tools/file-search#customizing-file-search-settings) for more information."""
    model_config = ConfigDict(populate_by_name=True)

    ranker: Literal["auto", "default_2024_08_21"] = Field(
        None
    )
    score_threshold: float = Field(
        ...
    )

class FileSearchToolCall(BaseModel):
    """The results of a file search tool call. See the
[file search guide](https://platform.openai.com/docs/guides/tools-file-search) for more information."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )
    type_: Literal["file_search_call"] = Field(
        ..., alias="type"
    )
    status: Literal["in_progress", "searching", "completed", "incomplete", "failed"] = Field(
        ...
    )
    queries: List[str] = Field(
        ...
    )
    results: List[Dict[str, Any]] = Field(
        None
    )

class FineTuneChatCompletionRequestAssistantMessage(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class FineTuneChatRequestInput(BaseModel):
    """The per-line training example of a fine-tuning input file for chat models using the supervised method.
Input messages may contain text or image content only. Audio and file input messages
are not currently supported for fine-tuning."""
    model_config = ConfigDict(populate_by_name=True)

    messages: List[Union[SystemMessage, UserMessage, AssistantMessage, ToolMessage, FunctionMessage]] = Field(
        None
    )
    tools: List[FunctionTool] = Field(
        None
    )
    parallel_tool_calls: bool = Field(
        None
    )
    functions: List[Dict[str, Any]] = Field(
        None
    )

class FineTuneDpoHyperparameters(BaseModel):
    """The hyperparameters used for the DPO fine-tuning job."""
    model_config = ConfigDict(populate_by_name=True)

    beta: Union[Literal["auto"], float] = Field(
        None
    )
    batch_size: Union[Literal["auto"], int] = Field(
        None
    )
    learning_rate_multiplier: Union[Literal["auto"], float] = Field(
        None
    )
    n_epochs: Union[Literal["auto"], int] = Field(
        None
    )

class FineTuneDpoMethod(BaseModel):
    """Configuration for the DPO fine-tuning method."""
    model_config = ConfigDict(populate_by_name=True)

    hyperparameters: Dict[str, Any] = Field(
        None
    )

class FineTuneMethod(BaseModel):
    """The method used for fine-tuning."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["supervised", "dpo", "reinforcement"] = Field(
        ..., alias="type"
    )
    supervised: Dict[str, Any] = Field(
        None
    )
    dpo: Dict[str, Any] = Field(
        None
    )
    reinforcement: Dict[str, Any] = Field(
        None
    )

class FineTunePreferenceRequestInput(BaseModel):
    """The per-line training example of a fine-tuning input file for chat models using the dpo method.
Input messages may contain text or image content only. Audio and file input messages
are not currently supported for fine-tuning."""
    model_config = ConfigDict(populate_by_name=True)

    input: Dict[str, Any] = Field(
        None
    )
    preferred_output: List[AssistantMessage] = Field(
        None
    )
    non_preferred_output: List[AssistantMessage] = Field(
        None
    )

class FineTuneReinforcementHyperparameters(BaseModel):
    """The hyperparameters used for the reinforcement fine-tuning job."""
    model_config = ConfigDict(populate_by_name=True)

    batch_size: Union[Literal["auto"], int] = Field(
        None
    )
    learning_rate_multiplier: Union[Literal["auto"], float] = Field(
        None
    )
    n_epochs: Union[Literal["auto"], int] = Field(
        None
    )
    reasoning_effort: Literal["default", "low", "medium", "high"] = Field(
        None
    )
    compute_multiplier: Union[Literal["auto"], float] = Field(
        None
    )
    eval_interval: Union[Literal["auto"], int] = Field(
        None
    )
    eval_samples: Union[Literal["auto"], int] = Field(
        None
    )

class FineTuneReinforcementMethod(BaseModel):
    """Configuration for the reinforcement fine-tuning method."""
    model_config = ConfigDict(populate_by_name=True)

    grader: Union[StringCheckGrader, TextSimilarityGrader, PythonGrader, ScoreModelGrader, MultiGrader] = Field(
        ...
    )
    hyperparameters: Dict[str, Any] = Field(
        None
    )

class FineTuneReinforcementRequestInput(BaseModel):
    """Per-line training example for reinforcement fine-tuning. Note that `messages` and `tools` are the only reserved keywords.
Any other arbitrary key-value data can be included on training datapoints and will be available to reference during grading under the `{{ item.XXX }}` template variable.
Input messages may contain text or image content only. Audio and file input messages
are not currently supported for fine-tuning."""
    model_config = ConfigDict(populate_by_name=True)

    messages: List[Union[DeveloperMessage, UserMessage, AssistantMessage, ToolMessage]] = Field(
        ...
    )
    tools: List[FunctionTool] = Field(
        None
    )

class FineTuneSupervisedHyperparameters(BaseModel):
    """The hyperparameters used for the fine-tuning job."""
    model_config = ConfigDict(populate_by_name=True)

    batch_size: Union[Literal["auto"], int] = Field(
        None
    )
    learning_rate_multiplier: Union[Literal["auto"], float] = Field(
        None
    )
    n_epochs: Union[Literal["auto"], int] = Field(
        None
    )

class FineTuneSupervisedMethod(BaseModel):
    """Configuration for the supervised fine-tuning method."""
    model_config = ConfigDict(populate_by_name=True)

    hyperparameters: Dict[str, Any] = Field(
        None
    )

class FineTuningCheckpointPermission(BaseModel):
    """The `checkpoint.permission` object represents a permission for a fine-tuned model checkpoint."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )
    created_at: int = Field(
        ...
    )
    project_id: str = Field(
        ...
    )
    object: Literal["checkpoint.permission"] = Field(
        ...
    )

class FineTuningIntegration(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["wandb"] = Field(
        ..., alias="type"
    )
    wandb: Dict[str, Any] = Field(
        ...
    )

class FineTuningJob(BaseModel):
    """The `fine_tuning.job` object represents a fine-tuning job that has been created through the API."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )
    created_at: int = Field(
        ...
    )
    error: Dict[str, Any] = Field(
        ...
    )
    fine_tuned_model: str = Field(
        ...
    )
    finished_at: int = Field(
        ...
    )
    hyperparameters: Dict[str, Any] = Field(
        ...
    )
    model: str = Field(
        ...
    )
    object: Literal["fine_tuning.job"] = Field(
        ...
    )
    organization_id: str = Field(
        ...
    )
    result_files: List[str] = Field(
        ...
    )
    status: Literal["validating_files", "queued", "running", "succeeded", "failed", "cancelled"] = Field(
        ...
    )
    trained_tokens: int = Field(
        ...
    )
    training_file: str = Field(
        ...
    )
    validation_file: str = Field(
        ...
    )
    integrations: List[FineTuningJobIntegration] = Field(
        None
    )
    seed: int = Field(
        ...
    )
    estimated_finish: int = Field(
        None
    )
    method: Dict[str, Any] = Field(
        None
    )
    metadata: Dict[str, str] = Field(
        None
    )

class FineTuningJobCheckpoint(BaseModel):
    """The `fine_tuning.job.checkpoint` object represents a model checkpoint for a fine-tuning job that is ready to use."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )
    created_at: int = Field(
        ...
    )
    fine_tuned_model_checkpoint: str = Field(
        ...
    )
    step_number: int = Field(
        ...
    )
    metrics: Dict[str, Any] = Field(
        ...
    )
    fine_tuning_job_id: str = Field(
        ...
    )
    object: Literal["fine_tuning.job.checkpoint"] = Field(
        ...
    )

class FineTuningJobEvent(BaseModel):
    """Fine-tuning job event object"""
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["fine_tuning.job.event"] = Field(
        ...
    )
    id_: str = Field(
        ..., alias="id"
    )
    created_at: int = Field(
        ...
    )
    level: Literal["info", "warn", "error"] = Field(
        ...
    )
    message: str = Field(
        ...
    )
    type_: Literal["message", "metrics"] = Field(
        None, alias="type"
    )
    data: Dict[str, Any] = Field(
        None
    )

class FunctionAndCustomToolCallOutput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class FunctionObject(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    description: str = Field(
        None
    )
    name: str = Field(
        ...
    )
    parameters: Dict[str, Any] = Field(
        None
    )
    strict: bool = Field(
        None
    )

class FunctionParameters(BaseModel):
    """The parameters the functions accepts, described as a JSON Schema object. See the [guide](https://platform.openai.com/docs/guides/function-calling) for examples, and the [JSON Schema reference](https://json-schema.org/understanding-json-schema/) for documentation about the format. 

Omitting `parameters` defines a function with an empty parameter list."""
    model_config = ConfigDict(populate_by_name=True)

    pass

class FunctionToolCall(BaseModel):
    """A tool call to run a function. See the 
[function calling guide](https://platform.openai.com/docs/guides/function-calling) for more information."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        None, alias="id"
    )
    type_: Literal["function_call"] = Field(
        ..., alias="type"
    )
    call_id: str = Field(
        ...
    )
    name: str = Field(
        ...
    )
    arguments: str = Field(
        ...
    )
    status: Literal["in_progress", "completed", "incomplete"] = Field(
        None
    )

class FunctionToolCallOutput(BaseModel):
    """The output of a function tool call."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        None, alias="id"
    )
    type_: Literal["function_call_output"] = Field(
        ..., alias="type"
    )
    call_id: str = Field(
        ...
    )
    output: Union[str, List[Union[InputText, InputImage, InputFile]]] = Field(
        ...
    )
    status: Literal["in_progress", "completed", "incomplete"] = Field(
        None
    )

class FunctionToolCallOutputResource(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class FunctionToolCallResource(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class GraderLabelModel(BaseModel):
    """A LabelModelGrader object which uses a model to assign labels to each item
in the evaluation."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["label_model"] = Field(
        ..., alias="type"
    )
    name: str = Field(
        ...
    )
    model: str = Field(
        ...
    )
    input: List[EvalItem] = Field(
        ...
    )
    labels: List[str] = Field(
        ...
    )
    passing_labels: List[str] = Field(
        ...
    )

class GraderMulti(BaseModel):
    """A MultiGrader object combines the output of multiple graders to produce a single score."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["multi"] = Field(
        ..., alias="type"
    )
    name: str = Field(
        ...
    )
    graders: Union[StringCheckGrader, TextSimilarityGrader, PythonGrader, ScoreModelGrader, LabelModelGrader] = Field(
        ...
    )
    calculate_output: str = Field(
        ...
    )

class GraderPython(BaseModel):
    """A PythonGrader object that runs a python script on the input."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["python"] = Field(
        ..., alias="type"
    )
    name: str = Field(
        ...
    )
    source: str = Field(
        ...
    )
    image_tag: str = Field(
        None
    )

class GraderScoreModel(BaseModel):
    """A ScoreModelGrader object that uses a model to assign a score to the input."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["score_model"] = Field(
        ..., alias="type"
    )
    name: str = Field(
        ...
    )
    model: str = Field(
        ...
    )
    sampling_params: Dict[str, Any] = Field(
        None
    )
    input: List[EvalItem] = Field(
        ...
    )
    range: List[float] = Field(
        None
    )

class GraderStringCheck(BaseModel):
    """A StringCheckGrader object that performs a string comparison between input and reference using a specified operation."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["string_check"] = Field(
        ..., alias="type"
    )
    name: str = Field(
        ...
    )
    input: str = Field(
        ...
    )
    reference: str = Field(
        ...
    )
    operation: Literal["eq", "ne", "like", "ilike"] = Field(
        ...
    )

class GraderTextSimilarity(BaseModel):
    """A TextSimilarityGrader object which grades text based on similarity metrics."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["text_similarity"] = Field(
        ..., alias="type"
    )
    name: str = Field(
        ...
    )
    input: str = Field(
        ...
    )
    reference: str = Field(
        ...
    )
    evaluation_metric: Literal["cosine", "fuzzy_match", "bleu", "gleu", "meteor", "rouge_1", "rouge_2", "rouge_3", "rouge_4", "rouge_5", "rouge_l"] = Field(
        ...
    )

class Group(BaseModel):
    """Summary information about a group returned in role assignment responses."""
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["group"] = Field(
        ...
    )
    id_: str = Field(
        ..., alias="id"
    )
    name: str = Field(
        ...
    )
    created_at: int = Field(
        ...
    )
    scim_managed: bool = Field(
        ...
    )

class GroupDeletedResource(BaseModel):
    """Confirmation payload returned after deleting a group."""
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["group.deleted"] = Field(
        ...
    )
    id_: str = Field(
        ..., alias="id"
    )
    deleted: bool = Field(
        ...
    )

class GroupListResource(BaseModel):
    """Paginated list of organization groups."""
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["list"] = Field(
        ...
    )
    data: List[Dict[str, Any]] = Field(
        ...
    )
    has_more: bool = Field(
        ...
    )
    next: str = Field(
        ...
    )

class GroupResourceWithSuccess(BaseModel):
    """Response returned after updating a group."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )
    name: str = Field(
        ...
    )
    created_at: int = Field(
        ...
    )
    is_scim_managed: bool = Field(
        ...
    )

class GroupResponse(BaseModel):
    """Details about an organization group."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )
    name: str = Field(
        ...
    )
    created_at: int = Field(
        ...
    )
    is_scim_managed: bool = Field(
        ...
    )

class GroupRoleAssignment(BaseModel):
    """Role assignment linking a group to a role."""
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["group.role"] = Field(
        ...
    )
    group: Dict[str, Any] = Field(
        ...
    )
    role: Dict[str, Any] = Field(
        ...
    )

class GroupUserAssignment(BaseModel):
    """Confirmation payload returned after adding a user to a group."""
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["group.user"] = Field(
        ...
    )
    user_id: str = Field(
        ...
    )
    group_id: str = Field(
        ...
    )

class GroupUserDeletedResource(BaseModel):
    """Confirmation payload returned after removing a user from a group."""
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["group.user.deleted"] = Field(
        ...
    )
    deleted: bool = Field(
        ...
    )

class Image(BaseModel):
    """Represents the content or the URL of an image generated by the OpenAI API."""
    model_config = ConfigDict(populate_by_name=True)

    b_64_json: str = Field(
        None, alias="b64_json"
    )
    url: str = Field(
        None
    )
    revised_prompt: str = Field(
        None
    )

class ImageEditCompletedEvent(BaseModel):
    """Emitted when image editing has completed and the final image is available."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["image_edit.completed"] = Field(
        ..., alias="type"
    )
    b_64_json: str = Field(
        ..., alias="b64_json"
    )
    created_at: int = Field(
        ...
    )
    size: Literal["1024x1024", "1024x1536", "1536x1024", "auto"] = Field(
        ...
    )
    quality: Literal["low", "medium", "high", "auto"] = Field(
        ...
    )
    background: Literal["transparent", "opaque", "auto"] = Field(
        ...
    )
    output_format: Literal["png", "webp", "jpeg"] = Field(
        ...
    )
    usage: Dict[str, Any] = Field(
        ...
    )

class ImageEditPartialImageEvent(BaseModel):
    """Emitted when a partial image is available during image editing streaming."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["image_edit.partial_image"] = Field(
        ..., alias="type"
    )
    b_64_json: str = Field(
        ..., alias="b64_json"
    )
    created_at: int = Field(
        ...
    )
    size: Literal["1024x1024", "1024x1536", "1536x1024", "auto"] = Field(
        ...
    )
    quality: Literal["low", "medium", "high", "auto"] = Field(
        ...
    )
    background: Literal["transparent", "opaque", "auto"] = Field(
        ...
    )
    output_format: Literal["png", "webp", "jpeg"] = Field(
        ...
    )
    partial_image_index: int = Field(
        ...
    )

class ImageEditStreamEvent(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class ImageGenCompletedEvent(BaseModel):
    """Emitted when image generation has completed and the final image is available."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["image_generation.completed"] = Field(
        ..., alias="type"
    )
    b_64_json: str = Field(
        ..., alias="b64_json"
    )
    created_at: int = Field(
        ...
    )
    size: Literal["1024x1024", "1024x1536", "1536x1024", "auto"] = Field(
        ...
    )
    quality: Literal["low", "medium", "high", "auto"] = Field(
        ...
    )
    background: Literal["transparent", "opaque", "auto"] = Field(
        ...
    )
    output_format: Literal["png", "webp", "jpeg"] = Field(
        ...
    )
    usage: Dict[str, Any] = Field(
        ...
    )

class ImageGenPartialImageEvent(BaseModel):
    """Emitted when a partial image is available during image generation streaming."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["image_generation.partial_image"] = Field(
        ..., alias="type"
    )
    b_64_json: str = Field(
        ..., alias="b64_json"
    )
    created_at: int = Field(
        ...
    )
    size: Literal["1024x1024", "1024x1536", "1536x1024", "auto"] = Field(
        ...
    )
    quality: Literal["low", "medium", "high", "auto"] = Field(
        ...
    )
    background: Literal["transparent", "opaque", "auto"] = Field(
        ...
    )
    output_format: Literal["png", "webp", "jpeg"] = Field(
        ...
    )
    partial_image_index: int = Field(
        ...
    )

class ImageGenStreamEvent(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class ImageGenTool(BaseModel):
    """A tool that generates images using the GPT image models."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["image_generation"] = Field(
        ..., alias="type"
    )
    model: Union[str, Literal["gpt-image-1", "gpt-image-1-mini"]] = Field(
        None
    )
    quality: Literal["low", "medium", "high", "auto"] = Field(
        None
    )
    size: Literal["1024x1024", "1024x1536", "1536x1024", "auto"] = Field(
        None
    )
    output_format: Literal["png", "webp", "jpeg"] = Field(
        None
    )
    output_compression: int = Field(
        None
    )
    moderation: Literal["auto", "low"] = Field(
        None
    )
    background: Literal["transparent", "opaque", "auto"] = Field(
        None
    )
    input_fidelity: Literal["high", "low"] = Field(
        None
    )
    input_image_mask: Dict[str, Any] = Field(
        None
    )
    partial_images: int = Field(
        None
    )

class ImageGenToolCall(BaseModel):
    """An image generation request made by the model."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["image_generation_call"] = Field(
        ..., alias="type"
    )
    id_: str = Field(
        ..., alias="id"
    )
    status: Literal["in_progress", "completed", "generating", "failed"] = Field(
        ...
    )
    result: str = Field(
        ...
    )

class ImagesResponse(BaseModel):
    """The response from the image generation endpoint."""
    model_config = ConfigDict(populate_by_name=True)

    created: int = Field(
        ...
    )
    data: List[Dict[str, Any]] = Field(
        None
    )
    background: Literal["transparent", "opaque"] = Field(
        None
    )
    output_format: Literal["png", "webp", "jpeg"] = Field(
        None
    )
    size: Literal["1024x1024", "1024x1536", "1536x1024"] = Field(
        None
    )
    quality: Literal["low", "medium", "high"] = Field(
        None
    )
    usage: ImageGenerationUsage = Field(
        None
    )

class ImagesUsage(BaseModel):
    """For the GPT image models only, the token usage information for the image generation."""
    model_config = ConfigDict(populate_by_name=True)

    total_tokens: int = Field(
        ...
    )
    input_tokens: int = Field(
        ...
    )
    output_tokens: int = Field(
        ...
    )
    input_tokens_details: Dict[str, Any] = Field(
        ...
    )

class InputAudio(BaseModel):
    """An audio input to the model."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["input_audio"] = Field(
        ..., alias="type"
    )
    input_audio: Dict[str, Any] = Field(
        ...
    )

class InputContent(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class InputItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class InputMessage(BaseModel):
    """A message input to the model with a role indicating instruction following
hierarchy. Instructions given with the `developer` or `system` role take
precedence over instructions given with the `user` role."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["message"] = Field(
        None, alias="type"
    )
    role: Literal["user", "system", "developer"] = Field(
        ...
    )
    status: Literal["in_progress", "completed", "incomplete"] = Field(
        None
    )
    content: List[Union[InputText, InputImage, InputFile]] = Field(
        ...
    )

class InputMessageContentList(BaseModel):
    """A list of one or many input items to the model, containing different content 
types."""
    model_config = ConfigDict(populate_by_name=True)

    pass

class InputMessageResource(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class InputParam(BaseModel):
    """Text, image, or file inputs to the model, used to generate a response.

Learn more:
- [Text inputs and outputs](https://platform.openai.com/docs/guides/text)
- [Image inputs](https://platform.openai.com/docs/guides/images)
- [File inputs](https://platform.openai.com/docs/guides/pdf-files)
- [Conversation state](https://platform.openai.com/docs/guides/conversation-state)
- [Function calling](https://platform.openai.com/docs/guides/function-calling)"""
    model_config = ConfigDict(populate_by_name=True)

    pass

class Invite(BaseModel):
    """Represents an individual `invite` to the organization."""
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["organization.invite"] = Field(
        ...
    )
    id_: str = Field(
        ..., alias="id"
    )
    email: str = Field(
        ...
    )
    role: Literal["owner", "reader"] = Field(
        ...
    )
    status: Literal["accepted", "expired", "pending"] = Field(
        ...
    )
    invited_at: int = Field(
        ...
    )
    expires_at: int = Field(
        ...
    )
    accepted_at: int = Field(
        None
    )
    projects: List[Dict[str, Any]] = Field(
        None
    )

class InviteDeleteResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["organization.invite.deleted"] = Field(
        ...
    )
    id_: str = Field(
        ..., alias="id"
    )
    deleted: bool = Field(
        ...
    )

class InviteListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["list"] = Field(
        ...
    )
    data: List[Dict[str, Any]] = Field(
        ...
    )
    first_id: str = Field(
        None
    )
    last_id: str = Field(
        None
    )
    has_more: bool = Field(
        None
    )

class InviteProjectGroupBody(BaseModel):
    """Request payload for granting a group access to a project."""
    model_config = ConfigDict(populate_by_name=True)

    group_id: str = Field(
        ...
    )
    role: str = Field(
        ...
    )

class InviteRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    email: str = Field(
        ...
    )
    role: Literal["reader", "owner"] = Field(
        ...
    )
    projects: List[Dict[str, Any]] = Field(
        None
    )

class Item(BaseModel):
    """Content item used to generate a response."""
    model_config = ConfigDict(populate_by_name=True)

    pass

class ItemResource(BaseModel):
    """Content item used to generate a response."""
    model_config = ConfigDict(populate_by_name=True)

    pass

class ListAssistantsResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    object: str = Field(
        ...
    )
    data: List[Assistant] = Field(
        ...
    )
    first_id: str = Field(
        ...
    )
    last_id: str = Field(
        ...
    )
    has_more: bool = Field(
        ...
    )

class ListAuditLogsResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["list"] = Field(
        ...
    )
    data: List[Dict[str, Any]] = Field(
        ...
    )
    first_id: str = Field(
        ...
    )
    last_id: str = Field(
        ...
    )
    has_more: bool = Field(
        ...
    )

class ListBatchesResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    data: List[Dict[str, Any]] = Field(
        ...
    )
    first_id: str = Field(
        None
    )
    last_id: str = Field(
        None
    )
    has_more: bool = Field(
        ...
    )
    object: Literal["list"] = Field(
        ...
    )

class ListCertificatesResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    data: List[Dict[str, Any]] = Field(
        ...
    )
    first_id: str = Field(
        None
    )
    last_id: str = Field(
        None
    )
    has_more: bool = Field(
        ...
    )
    object: Literal["list"] = Field(
        ...
    )

class ListFilesResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    object: str = Field(
        ...
    )
    data: List[Any] = Field(
        ...
    )
    first_id: str = Field(
        ...
    )
    last_id: str = Field(
        ...
    )
    has_more: bool = Field(
        ...
    )

class ListFineTuningCheckpointPermissionResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    data: List[FineTuningCheckpointPermission] = Field(
        ...
    )
    object: Literal["list"] = Field(
        ...
    )
    first_id: str = Field(
        None
    )
    last_id: str = Field(
        None
    )
    has_more: bool = Field(
        ...
    )

class ListFineTuningJobCheckpointsResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    data: List[FineTuningJobCheckpoint] = Field(
        ...
    )
    object: Literal["list"] = Field(
        ...
    )
    first_id: str = Field(
        None
    )
    last_id: str = Field(
        None
    )
    has_more: bool = Field(
        ...
    )

class ListFineTuningJobEventsResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    data: List[Dict[str, Any]] = Field(
        ...
    )
    object: Literal["list"] = Field(
        ...
    )
    has_more: bool = Field(
        ...
    )

class ListMessagesResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    object: str = Field(
        ...
    )
    data: List[TheMessageObject] = Field(
        ...
    )
    first_id: str = Field(
        ...
    )
    last_id: str = Field(
        ...
    )
    has_more: bool = Field(
        ...
    )

class ListModelsResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["list"] = Field(
        ...
    )
    data: List[Any] = Field(
        ...
    )

class ListPaginatedFineTuningJobsResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    data: List[FineTuningJob] = Field(
        ...
    )
    has_more: bool = Field(
        ...
    )
    object: Literal["list"] = Field(
        ...
    )

class ListRunStepsResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    object: str = Field(
        ...
    )
    data: List[RunSteps] = Field(
        ...
    )
    first_id: str = Field(
        ...
    )
    last_id: str = Field(
        ...
    )
    has_more: bool = Field(
        ...
    )

class ListRunsResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    object: str = Field(
        ...
    )
    data: List[ARunOnAThread] = Field(
        ...
    )
    first_id: str = Field(
        ...
    )
    last_id: str = Field(
        ...
    )
    has_more: bool = Field(
        ...
    )

class ListVectorStoreFilesResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    object: str = Field(
        ...
    )
    data: List[VectorStoreFiles] = Field(
        ...
    )
    first_id: str = Field(
        ...
    )
    last_id: str = Field(
        ...
    )
    has_more: bool = Field(
        ...
    )

class ListVectorStoresResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    object: str = Field(
        ...
    )
    data: List[VectorStore] = Field(
        ...
    )
    first_id: str = Field(
        ...
    )
    last_id: str = Field(
        ...
    )
    has_more: bool = Field(
        ...
    )

class LocalShellToolCall(BaseModel):
    """A tool call to run a command on the local shell."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["local_shell_call"] = Field(
        ..., alias="type"
    )
    id_: str = Field(
        ..., alias="id"
    )
    call_id: str = Field(
        ...
    )
    action: LocalShellExecAction = Field(
        ...
    )
    status: Literal["in_progress", "completed", "incomplete"] = Field(
        ...
    )

class LocalShellToolCallOutput(BaseModel):
    """The output of a local shell tool call."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["local_shell_call_output"] = Field(
        ..., alias="type"
    )
    id_: str = Field(
        ..., alias="id"
    )
    output: str = Field(
        ...
    )
    status: Literal["in_progress", "completed", "incomplete"] = Field(
        None
    )

class LogProbProperties(BaseModel):
    """A log probability object."""
    model_config = ConfigDict(populate_by_name=True)

    token: str = Field(
        ...
    )
    logprob: float = Field(
        ...
    )
    bytes: List[int] = Field(
        ...
    )

class McpApprovalRequest(BaseModel):
    """A request for human approval of a tool invocation."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["mcp_approval_request"] = Field(
        ..., alias="type"
    )
    id_: str = Field(
        ..., alias="id"
    )
    server_label: str = Field(
        ...
    )
    name: str = Field(
        ...
    )
    arguments: str = Field(
        ...
    )

class McpApprovalResponse(BaseModel):
    """A response to an MCP approval request."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["mcp_approval_response"] = Field(
        ..., alias="type"
    )
    id_: str = Field(
        None, alias="id"
    )
    approval_request_id: str = Field(
        ...
    )
    approve: bool = Field(
        ...
    )
    reason: str = Field(
        None
    )

class McpApprovalResponseResource(BaseModel):
    """A response to an MCP approval request."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["mcp_approval_response"] = Field(
        ..., alias="type"
    )
    id_: str = Field(
        ..., alias="id"
    )
    approval_request_id: str = Field(
        ...
    )
    approve: bool = Field(
        ...
    )
    reason: str = Field(
        None
    )

class McpListTools(BaseModel):
    """A list of tools available on an MCP server."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["mcp_list_tools"] = Field(
        ..., alias="type"
    )
    id_: str = Field(
        ..., alias="id"
    )
    server_label: str = Field(
        ...
    )
    tools: List[McpListToolsTool] = Field(
        ...
    )
    error: str = Field(
        None
    )

class McpListToolsTool(BaseModel):
    """A tool available on an MCP server."""
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(
        ...
    )
    description: str = Field(
        None
    )
    input_schema: Dict[str, Any] = Field(
        ...
    )
    annotations: Dict[str, Any] = Field(
        None
    )

class McpTool(BaseModel):
    """Give the model access to additional tools via remote Model Context Protocol
(MCP) servers. [Learn more about MCP](https://platform.openai.com/docs/guides/tools-remote-mcp)."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["mcp"] = Field(
        ..., alias="type"
    )
    server_label: str = Field(
        ...
    )
    server_url: str = Field(
        None
    )
    connector_id: Literal["connector_dropbox", "connector_gmail", "connector_googlecalendar", "connector_googledrive", "connector_microsoftteams", "connector_outlookcalendar", "connector_outlookemail", "connector_sharepoint"] = Field(
        None
    )
    authorization: str = Field(
        None
    )
    server_description: str = Field(
        None
    )
    headers: Dict[str, str] = Field(
        None
    )
    allowed_tools: Union[List[str], McpToolFilter] = Field(
        None
    )
    require_approval: Union[McpToolApprovalFilter, Literal["always", "never"]] = Field(
        None
    )

class McpToolCall(BaseModel):
    """An invocation of a tool on an MCP server."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["mcp_call"] = Field(
        ..., alias="type"
    )
    id_: str = Field(
        ..., alias="id"
    )
    server_label: str = Field(
        ...
    )
    name: str = Field(
        ...
    )
    arguments: str = Field(
        ...
    )
    output: str = Field(
        None
    )
    error: str = Field(
        None
    )
    status: Literal["in_progress", "completed", "incomplete", "calling", "failed"] = Field(
        None
    )
    approval_request_id: str = Field(
        None
    )

class McpToolFilter(BaseModel):
    """A filter object to specify which tools are allowed."""
    model_config = ConfigDict(populate_by_name=True)

    tool_names: List[str] = Field(
        None
    )
    read_only: bool = Field(
        None
    )

class MessageContentImageFileObject(BaseModel):
    """References an image [File](https://platform.openai.com/docs/api-reference/files) in the content of a message."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["image_file"] = Field(
        ..., alias="type"
    )
    image_file: Dict[str, Any] = Field(
        ...
    )

class MessageContentImageUrlObject(BaseModel):
    """References an image URL in the content of a message."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["image_url"] = Field(
        ..., alias="type"
    )
    image_url: Dict[str, Any] = Field(
        ...
    )

class MessageContentRefusalObject(BaseModel):
    """The refusal content generated by the assistant."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["refusal"] = Field(
        ..., alias="type"
    )
    refusal: str = Field(
        ...
    )

class MessageContentTextAnnotationsFileCitationObject(BaseModel):
    """A citation within the message that points to a specific quote from a specific File associated with the assistant or the message. Generated when the assistant uses the "file_search" tool to search files."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["file_citation"] = Field(
        ..., alias="type"
    )
    text: str = Field(
        ...
    )
    file_citation: Dict[str, Any] = Field(
        ...
    )
    start_index: int = Field(
        ...
    )
    end_index: int = Field(
        ...
    )

class MessageContentTextAnnotationsFilePathObject(BaseModel):
    """A URL for the file that's generated when the assistant used the `code_interpreter` tool to generate a file."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["file_path"] = Field(
        ..., alias="type"
    )
    text: str = Field(
        ...
    )
    file_path: Dict[str, Any] = Field(
        ...
    )
    start_index: int = Field(
        ...
    )
    end_index: int = Field(
        ...
    )

class MessageContentTextObject(BaseModel):
    """The text content that is part of a message."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["text"] = Field(
        ..., alias="type"
    )
    text: Dict[str, Any] = Field(
        ...
    )

class MessageDeltaContentImageFileObject(BaseModel):
    """References an image [File](https://platform.openai.com/docs/api-reference/files) in the content of a message."""
    model_config = ConfigDict(populate_by_name=True)

    index: int = Field(
        ...
    )
    type_: Literal["image_file"] = Field(
        ..., alias="type"
    )
    image_file: Dict[str, Any] = Field(
        None
    )

class MessageDeltaContentImageUrlObject(BaseModel):
    """References an image URL in the content of a message."""
    model_config = ConfigDict(populate_by_name=True)

    index: int = Field(
        ...
    )
    type_: Literal["image_url"] = Field(
        ..., alias="type"
    )
    image_url: Dict[str, Any] = Field(
        None
    )

class MessageDeltaContentRefusalObject(BaseModel):
    """The refusal content that is part of a message."""
    model_config = ConfigDict(populate_by_name=True)

    index: int = Field(
        ...
    )
    type_: Literal["refusal"] = Field(
        ..., alias="type"
    )
    refusal: str = Field(
        None
    )

class MessageDeltaContentTextAnnotationsFileCitationObject(BaseModel):
    """A citation within the message that points to a specific quote from a specific File associated with the assistant or the message. Generated when the assistant uses the "file_search" tool to search files."""
    model_config = ConfigDict(populate_by_name=True)

    index: int = Field(
        ...
    )
    type_: Literal["file_citation"] = Field(
        ..., alias="type"
    )
    text: str = Field(
        None
    )
    file_citation: Dict[str, Any] = Field(
        None
    )
    start_index: int = Field(
        None
    )
    end_index: int = Field(
        None
    )

class MessageDeltaContentTextAnnotationsFilePathObject(BaseModel):
    """A URL for the file that's generated when the assistant used the `code_interpreter` tool to generate a file."""
    model_config = ConfigDict(populate_by_name=True)

    index: int = Field(
        ...
    )
    type_: Literal["file_path"] = Field(
        ..., alias="type"
    )
    text: str = Field(
        None
    )
    file_path: Dict[str, Any] = Field(
        None
    )
    start_index: int = Field(
        None
    )
    end_index: int = Field(
        None
    )

class MessageDeltaContentTextObject(BaseModel):
    """The text content that is part of a message."""
    model_config = ConfigDict(populate_by_name=True)

    index: int = Field(
        ...
    )
    type_: Literal["text"] = Field(
        ..., alias="type"
    )
    text: Dict[str, Any] = Field(
        None
    )

class MessageDeltaObject(BaseModel):
    """Represents a message delta i.e. any changed fields on a message during streaming."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )
    object: Literal["thread.message.delta"] = Field(
        ...
    )
    delta: Dict[str, Any] = Field(
        ...
    )

class MessageObject(BaseModel):
    """Represents a message within a [thread](https://platform.openai.com/docs/api-reference/threads)."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )
    object: Literal["thread.message"] = Field(
        ...
    )
    created_at: int = Field(
        ...
    )
    thread_id: str = Field(
        ...
    )
    status: Literal["in_progress", "incomplete", "completed"] = Field(
        ...
    )
    incomplete_details: Dict[str, Any] = Field(
        ...
    )
    completed_at: int = Field(
        ...
    )
    incomplete_at: int = Field(
        ...
    )
    role: Literal["user", "assistant"] = Field(
        ...
    )
    content: List[Union[ImageFile, ImageUrl, Text, Refusal]] = Field(
        ...
    )
    assistant_id: str = Field(
        ...
    )
    run_id: str = Field(
        ...
    )
    attachments: List[Dict[str, Any]] = Field(
        ...
    )
    metadata: Dict[str, str] = Field(
        ...
    )

class MessageRequestContentTextObject(BaseModel):
    """The text content that is part of a message."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["text"] = Field(
        ..., alias="type"
    )
    text: str = Field(
        ...
    )

class MessageStreamEvent(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class Metadata(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class Model(BaseModel):
    """Describes an OpenAI model offering that can be used with the API."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )
    created: int = Field(
        ...
    )
    object: Literal["model"] = Field(
        ...
    )
    owned_by: str = Field(
        ...
    )

class ModelIds(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class ModelIdsCompaction(BaseModel):
    """Model ID used to generate the response, like `gpt-5` or `o3`. OpenAI offers a wide range of models with different capabilities, performance characteristics, and price points. Refer to the [model guide](https://platform.openai.com/docs/models) to browse and compare available models."""
    model_config = ConfigDict(populate_by_name=True)

    pass

class ModelIdsResponses(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class ModelIdsShared(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class ModelResponseProperties(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    metadata: Dict[str, str] = Field(
        None
    )
    top_logprobs: int = Field(
        None
    )
    temperature: float = Field(
        None
    )
    top_p: float = Field(
        None
    )
    user: str = Field(
        None
    )
    safety_identifier: str = Field(
        None
    )
    prompt_cache_key: str = Field(
        None
    )
    service_tier: Literal["auto", "default", "flex", "scale", "priority"] = Field(
        None
    )
    prompt_cache_retention: Literal["in-memory", "24h"] = Field(
        None
    )

class ModifyAssistantRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    model: Union[str, Literal["gpt-5", "gpt-5-mini", "gpt-5-nano", "gpt-5-2025-08-07", "gpt-5-mini-2025-08-07", "gpt-5-nano-2025-08-07", "gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano", "gpt-4.1-2025-04-14", "gpt-4.1-mini-2025-04-14", "gpt-4.1-nano-2025-04-14", "o3-mini", "o3-mini-2025-01-31", "o1", "o1-2024-12-17", "gpt-4o", "gpt-4o-2024-11-20", "gpt-4o-2024-08-06", "gpt-4o-2024-05-13", "gpt-4o-mini", "gpt-4o-mini-2024-07-18", "gpt-4.5-preview", "gpt-4.5-preview-2025-02-27", "gpt-4-turbo", "gpt-4-turbo-2024-04-09", "gpt-4-0125-preview", "gpt-4-turbo-preview", "gpt-4-1106-preview", "gpt-4-vision-preview", "gpt-4", "gpt-4-0314", "gpt-4-0613", "gpt-4-32k", "gpt-4-32k-0314", "gpt-4-32k-0613", "gpt-3.5-turbo", "gpt-3.5-turbo-16k", "gpt-3.5-turbo-0613", "gpt-3.5-turbo-1106", "gpt-3.5-turbo-0125", "gpt-3.5-turbo-16k-0613"]] = Field(
        None
    )
    reasoning_effort: Literal["none", "minimal", "low", "medium", "high", "xhigh"] = Field(
        None
    )
    name: str = Field(
        None
    )
    description: str = Field(
        None
    )
    instructions: str = Field(
        None
    )
    tools: List[Union[CodeInterpreterTool, FileSearchTool, FunctionTool]] = Field(
        None
    )
    tool_resources: Dict[str, Any] = Field(
        None
    )
    metadata: Dict[str, str] = Field(
        None
    )
    temperature: float = Field(
        None
    )
    top_p: float = Field(
        None
    )
    response_format: Union[Literal["auto"], Text, JsonObject, JsonSchema] = Field(
        None
    )

class ModifyCertificateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(
        ...
    )

class ModifyMessageRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    metadata: Dict[str, str] = Field(
        None
    )

class ModifyRunRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    metadata: Dict[str, str] = Field(
        None
    )

class ModifyThreadRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    tool_resources: Dict[str, Any] = Field(
        None
    )
    metadata: Dict[str, str] = Field(
        None
    )

class Move(BaseModel):
    """A mouse move action."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["move"] = Field(
        ..., alias="type"
    )
    x: int = Field(
        ...
    )
    y: int = Field(
        ...
    )

class NoiseReductionType(str, Enum):
    """Type of noise reduction. `near_field` is for close-talking microphones such as headphones, `far_field` is for far-field microphones such as laptop or conference room microphones."""
    NEAR_FIELD = "near_field"
    FAR_FIELD = "far_field"

class OpenAiFile(BaseModel):
    """The `File` object represents a document that has been uploaded to OpenAI."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )
    bytes: int = Field(
        ...
    )
    created_at: int = Field(
        ...
    )
    expires_at: int = Field(
        None
    )
    filename: str = Field(
        ...
    )
    object: Literal["file"] = Field(
        ...
    )
    purpose: Literal["assistants", "assistants_output", "batch", "batch_output", "fine-tune", "fine-tune-results", "vision", "user_data"] = Field(
        ...
    )
    status: Literal["uploaded", "processed", "error"] = Field(
        ...
    )
    status_details: str = Field(
        None
    )

class OtherChunkingStrategyResponseParam(BaseModel):
    """This is returned when the chunking strategy is unknown. Typically, this is because the file was indexed before the `chunking_strategy` concept was introduced in the API."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["other"] = Field(
        ..., alias="type"
    )

class OutputAudio(BaseModel):
    """An audio output from the model."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["output_audio"] = Field(
        ..., alias="type"
    )
    data: str = Field(
        ...
    )
    transcript: str = Field(
        ...
    )

class OutputContent(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class OutputItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class OutputMessage(BaseModel):
    """An output message from the model."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )
    type_: Literal["message"] = Field(
        ..., alias="type"
    )
    role: Literal["assistant"] = Field(
        ...
    )
    content: List[Union[OutputText, Refusal]] = Field(
        ...
    )
    status: Literal["in_progress", "completed", "incomplete"] = Field(
        ...
    )

class OutputMessageContent(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class ParallelToolCalls(BaseModel):
    """Whether to enable [parallel function calling](https://platform.openai.com/docs/guides/function-calling#configuring-parallel-function-calling) during tool use."""
    model_config = ConfigDict(populate_by_name=True)

    pass

class PartialImages(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class PredictionContent(BaseModel):
    """Static predicted output content, such as the content of a text file that is
being regenerated."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["content"] = Field(
        ..., alias="type"
    )
    content: Union[str, List[TextContentPart]] = Field(
        ...
    )

class Project(BaseModel):
    """Represents an individual project."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )
    object: Literal["organization.project"] = Field(
        ...
    )
    name: str = Field(
        ...
    )
    created_at: int = Field(
        ...
    )
    archived_at: int = Field(
        None
    )
    status: Literal["active", "archived"] = Field(
        ...
    )

class ProjectApiKey(BaseModel):
    """Represents an individual API key in a project."""
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["organization.project.api_key"] = Field(
        ...
    )
    redacted_value: str = Field(
        ...
    )
    name: str = Field(
        ...
    )
    created_at: int = Field(
        ...
    )
    last_used_at: int = Field(
        ...
    )
    id_: str = Field(
        ..., alias="id"
    )
    owner: Dict[str, Any] = Field(
        ...
    )

class ProjectApiKeyDeleteResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["organization.project.api_key.deleted"] = Field(
        ...
    )
    id_: str = Field(
        ..., alias="id"
    )
    deleted: bool = Field(
        ...
    )

class ProjectApiKeyListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["list"] = Field(
        ...
    )
    data: List[Dict[str, Any]] = Field(
        ...
    )
    first_id: str = Field(
        ...
    )
    last_id: str = Field(
        ...
    )
    has_more: bool = Field(
        ...
    )

class ProjectCreateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(
        ...
    )
    geography: Literal["US", "EU", "JP", "IN", "KR", "CA", "AU", "SG"] = Field(
        None
    )

class ProjectGroup(BaseModel):
    """Details about a group's membership in a project."""
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["project.group"] = Field(
        ...
    )
    project_id: str = Field(
        ...
    )
    group_id: str = Field(
        ...
    )
    group_name: str = Field(
        ...
    )
    created_at: int = Field(
        ...
    )

class ProjectGroupDeletedResource(BaseModel):
    """Confirmation payload returned after removing a group from a project."""
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["project.group.deleted"] = Field(
        ...
    )
    deleted: bool = Field(
        ...
    )

class ProjectGroupListResource(BaseModel):
    """Paginated list of groups that have access to a project."""
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["list"] = Field(
        ...
    )
    data: List[Dict[str, Any]] = Field(
        ...
    )
    has_more: bool = Field(
        ...
    )
    next: str = Field(
        ...
    )

class ProjectListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["list"] = Field(
        ...
    )
    data: List[Dict[str, Any]] = Field(
        ...
    )
    first_id: str = Field(
        ...
    )
    last_id: str = Field(
        ...
    )
    has_more: bool = Field(
        ...
    )

class ProjectRateLimit(BaseModel):
    """Represents a project rate limit config."""
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["project.rate_limit"] = Field(
        ...
    )
    id_: str = Field(
        ..., alias="id"
    )
    model: str = Field(
        ...
    )
    max_requests_per_1_minute: int = Field(
        ...
    )
    max_tokens_per_1_minute: int = Field(
        ...
    )
    max_images_per_1_minute: int = Field(
        None
    )
    max_audio_megabytes_per_1_minute: int = Field(
        None
    )
    max_requests_per_1_day: int = Field(
        None
    )
    batch_1_day_max_input_tokens: int = Field(
        None
    )

class ProjectRateLimitListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["list"] = Field(
        ...
    )
    data: List[Dict[str, Any]] = Field(
        ...
    )
    first_id: str = Field(
        ...
    )
    last_id: str = Field(
        ...
    )
    has_more: bool = Field(
        ...
    )

class ProjectRateLimitUpdateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    max_requests_per_1_minute: int = Field(
        None
    )
    max_tokens_per_1_minute: int = Field(
        None
    )
    max_images_per_1_minute: int = Field(
        None
    )
    max_audio_megabytes_per_1_minute: int = Field(
        None
    )
    max_requests_per_1_day: int = Field(
        None
    )
    batch_1_day_max_input_tokens: int = Field(
        None
    )

class ProjectServiceAccount(BaseModel):
    """Represents an individual service account in a project."""
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["organization.project.service_account"] = Field(
        ...
    )
    id_: str = Field(
        ..., alias="id"
    )
    name: str = Field(
        ...
    )
    role: Literal["owner", "member"] = Field(
        ...
    )
    created_at: int = Field(
        ...
    )

class ProjectServiceAccountApiKey(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["organization.project.service_account.api_key"] = Field(
        ...
    )
    value: str = Field(
        ...
    )
    name: str = Field(
        ...
    )
    created_at: int = Field(
        ...
    )
    id_: str = Field(
        ..., alias="id"
    )

class ProjectServiceAccountCreateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(
        ...
    )

class ProjectServiceAccountCreateResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["organization.project.service_account"] = Field(
        ...
    )
    id_: str = Field(
        ..., alias="id"
    )
    name: str = Field(
        ...
    )
    role: Literal["member"] = Field(
        ...
    )
    created_at: int = Field(
        ...
    )
    api_key: Dict[str, Any] = Field(
        ...
    )

class ProjectServiceAccountDeleteResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["organization.project.service_account.deleted"] = Field(
        ...
    )
    id_: str = Field(
        ..., alias="id"
    )
    deleted: bool = Field(
        ...
    )

class ProjectServiceAccountListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["list"] = Field(
        ...
    )
    data: List[Dict[str, Any]] = Field(
        ...
    )
    first_id: str = Field(
        ...
    )
    last_id: str = Field(
        ...
    )
    has_more: bool = Field(
        ...
    )

class ProjectUpdateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(
        ...
    )

class ProjectUser(BaseModel):
    """Represents an individual user in a project."""
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["organization.project.user"] = Field(
        ...
    )
    id_: str = Field(
        ..., alias="id"
    )
    name: str = Field(
        ...
    )
    email: str = Field(
        ...
    )
    role: Literal["owner", "member"] = Field(
        ...
    )
    added_at: int = Field(
        ...
    )

class ProjectUserCreateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    user_id: str = Field(
        ...
    )
    role: Literal["owner", "member"] = Field(
        ...
    )

class ProjectUserDeleteResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["organization.project.user.deleted"] = Field(
        ...
    )
    id_: str = Field(
        ..., alias="id"
    )
    deleted: bool = Field(
        ...
    )

class ProjectUserListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    object: str = Field(
        ...
    )
    data: List[Dict[str, Any]] = Field(
        ...
    )
    first_id: str = Field(
        ...
    )
    last_id: str = Field(
        ...
    )
    has_more: bool = Field(
        ...
    )

class ProjectUserUpdateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    role: Literal["owner", "member"] = Field(
        ...
    )

class Prompt(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class PublicAssignOrganizationGroupRoleBody(BaseModel):
    """Request payload for assigning a role to a group or user."""
    model_config = ConfigDict(populate_by_name=True)

    role_id: str = Field(
        ...
    )

class PublicCreateOrganizationRoleBody(BaseModel):
    """Request payload for creating a custom role."""
    model_config = ConfigDict(populate_by_name=True)

    role_name: str = Field(
        ...
    )
    permissions: List[str] = Field(
        ...
    )
    description: str = Field(
        None
    )

class PublicRoleListResource(BaseModel):
    """Paginated list of roles available on an organization or project."""
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["list"] = Field(
        ...
    )
    data: List[Dict[str, Any]] = Field(
        ...
    )
    has_more: bool = Field(
        ...
    )
    next: str = Field(
        ...
    )

class PublicUpdateOrganizationRoleBody(BaseModel):
    """Request payload for updating an existing role."""
    model_config = ConfigDict(populate_by_name=True)

    permissions: List[str] = Field(
        None
    )
    description: str = Field(
        None
    )
    role_name: str = Field(
        None
    )

class RealtimeAudioFormats(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class RealtimeBetaClientEventConversationItemCreate(BaseModel):
    """Add a new Item to the Conversation's context, including messages, function 
calls, and function call responses. This event can be used both to populate a 
"history" of the conversation and to add new items mid-stream, but has the 
current limitation that it cannot populate assistant audio messages.

If successful, the server will respond with a `conversation.item.created` 
event, otherwise an `error` event will be sent."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        None
    )
    type_: Any = Field(
        ..., alias="type"
    )
    previous_item_id: str = Field(
        None
    )
    item: Union[RealtimeSystemMessageItem, RealtimeUserMessageItem, RealtimeAssistantMessageItem, RealtimeFunctionCallItem, RealtimeFunctionCallOutputItem, RealtimeMcpApprovalResponse, RealtimeMcpListTools, RealtimeMcpToolCall, RealtimeMcpApprovalRequest] = Field(
        ...
    )

class RealtimeBetaClientEventConversationItemDelete(BaseModel):
    """Send this event when you want to remove any item from the conversation 
history. The server will respond with a `conversation.item.deleted` event, 
unless the item does not exist in the conversation history, in which case the 
server will respond with an error."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        None
    )
    type_: Any = Field(
        ..., alias="type"
    )
    item_id: str = Field(
        ...
    )

class RealtimeBetaClientEventConversationItemRetrieve(BaseModel):
    """Send this event when you want to retrieve the server's representation of a specific item in the conversation history. This is useful, for example, to inspect user audio after noise cancellation and VAD.
The server will respond with a `conversation.item.retrieved` event, 
unless the item does not exist in the conversation history, in which case the 
server will respond with an error."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        None
    )
    type_: Any = Field(
        ..., alias="type"
    )
    item_id: str = Field(
        ...
    )

class RealtimeBetaClientEventConversationItemTruncate(BaseModel):
    """Send this event to truncate a previous assistant message’s audio. The server 
will produce audio faster than realtime, so this event is useful when the user 
interrupts to truncate audio that has already been sent to the client but not 
yet played. This will synchronize the server's understanding of the audio with 
the client's playback.

Truncating audio will delete the server-side text transcript to ensure there 
is not text in the context that hasn't been heard by the user.

If successful, the server will respond with a `conversation.item.truncated` 
event."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        None
    )
    type_: Any = Field(
        ..., alias="type"
    )
    item_id: str = Field(
        ...
    )
    content_index: int = Field(
        ...
    )
    audio_end_ms: int = Field(
        ...
    )

class RealtimeBetaClientEventInputAudioBufferAppend(BaseModel):
    """Send this event to append audio bytes to the input audio buffer. The audio 
buffer is temporary storage you can write to and later commit. In Server VAD 
mode, the audio buffer is used to detect speech and the server will decide 
when to commit. When Server VAD is disabled, you must commit the audio buffer
manually.

The client may choose how much audio to place in each event up to a maximum 
of 15 MiB, for example streaming smaller chunks from the client may allow the 
VAD to be more responsive. Unlike made other client events, the server will 
not send a confirmation response to this event."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        None
    )
    type_: Any = Field(
        ..., alias="type"
    )
    audio: str = Field(
        ...
    )

class RealtimeBetaClientEventInputAudioBufferClear(BaseModel):
    """Send this event to clear the audio bytes in the buffer. The server will 
respond with an `input_audio_buffer.cleared` event."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        None
    )
    type_: Any = Field(
        ..., alias="type"
    )

class RealtimeBetaClientEventInputAudioBufferCommit(BaseModel):
    """Send this event to commit the user input audio buffer, which will create a 
new user message item in the conversation. This event will produce an error 
if the input audio buffer is empty. When in Server VAD mode, the client does 
not need to send this event, the server will commit the audio buffer 
automatically.

Committing the input audio buffer will trigger input audio transcription 
(if enabled in session configuration), but it will not create a response 
from the model. The server will respond with an `input_audio_buffer.committed` 
event."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        None
    )
    type_: Any = Field(
        ..., alias="type"
    )

class RealtimeBetaClientEventOutputAudioBufferClear(BaseModel):
    """**WebRTC/SIP Only:** Emit to cut off the current audio response. This will trigger the server to
stop generating audio and emit a `output_audio_buffer.cleared` event. This
event should be preceded by a `response.cancel` client event to stop the
generation of the current response.
[Learn more](https://platform.openai.com/docs/guides/realtime-conversations#client-and-server-events-for-audio-in-webrtc)."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        None
    )
    type_: Any = Field(
        ..., alias="type"
    )

class RealtimeBetaClientEventResponseCancel(BaseModel):
    """Send this event to cancel an in-progress response. The server will respond 
with a `response.done` event with a status of `response.status=cancelled`. If 
there is no response to cancel, the server will respond with an error."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        None
    )
    type_: Any = Field(
        ..., alias="type"
    )
    response_id: str = Field(
        None
    )

class RealtimeBetaClientEventResponseCreate(BaseModel):
    """This event instructs the server to create a Response, which means triggering 
model inference. When in Server VAD mode, the server will create Responses 
automatically.

A Response will include at least one Item, and may have two, in which case 
the second will be a function call. These Items will be appended to the 
conversation history.

The server will respond with a `response.created` event, events for Items 
and content created, and finally a `response.done` event to indicate the 
Response is complete.

The `response.create` event can optionally include inference configuration like 
`instructions`, and `temperature`. These fields will override the Session's 
configuration for this Response only.

Responses can be created out-of-band of the default Conversation, meaning that they can
have arbitrary input, and it's possible to disable writing the output to the Conversation.
Only one Response can write to the default Conversation at a time, but otherwise multiple
Responses can be created in parallel.

Clients can set `conversation` to `none` to create a Response that does not write to the default
Conversation. Arbitrary input can be provided with the `input` field, which is an array accepting
raw Items and references to existing Items."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        None
    )
    type_: Any = Field(
        ..., alias="type"
    )
    response: Dict[str, Any] = Field(
        None
    )

class RealtimeBetaClientEventSessionUpdate(BaseModel):
    """Send this event to update the session’s default configuration.
The client may send this event at any time to update any field,
except for `voice`. However, note that once a session has been
initialized with a particular `model`, it can’t be changed to
another model using `session.update`.

When the server receives a `session.update`, it will respond
with a `session.updated` event showing the full, effective configuration.
Only the fields that are present are updated. To clear a field like
`instructions`, pass an empty string."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        None
    )
    type_: Any = Field(
        ..., alias="type"
    )
    session: Dict[str, Any] = Field(
        ...
    )

class RealtimeBetaClientEventTranscriptionSessionUpdate(BaseModel):
    """Send this event to update a transcription session."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        None
    )
    type_: Any = Field(
        ..., alias="type"
    )
    session: RealtimeTranscriptionSessionConfiguration = Field(
        ...
    )

class RealtimeBetaResponse(BaseModel):
    """The response resource."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        None, alias="id"
    )
    object: Any = Field(
        None
    )
    status: Literal["completed", "cancelled", "failed", "incomplete", "in_progress"] = Field(
        None
    )
    status_details: Dict[str, Any] = Field(
        None
    )
    output: List[Union[RealtimeSystemMessageItem, RealtimeUserMessageItem, RealtimeAssistantMessageItem, RealtimeFunctionCallItem, RealtimeFunctionCallOutputItem, RealtimeMcpApprovalResponse, RealtimeMcpListTools, RealtimeMcpToolCall, RealtimeMcpApprovalRequest]] = Field(
        None
    )
    metadata: Dict[str, str] = Field(
        None
    )
    usage: Dict[str, Any] = Field(
        None
    )
    conversation_id: str = Field(
        None
    )
    voice: Union[str, Literal["alloy", "ash", "ballad", "coral", "echo", "sage", "shimmer", "verse", "marin", "cedar"]] = Field(
        None
    )
    modalities: List[Literal["text", "audio"]] = Field(
        None
    )
    output_audio_format: Literal["pcm16", "g711_ulaw", "g711_alaw"] = Field(
        None
    )
    temperature: float = Field(
        None
    )
    max_output_tokens: Union[int, Literal["inf"]] = Field(
        None
    )

class RealtimeBetaResponseCreateParams(BaseModel):
    """Create a new Realtime response with these parameters"""
    model_config = ConfigDict(populate_by_name=True)

    modalities: List[Literal["text", "audio"]] = Field(
        None
    )
    instructions: str = Field(
        None
    )
    voice: Union[str, Literal["alloy", "ash", "ballad", "coral", "echo", "sage", "shimmer", "verse", "marin", "cedar"]] = Field(
        None
    )
    output_audio_format: Literal["pcm16", "g711_ulaw", "g711_alaw"] = Field(
        None
    )
    tools: List[Dict[str, Any]] = Field(
        None
    )
    tool_choice: Union[Literal["none", "auto", "required"], FunctionTool, McpTool] = Field(
        None
    )
    temperature: float = Field(
        None
    )
    max_output_tokens: Union[int, Literal["inf"]] = Field(
        None
    )
    conversation: Union[str, Literal["auto", "none"]] = Field(
        None
    )
    metadata: Dict[str, str] = Field(
        None
    )
    prompt: Dict[str, Any] = Field(
        None
    )
    input: List[Union[RealtimeSystemMessageItem, RealtimeUserMessageItem, RealtimeAssistantMessageItem, RealtimeFunctionCallItem, RealtimeFunctionCallOutputItem, RealtimeMcpApprovalResponse, RealtimeMcpListTools, RealtimeMcpToolCall, RealtimeMcpApprovalRequest]] = Field(
        None
    )

class RealtimeBetaServerEventConversationItemCreated(BaseModel):
    """Returned when a conversation item is created. There are several scenarios that produce this event:
  - The server is generating a Response, which if successful will produce
    either one or two Items, which will be of type `message`
    (role `assistant`) or type `function_call`.
  - The input audio buffer has been committed, either by the client or the
    server (in `server_vad` mode). The server will take the content of the
    input audio buffer and add it to a new user message Item.
  - The client has sent a `conversation.item.create` event to add a new Item
    to the Conversation."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    previous_item_id: str = Field(
        None
    )
    item: Union[RealtimeSystemMessageItem, RealtimeUserMessageItem, RealtimeAssistantMessageItem, RealtimeFunctionCallItem, RealtimeFunctionCallOutputItem, RealtimeMcpApprovalResponse, RealtimeMcpListTools, RealtimeMcpToolCall, RealtimeMcpApprovalRequest] = Field(
        ...
    )

class RealtimeBetaServerEventConversationItemDeleted(BaseModel):
    """Returned when an item in the conversation is deleted by the client with a 
`conversation.item.delete` event. This event is used to synchronize the 
server's understanding of the conversation history with the client's view."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    item_id: str = Field(
        ...
    )

class RealtimeBetaServerEventConversationItemInputAudioTranscriptionCompleted(BaseModel):
    """This event is the output of audio transcription for user audio written to the
user audio buffer. Transcription begins when the input audio buffer is
committed by the client or server (in `server_vad` mode). Transcription runs
asynchronously with Response creation, so this event may come before or after
the Response events.

Realtime API models accept audio natively, and thus input transcription is a
separate process run on a separate ASR (Automatic Speech Recognition) model.
The transcript may diverge somewhat from the model's interpretation, and
should be treated as a rough guide."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Literal["conversation.item.input_audio_transcription.completed"] = Field(
        ..., alias="type"
    )
    item_id: str = Field(
        ...
    )
    content_index: int = Field(
        ...
    )
    transcript: str = Field(
        ...
    )
    logprobs: List[Dict[str, Any]] = Field(
        None
    )
    usage: Union[TranscriptTextUsageTokens, TranscriptTextUsageDuration] = Field(
        ...
    )

class RealtimeBetaServerEventConversationItemInputAudioTranscriptionDelta(BaseModel):
    """Returned when the text value of an input audio transcription content part is updated."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    item_id: str = Field(
        ...
    )
    content_index: int = Field(
        None
    )
    delta: str = Field(
        None
    )
    logprobs: List[Dict[str, Any]] = Field(
        None
    )

class RealtimeBetaServerEventConversationItemInputAudioTranscriptionFailed(BaseModel):
    """Returned when input audio transcription is configured, and a transcription 
request for a user message failed. These events are separate from other 
`error` events so that the client can identify the related Item."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Literal["conversation.item.input_audio_transcription.failed"] = Field(
        ..., alias="type"
    )
    item_id: str = Field(
        ...
    )
    content_index: int = Field(
        ...
    )
    error: Dict[str, Any] = Field(
        ...
    )

class RealtimeBetaServerEventConversationItemInputAudioTranscriptionSegment(BaseModel):
    """Returned when an input audio transcription segment is identified for an item."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    item_id: str = Field(
        ...
    )
    content_index: int = Field(
        ...
    )
    text: str = Field(
        ...
    )
    id_: str = Field(
        ..., alias="id"
    )
    speaker: str = Field(
        ...
    )
    start: float = Field(
        ...
    )
    end: float = Field(
        ...
    )

class RealtimeBetaServerEventConversationItemRetrieved(BaseModel):
    """Returned when a conversation item is retrieved with `conversation.item.retrieve`."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    item: Union[RealtimeSystemMessageItem, RealtimeUserMessageItem, RealtimeAssistantMessageItem, RealtimeFunctionCallItem, RealtimeFunctionCallOutputItem, RealtimeMcpApprovalResponse, RealtimeMcpListTools, RealtimeMcpToolCall, RealtimeMcpApprovalRequest] = Field(
        ...
    )

class RealtimeBetaServerEventConversationItemTruncated(BaseModel):
    """Returned when an earlier assistant audio message item is truncated by the 
client with a `conversation.item.truncate` event. This event is used to 
synchronize the server's understanding of the audio with the client's playback.

This action will truncate the audio and remove the server-side text transcript 
to ensure there is no text in the context that hasn't been heard by the user."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    item_id: str = Field(
        ...
    )
    content_index: int = Field(
        ...
    )
    audio_end_ms: int = Field(
        ...
    )

class RealtimeBetaServerEventError(BaseModel):
    """Returned when an error occurs, which could be a client problem or a server
problem. Most errors are recoverable and the session will stay open, we
recommend to implementors to monitor and log error messages by default."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    error: Dict[str, Any] = Field(
        ...
    )

class RealtimeBetaServerEventInputAudioBufferCleared(BaseModel):
    """Returned when the input audio buffer is cleared by the client with a 
`input_audio_buffer.clear` event."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )

class RealtimeBetaServerEventInputAudioBufferCommitted(BaseModel):
    """Returned when an input audio buffer is committed, either by the client or
automatically in server VAD mode. The `item_id` property is the ID of the user
message item that will be created, thus a `conversation.item.created` event
will also be sent to the client."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    previous_item_id: str = Field(
        None
    )
    item_id: str = Field(
        ...
    )

class RealtimeBetaServerEventInputAudioBufferSpeechStarted(BaseModel):
    """Sent by the server when in `server_vad` mode to indicate that speech has been 
detected in the audio buffer. This can happen any time audio is added to the 
buffer (unless speech is already detected). The client may want to use this 
event to interrupt audio playback or provide visual feedback to the user. 

The client should expect to receive a `input_audio_buffer.speech_stopped` event 
when speech stops. The `item_id` property is the ID of the user message item 
that will be created when speech stops and will also be included in the 
`input_audio_buffer.speech_stopped` event (unless the client manually commits 
the audio buffer during VAD activation)."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    audio_start_ms: int = Field(
        ...
    )
    item_id: str = Field(
        ...
    )

class RealtimeBetaServerEventInputAudioBufferSpeechStopped(BaseModel):
    """Returned in `server_vad` mode when the server detects the end of speech in 
the audio buffer. The server will also send an `conversation.item.created` 
event with the user message item that is created from the audio buffer."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    audio_end_ms: int = Field(
        ...
    )
    item_id: str = Field(
        ...
    )

class RealtimeBetaServerEventMcpListToolsCompleted(BaseModel):
    """Returned when listing MCP tools has completed for an item."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    item_id: str = Field(
        ...
    )

class RealtimeBetaServerEventMcpListToolsFailed(BaseModel):
    """Returned when listing MCP tools has failed for an item."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    item_id: str = Field(
        ...
    )

class RealtimeBetaServerEventMcpListToolsInProgress(BaseModel):
    """Returned when listing MCP tools is in progress for an item."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    item_id: str = Field(
        ...
    )

class RealtimeBetaServerEventRateLimitsUpdated(BaseModel):
    """Emitted at the beginning of a Response to indicate the updated rate limits. 
When a Response is created some tokens will be "reserved" for the output 
tokens, the rate limits shown here reflect that reservation, which is then 
adjusted accordingly once the Response is completed."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    rate_limits: List[Dict[str, Any]] = Field(
        ...
    )

class RealtimeBetaServerEventResponseAudioDelta(BaseModel):
    """Returned when the model-generated audio is updated."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    response_id: str = Field(
        ...
    )
    item_id: str = Field(
        ...
    )
    output_index: int = Field(
        ...
    )
    content_index: int = Field(
        ...
    )
    delta: str = Field(
        ...
    )

class RealtimeBetaServerEventResponseAudioDone(BaseModel):
    """Returned when the model-generated audio is done. Also emitted when a Response
is interrupted, incomplete, or cancelled."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    response_id: str = Field(
        ...
    )
    item_id: str = Field(
        ...
    )
    output_index: int = Field(
        ...
    )
    content_index: int = Field(
        ...
    )

class RealtimeBetaServerEventResponseAudioTranscriptDelta(BaseModel):
    """Returned when the model-generated transcription of audio output is updated."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    response_id: str = Field(
        ...
    )
    item_id: str = Field(
        ...
    )
    output_index: int = Field(
        ...
    )
    content_index: int = Field(
        ...
    )
    delta: str = Field(
        ...
    )

class RealtimeBetaServerEventResponseAudioTranscriptDone(BaseModel):
    """Returned when the model-generated transcription of audio output is done
streaming. Also emitted when a Response is interrupted, incomplete, or
cancelled."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    response_id: str = Field(
        ...
    )
    item_id: str = Field(
        ...
    )
    output_index: int = Field(
        ...
    )
    content_index: int = Field(
        ...
    )
    transcript: str = Field(
        ...
    )

class RealtimeBetaServerEventResponseContentPartAdded(BaseModel):
    """Returned when a new content part is added to an assistant message item during
response generation."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    response_id: str = Field(
        ...
    )
    item_id: str = Field(
        ...
    )
    output_index: int = Field(
        ...
    )
    content_index: int = Field(
        ...
    )
    part: Dict[str, Any] = Field(
        ...
    )

class RealtimeBetaServerEventResponseContentPartDone(BaseModel):
    """Returned when a content part is done streaming in an assistant message item.
Also emitted when a Response is interrupted, incomplete, or cancelled."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    response_id: str = Field(
        ...
    )
    item_id: str = Field(
        ...
    )
    output_index: int = Field(
        ...
    )
    content_index: int = Field(
        ...
    )
    part: Dict[str, Any] = Field(
        ...
    )

class RealtimeBetaServerEventResponseCreated(BaseModel):
    """Returned when a new Response is created. The first event of response creation,
where the response is in an initial state of `in_progress`."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    response: Dict[str, Any] = Field(
        ...
    )

class RealtimeBetaServerEventResponseDone(BaseModel):
    """Returned when a Response is done streaming. Always emitted, no matter the 
final state. The Response object included in the `response.done` event will 
include all output Items in the Response but will omit the raw audio data."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    response: Dict[str, Any] = Field(
        ...
    )

class RealtimeBetaServerEventResponseFunctionCallArgumentsDelta(BaseModel):
    """Returned when the model-generated function call arguments are updated."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    response_id: str = Field(
        ...
    )
    item_id: str = Field(
        ...
    )
    output_index: int = Field(
        ...
    )
    call_id: str = Field(
        ...
    )
    delta: str = Field(
        ...
    )

class RealtimeBetaServerEventResponseFunctionCallArgumentsDone(BaseModel):
    """Returned when the model-generated function call arguments are done streaming.
Also emitted when a Response is interrupted, incomplete, or cancelled."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    response_id: str = Field(
        ...
    )
    item_id: str = Field(
        ...
    )
    output_index: int = Field(
        ...
    )
    call_id: str = Field(
        ...
    )
    arguments: str = Field(
        ...
    )

class RealtimeBetaServerEventResponseMcpCallArgumentsDelta(BaseModel):
    """Returned when MCP tool call arguments are updated during response generation."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    response_id: str = Field(
        ...
    )
    item_id: str = Field(
        ...
    )
    output_index: int = Field(
        ...
    )
    delta: str = Field(
        ...
    )
    obfuscation: str = Field(
        None
    )

class RealtimeBetaServerEventResponseMcpCallArgumentsDone(BaseModel):
    """Returned when MCP tool call arguments are finalized during response generation."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    response_id: str = Field(
        ...
    )
    item_id: str = Field(
        ...
    )
    output_index: int = Field(
        ...
    )
    arguments: str = Field(
        ...
    )

class RealtimeBetaServerEventResponseMcpCallCompleted(BaseModel):
    """Returned when an MCP tool call has completed successfully."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    output_index: int = Field(
        ...
    )
    item_id: str = Field(
        ...
    )

class RealtimeBetaServerEventResponseMcpCallFailed(BaseModel):
    """Returned when an MCP tool call has failed."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    output_index: int = Field(
        ...
    )
    item_id: str = Field(
        ...
    )

class RealtimeBetaServerEventResponseMcpCallInProgress(BaseModel):
    """Returned when an MCP tool call has started and is in progress."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    output_index: int = Field(
        ...
    )
    item_id: str = Field(
        ...
    )

class RealtimeBetaServerEventResponseOutputItemAdded(BaseModel):
    """Returned when a new Item is created during Response generation."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    response_id: str = Field(
        ...
    )
    output_index: int = Field(
        ...
    )
    item: Union[RealtimeSystemMessageItem, RealtimeUserMessageItem, RealtimeAssistantMessageItem, RealtimeFunctionCallItem, RealtimeFunctionCallOutputItem, RealtimeMcpApprovalResponse, RealtimeMcpListTools, RealtimeMcpToolCall, RealtimeMcpApprovalRequest] = Field(
        ...
    )

class RealtimeBetaServerEventResponseOutputItemDone(BaseModel):
    """Returned when an Item is done streaming. Also emitted when a Response is 
interrupted, incomplete, or cancelled."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    response_id: str = Field(
        ...
    )
    output_index: int = Field(
        ...
    )
    item: Union[RealtimeSystemMessageItem, RealtimeUserMessageItem, RealtimeAssistantMessageItem, RealtimeFunctionCallItem, RealtimeFunctionCallOutputItem, RealtimeMcpApprovalResponse, RealtimeMcpListTools, RealtimeMcpToolCall, RealtimeMcpApprovalRequest] = Field(
        ...
    )

class RealtimeBetaServerEventResponseTextDelta(BaseModel):
    """Returned when the text value of an "output_text" content part is updated."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    response_id: str = Field(
        ...
    )
    item_id: str = Field(
        ...
    )
    output_index: int = Field(
        ...
    )
    content_index: int = Field(
        ...
    )
    delta: str = Field(
        ...
    )

class RealtimeBetaServerEventResponseTextDone(BaseModel):
    """Returned when the text value of an "output_text" content part is done streaming. Also
emitted when a Response is interrupted, incomplete, or cancelled."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    response_id: str = Field(
        ...
    )
    item_id: str = Field(
        ...
    )
    output_index: int = Field(
        ...
    )
    content_index: int = Field(
        ...
    )
    text: str = Field(
        ...
    )

class RealtimeBetaServerEventSessionCreated(BaseModel):
    """Returned when a Session is created. Emitted automatically when a new
connection is established as the first server event. This event will contain
the default Session configuration."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    session: Dict[str, Any] = Field(
        ...
    )

class RealtimeBetaServerEventSessionUpdated(BaseModel):
    """Returned when a session is updated with a `session.update` event, unless
there is an error."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    session: Dict[str, Any] = Field(
        ...
    )

class RealtimeBetaServerEventTranscriptionSessionCreated(BaseModel):
    """Returned when a transcription session is created."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    session: Dict[str, Any] = Field(
        ...
    )

class RealtimeBetaServerEventTranscriptionSessionUpdated(BaseModel):
    """Returned when a transcription session is updated with a `transcription_session.update` event, unless 
there is an error."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    session: Dict[str, Any] = Field(
        ...
    )

class RealtimeCallCreateRequest(BaseModel):
    """Parameters required to initiate a realtime call and receive the SDP answer
needed to complete a WebRTC peer connection. Provide an SDP offer generated
by your client and optionally configure the session that will answer the call."""
    model_config = ConfigDict(populate_by_name=True)

    sdp: str = Field(
        ...
    )
    session: RealtimeSessionConfiguration = Field(
        None
    )

class RealtimeCallReferRequest(BaseModel):
    """Parameters required to transfer a SIP call to a new destination using the
Realtime API."""
    model_config = ConfigDict(populate_by_name=True)

    target_uri: str = Field(
        ...
    )

class RealtimeCallRejectRequest(BaseModel):
    """Parameters used to decline an incoming SIP call handled by the Realtime API."""
    model_config = ConfigDict(populate_by_name=True)

    status_code: int = Field(
        None
    )

class RealtimeClientEvent(BaseModel):
    """A realtime client event."""
    model_config = ConfigDict(populate_by_name=True)

    pass

class RealtimeClientEventConversationItemCreate(BaseModel):
    """Add a new Item to the Conversation's context, including messages, function 
calls, and function call responses. This event can be used both to populate a 
"history" of the conversation and to add new items mid-stream, but has the 
current limitation that it cannot populate assistant audio messages.

If successful, the server will respond with a `conversation.item.created` 
event, otherwise an `error` event will be sent."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        None
    )
    type_: Any = Field(
        ..., alias="type"
    )
    previous_item_id: str = Field(
        None
    )
    item: Union[RealtimeSystemMessageItem, RealtimeUserMessageItem, RealtimeAssistantMessageItem, RealtimeFunctionCallItem, RealtimeFunctionCallOutputItem, RealtimeMcpApprovalResponse, RealtimeMcpListTools, RealtimeMcpToolCall, RealtimeMcpApprovalRequest] = Field(
        ...
    )

class RealtimeClientEventConversationItemDelete(BaseModel):
    """Send this event when you want to remove any item from the conversation 
history. The server will respond with a `conversation.item.deleted` event, 
unless the item does not exist in the conversation history, in which case the 
server will respond with an error."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        None
    )
    type_: Any = Field(
        ..., alias="type"
    )
    item_id: str = Field(
        ...
    )

class RealtimeClientEventConversationItemRetrieve(BaseModel):
    """Send this event when you want to retrieve the server's representation of a specific item in the conversation history. This is useful, for example, to inspect user audio after noise cancellation and VAD.
The server will respond with a `conversation.item.retrieved` event, 
unless the item does not exist in the conversation history, in which case the 
server will respond with an error."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        None
    )
    type_: Any = Field(
        ..., alias="type"
    )
    item_id: str = Field(
        ...
    )

class RealtimeClientEventConversationItemTruncate(BaseModel):
    """Send this event to truncate a previous assistant message’s audio. The server 
will produce audio faster than realtime, so this event is useful when the user 
interrupts to truncate audio that has already been sent to the client but not 
yet played. This will synchronize the server's understanding of the audio with 
the client's playback.

Truncating audio will delete the server-side text transcript to ensure there 
is not text in the context that hasn't been heard by the user.

If successful, the server will respond with a `conversation.item.truncated` 
event."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        None
    )
    type_: Any = Field(
        ..., alias="type"
    )
    item_id: str = Field(
        ...
    )
    content_index: int = Field(
        ...
    )
    audio_end_ms: int = Field(
        ...
    )

class RealtimeClientEventInputAudioBufferAppend(BaseModel):
    """Send this event to append audio bytes to the input audio buffer. The audio 
buffer is temporary storage you can write to and later commit. A "commit" will create a new
user message item in the conversation history from the buffer content and clear the buffer.
Input audio transcription (if enabled) will be generated when the buffer is committed.

If VAD is enabled the audio buffer is used to detect speech and the server will decide 
when to commit. When Server VAD is disabled, you must commit the audio buffer
manually. Input audio noise reduction operates on writes to the audio buffer.

The client may choose how much audio to place in each event up to a maximum 
of 15 MiB, for example streaming smaller chunks from the client may allow the 
VAD to be more responsive. Unlike most other client events, the server will 
not send a confirmation response to this event."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        None
    )
    type_: Any = Field(
        ..., alias="type"
    )
    audio: str = Field(
        ...
    )

class RealtimeClientEventInputAudioBufferClear(BaseModel):
    """Send this event to clear the audio bytes in the buffer. The server will 
respond with an `input_audio_buffer.cleared` event."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        None
    )
    type_: Any = Field(
        ..., alias="type"
    )

class RealtimeClientEventInputAudioBufferCommit(BaseModel):
    """Send this event to commit the user input audio buffer, which will create a  new user message item in the conversation. This event will produce an error  if the input audio buffer is empty. When in Server VAD mode, the client does  not need to send this event, the server will commit the audio buffer  automatically.

Committing the input audio buffer will trigger input audio transcription  (if enabled in session configuration), but it will not create a response  from the model. The server will respond with an `input_audio_buffer.committed` event."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        None
    )
    type_: Any = Field(
        ..., alias="type"
    )

class RealtimeClientEventOutputAudioBufferClear(BaseModel):
    """**WebRTC/SIP Only:** Emit to cut off the current audio response. This will trigger the server to
stop generating audio and emit a `output_audio_buffer.cleared` event. This
event should be preceded by a `response.cancel` client event to stop the
generation of the current response.
[Learn more](https://platform.openai.com/docs/guides/realtime-conversations#client-and-server-events-for-audio-in-webrtc)."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        None
    )
    type_: Any = Field(
        ..., alias="type"
    )

class RealtimeClientEventResponseCancel(BaseModel):
    """Send this event to cancel an in-progress response. The server will respond 
with a `response.done` event with a status of `response.status=cancelled`. If 
there is no response to cancel, the server will respond with an error. It's safe
to call `response.cancel` even if no response is in progress, an error will be
returned the session will remain unaffected."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        None
    )
    type_: Any = Field(
        ..., alias="type"
    )
    response_id: str = Field(
        None
    )

class RealtimeClientEventResponseCreate(BaseModel):
    """This event instructs the server to create a Response, which means triggering 
model inference. When in Server VAD mode, the server will create Responses 
automatically.

A Response will include at least one Item, and may have two, in which case 
the second will be a function call. These Items will be appended to the 
conversation history by default.

The server will respond with a `response.created` event, events for Items 
and content created, and finally a `response.done` event to indicate the 
Response is complete.

The `response.create` event includes inference configuration like 
`instructions` and `tools`. If these are set, they will override the Session's 
configuration for this Response only.

Responses can be created out-of-band of the default Conversation, meaning that they can
have arbitrary input, and it's possible to disable writing the output to the Conversation.
Only one Response can write to the default Conversation at a time, but otherwise multiple
Responses can be created in parallel. The `metadata` field is a good way to disambiguate
multiple simultaneous Responses.

Clients can set `conversation` to `none` to create a Response that does not write to the default
Conversation. Arbitrary input can be provided with the `input` field, which is an array accepting
raw Items and references to existing Items."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        None
    )
    type_: Any = Field(
        ..., alias="type"
    )
    response: Dict[str, Any] = Field(
        None
    )

class RealtimeClientEventSessionUpdate(BaseModel):
    """Send this event to update the session’s configuration.
The client may send this event at any time to update any field
except for `voice` and `model`. `voice` can be updated only if there have been no other audio outputs yet.

When the server receives a `session.update`, it will respond
with a `session.updated` event showing the full, effective configuration.
Only the fields that are present in the `session.update` are updated. To clear a field like
`instructions`, pass an empty string. To clear a field like `tools`, pass an empty array.
To clear a field like `turn_detection`, pass `null`."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        None
    )
    type_: Any = Field(
        ..., alias="type"
    )
    session: Union[RealtimeSessionConfiguration, RealtimeTranscriptionSessionConfiguration] = Field(
        ...
    )

class RealtimeClientEventTranscriptionSessionUpdate(BaseModel):
    """Send this event to update a transcription session."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        None
    )
    type_: Any = Field(
        ..., alias="type"
    )
    session: RealtimeTranscriptionSessionConfiguration = Field(
        ...
    )

class RealtimeConversationItem(BaseModel):
    """A single item within a Realtime conversation."""
    model_config = ConfigDict(populate_by_name=True)

    pass

class RealtimeConversationItemFunctionCall(BaseModel):
    """A function call item in a Realtime conversation."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        None, alias="id"
    )
    object: Literal["realtime.item"] = Field(
        None
    )
    type_: Literal["function_call"] = Field(
        ..., alias="type"
    )
    status: Literal["completed", "incomplete", "in_progress"] = Field(
        None
    )
    call_id: str = Field(
        None
    )
    name: str = Field(
        ...
    )
    arguments: str = Field(
        ...
    )

class RealtimeConversationItemFunctionCallOutput(BaseModel):
    """A function call output item in a Realtime conversation."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        None, alias="id"
    )
    object: Literal["realtime.item"] = Field(
        None
    )
    type_: Literal["function_call_output"] = Field(
        ..., alias="type"
    )
    status: Literal["completed", "incomplete", "in_progress"] = Field(
        None
    )
    call_id: str = Field(
        ...
    )
    output: str = Field(
        ...
    )

class RealtimeConversationItemMessageAssistant(BaseModel):
    """An assistant message item in a Realtime conversation."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        None, alias="id"
    )
    object: Literal["realtime.item"] = Field(
        None
    )
    type_: Literal["message"] = Field(
        ..., alias="type"
    )
    status: Literal["completed", "incomplete", "in_progress"] = Field(
        None
    )
    role: Literal["assistant"] = Field(
        ...
    )
    content: List[Dict[str, Any]] = Field(
        ...
    )

class RealtimeConversationItemMessageSystem(BaseModel):
    """A system message in a Realtime conversation can be used to provide additional context or instructions to the model. This is similar but distinct from the instruction prompt provided at the start of a conversation, as system messages can be added at any point in the conversation. For major changes to the conversation's behavior, use instructions, but for smaller updates (e.g. "the user is now asking about a different topic"), use system messages."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        None, alias="id"
    )
    object: Literal["realtime.item"] = Field(
        None
    )
    type_: Literal["message"] = Field(
        ..., alias="type"
    )
    status: Literal["completed", "incomplete", "in_progress"] = Field(
        None
    )
    role: Literal["system"] = Field(
        ...
    )
    content: List[Dict[str, Any]] = Field(
        ...
    )

class RealtimeConversationItemMessageUser(BaseModel):
    """A user message item in a Realtime conversation."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        None, alias="id"
    )
    object: Literal["realtime.item"] = Field(
        None
    )
    type_: Literal["message"] = Field(
        ..., alias="type"
    )
    status: Literal["completed", "incomplete", "in_progress"] = Field(
        None
    )
    role: Literal["user"] = Field(
        ...
    )
    content: List[Dict[str, Any]] = Field(
        ...
    )

class RealtimeConversationItemWithReference(BaseModel):
    """The item to add to the conversation."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        None, alias="id"
    )
    type_: Literal["message", "function_call", "function_call_output", "item_reference"] = Field(
        None, alias="type"
    )
    object: Literal["realtime.item"] = Field(
        None
    )
    status: Literal["completed", "incomplete", "in_progress"] = Field(
        None
    )
    role: Literal["user", "assistant", "system"] = Field(
        None
    )
    content: List[Dict[str, Any]] = Field(
        None
    )
    call_id: str = Field(
        None
    )
    name: str = Field(
        None
    )
    arguments: str = Field(
        None
    )
    output: str = Field(
        None
    )

class RealtimeCreateClientSecretRequest(BaseModel):
    """Create a session and client secret for the Realtime API. The request can specify
either a realtime or a transcription session configuration.
[Learn more about the Realtime API](https://platform.openai.com/docs/guides/realtime)."""
    model_config = ConfigDict(populate_by_name=True)

    expires_after: ClientSecretExpiration = Field(
        None
    )
    session: Union[RealtimeSessionConfiguration, RealtimeTranscriptionSessionConfiguration] = Field(
        None
    )

class RealtimeCreateClientSecretResponse(BaseModel):
    """Response from creating a session and client secret for the Realtime API."""
    model_config = ConfigDict(populate_by_name=True)

    value: str = Field(
        ...
    )
    expires_at: int = Field(
        ...
    )
    session: Union[Dict[str, Any], RealtimeTranscriptionSessionConfigurationObject] = Field(
        ...
    )

class RealtimeFunctionTool(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["function"] = Field(
        None, alias="type"
    )
    name: str = Field(
        None
    )
    description: str = Field(
        None
    )
    parameters: Dict[str, Any] = Field(
        None
    )

class RealtimeMcpApprovalRequest(BaseModel):
    """A Realtime item requesting human approval of a tool invocation."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["mcp_approval_request"] = Field(
        ..., alias="type"
    )
    id_: str = Field(
        ..., alias="id"
    )
    server_label: str = Field(
        ...
    )
    name: str = Field(
        ...
    )
    arguments: str = Field(
        ...
    )

class RealtimeMcpApprovalResponse(BaseModel):
    """A Realtime item responding to an MCP approval request."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["mcp_approval_response"] = Field(
        ..., alias="type"
    )
    id_: str = Field(
        ..., alias="id"
    )
    approval_request_id: str = Field(
        ...
    )
    approve: bool = Field(
        ...
    )
    reason: str = Field(
        None
    )

class RealtimeMcphttpError(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["http_error"] = Field(
        ..., alias="type"
    )
    code: int = Field(
        ...
    )
    message: str = Field(
        ...
    )

class RealtimeMcpListTools(BaseModel):
    """A Realtime item listing tools available on an MCP server."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["mcp_list_tools"] = Field(
        ..., alias="type"
    )
    id_: str = Field(
        None, alias="id"
    )
    server_label: str = Field(
        ...
    )
    tools: List[McpListToolsTool] = Field(
        ...
    )

class RealtimeMcpProtocolError(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["protocol_error"] = Field(
        ..., alias="type"
    )
    code: int = Field(
        ...
    )
    message: str = Field(
        ...
    )

class RealtimeMcpToolCall(BaseModel):
    """A Realtime item representing an invocation of a tool on an MCP server."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["mcp_call"] = Field(
        ..., alias="type"
    )
    id_: str = Field(
        ..., alias="id"
    )
    server_label: str = Field(
        ...
    )
    name: str = Field(
        ...
    )
    arguments: str = Field(
        ...
    )
    approval_request_id: str = Field(
        None
    )
    output: str = Field(
        None
    )
    error: Union[RealtimeMcpProtocolError, RealtimeMcpToolExecutionError, RealtimeMcpHttpError] = Field(
        None
    )

class RealtimeMcpToolExecutionError(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["tool_execution_error"] = Field(
        ..., alias="type"
    )
    message: str = Field(
        ...
    )

class RealtimeResponse(BaseModel):
    """The response resource."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        None, alias="id"
    )
    object: Any = Field(
        None
    )
    status: Literal["completed", "cancelled", "failed", "incomplete", "in_progress"] = Field(
        None
    )
    status_details: Dict[str, Any] = Field(
        None
    )
    output: List[Union[RealtimeSystemMessageItem, RealtimeUserMessageItem, RealtimeAssistantMessageItem, RealtimeFunctionCallItem, RealtimeFunctionCallOutputItem, RealtimeMcpApprovalResponse, RealtimeMcpListTools, RealtimeMcpToolCall, RealtimeMcpApprovalRequest]] = Field(
        None
    )
    metadata: Dict[str, str] = Field(
        None
    )
    audio: Dict[str, Any] = Field(
        None
    )
    usage: Dict[str, Any] = Field(
        None
    )
    conversation_id: str = Field(
        None
    )
    output_modalities: List[Literal["text", "audio"]] = Field(
        None
    )
    max_output_tokens: Union[int, Literal["inf"]] = Field(
        None
    )

class RealtimeResponseCreateParams(BaseModel):
    """Create a new Realtime response with these parameters"""
    model_config = ConfigDict(populate_by_name=True)

    output_modalities: List[Literal["text", "audio"]] = Field(
        None
    )
    instructions: str = Field(
        None
    )
    audio: Dict[str, Any] = Field(
        None
    )
    tools: List[Union[FunctionTool, McpTool]] = Field(
        None
    )
    tool_choice: Union[Literal["none", "auto", "required"], FunctionTool, McpTool] = Field(
        None
    )
    max_output_tokens: Union[int, Literal["inf"]] = Field(
        None
    )
    conversation: Union[str, Literal["auto", "none"]] = Field(
        None
    )
    metadata: Dict[str, str] = Field(
        None
    )
    prompt: Dict[str, Any] = Field(
        None
    )
    input: List[Union[RealtimeSystemMessageItem, RealtimeUserMessageItem, RealtimeAssistantMessageItem, RealtimeFunctionCallItem, RealtimeFunctionCallOutputItem, RealtimeMcpApprovalResponse, RealtimeMcpListTools, RealtimeMcpToolCall, RealtimeMcpApprovalRequest]] = Field(
        None
    )

class RealtimeServerEvent(BaseModel):
    """A realtime server event."""
    model_config = ConfigDict(populate_by_name=True)

    pass

class RealtimeServerEventConversationCreated(BaseModel):
    """Returned when a conversation is created. Emitted right after session creation."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    conversation: Dict[str, Any] = Field(
        ...
    )

class RealtimeServerEventConversationItemAdded(BaseModel):
    """Sent by the server when an Item is added to the default Conversation. This can happen in several cases:
- When the client sends a `conversation.item.create` event.
- When the input audio buffer is committed. In this case the item will be a user message containing the audio from the buffer.
- When the model is generating a Response. In this case the `conversation.item.added` event will be sent when the model starts generating a specific Item, and thus it will not yet have any content (and `status` will be `in_progress`).

The event will include the full content of the Item (except when model is generating a Response) except for audio data, which can be retrieved separately with a `conversation.item.retrieve` event if necessary."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    previous_item_id: str = Field(
        None
    )
    item: Union[RealtimeSystemMessageItem, RealtimeUserMessageItem, RealtimeAssistantMessageItem, RealtimeFunctionCallItem, RealtimeFunctionCallOutputItem, RealtimeMcpApprovalResponse, RealtimeMcpListTools, RealtimeMcpToolCall, RealtimeMcpApprovalRequest] = Field(
        ...
    )

class RealtimeServerEventConversationItemCreated(BaseModel):
    """Returned when a conversation item is created. There are several scenarios that produce this event:
  - The server is generating a Response, which if successful will produce
    either one or two Items, which will be of type `message`
    (role `assistant`) or type `function_call`.
  - The input audio buffer has been committed, either by the client or the
    server (in `server_vad` mode). The server will take the content of the
    input audio buffer and add it to a new user message Item.
  - The client has sent a `conversation.item.create` event to add a new Item
    to the Conversation."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    previous_item_id: str = Field(
        None
    )
    item: Union[RealtimeSystemMessageItem, RealtimeUserMessageItem, RealtimeAssistantMessageItem, RealtimeFunctionCallItem, RealtimeFunctionCallOutputItem, RealtimeMcpApprovalResponse, RealtimeMcpListTools, RealtimeMcpToolCall, RealtimeMcpApprovalRequest] = Field(
        ...
    )

class RealtimeServerEventConversationItemDeleted(BaseModel):
    """Returned when an item in the conversation is deleted by the client with a 
`conversation.item.delete` event. This event is used to synchronize the 
server's understanding of the conversation history with the client's view."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    item_id: str = Field(
        ...
    )

class RealtimeServerEventConversationItemDone(BaseModel):
    """Returned when a conversation item is finalized.

The event will include the full content of the Item except for audio data, which can be retrieved separately with a `conversation.item.retrieve` event if needed."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    previous_item_id: str = Field(
        None
    )
    item: Union[RealtimeSystemMessageItem, RealtimeUserMessageItem, RealtimeAssistantMessageItem, RealtimeFunctionCallItem, RealtimeFunctionCallOutputItem, RealtimeMcpApprovalResponse, RealtimeMcpListTools, RealtimeMcpToolCall, RealtimeMcpApprovalRequest] = Field(
        ...
    )

class RealtimeServerEventConversationItemInputAudioTranscriptionCompleted(BaseModel):
    """This event is the output of audio transcription for user audio written to the
user audio buffer. Transcription begins when the input audio buffer is
committed by the client or server (when VAD is enabled). Transcription runs
asynchronously with Response creation, so this event may come before or after
the Response events.

Realtime API models accept audio natively, and thus input transcription is a
separate process run on a separate ASR (Automatic Speech Recognition) model.
The transcript may diverge somewhat from the model's interpretation, and
should be treated as a rough guide."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Literal["conversation.item.input_audio_transcription.completed"] = Field(
        ..., alias="type"
    )
    item_id: str = Field(
        ...
    )
    content_index: int = Field(
        ...
    )
    transcript: str = Field(
        ...
    )
    logprobs: List[Dict[str, Any]] = Field(
        None
    )
    usage: Union[TranscriptTextUsageTokens, TranscriptTextUsageDuration] = Field(
        ...
    )

class RealtimeServerEventConversationItemInputAudioTranscriptionDelta(BaseModel):
    """Returned when the text value of an input audio transcription content part is updated with incremental transcription results."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    item_id: str = Field(
        ...
    )
    content_index: int = Field(
        None
    )
    delta: str = Field(
        None
    )
    logprobs: List[Dict[str, Any]] = Field(
        None
    )

class RealtimeServerEventConversationItemInputAudioTranscriptionFailed(BaseModel):
    """Returned when input audio transcription is configured, and a transcription 
request for a user message failed. These events are separate from other 
`error` events so that the client can identify the related Item."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Literal["conversation.item.input_audio_transcription.failed"] = Field(
        ..., alias="type"
    )
    item_id: str = Field(
        ...
    )
    content_index: int = Field(
        ...
    )
    error: Dict[str, Any] = Field(
        ...
    )

class RealtimeServerEventConversationItemInputAudioTranscriptionSegment(BaseModel):
    """Returned when an input audio transcription segment is identified for an item."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    item_id: str = Field(
        ...
    )
    content_index: int = Field(
        ...
    )
    text: str = Field(
        ...
    )
    id_: str = Field(
        ..., alias="id"
    )
    speaker: str = Field(
        ...
    )
    start: float = Field(
        ...
    )
    end: float = Field(
        ...
    )

class RealtimeServerEventConversationItemRetrieved(BaseModel):
    """Returned when a conversation item is retrieved with `conversation.item.retrieve`. This is provided as a way to fetch the server's representation of an item, for example to get access to the post-processed audio data after noise cancellation and VAD. It includes the full content of the Item, including audio data."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    item: Union[RealtimeSystemMessageItem, RealtimeUserMessageItem, RealtimeAssistantMessageItem, RealtimeFunctionCallItem, RealtimeFunctionCallOutputItem, RealtimeMcpApprovalResponse, RealtimeMcpListTools, RealtimeMcpToolCall, RealtimeMcpApprovalRequest] = Field(
        ...
    )

class RealtimeServerEventConversationItemTruncated(BaseModel):
    """Returned when an earlier assistant audio message item is truncated by the 
client with a `conversation.item.truncate` event. This event is used to 
synchronize the server's understanding of the audio with the client's playback.

This action will truncate the audio and remove the server-side text transcript 
to ensure there is no text in the context that hasn't been heard by the user."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    item_id: str = Field(
        ...
    )
    content_index: int = Field(
        ...
    )
    audio_end_ms: int = Field(
        ...
    )

class RealtimeServerEventError(BaseModel):
    """Returned when an error occurs, which could be a client problem or a server
problem. Most errors are recoverable and the session will stay open, we
recommend to implementors to monitor and log error messages by default."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    error: Dict[str, Any] = Field(
        ...
    )

class RealtimeServerEventInputAudioBufferCleared(BaseModel):
    """Returned when the input audio buffer is cleared by the client with a 
`input_audio_buffer.clear` event."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )

class RealtimeServerEventInputAudioBufferCommitted(BaseModel):
    """Returned when an input audio buffer is committed, either by the client or
automatically in server VAD mode. The `item_id` property is the ID of the user
message item that will be created, thus a `conversation.item.created` event
will also be sent to the client."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    previous_item_id: str = Field(
        None
    )
    item_id: str = Field(
        ...
    )

class RealtimeServerEventInputAudioBufferDtmfEventReceived(BaseModel):
    """**SIP Only:** Returned when an DTMF event is received. A DTMF event is a message that
represents a telephone keypad press (0–9, *, #, A–D). The `event` property
is the keypad that the user press. The `received_at` is the UTC Unix Timestamp
that the server received the event."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Any = Field(
        ..., alias="type"
    )
    event: str = Field(
        ...
    )
    received_at: int = Field(
        ...
    )

class RealtimeServerEventInputAudioBufferSpeechStarted(BaseModel):
    """Sent by the server when in `server_vad` mode to indicate that speech has been 
detected in the audio buffer. This can happen any time audio is added to the 
buffer (unless speech is already detected). The client may want to use this 
event to interrupt audio playback or provide visual feedback to the user. 

The client should expect to receive a `input_audio_buffer.speech_stopped` event 
when speech stops. The `item_id` property is the ID of the user message item 
that will be created when speech stops and will also be included in the 
`input_audio_buffer.speech_stopped` event (unless the client manually commits 
the audio buffer during VAD activation)."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    audio_start_ms: int = Field(
        ...
    )
    item_id: str = Field(
        ...
    )

class RealtimeServerEventInputAudioBufferSpeechStopped(BaseModel):
    """Returned in `server_vad` mode when the server detects the end of speech in 
the audio buffer. The server will also send an `conversation.item.created` 
event with the user message item that is created from the audio buffer."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    audio_end_ms: int = Field(
        ...
    )
    item_id: str = Field(
        ...
    )

class RealtimeServerEventInputAudioBufferTimeoutTriggered(BaseModel):
    """Returned when the Server VAD timeout is triggered for the input audio buffer. This is configured
with `idle_timeout_ms` in the `turn_detection` settings of the session, and it indicates that
there hasn't been any speech detected for the configured duration.

The `audio_start_ms` and `audio_end_ms` fields indicate the segment of audio after the last
model response up to the triggering time, as an offset from the beginning of audio written
to the input audio buffer. This means it demarcates the segment of audio that was silent and
the difference between the start and end values will roughly match the configured timeout.

The empty audio will be committed to the conversation as an `input_audio` item (there will be a
`input_audio_buffer.committed` event) and a model response will be generated. There may be speech
that didn't trigger VAD but is still detected by the model, so the model may respond with
something relevant to the conversation or a prompt to continue speaking."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    audio_start_ms: int = Field(
        ...
    )
    audio_end_ms: int = Field(
        ...
    )
    item_id: str = Field(
        ...
    )

class RealtimeServerEventMcpListToolsCompleted(BaseModel):
    """Returned when listing MCP tools has completed for an item."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    item_id: str = Field(
        ...
    )

class RealtimeServerEventMcpListToolsFailed(BaseModel):
    """Returned when listing MCP tools has failed for an item."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    item_id: str = Field(
        ...
    )

class RealtimeServerEventMcpListToolsInProgress(BaseModel):
    """Returned when listing MCP tools is in progress for an item."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    item_id: str = Field(
        ...
    )

class RealtimeServerEventOutputAudioBufferCleared(BaseModel):
    """**WebRTC/SIP Only:** Emitted when the output audio buffer is cleared. This happens either in VAD
mode when the user has interrupted (`input_audio_buffer.speech_started`),
or when the client has emitted the `output_audio_buffer.clear` event to manually
cut off the current audio response.
[Learn more](https://platform.openai.com/docs/guides/realtime-conversations#client-and-server-events-for-audio-in-webrtc)."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    response_id: str = Field(
        ...
    )

class RealtimeServerEventOutputAudioBufferStarted(BaseModel):
    """**WebRTC/SIP Only:** Emitted when the server begins streaming audio to the client. This event is
emitted after an audio content part has been added (`response.content_part.added`)
to the response.
[Learn more](https://platform.openai.com/docs/guides/realtime-conversations#client-and-server-events-for-audio-in-webrtc)."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    response_id: str = Field(
        ...
    )

class RealtimeServerEventOutputAudioBufferStopped(BaseModel):
    """**WebRTC/SIP Only:** Emitted when the output audio buffer has been completely drained on the server,
and no more audio is forthcoming. This event is emitted after the full response
data has been sent to the client (`response.done`).
[Learn more](https://platform.openai.com/docs/guides/realtime-conversations#client-and-server-events-for-audio-in-webrtc)."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    response_id: str = Field(
        ...
    )

class RealtimeServerEventRateLimitsUpdated(BaseModel):
    """Emitted at the beginning of a Response to indicate the updated rate limits. 
When a Response is created some tokens will be "reserved" for the output 
tokens, the rate limits shown here reflect that reservation, which is then 
adjusted accordingly once the Response is completed."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    rate_limits: List[Dict[str, Any]] = Field(
        ...
    )

class RealtimeServerEventResponseAudioDelta(BaseModel):
    """Returned when the model-generated audio is updated."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    response_id: str = Field(
        ...
    )
    item_id: str = Field(
        ...
    )
    output_index: int = Field(
        ...
    )
    content_index: int = Field(
        ...
    )
    delta: str = Field(
        ...
    )

class RealtimeServerEventResponseAudioDone(BaseModel):
    """Returned when the model-generated audio is done. Also emitted when a Response
is interrupted, incomplete, or cancelled."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    response_id: str = Field(
        ...
    )
    item_id: str = Field(
        ...
    )
    output_index: int = Field(
        ...
    )
    content_index: int = Field(
        ...
    )

class RealtimeServerEventResponseAudioTranscriptDelta(BaseModel):
    """Returned when the model-generated transcription of audio output is updated."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    response_id: str = Field(
        ...
    )
    item_id: str = Field(
        ...
    )
    output_index: int = Field(
        ...
    )
    content_index: int = Field(
        ...
    )
    delta: str = Field(
        ...
    )

class RealtimeServerEventResponseAudioTranscriptDone(BaseModel):
    """Returned when the model-generated transcription of audio output is done
streaming. Also emitted when a Response is interrupted, incomplete, or
cancelled."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    response_id: str = Field(
        ...
    )
    item_id: str = Field(
        ...
    )
    output_index: int = Field(
        ...
    )
    content_index: int = Field(
        ...
    )
    transcript: str = Field(
        ...
    )

class RealtimeServerEventResponseContentPartAdded(BaseModel):
    """Returned when a new content part is added to an assistant message item during
response generation."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    response_id: str = Field(
        ...
    )
    item_id: str = Field(
        ...
    )
    output_index: int = Field(
        ...
    )
    content_index: int = Field(
        ...
    )
    part: Dict[str, Any] = Field(
        ...
    )

class RealtimeServerEventResponseContentPartDone(BaseModel):
    """Returned when a content part is done streaming in an assistant message item.
Also emitted when a Response is interrupted, incomplete, or cancelled."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    response_id: str = Field(
        ...
    )
    item_id: str = Field(
        ...
    )
    output_index: int = Field(
        ...
    )
    content_index: int = Field(
        ...
    )
    part: Dict[str, Any] = Field(
        ...
    )

class RealtimeServerEventResponseCreated(BaseModel):
    """Returned when a new Response is created. The first event of response creation,
where the response is in an initial state of `in_progress`."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    response: Dict[str, Any] = Field(
        ...
    )

class RealtimeServerEventResponseDone(BaseModel):
    """Returned when a Response is done streaming. Always emitted, no matter the 
final state. The Response object included in the `response.done` event will 
include all output Items in the Response but will omit the raw audio data.

Clients should check the `status` field of the Response to determine if it was successful
(`completed`) or if there was another outcome: `cancelled`, `failed`, or `incomplete`.

A response will contain all output items that were generated during the response, excluding
any audio content."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    response: Dict[str, Any] = Field(
        ...
    )

class RealtimeServerEventResponseFunctionCallArgumentsDelta(BaseModel):
    """Returned when the model-generated function call arguments are updated."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    response_id: str = Field(
        ...
    )
    item_id: str = Field(
        ...
    )
    output_index: int = Field(
        ...
    )
    call_id: str = Field(
        ...
    )
    delta: str = Field(
        ...
    )

class RealtimeServerEventResponseFunctionCallArgumentsDone(BaseModel):
    """Returned when the model-generated function call arguments are done streaming.
Also emitted when a Response is interrupted, incomplete, or cancelled."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    response_id: str = Field(
        ...
    )
    item_id: str = Field(
        ...
    )
    output_index: int = Field(
        ...
    )
    call_id: str = Field(
        ...
    )
    arguments: str = Field(
        ...
    )

class RealtimeServerEventResponseMcpCallArgumentsDelta(BaseModel):
    """Returned when MCP tool call arguments are updated during response generation."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    response_id: str = Field(
        ...
    )
    item_id: str = Field(
        ...
    )
    output_index: int = Field(
        ...
    )
    delta: str = Field(
        ...
    )
    obfuscation: str = Field(
        None
    )

class RealtimeServerEventResponseMcpCallArgumentsDone(BaseModel):
    """Returned when MCP tool call arguments are finalized during response generation."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    response_id: str = Field(
        ...
    )
    item_id: str = Field(
        ...
    )
    output_index: int = Field(
        ...
    )
    arguments: str = Field(
        ...
    )

class RealtimeServerEventResponseMcpCallCompleted(BaseModel):
    """Returned when an MCP tool call has completed successfully."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    output_index: int = Field(
        ...
    )
    item_id: str = Field(
        ...
    )

class RealtimeServerEventResponseMcpCallFailed(BaseModel):
    """Returned when an MCP tool call has failed."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    output_index: int = Field(
        ...
    )
    item_id: str = Field(
        ...
    )

class RealtimeServerEventResponseMcpCallInProgress(BaseModel):
    """Returned when an MCP tool call has started and is in progress."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    output_index: int = Field(
        ...
    )
    item_id: str = Field(
        ...
    )

class RealtimeServerEventResponseOutputItemAdded(BaseModel):
    """Returned when a new Item is created during Response generation."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    response_id: str = Field(
        ...
    )
    output_index: int = Field(
        ...
    )
    item: Union[RealtimeSystemMessageItem, RealtimeUserMessageItem, RealtimeAssistantMessageItem, RealtimeFunctionCallItem, RealtimeFunctionCallOutputItem, RealtimeMcpApprovalResponse, RealtimeMcpListTools, RealtimeMcpToolCall, RealtimeMcpApprovalRequest] = Field(
        ...
    )

class RealtimeServerEventResponseOutputItemDone(BaseModel):
    """Returned when an Item is done streaming. Also emitted when a Response is 
interrupted, incomplete, or cancelled."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    response_id: str = Field(
        ...
    )
    output_index: int = Field(
        ...
    )
    item: Union[RealtimeSystemMessageItem, RealtimeUserMessageItem, RealtimeAssistantMessageItem, RealtimeFunctionCallItem, RealtimeFunctionCallOutputItem, RealtimeMcpApprovalResponse, RealtimeMcpListTools, RealtimeMcpToolCall, RealtimeMcpApprovalRequest] = Field(
        ...
    )

class RealtimeServerEventResponseTextDelta(BaseModel):
    """Returned when the text value of an "output_text" content part is updated."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    response_id: str = Field(
        ...
    )
    item_id: str = Field(
        ...
    )
    output_index: int = Field(
        ...
    )
    content_index: int = Field(
        ...
    )
    delta: str = Field(
        ...
    )

class RealtimeServerEventResponseTextDone(BaseModel):
    """Returned when the text value of an "output_text" content part is done streaming. Also
emitted when a Response is interrupted, incomplete, or cancelled."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    response_id: str = Field(
        ...
    )
    item_id: str = Field(
        ...
    )
    output_index: int = Field(
        ...
    )
    content_index: int = Field(
        ...
    )
    text: str = Field(
        ...
    )

class RealtimeServerEventSessionCreated(BaseModel):
    """Returned when a Session is created. Emitted automatically when a new
connection is established as the first server event. This event will contain
the default Session configuration."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    session: Union[RealtimeSessionConfiguration, RealtimeTranscriptionSessionConfiguration] = Field(
        ...
    )

class RealtimeServerEventSessionUpdated(BaseModel):
    """Returned when a session is updated with a `session.update` event, unless
there is an error."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    session: Union[RealtimeSessionConfiguration, RealtimeTranscriptionSessionConfiguration] = Field(
        ...
    )

class RealtimeServerEventTranscriptionSessionUpdated(BaseModel):
    """Returned when a transcription session is updated with a `transcription_session.update` event, unless 
there is an error."""
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(
        ...
    )
    type_: Any = Field(
        ..., alias="type"
    )
    session: Dict[str, Any] = Field(
        ...
    )

class RealtimeSession(BaseModel):
    """Realtime session object for the beta interface."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        None, alias="id"
    )
    object: Literal["realtime.session"] = Field(
        None
    )
    modalities: Any = Field(
        None
    )
    model: Literal["gpt-realtime", "gpt-realtime-2025-08-28", "gpt-4o-realtime-preview", "gpt-4o-realtime-preview-2024-10-01", "gpt-4o-realtime-preview-2024-12-17", "gpt-4o-realtime-preview-2025-06-03", "gpt-4o-mini-realtime-preview", "gpt-4o-mini-realtime-preview-2024-12-17", "gpt-realtime-mini", "gpt-realtime-mini-2025-10-06", "gpt-audio-mini", "gpt-audio-mini-2025-10-06"] = Field(
        None
    )
    instructions: str = Field(
        None
    )
    voice: Union[str, Literal["alloy", "ash", "ballad", "coral", "echo", "sage", "shimmer", "verse", "marin", "cedar"]] = Field(
        None
    )
    input_audio_format: Literal["pcm16", "g711_ulaw", "g711_alaw"] = Field(
        None
    )
    output_audio_format: Literal["pcm16", "g711_ulaw", "g711_alaw"] = Field(
        None
    )
    input_audio_transcription: Dict[str, Any] = Field(
        None
    )
    turn_detection: Union[ServerVad, SemanticVad] = Field(
        None
    )
    input_audio_noise_reduction: Dict[str, Any] = Field(
        None
    )
    speed: float = Field(
        None
    )
    tracing: Union[Literal["auto"], TracingConfiguration] = Field(
        None
    )
    tools: List[FunctionTool] = Field(
        None
    )
    tool_choice: str = Field(
        None
    )
    temperature: float = Field(
        None
    )
    max_response_output_tokens: Union[int, Literal["inf"]] = Field(
        None
    )
    expires_at: int = Field(
        None
    )
    prompt: Dict[str, Any] = Field(
        None
    )
    include: List[Literal["item.input_audio_transcription.logprobs"]] = Field(
        None
    )

class RealtimeSessionCreateRequest(BaseModel):
    """A new Realtime session configuration, with an ephemeral key. Default TTL
for keys is one minute."""
    model_config = ConfigDict(populate_by_name=True)

    client_secret: Dict[str, Any] = Field(
        ...
    )
    modalities: Any = Field(
        None
    )
    instructions: str = Field(
        None
    )
    voice: Union[str, Literal["alloy", "ash", "ballad", "coral", "echo", "sage", "shimmer", "verse", "marin", "cedar"]] = Field(
        None
    )
    input_audio_format: str = Field(
        None
    )
    output_audio_format: str = Field(
        None
    )
    input_audio_transcription: Dict[str, Any] = Field(
        None
    )
    speed: float = Field(
        None
    )
    tracing: Union[Literal["auto"], TracingConfiguration] = Field(
        None
    )
    turn_detection: Dict[str, Any] = Field(
        None
    )
    tools: List[Dict[str, Any]] = Field(
        None
    )
    tool_choice: str = Field(
        None
    )
    temperature: float = Field(
        None
    )
    max_response_output_tokens: Union[int, Literal["inf"]] = Field(
        None
    )
    truncation: Union[Literal["auto", "disabled"], RetentionRatioTruncation] = Field(
        None
    )
    prompt: Dict[str, Any] = Field(
        None
    )

class RealtimeSessionCreateRequestGa(BaseModel):
    """Realtime session object configuration."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["realtime"] = Field(
        ..., alias="type"
    )
    output_modalities: List[Literal["text", "audio"]] = Field(
        None
    )
    model: Union[str, Literal["gpt-realtime", "gpt-realtime-2025-08-28", "gpt-4o-realtime-preview", "gpt-4o-realtime-preview-2024-10-01", "gpt-4o-realtime-preview-2024-12-17", "gpt-4o-realtime-preview-2025-06-03", "gpt-4o-mini-realtime-preview", "gpt-4o-mini-realtime-preview-2024-12-17", "gpt-realtime-mini", "gpt-realtime-mini-2025-10-06", "gpt-audio-mini", "gpt-audio-mini-2025-10-06"]] = Field(
        None
    )
    instructions: str = Field(
        None
    )
    audio: Dict[str, Any] = Field(
        None
    )
    include: List[Literal["item.input_audio_transcription.logprobs"]] = Field(
        None
    )
    tracing: Union[Literal["auto"], TracingConfiguration] = Field(
        None
    )
    tools: List[Union[FunctionTool, McpTool]] = Field(
        None
    )
    tool_choice: Union[Literal["none", "auto", "required"], FunctionTool, McpTool] = Field(
        None
    )
    max_output_tokens: Union[int, Literal["inf"]] = Field(
        None
    )
    truncation: Union[Literal["auto", "disabled"], RetentionRatioTruncation] = Field(
        None
    )
    prompt: Dict[str, Any] = Field(
        None
    )

class RealtimeSessionCreateResponse(BaseModel):
    """A Realtime session configuration object."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        None, alias="id"
    )
    object: str = Field(
        None
    )
    expires_at: int = Field(
        None
    )
    include: List[Literal["item.input_audio_transcription.logprobs"]] = Field(
        None
    )
    model: str = Field(
        None
    )
    output_modalities: Any = Field(
        None
    )
    instructions: str = Field(
        None
    )
    audio: Dict[str, Any] = Field(
        None
    )
    tracing: Union[Literal["auto"], TracingConfiguration] = Field(
        None
    )
    turn_detection: Dict[str, Any] = Field(
        None
    )
    tools: List[FunctionTool] = Field(
        None
    )
    tool_choice: str = Field(
        None
    )
    max_output_tokens: Union[int, Literal["inf"]] = Field(
        None
    )

class RealtimeSessionCreateResponseGa(BaseModel):
    """A new Realtime session configuration, with an ephemeral key. Default TTL
for keys is one minute."""
    model_config = ConfigDict(populate_by_name=True)

    client_secret: Dict[str, Any] = Field(
        ...
    )
    type_: Literal["realtime"] = Field(
        ..., alias="type"
    )
    output_modalities: List[Literal["text", "audio"]] = Field(
        None
    )
    model: Union[str, Literal["gpt-realtime", "gpt-realtime-2025-08-28", "gpt-4o-realtime-preview", "gpt-4o-realtime-preview-2024-10-01", "gpt-4o-realtime-preview-2024-12-17", "gpt-4o-realtime-preview-2025-06-03", "gpt-4o-mini-realtime-preview", "gpt-4o-mini-realtime-preview-2024-12-17", "gpt-realtime-mini", "gpt-realtime-mini-2025-10-06", "gpt-audio-mini", "gpt-audio-mini-2025-10-06"]] = Field(
        None
    )
    instructions: str = Field(
        None
    )
    audio: Dict[str, Any] = Field(
        None
    )
    include: List[Literal["item.input_audio_transcription.logprobs"]] = Field(
        None
    )
    tracing: Union[Literal["auto"], TracingConfiguration] = Field(
        None
    )
    tools: List[Union[FunctionTool, McpTool]] = Field(
        None
    )
    tool_choice: Union[Literal["none", "auto", "required"], FunctionTool, McpTool] = Field(
        None
    )
    max_output_tokens: Union[int, Literal["inf"]] = Field(
        None
    )
    truncation: Union[Literal["auto", "disabled"], RetentionRatioTruncation] = Field(
        None
    )
    prompt: Dict[str, Any] = Field(
        None
    )

class RealtimeTranscriptionSessionCreateRequest(BaseModel):
    """Realtime transcription session object configuration."""
    model_config = ConfigDict(populate_by_name=True)

    turn_detection: Dict[str, Any] = Field(
        None
    )
    input_audio_noise_reduction: Dict[str, Any] = Field(
        None
    )
    input_audio_format: Literal["pcm16", "g711_ulaw", "g711_alaw"] = Field(
        None
    )
    input_audio_transcription: Dict[str, Any] = Field(
        None
    )
    include: List[Literal["item.input_audio_transcription.logprobs"]] = Field(
        None
    )

class RealtimeTranscriptionSessionCreateRequestGa(BaseModel):
    """Realtime transcription session object configuration."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["transcription"] = Field(
        ..., alias="type"
    )
    audio: Dict[str, Any] = Field(
        None
    )
    include: List[Literal["item.input_audio_transcription.logprobs"]] = Field(
        None
    )

class RealtimeTranscriptionSessionCreateResponse(BaseModel):
    """A new Realtime transcription session configuration.

When a session is created on the server via REST API, the session object
also contains an ephemeral key. Default TTL for keys is 10 minutes. This
property is not present when a session is updated via the WebSocket API."""
    model_config = ConfigDict(populate_by_name=True)

    client_secret: Dict[str, Any] = Field(
        ...
    )
    modalities: Any = Field(
        None
    )
    input_audio_format: str = Field(
        None
    )
    input_audio_transcription: Dict[str, Any] = Field(
        None
    )
    turn_detection: Dict[str, Any] = Field(
        None
    )

class RealtimeTranscriptionSessionCreateResponseGa(BaseModel):
    """A Realtime transcription session configuration object."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["transcription"] = Field(
        ..., alias="type"
    )
    id_: str = Field(
        ..., alias="id"
    )
    object: str = Field(
        ...
    )
    expires_at: int = Field(
        None
    )
    include: List[Literal["item.input_audio_transcription.logprobs"]] = Field(
        None
    )
    audio: Dict[str, Any] = Field(
        None
    )

class RealtimeTruncation(BaseModel):
    """When the number of tokens in a conversation exceeds the model's input token limit, the conversation be truncated, meaning messages (starting from the oldest) will not be included in the model's context. A 32k context model with 4,096 max output tokens can only include 28,224 tokens in the context before truncation occurs.

Clients can configure truncation behavior to truncate with a lower max token limit, which is an effective way to control token usage and cost.

Truncation will reduce the number of cached tokens on the next turn (busting the cache), since messages are dropped from the beginning of the context. However, clients can also configure truncation to retain messages up to a fraction of the maximum context size, which will reduce the need for future truncations and thus improve the cache rate.

Truncation can be disabled entirely, which means the server will never truncate but would instead return an error if the conversation exceeds the model's input token limit."""
    model_config = ConfigDict(populate_by_name=True)

    pass

class RealtimeTurnDetection(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class Reasoning(BaseModel):
    """**gpt-5 and o-series models only**

Configuration options for
[reasoning models](https://platform.openai.com/docs/guides/reasoning)."""
    model_config = ConfigDict(populate_by_name=True)

    effort: Literal["none", "minimal", "low", "medium", "high", "xhigh"] = Field(
        None
    )
    summary: Literal["auto", "concise", "detailed"] = Field(
        None
    )
    generate_summary: Literal["auto", "concise", "detailed"] = Field(
        None
    )

class ReasoningEffort(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class ReasoningItem(BaseModel):
    """A description of the chain of thought used by a reasoning model while generating
a response. Be sure to include these items in your `input` to the Responses API
for subsequent turns of a conversation if you are manually
[managing context](https://platform.openai.com/docs/guides/conversation-state)."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["reasoning"] = Field(
        ..., alias="type"
    )
    id_: str = Field(
        ..., alias="id"
    )
    encrypted_content: str = Field(
        None
    )
    summary: List[SummaryText] = Field(
        ...
    )
    content: List[ReasoningTextContent] = Field(
        None
    )
    status: Literal["in_progress", "completed", "incomplete"] = Field(
        None
    )

class Response(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class ResponseAudioDeltaEvent(BaseModel):
    """Emitted when there is a partial audio response."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["response.audio.delta"] = Field(
        ..., alias="type"
    )
    sequence_number: int = Field(
        ...
    )
    delta: str = Field(
        ...
    )

class ResponseAudioDoneEvent(BaseModel):
    """Emitted when the audio response is complete."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["response.audio.done"] = Field(
        ..., alias="type"
    )
    sequence_number: int = Field(
        ...
    )

class ResponseAudioTranscriptDeltaEvent(BaseModel):
    """Emitted when there is a partial transcript of audio."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["response.audio.transcript.delta"] = Field(
        ..., alias="type"
    )
    delta: str = Field(
        ...
    )
    sequence_number: int = Field(
        ...
    )

class ResponseAudioTranscriptDoneEvent(BaseModel):
    """Emitted when the full audio transcript is completed."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["response.audio.transcript.done"] = Field(
        ..., alias="type"
    )
    sequence_number: int = Field(
        ...
    )

class ResponseCodeInterpreterCallCodeDeltaEvent(BaseModel):
    """Emitted when a partial code snippet is streamed by the code interpreter."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["response.code_interpreter_call_code.delta"] = Field(
        ..., alias="type"
    )
    output_index: int = Field(
        ...
    )
    item_id: str = Field(
        ...
    )
    delta: str = Field(
        ...
    )
    sequence_number: int = Field(
        ...
    )

class ResponseCodeInterpreterCallCodeDoneEvent(BaseModel):
    """Emitted when the code snippet is finalized by the code interpreter."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["response.code_interpreter_call_code.done"] = Field(
        ..., alias="type"
    )
    output_index: int = Field(
        ...
    )
    item_id: str = Field(
        ...
    )
    code: str = Field(
        ...
    )
    sequence_number: int = Field(
        ...
    )

class ResponseCodeInterpreterCallCompletedEvent(BaseModel):
    """Emitted when the code interpreter call is completed."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["response.code_interpreter_call.completed"] = Field(
        ..., alias="type"
    )
    output_index: int = Field(
        ...
    )
    item_id: str = Field(
        ...
    )
    sequence_number: int = Field(
        ...
    )

class ResponseCodeInterpreterCallInProgressEvent(BaseModel):
    """Emitted when a code interpreter call is in progress."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["response.code_interpreter_call.in_progress"] = Field(
        ..., alias="type"
    )
    output_index: int = Field(
        ...
    )
    item_id: str = Field(
        ...
    )
    sequence_number: int = Field(
        ...
    )

class ResponseCodeInterpreterCallInterpretingEvent(BaseModel):
    """Emitted when the code interpreter is actively interpreting the code snippet."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["response.code_interpreter_call.interpreting"] = Field(
        ..., alias="type"
    )
    output_index: int = Field(
        ...
    )
    item_id: str = Field(
        ...
    )
    sequence_number: int = Field(
        ...
    )

class ResponseCompletedEvent(BaseModel):
    """Emitted when the model response is complete."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["response.completed"] = Field(
        ..., alias="type"
    )
    response: Dict[str, Any] = Field(
        ...
    )
    sequence_number: int = Field(
        ...
    )

class ResponseContentPartAddedEvent(BaseModel):
    """Emitted when a new content part is added."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["response.content_part.added"] = Field(
        ..., alias="type"
    )
    item_id: str = Field(
        ...
    )
    output_index: int = Field(
        ...
    )
    content_index: int = Field(
        ...
    )
    part: Union[OutputText, Refusal, ReasoningTextContent] = Field(
        ...
    )
    sequence_number: int = Field(
        ...
    )

class ResponseContentPartDoneEvent(BaseModel):
    """Emitted when a content part is done."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["response.content_part.done"] = Field(
        ..., alias="type"
    )
    item_id: str = Field(
        ...
    )
    output_index: int = Field(
        ...
    )
    content_index: int = Field(
        ...
    )
    sequence_number: int = Field(
        ...
    )
    part: Union[OutputText, Refusal, ReasoningTextContent] = Field(
        ...
    )

class ResponseCreatedEvent(BaseModel):
    """An event that is emitted when a response is created."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["response.created"] = Field(
        ..., alias="type"
    )
    response: Dict[str, Any] = Field(
        ...
    )
    sequence_number: int = Field(
        ...
    )

class ResponseCustomToolCallInputDeltaEvent(BaseModel):
    """Event representing a delta (partial update) to the input of a custom tool call."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["response.custom_tool_call_input.delta"] = Field(
        ..., alias="type"
    )
    sequence_number: int = Field(
        ...
    )
    output_index: int = Field(
        ...
    )
    item_id: str = Field(
        ...
    )
    delta: str = Field(
        ...
    )

class ResponseCustomToolCallInputDoneEvent(BaseModel):
    """Event indicating that input for a custom tool call is complete."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["response.custom_tool_call_input.done"] = Field(
        ..., alias="type"
    )
    sequence_number: int = Field(
        ...
    )
    output_index: int = Field(
        ...
    )
    item_id: str = Field(
        ...
    )
    input: str = Field(
        ...
    )

class ResponseError(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class ResponseErrorCode(str, Enum):
    """The error code for the response."""
    SERVER_ERROR = "server_error"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    INVALID_PROMPT = "invalid_prompt"
    VECTOR_STORE_TIMEOUT = "vector_store_timeout"
    INVALID_IMAGE = "invalid_image"
    INVALID_IMAGE_FORMAT = "invalid_image_format"
    INVALID_BASE64_IMAGE = "invalid_base64_image"
    INVALID_IMAGE_URL = "invalid_image_url"
    IMAGE_TOO_LARGE = "image_too_large"
    IMAGE_TOO_SMALL = "image_too_small"
    IMAGE_PARSE_ERROR = "image_parse_error"
    IMAGE_CONTENT_POLICY_VIOLATION = "image_content_policy_violation"
    INVALID_IMAGE_MODE = "invalid_image_mode"
    IMAGE_FILE_TOO_LARGE = "image_file_too_large"
    UNSUPPORTED_IMAGE_MEDIA_TYPE = "unsupported_image_media_type"
    EMPTY_IMAGE_FILE = "empty_image_file"
    FAILED_TO_DOWNLOAD_IMAGE = "failed_to_download_image"
    IMAGE_FILE_NOT_FOUND = "image_file_not_found"

class ResponseErrorEvent(BaseModel):
    """Emitted when an error occurs."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["error"] = Field(
        ..., alias="type"
    )
    code: str = Field(
        ...
    )
    message: str = Field(
        ...
    )
    param: str = Field(
        ...
    )
    sequence_number: int = Field(
        ...
    )

class ResponseFailedEvent(BaseModel):
    """An event that is emitted when a response fails."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["response.failed"] = Field(
        ..., alias="type"
    )
    sequence_number: int = Field(
        ...
    )
    response: Dict[str, Any] = Field(
        ...
    )

class ResponseFileSearchCallCompletedEvent(BaseModel):
    """Emitted when a file search call is completed (results found)."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["response.file_search_call.completed"] = Field(
        ..., alias="type"
    )
    output_index: int = Field(
        ...
    )
    item_id: str = Field(
        ...
    )
    sequence_number: int = Field(
        ...
    )

class ResponseFileSearchCallInProgressEvent(BaseModel):
    """Emitted when a file search call is initiated."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["response.file_search_call.in_progress"] = Field(
        ..., alias="type"
    )
    output_index: int = Field(
        ...
    )
    item_id: str = Field(
        ...
    )
    sequence_number: int = Field(
        ...
    )

class ResponseFileSearchCallSearchingEvent(BaseModel):
    """Emitted when a file search is currently searching."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["response.file_search_call.searching"] = Field(
        ..., alias="type"
    )
    output_index: int = Field(
        ...
    )
    item_id: str = Field(
        ...
    )
    sequence_number: int = Field(
        ...
    )

class ResponseFormatJsonObject(BaseModel):
    """JSON object response format. An older method of generating JSON responses.
Using `json_schema` is recommended for models that support it. Note that the
model will not generate JSON without a system or user message instructing it
to do so."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["json_object"] = Field(
        ..., alias="type"
    )

class ResponseFormatJsonSchema(BaseModel):
    """JSON Schema response format. Used to generate structured JSON responses.
Learn more about [Structured Outputs](https://platform.openai.com/docs/guides/structured-outputs)."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["json_schema"] = Field(
        ..., alias="type"
    )
    json_schema: JsonSchema = Field(
        ...
    )

class ResponseFormatJsonSchemaSchema(BaseModel):
    """The schema for the response format, described as a JSON Schema object.
Learn how to build JSON schemas [here](https://json-schema.org/)."""
    model_config = ConfigDict(populate_by_name=True)

    pass

class ResponseFormatText(BaseModel):
    """Default response format. Used to generate text responses."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["text"] = Field(
        ..., alias="type"
    )

class ResponseFormatTextGrammar(BaseModel):
    """A custom grammar for the model to follow when generating text.
Learn more in the [custom grammars guide](https://platform.openai.com/docs/guides/custom-grammars)."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["grammar"] = Field(
        ..., alias="type"
    )
    grammar: str = Field(
        ...
    )

class ResponseFormatTextPython(BaseModel):
    """Configure the model to generate valid Python code. See the
[custom grammars guide](https://platform.openai.com/docs/guides/custom-grammars) for more details."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["python"] = Field(
        ..., alias="type"
    )

class ResponseFunctionCallArgumentsDeltaEvent(BaseModel):
    """Emitted when there is a partial function-call arguments delta."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["response.function_call_arguments.delta"] = Field(
        ..., alias="type"
    )
    item_id: str = Field(
        ...
    )
    output_index: int = Field(
        ...
    )
    sequence_number: int = Field(
        ...
    )
    delta: str = Field(
        ...
    )

class ResponseFunctionCallArgumentsDoneEvent(BaseModel):
    """Emitted when function-call arguments are finalized."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["response.function_call_arguments.done"] = Field(
        ..., alias="type"
    )
    item_id: str = Field(
        ...
    )
    name: str = Field(
        ...
    )
    output_index: int = Field(
        ...
    )
    sequence_number: int = Field(
        ...
    )
    arguments: str = Field(
        ...
    )

class ResponseImageGenCallCompletedEvent(BaseModel):
    """Emitted when an image generation tool call has completed and the final image is available."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["response.image_generation_call.completed"] = Field(
        ..., alias="type"
    )
    output_index: int = Field(
        ...
    )
    sequence_number: int = Field(
        ...
    )
    item_id: str = Field(
        ...
    )

class ResponseImageGenCallGeneratingEvent(BaseModel):
    """Emitted when an image generation tool call is actively generating an image (intermediate state)."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["response.image_generation_call.generating"] = Field(
        ..., alias="type"
    )
    output_index: int = Field(
        ...
    )
    item_id: str = Field(
        ...
    )
    sequence_number: int = Field(
        ...
    )

class ResponseImageGenCallInProgressEvent(BaseModel):
    """Emitted when an image generation tool call is in progress."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["response.image_generation_call.in_progress"] = Field(
        ..., alias="type"
    )
    output_index: int = Field(
        ...
    )
    item_id: str = Field(
        ...
    )
    sequence_number: int = Field(
        ...
    )

class ResponseImageGenCallPartialImageEvent(BaseModel):
    """Emitted when a partial image is available during image generation streaming."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["response.image_generation_call.partial_image"] = Field(
        ..., alias="type"
    )
    output_index: int = Field(
        ...
    )
    item_id: str = Field(
        ...
    )
    sequence_number: int = Field(
        ...
    )
    partial_image_index: int = Field(
        ...
    )
    partial_image_b_64: str = Field(
        ..., alias="partial_image_b64"
    )

class ResponseInProgressEvent(BaseModel):
    """Emitted when the response is in progress."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["response.in_progress"] = Field(
        ..., alias="type"
    )
    response: Dict[str, Any] = Field(
        ...
    )
    sequence_number: int = Field(
        ...
    )

class ResponseIncompleteEvent(BaseModel):
    """An event that is emitted when a response finishes as incomplete."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["response.incomplete"] = Field(
        ..., alias="type"
    )
    response: Dict[str, Any] = Field(
        ...
    )
    sequence_number: int = Field(
        ...
    )

class ResponseItemList(BaseModel):
    """A list of Response items."""
    model_config = ConfigDict(populate_by_name=True)

    object: Any = Field(
        ...
    )
    data: List[Union[InputMessage, OutputMessage, FileSearchToolCall, ComputerToolCall, ComputerToolCallOutput, WebSearchToolCall, FunctionToolCall, FunctionToolCallOutput, ImageGenerationCall, CodeInterpreterToolCall, LocalShellCall, LocalShellCallOutput, ShellToolCall, ShellCallOutput, ApplyPatchToolCall, ApplyPatchToolCallOutput, McpListTools, McpApprovalRequest, McpApprovalResponse, McpToolCall]] = Field(
        ...
    )
    has_more: bool = Field(
        ...
    )
    first_id: str = Field(
        ...
    )
    last_id: str = Field(
        ...
    )

class ResponseLogProb(BaseModel):
    """A logprob is the logarithmic probability that the model assigns to producing 
a particular token at a given position in the sequence. Less-negative (higher) 
logprob values indicate greater model confidence in that token choice."""
    model_config = ConfigDict(populate_by_name=True)

    token: str = Field(
        ...
    )
    logprob: float = Field(
        ...
    )
    top_logprobs: List[Dict[str, Any]] = Field(
        None
    )

class ResponseMcpCallArgumentsDeltaEvent(BaseModel):
    """Emitted when there is a delta (partial update) to the arguments of an MCP tool call."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["response.mcp_call_arguments.delta"] = Field(
        ..., alias="type"
    )
    output_index: int = Field(
        ...
    )
    item_id: str = Field(
        ...
    )
    delta: str = Field(
        ...
    )
    sequence_number: int = Field(
        ...
    )

class ResponseMcpCallArgumentsDoneEvent(BaseModel):
    """Emitted when the arguments for an MCP tool call are finalized."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["response.mcp_call_arguments.done"] = Field(
        ..., alias="type"
    )
    output_index: int = Field(
        ...
    )
    item_id: str = Field(
        ...
    )
    arguments: str = Field(
        ...
    )
    sequence_number: int = Field(
        ...
    )

class ResponseMcpCallCompletedEvent(BaseModel):
    """Emitted when an MCP  tool call has completed successfully."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["response.mcp_call.completed"] = Field(
        ..., alias="type"
    )
    item_id: str = Field(
        ...
    )
    output_index: int = Field(
        ...
    )
    sequence_number: int = Field(
        ...
    )

class ResponseMcpCallFailedEvent(BaseModel):
    """Emitted when an MCP  tool call has failed."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["response.mcp_call.failed"] = Field(
        ..., alias="type"
    )
    item_id: str = Field(
        ...
    )
    output_index: int = Field(
        ...
    )
    sequence_number: int = Field(
        ...
    )

class ResponseMcpCallInProgressEvent(BaseModel):
    """Emitted when an MCP  tool call is in progress."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["response.mcp_call.in_progress"] = Field(
        ..., alias="type"
    )
    sequence_number: int = Field(
        ...
    )
    output_index: int = Field(
        ...
    )
    item_id: str = Field(
        ...
    )

class ResponseMcpListToolsCompletedEvent(BaseModel):
    """Emitted when the list of available MCP tools has been successfully retrieved."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["response.mcp_list_tools.completed"] = Field(
        ..., alias="type"
    )
    item_id: str = Field(
        ...
    )
    output_index: int = Field(
        ...
    )
    sequence_number: int = Field(
        ...
    )

class ResponseMcpListToolsFailedEvent(BaseModel):
    """Emitted when the attempt to list available MCP tools has failed."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["response.mcp_list_tools.failed"] = Field(
        ..., alias="type"
    )
    item_id: str = Field(
        ...
    )
    output_index: int = Field(
        ...
    )
    sequence_number: int = Field(
        ...
    )

class ResponseMcpListToolsInProgressEvent(BaseModel):
    """Emitted when the system is in the process of retrieving the list of available MCP tools."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["response.mcp_list_tools.in_progress"] = Field(
        ..., alias="type"
    )
    item_id: str = Field(
        ...
    )
    output_index: int = Field(
        ...
    )
    sequence_number: int = Field(
        ...
    )

class ResponseModalities(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class ResponseOutputItemAddedEvent(BaseModel):
    """Emitted when a new output item is added."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["response.output_item.added"] = Field(
        ..., alias="type"
    )
    output_index: int = Field(
        ...
    )
    sequence_number: int = Field(
        ...
    )
    item: Union[OutputMessage, FileSearchToolCall, FunctionToolCall, WebSearchToolCall, ComputerToolCall, Reasoning, CompactionItem, ImageGenerationCall, CodeInterpreterToolCall, LocalShellCall, ShellToolCall, ShellCallOutput, ApplyPatchToolCall, ApplyPatchToolCallOutput, McpToolCall, McpListTools, McpApprovalRequest, CustomToolCall] = Field(
        ...
    )

class ResponseOutputItemDoneEvent(BaseModel):
    """Emitted when an output item is marked done."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["response.output_item.done"] = Field(
        ..., alias="type"
    )
    output_index: int = Field(
        ...
    )
    sequence_number: int = Field(
        ...
    )
    item: Union[OutputMessage, FileSearchToolCall, FunctionToolCall, WebSearchToolCall, ComputerToolCall, Reasoning, CompactionItem, ImageGenerationCall, CodeInterpreterToolCall, LocalShellCall, ShellToolCall, ShellCallOutput, ApplyPatchToolCall, ApplyPatchToolCallOutput, McpToolCall, McpListTools, McpApprovalRequest, CustomToolCall] = Field(
        ...
    )

class ResponseOutputTextAnnotationAddedEvent(BaseModel):
    """Emitted when an annotation is added to output text content."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["response.output_text.annotation.added"] = Field(
        ..., alias="type"
    )
    item_id: str = Field(
        ...
    )
    output_index: int = Field(
        ...
    )
    content_index: int = Field(
        ...
    )
    annotation_index: int = Field(
        ...
    )
    sequence_number: int = Field(
        ...
    )
    annotation: Dict[str, Any] = Field(
        ...
    )

class ResponsePromptVariables(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class ResponseProperties(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    previous_response_id: str = Field(
        None
    )
    model: Union[Union[str, Literal["gpt-5.2", "gpt-5.2-2025-12-11", "gpt-5.2-chat-latest", "gpt-5.2-pro", "gpt-5.2-pro-2025-12-11", "gpt-5.1", "gpt-5.1-2025-11-13", "gpt-5.1-codex", "gpt-5.1-mini", "gpt-5.1-chat-latest", "gpt-5", "gpt-5-mini", "gpt-5-nano", "gpt-5-2025-08-07", "gpt-5-mini-2025-08-07", "gpt-5-nano-2025-08-07", "gpt-5-chat-latest", "gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano", "gpt-4.1-2025-04-14", "gpt-4.1-mini-2025-04-14", "gpt-4.1-nano-2025-04-14", "o4-mini", "o4-mini-2025-04-16", "o3", "o3-2025-04-16", "o3-mini", "o3-mini-2025-01-31", "o1", "o1-2024-12-17", "o1-preview", "o1-preview-2024-09-12", "o1-mini", "o1-mini-2024-09-12", "gpt-4o", "gpt-4o-2024-11-20", "gpt-4o-2024-08-06", "gpt-4o-2024-05-13", "gpt-4o-audio-preview", "gpt-4o-audio-preview-2024-10-01", "gpt-4o-audio-preview-2024-12-17", "gpt-4o-audio-preview-2025-06-03", "gpt-4o-mini-audio-preview", "gpt-4o-mini-audio-preview-2024-12-17", "gpt-4o-search-preview", "gpt-4o-mini-search-preview", "gpt-4o-search-preview-2025-03-11", "gpt-4o-mini-search-preview-2025-03-11", "chatgpt-4o-latest", "codex-mini-latest", "gpt-4o-mini", "gpt-4o-mini-2024-07-18", "gpt-4-turbo", "gpt-4-turbo-2024-04-09", "gpt-4-0125-preview", "gpt-4-turbo-preview", "gpt-4-1106-preview", "gpt-4-vision-preview", "gpt-4", "gpt-4-0314", "gpt-4-0613", "gpt-4-32k", "gpt-4-32k-0314", "gpt-4-32k-0613", "gpt-3.5-turbo", "gpt-3.5-turbo-16k", "gpt-3.5-turbo-0301", "gpt-3.5-turbo-0613", "gpt-3.5-turbo-1106", "gpt-3.5-turbo-0125", "gpt-3.5-turbo-16k-0613"]], Literal["o1-pro", "o1-pro-2025-03-19", "o3-pro", "o3-pro-2025-06-10", "o3-deep-research", "o3-deep-research-2025-06-26", "o4-mini-deep-research", "o4-mini-deep-research-2025-06-26", "computer-use-preview", "computer-use-preview-2025-03-11", "gpt-5-codex", "gpt-5-pro", "gpt-5-pro-2025-10-06", "gpt-5.1-codex-max"]] = Field(
        None
    )
    reasoning: Reasoning = Field(
        None
    )
    background: bool = Field(
        None
    )
    max_output_tokens: int = Field(
        None
    )
    max_tool_calls: int = Field(
        None
    )
    text: Dict[str, Any] = Field(
        None
    )
    tools: List[Union[Function, FileSearch, ComputerUsePreview, WebSearch, McpTool, CodeInterpreter, ImageGenerationTool, LocalShellTool, ShellTool, CustomTool, WebSearchPreview, ApplyPatchTool]] = Field(
        None
    )
    tool_choice: Union[Literal["none", "auto", "required"], AllowedTools, HostedTool, FunctionTool, McpTool, CustomTool, SpecificApplyPatchToolChoice, SpecificShellToolChoice] = Field(
        None
    )
    prompt: Dict[str, Any] = Field(
        None
    )
    truncation: Literal["auto", "disabled"] = Field(
        None
    )

class ResponseQueuedEvent(BaseModel):
    """Emitted when a response is queued and waiting to be processed."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["response.queued"] = Field(
        ..., alias="type"
    )
    response: Dict[str, Any] = Field(
        ...
    )
    sequence_number: int = Field(
        ...
    )

class ResponseReasoningSummaryPartAddedEvent(BaseModel):
    """Emitted when a new reasoning summary part is added."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["response.reasoning_summary_part.added"] = Field(
        ..., alias="type"
    )
    item_id: str = Field(
        ...
    )
    output_index: int = Field(
        ...
    )
    summary_index: int = Field(
        ...
    )
    sequence_number: int = Field(
        ...
    )
    part: Dict[str, Any] = Field(
        ...
    )

class ResponseReasoningSummaryPartDoneEvent(BaseModel):
    """Emitted when a reasoning summary part is completed."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["response.reasoning_summary_part.done"] = Field(
        ..., alias="type"
    )
    item_id: str = Field(
        ...
    )
    output_index: int = Field(
        ...
    )
    summary_index: int = Field(
        ...
    )
    sequence_number: int = Field(
        ...
    )
    part: Dict[str, Any] = Field(
        ...
    )

class ResponseReasoningSummaryTextDeltaEvent(BaseModel):
    """Emitted when a delta is added to a reasoning summary text."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["response.reasoning_summary_text.delta"] = Field(
        ..., alias="type"
    )
    item_id: str = Field(
        ...
    )
    output_index: int = Field(
        ...
    )
    summary_index: int = Field(
        ...
    )
    delta: str = Field(
        ...
    )
    sequence_number: int = Field(
        ...
    )

class ResponseReasoningSummaryTextDoneEvent(BaseModel):
    """Emitted when a reasoning summary text is completed."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["response.reasoning_summary_text.done"] = Field(
        ..., alias="type"
    )
    item_id: str = Field(
        ...
    )
    output_index: int = Field(
        ...
    )
    summary_index: int = Field(
        ...
    )
    text: str = Field(
        ...
    )
    sequence_number: int = Field(
        ...
    )

class ResponseReasoningTextDeltaEvent(BaseModel):
    """Emitted when a delta is added to a reasoning text."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["response.reasoning_text.delta"] = Field(
        ..., alias="type"
    )
    item_id: str = Field(
        ...
    )
    output_index: int = Field(
        ...
    )
    content_index: int = Field(
        ...
    )
    delta: str = Field(
        ...
    )
    sequence_number: int = Field(
        ...
    )

class ResponseReasoningTextDoneEvent(BaseModel):
    """Emitted when a reasoning text is completed."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["response.reasoning_text.done"] = Field(
        ..., alias="type"
    )
    item_id: str = Field(
        ...
    )
    output_index: int = Field(
        ...
    )
    content_index: int = Field(
        ...
    )
    text: str = Field(
        ...
    )
    sequence_number: int = Field(
        ...
    )

class ResponseRefusalDeltaEvent(BaseModel):
    """Emitted when there is a partial refusal text."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["response.refusal.delta"] = Field(
        ..., alias="type"
    )
    item_id: str = Field(
        ...
    )
    output_index: int = Field(
        ...
    )
    content_index: int = Field(
        ...
    )
    delta: str = Field(
        ...
    )
    sequence_number: int = Field(
        ...
    )

class ResponseRefusalDoneEvent(BaseModel):
    """Emitted when refusal text is finalized."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["response.refusal.done"] = Field(
        ..., alias="type"
    )
    item_id: str = Field(
        ...
    )
    output_index: int = Field(
        ...
    )
    content_index: int = Field(
        ...
    )
    refusal: str = Field(
        ...
    )
    sequence_number: int = Field(
        ...
    )

class ResponseStreamEvent(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class ResponseStreamOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class ResponseTextDeltaEvent(BaseModel):
    """Emitted when there is an additional text delta."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["response.output_text.delta"] = Field(
        ..., alias="type"
    )
    item_id: str = Field(
        ...
    )
    output_index: int = Field(
        ...
    )
    content_index: int = Field(
        ...
    )
    delta: str = Field(
        ...
    )
    sequence_number: int = Field(
        ...
    )
    logprobs: List[Dict[str, Any]] = Field(
        ...
    )

class ResponseTextDoneEvent(BaseModel):
    """Emitted when text content is finalized."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["response.output_text.done"] = Field(
        ..., alias="type"
    )
    item_id: str = Field(
        ...
    )
    output_index: int = Field(
        ...
    )
    content_index: int = Field(
        ...
    )
    text: str = Field(
        ...
    )
    sequence_number: int = Field(
        ...
    )
    logprobs: List[Dict[str, Any]] = Field(
        ...
    )

class ResponseTextParam(BaseModel):
    """Configuration options for a text response from the model. Can be plain
text or structured JSON data. Learn more:
- [Text inputs and outputs](https://platform.openai.com/docs/guides/text)
- [Structured Outputs](https://platform.openai.com/docs/guides/structured-outputs)"""
    model_config = ConfigDict(populate_by_name=True)

    format: Union[Text, JsonSchema, JsonObject] = Field(
        None
    )
    verbosity: Literal["low", "medium", "high"] = Field(
        None
    )

class ResponseUsage(BaseModel):
    """Represents token usage details including input tokens, output tokens,
a breakdown of output tokens, and the total tokens used."""
    model_config = ConfigDict(populate_by_name=True)

    input_tokens: int = Field(
        ...
    )
    input_tokens_details: Dict[str, Any] = Field(
        ...
    )
    output_tokens: int = Field(
        ...
    )
    output_tokens_details: Dict[str, Any] = Field(
        ...
    )
    total_tokens: int = Field(
        ...
    )

class ResponseWebSearchCallCompletedEvent(BaseModel):
    """Emitted when a web search call is completed."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["response.web_search_call.completed"] = Field(
        ..., alias="type"
    )
    output_index: int = Field(
        ...
    )
    item_id: str = Field(
        ...
    )
    sequence_number: int = Field(
        ...
    )

class ResponseWebSearchCallInProgressEvent(BaseModel):
    """Emitted when a web search call is initiated."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["response.web_search_call.in_progress"] = Field(
        ..., alias="type"
    )
    output_index: int = Field(
        ...
    )
    item_id: str = Field(
        ...
    )
    sequence_number: int = Field(
        ...
    )

class ResponseWebSearchCallSearchingEvent(BaseModel):
    """Emitted when a web search call is executing."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["response.web_search_call.searching"] = Field(
        ..., alias="type"
    )
    output_index: int = Field(
        ...
    )
    item_id: str = Field(
        ...
    )
    sequence_number: int = Field(
        ...
    )

class Role(BaseModel):
    """Details about a role that can be assigned through the public Roles API."""
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["role"] = Field(
        ...
    )
    id_: str = Field(
        ..., alias="id"
    )
    name: str = Field(
        ...
    )
    description: str = Field(
        ...
    )
    permissions: List[str] = Field(
        ...
    )
    resource_type: str = Field(
        ...
    )
    predefined_role: bool = Field(
        ...
    )

class RoleDeletedResource(BaseModel):
    """Confirmation payload returned after deleting a role."""
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["role.deleted"] = Field(
        ...
    )
    id_: str = Field(
        ..., alias="id"
    )
    deleted: bool = Field(
        ...
    )

class RoleListResource(BaseModel):
    """Paginated list of roles assigned to a principal."""
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["list"] = Field(
        ...
    )
    data: List[Dict[str, Any]] = Field(
        ...
    )
    has_more: bool = Field(
        ...
    )
    next: str = Field(
        ...
    )

class RunCompletionUsage(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class RunGraderRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    grader: Union[StringCheckGrader, TextSimilarityGrader, PythonGrader, ScoreModelGrader, MultiGrader] = Field(
        ...
    )
    item: Dict[str, Any] = Field(
        None
    )
    model_sample: str = Field(
        ...
    )

class RunGraderResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    reward: float = Field(
        ...
    )
    metadata: Dict[str, Any] = Field(
        ...
    )
    sub_rewards: Dict[str, Any] = Field(
        ...
    )
    model_grader_token_usage_per_model: Dict[str, Any] = Field(
        ...
    )

class RunObject(BaseModel):
    """Represents an execution run on a [thread](https://platform.openai.com/docs/api-reference/threads)."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )
    object: Literal["thread.run"] = Field(
        ...
    )
    created_at: int = Field(
        ...
    )
    thread_id: str = Field(
        ...
    )
    assistant_id: str = Field(
        ...
    )
    status: Literal["queued", "in_progress", "requires_action", "cancelling", "cancelled", "failed", "completed", "incomplete", "expired"] = Field(
        ...
    )
    required_action: Optional[Dict[str, Any]] = Field(
        ...
    )
    last_error: Optional[Dict[str, Any]] = Field(
        ...
    )
    expires_at: Optional[int] = Field(
        ...
    )
    started_at: Optional[int] = Field(
        ...
    )
    cancelled_at: Optional[int] = Field(
        ...
    )
    failed_at: Optional[int] = Field(
        ...
    )
    completed_at: Optional[int] = Field(
        ...
    )
    incomplete_details: Optional[Dict[str, Any]] = Field(
        ...
    )
    model: str = Field(
        ...
    )
    instructions: str = Field(
        ...
    )
    tools: List[Union[CodeInterpreterTool, FileSearchTool, FunctionTool]] = Field(
        ...
    )
    metadata: Dict[str, str] = Field(
        ...
    )
    usage: Dict[str, Any] = Field(
        ...
    )
    temperature: Optional[float] = Field(
        None
    )
    top_p: Optional[float] = Field(
        None
    )
    max_prompt_tokens: Optional[int] = Field(
        ...
    )
    max_completion_tokens: Optional[int] = Field(
        ...
    )
    truncation_strategy: ThreadTruncationControls = Field(
        ...
    )
    tool_choice: Union[Literal["none", "auto", "required"], Dict[str, Any]] = Field(
        ...
    )
    parallel_tool_calls: bool = Field(
        ...
    )
    response_format: Union[Literal["auto"], Text, JsonObject, JsonSchema] = Field(
        ...
    )

class RunStepCompletionUsage(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class RunStepDeltaObject(BaseModel):
    """Represents a run step delta i.e. any changed fields on a run step during streaming."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )
    object: Literal["thread.run.step.delta"] = Field(
        ...
    )
    delta: Dict[str, Any] = Field(
        ...
    )

class RunStepDeltaStepDetailsMessageCreationObject(BaseModel):
    """Details of the message creation by the run step."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["message_creation"] = Field(
        ..., alias="type"
    )
    message_creation: Dict[str, Any] = Field(
        None
    )

class RunStepDeltaStepDetailsToolCallsCodeObject(BaseModel):
    """Details of the Code Interpreter tool call the run step was involved in."""
    model_config = ConfigDict(populate_by_name=True)

    index: int = Field(
        ...
    )
    id_: str = Field(
        None, alias="id"
    )
    type_: Literal["code_interpreter"] = Field(
        ..., alias="type"
    )
    code_interpreter: Dict[str, Any] = Field(
        None
    )

class RunStepDeltaStepDetailsToolCallsCodeOutputImageObject(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    index: int = Field(
        ...
    )
    type_: Literal["image"] = Field(
        ..., alias="type"
    )
    image: Dict[str, Any] = Field(
        None
    )

class RunStepDeltaStepDetailsToolCallsCodeOutputLogsObject(BaseModel):
    """Text output from the Code Interpreter tool call as part of a run step."""
    model_config = ConfigDict(populate_by_name=True)

    index: int = Field(
        ...
    )
    type_: Literal["logs"] = Field(
        ..., alias="type"
    )
    logs: str = Field(
        None
    )

class RunStepDeltaStepDetailsToolCallsFileSearchObject(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    index: int = Field(
        ...
    )
    id_: str = Field(
        None, alias="id"
    )
    type_: Literal["file_search"] = Field(
        ..., alias="type"
    )
    file_search: Dict[str, Any] = Field(
        ...
    )

class RunStepDeltaStepDetailsToolCallsFunctionObject(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    index: int = Field(
        ...
    )
    id_: str = Field(
        None, alias="id"
    )
    type_: Literal["function"] = Field(
        ..., alias="type"
    )
    function: Dict[str, Any] = Field(
        None
    )

class RunStepDeltaStepDetailsToolCallsObject(BaseModel):
    """Details of the tool call."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["tool_calls"] = Field(
        ..., alias="type"
    )
    tool_calls: List[Union[CodeInterpreterToolCall, FileSearchToolCall, FunctionToolCall]] = Field(
        None
    )

class RunStepDetailsMessageCreationObject(BaseModel):
    """Details of the message creation by the run step."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["message_creation"] = Field(
        ..., alias="type"
    )
    message_creation: Dict[str, Any] = Field(
        ...
    )

class RunStepDetailsToolCallsCodeObject(BaseModel):
    """Details of the Code Interpreter tool call the run step was involved in."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )
    type_: Literal["code_interpreter"] = Field(
        ..., alias="type"
    )
    code_interpreter: Dict[str, Any] = Field(
        ...
    )

class RunStepDetailsToolCallsCodeOutputImageObject(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["image"] = Field(
        ..., alias="type"
    )
    image: Dict[str, Any] = Field(
        ...
    )

class RunStepDetailsToolCallsCodeOutputLogsObject(BaseModel):
    """Text output from the Code Interpreter tool call as part of a run step."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["logs"] = Field(
        ..., alias="type"
    )
    logs: str = Field(
        ...
    )

class RunStepDetailsToolCallsFileSearchObject(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )
    type_: Literal["file_search"] = Field(
        ..., alias="type"
    )
    file_search: Dict[str, Any] = Field(
        ...
    )

class RunStepDetailsToolCallsFileSearchRankingOptionsObject(BaseModel):
    """The ranking options for the file search."""
    model_config = ConfigDict(populate_by_name=True)

    ranker: Literal["auto", "default_2024_08_21"] = Field(
        ...
    )
    score_threshold: float = Field(
        ...
    )

class RunStepDetailsToolCallsFileSearchResultObject(BaseModel):
    """A result instance of the file search."""
    model_config = ConfigDict(populate_by_name=True)

    file_id: str = Field(
        ...
    )
    file_name: str = Field(
        ...
    )
    score: float = Field(
        ...
    )
    content: List[Dict[str, Any]] = Field(
        None
    )

class RunStepDetailsToolCallsFunctionObject(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )
    type_: Literal["function"] = Field(
        ..., alias="type"
    )
    function: Dict[str, Any] = Field(
        ...
    )

class RunStepDetailsToolCallsObject(BaseModel):
    """Details of the tool call."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["tool_calls"] = Field(
        ..., alias="type"
    )
    tool_calls: List[Union[CodeInterpreterToolCall, FileSearchToolCall, FunctionToolCall]] = Field(
        ...
    )

class RunStepObject(BaseModel):
    """Represents a step in execution of a run."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )
    object: Literal["thread.run.step"] = Field(
        ...
    )
    created_at: int = Field(
        ...
    )
    assistant_id: str = Field(
        ...
    )
    thread_id: str = Field(
        ...
    )
    run_id: str = Field(
        ...
    )
    type_: Literal["message_creation", "tool_calls"] = Field(
        ..., alias="type"
    )
    status: Literal["in_progress", "cancelled", "failed", "completed", "expired"] = Field(
        ...
    )
    step_details: Union[MessageCreation, ToolCalls] = Field(
        ...
    )
    last_error: Dict[str, Any] = Field(
        ...
    )
    expired_at: int = Field(
        ...
    )
    cancelled_at: int = Field(
        ...
    )
    failed_at: int = Field(
        ...
    )
    completed_at: int = Field(
        ...
    )
    metadata: Dict[str, str] = Field(
        ...
    )
    usage: Dict[str, Any] = Field(
        ...
    )

class RunStepStreamEvent(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class RunStreamEvent(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class RunToolCallObject(BaseModel):
    """Tool call objects"""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )
    type_: Literal["function"] = Field(
        ..., alias="type"
    )
    function: Dict[str, Any] = Field(
        ...
    )

class Screenshot(BaseModel):
    """A screenshot action."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["screenshot"] = Field(
        ..., alias="type"
    )

class Scroll(BaseModel):
    """A scroll action."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["scroll"] = Field(
        ..., alias="type"
    )
    x: int = Field(
        ...
    )
    y: int = Field(
        ...
    )
    scroll_x: int = Field(
        ...
    )
    scroll_y: int = Field(
        ...
    )

class ServiceTier(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class SpeechAudioDeltaEvent(BaseModel):
    """Emitted for each chunk of audio data generated during speech synthesis."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["speech.audio.delta"] = Field(
        ..., alias="type"
    )
    audio: str = Field(
        ...
    )

class SpeechAudioDoneEvent(BaseModel):
    """Emitted when the speech synthesis is complete and all audio has been streamed."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["speech.audio.done"] = Field(
        ..., alias="type"
    )
    usage: Dict[str, Any] = Field(
        ...
    )

class StaticChunkingStrategy(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    max_chunk_size_tokens: int = Field(
        ...
    )
    chunk_overlap_tokens: int = Field(
        ...
    )

class StaticChunkingStrategyRequestParam(BaseModel):
    """Customize your own chunking strategy by setting chunk size and chunk overlap."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["static"] = Field(
        ..., alias="type"
    )
    static: Dict[str, Any] = Field(
        ...
    )

class StaticChunkingStrategyResponseParam(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["static"] = Field(
        ..., alias="type"
    )
    static: Dict[str, Any] = Field(
        ...
    )

class StopConfiguration(BaseModel):
    """Not supported with latest reasoning models `o3` and `o4-mini`.

Up to 4 sequences where the API will stop generating further tokens. The
returned text will not contain the stop sequence."""
    model_config = ConfigDict(populate_by_name=True)

    pass

class SubmitToolOutputsRunRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    tool_outputs: List[Dict[str, Any]] = Field(
        ...
    )
    stream: bool = Field(
        None
    )

class TextResponseFormatConfiguration(BaseModel):
    """An object specifying the format that the model must output.

Configuring `{ "type": "json_schema" }` enables Structured Outputs, 
which ensures the model will match your supplied JSON schema. Learn more in the 
[Structured Outputs guide](https://platform.openai.com/docs/guides/structured-outputs).

The default format is `{ "type": "text" }` with no additional options.

**Not recommended for gpt-4o and newer models:**

Setting to `{ "type": "json_object" }` enables the older JSON mode, which
ensures the message the model generates is valid JSON. Using `json_schema`
is preferred for models that support it."""
    model_config = ConfigDict(populate_by_name=True)

    pass

class TextResponseFormatJsonSchema(BaseModel):
    """JSON Schema response format. Used to generate structured JSON responses.
Learn more about [Structured Outputs](https://platform.openai.com/docs/guides/structured-outputs)."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["json_schema"] = Field(
        ..., alias="type"
    )
    description: str = Field(
        None
    )
    name: str = Field(
        ...
    )
    schema: Dict[str, Any] = Field(
        ...
    )
    strict: bool = Field(
        None
    )

class ThreadObject(BaseModel):
    """Represents a thread that contains [messages](https://platform.openai.com/docs/api-reference/messages)."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )
    object: Literal["thread"] = Field(
        ...
    )
    created_at: int = Field(
        ...
    )
    tool_resources: Dict[str, Any] = Field(
        ...
    )
    metadata: Dict[str, str] = Field(
        ...
    )

class ThreadStreamEvent(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class ToggleCertificatesRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    certificate_ids: List[str] = Field(
        ...
    )

class Tool(BaseModel):
    """A tool that can be used to generate a response."""
    model_config = ConfigDict(populate_by_name=True)

    pass

class ToolChoiceAllowed(BaseModel):
    """Constrains the tools available to the model to a pre-defined set."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["allowed_tools"] = Field(
        ..., alias="type"
    )
    mode: Literal["auto", "required"] = Field(
        ...
    )
    tools: List[Dict[str, Any]] = Field(
        ...
    )

class ToolChoiceCustom(BaseModel):
    """Use this option to force the model to call a specific custom tool."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["custom"] = Field(
        ..., alias="type"
    )
    name: str = Field(
        ...
    )

class ToolChoiceFunction(BaseModel):
    """Use this option to force the model to call a specific function."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["function"] = Field(
        ..., alias="type"
    )
    name: str = Field(
        ...
    )

class ToolChoiceMcp(BaseModel):
    """Use this option to force the model to call a specific tool on a remote MCP server."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["mcp"] = Field(
        ..., alias="type"
    )
    server_label: str = Field(
        ...
    )
    name: str = Field(
        None
    )

class ToolChoiceOptions(str, Enum):
    """Controls which (if any) tool is called by the model.

`none` means the model will not call any tool and instead generates a message.

`auto` means the model can pick between generating a message or calling one or
more tools.

`required` means the model must call one or more tools."""
    NONE = "none"
    AUTO = "auto"
    REQUIRED = "required"

class ToolChoiceParam(BaseModel):
    """How the model should select which tool (or tools) to use when generating
a response. See the `tools` parameter to see how to specify which tools
the model can call."""
    model_config = ConfigDict(populate_by_name=True)

    pass

class ToolChoiceTypes(BaseModel):
    """Indicates that the model should use a built-in tool to generate a response.
[Learn more about built-in tools](https://platform.openai.com/docs/guides/tools)."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["file_search", "web_search_preview", "computer_use_preview", "web_search_preview_2025_03_11", "image_generation", "code_interpreter"] = Field(
        ..., alias="type"
    )

class ToolsArray(BaseModel):
    """An array of tools the model may call while generating a response. You
can specify which tool to use by setting the `tool_choice` parameter.

We support the following categories of tools:
- **Built-in tools**: Tools that are provided by OpenAI that extend the
  model's capabilities, like [web search](https://platform.openai.com/docs/guides/tools-web-search)
  or [file search](https://platform.openai.com/docs/guides/tools-file-search). Learn more about
  [built-in tools](https://platform.openai.com/docs/guides/tools).
- **MCP Tools**: Integrations with third-party systems via custom MCP servers
  or predefined connectors such as Google Drive and SharePoint. Learn more about
  [MCP Tools](https://platform.openai.com/docs/guides/tools-connectors-mcp).
- **Function calls (custom tools)**: Functions that are defined by you,
  enabling the model to call your own code with strongly typed arguments
  and outputs. Learn more about
  [function calling](https://platform.openai.com/docs/guides/function-calling). You can also use
  custom tools to call your own code."""
    model_config = ConfigDict(populate_by_name=True)

    pass

class TranscriptTextDeltaEvent(BaseModel):
    """Emitted when there is an additional text delta. This is also the first event emitted when the transcription starts. Only emitted when you [create a transcription](https://platform.openai.com/docs/api-reference/audio/create-transcription) with the `Stream` parameter set to `true`."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["transcript.text.delta"] = Field(
        ..., alias="type"
    )
    delta: str = Field(
        ...
    )
    logprobs: List[Dict[str, Any]] = Field(
        None
    )
    segment_id: str = Field(
        None
    )

class TranscriptTextDoneEvent(BaseModel):
    """Emitted when the transcription is complete. Contains the complete transcription text. Only emitted when you [create a transcription](https://platform.openai.com/docs/api-reference/audio/create-transcription) with the `Stream` parameter set to `true`."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["transcript.text.done"] = Field(
        ..., alias="type"
    )
    text: str = Field(
        ...
    )
    logprobs: List[Dict[str, Any]] = Field(
        None
    )
    usage: TranscriptTextUsageTokens = Field(
        None
    )

class TranscriptTextSegmentEvent(BaseModel):
    """Emitted when a diarized transcription returns a completed segment with speaker information. Only emitted when you [create a transcription](https://platform.openai.com/docs/api-reference/audio/create-transcription) with `stream` set to `true` and `response_format` set to `diarized_json`."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["transcript.text.segment"] = Field(
        ..., alias="type"
    )
    id_: str = Field(
        ..., alias="id"
    )
    start: float = Field(
        ...
    )
    end: float = Field(
        ...
    )
    text: str = Field(
        ...
    )
    speaker: str = Field(
        ...
    )

class TranscriptTextUsageDuration(BaseModel):
    """Usage statistics for models billed by audio input duration."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["duration"] = Field(
        ..., alias="type"
    )
    seconds: float = Field(
        ...
    )

class TranscriptTextUsageTokens(BaseModel):
    """Usage statistics for models billed by token usage."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["tokens"] = Field(
        ..., alias="type"
    )
    input_tokens: int = Field(
        ...
    )
    input_token_details: Dict[str, Any] = Field(
        None
    )
    output_tokens: int = Field(
        ...
    )
    total_tokens: int = Field(
        ...
    )

class TranscriptionChunkingStrategy(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class TranscriptionDiarizedSegment(BaseModel):
    """A segment of diarized transcript text with speaker metadata."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["transcript.text.segment"] = Field(
        ..., alias="type"
    )
    id_: str = Field(
        ..., alias="id"
    )
    start: float = Field(
        ...
    )
    end: float = Field(
        ...
    )
    text: str = Field(
        ...
    )
    speaker: str = Field(
        ...
    )

class TranscriptionInclude(str, Enum):
    LOGPROBS = "logprobs"

class TranscriptionSegment(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id_: int = Field(
        ..., alias="id"
    )
    seek: int = Field(
        ...
    )
    start: float = Field(
        ...
    )
    end: float = Field(
        ...
    )
    text: str = Field(
        ...
    )
    tokens: List[int] = Field(
        ...
    )
    temperature: float = Field(
        ...
    )
    avg_logprob: float = Field(
        ...
    )
    compression_ratio: float = Field(
        ...
    )
    no_speech_prob: float = Field(
        ...
    )

class TranscriptionWord(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    word: str = Field(
        ...
    )
    start: float = Field(
        ...
    )
    end: float = Field(
        ...
    )

class TruncationObject(BaseModel):
    """Controls for how a thread will be truncated prior to the run. Use this to control the initial context window of the run."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["auto", "last_messages"] = Field(
        ..., alias="type"
    )
    last_messages: int = Field(
        None
    )

class Type(BaseModel):
    """An action to type in text."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["type"] = Field(
        ..., alias="type"
    )
    text: str = Field(
        ...
    )

class UpdateGroupBody(BaseModel):
    """Request payload for updating the details of an existing group."""
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(
        ...
    )

class UpdateVectorStoreFileAttributesRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    attributes: Dict[str, Union[str, float, bool]] = Field(
        ...
    )

class UpdateVectorStoreRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: Optional[str] = Field(
        None
    )
    expires_after: VectorStoreExpirationPolicy = Field(
        None
    )
    metadata: Dict[str, str] = Field(
        None
    )

class UpdateVoiceConsentRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(
        ...
    )

class Upload(BaseModel):
    """The Upload object can accept byte chunks in the form of Parts."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )
    created_at: int = Field(
        ...
    )
    filename: str = Field(
        ...
    )
    bytes: int = Field(
        ...
    )
    purpose: str = Field(
        ...
    )
    status: Literal["pending", "completed", "cancelled", "expired"] = Field(
        ...
    )
    expires_at: int = Field(
        ...
    )
    object: Literal["upload"] = Field(
        ...
    )
    file: Any = Field(
        None
    )

class UploadCertificateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(
        None
    )
    content: str = Field(
        ...
    )

class UploadPart(BaseModel):
    """The upload Part represents a chunk of bytes we can add to an Upload object."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )
    created_at: int = Field(
        ...
    )
    upload_id: str = Field(
        ...
    )
    object: Literal["upload.part"] = Field(
        ...
    )

class UsageAudioSpeechesResult(BaseModel):
    """The aggregated audio speeches usage details of the specific time bucket."""
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["organization.usage.audio_speeches.result"] = Field(
        ...
    )
    characters: int = Field(
        ...
    )
    num_model_requests: int = Field(
        ...
    )
    project_id: str = Field(
        None
    )
    user_id: str = Field(
        None
    )
    api_key_id: str = Field(
        None
    )
    model: str = Field(
        None
    )

class UsageAudioTranscriptionsResult(BaseModel):
    """The aggregated audio transcriptions usage details of the specific time bucket."""
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["organization.usage.audio_transcriptions.result"] = Field(
        ...
    )
    seconds: int = Field(
        ...
    )
    num_model_requests: int = Field(
        ...
    )
    project_id: str = Field(
        None
    )
    user_id: str = Field(
        None
    )
    api_key_id: str = Field(
        None
    )
    model: str = Field(
        None
    )

class UsageCodeInterpreterSessionsResult(BaseModel):
    """The aggregated code interpreter sessions usage details of the specific time bucket."""
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["organization.usage.code_interpreter_sessions.result"] = Field(
        ...
    )
    num_sessions: int = Field(
        None
    )
    project_id: str = Field(
        None
    )

class UsageCompletionsResult(BaseModel):
    """The aggregated completions usage details of the specific time bucket."""
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["organization.usage.completions.result"] = Field(
        ...
    )
    input_tokens: int = Field(
        ...
    )
    input_cached_tokens: int = Field(
        None
    )
    output_tokens: int = Field(
        ...
    )
    input_audio_tokens: int = Field(
        None
    )
    output_audio_tokens: int = Field(
        None
    )
    num_model_requests: int = Field(
        ...
    )
    project_id: str = Field(
        None
    )
    user_id: str = Field(
        None
    )
    api_key_id: str = Field(
        None
    )
    model: str = Field(
        None
    )
    batch: bool = Field(
        None
    )
    service_tier: str = Field(
        None
    )

class UsageEmbeddingsResult(BaseModel):
    """The aggregated embeddings usage details of the specific time bucket."""
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["organization.usage.embeddings.result"] = Field(
        ...
    )
    input_tokens: int = Field(
        ...
    )
    num_model_requests: int = Field(
        ...
    )
    project_id: str = Field(
        None
    )
    user_id: str = Field(
        None
    )
    api_key_id: str = Field(
        None
    )
    model: str = Field(
        None
    )

class UsageImagesResult(BaseModel):
    """The aggregated images usage details of the specific time bucket."""
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["organization.usage.images.result"] = Field(
        ...
    )
    images: int = Field(
        ...
    )
    num_model_requests: int = Field(
        ...
    )
    source: str = Field(
        None
    )
    size: str = Field(
        None
    )
    project_id: str = Field(
        None
    )
    user_id: str = Field(
        None
    )
    api_key_id: str = Field(
        None
    )
    model: str = Field(
        None
    )

class UsageModerationsResult(BaseModel):
    """The aggregated moderations usage details of the specific time bucket."""
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["organization.usage.moderations.result"] = Field(
        ...
    )
    input_tokens: int = Field(
        ...
    )
    num_model_requests: int = Field(
        ...
    )
    project_id: str = Field(
        None
    )
    user_id: str = Field(
        None
    )
    api_key_id: str = Field(
        None
    )
    model: str = Field(
        None
    )

class UsageResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["page"] = Field(
        ...
    )
    data: List[Dict[str, Any]] = Field(
        ...
    )
    has_more: bool = Field(
        ...
    )
    next_page: str = Field(
        ...
    )

class UsageTimeBucket(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["bucket"] = Field(
        ...
    )
    start_time: int = Field(
        ...
    )
    end_time: int = Field(
        ...
    )
    result: List[Union[Dict[str, Any]]] = Field(
        ...
    )

class UsageVectorStoresResult(BaseModel):
    """The aggregated vector stores usage details of the specific time bucket."""
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["organization.usage.vector_stores.result"] = Field(
        ...
    )
    usage_bytes: int = Field(
        ...
    )
    project_id: str = Field(
        None
    )

class User(BaseModel):
    """Represents an individual `user` within an organization."""
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["organization.user"] = Field(
        ...
    )
    id_: str = Field(
        ..., alias="id"
    )
    name: str = Field(
        ...
    )
    email: str = Field(
        ...
    )
    role: Literal["owner", "reader"] = Field(
        ...
    )
    added_at: int = Field(
        ...
    )

class UserDeleteResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["organization.user.deleted"] = Field(
        ...
    )
    id_: str = Field(
        ..., alias="id"
    )
    deleted: bool = Field(
        ...
    )

class UserListResource(BaseModel):
    """Paginated list of user objects returned when inspecting group membership."""
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["list"] = Field(
        ...
    )
    data: List[Dict[str, Any]] = Field(
        ...
    )
    has_more: bool = Field(
        ...
    )
    next: str = Field(
        ...
    )

class UserListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["list"] = Field(
        ...
    )
    data: List[Dict[str, Any]] = Field(
        ...
    )
    first_id: str = Field(
        ...
    )
    last_id: str = Field(
        ...
    )
    has_more: bool = Field(
        ...
    )

class UserRoleAssignment(BaseModel):
    """Role assignment linking a user to a role."""
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["user.role"] = Field(
        ...
    )
    user: Dict[str, Any] = Field(
        ...
    )
    role: Dict[str, Any] = Field(
        ...
    )

class UserRoleUpdateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    role: Literal["owner", "reader"] = Field(
        ...
    )

class VadConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["server_vad"] = Field(
        ..., alias="type"
    )
    prefix_padding_ms: int = Field(
        None
    )
    silence_duration_ms: int = Field(
        None
    )
    threshold: float = Field(
        None
    )

class ValidateGraderRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    grader: Union[StringCheckGrader, TextSimilarityGrader, PythonGrader, ScoreModelGrader, MultiGrader] = Field(
        ...
    )

class ValidateGraderResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    grader: Union[StringCheckGrader, TextSimilarityGrader, PythonGrader, ScoreModelGrader, MultiGrader] = Field(
        None
    )

class VectorStoreExpirationAfter(BaseModel):
    """The expiration policy for a vector store."""
    model_config = ConfigDict(populate_by_name=True)

    anchor: Literal["last_active_at"] = Field(
        ...
    )
    days: int = Field(
        ...
    )

class VectorStoreFileAttributes(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class VectorStoreFileBatchObject(BaseModel):
    """A batch of files attached to a vector store."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )
    object: Literal["vector_store.files_batch"] = Field(
        ...
    )
    created_at: int = Field(
        ...
    )
    vector_store_id: str = Field(
        ...
    )
    status: Literal["in_progress", "completed", "cancelled", "failed"] = Field(
        ...
    )
    file_counts: Dict[str, Any] = Field(
        ...
    )

class VectorStoreFileContentResponse(BaseModel):
    """Represents the parsed content of a vector store file."""
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["vector_store.file_content.page"] = Field(
        ...
    )
    data: List[Dict[str, Any]] = Field(
        ...
    )
    has_more: bool = Field(
        ...
    )
    next_page: str = Field(
        ...
    )

class VectorStoreFileObject(BaseModel):
    """A list of files attached to a vector store."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )
    object: Literal["vector_store.file"] = Field(
        ...
    )
    usage_bytes: int = Field(
        ...
    )
    created_at: int = Field(
        ...
    )
    vector_store_id: str = Field(
        ...
    )
    status: Literal["in_progress", "completed", "cancelled", "failed"] = Field(
        ...
    )
    last_error: Dict[str, Any] = Field(
        ...
    )
    chunking_strategy: Union[StaticChunkingStrategy, OtherChunkingStrategy] = Field(
        None
    )
    attributes: Dict[str, Union[str, float, bool]] = Field(
        None
    )

class VectorStoreObject(BaseModel):
    """A vector store is a collection of processed files can be used by the `file_search` tool."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )
    object: Literal["vector_store"] = Field(
        ...
    )
    created_at: int = Field(
        ...
    )
    name: str = Field(
        ...
    )
    usage_bytes: int = Field(
        ...
    )
    file_counts: Dict[str, Any] = Field(
        ...
    )
    status: Literal["expired", "in_progress", "completed"] = Field(
        ...
    )
    expires_after: VectorStoreExpirationPolicy = Field(
        None
    )
    expires_at: int = Field(
        None
    )
    last_active_at: int = Field(
        ...
    )
    metadata: Dict[str, str] = Field(
        ...
    )

class VectorStoreSearchRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    query: Union[str, List[str]] = Field(
        ...
    )
    rewrite_query: bool = Field(
        None
    )
    max_num_results: int = Field(
        None
    )
    filters: Union[ComparisonFilter, CompoundFilter] = Field(
        None
    )
    ranking_options: Dict[str, Any] = Field(
        None
    )

class VectorStoreSearchResultContentObject(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["text"] = Field(
        ..., alias="type"
    )
    text: str = Field(
        ...
    )

class VectorStoreSearchResultItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    file_id: str = Field(
        ...
    )
    filename: str = Field(
        ...
    )
    score: float = Field(
        ...
    )
    attributes: Dict[str, Union[str, float, bool]] = Field(
        ...
    )
    content: List[Dict[str, Any]] = Field(
        ...
    )

class VectorStoreSearchResultsPage(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["vector_store.search_results.page"] = Field(
        ...
    )
    search_query: List[str] = Field(
        ...
    )
    data: List[Dict[str, Any]] = Field(
        ...
    )
    has_more: bool = Field(
        ...
    )
    next_page: str = Field(
        ...
    )

class Verbosity(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class VoiceConsentDeletedResource(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )
    object: Literal["audio.voice_consent"] = Field(
        ...
    )
    deleted: bool = Field(
        ...
    )

class VoiceConsentListResource(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["list"] = Field(
        ...
    )
    data: List[VoiceConsent] = Field(
        ...
    )
    first_id: str = Field(
        None
    )
    last_id: str = Field(
        None
    )
    has_more: bool = Field(
        ...
    )

class VoiceConsentResource(BaseModel):
    """A consent recording used to authorize creation of a custom voice."""
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["audio.voice_consent"] = Field(
        ...
    )
    id_: str = Field(
        ..., alias="id"
    )
    name: str = Field(
        ...
    )
    language: str = Field(
        ...
    )
    created_at: int = Field(
        ...
    )

class VoiceIdsShared(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class VoiceResource(BaseModel):
    """A custom voice that can be used for audio output."""
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["audio.voice"] = Field(
        ...
    )
    id_: str = Field(
        ..., alias="id"
    )
    name: str = Field(
        ...
    )
    created_at: int = Field(
        ...
    )

class Wait(BaseModel):
    """A wait action."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["wait"] = Field(
        ..., alias="type"
    )

class WebSearchActionFind(BaseModel):
    """Action type "find": Searches for a pattern within a loaded page."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["find"] = Field(
        ..., alias="type"
    )
    url: str = Field(
        ...
    )
    pattern: str = Field(
        ...
    )

class WebSearchActionOpenPage(BaseModel):
    """Action type "open_page" - Opens a specific URL from search results."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["open_page"] = Field(
        ..., alias="type"
    )
    url: str = Field(
        ...
    )

class WebSearchActionSearch(BaseModel):
    """Action type "search" - Performs a web search query."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["search"] = Field(
        ..., alias="type"
    )
    query: str = Field(
        ...
    )
    sources: List[WebSearchSource] = Field(
        None
    )

class WebSearchApproximateLocation(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class WebSearchContextSize(str, Enum):
    """High level guidance for the amount of context window space to use for the 
search. One of `low`, `medium`, or `high`. `medium` is the default."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class WebSearchLocation(BaseModel):
    """Approximate location parameters for the search."""
    model_config = ConfigDict(populate_by_name=True)

    country: str = Field(
        None
    )
    region: str = Field(
        None
    )
    city: str = Field(
        None
    )
    timezone: str = Field(
        None
    )

class WebSearchTool(BaseModel):
    """Search the Internet for sources related to the prompt. Learn more about the
[web search tool](https://platform.openai.com/docs/guides/tools-web-search)."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["web_search", "web_search_2025_08_26"] = Field(
        ..., alias="type"
    )
    filters: Dict[str, Any] = Field(
        None
    )
    user_location: WebSearchApproximateLocation = Field(
        None
    )
    search_context_size: Literal["low", "medium", "high"] = Field(
        None
    )

class WebSearchToolCall(BaseModel):
    """The results of a web search tool call. See the
[web search guide](https://platform.openai.com/docs/guides/tools-web-search) for more information."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )
    type_: Literal["web_search_call"] = Field(
        ..., alias="type"
    )
    status: Literal["in_progress", "searching", "completed", "failed"] = Field(
        ...
    )
    action: Union[SearchAction, OpenPageAction, FindAction] = Field(
        ...
    )

class WebhookBatchCancelled(BaseModel):
    """Sent when a batch API request has been cancelled."""
    model_config = ConfigDict(populate_by_name=True)

    created_at: int = Field(
        ...
    )
    id_: str = Field(
        ..., alias="id"
    )
    data: Dict[str, Any] = Field(
        ...
    )
    object: Literal["event"] = Field(
        None
    )
    type_: Literal["batch.cancelled"] = Field(
        ..., alias="type"
    )

class WebhookBatchCompleted(BaseModel):
    """Sent when a batch API request has been completed."""
    model_config = ConfigDict(populate_by_name=True)

    created_at: int = Field(
        ...
    )
    id_: str = Field(
        ..., alias="id"
    )
    data: Dict[str, Any] = Field(
        ...
    )
    object: Literal["event"] = Field(
        None
    )
    type_: Literal["batch.completed"] = Field(
        ..., alias="type"
    )

class WebhookBatchExpired(BaseModel):
    """Sent when a batch API request has expired."""
    model_config = ConfigDict(populate_by_name=True)

    created_at: int = Field(
        ...
    )
    id_: str = Field(
        ..., alias="id"
    )
    data: Dict[str, Any] = Field(
        ...
    )
    object: Literal["event"] = Field(
        None
    )
    type_: Literal["batch.expired"] = Field(
        ..., alias="type"
    )

class WebhookBatchFailed(BaseModel):
    """Sent when a batch API request has failed."""
    model_config = ConfigDict(populate_by_name=True)

    created_at: int = Field(
        ...
    )
    id_: str = Field(
        ..., alias="id"
    )
    data: Dict[str, Any] = Field(
        ...
    )
    object: Literal["event"] = Field(
        None
    )
    type_: Literal["batch.failed"] = Field(
        ..., alias="type"
    )

class WebhookEvalRunCanceled(BaseModel):
    """Sent when an eval run has been canceled."""
    model_config = ConfigDict(populate_by_name=True)

    created_at: int = Field(
        ...
    )
    id_: str = Field(
        ..., alias="id"
    )
    data: Dict[str, Any] = Field(
        ...
    )
    object: Literal["event"] = Field(
        None
    )
    type_: Literal["eval.run.canceled"] = Field(
        ..., alias="type"
    )

class WebhookEvalRunFailed(BaseModel):
    """Sent when an eval run has failed."""
    model_config = ConfigDict(populate_by_name=True)

    created_at: int = Field(
        ...
    )
    id_: str = Field(
        ..., alias="id"
    )
    data: Dict[str, Any] = Field(
        ...
    )
    object: Literal["event"] = Field(
        None
    )
    type_: Literal["eval.run.failed"] = Field(
        ..., alias="type"
    )

class WebhookEvalRunSucceeded(BaseModel):
    """Sent when an eval run has succeeded."""
    model_config = ConfigDict(populate_by_name=True)

    created_at: int = Field(
        ...
    )
    id_: str = Field(
        ..., alias="id"
    )
    data: Dict[str, Any] = Field(
        ...
    )
    object: Literal["event"] = Field(
        None
    )
    type_: Literal["eval.run.succeeded"] = Field(
        ..., alias="type"
    )

class WebhookFineTuningJobCancelled(BaseModel):
    """Sent when a fine-tuning job has been cancelled."""
    model_config = ConfigDict(populate_by_name=True)

    created_at: int = Field(
        ...
    )
    id_: str = Field(
        ..., alias="id"
    )
    data: Dict[str, Any] = Field(
        ...
    )
    object: Literal["event"] = Field(
        None
    )
    type_: Literal["fine_tuning.job.cancelled"] = Field(
        ..., alias="type"
    )

class WebhookFineTuningJobFailed(BaseModel):
    """Sent when a fine-tuning job has failed."""
    model_config = ConfigDict(populate_by_name=True)

    created_at: int = Field(
        ...
    )
    id_: str = Field(
        ..., alias="id"
    )
    data: Dict[str, Any] = Field(
        ...
    )
    object: Literal["event"] = Field(
        None
    )
    type_: Literal["fine_tuning.job.failed"] = Field(
        ..., alias="type"
    )

class WebhookFineTuningJobSucceeded(BaseModel):
    """Sent when a fine-tuning job has succeeded."""
    model_config = ConfigDict(populate_by_name=True)

    created_at: int = Field(
        ...
    )
    id_: str = Field(
        ..., alias="id"
    )
    data: Dict[str, Any] = Field(
        ...
    )
    object: Literal["event"] = Field(
        None
    )
    type_: Literal["fine_tuning.job.succeeded"] = Field(
        ..., alias="type"
    )

class WebhookRealtimeCallIncoming(BaseModel):
    """Sent when Realtime API Receives a incoming SIP call."""
    model_config = ConfigDict(populate_by_name=True)

    created_at: int = Field(
        ...
    )
    id_: str = Field(
        ..., alias="id"
    )
    data: Dict[str, Any] = Field(
        ...
    )
    object: Literal["event"] = Field(
        None
    )
    type_: Literal["realtime.call.incoming"] = Field(
        ..., alias="type"
    )

class WebhookResponseCancelled(BaseModel):
    """Sent when a background response has been cancelled."""
    model_config = ConfigDict(populate_by_name=True)

    created_at: int = Field(
        ...
    )
    id_: str = Field(
        ..., alias="id"
    )
    data: Dict[str, Any] = Field(
        ...
    )
    object: Literal["event"] = Field(
        None
    )
    type_: Literal["response.cancelled"] = Field(
        ..., alias="type"
    )

class WebhookResponseCompleted(BaseModel):
    """Sent when a background response has been completed."""
    model_config = ConfigDict(populate_by_name=True)

    created_at: int = Field(
        ...
    )
    id_: str = Field(
        ..., alias="id"
    )
    data: Dict[str, Any] = Field(
        ...
    )
    object: Literal["event"] = Field(
        None
    )
    type_: Literal["response.completed"] = Field(
        ..., alias="type"
    )

class WebhookResponseFailed(BaseModel):
    """Sent when a background response has failed."""
    model_config = ConfigDict(populate_by_name=True)

    created_at: int = Field(
        ...
    )
    id_: str = Field(
        ..., alias="id"
    )
    data: Dict[str, Any] = Field(
        ...
    )
    object: Literal["event"] = Field(
        None
    )
    type_: Literal["response.failed"] = Field(
        ..., alias="type"
    )

class WebhookResponseIncomplete(BaseModel):
    """Sent when a background response has been interrupted."""
    model_config = ConfigDict(populate_by_name=True)

    created_at: int = Field(
        ...
    )
    id_: str = Field(
        ..., alias="id"
    )
    data: Dict[str, Any] = Field(
        ...
    )
    object: Literal["event"] = Field(
        None
    )
    type_: Literal["response.incomplete"] = Field(
        ..., alias="type"
    )

class IncludeEnum(str, Enum):
    """Specify additional output data to include in the model response. Currently supported values are:
- `web_search_call.action.sources`: Include the sources of the web search tool call.
- `code_interpreter_call.outputs`: Includes the outputs of python code execution in code interpreter tool call items.
- `computer_call_output.output.image_url`: Include image urls from the computer call output.
- `file_search_call.results`: Include the search results of the file search tool call.
- `message.input_image.image_url`: Include image urls from the input message.
- `message.output_text.logprobs`: Include logprobs with assistant messages.
- `reasoning.encrypted_content`: Includes an encrypted version of reasoning tokens in reasoning item outputs. This enables reasoning items to be used in multi-turn conversations when using the Responses API statelessly (like when the `store` parameter is set to `false`, or when an organization is enrolled in the zero data retention program)."""
    FILE_SEARCH_CALL_RESULTS = "file_search_call.results"
    WEB_SEARCH_CALL_RESULTS = "web_search_call.results"
    WEB_SEARCH_CALL_ACTION_SOURCES = "web_search_call.action.sources"
    MESSAGE_INPUT_IMAGE_IMAGE_URL = "message.input_image.image_url"
    COMPUTER_CALL_OUTPUT_OUTPUT_IMAGE_URL = "computer_call_output.output.image_url"
    CODE_INTERPRETER_CALL_OUTPUTS = "code_interpreter_call.outputs"
    REASONING_ENCRYPTED_CONTENT = "reasoning.encrypted_content"
    MESSAGE_OUTPUT_TEXT_LOGPROBS = "message.output_text.logprobs"

class MessageStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    INCOMPLETE = "incomplete"

class MessageRole(str, Enum):
    UNKNOWN = "unknown"
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    CRITIC = "critic"
    DISCRIMINATOR = "discriminator"
    DEVELOPER = "developer"
    TOOL = "tool"

class InputTextContent(BaseModel):
    """A text input to the model."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["input_text"] = Field(
        ..., alias="type"
    )
    text: str = Field(
        ...
    )

class FileCitationBody(BaseModel):
    """A citation to a file."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["file_citation"] = Field(
        ..., alias="type"
    )
    file_id: str = Field(
        ...
    )
    index: int = Field(
        ...
    )
    filename: str = Field(
        ...
    )

class UrlCitationBody(BaseModel):
    """A citation for a web resource used to generate a model response."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["url_citation"] = Field(
        ..., alias="type"
    )
    url: str = Field(
        ...
    )
    start_index: int = Field(
        ...
    )
    end_index: int = Field(
        ...
    )
    title: str = Field(
        ...
    )

class ContainerFileCitationBody(BaseModel):
    """A citation for a container file used to generate a model response."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["container_file_citation"] = Field(
        ..., alias="type"
    )
    container_id: str = Field(
        ...
    )
    file_id: str = Field(
        ...
    )
    start_index: int = Field(
        ...
    )
    end_index: int = Field(
        ...
    )
    filename: str = Field(
        ...
    )

class Annotation(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class TopLogProb(BaseModel):
    """The top log probability of a token."""
    model_config = ConfigDict(populate_by_name=True)

    token: str = Field(
        ...
    )
    logprob: float = Field(
        ...
    )
    bytes: List[int] = Field(
        ...
    )

class LogProb(BaseModel):
    """The log probability of a token."""
    model_config = ConfigDict(populate_by_name=True)

    token: str = Field(
        ...
    )
    logprob: float = Field(
        ...
    )
    bytes: List[int] = Field(
        ...
    )
    top_logprobs: List[TopLogProbability] = Field(
        ...
    )

class OutputTextContent(BaseModel):
    """A text output from the model."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["output_text"] = Field(
        ..., alias="type"
    )
    text: str = Field(
        ...
    )
    annotations: List[Union[FileCitation, UrlCitation, ContainerFileCitation, FilePath]] = Field(
        ...
    )
    logprobs: List[LogProbability] = Field(
        None
    )

class TextContent(BaseModel):
    """A text content."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["text"] = Field(
        ..., alias="type"
    )
    text: str = Field(
        ...
    )

class SummaryTextContent(BaseModel):
    """A summary text from the model."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["summary_text"] = Field(
        ..., alias="type"
    )
    text: str = Field(
        ...
    )

class ReasoningTextContent(BaseModel):
    """Reasoning text from the model."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["reasoning_text"] = Field(
        ..., alias="type"
    )
    text: str = Field(
        ...
    )

class RefusalContent(BaseModel):
    """A refusal from the model."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["refusal"] = Field(
        ..., alias="type"
    )
    refusal: str = Field(
        ...
    )

class ImageDetail(str, Enum):
    LOW = "low"
    HIGH = "high"
    AUTO = "auto"

class InputImageContent(BaseModel):
    """An image input to the model. Learn about [image inputs](https://platform.openai.com/docs/guides/vision)."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["input_image"] = Field(
        ..., alias="type"
    )
    image_url: str = Field(
        None
    )
    file_id: str = Field(
        None
    )
    detail: Literal["low", "high", "auto"] = Field(
        ...
    )

class ComputerScreenshotContent(BaseModel):
    """A screenshot of a computer."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["computer_screenshot"] = Field(
        ..., alias="type"
    )
    image_url: str = Field(
        ...
    )
    file_id: str = Field(
        ...
    )

class InputFileContent(BaseModel):
    """A file input to the model."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["input_file"] = Field(
        ..., alias="type"
    )
    file_id: str = Field(
        None
    )
    filename: str = Field(
        None
    )
    file_url: str = Field(
        None
    )
    file_data: str = Field(
        None
    )

class Message(BaseModel):
    """A message to or from the model."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["message"] = Field(
        ..., alias="type"
    )
    id_: str = Field(
        ..., alias="id"
    )
    status: Literal["in_progress", "completed", "incomplete"] = Field(
        ...
    )
    role: Literal["unknown", "user", "assistant", "system", "critic", "discriminator", "developer", "tool"] = Field(
        ...
    )
    content: List[Union[InputText, OutputText, TextContent, SummaryText, ReasoningTextContent, Refusal, InputImage, ComputerScreenshot, InputFile]] = Field(
        ...
    )

class ClickButtonType(str, Enum):
    LEFT = "left"
    RIGHT = "right"
    WHEEL = "wheel"
    BACK = "back"
    FORWARD = "forward"

class ClickParam(BaseModel):
    """A click action."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["click"] = Field(
        ..., alias="type"
    )
    button: Literal["left", "right", "wheel", "back", "forward"] = Field(
        ...
    )
    x: int = Field(
        ...
    )
    y: int = Field(
        ...
    )

class DoubleClickAction(BaseModel):
    """A double click action."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["double_click"] = Field(
        ..., alias="type"
    )
    x: int = Field(
        ...
    )
    y: int = Field(
        ...
    )

class DragPoint(BaseModel):
    """An x/y coordinate pair, e.g. `{ x: 100, y: 200 }`."""
    model_config = ConfigDict(populate_by_name=True)

    x: int = Field(
        ...
    )
    y: int = Field(
        ...
    )

class KeyPressAction(BaseModel):
    """A collection of keypresses the model would like to perform."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["keypress"] = Field(
        ..., alias="type"
    )
    keys: List[str] = Field(
        ...
    )

class ComputerCallSafetyCheckParam(BaseModel):
    """A pending safety check for the computer call."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )
    code: str = Field(
        None
    )
    message: str = Field(
        None
    )

class CodeInterpreterOutputLogs(BaseModel):
    """The logs output from the code interpreter."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["logs"] = Field(
        ..., alias="type"
    )
    logs: str = Field(
        ...
    )

class CodeInterpreterOutputImage(BaseModel):
    """The image output from the code interpreter."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["image"] = Field(
        ..., alias="type"
    )
    url: str = Field(
        ...
    )

class LocalShellExecAction(BaseModel):
    """Execute a shell command on the server."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["exec"] = Field(
        ..., alias="type"
    )
    command: List[str] = Field(
        ...
    )
    timeout_ms: int = Field(
        None
    )
    working_directory: str = Field(
        None
    )
    env: Dict[str, str] = Field(
        ...
    )
    user: str = Field(
        None
    )

class FunctionShellAction(BaseModel):
    """Execute a shell command."""
    model_config = ConfigDict(populate_by_name=True)

    commands: List[str] = Field(
        ...
    )
    timeout_ms: int = Field(
        ...
    )
    max_output_length: int = Field(
        ...
    )

class LocalShellCallStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    INCOMPLETE = "incomplete"

class FunctionShellCall(BaseModel):
    """A tool call that executes one or more shell commands in a managed environment."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["shell_call"] = Field(
        ..., alias="type"
    )
    id_: str = Field(
        ..., alias="id"
    )
    call_id: str = Field(
        ...
    )
    action: ShellExecAction = Field(
        ...
    )
    status: Literal["in_progress", "completed", "incomplete"] = Field(
        ...
    )
    created_by: str = Field(
        None
    )

class FunctionShellCallOutputTimeoutOutcome(BaseModel):
    """Indicates that the shell call exceeded its configured time limit."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["timeout"] = Field(
        ..., alias="type"
    )

class FunctionShellCallOutputExitOutcome(BaseModel):
    """Indicates that the shell commands finished and returned an exit code."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["exit"] = Field(
        ..., alias="type"
    )
    exit_code: int = Field(
        ...
    )

class FunctionShellCallOutputContent(BaseModel):
    """The content of a shell call output."""
    model_config = ConfigDict(populate_by_name=True)

    stdout: str = Field(
        ...
    )
    stderr: str = Field(
        ...
    )
    outcome: Union[ShellCallTimeoutOutcome, ShellCallExitOutcome] = Field(
        ...
    )
    created_by: str = Field(
        None
    )

class FunctionShellCallOutput(BaseModel):
    """The output of a shell tool call."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["shell_call_output"] = Field(
        ..., alias="type"
    )
    id_: str = Field(
        ..., alias="id"
    )
    call_id: str = Field(
        ...
    )
    output: List[ShellCallOutputContent] = Field(
        ...
    )
    max_output_length: int = Field(
        ...
    )
    created_by: str = Field(
        None
    )

class ApplyPatchCallStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

class ApplyPatchCreateFileOperation(BaseModel):
    """Instruction describing how to create a file via the apply_patch tool."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["create_file"] = Field(
        ..., alias="type"
    )
    path: str = Field(
        ...
    )
    diff: str = Field(
        ...
    )

class ApplyPatchDeleteFileOperation(BaseModel):
    """Instruction describing how to delete a file via the apply_patch tool."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["delete_file"] = Field(
        ..., alias="type"
    )
    path: str = Field(
        ...
    )

class ApplyPatchUpdateFileOperation(BaseModel):
    """Instruction describing how to update a file via the apply_patch tool."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["update_file"] = Field(
        ..., alias="type"
    )
    path: str = Field(
        ...
    )
    diff: str = Field(
        ...
    )

class ApplyPatchToolCall(BaseModel):
    """A tool call that applies file diffs by creating, deleting, or updating files."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["apply_patch_call"] = Field(
        ..., alias="type"
    )
    id_: str = Field(
        ..., alias="id"
    )
    call_id: str = Field(
        ...
    )
    status: Literal["in_progress", "completed"] = Field(
        ...
    )
    operation: Union[ApplyPatchCreateFileOperation, ApplyPatchDeleteFileOperation, ApplyPatchUpdateFileOperation] = Field(
        ...
    )
    created_by: str = Field(
        None
    )

class ApplyPatchCallOutputStatus(str, Enum):
    COMPLETED = "completed"
    FAILED = "failed"

class ApplyPatchToolCallOutput(BaseModel):
    """The output emitted by an apply patch tool call."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["apply_patch_call_output"] = Field(
        ..., alias="type"
    )
    id_: str = Field(
        ..., alias="id"
    )
    call_id: str = Field(
        ...
    )
    status: Literal["completed", "failed"] = Field(
        ...
    )
    output: str = Field(
        None
    )
    created_by: str = Field(
        None
    )

class McpToolCallStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    INCOMPLETE = "incomplete"
    CALLING = "calling"
    FAILED = "failed"

class DetailEnum(str, Enum):
    LOW = "low"
    HIGH = "high"
    AUTO = "auto"

class FunctionCallItemStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    INCOMPLETE = "incomplete"

class ComputerCallOutputItemParam(BaseModel):
    """The output of a computer tool call."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        None, alias="id"
    )
    call_id: str = Field(
        ...
    )
    type_: Literal["computer_call_output"] = Field(
        ..., alias="type"
    )
    output: Dict[str, Any] = Field(
        ...
    )
    acknowledged_safety_checks: List[Dict[str, Any]] = Field(
        None
    )
    status: Literal["in_progress", "completed", "incomplete"] = Field(
        None
    )

class InputTextContentParam(BaseModel):
    """A text input to the model."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["input_text"] = Field(
        ..., alias="type"
    )
    text: str = Field(
        ...
    )

class InputImageContentParamAutoParam(BaseModel):
    """An image input to the model. Learn about [image inputs](https://platform.openai.com/docs/guides/vision)"""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["input_image"] = Field(
        ..., alias="type"
    )
    image_url: str = Field(
        None
    )
    file_id: str = Field(
        None
    )
    detail: Literal["low", "high", "auto"] = Field(
        None
    )

class InputFileContentParam(BaseModel):
    """A file input to the model."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["input_file"] = Field(
        ..., alias="type"
    )
    file_id: str = Field(
        None
    )
    filename: str = Field(
        None
    )
    file_data: str = Field(
        None
    )
    file_url: str = Field(
        None
    )

class FunctionCallOutputItemParam(BaseModel):
    """The output of a function tool call."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        None, alias="id"
    )
    call_id: str = Field(
        ...
    )
    type_: Literal["function_call_output"] = Field(
        ..., alias="type"
    )
    output: Union[str, List[Union[InputText, InputImage, InputFile]]] = Field(
        ...
    )
    status: Literal["in_progress", "completed", "incomplete"] = Field(
        None
    )

class CompactionSummaryItemParam(BaseModel):
    """A compaction item generated by the [`v1/responses/compact` API](https://platform.openai.com/docs/api-reference/responses/compact)."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        None, alias="id"
    )
    type_: Literal["compaction"] = Field(
        ..., alias="type"
    )
    encrypted_content: str = Field(
        ...
    )

class FunctionShellActionParam(BaseModel):
    """Commands and limits describing how to run the shell tool call."""
    model_config = ConfigDict(populate_by_name=True)

    commands: List[str] = Field(
        ...
    )
    timeout_ms: int = Field(
        None
    )
    max_output_length: int = Field(
        None
    )

class FunctionShellCallItemStatus(str, Enum):
    """Status values reported for shell tool calls."""
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    INCOMPLETE = "incomplete"

class FunctionShellCallItemParam(BaseModel):
    """A tool representing a request to execute one or more shell commands."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        None, alias="id"
    )
    call_id: str = Field(
        ...
    )
    type_: Literal["shell_call"] = Field(
        ..., alias="type"
    )
    action: ShellAction = Field(
        ...
    )
    status: Literal["in_progress", "completed", "incomplete"] = Field(
        None
    )

class FunctionShellCallOutputTimeoutOutcomeParam(BaseModel):
    """Indicates that the shell call exceeded its configured time limit."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["timeout"] = Field(
        ..., alias="type"
    )

class FunctionShellCallOutputExitOutcomeParam(BaseModel):
    """Indicates that the shell commands finished and returned an exit code."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["exit"] = Field(
        ..., alias="type"
    )
    exit_code: int = Field(
        ...
    )

class FunctionShellCallOutputOutcomeParam(BaseModel):
    """The exit or timeout outcome associated with this shell call."""
    model_config = ConfigDict(populate_by_name=True)

    pass

class FunctionShellCallOutputContentParam(BaseModel):
    """Captured stdout and stderr for a portion of a shell tool call output."""
    model_config = ConfigDict(populate_by_name=True)

    stdout: str = Field(
        ...
    )
    stderr: str = Field(
        ...
    )
    outcome: Union[ShellCallTimeoutOutcome, ShellCallExitOutcome] = Field(
        ...
    )

class FunctionShellCallOutputItemParam(BaseModel):
    """The streamed output items emitted by a shell tool call."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        None, alias="id"
    )
    call_id: str = Field(
        ...
    )
    type_: Literal["shell_call_output"] = Field(
        ..., alias="type"
    )
    output: List[ShellOutputContent] = Field(
        ...
    )
    max_output_length: int = Field(
        None
    )

class ApplyPatchCallStatusParam(str, Enum):
    """Status values reported for apply_patch tool calls."""
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

class ApplyPatchCreateFileOperationParam(BaseModel):
    """Instruction for creating a new file via the apply_patch tool."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["create_file"] = Field(
        ..., alias="type"
    )
    path: str = Field(
        ...
    )
    diff: str = Field(
        ...
    )

class ApplyPatchDeleteFileOperationParam(BaseModel):
    """Instruction for deleting an existing file via the apply_patch tool."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["delete_file"] = Field(
        ..., alias="type"
    )
    path: str = Field(
        ...
    )

class ApplyPatchUpdateFileOperationParam(BaseModel):
    """Instruction for updating an existing file via the apply_patch tool."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["update_file"] = Field(
        ..., alias="type"
    )
    path: str = Field(
        ...
    )
    diff: str = Field(
        ...
    )

class ApplyPatchOperationParam(BaseModel):
    """One of the create_file, delete_file, or update_file operations supplied to the apply_patch tool."""
    model_config = ConfigDict(populate_by_name=True)

    pass

class ApplyPatchToolCallItemParam(BaseModel):
    """A tool call representing a request to create, delete, or update files using diff patches."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["apply_patch_call"] = Field(
        ..., alias="type"
    )
    id_: str = Field(
        None, alias="id"
    )
    call_id: str = Field(
        ...
    )
    status: Literal["in_progress", "completed"] = Field(
        ...
    )
    operation: Union[ApplyPatchCreateFileOperation, ApplyPatchDeleteFileOperation, ApplyPatchUpdateFileOperation] = Field(
        ...
    )

class ApplyPatchCallOutputStatusParam(str, Enum):
    """Outcome values reported for apply_patch tool call outputs."""
    COMPLETED = "completed"
    FAILED = "failed"

class ApplyPatchToolCallOutputItemParam(BaseModel):
    """The streamed output emitted by an apply patch tool call."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["apply_patch_call_output"] = Field(
        ..., alias="type"
    )
    id_: str = Field(
        None, alias="id"
    )
    call_id: str = Field(
        ...
    )
    status: Literal["completed", "failed"] = Field(
        ...
    )
    output: str = Field(
        None
    )

class ItemReferenceParam(BaseModel):
    """An internal identifier for an item to reference."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["item_reference"] = Field(
        None, alias="type"
    )
    id_: str = Field(
        ..., alias="id"
    )

class ConversationResource(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )
    object: Literal["conversation"] = Field(
        ...
    )
    metadata: Any = Field(
        ...
    )
    created_at: int = Field(
        ...
    )

class FunctionTool(BaseModel):
    """Defines a function in your own code the model can choose to call. Learn more about [function calling](https://platform.openai.com/docs/guides/function-calling)."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["function"] = Field(
        ..., alias="type"
    )
    name: str = Field(
        ...
    )
    description: str = Field(
        None
    )
    parameters: Dict[str, Any] = Field(
        ...
    )
    strict: bool = Field(
        ...
    )

class RankerVersionType(str, Enum):
    AUTO = "auto"
    DEFAULT_2024_11_15 = "default-2024-11-15"

class HybridSearchOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    embedding_weight: float = Field(
        ...
    )
    text_weight: float = Field(
        ...
    )

class RankingOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    ranker: Literal["auto", "default-2024-11-15"] = Field(
        None
    )
    score_threshold: float = Field(
        None
    )
    hybrid_search: Dict[str, Any] = Field(
        None
    )

class Filters(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class FileSearchTool(BaseModel):
    """A tool that searches for relevant content from uploaded files. Learn more about the [file search tool](https://platform.openai.com/docs/guides/tools-file-search)."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["file_search"] = Field(
        ..., alias="type"
    )
    vector_store_ids: List[str] = Field(
        ...
    )
    max_num_results: int = Field(
        None
    )
    ranking_options: Dict[str, Any] = Field(
        None
    )
    filters: Union[ComparisonFilter, CompoundFilter] = Field(
        None
    )

class ComputerEnvironment(str, Enum):
    WINDOWS = "windows"
    MAC = "mac"
    LINUX = "linux"
    UBUNTU = "ubuntu"
    BROWSER = "browser"

class ComputerUsePreviewTool(BaseModel):
    """A tool that controls a virtual computer. Learn more about the [computer tool](https://platform.openai.com/docs/guides/tools-computer-use)."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["computer_use_preview"] = Field(
        ..., alias="type"
    )
    environment: Literal["windows", "mac", "linux", "ubuntu", "browser"] = Field(
        ...
    )
    display_width: int = Field(
        ...
    )
    display_height: int = Field(
        ...
    )

class ContainerMemoryLimit(str, Enum):
    _1G = "1g"
    _4G = "4g"
    _16G = "16g"
    _64G = "64g"

class InputFidelity(str, Enum):
    """Control how much effort the model will exert to match the style and features, especially facial features, of input images. This parameter is only supported for `gpt-image-1`. Unsupported for `gpt-image-1-mini`. Supports `high` and `low`. Defaults to `low`."""
    HIGH = "high"
    LOW = "low"

class LocalShellToolParam(BaseModel):
    """A tool that allows the model to execute shell commands in a local environment."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["local_shell"] = Field(
        ..., alias="type"
    )

class FunctionShellToolParam(BaseModel):
    """A tool that allows the model to execute shell commands."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["shell"] = Field(
        ..., alias="type"
    )

class CustomTextFormatParam(BaseModel):
    """Unconstrained free-form text."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["text"] = Field(
        ..., alias="type"
    )

class GrammarSyntax1(str, Enum):
    LARK = "lark"
    REGEX = "regex"

class CustomGrammarFormatParam(BaseModel):
    """A grammar defined by the user."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["grammar"] = Field(
        ..., alias="type"
    )
    syntax: Literal["lark", "regex"] = Field(
        ...
    )
    definition: str = Field(
        ...
    )

class CustomToolParam(BaseModel):
    """A custom tool that processes input using a specified format. Learn more about   [custom tools](https://platform.openai.com/docs/guides/function-calling#custom-tools)"""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["custom"] = Field(
        ..., alias="type"
    )
    name: str = Field(
        ...
    )
    description: str = Field(
        None
    )
    format: Union[TextFormat, GrammarFormat] = Field(
        None
    )

class ApproximateLocation(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["approximate"] = Field(
        ..., alias="type"
    )
    country: str = Field(
        None
    )
    region: str = Field(
        None
    )
    city: str = Field(
        None
    )
    timezone: str = Field(
        None
    )

class SearchContextSize(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class WebSearchPreviewTool(BaseModel):
    """This tool searches the web for relevant results to use in a response. Learn more about the [web search tool](https://platform.openai.com/docs/guides/tools-web-search)."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["web_search_preview", "web_search_preview_2025_03_11"] = Field(
        ..., alias="type"
    )
    user_location: Dict[str, Any] = Field(
        None
    )
    search_context_size: Literal["low", "medium", "high"] = Field(
        None
    )

class ApplyPatchToolParam(BaseModel):
    """Allows the assistant to create, delete, or update files using unified diffs."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["apply_patch"] = Field(
        ..., alias="type"
    )

class ImageGenOutputTokensDetails(BaseModel):
    """The output token details for the image generation."""
    model_config = ConfigDict(populate_by_name=True)

    image_tokens: int = Field(
        ...
    )
    text_tokens: int = Field(
        ...
    )

class ImageGenInputUsageDetails(BaseModel):
    """The input tokens detailed information for the image generation."""
    model_config = ConfigDict(populate_by_name=True)

    text_tokens: int = Field(
        ...
    )
    image_tokens: int = Field(
        ...
    )

class ImageGenUsage(BaseModel):
    """For `gpt-image-1` only, the token usage information for the image generation."""
    model_config = ConfigDict(populate_by_name=True)

    input_tokens: int = Field(
        ...
    )
    total_tokens: int = Field(
        ...
    )
    output_tokens: int = Field(
        ...
    )
    output_tokens_details: ImageGenerationOutputTokenDetails = Field(
        None
    )
    input_tokens_details: InputUsageDetails = Field(
        ...
    )

class SpecificApplyPatchParam(BaseModel):
    """Forces the model to call the apply_patch tool when executing a tool call."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["apply_patch"] = Field(
        ..., alias="type"
    )

class SpecificFunctionShellParam(BaseModel):
    """Forces the model to call the shell tool when a tool call is required."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["shell"] = Field(
        ..., alias="type"
    )

class ConversationParam2(BaseModel):
    """The conversation that this response belongs to."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )

class CompactionBody(BaseModel):
    """A compaction item generated by the [`v1/responses/compact` API](https://platform.openai.com/docs/api-reference/responses/compact)."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["compaction"] = Field(
        ..., alias="type"
    )
    id_: str = Field(
        ..., alias="id"
    )
    encrypted_content: str = Field(
        ...
    )
    created_by: str = Field(
        None
    )

class Conversation2(BaseModel):
    """The conversation that this response belongs to. Input items and output items from this response are automatically added to this conversation."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )

class CreateConversationBody(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    metadata: Dict[str, str] = Field(
        None
    )
    items: List[Union[InputMessage, Union[InputMessage, OutputMessage, FileSearchToolCall, ComputerToolCall, ComputerToolCallOutput, WebSearchToolCall, FunctionToolCall, FunctionToolCallOutput, Reasoning, CompactionItem, ImageGenerationCall, CodeInterpreterToolCall, LocalShellCall, LocalShellCallOutput, ShellToolCall, ShellToolCallOutput, ApplyPatchToolCall, ApplyPatchToolCallOutput, McpListTools, McpApprovalRequest, McpApprovalResponse, McpToolCall, CustomToolCallOutput, CustomToolCall], ItemReference]] = Field(
        None
    )

class UpdateConversationBody(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    metadata: Dict[str, str] = Field(
        ...
    )

class DeletedConversationResource(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["conversation.deleted"] = Field(
        ...
    )
    deleted: bool = Field(
        ...
    )
    id_: str = Field(
        ..., alias="id"
    )

class OrderEnum(str, Enum):
    ASC = "asc"
    DESC = "desc"

class VideoModel(str, Enum):
    SORA_2 = "sora-2"
    SORA_2_PRO = "sora-2-pro"
    SORA_2_2025_10_06 = "sora-2-2025-10-06"
    SORA_2_PRO_2025_10_06 = "sora-2-pro-2025-10-06"
    SORA_2_2025_12_08 = "sora-2-2025-12-08"

class VideoStatus(str, Enum):
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class VideoSize(str, Enum):
    _720X1280 = "720x1280"
    _1280X720 = "1280x720"
    _1024X1792 = "1024x1792"
    _1792X1024 = "1792x1024"

class VideoSeconds(str, Enum):
    _4 = "4"
    _8 = "8"
    _12 = "12"

class Error2(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    code: str = Field(
        ...
    )
    message: str = Field(
        ...
    )

class VideoResource(BaseModel):
    """Structured information describing a generated video job."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )
    object: Literal["video"] = Field(
        ...
    )
    model: Literal["sora-2", "sora-2-pro", "sora-2-2025-10-06", "sora-2-pro-2025-10-06", "sora-2-2025-12-08"] = Field(
        ...
    )
    status: Literal["queued", "in_progress", "completed", "failed"] = Field(
        ...
    )
    progress: int = Field(
        ...
    )
    created_at: int = Field(
        ...
    )
    completed_at: int = Field(
        ...
    )
    expires_at: int = Field(
        ...
    )
    prompt: str = Field(
        ...
    )
    size: Literal["720x1280", "1280x720", "1024x1792", "1792x1024"] = Field(
        ...
    )
    seconds: Literal["4", "8", "12"] = Field(
        ...
    )
    remixed_from_video_id: str = Field(
        ...
    )
    error: Dict[str, Any] = Field(
        ...
    )

class VideoListResource(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    object: Any = Field(
        ...
    )
    data: List[VideoJob] = Field(
        ...
    )
    first_id: str = Field(
        ...
    )
    last_id: str = Field(
        ...
    )
    has_more: bool = Field(
        ...
    )

class CreateVideoBody(BaseModel):
    """Parameters for creating a new video generation job."""
    model_config = ConfigDict(populate_by_name=True)

    model: Literal["sora-2", "sora-2-pro", "sora-2-2025-10-06", "sora-2-pro-2025-10-06", "sora-2-2025-12-08"] = Field(
        None
    )
    prompt: str = Field(
        ...
    )
    input_reference: bytes = Field(
        None
    )
    seconds: Literal["4", "8", "12"] = Field(
        None
    )
    size: Literal["720x1280", "1280x720", "1024x1792", "1792x1024"] = Field(
        None
    )

class DeletedVideoResource(BaseModel):
    """Confirmation payload returned after deleting a video."""
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["video.deleted"] = Field(
        ...
    )
    deleted: bool = Field(
        ...
    )
    id_: str = Field(
        ..., alias="id"
    )

class VideoContentVariant(str, Enum):
    VIDEO = "video"
    THUMBNAIL = "thumbnail"
    SPRITESHEET = "spritesheet"

class CreateVideoRemixBody(BaseModel):
    """Parameters for remixing an existing generated video."""
    model_config = ConfigDict(populate_by_name=True)

    prompt: str = Field(
        ...
    )

class TruncationEnum(str, Enum):
    AUTO = "auto"
    DISABLED = "disabled"

class TokenCountsBody(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    model: str = Field(
        None
    )
    input: Union[str, List[Union[InputMessage, Union[InputMessage, OutputMessage, FileSearchToolCall, ComputerToolCall, ComputerToolCallOutput, WebSearchToolCall, FunctionToolCall, FunctionToolCallOutput, Reasoning, CompactionItem, ImageGenerationCall, CodeInterpreterToolCall, LocalShellCall, LocalShellCallOutput, ShellToolCall, ShellToolCallOutput, ApplyPatchToolCall, ApplyPatchToolCallOutput, McpListTools, McpApprovalRequest, McpApprovalResponse, McpToolCall, CustomToolCallOutput, CustomToolCall], ItemReference]]] = Field(
        None
    )
    previous_response_id: str = Field(
        None
    )
    tools: List[Union[Function, FileSearch, ComputerUsePreview, WebSearch, McpTool, CodeInterpreter, ImageGenerationTool, LocalShellTool, ShellTool, CustomTool, WebSearchPreview, ApplyPatchTool]] = Field(
        None
    )
    text: Dict[str, Any] = Field(
        None
    )
    reasoning: Reasoning = Field(
        None
    )
    truncation: Literal["auto", "disabled"] = Field(
        None
    )
    instructions: str = Field(
        None
    )
    conversation: Union[str, ConversationObject] = Field(
        None
    )
    tool_choice: Union[Literal["none", "auto", "required"], AllowedTools, HostedTool, FunctionTool, McpTool, CustomTool, SpecificApplyPatchToolChoice, SpecificShellToolChoice] = Field(
        None
    )
    parallel_tool_calls: bool = Field(
        None
    )

class TokenCountsResource(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    object: Literal["response.input_tokens"] = Field(
        ...
    )
    input_tokens: int = Field(
        ...
    )

class CompactResponseMethodPublicBody(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    model: Union[Union[Union[str, Literal["gpt-5.2", "gpt-5.2-2025-12-11", "gpt-5.2-chat-latest", "gpt-5.2-pro", "gpt-5.2-pro-2025-12-11", "gpt-5.1", "gpt-5.1-2025-11-13", "gpt-5.1-codex", "gpt-5.1-mini", "gpt-5.1-chat-latest", "gpt-5", "gpt-5-mini", "gpt-5-nano", "gpt-5-2025-08-07", "gpt-5-mini-2025-08-07", "gpt-5-nano-2025-08-07", "gpt-5-chat-latest", "gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano", "gpt-4.1-2025-04-14", "gpt-4.1-mini-2025-04-14", "gpt-4.1-nano-2025-04-14", "o4-mini", "o4-mini-2025-04-16", "o3", "o3-2025-04-16", "o3-mini", "o3-mini-2025-01-31", "o1", "o1-2024-12-17", "o1-preview", "o1-preview-2024-09-12", "o1-mini", "o1-mini-2024-09-12", "gpt-4o", "gpt-4o-2024-11-20", "gpt-4o-2024-08-06", "gpt-4o-2024-05-13", "gpt-4o-audio-preview", "gpt-4o-audio-preview-2024-10-01", "gpt-4o-audio-preview-2024-12-17", "gpt-4o-audio-preview-2025-06-03", "gpt-4o-mini-audio-preview", "gpt-4o-mini-audio-preview-2024-12-17", "gpt-4o-search-preview", "gpt-4o-mini-search-preview", "gpt-4o-search-preview-2025-03-11", "gpt-4o-mini-search-preview-2025-03-11", "chatgpt-4o-latest", "codex-mini-latest", "gpt-4o-mini", "gpt-4o-mini-2024-07-18", "gpt-4-turbo", "gpt-4-turbo-2024-04-09", "gpt-4-0125-preview", "gpt-4-turbo-preview", "gpt-4-1106-preview", "gpt-4-vision-preview", "gpt-4", "gpt-4-0314", "gpt-4-0613", "gpt-4-32k", "gpt-4-32k-0314", "gpt-4-32k-0613", "gpt-3.5-turbo", "gpt-3.5-turbo-16k", "gpt-3.5-turbo-0301", "gpt-3.5-turbo-0613", "gpt-3.5-turbo-1106", "gpt-3.5-turbo-0125", "gpt-3.5-turbo-16k-0613"]], Literal["o1-pro", "o1-pro-2025-03-19", "o3-pro", "o3-pro-2025-06-10", "o3-deep-research", "o3-deep-research-2025-06-26", "o4-mini-deep-research", "o4-mini-deep-research-2025-06-26", "computer-use-preview", "computer-use-preview-2025-03-11", "gpt-5-codex", "gpt-5-pro", "gpt-5-pro-2025-10-06", "gpt-5.1-codex-max"]], str] = Field(
        ...
    )
    input: Union[str, List[Union[InputMessage, Union[InputMessage, OutputMessage, FileSearchToolCall, ComputerToolCall, ComputerToolCallOutput, WebSearchToolCall, FunctionToolCall, FunctionToolCallOutput, Reasoning, CompactionItem, ImageGenerationCall, CodeInterpreterToolCall, LocalShellCall, LocalShellCallOutput, ShellToolCall, ShellToolCallOutput, ApplyPatchToolCall, ApplyPatchToolCallOutput, McpListTools, McpApprovalRequest, McpApprovalResponse, McpToolCall, CustomToolCallOutput, CustomToolCall], ItemReference]]] = Field(
        None
    )
    previous_response_id: str = Field(
        None
    )
    instructions: str = Field(
        None
    )

class ItemField(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class CompactResource(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )
    object: Literal["response.compaction"] = Field(
        ...
    )
    output: List[Union[OutputMessage, FileSearchToolCall, FunctionToolCall, WebSearchToolCall, ComputerToolCall, Reasoning, CompactionItem, ImageGenerationCall, CodeInterpreterToolCall, LocalShellCall, ShellToolCall, ShellCallOutput, ApplyPatchToolCall, ApplyPatchToolCallOutput, McpToolCall, McpListTools, McpApprovalRequest, CustomToolCall]] = Field(
        ...
    )
    created_at: int = Field(
        ...
    )
    usage: Dict[str, Any] = Field(
        ...
    )

class ChatkitWorkflowTracing(BaseModel):
    """Controls diagnostic tracing during the session."""
    model_config = ConfigDict(populate_by_name=True)

    enabled: bool = Field(
        ...
    )

class ChatkitWorkflow(BaseModel):
    """Workflow metadata and state returned for the session."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )
    version: str = Field(
        ...
    )
    state_variables: Dict[str, Union[str, int, bool, float]] = Field(
        ...
    )
    tracing: TracingConfiguration = Field(
        ...
    )

class ChatSessionRateLimits(BaseModel):
    """Active per-minute request limit for the session."""
    model_config = ConfigDict(populate_by_name=True)

    max_requests_per_1_minute: int = Field(
        ...
    )

class ChatSessionStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

class ChatSessionAutomaticThreadTitling(BaseModel):
    """Automatic thread title preferences for the session."""
    model_config = ConfigDict(populate_by_name=True)

    enabled: bool = Field(
        ...
    )

class ChatSessionFileUpload(BaseModel):
    """Upload permissions and limits applied to the session."""
    model_config = ConfigDict(populate_by_name=True)

    enabled: bool = Field(
        ...
    )
    max_file_size: int = Field(
        ...
    )
    max_files: int = Field(
        ...
    )

class ChatSessionHistory(BaseModel):
    """History retention preferences returned for the session."""
    model_config = ConfigDict(populate_by_name=True)

    enabled: bool = Field(
        ...
    )
    recent_threads: int = Field(
        ...
    )

class ChatSessionChatkitConfiguration(BaseModel):
    """ChatKit configuration for the session."""
    model_config = ConfigDict(populate_by_name=True)

    automatic_thread_titling: AutomaticThreadTitling = Field(
        ...
    )
    file_upload: FileUploadSettings = Field(
        ...
    )
    history: HistorySettings = Field(
        ...
    )

class ChatSessionResource(BaseModel):
    """Represents a ChatKit session and its resolved configuration."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )
    object: Literal["chatkit.session"] = Field(
        ...
    )
    expires_at: int = Field(
        ...
    )
    client_secret: str = Field(
        ...
    )
    workflow: Workflow = Field(
        ...
    )
    user: str = Field(
        ...
    )
    rate_limits: RateLimits = Field(
        ...
    )
    max_requests_per_1_minute: int = Field(
        ...
    )
    status: Literal["active", "expired", "cancelled"] = Field(
        ...
    )
    chatkit_configuration: ChatKitConfiguration = Field(
        ...
    )

class WorkflowTracingParam(BaseModel):
    """Controls diagnostic tracing during the session."""
    model_config = ConfigDict(populate_by_name=True)

    enabled: bool = Field(
        None
    )

class WorkflowParam(BaseModel):
    """Workflow reference and overrides applied to the chat session."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )
    version: str = Field(
        None
    )
    state_variables: Dict[str, Union[str, int, bool, float]] = Field(
        None
    )
    tracing: TracingConfiguration = Field(
        None
    )

class ExpiresAfterParam(BaseModel):
    """Controls when the session expires relative to an anchor timestamp."""
    model_config = ConfigDict(populate_by_name=True)

    anchor: Literal["created_at"] = Field(
        ...
    )
    seconds: int = Field(
        ...
    )

class RateLimitsParam(BaseModel):
    """Controls request rate limits for the session."""
    model_config = ConfigDict(populate_by_name=True)

    max_requests_per_1_minute: int = Field(
        None
    )

class AutomaticThreadTitlingParam(BaseModel):
    """Controls whether ChatKit automatically generates thread titles."""
    model_config = ConfigDict(populate_by_name=True)

    enabled: bool = Field(
        None
    )

class FileUploadParam(BaseModel):
    """Controls whether users can upload files."""
    model_config = ConfigDict(populate_by_name=True)

    enabled: bool = Field(
        None
    )
    max_file_size: int = Field(
        None
    )
    max_files: int = Field(
        None
    )

class HistoryParam(BaseModel):
    """Controls how much historical context is retained for the session."""
    model_config = ConfigDict(populate_by_name=True)

    enabled: bool = Field(
        None
    )
    recent_threads: int = Field(
        None
    )

class ChatkitConfigurationParam(BaseModel):
    """Optional per-session configuration settings for ChatKit behavior."""
    model_config = ConfigDict(populate_by_name=True)

    automatic_thread_titling: AutomaticThreadTitlingConfiguration = Field(
        None
    )
    file_upload: FileUploadConfiguration = Field(
        None
    )
    history: ChatHistoryConfiguration = Field(
        None
    )

class CreateChatSessionBody(BaseModel):
    """Parameters for provisioning a new ChatKit session."""
    model_config = ConfigDict(populate_by_name=True)

    workflow: WorkflowSettings = Field(
        ...
    )
    user: str = Field(
        ...
    )
    expires_after: ExpirationOverrides = Field(
        None
    )
    rate_limits: RateLimitOverrides = Field(
        None
    )
    chatkit_configuration: ChatKitConfigurationOverrides = Field(
        None
    )

class UserMessageInputText(BaseModel):
    """Text block that a user contributed to the thread."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["input_text"] = Field(
        ..., alias="type"
    )
    text: str = Field(
        ...
    )

class UserMessageQuotedText(BaseModel):
    """Quoted snippet that the user referenced in their message."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["quoted_text"] = Field(
        ..., alias="type"
    )
    text: str = Field(
        ...
    )

class AttachmentType(str, Enum):
    IMAGE = "image"
    FILE = "file"

class Attachment(BaseModel):
    """Attachment metadata included on thread items."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["image", "file"] = Field(
        ..., alias="type"
    )
    id_: str = Field(
        ..., alias="id"
    )
    name: str = Field(
        ...
    )
    mime_type: str = Field(
        ...
    )
    preview_url: str = Field(
        ...
    )

class ToolChoice(BaseModel):
    """Tool selection that the assistant should honor when executing the item."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )

class InferenceOptions(BaseModel):
    """Model and tool overrides applied when generating the assistant response."""
    model_config = ConfigDict(populate_by_name=True)

    tool_choice: ToolChoice = Field(
        ...
    )
    model: str = Field(
        ...
    )

class UserMessageItem(BaseModel):
    """User-authored messages within a thread."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )
    object: Literal["chatkit.thread_item"] = Field(
        ...
    )
    created_at: int = Field(
        ...
    )
    thread_id: str = Field(
        ...
    )
    type_: Literal["chatkit.user_message"] = Field(
        ..., alias="type"
    )
    content: List[Union[UserMessageInput, UserMessageQuotedText]] = Field(
        ...
    )
    attachments: List[Attachment] = Field(
        ...
    )
    inference_options: InferenceOptions = Field(
        ...
    )

class FileAnnotationSource(BaseModel):
    """Attachment source referenced by an annotation."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["file"] = Field(
        ..., alias="type"
    )
    filename: str = Field(
        ...
    )

class FileAnnotation(BaseModel):
    """Annotation that references an uploaded file."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["file"] = Field(
        ..., alias="type"
    )
    source: FileAnnotationSource = Field(
        ...
    )

class UrlAnnotationSource(BaseModel):
    """URL backing an annotation entry."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["url"] = Field(
        ..., alias="type"
    )
    url: str = Field(
        ...
    )

class UrlAnnotation(BaseModel):
    """Annotation that references a URL."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["url"] = Field(
        ..., alias="type"
    )
    source: UrlAnnotationSource = Field(
        ...
    )

class ResponseOutputText(BaseModel):
    """Assistant response text accompanied by optional annotations."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["output_text"] = Field(
        ..., alias="type"
    )
    text: str = Field(
        ...
    )
    annotations: List[Union[FileAnnotation, UrlAnnotation]] = Field(
        ...
    )

class AssistantMessageItem(BaseModel):
    """Assistant-authored message within a thread."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )
    object: Literal["chatkit.thread_item"] = Field(
        ...
    )
    created_at: int = Field(
        ...
    )
    thread_id: str = Field(
        ...
    )
    type_: Literal["chatkit.assistant_message"] = Field(
        ..., alias="type"
    )
    content: List[AssistantMessageContent] = Field(
        ...
    )

class WidgetMessageItem(BaseModel):
    """Thread item that renders a widget payload."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )
    object: Literal["chatkit.thread_item"] = Field(
        ...
    )
    created_at: int = Field(
        ...
    )
    thread_id: str = Field(
        ...
    )
    type_: Literal["chatkit.widget"] = Field(
        ..., alias="type"
    )
    widget: str = Field(
        ...
    )

class ClientToolCallStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

class ClientToolCallItem(BaseModel):
    """Record of a client side tool invocation initiated by the assistant."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )
    object: Literal["chatkit.thread_item"] = Field(
        ...
    )
    created_at: int = Field(
        ...
    )
    thread_id: str = Field(
        ...
    )
    type_: Literal["chatkit.client_tool_call"] = Field(
        ..., alias="type"
    )
    status: Literal["in_progress", "completed"] = Field(
        ...
    )
    call_id: str = Field(
        ...
    )
    name: str = Field(
        ...
    )
    arguments: str = Field(
        ...
    )
    output: str = Field(
        ...
    )

class TaskType(str, Enum):
    CUSTOM = "custom"
    THOUGHT = "thought"

class TaskItem(BaseModel):
    """Task emitted by the workflow to show progress and status updates."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )
    object: Literal["chatkit.thread_item"] = Field(
        ...
    )
    created_at: int = Field(
        ...
    )
    thread_id: str = Field(
        ...
    )
    type_: Literal["chatkit.task"] = Field(
        ..., alias="type"
    )
    task_type: Literal["custom", "thought"] = Field(
        ...
    )
    heading: str = Field(
        ...
    )
    summary: str = Field(
        ...
    )

class TaskGroupTask(BaseModel):
    """Task entry that appears within a TaskGroup."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["custom", "thought"] = Field(
        ..., alias="type"
    )
    heading: str = Field(
        ...
    )
    summary: str = Field(
        ...
    )

class TaskGroupItem(BaseModel):
    """Collection of workflow tasks grouped together in the thread."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )
    object: Literal["chatkit.thread_item"] = Field(
        ...
    )
    created_at: int = Field(
        ...
    )
    thread_id: str = Field(
        ...
    )
    type_: Literal["chatkit.task_group"] = Field(
        ..., alias="type"
    )
    tasks: List[TaskGroupTask] = Field(
        ...
    )

class ThreadItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class ThreadItemListResource(BaseModel):
    """A paginated list of thread items rendered for the ChatKit API."""
    model_config = ConfigDict(populate_by_name=True)

    object: Any = Field(
        ...
    )
    data: List[Union[UserMessageItem, AssistantMessage, WidgetMessage, ClientToolCall, TaskItem, TaskGroup]] = Field(
        ...
    )
    first_id: str = Field(
        ...
    )
    last_id: str = Field(
        ...
    )
    has_more: bool = Field(
        ...
    )

class ActiveStatus(BaseModel):
    """Indicates that a thread is active."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["active"] = Field(
        ..., alias="type"
    )

class LockedStatus(BaseModel):
    """Indicates that a thread is locked and cannot accept new input."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["locked"] = Field(
        ..., alias="type"
    )
    reason: str = Field(
        ...
    )

class ClosedStatus(BaseModel):
    """Indicates that a thread has been closed."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["closed"] = Field(
        ..., alias="type"
    )
    reason: str = Field(
        ...
    )

class ThreadResource(BaseModel):
    """Represents a ChatKit thread and its current status."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )
    object: Literal["chatkit.thread"] = Field(
        ...
    )
    created_at: int = Field(
        ...
    )
    title: str = Field(
        ...
    )
    status: Union[ActiveThreadStatus, LockedThreadStatus, ClosedThreadStatus] = Field(
        ...
    )
    user: str = Field(
        ...
    )

class DeletedThreadResource(BaseModel):
    """Confirmation payload returned after deleting a thread."""
    model_config = ConfigDict(populate_by_name=True)

    id_: str = Field(
        ..., alias="id"
    )
    object: Literal["chatkit.thread.deleted"] = Field(
        ...
    )
    deleted: bool = Field(
        ...
    )

class ThreadListResource(BaseModel):
    """A paginated list of ChatKit threads."""
    model_config = ConfigDict(populate_by_name=True)

    object: Any = Field(
        ...
    )
    data: List[TheThreadObject] = Field(
        ...
    )
    first_id: str = Field(
        ...
    )
    last_id: str = Field(
        ...
    )
    has_more: bool = Field(
        ...
    )

class RealtimeConnectParams(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    model: str = Field(
        None
    )
    call_id: str = Field(
        None
    )

class ModerationImageUrlInput(BaseModel):
    """An object describing an image to classify."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["image_url"] = Field(
        ..., alias="type"
    )
    image_url: Dict[str, Any] = Field(
        ...
    )

class ModerationTextInput(BaseModel):
    """An object describing text to classify."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["text"] = Field(
        ..., alias="type"
    )
    text: str = Field(
        ...
    )

class ComparisonFilterValueItems(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class ChunkingStrategyResponse(BaseModel):
    """The strategy used to chunk the file."""
    model_config = ConfigDict(populate_by_name=True)

    pass

class FilePurpose(str, Enum):
    """The intended purpose of the uploaded file. One of: - `assistants`: Used in the Assistants API - `batch`: Used in the Batch API - `fine-tune`: Used for fine-tuning - `vision`: Images used for vision fine-tuning - `user_data`: Flexible file type for any purpose - `evals`: Used for eval data sets"""
    ASSISTANTS = "assistants"
    BATCH = "batch"
    FINE_TUNE = "fine-tune"
    VISION = "vision"
    USER_DATA = "user_data"
    EVALS = "evals"

class BatchError(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    code: str = Field(
        None
    )
    message: str = Field(
        None
    )
    param: str = Field(
        None
    )
    line: int = Field(
        None
    )

class BatchRequestCounts(BaseModel):
    """The request counts for different statuses within the batch."""
    model_config = ConfigDict(populate_by_name=True)

    total: int = Field(
        ...
    )
    completed: int = Field(
        ...
    )
    failed: int = Field(
        ...
    )

class AssistantTool(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class TextAnnotationDelta(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class TextAnnotation(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class RunStepDetailsToolCall(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class RunStepDeltaStepDetailsToolCall(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class MessageContent(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class MessageContentDelta(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass

class ChatModel(str, Enum):
    GPT_5_2 = "gpt-5.2"
    GPT_5_2_2025_12_11 = "gpt-5.2-2025-12-11"
    GPT_5_2_CHAT_LATEST = "gpt-5.2-chat-latest"
    GPT_5_2_PRO = "gpt-5.2-pro"
    GPT_5_2_PRO_2025_12_11 = "gpt-5.2-pro-2025-12-11"
    GPT_5_1 = "gpt-5.1"
    GPT_5_1_2025_11_13 = "gpt-5.1-2025-11-13"
    GPT_5_1_CODEX = "gpt-5.1-codex"
    GPT_5_1_MINI = "gpt-5.1-mini"
    GPT_5_1_CHAT_LATEST = "gpt-5.1-chat-latest"
    GPT_5 = "gpt-5"
    GPT_5_MINI = "gpt-5-mini"
    GPT_5_NANO = "gpt-5-nano"
    GPT_5_2025_08_07 = "gpt-5-2025-08-07"
    GPT_5_MINI_2025_08_07 = "gpt-5-mini-2025-08-07"
    GPT_5_NANO_2025_08_07 = "gpt-5-nano-2025-08-07"
    GPT_5_CHAT_LATEST = "gpt-5-chat-latest"
    GPT_4_1 = "gpt-4.1"
    GPT_4_1_MINI = "gpt-4.1-mini"
    GPT_4_1_NANO = "gpt-4.1-nano"
    GPT_4_1_2025_04_14 = "gpt-4.1-2025-04-14"
    GPT_4_1_MINI_2025_04_14 = "gpt-4.1-mini-2025-04-14"
    GPT_4_1_NANO_2025_04_14 = "gpt-4.1-nano-2025-04-14"
    O4_MINI = "o4-mini"
    O4_MINI_2025_04_16 = "o4-mini-2025-04-16"
    O3 = "o3"
    O3_2025_04_16 = "o3-2025-04-16"
    O3_MINI = "o3-mini"
    O3_MINI_2025_01_31 = "o3-mini-2025-01-31"
    O1 = "o1"
    O1_2024_12_17 = "o1-2024-12-17"
    O1_PREVIEW = "o1-preview"
    O1_PREVIEW_2024_09_12 = "o1-preview-2024-09-12"
    O1_MINI = "o1-mini"
    O1_MINI_2024_09_12 = "o1-mini-2024-09-12"
    GPT_4O = "gpt-4o"
    GPT_4O_2024_11_20 = "gpt-4o-2024-11-20"
    GPT_4O_2024_08_06 = "gpt-4o-2024-08-06"
    GPT_4O_2024_05_13 = "gpt-4o-2024-05-13"
    GPT_4O_AUDIO_PREVIEW = "gpt-4o-audio-preview"
    GPT_4O_AUDIO_PREVIEW_2024_10_01 = "gpt-4o-audio-preview-2024-10-01"
    GPT_4O_AUDIO_PREVIEW_2024_12_17 = "gpt-4o-audio-preview-2024-12-17"
    GPT_4O_AUDIO_PREVIEW_2025_06_03 = "gpt-4o-audio-preview-2025-06-03"
    GPT_4O_MINI_AUDIO_PREVIEW = "gpt-4o-mini-audio-preview"
    GPT_4O_MINI_AUDIO_PREVIEW_2024_12_17 = "gpt-4o-mini-audio-preview-2024-12-17"
    GPT_4O_SEARCH_PREVIEW = "gpt-4o-search-preview"
    GPT_4O_MINI_SEARCH_PREVIEW = "gpt-4o-mini-search-preview"
    GPT_4O_SEARCH_PREVIEW_2025_03_11 = "gpt-4o-search-preview-2025-03-11"
    GPT_4O_MINI_SEARCH_PREVIEW_2025_03_11 = "gpt-4o-mini-search-preview-2025-03-11"
    CHATGPT_4O_LATEST = "chatgpt-4o-latest"
    CODEX_MINI_LATEST = "codex-mini-latest"
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_4O_MINI_2024_07_18 = "gpt-4o-mini-2024-07-18"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_4_TURBO_2024_04_09 = "gpt-4-turbo-2024-04-09"
    GPT_4_0125_PREVIEW = "gpt-4-0125-preview"
    GPT_4_TURBO_PREVIEW = "gpt-4-turbo-preview"
    GPT_4_1106_PREVIEW = "gpt-4-1106-preview"
    GPT_4_VISION_PREVIEW = "gpt-4-vision-preview"
    GPT_4 = "gpt-4"
    GPT_4_0314 = "gpt-4-0314"
    GPT_4_0613 = "gpt-4-0613"
    GPT_4_32K = "gpt-4-32k"
    GPT_4_32K_0314 = "gpt-4-32k-0314"
    GPT_4_32K_0613 = "gpt-4-32k-0613"
    GPT_3_5_TURBO = "gpt-3.5-turbo"
    GPT_3_5_TURBO_16K = "gpt-3.5-turbo-16k"
    GPT_3_5_TURBO_0301 = "gpt-3.5-turbo-0301"
    GPT_3_5_TURBO_0613 = "gpt-3.5-turbo-0613"
    GPT_3_5_TURBO_1106 = "gpt-3.5-turbo-1106"
    GPT_3_5_TURBO_0125 = "gpt-3.5-turbo-0125"
    GPT_3_5_TURBO_16K_0613 = "gpt-3.5-turbo-16k-0613"

class Summary(BaseModel):
    """A summary text from the model."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["summary_text"] = Field(
        ..., alias="type"
    )
    text: str = Field(
        ...
    )

class CreateThreadAndRunRequestWithoutStream(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    assistant_id: str = Field(
        ...
    )
    thread: Dict[str, Any] = Field(
        None
    )
    model: Union[str, Literal["gpt-5", "gpt-5-mini", "gpt-5-nano", "gpt-5-2025-08-07", "gpt-5-mini-2025-08-07", "gpt-5-nano-2025-08-07", "gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano", "gpt-4.1-2025-04-14", "gpt-4.1-mini-2025-04-14", "gpt-4.1-nano-2025-04-14", "gpt-4o", "gpt-4o-2024-11-20", "gpt-4o-2024-08-06", "gpt-4o-2024-05-13", "gpt-4o-mini", "gpt-4o-mini-2024-07-18", "gpt-4.5-preview", "gpt-4.5-preview-2025-02-27", "gpt-4-turbo", "gpt-4-turbo-2024-04-09", "gpt-4-0125-preview", "gpt-4-turbo-preview", "gpt-4-1106-preview", "gpt-4-vision-preview", "gpt-4", "gpt-4-0314", "gpt-4-0613", "gpt-4-32k", "gpt-4-32k-0314", "gpt-4-32k-0613", "gpt-3.5-turbo", "gpt-3.5-turbo-16k", "gpt-3.5-turbo-0613", "gpt-3.5-turbo-1106", "gpt-3.5-turbo-0125", "gpt-3.5-turbo-16k-0613"]] = Field(
        None
    )
    instructions: Optional[str] = Field(
        None
    )
    tools: Optional[List[Union[CodeInterpreterTool, FileSearchTool, FunctionTool]]] = Field(
        None
    )
    tool_resources: Optional[Dict[str, Any]] = Field(
        None
    )
    metadata: Dict[str, str] = Field(
        None
    )
    temperature: Optional[float] = Field(
        None
    )
    top_p: Optional[float] = Field(
        None
    )
    max_prompt_tokens: Optional[int] = Field(
        None
    )
    max_completion_tokens: Optional[int] = Field(
        None
    )
    truncation_strategy: ThreadTruncationControls = Field(
        None
    )
    tool_choice: Union[Literal["none", "auto", "required"], Dict[str, Any]] = Field(
        None
    )
    parallel_tool_calls: bool = Field(
        None
    )
    response_format: Union[Literal["auto"], Text, JsonObject, JsonSchema] = Field(
        None
    )

class CreateRunRequestWithoutStream(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    assistant_id: str = Field(
        ...
    )
    model: Union[str, Literal["gpt-5", "gpt-5-mini", "gpt-5-nano", "gpt-5-2025-08-07", "gpt-5-mini-2025-08-07", "gpt-5-nano-2025-08-07", "gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano", "gpt-4.1-2025-04-14", "gpt-4.1-mini-2025-04-14", "gpt-4.1-nano-2025-04-14", "o3-mini", "o3-mini-2025-01-31", "o1", "o1-2024-12-17", "gpt-4o", "gpt-4o-2024-11-20", "gpt-4o-2024-08-06", "gpt-4o-2024-05-13", "gpt-4o-mini", "gpt-4o-mini-2024-07-18", "gpt-4.5-preview", "gpt-4.5-preview-2025-02-27", "gpt-4-turbo", "gpt-4-turbo-2024-04-09", "gpt-4-0125-preview", "gpt-4-turbo-preview", "gpt-4-1106-preview", "gpt-4-vision-preview", "gpt-4", "gpt-4-0314", "gpt-4-0613", "gpt-4-32k", "gpt-4-32k-0314", "gpt-4-32k-0613", "gpt-3.5-turbo", "gpt-3.5-turbo-16k", "gpt-3.5-turbo-0613", "gpt-3.5-turbo-1106", "gpt-3.5-turbo-0125", "gpt-3.5-turbo-16k-0613"]] = Field(
        None
    )
    reasoning_effort: Literal["none", "minimal", "low", "medium", "high", "xhigh"] = Field(
        None
    )
    instructions: Optional[str] = Field(
        None
    )
    additional_instructions: Optional[str] = Field(
        None
    )
    additional_messages: Optional[List[Dict[str, Any]]] = Field(
        None
    )
    tools: Optional[List[Union[CodeInterpreterTool, FileSearchTool, FunctionTool]]] = Field(
        None
    )
    metadata: Dict[str, str] = Field(
        None
    )
    temperature: Optional[float] = Field(
        None
    )
    top_p: Optional[float] = Field(
        None
    )
    max_prompt_tokens: Optional[int] = Field(
        None
    )
    max_completion_tokens: Optional[int] = Field(
        None
    )
    truncation_strategy: ThreadTruncationControls = Field(
        None
    )
    tool_choice: Union[Literal["none", "auto", "required"], Dict[str, Any]] = Field(
        None
    )
    parallel_tool_calls: bool = Field(
        None
    )
    response_format: Union[Literal["auto"], Text, JsonObject, JsonSchema] = Field(
        None
    )

class SubmitToolOutputsRunRequestWithoutStream(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    tool_outputs: List[Dict[str, Any]] = Field(
        ...
    )

class RunStatus(str, Enum):
    """The status of the run, which can be either `queued`, `in_progress`, `requires_action`, `cancelling`, `cancelled`, `failed`, `completed`, `incomplete`, or `expired`."""
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    REQUIRES_ACTION = "requires_action"
    CANCELLING = "cancelling"
    CANCELLED = "cancelled"
    FAILED = "failed"
    COMPLETED = "completed"
    INCOMPLETE = "incomplete"
    EXPIRED = "expired"

class RunStepDeltaObjectDelta(BaseModel):
    """The delta containing the fields that have changed on the run step."""
    model_config = ConfigDict(populate_by_name=True)

    step_details: Union[MessageCreation, ToolCalls] = Field(
        None
    )

class CodeInterpreterContainerAuto(BaseModel):
    """Configuration for a code interpreter container. Optionally specify the IDs of the files to run the code on."""
    model_config = ConfigDict(populate_by_name=True)

    type_: Literal["auto"] = Field(
        ..., alias="type"
    )
    file_ids: List[str] = Field(
        None
    )
    memory_limit: Literal["1g", "4g", "16g", "64g"] = Field(
        None
    )
