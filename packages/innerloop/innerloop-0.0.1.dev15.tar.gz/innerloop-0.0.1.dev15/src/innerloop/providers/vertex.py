"""
Vertex AI Provider

Implements streaming for Gemini models via Google Cloud Vertex AI.
Uses Application Default Credentials (ADC) for authentication.

Environment variables:
- GOOGLE_CLOUD_PROJECT: GCP project ID (required)
- GOOGLE_CLOUD_LOCATION: GCP region (default: us-central1)
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any

from ..types import (
    AssistantMessage,
    Config,
    DoneEvent,
    ErrorEvent,
    Event,
    Message,
    TextEvent,
    TextPart,
    Tool,
    ToolCallEvent,
    ToolResultMessage,
    ToolUsePart,
    UsageEvent,
    UserMessage,
)
from . import register_provider
from .base import Provider

if TYPE_CHECKING:
    from vertexai.generative_models import GenerativeModel


def _check_vertex_installed() -> None:
    """Check if google-cloud-aiplatform SDK is installed."""
    try:
        import vertexai  # noqa: F401
    except ImportError as e:
        raise ImportError(
            "Vertex provider requires the 'google-cloud-aiplatform' package. "
            "Install with: pip install innerloop[vertex]"
        ) from e


class VertexProvider(Provider):
    """Google Vertex AI provider for Gemini models."""

    def __init__(
        self,
        model_id: str,
        api_key: str | None = None,  # Actually project ID for Vertex
        base_url: str | None = None,  # Actually location for Vertex
    ):
        _check_vertex_installed()
        self._model_id = model_id
        # For Vertex, api_key is repurposed as project, base_url as location
        self._project = api_key or os.environ.get("GOOGLE_CLOUD_PROJECT")
        self._location = base_url or os.environ.get(
            "GOOGLE_CLOUD_LOCATION", "us-central1"
        )
        self._client: GenerativeModel | None = None
        self._initialized = False

    @property
    def name(self) -> str:
        return "vertex"

    @property
    def model_id(self) -> str:
        return self._model_id

    def _get_client(self) -> GenerativeModel:
        """Lazy-load the Vertex AI client."""
        if self._client is None:
            import vertexai
            from vertexai.generative_models import GenerativeModel

            if not self._initialized:
                vertexai.init(project=self._project, location=self._location)
                self._initialized = True

            self._client = GenerativeModel(self._model_id)
        return self._client

    async def stream(
        self,
        messages: list[Message],
        tools: list[Tool] | None = None,
        config: Config | None = None,
        tool_choice: dict[str, str] | None = None,
    ) -> AsyncIterator[Event]:
        """Stream a response from Vertex AI."""
        from google.api_core import exceptions as google_exceptions
        from vertexai.generative_models import (
            GenerationConfig,
        )

        config = config or Config()
        model = self._get_client()

        # Convert messages to Vertex format
        history, last_content = _convert_messages(messages, config.system)

        # Build generation config
        generation_config = GenerationConfig(
            max_output_tokens=config.max_output_tokens,
        )
        if config.temperature is not None:
            generation_config.temperature = config.temperature

        # Build tools
        vertex_tools = None
        if tools:
            vertex_tools = _convert_tools(tools)

        try:
            # Create chat with history
            chat = model.start_chat(history=history)

            # Stream the response
            response = await chat.send_message_async(
                last_content,
                generation_config=generation_config,
                tools=vertex_tools,
                stream=True,
            )

            input_tokens = 0
            output_tokens = 0

            async for chunk in response:
                # Handle text content and function calls
                if chunk.candidates:
                    for candidate in chunk.candidates:
                        if candidate.content and candidate.content.parts:
                            for part in candidate.content.parts:
                                if hasattr(part, "text") and part.text:
                                    yield TextEvent(text=part.text)
                                if (
                                    hasattr(part, "function_call")
                                    and part.function_call
                                ):
                                    fc = part.function_call
                                    args_dict = dict(fc.args) if fc.args else {}
                                    yield ToolCallEvent(
                                        id=f"call_{fc.name}",
                                        name=fc.name,
                                        input=args_dict,
                                    )

                # Extract usage if available
                if hasattr(chunk, "usage_metadata") and chunk.usage_metadata:
                    usage = chunk.usage_metadata
                    input_tokens = getattr(usage, "prompt_token_count", 0)
                    output_tokens = getattr(usage, "candidates_token_count", 0)

            yield UsageEvent(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )

            # Determine stop reason
            stop_reason = "end_turn"
            if response.candidates:
                candidate = response.candidates[0]
                if candidate.content and candidate.content.parts:
                    for part in candidate.content.parts:
                        if hasattr(part, "function_call") and part.function_call:
                            stop_reason = "tool_use"
                            break

            yield DoneEvent(stop_reason=stop_reason)

        except google_exceptions.GoogleAPIError as e:
            yield ErrorEvent(
                error=str(e),
                code=getattr(e, "code", None),
                recoverable=_is_recoverable(e),
            )
            yield DoneEvent(stop_reason="error")


def _convert_messages(
    messages: list[Message], system: str | None
) -> tuple[list[Any], list[Any]]:
    """Convert InnerLoop messages to Vertex AI format."""
    from vertexai.generative_models import Content, Part

    history: list[Content] = []

    for msg in messages:
        if isinstance(msg, UserMessage):
            parts: list[Part] = []
            content = msg.content
            # Prepend system message to first user message
            if system and not history:
                content = f"System: {system}\n\n{msg.content}"
            parts.append(Part.from_text(content))
            history.append(Content(role="user", parts=parts))

        elif isinstance(msg, AssistantMessage):
            parts = []
            for part in msg.content:
                if isinstance(part, TextPart):
                    parts.append(Part.from_text(part.text))
                elif isinstance(part, ToolUsePart):
                    # Assistant's tool call (function_call, not function_response)
                    parts.append(
                        Part.from_function_call(
                            name=part.name,
                            args=part.input,
                        )
                    )
            if parts:
                history.append(Content(role="model", parts=parts))

        elif isinstance(msg, ToolResultMessage):
            parts = [
                Part.from_function_response(
                    name=msg.tool_use_id.replace("call_", ""),
                    response={"result": msg.content},
                )
            ]
            history.append(Content(role="user", parts=parts))

    # Pop the last user message as it will be sent via send_message
    if history and history[-1].role == "user":
        last = history.pop()
        return history, last.parts

    return history, []


def _convert_tools(tools: list[Tool]) -> list[Any]:
    """Convert InnerLoop tools to Vertex AI format."""
    from vertexai.generative_models import FunctionDeclaration
    from vertexai.generative_models import Tool as VertexTool

    function_declarations = []
    for tool in tools:
        function_declarations.append(
            FunctionDeclaration(
                name=tool.name,
                description=tool.get_description(),
                parameters=tool.input_schema,
            )
        )

    return [VertexTool(function_declarations=function_declarations)]


def _is_recoverable(error: Exception) -> bool:
    """Check if an error is recoverable."""
    from google.api_core import exceptions as google_exceptions

    if isinstance(error, google_exceptions.ResourceExhausted):
        return True
    if isinstance(error, google_exceptions.ServiceUnavailable):
        return True
    if isinstance(error, google_exceptions.InternalServerError):
        return True
    return False


# Register this provider
register_provider("vertex", VertexProvider)


__all__ = ["VertexProvider"]
