"""
Layer 0 Agent: Environment-based client wrapper for openai
Automatically loads credentials from environment variables for easy integration
with AI Agent frameworks (LangChain, CrewAI, Madison, etc.)
"""
import os
from typing import Any, Dict, List, Literal, Optional, Union
from .raw import *


class RawAgent:
    """
    Agent-ready wrapper for openai raw API client.

    Automatically loads credentials from environment variables:
    - OPENAI_API_KEY: API key/token for authentication
    - OPENAI_BASE_URL: Base URL for the API (optional, has default)

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
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.base_url = base_url or os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")

        if not self.api_key:
            raise ValueError(
                "API key is required. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter."
            )

        # Initialize raw client(s)
        self._assistants = AssistantsClient(
            base_url=self.base_url,
            token=self.api_key
        )
        self._audio = AudioClient(
            base_url=self.base_url,
            token=self.api_key
        )
        self._batch = BatchClient(
            base_url=self.base_url,
            token=self.api_key
        )
        self._chat = ChatClient(
            base_url=self.base_url,
            token=self.api_key
        )
        self._completions = CompletionsClient(
            base_url=self.base_url,
            token=self.api_key
        )
        self._default = DefaultClient(
            base_url=self.base_url,
            token=self.api_key
        )
        self._conversations = ConversationsClient(
            base_url=self.base_url,
            token=self.api_key
        )
        self._embeddings = EmbeddingsClient(
            base_url=self.base_url,
            token=self.api_key
        )
        self._evals = EvalsClient(
            base_url=self.base_url,
            token=self.api_key
        )
        self._files = FilesClient(
            base_url=self.base_url,
            token=self.api_key
        )
        self._fine_tuning = FineTuningClient(
            base_url=self.base_url,
            token=self.api_key
        )
        self._images = ImagesClient(
            base_url=self.base_url,
            token=self.api_key
        )
        self._models = ModelsClient(
            base_url=self.base_url,
            token=self.api_key
        )
        self._moderations = ModerationsClient(
            base_url=self.base_url,
            token=self.api_key
        )
        self._audit_logs = AuditLogsClient(
            base_url=self.base_url,
            token=self.api_key
        )
        self._certificates = CertificatesClient(
            base_url=self.base_url,
            token=self.api_key
        )
        self._usage = UsageClient(
            base_url=self.base_url,
            token=self.api_key
        )
        self._groups = GroupsClient(
            base_url=self.base_url,
            token=self.api_key
        )
        self._group_organization_role_assignments = GroupOrganizationRoleAssignmentsClient(
            base_url=self.base_url,
            token=self.api_key
        )
        self._group_users = GroupUsersClient(
            base_url=self.base_url,
            token=self.api_key
        )
        self._invites = InvitesClient(
            base_url=self.base_url,
            token=self.api_key
        )
        self._projects = ProjectsClient(
            base_url=self.base_url,
            token=self.api_key
        )
        self._project_groups = ProjectGroupsClient(
            base_url=self.base_url,
            token=self.api_key
        )
        self._roles = RolesClient(
            base_url=self.base_url,
            token=self.api_key
        )
        self._users = UsersClient(
            base_url=self.base_url,
            token=self.api_key
        )
        self._user_organization_role_assignments = UserOrganizationRoleAssignmentsClient(
            base_url=self.base_url,
            token=self.api_key
        )
        self._project_group_role_assignments = ProjectGroupRoleAssignmentsClient(
            base_url=self.base_url,
            token=self.api_key
        )
        self._project_user_role_assignments = ProjectUserRoleAssignmentsClient(
            base_url=self.base_url,
            token=self.api_key
        )
        self._realtime = RealtimeClient(
            base_url=self.base_url,
            token=self.api_key
        )
        self._responses = ResponsesClient(
            base_url=self.base_url,
            token=self.api_key
        )
        self._uploads = UploadsClient(
            base_url=self.base_url,
            token=self.api_key
        )
        self._vector_stores = VectorStoresClient(
            base_url=self.base_url,
            token=self.api_key
        )
        self._videos = VideosClient(
            base_url=self.base_url,
            token=self.api_key
        )

    # ─────────────────────────────────────────────────────────────────────────────
    # Assistants operations
    # ─────────────────────────────────────────────────────────────────────────────

    async def list_assistants(self, limit: int = None, order: Literal["asc", "desc"] = None, after: str = None, before: str = None) -> Dict[str, Any]:
        """Returns a list of assistants."""
        return await self._assistants.list_assistants(limit=limit, order=order, after=after, before=before)

    async def create_assistant(self, body: Dict[str, Any]) -> Assistant:
        """Create an assistant with a model and instructions."""
        return await self._assistants.create_assistant(body=body)

    async def get_assistant(self, assistant_id: str) -> Assistant:
        """Retrieves an assistant."""
        return await self._assistants.get_assistant(assistant_id=assistant_id)

    async def modify_assistant(self, assistant_id: str, body: Dict[str, Any]) -> Assistant:
        """Modifies an assistant."""
        return await self._assistants.modify_assistant(assistant_id=assistant_id, body=body)

    async def delete_assistant(self, assistant_id: str) -> Dict[str, Any]:
        """Delete an assistant."""
        return await self._assistants.delete_assistant(assistant_id=assistant_id)

    async def create_thread(self, body: Dict[str, Any]) -> Thread:
        """Create a thread."""
        return await self._assistants.create_thread(body=body)

    async def create_thread_and_run(self, body: Dict[str, Any]) -> ARunOnAThread:
        """Create a thread and run it in one request."""
        return await self._assistants.create_thread_and_run(body=body)

    async def get_thread(self, thread_id: str) -> Thread:
        """Retrieves a thread."""
        return await self._assistants.get_thread(thread_id=thread_id)

    async def modify_thread(self, thread_id: str, body: Dict[str, Any]) -> Thread:
        """Modifies a thread."""
        return await self._assistants.modify_thread(thread_id=thread_id, body=body)

    async def delete_thread(self, thread_id: str) -> Dict[str, Any]:
        """Delete a thread."""
        return await self._assistants.delete_thread(thread_id=thread_id)

    async def list_messages(self, thread_id: str, limit: int = None, order: Literal["asc", "desc"] = None, after: str = None, before: str = None, run_id: str = None) -> Any:
        """Returns a list of messages for a given thread."""
        return await self._assistants.list_messages(thread_id=thread_id, limit=limit, order=order, after=after, before=before, run_id=run_id)

    async def create_message(self, thread_id: str, body: Dict[str, Any]) -> TheMessageObject:
        """Create a message."""
        return await self._assistants.create_message(thread_id=thread_id, body=body)

    async def get_message(self, thread_id: str, message_id: str) -> TheMessageObject:
        """Retrieve a message."""
        return await self._assistants.get_message(thread_id=thread_id, message_id=message_id)

    async def modify_message(self, thread_id: str, message_id: str, body: Dict[str, Any]) -> TheMessageObject:
        """Modifies a message."""
        return await self._assistants.modify_message(thread_id=thread_id, message_id=message_id, body=body)

    async def delete_message(self, thread_id: str, message_id: str) -> Dict[str, Any]:
        """Deletes a message."""
        return await self._assistants.delete_message(thread_id=thread_id, message_id=message_id)

    async def list_runs(self, thread_id: str, limit: int = None, order: Literal["asc", "desc"] = None, after: str = None, before: str = None) -> Dict[str, Any]:
        """Returns a list of runs belonging to a thread."""
        return await self._assistants.list_runs(thread_id=thread_id, limit=limit, order=order, after=after, before=before)

    async def create_run(self, thread_id: str, body: Dict[str, Any], include: List[Literal["step_details.tool_calls[*].file_search.results[*].content"]] = None) -> ARunOnAThread:
        """Create a run."""
        return await self._assistants.create_run(thread_id=thread_id, include=include, body=body)

    async def get_run(self, thread_id: str, run_id: str) -> ARunOnAThread:
        """Retrieves a run."""
        return await self._assistants.get_run(thread_id=thread_id, run_id=run_id)

    async def modify_run(self, thread_id: str, run_id: str, body: Dict[str, Any]) -> ARunOnAThread:
        """Modifies a run."""
        return await self._assistants.modify_run(thread_id=thread_id, run_id=run_id, body=body)

    async def cancel_run(self, thread_id: str, run_id: str) -> ARunOnAThread:
        """Cancels a run that is `in_progress`."""
        return await self._assistants.cancel_run(thread_id=thread_id, run_id=run_id)

    async def list_run_steps(self, thread_id: str, run_id: str, limit: int = None, order: Literal["asc", "desc"] = None, after: str = None, before: str = None, include: List[Literal["step_details.tool_calls[*].file_search.results[*].content"]] = None) -> Any:
        """Returns a list of run steps belonging to a run."""
        return await self._assistants.list_run_steps(thread_id=thread_id, run_id=run_id, limit=limit, order=order, after=after, before=before, include=include)

    async def get_run_step(self, thread_id: str, run_id: str, step_id: str, include: List[Literal["step_details.tool_calls[*].file_search.results[*].content"]] = None) -> RunSteps:
        """Retrieves a run step."""
        return await self._assistants.get_run_step(thread_id=thread_id, run_id=run_id, step_id=step_id, include=include)

    async def submit_tool_ouputs_to_run(self, thread_id: str, run_id: str, body: Dict[str, Any]) -> ARunOnAThread:
        """When a run has the `status: "requires_action"` and `required_action.type` is `submit_tool_outputs`, this endpoint can be used to submit the outputs from the tool calls once they're all completed. All outputs must be submitted in a single request."""
        return await self._assistants.submit_tool_ouputs_to_run(thread_id=thread_id, run_id=run_id, body=body)

    # ─────────────────────────────────────────────────────────────────────────────
    # Audio operations
    # ─────────────────────────────────────────────────────────────────────────────

    async def create_speech(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Generates audio from the input text."""
        return await self._audio.create_speech(body=body)

    async def create_transcription(self) -> Union[Dict[str, Any]]:
        """Transcribes audio into the input language."""
        return await self._audio.create_transcription()

    async def create_translation(self) -> Union[Dict[str, Any]]:
        """Translates audio into English."""
        return await self._audio.create_translation()

    async def list_voice_consents(self, after: str = None, limit: int = None) -> Dict[str, Any]:
        """Returns a list of voice consent recordings."""
        return await self._audio.list_voice_consents(after=after, limit=limit)

    async def create_voice_consent(self) -> VoiceConsent:
        """Upload a voice consent recording."""
        return await self._audio.create_voice_consent()

    async def get_voice_consent(self, consent_id: str) -> VoiceConsent:
        """Retrieves a voice consent recording."""
        return await self._audio.get_voice_consent(consent_id=consent_id)

    async def update_voice_consent(self, consent_id: str, body: Dict[str, Any]) -> VoiceConsent:
        """Updates a voice consent recording (metadata only)."""
        return await self._audio.update_voice_consent(consent_id=consent_id, body=body)

    async def delete_voice_consent(self, consent_id: str) -> Dict[str, Any]:
        """Deletes a voice consent recording."""
        return await self._audio.delete_voice_consent(consent_id=consent_id)

    async def create_voice(self) -> Voice:
        """Creates a custom voice."""
        return await self._audio.create_voice()

    # ─────────────────────────────────────────────────────────────────────────────
    # Batch operations
    # ─────────────────────────────────────────────────────────────────────────────

    async def list_batches(self, after: str = None, limit: int = None) -> Dict[str, Any]:
        """List your organization's batches."""
        return await self._batch.list_batches(after=after, limit=limit)

    async def create_batch(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Creates and executes a batch from an uploaded file of requests"""
        return await self._batch.create_batch(body=body)

    async def retrieve_batch(self, batch_id: str) -> Dict[str, Any]:
        """Retrieves a batch."""
        return await self._batch.retrieve_batch(batch_id=batch_id)

    async def cancel_batch(self, batch_id: str) -> Dict[str, Any]:
        """Cancels an in-progress batch. The batch will be in status `cancelling` for up to 10 minutes, before changing to `cancelled`, where it will have partial results (if any) available in the output file."""
        return await self._batch.cancel_batch(batch_id=batch_id)

    # ─────────────────────────────────────────────────────────────────────────────
    # Chat operations
    # ─────────────────────────────────────────────────────────────────────────────

    async def list_chat_completions(self, model: str = None, metadata: Dict[str, str] = None, after: str = None, limit: int = None, order: Literal["asc", "desc"] = None) -> ChatCompletionList:
        """List stored Chat Completions. Only Chat Completions that have been stored
with the `store` parameter set to `true` will be returned."""
        return await self._chat.list_chat_completions(model=model, metadata=metadata, after=after, limit=limit, order=order)

    async def create_chat_completion(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """**Starting a new project?** We recommend trying [Responses](https://platform.openai.com/docs/api-reference/responses) 
to take advantage of the latest OpenAI platform features. Compare
[Chat Completions with Responses](https://platform.openai.com/docs/guides/responses-vs-chat-completions?api-mode=responses).

---

Creates a model response for the given chat conversation. Learn more in the
[text generation](https://platform.openai.com/docs/guides/text-generation), [vision](https://platform.openai.com/docs/guides/vision),
and [audio](https://platform.openai.com/docs/guides/audio) guides.

Parameter support can differ depending on the model used to generate the
response, particularly for newer reasoning models. Parameters that are only
supported for reasoning models are noted below. For the current state of 
unsupported parameters in reasoning models, 
[refer to the reasoning guide](https://platform.openai.com/docs/guides/reasoning)."""
        return await self._chat.create_chat_completion(body=body)

    async def get_chat_completion(self, completion_id: str) -> Dict[str, Any]:
        """Get a stored chat completion. Only Chat Completions that have been created
with the `store` parameter set to `true` will be returned."""
        return await self._chat.get_chat_completion(completion_id=completion_id)

    async def update_chat_completion(self, completion_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """Modify a stored chat completion. Only Chat Completions that have been
created with the `store` parameter set to `true` can be modified. Currently,
the only supported modification is to update the `metadata` field."""
        return await self._chat.update_chat_completion(completion_id=completion_id, body=body)

    async def delete_chat_completion(self, completion_id: str) -> Dict[str, Any]:
        """Delete a stored chat completion. Only Chat Completions that have been
created with the `store` parameter set to `true` can be deleted."""
        return await self._chat.delete_chat_completion(completion_id=completion_id)

    async def get_chat_completion_messages(self, completion_id: str, after: str = None, limit: int = None, order: Literal["asc", "desc"] = None) -> ChatCompletionMessageList:
        """Get the messages in a stored chat completion. Only Chat Completions that
have been created with the `store` parameter set to `true` will be
returned."""
        return await self._chat.get_chat_completion_messages(completion_id=completion_id, after=after, limit=limit, order=order)

    # ─────────────────────────────────────────────────────────────────────────────
    # Completions operations
    # ─────────────────────────────────────────────────────────────────────────────

    async def create_completion(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Creates a completion for the provided prompt and parameters."""
        return await self._completions.create_completion(body=body)

    # ─────────────────────────────────────────────────────────────────────────────
    # Default operations
    # ─────────────────────────────────────────────────────────────────────────────

    async def list_containers(self, limit: int = None, order: Literal["asc", "desc"] = None, after: str = None) -> Dict[str, Any]:
        """List Containers"""
        return await self._default.list_containers(limit=limit, order=order, after=after)

    async def create_container(self, body: Dict[str, Any]) -> TheContainerObject:
        """Create Container"""
        return await self._default.create_container(body=body)

    async def retrieve_container(self, container_id: str) -> TheContainerObject:
        """Retrieve Container"""
        return await self._default.retrieve_container(container_id=container_id)

    async def delete_container(self, container_id: str) -> Dict[str, Any]:
        """Delete Container"""
        return await self._default.delete_container(container_id=container_id)

    async def list_container_files(self, container_id: str, limit: int = None, order: Literal["asc", "desc"] = None, after: str = None) -> Dict[str, Any]:
        """List Container files"""
        return await self._default.list_container_files(container_id=container_id, limit=limit, order=order, after=after)

    async def create_container_file(self, container_id: str) -> TheContainerFileObject:
        """Create a Container File

You can send either a multipart/form-data request with the raw file content, or a JSON request with a file ID."""
        return await self._default.create_container_file(container_id=container_id)

    async def retrieve_container_file(self, container_id: str, file_id: str) -> TheContainerFileObject:
        """Retrieve Container File"""
        return await self._default.retrieve_container_file(container_id=container_id, file_id=file_id)

    async def delete_container_file(self, container_id: str, file_id: str) -> Dict[str, Any]:
        """Delete Container File"""
        return await self._default.delete_container_file(container_id=container_id, file_id=file_id)

    async def retrieve_container_file_content(self, container_id: str, file_id: str) -> Dict[str, Any]:
        """Retrieve Container File Content"""
        return await self._default.retrieve_container_file_content(container_id=container_id, file_id=file_id)

    async def admin_api_keys_list(self, after: Optional[str] = None, order: Literal["asc", "desc"] = None, limit: int = None) -> Dict[str, Any]:
        """List organization API keys"""
        return await self._default.admin_api_keys_list(after=after, order=order, limit=limit)

    async def admin_api_keys_create(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Create an organization admin API key"""
        return await self._default.admin_api_keys_create(body=body)

    async def admin_api_keys_get(self, key_id: str) -> Dict[str, Any]:
        """Retrieve a single organization API key"""
        return await self._default.admin_api_keys_get(key_id=key_id)

    async def admin_api_keys_delete(self, key_id: str) -> Dict[str, Any]:
        """Delete an organization admin API key"""
        return await self._default.admin_api_keys_delete(key_id=key_id)

    async def getinputtokencounts(self, body: Dict[str, Any]) -> TokenCounts:
        """Get input token counts"""
        return await self._default.getinputtokencounts(body=body)

    async def compactconversation(self, body: Dict[str, Any]) -> TheCompactedResponseObject:
        """Compact conversation"""
        return await self._default.compactconversation(body=body)

    async def cancel_chat_session_method(self, session_id: str) -> TheChatSessionObject:
        """Cancel a ChatKit session"""
        return await self._default.cancel_chat_session_method(session_id=session_id)

    async def create_chat_session_method(self, body: CreateChatSessionRequest) -> TheChatSessionObject:
        """Create a ChatKit session"""
        return await self._default.create_chat_session_method(body=body)

    async def list_thread_items_method(self, thread_id: str, limit: int = None, order: Literal["asc", "desc"] = None, after: str = None, before: str = None) -> ThreadItems:
        """List ChatKit thread items"""
        return await self._default.list_thread_items_method(thread_id=thread_id, limit=limit, order=order, after=after, before=before)

    async def get_thread_method(self, thread_id: str) -> TheThreadObject:
        """Retrieve a ChatKit thread"""
        return await self._default.get_thread_method(thread_id=thread_id)

    async def delete_thread_method(self, thread_id: str) -> DeletedThread:
        """Delete a ChatKit thread"""
        return await self._default.delete_thread_method(thread_id=thread_id)

    async def list_threads_method(self, limit: int = None, order: Literal["asc", "desc"] = None, after: str = None, before: str = None, user: str = None) -> Threads:
        """List ChatKit threads"""
        return await self._default.list_threads_method(limit=limit, order=order, after=after, before=before, user=user)

    # ─────────────────────────────────────────────────────────────────────────────
    # Conversations operations
    # ─────────────────────────────────────────────────────────────────────────────

    async def list_conversation_items(self, conversation_id: str, limit: int = None, order: Literal["asc", "desc"] = None, after: str = None, include: List[Literal["file_search_call.results", "web_search_call.results", "web_search_call.action.sources", "message.input_image.image_url", "computer_call_output.output.image_url", "code_interpreter_call.outputs", "reasoning.encrypted_content", "message.output_text.logprobs"]] = None) -> TheConversationItemList:
        """List all items for a conversation with the given ID."""
        return await self._conversations.list_conversation_items(conversation_id=conversation_id, limit=limit, order=order, after=after, include=include)

    async def create_conversation_items(self, conversation_id: str, body: Any, include: List[Literal["file_search_call.results", "web_search_call.results", "web_search_call.action.sources", "message.input_image.image_url", "computer_call_output.output.image_url", "code_interpreter_call.outputs", "reasoning.encrypted_content", "message.output_text.logprobs"]] = None) -> TheConversationItemList:
        """Create items in a conversation with the given ID."""
        return await self._conversations.create_conversation_items(conversation_id=conversation_id, include=include, body=body)

    async def get_conversation_item(self, conversation_id: str, item_id: str, include: List[Literal["file_search_call.results", "web_search_call.results", "web_search_call.action.sources", "message.input_image.image_url", "computer_call_output.output.image_url", "code_interpreter_call.outputs", "reasoning.encrypted_content", "message.output_text.logprobs"]] = None) -> Union[Message, FunctionToolCall, FunctionToolCallOutput, FileSearchToolCall, WebSearchToolCall, ImageGenerationCall, ComputerToolCall, ComputerToolCallOutput, Reasoning, CodeInterpreterToolCall, LocalShellCall, LocalShellCallOutput, ShellToolCall, ShellCallOutput, ApplyPatchToolCall, ApplyPatchToolCallOutput, McpListTools, McpApprovalRequest, McpApprovalResponse, McpToolCall, CustomToolCall, CustomToolCallOutput]:
        """Get a single item from a conversation with the given IDs."""
        return await self._conversations.get_conversation_item(conversation_id=conversation_id, item_id=item_id, include=include)

    async def delete_conversation_item(self, conversation_id: str, item_id: str) -> Dict[str, Any]:
        """Delete an item from a conversation with the given IDs."""
        return await self._conversations.delete_conversation_item(conversation_id=conversation_id, item_id=item_id)

    async def create_conversation(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Create a conversation."""
        return await self._conversations.create_conversation(body=body)

    async def get_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """Get a conversation"""
        return await self._conversations.get_conversation(conversation_id=conversation_id)

    async def update_conversation(self, conversation_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """Update a conversation"""
        return await self._conversations.update_conversation(conversation_id=conversation_id, body=body)

    async def delete_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """Delete a conversation. Items in the conversation will not be deleted."""
        return await self._conversations.delete_conversation(conversation_id=conversation_id)

    # ─────────────────────────────────────────────────────────────────────────────
    # Embeddings operations
    # ─────────────────────────────────────────────────────────────────────────────

    async def create_embedding(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Creates an embedding vector representing the input text."""
        return await self._embeddings.create_embedding(body=body)

    # ─────────────────────────────────────────────────────────────────────────────
    # Evals operations
    # ─────────────────────────────────────────────────────────────────────────────

    async def list_evals(self, after: str = None, limit: int = None, order: Literal["asc", "desc"] = None, order_by: Literal["created_at", "updated_at"] = None) -> EvalList:
        """List evaluations for a project."""
        return await self._evals.list_evals(after=after, limit=limit, order=order, order_by=order_by)

    async def create_eval(self, body: CreateEvalRequest) -> Eval:
        """Create the structure of an evaluation that can be used to test a model's performance.
An evaluation is a set of testing criteria and the config for a data source, which dictates the schema of the data used in the evaluation. After creating an evaluation, you can run it on different models and model parameters. We support several types of graders and datasources.
For more information, see the [Evals guide](https://platform.openai.com/docs/guides/evals)."""
        return await self._evals.create_eval(body=body)

    async def get_eval(self, eval_id: str) -> Eval:
        """Get an evaluation by ID."""
        return await self._evals.get_eval(eval_id=eval_id)

    async def update_eval(self, eval_id: str, body: Dict[str, Any]) -> Eval:
        """Update certain properties of an evaluation."""
        return await self._evals.update_eval(eval_id=eval_id, body=body)

    async def delete_eval(self, eval_id: str) -> Dict[str, Any]:
        """Delete an evaluation."""
        return await self._evals.delete_eval(eval_id=eval_id)

    async def get_eval_runs(self, eval_id: str, after: str = None, limit: int = None, order: Literal["asc", "desc"] = None, status: Literal["queued", "in_progress", "completed", "canceled", "failed"] = None) -> EvalRunList:
        """Get a list of runs for an evaluation."""
        return await self._evals.get_eval_runs(eval_id=eval_id, after=after, limit=limit, order=order, status=status)

    async def create_eval_run(self, eval_id: str, body: CreateEvalRunRequest) -> EvalRun:
        """Kicks off a new run for a given evaluation, specifying the data source, and what model configuration to use to test. The datasource will be validated against the schema specified in the config of the evaluation."""
        return await self._evals.create_eval_run(eval_id=eval_id, body=body)

    async def get_eval_run(self, eval_id: str, run_id: str) -> EvalRun:
        """Get an evaluation run by ID."""
        return await self._evals.get_eval_run(eval_id=eval_id, run_id=run_id)

    async def cancel_eval_run(self, eval_id: str, run_id: str) -> EvalRun:
        """Cancel an ongoing evaluation run."""
        return await self._evals.cancel_eval_run(eval_id=eval_id, run_id=run_id)

    async def delete_eval_run(self, eval_id: str, run_id: str) -> Dict[str, Any]:
        """Delete an eval run."""
        return await self._evals.delete_eval_run(eval_id=eval_id, run_id=run_id)

    async def get_eval_run_output_items(self, eval_id: str, run_id: str, after: str = None, limit: int = None, status: Literal["fail", "pass"] = None, order: Literal["asc", "desc"] = None) -> EvalRunOutputItemList:
        """Get a list of output items for an evaluation run."""
        return await self._evals.get_eval_run_output_items(eval_id=eval_id, run_id=run_id, after=after, limit=limit, status=status, order=order)

    async def get_eval_run_output_item(self, eval_id: str, run_id: str, output_item_id: str) -> EvalRunOutputItem:
        """Get an evaluation run output item by ID."""
        return await self._evals.get_eval_run_output_item(eval_id=eval_id, run_id=run_id, output_item_id=output_item_id)

    # ─────────────────────────────────────────────────────────────────────────────
    # Files operations
    # ─────────────────────────────────────────────────────────────────────────────

    async def list_files(self, purpose: str = None, limit: int = None, order: Literal["asc", "desc"] = None, after: str = None) -> Dict[str, Any]:
        """Returns a list of files."""
        return await self._files.list_files(purpose=purpose, limit=limit, order=order, after=after)

    async def create_file(self) -> Any:
        """Upload a file that can be used across various endpoints. Individual files
can be up to 512 MB, and the size of all files uploaded by one organization
can be up to 1 TB.

- The Assistants API supports files up to 2 million tokens and of specific
  file types. See the [Assistants Tools guide](https://platform.openai.com/docs/assistants/tools) for
  details.
- The Fine-tuning API only supports `.jsonl` files. The input also has
  certain required formats for fine-tuning
  [chat](https://platform.openai.com/docs/api-reference/fine-tuning/chat-input) or
  [completions](https://platform.openai.com/docs/api-reference/fine-tuning/completions-input) models.
- The Batch API only supports `.jsonl` files up to 200 MB in size. The input
  also has a specific required
  [format](https://platform.openai.com/docs/api-reference/batch/request-input).

Please [contact us](https://help.openai.com/) if you need to increase these
storage limits."""
        return await self._files.create_file()

    async def retrieve_file(self, file_id: str) -> Any:
        """Returns information about a specific file."""
        return await self._files.retrieve_file(file_id=file_id)

    async def delete_file(self, file_id: str) -> Dict[str, Any]:
        """Delete a file and remove it from all vector stores."""
        return await self._files.delete_file(file_id=file_id)

    async def download_file(self, file_id: str) -> str:
        """Returns the contents of the specified file."""
        return await self._files.download_file(file_id=file_id)

    # ─────────────────────────────────────────────────────────────────────────────
    # Fine-tuning operations
    # ─────────────────────────────────────────────────────────────────────────────

    async def run_grader(self, body: RunGraderRequest) -> Dict[str, Any]:
        """Run a grader."""
        return await self._fine_tuning.run_grader(body=body)

    async def validate_grader(self, body: ValidateGraderRequest) -> ValidateGraderResponse:
        """Validate a grader."""
        return await self._fine_tuning.validate_grader(body=body)

    async def list_fine_tuning_checkpoint_permissions(self, fine_tuned_model_checkpoint: str, project_id: str = None, after: str = None, limit: int = None, order: Literal["ascending", "descending"] = None) -> Dict[str, Any]:
        """**NOTE:** This endpoint requires an [admin API key](../admin-api-keys).

Organization owners can use this endpoint to view all permissions for a fine-tuned model checkpoint."""
        return await self._fine_tuning.list_fine_tuning_checkpoint_permissions(fine_tuned_model_checkpoint=fine_tuned_model_checkpoint, project_id=project_id, after=after, limit=limit, order=order)

    async def create_fine_tuning_checkpoint_permission(self, fine_tuned_model_checkpoint: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """**NOTE:** Calling this endpoint requires an [admin API key](../admin-api-keys).

This enables organization owners to share fine-tuned models with other projects in their organization."""
        return await self._fine_tuning.create_fine_tuning_checkpoint_permission(fine_tuned_model_checkpoint=fine_tuned_model_checkpoint, body=body)

    async def delete_fine_tuning_checkpoint_permission(self, fine_tuned_model_checkpoint: str, permission_id: str) -> Dict[str, Any]:
        """**NOTE:** This endpoint requires an [admin API key](../admin-api-keys).

Organization owners can use this endpoint to delete a permission for a fine-tuned model checkpoint."""
        return await self._fine_tuning.delete_fine_tuning_checkpoint_permission(fine_tuned_model_checkpoint=fine_tuned_model_checkpoint, permission_id=permission_id)

    async def list_paginated_fine_tuning_jobs(self, after: str = None, limit: int = None, metadata: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """List your organization's fine-tuning jobs"""
        return await self._fine_tuning.list_paginated_fine_tuning_jobs(after=after, limit=limit, metadata=metadata)

    async def create_fine_tuning_job(self, body: Dict[str, Any]) -> FineTuningJob:
        """Creates a fine-tuning job which begins the process of creating a new model from a given dataset.

Response includes details of the enqueued job including job status and the name of the fine-tuned models once complete.

[Learn more about fine-tuning](https://platform.openai.com/docs/guides/model-optimization)"""
        return await self._fine_tuning.create_fine_tuning_job(body=body)

    async def retrieve_fine_tuning_job(self, fine_tuning_job_id: str) -> FineTuningJob:
        """Get info about a fine-tuning job.

[Learn more about fine-tuning](https://platform.openai.com/docs/guides/model-optimization)"""
        return await self._fine_tuning.retrieve_fine_tuning_job(fine_tuning_job_id=fine_tuning_job_id)

    async def cancel_fine_tuning_job(self, fine_tuning_job_id: str) -> FineTuningJob:
        """Immediately cancel a fine-tune job."""
        return await self._fine_tuning.cancel_fine_tuning_job(fine_tuning_job_id=fine_tuning_job_id)

    async def list_fine_tuning_job_checkpoints(self, fine_tuning_job_id: str, after: str = None, limit: int = None) -> Dict[str, Any]:
        """List checkpoints for a fine-tuning job."""
        return await self._fine_tuning.list_fine_tuning_job_checkpoints(fine_tuning_job_id=fine_tuning_job_id, after=after, limit=limit)

    async def list_fine_tuning_events(self, fine_tuning_job_id: str, after: str = None, limit: int = None) -> Dict[str, Any]:
        """Get status updates for a fine-tuning job."""
        return await self._fine_tuning.list_fine_tuning_events(fine_tuning_job_id=fine_tuning_job_id, after=after, limit=limit)

    async def pause_fine_tuning_job(self, fine_tuning_job_id: str) -> FineTuningJob:
        """Pause a fine-tune job."""
        return await self._fine_tuning.pause_fine_tuning_job(fine_tuning_job_id=fine_tuning_job_id)

    async def resume_fine_tuning_job(self, fine_tuning_job_id: str) -> FineTuningJob:
        """Resume a fine-tune job."""
        return await self._fine_tuning.resume_fine_tuning_job(fine_tuning_job_id=fine_tuning_job_id)

    # ─────────────────────────────────────────────────────────────────────────────
    # Images operations
    # ─────────────────────────────────────────────────────────────────────────────

    async def create_image_edit(self) -> ImageGenerationResponse:
        """Creates an edited or extended image given one or more source images and a prompt. This endpoint only supports `gpt-image-1` and `dall-e-2`."""
        return await self._images.create_image_edit()

    async def create_image(self, body: Dict[str, Any]) -> ImageGenerationResponse:
        """Creates an image given a prompt. [Learn more](https://platform.openai.com/docs/guides/images)."""
        return await self._images.create_image(body=body)

    async def create_image_variation(self) -> ImageGenerationResponse:
        """Creates a variation of a given image. This endpoint only supports `dall-e-2`."""
        return await self._images.create_image_variation()

    # ─────────────────────────────────────────────────────────────────────────────
    # Models operations
    # ─────────────────────────────────────────────────────────────────────────────

    async def list_models(self) -> Dict[str, Any]:
        """Lists the currently available models, and provides basic information about each one such as the owner and availability."""
        return await self._models.list_models()

    async def retrieve_model(self, model: str) -> Any:
        """Retrieves a model instance, providing basic information about the model such as the owner and permissioning."""
        return await self._models.retrieve_model(model=model)

    async def delete_model(self, model: str) -> Dict[str, Any]:
        """Delete a fine-tuned model. You must have the Owner role in your organization to delete a model."""
        return await self._models.delete_model(model=model)

    # ─────────────────────────────────────────────────────────────────────────────
    # Moderations operations
    # ─────────────────────────────────────────────────────────────────────────────

    async def create_moderation(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Classifies if text and/or image inputs are potentially harmful. Learn
more in the [moderation guide](https://platform.openai.com/docs/guides/moderation)."""
        return await self._moderations.create_moderation(body=body)

    # ─────────────────────────────────────────────────────────────────────────────
    # Audit Logs operations
    # ─────────────────────────────────────────────────────────────────────────────

    async def list_audit_logs(self, effective_at: Dict[str, Any] = None, project_ids: List[str] = None, event_types: List[Literal["api_key.created", "api_key.updated", "api_key.deleted", "certificate.created", "certificate.updated", "certificate.deleted", "certificates.activated", "certificates.deactivated", "checkpoint.permission.created", "checkpoint.permission.deleted", "external_key.registered", "external_key.removed", "group.created", "group.updated", "group.deleted", "invite.sent", "invite.accepted", "invite.deleted", "ip_allowlist.created", "ip_allowlist.updated", "ip_allowlist.deleted", "ip_allowlist.config.activated", "ip_allowlist.config.deactivated", "login.succeeded", "login.failed", "logout.succeeded", "logout.failed", "organization.updated", "project.created", "project.updated", "project.archived", "project.deleted", "rate_limit.updated", "rate_limit.deleted", "resource.deleted", "tunnel.created", "tunnel.updated", "tunnel.deleted", "role.created", "role.updated", "role.deleted", "role.assignment.created", "role.assignment.deleted", "scim.enabled", "scim.disabled", "service_account.created", "service_account.updated", "service_account.deleted", "user.added", "user.updated", "user.deleted"]] = None, actor_ids: List[str] = None, actor_emails: List[str] = None, resource_ids: List[str] = None, limit: int = None, after: str = None, before: str = None) -> Dict[str, Any]:
        """List user actions and configuration changes within this organization."""
        return await self._audit_logs.list_audit_logs(effective_at=effective_at, project_ids=project_ids, event_types=event_types, actor_ids=actor_ids, actor_emails=actor_emails, resource_ids=resource_ids, limit=limit, after=after, before=before)

    # ─────────────────────────────────────────────────────────────────────────────
    # Certificates operations
    # ─────────────────────────────────────────────────────────────────────────────

    async def list_organization_certificates(self, limit: int = None, after: str = None, order: Literal["asc", "desc"] = None) -> Dict[str, Any]:
        """List uploaded certificates for this organization."""
        return await self._certificates.list_organization_certificates(limit=limit, after=after, order=order)

    async def upload_certificate(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Upload a certificate to the organization. This does **not** automatically activate the certificate.

Organizations can upload up to 50 certificates."""
        return await self._certificates.upload_certificate(body=body)

    async def activate_organization_certificates(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Activate certificates at the organization level.

You can atomically and idempotently activate up to 10 certificates at a time."""
        return await self._certificates.activate_organization_certificates(body=body)

    async def deactivate_organization_certificates(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Deactivate certificates at the organization level.

You can atomically and idempotently deactivate up to 10 certificates at a time."""
        return await self._certificates.deactivate_organization_certificates(body=body)

    async def get_certificate(self, certificate_id: str, include: List[Literal["content"]] = None) -> Dict[str, Any]:
        """Get a certificate that has been uploaded to the organization.

You can get a certificate regardless of whether it is active or not."""
        return await self._certificates.get_certificate(certificate_id=certificate_id, include=include)

    async def modify_certificate(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Modify a certificate. Note that only the name can be modified."""
        return await self._certificates.modify_certificate(body=body)

    async def delete_certificate(self) -> Dict[str, Any]:
        """Delete a certificate from the organization.

The certificate must be inactive for the organization and all projects."""
        return await self._certificates.delete_certificate()

    async def list_project_certificates(self, project_id: str, limit: int = None, after: str = None, order: Literal["asc", "desc"] = None) -> Dict[str, Any]:
        """List certificates for this project."""
        return await self._certificates.list_project_certificates(project_id=project_id, limit=limit, after=after, order=order)

    async def activate_project_certificates(self, project_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """Activate certificates at the project level.

You can atomically and idempotently activate up to 10 certificates at a time."""
        return await self._certificates.activate_project_certificates(project_id=project_id, body=body)

    async def deactivate_project_certificates(self, project_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """Deactivate certificates at the project level. You can atomically and 
idempotently deactivate up to 10 certificates at a time."""
        return await self._certificates.deactivate_project_certificates(project_id=project_id, body=body)

    # ─────────────────────────────────────────────────────────────────────────────
    # Usage operations
    # ─────────────────────────────────────────────────────────────────────────────

    async def usage_costs(self, start_time: int = None, end_time: int = None, bucket_width: Literal["1d"] = None, project_ids: List[str] = None, group_by: List[Literal["project_id", "line_item"]] = None, limit: int = None, page: str = None) -> Dict[str, Any]:
        """Get costs details for the organization."""
        return await self._usage.usage_costs(start_time=start_time, end_time=end_time, bucket_width=bucket_width, project_ids=project_ids, group_by=group_by, limit=limit, page=page)

    async def usage_audio_speeches(self, start_time: int = None, end_time: int = None, bucket_width: Literal["1m", "1h", "1d"] = None, project_ids: List[str] = None, user_ids: List[str] = None, api_key_ids: List[str] = None, models: List[str] = None, group_by: List[Literal["project_id", "user_id", "api_key_id", "model"]] = None, limit: int = None, page: str = None) -> Dict[str, Any]:
        """Get audio speeches usage details for the organization."""
        return await self._usage.usage_audio_speeches(start_time=start_time, end_time=end_time, bucket_width=bucket_width, project_ids=project_ids, user_ids=user_ids, api_key_ids=api_key_ids, models=models, group_by=group_by, limit=limit, page=page)

    async def usage_audio_transcriptions(self, start_time: int = None, end_time: int = None, bucket_width: Literal["1m", "1h", "1d"] = None, project_ids: List[str] = None, user_ids: List[str] = None, api_key_ids: List[str] = None, models: List[str] = None, group_by: List[Literal["project_id", "user_id", "api_key_id", "model"]] = None, limit: int = None, page: str = None) -> Dict[str, Any]:
        """Get audio transcriptions usage details for the organization."""
        return await self._usage.usage_audio_transcriptions(start_time=start_time, end_time=end_time, bucket_width=bucket_width, project_ids=project_ids, user_ids=user_ids, api_key_ids=api_key_ids, models=models, group_by=group_by, limit=limit, page=page)

    async def usage_code_interpreter_sessions(self, start_time: int = None, end_time: int = None, bucket_width: Literal["1m", "1h", "1d"] = None, project_ids: List[str] = None, group_by: List[Literal["project_id"]] = None, limit: int = None, page: str = None) -> Dict[str, Any]:
        """Get code interpreter sessions usage details for the organization."""
        return await self._usage.usage_code_interpreter_sessions(start_time=start_time, end_time=end_time, bucket_width=bucket_width, project_ids=project_ids, group_by=group_by, limit=limit, page=page)

    async def usage_completions(self, start_time: int = None, end_time: int = None, bucket_width: Literal["1m", "1h", "1d"] = None, project_ids: List[str] = None, user_ids: List[str] = None, api_key_ids: List[str] = None, models: List[str] = None, batch: bool = None, group_by: List[Literal["project_id", "user_id", "api_key_id", "model", "batch", "service_tier"]] = None, limit: int = None, page: str = None) -> Dict[str, Any]:
        """Get completions usage details for the organization."""
        return await self._usage.usage_completions(start_time=start_time, end_time=end_time, bucket_width=bucket_width, project_ids=project_ids, user_ids=user_ids, api_key_ids=api_key_ids, models=models, batch=batch, group_by=group_by, limit=limit, page=page)

    async def usage_embeddings(self, start_time: int = None, end_time: int = None, bucket_width: Literal["1m", "1h", "1d"] = None, project_ids: List[str] = None, user_ids: List[str] = None, api_key_ids: List[str] = None, models: List[str] = None, group_by: List[Literal["project_id", "user_id", "api_key_id", "model"]] = None, limit: int = None, page: str = None) -> Dict[str, Any]:
        """Get embeddings usage details for the organization."""
        return await self._usage.usage_embeddings(start_time=start_time, end_time=end_time, bucket_width=bucket_width, project_ids=project_ids, user_ids=user_ids, api_key_ids=api_key_ids, models=models, group_by=group_by, limit=limit, page=page)

    async def usage_images(self, start_time: int = None, end_time: int = None, bucket_width: Literal["1m", "1h", "1d"] = None, sources: List[Literal["image.generation", "image.edit", "image.variation"]] = None, sizes: List[Literal["256x256", "512x512", "1024x1024", "1792x1792", "1024x1792"]] = None, project_ids: List[str] = None, user_ids: List[str] = None, api_key_ids: List[str] = None, models: List[str] = None, group_by: List[Literal["project_id", "user_id", "api_key_id", "model", "size", "source"]] = None, limit: int = None, page: str = None) -> Dict[str, Any]:
        """Get images usage details for the organization."""
        return await self._usage.usage_images(start_time=start_time, end_time=end_time, bucket_width=bucket_width, sources=sources, sizes=sizes, project_ids=project_ids, user_ids=user_ids, api_key_ids=api_key_ids, models=models, group_by=group_by, limit=limit, page=page)

    async def usage_moderations(self, start_time: int = None, end_time: int = None, bucket_width: Literal["1m", "1h", "1d"] = None, project_ids: List[str] = None, user_ids: List[str] = None, api_key_ids: List[str] = None, models: List[str] = None, group_by: List[Literal["project_id", "user_id", "api_key_id", "model"]] = None, limit: int = None, page: str = None) -> Dict[str, Any]:
        """Get moderations usage details for the organization."""
        return await self._usage.usage_moderations(start_time=start_time, end_time=end_time, bucket_width=bucket_width, project_ids=project_ids, user_ids=user_ids, api_key_ids=api_key_ids, models=models, group_by=group_by, limit=limit, page=page)

    async def usage_vector_stores(self, start_time: int = None, end_time: int = None, bucket_width: Literal["1m", "1h", "1d"] = None, project_ids: List[str] = None, group_by: List[Literal["project_id"]] = None, limit: int = None, page: str = None) -> Dict[str, Any]:
        """Get vector stores usage details for the organization."""
        return await self._usage.usage_vector_stores(start_time=start_time, end_time=end_time, bucket_width=bucket_width, project_ids=project_ids, group_by=group_by, limit=limit, page=page)

    # ─────────────────────────────────────────────────────────────────────────────
    # Groups operations
    # ─────────────────────────────────────────────────────────────────────────────

    async def list_groups(self, limit: int = None, after: str = None, order: Literal["asc", "desc"] = None) -> Dict[str, Any]:
        """Lists all groups in the organization."""
        return await self._groups.list_groups(limit=limit, after=after, order=order)

    async def create_group(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Creates a new group in the organization."""
        return await self._groups.create_group(body=body)

    async def update_group(self, group_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """Updates a group's information."""
        return await self._groups.update_group(group_id=group_id, body=body)

    async def delete_group(self, group_id: str) -> Dict[str, Any]:
        """Deletes a group from the organization."""
        return await self._groups.delete_group(group_id=group_id)

    # ─────────────────────────────────────────────────────────────────────────────
    # Group organization role assignments operations
    # ─────────────────────────────────────────────────────────────────────────────

    async def list_group_role_assignments(self, group_id: str, limit: int = None, after: str = None, order: Literal["asc", "desc"] = None) -> Dict[str, Any]:
        """Lists the organization roles assigned to a group within the organization."""
        return await self._group_organization_role_assignments.list_group_role_assignments(group_id=group_id, limit=limit, after=after, order=order)

    async def assign_group_role(self, group_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """Assigns an organization role to a group within the organization."""
        return await self._group_organization_role_assignments.assign_group_role(group_id=group_id, body=body)

    async def unassign_group_role(self, group_id: str, role_id: str) -> Dict[str, Any]:
        """Unassigns an organization role from a group within the organization."""
        return await self._group_organization_role_assignments.unassign_group_role(group_id=group_id, role_id=role_id)

    # ─────────────────────────────────────────────────────────────────────────────
    # Group users operations
    # ─────────────────────────────────────────────────────────────────────────────

    async def list_group_users(self, group_id: str, limit: int = None, after: str = None, order: Literal["asc", "desc"] = None) -> Dict[str, Any]:
        """Lists the users assigned to a group."""
        return await self._group_users.list_group_users(group_id=group_id, limit=limit, after=after, order=order)

    async def add_group_user(self, group_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """Adds a user to a group."""
        return await self._group_users.add_group_user(group_id=group_id, body=body)

    async def remove_group_user(self, group_id: str, user_id: str) -> Dict[str, Any]:
        """Removes a user from a group."""
        return await self._group_users.remove_group_user(group_id=group_id, user_id=user_id)

    # ─────────────────────────────────────────────────────────────────────────────
    # Invites operations
    # ─────────────────────────────────────────────────────────────────────────────

    async def list_invites(self, limit: int = None, after: str = None) -> Dict[str, Any]:
        """Returns a list of invites in the organization."""
        return await self._invites.list_invites(limit=limit, after=after)

    async def invite_user(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Create an invite for a user to the organization. The invite must be accepted by the user before they have access to the organization."""
        return await self._invites.invite_user(body=body)

    async def retrieve_invite(self, invite_id: str) -> Dict[str, Any]:
        """Retrieves an invite."""
        return await self._invites.retrieve_invite(invite_id=invite_id)

    async def delete_invite(self, invite_id: str) -> Dict[str, Any]:
        """Delete an invite. If the invite has already been accepted, it cannot be deleted."""
        return await self._invites.delete_invite(invite_id=invite_id)

    # ─────────────────────────────────────────────────────────────────────────────
    # Projects operations
    # ─────────────────────────────────────────────────────────────────────────────

    async def list_projects(self, limit: int = None, after: str = None, include_archived: bool = None) -> Dict[str, Any]:
        """Returns a list of projects."""
        return await self._projects.list_projects(limit=limit, after=after, include_archived=include_archived)

    async def create_project(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new project in the organization. Projects can be created and archived, but cannot be deleted."""
        return await self._projects.create_project(body=body)

    async def retrieve_project(self, project_id: str) -> Dict[str, Any]:
        """Retrieves a project."""
        return await self._projects.retrieve_project(project_id=project_id)

    async def modify_project(self, project_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """Modifies a project in the organization."""
        return await self._projects.modify_project(project_id=project_id, body=body)

    async def list_project_api_keys(self, project_id: str, limit: int = None, after: str = None) -> Dict[str, Any]:
        """Returns a list of API keys in the project."""
        return await self._projects.list_project_api_keys(project_id=project_id, limit=limit, after=after)

    async def retrieve_project_api_key(self, project_id: str, key_id: str) -> Dict[str, Any]:
        """Retrieves an API key in the project."""
        return await self._projects.retrieve_project_api_key(project_id=project_id, key_id=key_id)

    async def delete_project_api_key(self, project_id: str, key_id: str) -> Dict[str, Any]:
        """Deletes an API key from the project."""
        return await self._projects.delete_project_api_key(project_id=project_id, key_id=key_id)

    async def archive_project(self, project_id: str) -> Dict[str, Any]:
        """Archives a project in the organization. Archived projects cannot be used or updated."""
        return await self._projects.archive_project(project_id=project_id)

    async def list_project_rate_limits(self, project_id: str, limit: int = None, after: str = None, before: str = None) -> Dict[str, Any]:
        """Returns the rate limits per model for a project."""
        return await self._projects.list_project_rate_limits(project_id=project_id, limit=limit, after=after, before=before)

    async def update_project_rate_limits(self, project_id: str, rate_limit_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """Updates a project rate limit."""
        return await self._projects.update_project_rate_limits(project_id=project_id, rate_limit_id=rate_limit_id, body=body)

    async def list_project_service_accounts(self, project_id: str, limit: int = None, after: str = None) -> Dict[str, Any]:
        """Returns a list of service accounts in the project."""
        return await self._projects.list_project_service_accounts(project_id=project_id, limit=limit, after=after)

    async def create_project_service_account(self, project_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """Creates a new service account in the project. This also returns an unredacted API key for the service account."""
        return await self._projects.create_project_service_account(project_id=project_id, body=body)

    async def retrieve_project_service_account(self, project_id: str, service_account_id: str) -> Dict[str, Any]:
        """Retrieves a service account in the project."""
        return await self._projects.retrieve_project_service_account(project_id=project_id, service_account_id=service_account_id)

    async def delete_project_service_account(self, project_id: str, service_account_id: str) -> Dict[str, Any]:
        """Deletes a service account from the project."""
        return await self._projects.delete_project_service_account(project_id=project_id, service_account_id=service_account_id)

    async def list_project_users(self, project_id: str, limit: int = None, after: str = None) -> Dict[str, Any]:
        """Returns a list of users in the project."""
        return await self._projects.list_project_users(project_id=project_id, limit=limit, after=after)

    async def create_project_user(self, project_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """Adds a user to the project. Users must already be members of the organization to be added to a project."""
        return await self._projects.create_project_user(project_id=project_id, body=body)

    async def retrieve_project_user(self, project_id: str, user_id: str) -> Dict[str, Any]:
        """Retrieves a user in the project."""
        return await self._projects.retrieve_project_user(project_id=project_id, user_id=user_id)

    async def modify_project_user(self, project_id: str, user_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """Modifies a user's role in the project."""
        return await self._projects.modify_project_user(project_id=project_id, user_id=user_id, body=body)

    async def delete_project_user(self, project_id: str, user_id: str) -> Dict[str, Any]:
        """Deletes a user from the project."""
        return await self._projects.delete_project_user(project_id=project_id, user_id=user_id)

    # ─────────────────────────────────────────────────────────────────────────────
    # Project groups operations
    # ─────────────────────────────────────────────────────────────────────────────

    async def list_project_groups(self, project_id: str, limit: int = None, after: str = None, order: Literal["asc", "desc"] = None) -> Dict[str, Any]:
        """Lists the groups that have access to a project."""
        return await self._project_groups.list_project_groups(project_id=project_id, limit=limit, after=after, order=order)

    async def add_project_group(self, project_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """Grants a group access to a project."""
        return await self._project_groups.add_project_group(project_id=project_id, body=body)

    async def remove_project_group(self, project_id: str, group_id: str) -> Dict[str, Any]:
        """Revokes a group's access to a project."""
        return await self._project_groups.remove_project_group(project_id=project_id, group_id=group_id)

    # ─────────────────────────────────────────────────────────────────────────────
    # Roles operations
    # ─────────────────────────────────────────────────────────────────────────────

    async def list_roles(self, limit: int = None, after: str = None, order: Literal["asc", "desc"] = None) -> Dict[str, Any]:
        """Lists the roles configured for the organization."""
        return await self._roles.list_roles(limit=limit, after=after, order=order)

    async def create_role(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Creates a custom role for the organization."""
        return await self._roles.create_role(body=body)

    async def update_role(self, role_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """Updates an existing organization role."""
        return await self._roles.update_role(role_id=role_id, body=body)

    async def delete_role(self, role_id: str) -> Dict[str, Any]:
        """Deletes a custom role from the organization."""
        return await self._roles.delete_role(role_id=role_id)

    async def list_project_roles(self, project_id: str, limit: int = None, after: str = None, order: Literal["asc", "desc"] = None) -> Dict[str, Any]:
        """Lists the roles configured for a project."""
        return await self._roles.list_project_roles(project_id=project_id, limit=limit, after=after, order=order)

    async def create_project_role(self, project_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """Creates a custom role for a project."""
        return await self._roles.create_project_role(project_id=project_id, body=body)

    async def update_project_role(self, project_id: str, role_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """Updates an existing project role."""
        return await self._roles.update_project_role(project_id=project_id, role_id=role_id, body=body)

    async def delete_project_role(self, project_id: str, role_id: str) -> Dict[str, Any]:
        """Deletes a custom role from a project."""
        return await self._roles.delete_project_role(project_id=project_id, role_id=role_id)

    # ─────────────────────────────────────────────────────────────────────────────
    # Users operations
    # ─────────────────────────────────────────────────────────────────────────────

    async def list_users(self, limit: int = None, after: str = None, emails: List[str] = None) -> Dict[str, Any]:
        """Lists all of the users in the organization."""
        return await self._users.list_users(limit=limit, after=after, emails=emails)

    async def retrieve_user(self, user_id: str) -> Dict[str, Any]:
        """Retrieves a user by their identifier."""
        return await self._users.retrieve_user(user_id=user_id)

    async def modify_user(self, user_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """Modifies a user's role in the organization."""
        return await self._users.modify_user(user_id=user_id, body=body)

    async def delete_user(self, user_id: str) -> Dict[str, Any]:
        """Deletes a user from the organization."""
        return await self._users.delete_user(user_id=user_id)

    # ─────────────────────────────────────────────────────────────────────────────
    # User organization role assignments operations
    # ─────────────────────────────────────────────────────────────────────────────

    async def list_user_role_assignments(self, user_id: str, limit: int = None, after: str = None, order: Literal["asc", "desc"] = None) -> Dict[str, Any]:
        """Lists the organization roles assigned to a user within the organization."""
        return await self._user_organization_role_assignments.list_user_role_assignments(user_id=user_id, limit=limit, after=after, order=order)

    async def assign_user_role(self, user_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """Assigns an organization role to a user within the organization."""
        return await self._user_organization_role_assignments.assign_user_role(user_id=user_id, body=body)

    async def unassign_user_role(self, user_id: str, role_id: str) -> Dict[str, Any]:
        """Unassigns an organization role from a user within the organization."""
        return await self._user_organization_role_assignments.unassign_user_role(user_id=user_id, role_id=role_id)

    # ─────────────────────────────────────────────────────────────────────────────
    # Project group role assignments operations
    # ─────────────────────────────────────────────────────────────────────────────

    async def list_project_group_role_assignments(self, project_id: str, group_id: str, limit: int = None, after: str = None, order: Literal["asc", "desc"] = None) -> Dict[str, Any]:
        """Lists the project roles assigned to a group within a project."""
        return await self._project_group_role_assignments.list_project_group_role_assignments(project_id=project_id, group_id=group_id, limit=limit, after=after, order=order)

    async def assign_project_group_role(self, project_id: str, group_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """Assigns a project role to a group within a project."""
        return await self._project_group_role_assignments.assign_project_group_role(project_id=project_id, group_id=group_id, body=body)

    async def unassign_project_group_role(self, project_id: str, group_id: str, role_id: str) -> Dict[str, Any]:
        """Unassigns a project role from a group within a project."""
        return await self._project_group_role_assignments.unassign_project_group_role(project_id=project_id, group_id=group_id, role_id=role_id)

    # ─────────────────────────────────────────────────────────────────────────────
    # Project user role assignments operations
    # ─────────────────────────────────────────────────────────────────────────────

    async def list_project_user_role_assignments(self, project_id: str, user_id: str, limit: int = None, after: str = None, order: Literal["asc", "desc"] = None) -> Dict[str, Any]:
        """Lists the project roles assigned to a user within a project."""
        return await self._project_user_role_assignments.list_project_user_role_assignments(project_id=project_id, user_id=user_id, limit=limit, after=after, order=order)

    async def assign_project_user_role(self, project_id: str, user_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """Assigns a project role to a user within a project."""
        return await self._project_user_role_assignments.assign_project_user_role(project_id=project_id, user_id=user_id, body=body)

    async def unassign_project_user_role(self, project_id: str, user_id: str, role_id: str) -> Dict[str, Any]:
        """Unassigns a project role from a user within a project."""
        return await self._project_user_role_assignments.unassign_project_user_role(project_id=project_id, user_id=user_id, role_id=role_id)

    # ─────────────────────────────────────────────────────────────────────────────
    # Realtime operations
    # ─────────────────────────────────────────────────────────────────────────────

    async def create_realtime_call(self) -> Dict[str, Any]:
        """Create a new Realtime API call over WebRTC and receive the SDP answer needed
to complete the peer connection."""
        return await self._realtime.create_realtime_call()

    async def accept_realtime_call(self, call_id: str, body: RealtimeSessionConfiguration) -> Dict[str, Any]:
        """Accept an incoming SIP call and configure the realtime session that will
handle it."""
        return await self._realtime.accept_realtime_call(call_id=call_id, body=body)

    async def hangup_realtime_call(self, call_id: str) -> Dict[str, Any]:
        """End an active Realtime API call, whether it was initiated over SIP or
WebRTC."""
        return await self._realtime.hangup_realtime_call(call_id=call_id)

    async def refer_realtime_call(self, call_id: str, body: RealtimeCallReferRequest) -> Dict[str, Any]:
        """Transfer an active SIP call to a new destination using the SIP REFER verb."""
        return await self._realtime.refer_realtime_call(call_id=call_id, body=body)

    async def reject_realtime_call(self, call_id: str, body: RealtimeCallRejectRequest) -> Dict[str, Any]:
        """Decline an incoming SIP call by returning a SIP status code to the caller."""
        return await self._realtime.reject_realtime_call(call_id=call_id, body=body)

    async def create_realtime_client_secret(self, body: RealtimeClientSecretCreationRequest) -> RealtimeSessionAndClientSecret:
        """Create a Realtime client secret with an associated session configuration."""
        return await self._realtime.create_realtime_client_secret(body=body)

    async def create_realtime_session(self, body: Dict[str, Any]) -> RealtimeSessionConfigurationObject:
        """Create an ephemeral API token for use in client-side applications with the
Realtime API. Can be configured with the same session parameters as the
`session.update` client event.

It responds with a session object, plus a `client_secret` key which contains
a usable ephemeral API token that can be used to authenticate browser clients
for the Realtime API."""
        return await self._realtime.create_realtime_session(body=body)

    async def create_realtime_transcription_session(self, body: RealtimeTranscriptionSessionConfiguration) -> Dict[str, Any]:
        """Create an ephemeral API token for use in client-side applications with the
Realtime API specifically for realtime transcriptions. 
Can be configured with the same session parameters as the `transcription_session.update` client event.

It responds with a session object, plus a `client_secret` key which contains
a usable ephemeral API token that can be used to authenticate browser clients
for the Realtime API."""
        return await self._realtime.create_realtime_transcription_session(body=body)

    # ─────────────────────────────────────────────────────────────────────────────
    # Responses operations
    # ─────────────────────────────────────────────────────────────────────────────

    async def create_response(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Creates a model response. Provide [text](https://platform.openai.com/docs/guides/text) or
[image](https://platform.openai.com/docs/guides/images) inputs to generate [text](https://platform.openai.com/docs/guides/text)
or [JSON](https://platform.openai.com/docs/guides/structured-outputs) outputs. Have the model call
your own [custom code](https://platform.openai.com/docs/guides/function-calling) or use built-in
[tools](https://platform.openai.com/docs/guides/tools) like [web search](https://platform.openai.com/docs/guides/tools-web-search)
or [file search](https://platform.openai.com/docs/guides/tools-file-search) to use your own data
as input for the model's response."""
        return await self._responses.create_response(body=body)

    async def get_response(self, response_id: str, include: List[Literal["file_search_call.results", "web_search_call.results", "web_search_call.action.sources", "message.input_image.image_url", "computer_call_output.output.image_url", "code_interpreter_call.outputs", "reasoning.encrypted_content", "message.output_text.logprobs"]] = None, stream: bool = None, starting_after: int = None, include_obfuscation: bool = None) -> Dict[str, Any]:
        """Retrieves a model response with the given ID."""
        return await self._responses.get_response(response_id=response_id, include=include, stream=stream, starting_after=starting_after, include_obfuscation=include_obfuscation)

    async def delete_response(self, response_id: str) -> Dict[str, Any]:
        """Deletes a model response with the given ID."""
        return await self._responses.delete_response(response_id=response_id)

    async def cancel_response(self, response_id: str) -> Dict[str, Any]:
        """Cancels a model response with the given ID. Only responses created with
the `background` parameter set to `true` can be cancelled. 
[Learn more](https://platform.openai.com/docs/guides/background)."""
        return await self._responses.cancel_response(response_id=response_id)

    async def list_input_items(self, response_id: str, limit: int = None, order: Literal["asc", "desc"] = None, after: str = None, include: List[Literal["file_search_call.results", "web_search_call.results", "web_search_call.action.sources", "message.input_image.image_url", "computer_call_output.output.image_url", "code_interpreter_call.outputs", "reasoning.encrypted_content", "message.output_text.logprobs"]] = None) -> Dict[str, Any]:
        """Returns a list of input items for a given response."""
        return await self._responses.list_input_items(response_id=response_id, limit=limit, order=order, after=after, include=include)

    # ─────────────────────────────────────────────────────────────────────────────
    # Uploads operations
    # ─────────────────────────────────────────────────────────────────────────────

    async def create_upload(self, body: Dict[str, Any]) -> Upload:
        """Creates an intermediate [Upload](https://platform.openai.com/docs/api-reference/uploads/object) object
that you can add [Parts](https://platform.openai.com/docs/api-reference/uploads/part-object) to.
Currently, an Upload can accept at most 8 GB in total and expires after an
hour after you create it.

Once you complete the Upload, we will create a
[File](https://platform.openai.com/docs/api-reference/files/object) object that contains all the parts
you uploaded. This File is usable in the rest of our platform as a regular
File object.

For certain `purpose` values, the correct `mime_type` must be specified. 
Please refer to documentation for the 
[supported MIME types for your use case](https://platform.openai.com/docs/assistants/tools/file-search#supported-files).

For guidance on the proper filename extensions for each purpose, please
follow the documentation on [creating a
File](https://platform.openai.com/docs/api-reference/files/create)."""
        return await self._uploads.create_upload(body=body)

    async def cancel_upload(self, upload_id: str) -> Upload:
        """Cancels the Upload. No Parts may be added after an Upload is cancelled."""
        return await self._uploads.cancel_upload(upload_id=upload_id)

    async def complete_upload(self, upload_id: str, body: Dict[str, Any]) -> Upload:
        """Completes the [Upload](https://platform.openai.com/docs/api-reference/uploads/object). 

Within the returned Upload object, there is a nested [File](https://platform.openai.com/docs/api-reference/files/object) object that is ready to use in the rest of the platform.

You can specify the order of the Parts by passing in an ordered list of the Part IDs.

The number of bytes uploaded upon completion must match the number of bytes initially specified when creating the Upload object. No Parts may be added after an Upload is completed."""
        return await self._uploads.complete_upload(upload_id=upload_id, body=body)

    async def add_upload_part(self, upload_id: str) -> UploadPart:
        """Adds a [Part](https://platform.openai.com/docs/api-reference/uploads/part-object) to an [Upload](https://platform.openai.com/docs/api-reference/uploads/object) object. A Part represents a chunk of bytes from the file you are trying to upload. 

Each Part can be at most 64 MB, and you can add Parts until you hit the Upload maximum of 8 GB.

It is possible to add multiple Parts in parallel. You can decide the intended order of the Parts when you [complete the Upload](https://platform.openai.com/docs/api-reference/uploads/complete)."""
        return await self._uploads.add_upload_part(upload_id=upload_id)

    # ─────────────────────────────────────────────────────────────────────────────
    # Vector stores operations
    # ─────────────────────────────────────────────────────────────────────────────

    async def list_vector_stores(self, limit: int = None, order: Literal["asc", "desc"] = None, after: str = None, before: str = None) -> Any:
        """Returns a list of vector stores."""
        return await self._vector_stores.list_vector_stores(limit=limit, order=order, after=after, before=before)

    async def create_vector_store(self, body: Dict[str, Any]) -> VectorStore:
        """Create a vector store."""
        return await self._vector_stores.create_vector_store(body=body)

    async def get_vector_store(self, vector_store_id: str) -> VectorStore:
        """Retrieves a vector store."""
        return await self._vector_stores.get_vector_store(vector_store_id=vector_store_id)

    async def modify_vector_store(self, vector_store_id: str, body: Dict[str, Any]) -> VectorStore:
        """Modifies a vector store."""
        return await self._vector_stores.modify_vector_store(vector_store_id=vector_store_id, body=body)

    async def delete_vector_store(self, vector_store_id: str) -> Dict[str, Any]:
        """Delete a vector store."""
        return await self._vector_stores.delete_vector_store(vector_store_id=vector_store_id)

    async def create_vector_store_file_batch(self, vector_store_id: str, body: Dict[str, Any]) -> VectorStoreFileBatch:
        """Create a vector store file batch."""
        return await self._vector_stores.create_vector_store_file_batch(vector_store_id=vector_store_id, body=body)

    async def get_vector_store_file_batch(self, vector_store_id: str, batch_id: str) -> VectorStoreFileBatch:
        """Retrieves a vector store file batch."""
        return await self._vector_stores.get_vector_store_file_batch(vector_store_id=vector_store_id, batch_id=batch_id)

    async def cancel_vector_store_file_batch(self, vector_store_id: str, batch_id: str) -> VectorStoreFileBatch:
        """Cancel a vector store file batch. This attempts to cancel the processing of files in this batch as soon as possible."""
        return await self._vector_stores.cancel_vector_store_file_batch(vector_store_id=vector_store_id, batch_id=batch_id)

    async def list_files_in_vector_store_batch(self, vector_store_id: str, batch_id: str, limit: int = None, order: Literal["asc", "desc"] = None, after: str = None, before: str = None, filter: Literal["in_progress", "completed", "failed", "cancelled"] = None) -> Any:
        """Returns a list of vector store files in a batch."""
        return await self._vector_stores.list_files_in_vector_store_batch(vector_store_id=vector_store_id, batch_id=batch_id, limit=limit, order=order, after=after, before=before, filter=filter)

    async def list_vector_store_files(self, vector_store_id: str, limit: int = None, order: Literal["asc", "desc"] = None, after: str = None, before: str = None, filter: Literal["in_progress", "completed", "failed", "cancelled"] = None) -> Any:
        """Returns a list of vector store files."""
        return await self._vector_stores.list_vector_store_files(vector_store_id=vector_store_id, limit=limit, order=order, after=after, before=before, filter=filter)

    async def create_vector_store_file(self, vector_store_id: str, body: Dict[str, Any]) -> VectorStoreFiles:
        """Create a vector store file by attaching a [File](https://platform.openai.com/docs/api-reference/files) to a [vector store](https://platform.openai.com/docs/api-reference/vector-stores/object)."""
        return await self._vector_stores.create_vector_store_file(vector_store_id=vector_store_id, body=body)

    async def get_vector_store_file(self, vector_store_id: str, file_id: str) -> VectorStoreFiles:
        """Retrieves a vector store file."""
        return await self._vector_stores.get_vector_store_file(vector_store_id=vector_store_id, file_id=file_id)

    async def update_vector_store_file_attributes(self, vector_store_id: str, file_id: str, body: Dict[str, Any]) -> VectorStoreFiles:
        """Update attributes on a vector store file."""
        return await self._vector_stores.update_vector_store_file_attributes(vector_store_id=vector_store_id, file_id=file_id, body=body)

    async def delete_vector_store_file(self, vector_store_id: str, file_id: str) -> Dict[str, Any]:
        """Delete a vector store file. This will remove the file from the vector store but the file itself will not be deleted. To delete the file, use the [delete file](https://platform.openai.com/docs/api-reference/files/delete) endpoint."""
        return await self._vector_stores.delete_vector_store_file(vector_store_id=vector_store_id, file_id=file_id)

    async def retrieve_vector_store_file_content(self, vector_store_id: str, file_id: str) -> Dict[str, Any]:
        """Retrieve the parsed contents of a vector store file."""
        return await self._vector_stores.retrieve_vector_store_file_content(vector_store_id=vector_store_id, file_id=file_id)

    async def search_vector_store(self, vector_store_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """Search a vector store for relevant chunks based on a query and file attributes filter."""
        return await self._vector_stores.search_vector_store(vector_store_id=vector_store_id, body=body)

    # ─────────────────────────────────────────────────────────────────────────────
    # Videos operations
    # ─────────────────────────────────────────────────────────────────────────────

    async def list_videos(self, limit: int = None, order: Literal["asc", "desc"] = None, after: str = None) -> Dict[str, Any]:
        """List videos"""
        return await self._videos.list_videos(limit=limit, order=order, after=after)

    async def create_video(self, body: CreateVideoRequest) -> VideoJob:
        """Create a video"""
        return await self._videos.create_video(body=body)

    async def get_video(self, video_id: str) -> VideoJob:
        """Retrieve a video"""
        return await self._videos.get_video(video_id=video_id)

    async def delete_video(self, video_id: str) -> DeletedVideoResponse:
        """Delete a video"""
        return await self._videos.delete_video(video_id=video_id)

    async def retrieve_video_content(self, video_id: str, variant: Literal["video", "thumbnail", "spritesheet"] = None) -> str:
        """Download video content"""
        return await self._videos.retrieve_video_content(video_id=video_id, variant=variant)

    async def create_video_remix(self, video_id: str, body: CreateVideoRemixRequest) -> VideoJob:
        """Create a video remix"""
        return await self._videos.create_video_remix(video_id=video_id, body=body)
