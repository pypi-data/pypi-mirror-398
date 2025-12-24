import httpx
from typing import Any, Dict, List, Literal, Optional, Union
from .types import *

class AssistantsClient:
    def __init__(self, base_url: str, token: str):
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token}"}
        )

    async def list_assistants(
        self,
        limit: int = None,
        order: Literal["asc", "desc"] = None,
        after: str = None,
        before: str = None
    ) -> Dict[str, Any]:
        """Returns a list of assistants."""
        url = f"/assistants"

        params = {
            "limit": limit,
            "order": order,
            "after": after,
            "before": before,
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

    async def create_assistant(
        self,
        body: Dict[str, Any]
    ) -> Assistant:
        """Create an assistant with a model and instructions."""
        url = f"/assistants"

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

    async def get_assistant(
        self,
        assistant_id: str
    ) -> Assistant:
        """Retrieves an assistant."""
        url = f"/assistants/{assistant_id}"

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

    async def modify_assistant(
        self,
        assistant_id: str,
        body: Dict[str, Any]
    ) -> Assistant:
        """Modifies an assistant."""
        url = f"/assistants/{assistant_id}"

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

    async def delete_assistant(
        self,
        assistant_id: str
    ) -> Dict[str, Any]:
        """Delete an assistant."""
        url = f"/assistants/{assistant_id}"

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

        return response.json()

    async def create_thread(
        self,
        body: Dict[str, Any]
    ) -> Thread:
        """Create a thread."""
        url = f"/threads"

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

    async def create_thread_and_run(
        self,
        body: Dict[str, Any]
    ) -> ARunOnAThread:
        """Create a thread and run it in one request."""
        url = f"/threads/runs"

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

    async def get_thread(
        self,
        thread_id: str
    ) -> Thread:
        """Retrieves a thread."""
        url = f"/threads/{thread_id}"

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

    async def modify_thread(
        self,
        thread_id: str,
        body: Dict[str, Any]
    ) -> Thread:
        """Modifies a thread."""
        url = f"/threads/{thread_id}"

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

    async def delete_thread(
        self,
        thread_id: str
    ) -> Dict[str, Any]:
        """Delete a thread."""
        url = f"/threads/{thread_id}"

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

        return response.json()

    async def list_messages(
        self,
        thread_id: str,
        limit: int = None,
        order: Literal["asc", "desc"] = None,
        after: str = None,
        before: str = None,
        run_id: str = None
    ) -> Any:
        """Returns a list of messages for a given thread."""
        url = f"/threads/{thread_id}/messages"

        params = {
            "limit": limit,
            "order": order,
            "after": after,
            "before": before,
            "run_id": run_id,
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

    async def create_message(
        self,
        thread_id: str,
        body: Dict[str, Any]
    ) -> TheMessageObject:
        """Create a message."""
        url = f"/threads/{thread_id}/messages"

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

    async def get_message(
        self,
        thread_id: str,
        message_id: str
    ) -> TheMessageObject:
        """Retrieve a message."""
        url = f"/threads/{thread_id}/messages/{message_id}"

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

    async def modify_message(
        self,
        thread_id: str,
        message_id: str,
        body: Dict[str, Any]
    ) -> TheMessageObject:
        """Modifies a message."""
        url = f"/threads/{thread_id}/messages/{message_id}"

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

    async def delete_message(
        self,
        thread_id: str,
        message_id: str
    ) -> Dict[str, Any]:
        """Deletes a message."""
        url = f"/threads/{thread_id}/messages/{message_id}"

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

        return response.json()

    async def list_runs(
        self,
        thread_id: str,
        limit: int = None,
        order: Literal["asc", "desc"] = None,
        after: str = None,
        before: str = None
    ) -> Dict[str, Any]:
        """Returns a list of runs belonging to a thread."""
        url = f"/threads/{thread_id}/runs"

        params = {
            "limit": limit,
            "order": order,
            "after": after,
            "before": before,
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

    async def create_run(
        self,
        thread_id: str,
        body: Dict[str, Any],
        include: List[Literal["step_details.tool_calls[*].file_search.results[*].content"]] = None
    ) -> ARunOnAThread:
        """Create a run."""
        url = f"/threads/{thread_id}/runs"

        params = {
            "include[]": include,
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

    async def get_run(
        self,
        thread_id: str,
        run_id: str
    ) -> ARunOnAThread:
        """Retrieves a run."""
        url = f"/threads/{thread_id}/runs/{run_id}"

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

    async def modify_run(
        self,
        thread_id: str,
        run_id: str,
        body: Dict[str, Any]
    ) -> ARunOnAThread:
        """Modifies a run."""
        url = f"/threads/{thread_id}/runs/{run_id}"

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

    async def cancel_run(
        self,
        thread_id: str,
        run_id: str
    ) -> ARunOnAThread:
        """Cancels a run that is `in_progress`."""
        url = f"/threads/{thread_id}/runs/{run_id}/cancel"

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

        return response.json()

    async def list_run_steps(
        self,
        thread_id: str,
        run_id: str,
        limit: int = None,
        order: Literal["asc", "desc"] = None,
        after: str = None,
        before: str = None,
        include: List[Literal["step_details.tool_calls[*].file_search.results[*].content"]] = None
    ) -> Any:
        """Returns a list of run steps belonging to a run."""
        url = f"/threads/{thread_id}/runs/{run_id}/steps"

        params = {
            "limit": limit,
            "order": order,
            "after": after,
            "before": before,
            "include[]": include,
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

    async def get_run_step(
        self,
        thread_id: str,
        run_id: str,
        step_id: str,
        include: List[Literal["step_details.tool_calls[*].file_search.results[*].content"]] = None
    ) -> RunSteps:
        """Retrieves a run step."""
        url = f"/threads/{thread_id}/runs/{run_id}/steps/{step_id}"

        params = {
            "include[]": include,
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

    async def submit_tool_ouputs_to_run(
        self,
        thread_id: str,
        run_id: str,
        body: Dict[str, Any]
    ) -> ARunOnAThread:
        """When a run has the `status: "requires_action"` and `required_action.type` is `submit_tool_outputs`, this endpoint can be used to submit the outputs from the tool calls once they're all completed. All outputs must be submitted in a single request."""
        url = f"/threads/{thread_id}/runs/{run_id}/submit_tool_outputs"

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


class AudioClient:
    def __init__(self, base_url: str, token: str):
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token}"}
        )

    async def create_speech(
        self,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generates audio from the input text."""
        url = f"/audio/speech"

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

    async def create_transcription(
        self,
        
    ) -> Union[Dict[str, Any]]:
        """Transcribes audio into the input language."""
        url = f"/audio/transcriptions"

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

        return response.json()

    async def create_translation(
        self,
        
    ) -> Union[Dict[str, Any]]:
        """Translates audio into English."""
        url = f"/audio/translations"

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

        return response.json()

    async def list_voice_consents(
        self,
        after: str = None,
        limit: int = None
    ) -> Dict[str, Any]:
        """Returns a list of voice consent recordings."""
        url = f"/audio/voice_consents"

        params = {
            "after": after,
            "limit": limit,
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

    async def create_voice_consent(
        self,
        
    ) -> VoiceConsent:
        """Upload a voice consent recording."""
        url = f"/audio/voice_consents"

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

        return response.json()

    async def get_voice_consent(
        self,
        consent_id: str
    ) -> VoiceConsent:
        """Retrieves a voice consent recording."""
        url = f"/audio/voice_consents/{consent_id}"

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

    async def update_voice_consent(
        self,
        consent_id: str,
        body: Dict[str, Any]
    ) -> VoiceConsent:
        """Updates a voice consent recording (metadata only)."""
        url = f"/audio/voice_consents/{consent_id}"

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

    async def delete_voice_consent(
        self,
        consent_id: str
    ) -> Dict[str, Any]:
        """Deletes a voice consent recording."""
        url = f"/audio/voice_consents/{consent_id}"

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

        return response.json()

    async def create_voice(
        self,
        
    ) -> Voice:
        """Creates a custom voice."""
        url = f"/audio/voices"

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

        return response.json()


class BatchClient:
    def __init__(self, base_url: str, token: str):
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token}"}
        )

    async def list_batches(
        self,
        after: str = None,
        limit: int = None
    ) -> Dict[str, Any]:
        """List your organization's batches."""
        url = f"/batches"

        params = {
            "after": after,
            "limit": limit,
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

    async def create_batch(
        self,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Creates and executes a batch from an uploaded file of requests"""
        url = f"/batches"

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

    async def retrieve_batch(
        self,
        batch_id: str
    ) -> Dict[str, Any]:
        """Retrieves a batch."""
        url = f"/batches/{batch_id}"

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

    async def cancel_batch(
        self,
        batch_id: str
    ) -> Dict[str, Any]:
        """Cancels an in-progress batch. The batch will be in status `cancelling` for up to 10 minutes, before changing to `cancelled`, where it will have partial results (if any) available in the output file."""
        url = f"/batches/{batch_id}/cancel"

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

        return response.json()


class ChatClient:
    def __init__(self, base_url: str, token: str):
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token}"}
        )

    async def list_chat_completions(
        self,
        model: str = None,
        metadata: Dict[str, str] = None,
        after: str = None,
        limit: int = None,
        order: Literal["asc", "desc"] = None
    ) -> ChatCompletionList:
        """List stored Chat Completions. Only Chat Completions that have been stored
with the `store` parameter set to `true` will be returned."""
        url = f"/chat/completions"

        params = {
            "model": model,
            "metadata": metadata,
            "after": after,
            "limit": limit,
            "order": order,
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

    async def create_chat_completion(
        self,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
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
        url = f"/chat/completions"

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

    async def get_chat_completion(
        self,
        completion_id: str
    ) -> Dict[str, Any]:
        """Get a stored chat completion. Only Chat Completions that have been created
with the `store` parameter set to `true` will be returned."""
        url = f"/chat/completions/{completion_id}"

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

    async def update_chat_completion(
        self,
        completion_id: str,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Modify a stored chat completion. Only Chat Completions that have been
created with the `store` parameter set to `true` can be modified. Currently,
the only supported modification is to update the `metadata` field."""
        url = f"/chat/completions/{completion_id}"

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

    async def delete_chat_completion(
        self,
        completion_id: str
    ) -> Dict[str, Any]:
        """Delete a stored chat completion. Only Chat Completions that have been
created with the `store` parameter set to `true` can be deleted."""
        url = f"/chat/completions/{completion_id}"

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

        return response.json()

    async def get_chat_completion_messages(
        self,
        completion_id: str,
        after: str = None,
        limit: int = None,
        order: Literal["asc", "desc"] = None
    ) -> ChatCompletionMessageList:
        """Get the messages in a stored chat completion. Only Chat Completions that
have been created with the `store` parameter set to `true` will be
returned."""
        url = f"/chat/completions/{completion_id}/messages"

        params = {
            "after": after,
            "limit": limit,
            "order": order,
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


class CompletionsClient:
    def __init__(self, base_url: str, token: str):
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token}"}
        )

    async def create_completion(
        self,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Creates a completion for the provided prompt and parameters."""
        url = f"/completions"

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


class DefaultClient:
    def __init__(self, base_url: str, token: str):
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token}"}
        )

    async def list_containers(
        self,
        limit: int = None,
        order: Literal["asc", "desc"] = None,
        after: str = None
    ) -> Dict[str, Any]:
        """List Containers"""
        url = f"/containers"

        params = {
            "limit": limit,
            "order": order,
            "after": after,
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

    async def create_container(
        self,
        body: Dict[str, Any]
    ) -> TheContainerObject:
        """Create Container"""
        url = f"/containers"

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

    async def retrieve_container(
        self,
        container_id: str
    ) -> TheContainerObject:
        """Retrieve Container"""
        url = f"/containers/{container_id}"

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

    async def delete_container(
        self,
        container_id: str
    ) -> Dict[str, Any]:
        """Delete Container"""
        url = f"/containers/{container_id}"

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

    async def list_container_files(
        self,
        container_id: str,
        limit: int = None,
        order: Literal["asc", "desc"] = None,
        after: str = None
    ) -> Dict[str, Any]:
        """List Container files"""
        url = f"/containers/{container_id}/files"

        params = {
            "limit": limit,
            "order": order,
            "after": after,
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

    async def create_container_file(
        self,
        container_id: str
    ) -> TheContainerFileObject:
        """Create a Container File

You can send either a multipart/form-data request with the raw file content, or a JSON request with a file ID."""
        url = f"/containers/{container_id}/files"

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

        return response.json()

    async def retrieve_container_file(
        self,
        container_id: str,
        file_id: str
    ) -> TheContainerFileObject:
        """Retrieve Container File"""
        url = f"/containers/{container_id}/files/{file_id}"

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

    async def delete_container_file(
        self,
        container_id: str,
        file_id: str
    ) -> Dict[str, Any]:
        """Delete Container File"""
        url = f"/containers/{container_id}/files/{file_id}"

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

    async def retrieve_container_file_content(
        self,
        container_id: str,
        file_id: str
    ) -> Dict[str, Any]:
        """Retrieve Container File Content"""
        url = f"/containers/{container_id}/files/{file_id}/content"

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

    async def admin_api_keys_list(
        self,
        after: Optional[str] = None,
        order: Literal["asc", "desc"] = None,
        limit: int = None
    ) -> Dict[str, Any]:
        """List organization API keys"""
        url = f"/organization/admin_api_keys"

        params = {
            "after": after,
            "order": order,
            "limit": limit,
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

    async def admin_api_keys_create(
        self,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create an organization admin API key"""
        url = f"/organization/admin_api_keys"

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

    async def admin_api_keys_get(
        self,
        key_id: str
    ) -> Dict[str, Any]:
        """Retrieve a single organization API key"""
        url = f"/organization/admin_api_keys/{key_id}"

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

    async def admin_api_keys_delete(
        self,
        key_id: str
    ) -> Dict[str, Any]:
        """Delete an organization admin API key"""
        url = f"/organization/admin_api_keys/{key_id}"

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

        return response.json()

    async def getinputtokencounts(
        self,
        body: Dict[str, Any]
    ) -> TokenCounts:
        """Get input token counts"""
        url = f"/responses/input_tokens"

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

    async def compactconversation(
        self,
        body: Dict[str, Any]
    ) -> TheCompactedResponseObject:
        """Compact conversation"""
        url = f"/responses/compact"

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

    async def cancel_chat_session_method(
        self,
        session_id: str
    ) -> TheChatSessionObject:
        """Cancel a ChatKit session"""
        url = f"/chatkit/sessions/{session_id}/cancel"

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

        return response.json()

    async def create_chat_session_method(
        self,
        body: CreateChatSessionRequest
    ) -> TheChatSessionObject:
        """Create a ChatKit session"""
        url = f"/chatkit/sessions"

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

    async def list_thread_items_method(
        self,
        thread_id: str,
        limit: int = None,
        order: Literal["asc", "desc"] = None,
        after: str = None,
        before: str = None
    ) -> ThreadItems:
        """List ChatKit thread items"""
        url = f"/chatkit/threads/{thread_id}/items"

        params = {
            "limit": limit,
            "order": order,
            "after": after,
            "before": before,
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

    async def get_thread_method(
        self,
        thread_id: str
    ) -> TheThreadObject:
        """Retrieve a ChatKit thread"""
        url = f"/chatkit/threads/{thread_id}"

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

    async def delete_thread_method(
        self,
        thread_id: str
    ) -> DeletedThread:
        """Delete a ChatKit thread"""
        url = f"/chatkit/threads/{thread_id}"

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

        return response.json()

    async def list_threads_method(
        self,
        limit: int = None,
        order: Literal["asc", "desc"] = None,
        after: str = None,
        before: str = None,
        user: str = None
    ) -> Threads:
        """List ChatKit threads"""
        url = f"/chatkit/threads"

        params = {
            "limit": limit,
            "order": order,
            "after": after,
            "before": before,
            "user": user,
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


class ConversationsClient:
    def __init__(self, base_url: str, token: str):
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token}"}
        )

    async def list_conversation_items(
        self,
        conversation_id: str,
        limit: int = None,
        order: Literal["asc", "desc"] = None,
        after: str = None,
        include: List[Literal["file_search_call.results", "web_search_call.results", "web_search_call.action.sources", "message.input_image.image_url", "computer_call_output.output.image_url", "code_interpreter_call.outputs", "reasoning.encrypted_content", "message.output_text.logprobs"]] = None
    ) -> TheConversationItemList:
        """List all items for a conversation with the given ID."""
        url = f"/conversations/{conversation_id}/items"

        params = {
            "limit": limit,
            "order": order,
            "after": after,
            "include": include,
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

    async def create_conversation_items(
        self,
        conversation_id: str,
        body: Any,
        include: List[Literal["file_search_call.results", "web_search_call.results", "web_search_call.action.sources", "message.input_image.image_url", "computer_call_output.output.image_url", "code_interpreter_call.outputs", "reasoning.encrypted_content", "message.output_text.logprobs"]] = None
    ) -> TheConversationItemList:
        """Create items in a conversation with the given ID."""
        url = f"/conversations/{conversation_id}/items"

        params = {
            "include": include,
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

    async def get_conversation_item(
        self,
        conversation_id: str,
        item_id: str,
        include: List[Literal["file_search_call.results", "web_search_call.results", "web_search_call.action.sources", "message.input_image.image_url", "computer_call_output.output.image_url", "code_interpreter_call.outputs", "reasoning.encrypted_content", "message.output_text.logprobs"]] = None
    ) -> Union[Message, FunctionToolCall, FunctionToolCallOutput, FileSearchToolCall, WebSearchToolCall, ImageGenerationCall, ComputerToolCall, ComputerToolCallOutput, Reasoning, CodeInterpreterToolCall, LocalShellCall, LocalShellCallOutput, ShellToolCall, ShellCallOutput, ApplyPatchToolCall, ApplyPatchToolCallOutput, McpListTools, McpApprovalRequest, McpApprovalResponse, McpToolCall, CustomToolCall, CustomToolCallOutput]:
        """Get a single item from a conversation with the given IDs."""
        url = f"/conversations/{conversation_id}/items/{item_id}"

        params = {
            "include": include,
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

    async def delete_conversation_item(
        self,
        conversation_id: str,
        item_id: str
    ) -> Dict[str, Any]:
        """Delete an item from a conversation with the given IDs."""
        url = f"/conversations/{conversation_id}/items/{item_id}"

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

        return response.json()

    async def create_conversation(
        self,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a conversation."""
        url = f"/conversations"

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

    async def get_conversation(
        self,
        conversation_id: str
    ) -> Dict[str, Any]:
        """Get a conversation"""
        url = f"/conversations/{conversation_id}"

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

    async def update_conversation(
        self,
        conversation_id: str,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a conversation"""
        url = f"/conversations/{conversation_id}"

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

    async def delete_conversation(
        self,
        conversation_id: str
    ) -> Dict[str, Any]:
        """Delete a conversation. Items in the conversation will not be deleted."""
        url = f"/conversations/{conversation_id}"

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

        return response.json()


class EmbeddingsClient:
    def __init__(self, base_url: str, token: str):
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token}"}
        )

    async def create_embedding(
        self,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Creates an embedding vector representing the input text."""
        url = f"/embeddings"

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


class EvalsClient:
    def __init__(self, base_url: str, token: str):
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token}"}
        )

    async def list_evals(
        self,
        after: str = None,
        limit: int = None,
        order: Literal["asc", "desc"] = None,
        order_by: Literal["created_at", "updated_at"] = None
    ) -> EvalList:
        """List evaluations for a project."""
        url = f"/evals"

        params = {
            "after": after,
            "limit": limit,
            "order": order,
            "order_by": order_by,
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

    async def create_eval(
        self,
        body: CreateEvalRequest
    ) -> Eval:
        """Create the structure of an evaluation that can be used to test a model's performance.
An evaluation is a set of testing criteria and the config for a data source, which dictates the schema of the data used in the evaluation. After creating an evaluation, you can run it on different models and model parameters. We support several types of graders and datasources.
For more information, see the [Evals guide](https://platform.openai.com/docs/guides/evals)."""
        url = f"/evals"

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

    async def get_eval(
        self,
        eval_id: str
    ) -> Eval:
        """Get an evaluation by ID."""
        url = f"/evals/{eval_id}"

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

    async def update_eval(
        self,
        eval_id: str,
        body: Dict[str, Any]
    ) -> Eval:
        """Update certain properties of an evaluation."""
        url = f"/evals/{eval_id}"

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

    async def delete_eval(
        self,
        eval_id: str
    ) -> Dict[str, Any]:
        """Delete an evaluation."""
        url = f"/evals/{eval_id}"

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

        return response.json()

    async def get_eval_runs(
        self,
        eval_id: str,
        after: str = None,
        limit: int = None,
        order: Literal["asc", "desc"] = None,
        status: Literal["queued", "in_progress", "completed", "canceled", "failed"] = None
    ) -> EvalRunList:
        """Get a list of runs for an evaluation."""
        url = f"/evals/{eval_id}/runs"

        params = {
            "after": after,
            "limit": limit,
            "order": order,
            "status": status,
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

    async def create_eval_run(
        self,
        eval_id: str,
        body: CreateEvalRunRequest
    ) -> EvalRun:
        """Kicks off a new run for a given evaluation, specifying the data source, and what model configuration to use to test. The datasource will be validated against the schema specified in the config of the evaluation."""
        url = f"/evals/{eval_id}/runs"

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

    async def get_eval_run(
        self,
        eval_id: str,
        run_id: str
    ) -> EvalRun:
        """Get an evaluation run by ID."""
        url = f"/evals/{eval_id}/runs/{run_id}"

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

    async def cancel_eval_run(
        self,
        eval_id: str,
        run_id: str
    ) -> EvalRun:
        """Cancel an ongoing evaluation run."""
        url = f"/evals/{eval_id}/runs/{run_id}"

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

        return response.json()

    async def delete_eval_run(
        self,
        eval_id: str,
        run_id: str
    ) -> Dict[str, Any]:
        """Delete an eval run."""
        url = f"/evals/{eval_id}/runs/{run_id}"

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

        return response.json()

    async def get_eval_run_output_items(
        self,
        eval_id: str,
        run_id: str,
        after: str = None,
        limit: int = None,
        status: Literal["fail", "pass"] = None,
        order: Literal["asc", "desc"] = None
    ) -> EvalRunOutputItemList:
        """Get a list of output items for an evaluation run."""
        url = f"/evals/{eval_id}/runs/{run_id}/output_items"

        params = {
            "after": after,
            "limit": limit,
            "status": status,
            "order": order,
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

    async def get_eval_run_output_item(
        self,
        eval_id: str,
        run_id: str,
        output_item_id: str
    ) -> EvalRunOutputItem:
        """Get an evaluation run output item by ID."""
        url = f"/evals/{eval_id}/runs/{run_id}/output_items/{output_item_id}"

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


class FilesClient:
    def __init__(self, base_url: str, token: str):
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token}"}
        )

    async def list_files(
        self,
        purpose: str = None,
        limit: int = None,
        order: Literal["asc", "desc"] = None,
        after: str = None
    ) -> Dict[str, Any]:
        """Returns a list of files."""
        url = f"/files"

        params = {
            "purpose": purpose,
            "limit": limit,
            "order": order,
            "after": after,
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

    async def create_file(
        self,
        
    ) -> Any:
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
        url = f"/files"

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

        return response.json()

    async def retrieve_file(
        self,
        file_id: str
    ) -> Any:
        """Returns information about a specific file."""
        url = f"/files/{file_id}"

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

    async def delete_file(
        self,
        file_id: str
    ) -> Dict[str, Any]:
        """Delete a file and remove it from all vector stores."""
        url = f"/files/{file_id}"

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

        return response.json()

    async def download_file(
        self,
        file_id: str
    ) -> str:
        """Returns the contents of the specified file."""
        url = f"/files/{file_id}/content"

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


class FineTuningClient:
    def __init__(self, base_url: str, token: str):
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token}"}
        )

    async def run_grader(
        self,
        body: RunGraderRequest
    ) -> Dict[str, Any]:
        """Run a grader."""
        url = f"/fine_tuning/alpha/graders/run"

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

    async def validate_grader(
        self,
        body: ValidateGraderRequest
    ) -> ValidateGraderResponse:
        """Validate a grader."""
        url = f"/fine_tuning/alpha/graders/validate"

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

    async def list_fine_tuning_checkpoint_permissions(
        self,
        fine_tuned_model_checkpoint: str,
        project_id: str = None,
        after: str = None,
        limit: int = None,
        order: Literal["ascending", "descending"] = None
    ) -> Dict[str, Any]:
        """**NOTE:** This endpoint requires an [admin API key](../admin-api-keys).

Organization owners can use this endpoint to view all permissions for a fine-tuned model checkpoint."""
        url = f"/fine_tuning/checkpoints/{fine_tuned_model_checkpoint}/permissions"

        params = {
            "project_id": project_id,
            "after": after,
            "limit": limit,
            "order": order,
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

    async def create_fine_tuning_checkpoint_permission(
        self,
        fine_tuned_model_checkpoint: str,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """**NOTE:** Calling this endpoint requires an [admin API key](../admin-api-keys).

This enables organization owners to share fine-tuned models with other projects in their organization."""
        url = f"/fine_tuning/checkpoints/{fine_tuned_model_checkpoint}/permissions"

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

    async def delete_fine_tuning_checkpoint_permission(
        self,
        fine_tuned_model_checkpoint: str,
        permission_id: str
    ) -> Dict[str, Any]:
        """**NOTE:** This endpoint requires an [admin API key](../admin-api-keys).

Organization owners can use this endpoint to delete a permission for a fine-tuned model checkpoint."""
        url = f"/fine_tuning/checkpoints/{fine_tuned_model_checkpoint}/permissions/{permission_id}"

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

        return response.json()

    async def list_paginated_fine_tuning_jobs(
        self,
        after: str = None,
        limit: int = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """List your organization's fine-tuning jobs"""
        url = f"/fine_tuning/jobs"

        params = {
            "after": after,
            "limit": limit,
            "metadata": metadata,
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

    async def create_fine_tuning_job(
        self,
        body: Dict[str, Any]
    ) -> FineTuningJob:
        """Creates a fine-tuning job which begins the process of creating a new model from a given dataset.

Response includes details of the enqueued job including job status and the name of the fine-tuned models once complete.

[Learn more about fine-tuning](https://platform.openai.com/docs/guides/model-optimization)"""
        url = f"/fine_tuning/jobs"

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

    async def retrieve_fine_tuning_job(
        self,
        fine_tuning_job_id: str
    ) -> FineTuningJob:
        """Get info about a fine-tuning job.

[Learn more about fine-tuning](https://platform.openai.com/docs/guides/model-optimization)"""
        url = f"/fine_tuning/jobs/{fine_tuning_job_id}"

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

    async def cancel_fine_tuning_job(
        self,
        fine_tuning_job_id: str
    ) -> FineTuningJob:
        """Immediately cancel a fine-tune job."""
        url = f"/fine_tuning/jobs/{fine_tuning_job_id}/cancel"

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

        return response.json()

    async def list_fine_tuning_job_checkpoints(
        self,
        fine_tuning_job_id: str,
        after: str = None,
        limit: int = None
    ) -> Dict[str, Any]:
        """List checkpoints for a fine-tuning job."""
        url = f"/fine_tuning/jobs/{fine_tuning_job_id}/checkpoints"

        params = {
            "after": after,
            "limit": limit,
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

    async def list_fine_tuning_events(
        self,
        fine_tuning_job_id: str,
        after: str = None,
        limit: int = None
    ) -> Dict[str, Any]:
        """Get status updates for a fine-tuning job."""
        url = f"/fine_tuning/jobs/{fine_tuning_job_id}/events"

        params = {
            "after": after,
            "limit": limit,
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

    async def pause_fine_tuning_job(
        self,
        fine_tuning_job_id: str
    ) -> FineTuningJob:
        """Pause a fine-tune job."""
        url = f"/fine_tuning/jobs/{fine_tuning_job_id}/pause"

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

        return response.json()

    async def resume_fine_tuning_job(
        self,
        fine_tuning_job_id: str
    ) -> FineTuningJob:
        """Resume a fine-tune job."""
        url = f"/fine_tuning/jobs/{fine_tuning_job_id}/resume"

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

        return response.json()


class ImagesClient:
    def __init__(self, base_url: str, token: str):
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token}"}
        )

    async def create_image_edit(
        self,
        
    ) -> ImageGenerationResponse:
        """Creates an edited or extended image given one or more source images and a prompt. This endpoint only supports `gpt-image-1` and `dall-e-2`."""
        url = f"/images/edits"

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

        return response.json()

    async def create_image(
        self,
        body: Dict[str, Any]
    ) -> ImageGenerationResponse:
        """Creates an image given a prompt. [Learn more](https://platform.openai.com/docs/guides/images)."""
        url = f"/images/generations"

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

    async def create_image_variation(
        self,
        
    ) -> ImageGenerationResponse:
        """Creates a variation of a given image. This endpoint only supports `dall-e-2`."""
        url = f"/images/variations"

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

        return response.json()


class ModelsClient:
    def __init__(self, base_url: str, token: str):
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token}"}
        )

    async def list_models(
        self,
        
    ) -> Dict[str, Any]:
        """Lists the currently available models, and provides basic information about each one such as the owner and availability."""
        url = f"/models"

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

    async def retrieve_model(
        self,
        model: str
    ) -> Any:
        """Retrieves a model instance, providing basic information about the model such as the owner and permissioning."""
        url = f"/models/{model}"

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

    async def delete_model(
        self,
        model: str
    ) -> Dict[str, Any]:
        """Delete a fine-tuned model. You must have the Owner role in your organization to delete a model."""
        url = f"/models/{model}"

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

        return response.json()


class ModerationsClient:
    def __init__(self, base_url: str, token: str):
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token}"}
        )

    async def create_moderation(
        self,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Classifies if text and/or image inputs are potentially harmful. Learn
more in the [moderation guide](https://platform.openai.com/docs/guides/moderation)."""
        url = f"/moderations"

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


class AuditLogsClient:
    def __init__(self, base_url: str, token: str):
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token}"}
        )

    async def list_audit_logs(
        self,
        effective_at: Dict[str, Any] = None,
        project_ids: List[str] = None,
        event_types: List[Literal["api_key.created", "api_key.updated", "api_key.deleted", "certificate.created", "certificate.updated", "certificate.deleted", "certificates.activated", "certificates.deactivated", "checkpoint.permission.created", "checkpoint.permission.deleted", "external_key.registered", "external_key.removed", "group.created", "group.updated", "group.deleted", "invite.sent", "invite.accepted", "invite.deleted", "ip_allowlist.created", "ip_allowlist.updated", "ip_allowlist.deleted", "ip_allowlist.config.activated", "ip_allowlist.config.deactivated", "login.succeeded", "login.failed", "logout.succeeded", "logout.failed", "organization.updated", "project.created", "project.updated", "project.archived", "project.deleted", "rate_limit.updated", "rate_limit.deleted", "resource.deleted", "tunnel.created", "tunnel.updated", "tunnel.deleted", "role.created", "role.updated", "role.deleted", "role.assignment.created", "role.assignment.deleted", "scim.enabled", "scim.disabled", "service_account.created", "service_account.updated", "service_account.deleted", "user.added", "user.updated", "user.deleted"]] = None,
        actor_ids: List[str] = None,
        actor_emails: List[str] = None,
        resource_ids: List[str] = None,
        limit: int = None,
        after: str = None,
        before: str = None
    ) -> Dict[str, Any]:
        """List user actions and configuration changes within this organization."""
        url = f"/organization/audit_logs"

        params = {
            "effective_at": effective_at,
            "project_ids[]": project_ids,
            "event_types[]": event_types,
            "actor_ids[]": actor_ids,
            "actor_emails[]": actor_emails,
            "resource_ids[]": resource_ids,
            "limit": limit,
            "after": after,
            "before": before,
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


class CertificatesClient:
    def __init__(self, base_url: str, token: str):
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token}"}
        )

    async def list_organization_certificates(
        self,
        limit: int = None,
        after: str = None,
        order: Literal["asc", "desc"] = None
    ) -> Dict[str, Any]:
        """List uploaded certificates for this organization."""
        url = f"/organization/certificates"

        params = {
            "limit": limit,
            "after": after,
            "order": order,
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

    async def upload_certificate(
        self,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Upload a certificate to the organization. This does **not** automatically activate the certificate.

Organizations can upload up to 50 certificates."""
        url = f"/organization/certificates"

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

    async def activate_organization_certificates(
        self,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Activate certificates at the organization level.

You can atomically and idempotently activate up to 10 certificates at a time."""
        url = f"/organization/certificates/activate"

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

    async def deactivate_organization_certificates(
        self,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Deactivate certificates at the organization level.

You can atomically and idempotently deactivate up to 10 certificates at a time."""
        url = f"/organization/certificates/deactivate"

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

    async def get_certificate(
        self,
        certificate_id: str,
        include: List[Literal["content"]] = None
    ) -> Dict[str, Any]:
        """Get a certificate that has been uploaded to the organization.

You can get a certificate regardless of whether it is active or not."""
        url = f"/organization/certificates/{certificate_id}"

        params = {
            "include": include,
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

    async def modify_certificate(
        self,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Modify a certificate. Note that only the name can be modified."""
        url = f"/organization/certificates/{certificate_id}"

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

    async def delete_certificate(
        self,
        
    ) -> Dict[str, Any]:
        """Delete a certificate from the organization.

The certificate must be inactive for the organization and all projects."""
        url = f"/organization/certificates/{certificate_id}"

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

        return response.json()

    async def list_project_certificates(
        self,
        project_id: str,
        limit: int = None,
        after: str = None,
        order: Literal["asc", "desc"] = None
    ) -> Dict[str, Any]:
        """List certificates for this project."""
        url = f"/organization/projects/{project_id}/certificates"

        params = {
            "limit": limit,
            "after": after,
            "order": order,
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

    async def activate_project_certificates(
        self,
        project_id: str,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Activate certificates at the project level.

You can atomically and idempotently activate up to 10 certificates at a time."""
        url = f"/organization/projects/{project_id}/certificates/activate"

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

    async def deactivate_project_certificates(
        self,
        project_id: str,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Deactivate certificates at the project level. You can atomically and 
idempotently deactivate up to 10 certificates at a time."""
        url = f"/organization/projects/{project_id}/certificates/deactivate"

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


class UsageClient:
    def __init__(self, base_url: str, token: str):
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token}"}
        )

    async def usage_costs(
        self,
        start_time: int = None,
        end_time: int = None,
        bucket_width: Literal["1d"] = None,
        project_ids: List[str] = None,
        group_by: List[Literal["project_id", "line_item"]] = None,
        limit: int = None,
        page: str = None
    ) -> Dict[str, Any]:
        """Get costs details for the organization."""
        url = f"/organization/costs"

        params = {
            "start_time": start_time,
            "end_time": end_time,
            "bucket_width": bucket_width,
            "project_ids": project_ids,
            "group_by": group_by,
            "limit": limit,
            "page": page,
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

    async def usage_audio_speeches(
        self,
        start_time: int = None,
        end_time: int = None,
        bucket_width: Literal["1m", "1h", "1d"] = None,
        project_ids: List[str] = None,
        user_ids: List[str] = None,
        api_key_ids: List[str] = None,
        models: List[str] = None,
        group_by: List[Literal["project_id", "user_id", "api_key_id", "model"]] = None,
        limit: int = None,
        page: str = None
    ) -> Dict[str, Any]:
        """Get audio speeches usage details for the organization."""
        url = f"/organization/usage/audio_speeches"

        params = {
            "start_time": start_time,
            "end_time": end_time,
            "bucket_width": bucket_width,
            "project_ids": project_ids,
            "user_ids": user_ids,
            "api_key_ids": api_key_ids,
            "models": models,
            "group_by": group_by,
            "limit": limit,
            "page": page,
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

    async def usage_audio_transcriptions(
        self,
        start_time: int = None,
        end_time: int = None,
        bucket_width: Literal["1m", "1h", "1d"] = None,
        project_ids: List[str] = None,
        user_ids: List[str] = None,
        api_key_ids: List[str] = None,
        models: List[str] = None,
        group_by: List[Literal["project_id", "user_id", "api_key_id", "model"]] = None,
        limit: int = None,
        page: str = None
    ) -> Dict[str, Any]:
        """Get audio transcriptions usage details for the organization."""
        url = f"/organization/usage/audio_transcriptions"

        params = {
            "start_time": start_time,
            "end_time": end_time,
            "bucket_width": bucket_width,
            "project_ids": project_ids,
            "user_ids": user_ids,
            "api_key_ids": api_key_ids,
            "models": models,
            "group_by": group_by,
            "limit": limit,
            "page": page,
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

    async def usage_code_interpreter_sessions(
        self,
        start_time: int = None,
        end_time: int = None,
        bucket_width: Literal["1m", "1h", "1d"] = None,
        project_ids: List[str] = None,
        group_by: List[Literal["project_id"]] = None,
        limit: int = None,
        page: str = None
    ) -> Dict[str, Any]:
        """Get code interpreter sessions usage details for the organization."""
        url = f"/organization/usage/code_interpreter_sessions"

        params = {
            "start_time": start_time,
            "end_time": end_time,
            "bucket_width": bucket_width,
            "project_ids": project_ids,
            "group_by": group_by,
            "limit": limit,
            "page": page,
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

    async def usage_completions(
        self,
        start_time: int = None,
        end_time: int = None,
        bucket_width: Literal["1m", "1h", "1d"] = None,
        project_ids: List[str] = None,
        user_ids: List[str] = None,
        api_key_ids: List[str] = None,
        models: List[str] = None,
        batch: bool = None,
        group_by: List[Literal["project_id", "user_id", "api_key_id", "model", "batch", "service_tier"]] = None,
        limit: int = None,
        page: str = None
    ) -> Dict[str, Any]:
        """Get completions usage details for the organization."""
        url = f"/organization/usage/completions"

        params = {
            "start_time": start_time,
            "end_time": end_time,
            "bucket_width": bucket_width,
            "project_ids": project_ids,
            "user_ids": user_ids,
            "api_key_ids": api_key_ids,
            "models": models,
            "batch": batch,
            "group_by": group_by,
            "limit": limit,
            "page": page,
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

    async def usage_embeddings(
        self,
        start_time: int = None,
        end_time: int = None,
        bucket_width: Literal["1m", "1h", "1d"] = None,
        project_ids: List[str] = None,
        user_ids: List[str] = None,
        api_key_ids: List[str] = None,
        models: List[str] = None,
        group_by: List[Literal["project_id", "user_id", "api_key_id", "model"]] = None,
        limit: int = None,
        page: str = None
    ) -> Dict[str, Any]:
        """Get embeddings usage details for the organization."""
        url = f"/organization/usage/embeddings"

        params = {
            "start_time": start_time,
            "end_time": end_time,
            "bucket_width": bucket_width,
            "project_ids": project_ids,
            "user_ids": user_ids,
            "api_key_ids": api_key_ids,
            "models": models,
            "group_by": group_by,
            "limit": limit,
            "page": page,
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

    async def usage_images(
        self,
        start_time: int = None,
        end_time: int = None,
        bucket_width: Literal["1m", "1h", "1d"] = None,
        sources: List[Literal["image.generation", "image.edit", "image.variation"]] = None,
        sizes: List[Literal["256x256", "512x512", "1024x1024", "1792x1792", "1024x1792"]] = None,
        project_ids: List[str] = None,
        user_ids: List[str] = None,
        api_key_ids: List[str] = None,
        models: List[str] = None,
        group_by: List[Literal["project_id", "user_id", "api_key_id", "model", "size", "source"]] = None,
        limit: int = None,
        page: str = None
    ) -> Dict[str, Any]:
        """Get images usage details for the organization."""
        url = f"/organization/usage/images"

        params = {
            "start_time": start_time,
            "end_time": end_time,
            "bucket_width": bucket_width,
            "sources": sources,
            "sizes": sizes,
            "project_ids": project_ids,
            "user_ids": user_ids,
            "api_key_ids": api_key_ids,
            "models": models,
            "group_by": group_by,
            "limit": limit,
            "page": page,
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

    async def usage_moderations(
        self,
        start_time: int = None,
        end_time: int = None,
        bucket_width: Literal["1m", "1h", "1d"] = None,
        project_ids: List[str] = None,
        user_ids: List[str] = None,
        api_key_ids: List[str] = None,
        models: List[str] = None,
        group_by: List[Literal["project_id", "user_id", "api_key_id", "model"]] = None,
        limit: int = None,
        page: str = None
    ) -> Dict[str, Any]:
        """Get moderations usage details for the organization."""
        url = f"/organization/usage/moderations"

        params = {
            "start_time": start_time,
            "end_time": end_time,
            "bucket_width": bucket_width,
            "project_ids": project_ids,
            "user_ids": user_ids,
            "api_key_ids": api_key_ids,
            "models": models,
            "group_by": group_by,
            "limit": limit,
            "page": page,
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

    async def usage_vector_stores(
        self,
        start_time: int = None,
        end_time: int = None,
        bucket_width: Literal["1m", "1h", "1d"] = None,
        project_ids: List[str] = None,
        group_by: List[Literal["project_id"]] = None,
        limit: int = None,
        page: str = None
    ) -> Dict[str, Any]:
        """Get vector stores usage details for the organization."""
        url = f"/organization/usage/vector_stores"

        params = {
            "start_time": start_time,
            "end_time": end_time,
            "bucket_width": bucket_width,
            "project_ids": project_ids,
            "group_by": group_by,
            "limit": limit,
            "page": page,
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


class GroupsClient:
    def __init__(self, base_url: str, token: str):
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token}"}
        )

    async def list_groups(
        self,
        limit: int = None,
        after: str = None,
        order: Literal["asc", "desc"] = None
    ) -> Dict[str, Any]:
        """Lists all groups in the organization."""
        url = f"/organization/groups"

        params = {
            "limit": limit,
            "after": after,
            "order": order,
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

    async def create_group(
        self,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Creates a new group in the organization."""
        url = f"/organization/groups"

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

    async def update_group(
        self,
        group_id: str,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Updates a group's information."""
        url = f"/organization/groups/{group_id}"

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

    async def delete_group(
        self,
        group_id: str
    ) -> Dict[str, Any]:
        """Deletes a group from the organization."""
        url = f"/organization/groups/{group_id}"

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

        return response.json()


class GroupOrganizationRoleAssignmentsClient:
    def __init__(self, base_url: str, token: str):
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token}"}
        )

    async def list_group_role_assignments(
        self,
        group_id: str,
        limit: int = None,
        after: str = None,
        order: Literal["asc", "desc"] = None
    ) -> Dict[str, Any]:
        """Lists the organization roles assigned to a group within the organization."""
        url = f"/organization/groups/{group_id}/roles"

        params = {
            "limit": limit,
            "after": after,
            "order": order,
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

    async def assign_group_role(
        self,
        group_id: str,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assigns an organization role to a group within the organization."""
        url = f"/organization/groups/{group_id}/roles"

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

    async def unassign_group_role(
        self,
        group_id: str,
        role_id: str
    ) -> Dict[str, Any]:
        """Unassigns an organization role from a group within the organization."""
        url = f"/organization/groups/{group_id}/roles/{role_id}"

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

        return response.json()


class GroupUsersClient:
    def __init__(self, base_url: str, token: str):
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token}"}
        )

    async def list_group_users(
        self,
        group_id: str,
        limit: int = None,
        after: str = None,
        order: Literal["asc", "desc"] = None
    ) -> Dict[str, Any]:
        """Lists the users assigned to a group."""
        url = f"/organization/groups/{group_id}/users"

        params = {
            "limit": limit,
            "after": after,
            "order": order,
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

    async def add_group_user(
        self,
        group_id: str,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Adds a user to a group."""
        url = f"/organization/groups/{group_id}/users"

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

    async def remove_group_user(
        self,
        group_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Removes a user from a group."""
        url = f"/organization/groups/{group_id}/users/{user_id}"

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

        return response.json()


class InvitesClient:
    def __init__(self, base_url: str, token: str):
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token}"}
        )

    async def list_invites(
        self,
        limit: int = None,
        after: str = None
    ) -> Dict[str, Any]:
        """Returns a list of invites in the organization."""
        url = f"/organization/invites"

        params = {
            "limit": limit,
            "after": after,
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

    async def invite_user(
        self,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create an invite for a user to the organization. The invite must be accepted by the user before they have access to the organization."""
        url = f"/organization/invites"

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

    async def retrieve_invite(
        self,
        invite_id: str
    ) -> Dict[str, Any]:
        """Retrieves an invite."""
        url = f"/organization/invites/{invite_id}"

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

    async def delete_invite(
        self,
        invite_id: str
    ) -> Dict[str, Any]:
        """Delete an invite. If the invite has already been accepted, it cannot be deleted."""
        url = f"/organization/invites/{invite_id}"

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

        return response.json()


class ProjectsClient:
    def __init__(self, base_url: str, token: str):
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token}"}
        )

    async def list_projects(
        self,
        limit: int = None,
        after: str = None,
        include_archived: bool = None
    ) -> Dict[str, Any]:
        """Returns a list of projects."""
        url = f"/organization/projects"

        params = {
            "limit": limit,
            "after": after,
            "include_archived": include_archived,
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

    async def create_project(
        self,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new project in the organization. Projects can be created and archived, but cannot be deleted."""
        url = f"/organization/projects"

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

    async def retrieve_project(
        self,
        project_id: str
    ) -> Dict[str, Any]:
        """Retrieves a project."""
        url = f"/organization/projects/{project_id}"

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

    async def modify_project(
        self,
        project_id: str,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Modifies a project in the organization."""
        url = f"/organization/projects/{project_id}"

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

    async def list_project_api_keys(
        self,
        project_id: str,
        limit: int = None,
        after: str = None
    ) -> Dict[str, Any]:
        """Returns a list of API keys in the project."""
        url = f"/organization/projects/{project_id}/api_keys"

        params = {
            "limit": limit,
            "after": after,
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

    async def retrieve_project_api_key(
        self,
        project_id: str,
        key_id: str
    ) -> Dict[str, Any]:
        """Retrieves an API key in the project."""
        url = f"/organization/projects/{project_id}/api_keys/{key_id}"

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

    async def delete_project_api_key(
        self,
        project_id: str,
        key_id: str
    ) -> Dict[str, Any]:
        """Deletes an API key from the project."""
        url = f"/organization/projects/{project_id}/api_keys/{key_id}"

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

        return response.json()

    async def archive_project(
        self,
        project_id: str
    ) -> Dict[str, Any]:
        """Archives a project in the organization. Archived projects cannot be used or updated."""
        url = f"/organization/projects/{project_id}/archive"

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

        return response.json()

    async def list_project_rate_limits(
        self,
        project_id: str,
        limit: int = None,
        after: str = None,
        before: str = None
    ) -> Dict[str, Any]:
        """Returns the rate limits per model for a project."""
        url = f"/organization/projects/{project_id}/rate_limits"

        params = {
            "limit": limit,
            "after": after,
            "before": before,
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

    async def update_project_rate_limits(
        self,
        project_id: str,
        rate_limit_id: str,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Updates a project rate limit."""
        url = f"/organization/projects/{project_id}/rate_limits/{rate_limit_id}"

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

    async def list_project_service_accounts(
        self,
        project_id: str,
        limit: int = None,
        after: str = None
    ) -> Dict[str, Any]:
        """Returns a list of service accounts in the project."""
        url = f"/organization/projects/{project_id}/service_accounts"

        params = {
            "limit": limit,
            "after": after,
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

    async def create_project_service_account(
        self,
        project_id: str,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Creates a new service account in the project. This also returns an unredacted API key for the service account."""
        url = f"/organization/projects/{project_id}/service_accounts"

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

    async def retrieve_project_service_account(
        self,
        project_id: str,
        service_account_id: str
    ) -> Dict[str, Any]:
        """Retrieves a service account in the project."""
        url = f"/organization/projects/{project_id}/service_accounts/{service_account_id}"

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

    async def delete_project_service_account(
        self,
        project_id: str,
        service_account_id: str
    ) -> Dict[str, Any]:
        """Deletes a service account from the project."""
        url = f"/organization/projects/{project_id}/service_accounts/{service_account_id}"

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

        return response.json()

    async def list_project_users(
        self,
        project_id: str,
        limit: int = None,
        after: str = None
    ) -> Dict[str, Any]:
        """Returns a list of users in the project."""
        url = f"/organization/projects/{project_id}/users"

        params = {
            "limit": limit,
            "after": after,
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

    async def create_project_user(
        self,
        project_id: str,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Adds a user to the project. Users must already be members of the organization to be added to a project."""
        url = f"/organization/projects/{project_id}/users"

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

    async def retrieve_project_user(
        self,
        project_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Retrieves a user in the project."""
        url = f"/organization/projects/{project_id}/users/{user_id}"

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

    async def modify_project_user(
        self,
        project_id: str,
        user_id: str,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Modifies a user's role in the project."""
        url = f"/organization/projects/{project_id}/users/{user_id}"

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

    async def delete_project_user(
        self,
        project_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Deletes a user from the project."""
        url = f"/organization/projects/{project_id}/users/{user_id}"

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

        return response.json()


class ProjectGroupsClient:
    def __init__(self, base_url: str, token: str):
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token}"}
        )

    async def list_project_groups(
        self,
        project_id: str,
        limit: int = None,
        after: str = None,
        order: Literal["asc", "desc"] = None
    ) -> Dict[str, Any]:
        """Lists the groups that have access to a project."""
        url = f"/organization/projects/{project_id}/groups"

        params = {
            "limit": limit,
            "after": after,
            "order": order,
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

    async def add_project_group(
        self,
        project_id: str,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Grants a group access to a project."""
        url = f"/organization/projects/{project_id}/groups"

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

    async def remove_project_group(
        self,
        project_id: str,
        group_id: str
    ) -> Dict[str, Any]:
        """Revokes a group's access to a project."""
        url = f"/organization/projects/{project_id}/groups/{group_id}"

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

        return response.json()


class RolesClient:
    def __init__(self, base_url: str, token: str):
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token}"}
        )

    async def list_roles(
        self,
        limit: int = None,
        after: str = None,
        order: Literal["asc", "desc"] = None
    ) -> Dict[str, Any]:
        """Lists the roles configured for the organization."""
        url = f"/organization/roles"

        params = {
            "limit": limit,
            "after": after,
            "order": order,
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

    async def create_role(
        self,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Creates a custom role for the organization."""
        url = f"/organization/roles"

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

    async def update_role(
        self,
        role_id: str,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Updates an existing organization role."""
        url = f"/organization/roles/{role_id}"

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

    async def delete_role(
        self,
        role_id: str
    ) -> Dict[str, Any]:
        """Deletes a custom role from the organization."""
        url = f"/organization/roles/{role_id}"

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

        return response.json()

    async def list_project_roles(
        self,
        project_id: str,
        limit: int = None,
        after: str = None,
        order: Literal["asc", "desc"] = None
    ) -> Dict[str, Any]:
        """Lists the roles configured for a project."""
        url = f"/projects/{project_id}/roles"

        params = {
            "limit": limit,
            "after": after,
            "order": order,
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

    async def create_project_role(
        self,
        project_id: str,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Creates a custom role for a project."""
        url = f"/projects/{project_id}/roles"

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

    async def update_project_role(
        self,
        project_id: str,
        role_id: str,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Updates an existing project role."""
        url = f"/projects/{project_id}/roles/{role_id}"

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

    async def delete_project_role(
        self,
        project_id: str,
        role_id: str
    ) -> Dict[str, Any]:
        """Deletes a custom role from a project."""
        url = f"/projects/{project_id}/roles/{role_id}"

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

        return response.json()


class UsersClient:
    def __init__(self, base_url: str, token: str):
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token}"}
        )

    async def list_users(
        self,
        limit: int = None,
        after: str = None,
        emails: List[str] = None
    ) -> Dict[str, Any]:
        """Lists all of the users in the organization."""
        url = f"/organization/users"

        params = {
            "limit": limit,
            "after": after,
            "emails": emails,
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

    async def retrieve_user(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """Retrieves a user by their identifier."""
        url = f"/organization/users/{user_id}"

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

    async def modify_user(
        self,
        user_id: str,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Modifies a user's role in the organization."""
        url = f"/organization/users/{user_id}"

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

    async def delete_user(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """Deletes a user from the organization."""
        url = f"/organization/users/{user_id}"

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

        return response.json()


class UserOrganizationRoleAssignmentsClient:
    def __init__(self, base_url: str, token: str):
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token}"}
        )

    async def list_user_role_assignments(
        self,
        user_id: str,
        limit: int = None,
        after: str = None,
        order: Literal["asc", "desc"] = None
    ) -> Dict[str, Any]:
        """Lists the organization roles assigned to a user within the organization."""
        url = f"/organization/users/{user_id}/roles"

        params = {
            "limit": limit,
            "after": after,
            "order": order,
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

    async def assign_user_role(
        self,
        user_id: str,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assigns an organization role to a user within the organization."""
        url = f"/organization/users/{user_id}/roles"

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

    async def unassign_user_role(
        self,
        user_id: str,
        role_id: str
    ) -> Dict[str, Any]:
        """Unassigns an organization role from a user within the organization."""
        url = f"/organization/users/{user_id}/roles/{role_id}"

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

        return response.json()


class ProjectGroupRoleAssignmentsClient:
    def __init__(self, base_url: str, token: str):
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token}"}
        )

    async def list_project_group_role_assignments(
        self,
        project_id: str,
        group_id: str,
        limit: int = None,
        after: str = None,
        order: Literal["asc", "desc"] = None
    ) -> Dict[str, Any]:
        """Lists the project roles assigned to a group within a project."""
        url = f"/projects/{project_id}/groups/{group_id}/roles"

        params = {
            "limit": limit,
            "after": after,
            "order": order,
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

    async def assign_project_group_role(
        self,
        project_id: str,
        group_id: str,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assigns a project role to a group within a project."""
        url = f"/projects/{project_id}/groups/{group_id}/roles"

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

    async def unassign_project_group_role(
        self,
        project_id: str,
        group_id: str,
        role_id: str
    ) -> Dict[str, Any]:
        """Unassigns a project role from a group within a project."""
        url = f"/projects/{project_id}/groups/{group_id}/roles/{role_id}"

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

        return response.json()


class ProjectUserRoleAssignmentsClient:
    def __init__(self, base_url: str, token: str):
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token}"}
        )

    async def list_project_user_role_assignments(
        self,
        project_id: str,
        user_id: str,
        limit: int = None,
        after: str = None,
        order: Literal["asc", "desc"] = None
    ) -> Dict[str, Any]:
        """Lists the project roles assigned to a user within a project."""
        url = f"/projects/{project_id}/users/{user_id}/roles"

        params = {
            "limit": limit,
            "after": after,
            "order": order,
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

    async def assign_project_user_role(
        self,
        project_id: str,
        user_id: str,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assigns a project role to a user within a project."""
        url = f"/projects/{project_id}/users/{user_id}/roles"

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

    async def unassign_project_user_role(
        self,
        project_id: str,
        user_id: str,
        role_id: str
    ) -> Dict[str, Any]:
        """Unassigns a project role from a user within a project."""
        url = f"/projects/{project_id}/users/{user_id}/roles/{role_id}"

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

        return response.json()


class RealtimeClient:
    def __init__(self, base_url: str, token: str):
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token}"}
        )

    async def create_realtime_call(
        self,
        
    ) -> Dict[str, Any]:
        """Create a new Realtime API call over WebRTC and receive the SDP answer needed
to complete the peer connection."""
        url = f"/realtime/calls"

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

    async def accept_realtime_call(
        self,
        call_id: str,
        body: RealtimeSessionConfiguration
    ) -> Dict[str, Any]:
        """Accept an incoming SIP call and configure the realtime session that will
handle it."""
        url = f"/realtime/calls/{call_id}/accept"

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

    async def hangup_realtime_call(
        self,
        call_id: str
    ) -> Dict[str, Any]:
        """End an active Realtime API call, whether it was initiated over SIP or
WebRTC."""
        url = f"/realtime/calls/{call_id}/hangup"

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

    async def refer_realtime_call(
        self,
        call_id: str,
        body: RealtimeCallReferRequest
    ) -> Dict[str, Any]:
        """Transfer an active SIP call to a new destination using the SIP REFER verb."""
        url = f"/realtime/calls/{call_id}/refer"

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

    async def reject_realtime_call(
        self,
        call_id: str,
        body: RealtimeCallRejectRequest
    ) -> Dict[str, Any]:
        """Decline an incoming SIP call by returning a SIP status code to the caller."""
        url = f"/realtime/calls/{call_id}/reject"

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

    async def create_realtime_client_secret(
        self,
        body: RealtimeClientSecretCreationRequest
    ) -> RealtimeSessionAndClientSecret:
        """Create a Realtime client secret with an associated session configuration."""
        url = f"/realtime/client_secrets"

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

    async def create_realtime_session(
        self,
        body: Dict[str, Any]
    ) -> RealtimeSessionConfigurationObject:
        """Create an ephemeral API token for use in client-side applications with the
Realtime API. Can be configured with the same session parameters as the
`session.update` client event.

It responds with a session object, plus a `client_secret` key which contains
a usable ephemeral API token that can be used to authenticate browser clients
for the Realtime API."""
        url = f"/realtime/sessions"

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

    async def create_realtime_transcription_session(
        self,
        body: RealtimeTranscriptionSessionConfiguration
    ) -> Dict[str, Any]:
        """Create an ephemeral API token for use in client-side applications with the
Realtime API specifically for realtime transcriptions. 
Can be configured with the same session parameters as the `transcription_session.update` client event.

It responds with a session object, plus a `client_secret` key which contains
a usable ephemeral API token that can be used to authenticate browser clients
for the Realtime API."""
        url = f"/realtime/transcription_sessions"

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


class ResponsesClient:
    def __init__(self, base_url: str, token: str):
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token}"}
        )

    async def create_response(
        self,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Creates a model response. Provide [text](https://platform.openai.com/docs/guides/text) or
[image](https://platform.openai.com/docs/guides/images) inputs to generate [text](https://platform.openai.com/docs/guides/text)
or [JSON](https://platform.openai.com/docs/guides/structured-outputs) outputs. Have the model call
your own [custom code](https://platform.openai.com/docs/guides/function-calling) or use built-in
[tools](https://platform.openai.com/docs/guides/tools) like [web search](https://platform.openai.com/docs/guides/tools-web-search)
or [file search](https://platform.openai.com/docs/guides/tools-file-search) to use your own data
as input for the model's response."""
        url = f"/responses"

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

    async def get_response(
        self,
        response_id: str,
        include: List[Literal["file_search_call.results", "web_search_call.results", "web_search_call.action.sources", "message.input_image.image_url", "computer_call_output.output.image_url", "code_interpreter_call.outputs", "reasoning.encrypted_content", "message.output_text.logprobs"]] = None,
        stream: bool = None,
        starting_after: int = None,
        include_obfuscation: bool = None
    ) -> Dict[str, Any]:
        """Retrieves a model response with the given ID."""
        url = f"/responses/{response_id}"

        params = {
            "include": include,
            "stream": stream,
            "starting_after": starting_after,
            "include_obfuscation": include_obfuscation,
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

    async def delete_response(
        self,
        response_id: str
    ) -> Dict[str, Any]:
        """Deletes a model response with the given ID."""
        url = f"/responses/{response_id}"

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

    async def cancel_response(
        self,
        response_id: str
    ) -> Dict[str, Any]:
        """Cancels a model response with the given ID. Only responses created with
the `background` parameter set to `true` can be cancelled. 
[Learn more](https://platform.openai.com/docs/guides/background)."""
        url = f"/responses/{response_id}/cancel"

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

        return response.json()

    async def list_input_items(
        self,
        response_id: str,
        limit: int = None,
        order: Literal["asc", "desc"] = None,
        after: str = None,
        include: List[Literal["file_search_call.results", "web_search_call.results", "web_search_call.action.sources", "message.input_image.image_url", "computer_call_output.output.image_url", "code_interpreter_call.outputs", "reasoning.encrypted_content", "message.output_text.logprobs"]] = None
    ) -> Dict[str, Any]:
        """Returns a list of input items for a given response."""
        url = f"/responses/{response_id}/input_items"

        params = {
            "limit": limit,
            "order": order,
            "after": after,
            "include": include,
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


class UploadsClient:
    def __init__(self, base_url: str, token: str):
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token}"}
        )

    async def create_upload(
        self,
        body: Dict[str, Any]
    ) -> Upload:
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
        url = f"/uploads"

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

    async def cancel_upload(
        self,
        upload_id: str
    ) -> Upload:
        """Cancels the Upload. No Parts may be added after an Upload is cancelled."""
        url = f"/uploads/{upload_id}/cancel"

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

        return response.json()

    async def complete_upload(
        self,
        upload_id: str,
        body: Dict[str, Any]
    ) -> Upload:
        """Completes the [Upload](https://platform.openai.com/docs/api-reference/uploads/object). 

Within the returned Upload object, there is a nested [File](https://platform.openai.com/docs/api-reference/files/object) object that is ready to use in the rest of the platform.

You can specify the order of the Parts by passing in an ordered list of the Part IDs.

The number of bytes uploaded upon completion must match the number of bytes initially specified when creating the Upload object. No Parts may be added after an Upload is completed."""
        url = f"/uploads/{upload_id}/complete"

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

    async def add_upload_part(
        self,
        upload_id: str
    ) -> UploadPart:
        """Adds a [Part](https://platform.openai.com/docs/api-reference/uploads/part-object) to an [Upload](https://platform.openai.com/docs/api-reference/uploads/object) object. A Part represents a chunk of bytes from the file you are trying to upload. 

Each Part can be at most 64 MB, and you can add Parts until you hit the Upload maximum of 8 GB.

It is possible to add multiple Parts in parallel. You can decide the intended order of the Parts when you [complete the Upload](https://platform.openai.com/docs/api-reference/uploads/complete)."""
        url = f"/uploads/{upload_id}/parts"

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

        return response.json()


class VectorStoresClient:
    def __init__(self, base_url: str, token: str):
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token}"}
        )

    async def list_vector_stores(
        self,
        limit: int = None,
        order: Literal["asc", "desc"] = None,
        after: str = None,
        before: str = None
    ) -> Any:
        """Returns a list of vector stores."""
        url = f"/vector_stores"

        params = {
            "limit": limit,
            "order": order,
            "after": after,
            "before": before,
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

    async def create_vector_store(
        self,
        body: Dict[str, Any]
    ) -> VectorStore:
        """Create a vector store."""
        url = f"/vector_stores"

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

    async def get_vector_store(
        self,
        vector_store_id: str
    ) -> VectorStore:
        """Retrieves a vector store."""
        url = f"/vector_stores/{vector_store_id}"

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

    async def modify_vector_store(
        self,
        vector_store_id: str,
        body: Dict[str, Any]
    ) -> VectorStore:
        """Modifies a vector store."""
        url = f"/vector_stores/{vector_store_id}"

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

    async def delete_vector_store(
        self,
        vector_store_id: str
    ) -> Dict[str, Any]:
        """Delete a vector store."""
        url = f"/vector_stores/{vector_store_id}"

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

        return response.json()

    async def create_vector_store_file_batch(
        self,
        vector_store_id: str,
        body: Dict[str, Any]
    ) -> VectorStoreFileBatch:
        """Create a vector store file batch."""
        url = f"/vector_stores/{vector_store_id}/file_batches"

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

    async def get_vector_store_file_batch(
        self,
        vector_store_id: str,
        batch_id: str
    ) -> VectorStoreFileBatch:
        """Retrieves a vector store file batch."""
        url = f"/vector_stores/{vector_store_id}/file_batches/{batch_id}"

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

    async def cancel_vector_store_file_batch(
        self,
        vector_store_id: str,
        batch_id: str
    ) -> VectorStoreFileBatch:
        """Cancel a vector store file batch. This attempts to cancel the processing of files in this batch as soon as possible."""
        url = f"/vector_stores/{vector_store_id}/file_batches/{batch_id}/cancel"

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

        return response.json()

    async def list_files_in_vector_store_batch(
        self,
        vector_store_id: str,
        batch_id: str,
        limit: int = None,
        order: Literal["asc", "desc"] = None,
        after: str = None,
        before: str = None,
        filter: Literal["in_progress", "completed", "failed", "cancelled"] = None
    ) -> Any:
        """Returns a list of vector store files in a batch."""
        url = f"/vector_stores/{vector_store_id}/file_batches/{batch_id}/files"

        params = {
            "limit": limit,
            "order": order,
            "after": after,
            "before": before,
            "filter": filter,
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

    async def list_vector_store_files(
        self,
        vector_store_id: str,
        limit: int = None,
        order: Literal["asc", "desc"] = None,
        after: str = None,
        before: str = None,
        filter: Literal["in_progress", "completed", "failed", "cancelled"] = None
    ) -> Any:
        """Returns a list of vector store files."""
        url = f"/vector_stores/{vector_store_id}/files"

        params = {
            "limit": limit,
            "order": order,
            "after": after,
            "before": before,
            "filter": filter,
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

    async def create_vector_store_file(
        self,
        vector_store_id: str,
        body: Dict[str, Any]
    ) -> VectorStoreFiles:
        """Create a vector store file by attaching a [File](https://platform.openai.com/docs/api-reference/files) to a [vector store](https://platform.openai.com/docs/api-reference/vector-stores/object)."""
        url = f"/vector_stores/{vector_store_id}/files"

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

    async def get_vector_store_file(
        self,
        vector_store_id: str,
        file_id: str
    ) -> VectorStoreFiles:
        """Retrieves a vector store file."""
        url = f"/vector_stores/{vector_store_id}/files/{file_id}"

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

    async def update_vector_store_file_attributes(
        self,
        vector_store_id: str,
        file_id: str,
        body: Dict[str, Any]
    ) -> VectorStoreFiles:
        """Update attributes on a vector store file."""
        url = f"/vector_stores/{vector_store_id}/files/{file_id}"

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

    async def delete_vector_store_file(
        self,
        vector_store_id: str,
        file_id: str
    ) -> Dict[str, Any]:
        """Delete a vector store file. This will remove the file from the vector store but the file itself will not be deleted. To delete the file, use the [delete file](https://platform.openai.com/docs/api-reference/files/delete) endpoint."""
        url = f"/vector_stores/{vector_store_id}/files/{file_id}"

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

        return response.json()

    async def retrieve_vector_store_file_content(
        self,
        vector_store_id: str,
        file_id: str
    ) -> Dict[str, Any]:
        """Retrieve the parsed contents of a vector store file."""
        url = f"/vector_stores/{vector_store_id}/files/{file_id}/content"

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

    async def search_vector_store(
        self,
        vector_store_id: str,
        body: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Search a vector store for relevant chunks based on a query and file attributes filter."""
        url = f"/vector_stores/{vector_store_id}/search"

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


class VideosClient:
    def __init__(self, base_url: str, token: str):
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token}"}
        )

    async def list_videos(
        self,
        limit: int = None,
        order: Literal["asc", "desc"] = None,
        after: str = None
    ) -> Dict[str, Any]:
        """List videos"""
        url = f"/videos"

        params = {
            "limit": limit,
            "order": order,
            "after": after,
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

    async def create_video(
        self,
        body: CreateVideoRequest
    ) -> VideoJob:
        """Create a video"""
        url = f"/videos"

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

    async def get_video(
        self,
        video_id: str
    ) -> VideoJob:
        """Retrieve a video"""
        url = f"/videos/{video_id}"

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

    async def delete_video(
        self,
        video_id: str
    ) -> DeletedVideoResponse:
        """Delete a video"""
        url = f"/videos/{video_id}"

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

        return response.json()

    async def retrieve_video_content(
        self,
        video_id: str,
        variant: Literal["video", "thumbnail", "spritesheet"] = None
    ) -> str:
        """Download video content"""
        url = f"/videos/{video_id}/content"

        params = {
            "variant": variant,
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

    async def create_video_remix(
        self,
        video_id: str,
        body: CreateVideoRemixRequest
    ) -> VideoJob:
        """Create a video remix"""
        url = f"/videos/{video_id}/remix"

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

