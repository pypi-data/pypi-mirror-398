"""
Layer 1 Agent: Environment-based primitives wrapper for openai
Composes RawAgent and provides access to Layer 1 primitives (structured helpers).
Automatically loads credentials from environment variables for easy integration
with AI Agent frameworks (LangChain, CrewAI, Madison, etc.)
"""
import os
from typing import Any, Dict, List, Literal, Optional, Type, TypeVar, Union
from pydantic import BaseModel
from .raw_agent import RawAgent
from .primitives import OpenaiPrimitives

T = TypeVar('T', bound=BaseModel)

class PrimitivesAgent:
    """
    Agent-ready wrapper for openai primitives (Layer 1).

    Composes RawAgent and provides access to structured helper methods.

    Automatically loads credentials from environment variables:
    - OPENAI_API_KEY: API key/token for authentication
    - OPENAI_BASE_URL: Base URL for the API (optional, has default)

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
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.base_url = base_url or os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")

        if not self.api_key:
            raise ValueError(
                "API key is required. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter."
            )

        # Initialize RawAgent (Layer 0)
        self.raw = RawAgent(api_key=self.api_key, base_url=self.base_url)

        # Initialize Primitives (Layer 1)
        # Primitives need the raw client instances
        self._primitives = OpenaiPrimitives(
            chat_client=self.raw._chat,
            embeddings_client=self.raw._embeddings
        )

    # ─────────────────────────────────────────────────────────────────────────────
    # Primitive operations (Layer 1)
    # ─────────────────────────────────────────────────────────────────────────────

    async def list_chat_completions_structured(
        self,
        model: str = None, metadata: Dict[str, str] = None, after: str = None, limit: int = None, order: Literal["asc", "desc"] = None,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        List stored Chat Completions. Only Chat Completions that have been stored
with the `store` parameter set to `true` will be returned.
        Args:
            model: The model used to generate the Chat Completions.
            metadata: A list of metadata keys to filter the Chat Completions by. Example:

`metadata[key1]=value1&metadata[key2]=value2`
            after: Identifier for the last chat completion from the previous pagination request.
            limit: Number of Chat Completions to retrieve.
            order: Sort order for Chat Completions by timestamp. Use `asc` for ascending order or `desc` for descending order. Defaults to `asc`.
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        return await self._primitives.list_chat_completions_structured(
            model=model, metadata=metadata, after=after, limit=limit, order=order,
            response_model=response_model
        )

    async def create_chat_completion_structured(
        self,
        body: Dict[str, Any],
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        **Starting a new project?** We recommend trying [Responses](https://platform.openai.com/docs/api-reference/responses) 
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
[refer to the reasoning guide](https://platform.openai.com/docs/guides/reasoning).
        Args:
            body: Request body
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        return await self._primitives.create_chat_completion_structured(
            body=body,
            response_model=response_model
        )

    async def get_chat_completion_structured(
        self,
        completion_id: str,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Get a stored chat completion. Only Chat Completions that have been created
with the `store` parameter set to `true` will be returned.
        Args:
            completion_id: The ID of the chat completion to retrieve.
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        return await self._primitives.get_chat_completion_structured(
            completion_id=completion_id,
            response_model=response_model
        )

    async def update_chat_completion_structured(
        self,
        completion_id: str, body: Dict[str, Any],
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Modify a stored chat completion. Only Chat Completions that have been
created with the `store` parameter set to `true` can be modified. Currently,
the only supported modification is to update the `metadata` field.
        Args:
            completion_id: The ID of the chat completion to update.
            body: Request body
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        return await self._primitives.update_chat_completion_structured(
            completion_id=completion_id, body=body,
            response_model=response_model
        )

    async def delete_chat_completion_structured(
        self,
        completion_id: str,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Delete a stored chat completion. Only Chat Completions that have been
created with the `store` parameter set to `true` can be deleted.
        Args:
            completion_id: The ID of the chat completion to delete.
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        return await self._primitives.delete_chat_completion_structured(
            completion_id=completion_id,
            response_model=response_model
        )

    async def get_chat_completion_messages_structured(
        self,
        completion_id: str, after: str = None, limit: int = None, order: Literal["asc", "desc"] = None,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Get the messages in a stored chat completion. Only Chat Completions that
have been created with the `store` parameter set to `true` will be
returned.
        Args:
            completion_id: The ID of the chat completion to retrieve messages from.
            after: Identifier for the last message from the previous pagination request.
            limit: Number of messages to retrieve.
            order: Sort order for messages by timestamp. Use `asc` for ascending order or `desc` for descending order. Defaults to `asc`.
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        return await self._primitives.get_chat_completion_messages_structured(
            completion_id=completion_id, after=after, limit=limit, order=order,
            response_model=response_model
        )

    async def create_embedding_structured(
        self,
        body: Dict[str, Any],
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Creates an embedding vector representing the input text.
        Args:
            body: Request body
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        return await self._primitives.create_embedding_structured(
            body=body,
            response_model=response_model
        )
