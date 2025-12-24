"""
Layer 1: Primitives - Opinionated helper methods for openai
These helpers provide higher-level abstractions over the raw API client.
Each method wraps a Layer 0 operation with the _structured suffix.
"""
from typing import Any, Dict, List, Literal, Optional, Type, TypeVar, Union
from pydantic import BaseModel
from .raw import *

T = TypeVar('T', bound=BaseModel)


class OpenaiPrimitives:
    """
    Opinionated helper methods for openai.

    Generated Layer 1 primitives for 7 operations.
    """

    def __init__(self, chat_client: ChatClient, embeddings_client: EmbeddingsClient):
        self.chat_client = chat_client
        self.embeddings_client = embeddings_client

    async def list_chat_completions_structured(
        self,
        model: str = None,
        metadata: Dict[str, str] = None,
        after: str = None,
        limit: int = None,
        order: Literal["asc", "desc"] = None,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        List stored Chat Completions. Only Chat Completions that have been stored
with the `store` parameter set to `true` will be returned.
        This is a Layer 1 primitive that wraps the Layer 0 list_chat_completions() method.
        If response_model is provided, the response will be parsed into that Pydantic model.

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
        # Call Layer 0 method
        response = await self.chat_client.list_chat_completions(
            model=model,
            metadata=metadata,
            after=after,
            limit=limit,
            order=order
        )

        # If no response model specified, return raw response
        if response_model is None:
            return response

        # Parse response into Pydantic model
        try:
            return response_model.model_validate(response)
        except Exception as e:
            raise ValueError(f"Failed to parse response as {response_model.__name__}: {e}")

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
        This is a Layer 1 primitive that wraps the Layer 0 create_chat_completion() method.
        If response_model is provided, the response will be parsed into that Pydantic model.

        Args:
            body: Request body
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        # Call Layer 0 method
        response = await self.chat_client.create_chat_completion(
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

    async def get_chat_completion_structured(
        self,
        completion_id: str,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Get a stored chat completion. Only Chat Completions that have been created
with the `store` parameter set to `true` will be returned.
        This is a Layer 1 primitive that wraps the Layer 0 get_chat_completion() method.
        If response_model is provided, the response will be parsed into that Pydantic model.

        Args:
            completion_id: The ID of the chat completion to retrieve.
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        # Call Layer 0 method
        response = await self.chat_client.get_chat_completion(
            completion_id=completion_id
        )

        # If no response model specified, return raw response
        if response_model is None:
            return response

        # Parse response into Pydantic model
        try:
            return response_model.model_validate(response)
        except Exception as e:
            raise ValueError(f"Failed to parse response as {response_model.__name__}: {e}")

    async def update_chat_completion_structured(
        self,
        completion_id: str,
        body: Dict[str, Any],
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Modify a stored chat completion. Only Chat Completions that have been
created with the `store` parameter set to `true` can be modified. Currently,
the only supported modification is to update the `metadata` field.
        This is a Layer 1 primitive that wraps the Layer 0 update_chat_completion() method.
        If response_model is provided, the response will be parsed into that Pydantic model.

        Args:
            completion_id: The ID of the chat completion to update.
            body: Request body
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        # Call Layer 0 method
        response = await self.chat_client.update_chat_completion(
            completion_id=completion_id,
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

    async def delete_chat_completion_structured(
        self,
        completion_id: str,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Delete a stored chat completion. Only Chat Completions that have been
created with the `store` parameter set to `true` can be deleted.
        This is a Layer 1 primitive that wraps the Layer 0 delete_chat_completion() method.
        If response_model is provided, the response will be parsed into that Pydantic model.

        Args:
            completion_id: The ID of the chat completion to delete.
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        # Call Layer 0 method
        response = await self.chat_client.delete_chat_completion(
            completion_id=completion_id
        )

        # If no response model specified, return raw response
        if response_model is None:
            return response

        # Parse response into Pydantic model
        try:
            return response_model.model_validate(response)
        except Exception as e:
            raise ValueError(f"Failed to parse response as {response_model.__name__}: {e}")

    async def get_chat_completion_messages_structured(
        self,
        completion_id: str,
        after: str = None,
        limit: int = None,
        order: Literal["asc", "desc"] = None,
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Get the messages in a stored chat completion. Only Chat Completions that
have been created with the `store` parameter set to `true` will be
returned.
        This is a Layer 1 primitive that wraps the Layer 0 get_chat_completion_messages() method.
        If response_model is provided, the response will be parsed into that Pydantic model.

        Args:
            completion_id: The ID of the chat completion to retrieve messages from.
            after: Identifier for the last message from the previous pagination request.
            limit: Number of messages to retrieve.
            order: Sort order for messages by timestamp. Use `asc` for ascending order or `desc` for descending order. Defaults to `asc`.
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        # Call Layer 0 method
        response = await self.chat_client.get_chat_completion_messages(
            completion_id=completion_id,
            after=after,
            limit=limit,
            order=order
        )

        # If no response model specified, return raw response
        if response_model is None:
            return response

        # Parse response into Pydantic model
        try:
            return response_model.model_validate(response)
        except Exception as e:
            raise ValueError(f"Failed to parse response as {response_model.__name__}: {e}")

    async def create_embedding_structured(
        self,
        body: Dict[str, Any],
        response_model: Type[T] = None
    ) -> T | Dict[str, Any]:
        """
        Creates an embedding vector representing the input text.
        This is a Layer 1 primitive that wraps the Layer 0 create_embedding() method.
        If response_model is provided, the response will be parsed into that Pydantic model.

        Args:
            body: Request body
            response_model: Optional Pydantic model to parse the response into
        Returns:
            Parsed response as the specified Pydantic model, or raw Dict if no model provided
        """
        # Call Layer 0 method
        response = await self.embeddings_client.create_embedding(
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
