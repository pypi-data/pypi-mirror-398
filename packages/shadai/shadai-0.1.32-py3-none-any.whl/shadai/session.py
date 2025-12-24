"""
Session Context Manager
-----------------------
Context manager for managing RAG session lifecycle.
"""

import json
from typing import Optional, Union
from uuid import uuid4

from .client import ShadaiClient
from .models import EmbeddingModel, LanguageCode, LLMModel


class Session:
    """Internal context manager for RAG session lifecycle.

    Automatically handles session creation, retrieval, and optional deletion.

    Args:
        name: Optional session name to retrieve existing session
        temporal: If True, delete session on context exit (default: False)
        client: ShadaiClient instance
        system_prompt: Optional system prompt for the session
        llm_model: Optional LLM model enum (e.g., LLMModel.OPENAI_GPT_4O_MINI)
        embedding_model: Optional embedding model enum (e.g., EmbeddingModel.OPENAI_TEXT_EMBEDDING_3_SMALL)
        response_language: Optional language code for responses (e.g., LanguageCode.SPANISH, LanguageCode.ENGLISH)
    """

    def __init__(
        self,
        name: Optional[str] = None,
        temporal: bool = False,
        client: Optional[ShadaiClient] = None,
        system_prompt: Optional[str] = None,
        llm_model: Optional[Union[str, "LLMModel"]] = None,
        embedding_model: Optional[Union[str, "EmbeddingModel"]] = None,
        response_language: Optional[Union[str, "LanguageCode"]] = None,
    ) -> None:
        """Initialize session context manager.

        Args:
            name: Optional session name to retrieve
            temporal: Whether to delete session on exit
            client: ShadaiClient instance (required)
            system_prompt: Optional system prompt
            llm_model: Optional LLM model
            embedding_model: Optional embedding model
            response_language: Optional language code for responses (e.g., "es", "en")
        """
        if not client:
            raise ValueError("ShadaiClient instance is required")

        self._name = name
        self._temporal = temporal
        self._client = client
        self._system_prompt = system_prompt
        self._llm_model = llm_model
        self._embedding_model = embedding_model
        self._response_language = response_language
        self._session_data: Optional[dict] = None

    @property
    def uuid(self) -> Optional[str]:
        """Get session UUID."""
        return str(self._session_data.get("uuid")) if self._session_data else None

    @property
    def name(self) -> Optional[str]:
        """Get session name."""
        return self._session_data.get("name") if self._session_data else None

    @property
    def llm_model_uuid(self) -> Optional[str]:
        """Get LLM model UUID if configured."""
        if not self._session_data:
            return None
        # Session data has flat structure: {"llm_model_uuid": "..."}
        return self._session_data.get("llm_model_uuid")

    @property
    def embedding_uuid(self) -> Optional[str]:
        """Get embedding model UUID if configured."""
        if not self._session_data:
            return None
        # Session data has flat structure: {"embedding_uuid": "..."}
        return self._session_data.get("embedding_uuid")

    async def __aenter__(self) -> "Session":
        """Enter context: create or retrieve session.

        Returns:
            Session instance with populated session data

        Raises:
            Exception: If session creation/update fails
        """
        # Step 1: Create or retrieve session
        create_args = {}

        if self._name:
            # Get existing session or create if doesn't exist
            create_args["name"] = self._name
            if self._system_prompt:
                create_args["system_prompt"] = self._system_prompt
            if self._response_language:
                response_lang_value = (
                    self._response_language.value
                    if hasattr(self._response_language, "value")
                    else str(self._response_language)
                )
                create_args["response_language"] = response_lang_value

            result = await self._client.call_tool(
                tool_name="session_get_or_create",
                arguments=create_args,
            )
            self._session_data = json.loads(result)
        else:
            # Create new session with generated name
            generated_name = f"session-{uuid4().hex[:8]}"
            create_args["name"] = generated_name
            if self._system_prompt:
                create_args["system_prompt"] = self._system_prompt
            if self._response_language:
                response_lang_value = (
                    self._response_language.value
                    if hasattr(self._response_language, "value")
                    else str(self._response_language)
                )
                create_args["response_language"] = response_lang_value

            result = await self._client.call_tool(
                tool_name="session_create",
                arguments=create_args,
            )
            self._session_data = json.loads(result)

        # Step 2: Update models if provided
        if self._llm_model or self._embedding_model:
            try:
                update_args = {"session_uuid": self.uuid}

                # Parse LLM model if provided
                if self._llm_model:
                    llm_value = (
                        self._llm_model.value
                        if hasattr(self._llm_model, "value")
                        else str(self._llm_model)
                    )
                    llm_provider, llm_model_name = llm_value.split(":")
                    update_args["llm_provider"] = llm_provider
                    update_args["llm_model"] = llm_model_name

                # Parse embedding model if provided
                if self._embedding_model:
                    embedding_value = (
                        self._embedding_model.value
                        if hasattr(self._embedding_model, "value")
                        else str(self._embedding_model)
                    )
                    embedding_provider, embedding_model_name = embedding_value.split(
                        ":"
                    )
                    update_args["embedding_provider"] = embedding_provider
                    update_args["embedding_model"] = embedding_model_name

                # Call session_update_models MCP tool
                result = await self._client.call_tool(
                    tool_name="session_update_models",
                    arguments=update_args,
                )

                # Parse response and update session data
                response = json.loads(result)

                # Check if response is in new format with success/data structure
                if isinstance(response, dict) and "success" in response:
                    if not response["success"]:
                        # Extract error information
                        error = response.get("error", {})
                        error_code = error.get("code", "UNKNOWN_ERROR")
                        error_message = error.get("message", "Model update failed")
                        error_details = error.get("details", {})

                        # Raise exception with detailed error information
                        raise Exception(
                            f"[{error_code}] {error_message}"
                            + (f" - Details: {error_details}" if error_details else "")
                        )

                    # Update was successful, extract data
                    self._session_data = response.get("data", response)
                else:
                    # Legacy format or direct data response
                    self._session_data = response

            except Exception as e:
                # Clean up session if model update fails
                if self.uuid:
                    try:
                        await self._client.call_tool(
                            tool_name="session_delete",
                            arguments={"session_uuid": self.uuid},
                        )
                    except Exception:
                        pass  # Ignore cleanup errors

                # Re-raise the original error
                raise Exception(f"Failed to configure session models: {str(e)}") from e

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context: optionally delete session.

        Args:
            exc_type: Exception type if raised
            exc_val: Exception value if raised
            exc_tb: Exception traceback if raised
        """
        if self._temporal and self.uuid:
            await self._client.call_tool(
                tool_name="session_delete",
                arguments={"session_uuid": self.uuid},
            )
