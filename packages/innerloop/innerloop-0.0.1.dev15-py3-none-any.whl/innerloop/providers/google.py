"""
Google Provider

Implements streaming for Gemini models via the Google Generative AI SDK.
Handles:
- Message format conversion
- Tool calls with streaming
- Safety settings
- Image generation models (gemini-*-image-*)
"""

from __future__ import annotations

import base64
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any

from ..types import (
    AssistantMessage,
    Config,
    DoneEvent,
    ErrorEvent,
    Event,
    ImageEvent,
    ImagePart,
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
    import google.generativeai as genai


def _is_image_model(model_id: str) -> bool:
    """Check if model is an image generation model."""
    return "image" in model_id.lower()


def _check_google_installed() -> None:
    """Check if google-generativeai SDK is installed, raise helpful error if not."""
    try:
        import google.generativeai  # noqa: F401
    except ImportError as e:
        raise ImportError(
            "Google provider requires the 'google-generativeai' package. "
            "Install with: pip install innerloop[google]"
        ) from e


def _check_genai_installed() -> None:
    """Check if google-genai SDK is installed (needed for image models)."""
    try:
        from google import genai  # noqa: F401
    except ImportError as e:
        raise ImportError(
            "Image generation models require the 'google-genai' package. "
            "Install with: pip install google-genai"
        ) from e


class GoogleProvider(Provider):
    """Google Gemini provider."""

    def __init__(
        self,
        model_id: str,
        api_key: str | None = None,
        base_url: str | None = None,
    ):
        self._model_id = model_id
        self._api_key = api_key
        self._base_url = base_url  # Not used, but kept for interface consistency
        self._client: genai.GenerativeModel | None = None
        self._genai_client: Any = None  # For new google-genai SDK

        # Check for appropriate SDK
        if _is_image_model(model_id):
            _check_genai_installed()
        else:
            _check_google_installed()

    @property
    def name(self) -> str:
        return "google"

    @property
    def model_id(self) -> str:
        return self._model_id

    def _get_client(self) -> genai.GenerativeModel:
        """Lazy-load the Gemini client (old SDK for text models)."""
        if self._client is None:
            import google.generativeai as genai

            if self._api_key:
                genai.configure(api_key=self._api_key)

            self._client = genai.GenerativeModel(self._model_id)
        return self._client

    def _get_genai_client(self) -> Any:
        """Lazy-load the new google-genai client (for image models)."""
        import os

        if self._genai_client is None:
            from google import genai

            # Check for API key in order: explicit, GEMINI_API_KEY, GOOGLE_API_KEY
            api_key = (
                self._api_key
                or os.environ.get("GEMINI_API_KEY")
                or os.environ.get("GOOGLE_API_KEY")
            )
            self._genai_client = genai.Client(api_key=api_key)
        return self._genai_client

    async def stream(
        self,
        messages: list[Message],
        tools: list[Tool] | None = None,
        config: Config | None = None,
        tool_choice: dict[str, str] | None = None,
    ) -> AsyncIterator[Event]:
        """Stream a response from Google Gemini."""
        config = config or Config()

        # Route to image model handler if needed
        if _is_image_model(self._model_id):
            async for event in self._stream_image_model(messages, config):
                yield event
            return

        # Standard text model handling
        import google.generativeai as genai
        from google.api_core import exceptions as google_exceptions

        model = self._get_client()

        # Convert messages to Gemini format
        history, last_content = _convert_messages(messages, config.system)

        # Build generation config
        generation_config = genai.GenerationConfig(
            max_output_tokens=config.max_output_tokens,
        )
        if config.temperature is not None:
            generation_config.temperature = config.temperature

        # Build tool config
        gemini_tools = None
        if tools:
            gemini_tools = _convert_tools(tools)
            # Respect forced tool selection by restricting allowed functions
            if tool_choice and tool_choice.get("name"):
                tool_config = genai.protos.ToolConfig(
                    function_calling_config=genai.protos.FunctionCallingConfig(
                        mode=genai.protos.FunctionCallingConfig.Mode.ANY,
                        allowed_function_names=[tool_choice["name"]],
                    )
                )
            else:
                tool_config = None
        else:
            tool_config = None

        try:
            # Create chat with history
            chat = model.start_chat(history=history)

            # Stream the response
            response = await chat.send_message_async(
                last_content,
                generation_config=generation_config,
                tools=gemini_tools,
                tool_config=tool_config,
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

            # Emit usage
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

    async def _stream_image_model(
        self,
        messages: list[Message],
        config: Config,
    ) -> AsyncIterator[Event]:
        """Stream response from an image generation model using google-genai SDK."""
        from google.genai import types

        client = self._get_genai_client()

        # Build content from messages
        contents = _convert_messages_for_genai(messages, config.system)

        # Build generation config
        response_modalities = config.response_modalities or ["TEXT", "IMAGE"]
        gen_config = types.GenerateContentConfig(
            response_modalities=response_modalities,
        )
        if config.temperature is not None:
            gen_config.temperature = config.temperature

        try:
            # Generate content (non-streaming for now - image models don't stream well)
            response = client.models.generate_content(
                model=self._model_id,
                contents=contents,
                config=gen_config,
            )

            # Process response parts
            for part in response.candidates[0].content.parts:
                if hasattr(part, "text") and part.text:
                    yield TextEvent(text=part.text)
                if hasattr(part, "inline_data") and part.inline_data:
                    # Extract image data
                    image_data = part.inline_data
                    yield ImageEvent(
                        image=ImagePart(
                            base64_data=base64.b64encode(image_data.data).decode(),
                            media_type=image_data.mime_type,
                        )
                    )

            # Emit usage if available
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                usage = response.usage_metadata
                yield UsageEvent(
                    input_tokens=getattr(usage, "prompt_token_count", 0),
                    output_tokens=getattr(usage, "candidates_token_count", 0),
                )
            else:
                yield UsageEvent(input_tokens=0, output_tokens=0)

            yield DoneEvent(stop_reason="end_turn")

        except Exception as e:
            code = getattr(e, "code", None) if hasattr(e, "code") else None
            yield ErrorEvent(
                error=str(e),
                code=str(code) if code is not None else None,
                recoverable=False,
            )
            yield DoneEvent(stop_reason="error")


def _fetch_image(url: str) -> bytes:
    """Fetch image data from URL.

    Only allows http:// and https:// schemes to prevent path traversal
    via file:// or other custom schemes (CWE-22).
    """
    import urllib.request
    from urllib.parse import urlparse

    # Validate URL scheme to prevent file:// and custom scheme attacks
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"Unsupported URL scheme: {parsed.scheme}")

    with urllib.request.urlopen(url, timeout=30) as response:  # nosec B310
        return response.read()


def _convert_messages(
    messages: list[Message], system: str | None
) -> tuple[list[dict[str, Any]], list[Any]]:
    """
    Convert InnerLoop messages to Gemini format.

    Returns (history, last_content) where history is the chat history
    and last_content is the content for the final send_message call.
    """
    import google.generativeai as genai

    history: list[dict[str, Any]] = []

    for msg in messages:
        if isinstance(msg, UserMessage):
            # Convert content, prepend system to first message
            prepend = system if not history else None
            user_parts = _convert_user_content(msg.content, prepend)
            history.append({"role": "user", "parts": user_parts})

        elif isinstance(msg, AssistantMessage):
            assistant_parts: list[Any] = []
            for part in msg.content:
                if isinstance(part, TextPart):
                    assistant_parts.append(part.text)
                elif isinstance(part, ToolUsePart):
                    # Create function call part
                    assistant_parts.append(
                        genai.protos.Part(
                            function_call=genai.protos.FunctionCall(
                                name=part.name,
                                args=part.input,
                            )
                        )
                    )
            if assistant_parts:
                history.append({"role": "model", "parts": assistant_parts})

        elif isinstance(msg, ToolResultMessage):
            # Function response
            parts = [
                genai.protos.Part(
                    function_response=genai.protos.FunctionResponse(
                        name=msg.tool_use_id.replace("call_", ""),
                        response={"result": msg.content},
                    )
                )
            ]
            history.append({"role": "user", "parts": parts})

    # Pop the last user message as it will be sent via send_message
    if history and history[-1]["role"] == "user":
        last = history.pop()
        return history, last["parts"]

    # If no user message at end, return empty content
    return history, []


def _convert_user_content(content: Any, system: str | None) -> list[Any]:
    """Convert user content to Gemini parts while preserving the system prompt.

    Handles both simple strings and lists of content parts (TextPart, ImagePart).
    For images, URLs are fetched and converted to inline data.
    """
    import base64

    system_prefix = system
    parts: list[Any] = []

    def _append_text(text: str) -> None:
        nonlocal system_prefix
        if system_prefix:
            text = f"System: {system_prefix}\n\n{text}"
            system_prefix = None
        parts.append(text)

    def _append_image(part: ImagePart) -> None:
        """Convert ImagePart to Gemini-compatible dict."""
        if part.base64_data:
            # Inline image data
            parts.append(
                {
                    "mime_type": part.media_type,
                    "data": base64.b64decode(part.base64_data),
                }
            )
        elif part.url:
            # For URLs, fetch the image data
            try:
                image_data = _fetch_image(part.url)
                parts.append(
                    {
                        "mime_type": part.media_type,
                        "data": image_data,
                    }
                )
            except Exception:
                # If fetch fails, skip the image
                pass

    if isinstance(content, list):
        for part in content:
            if isinstance(part, TextPart):
                _append_text(part.text)
            elif isinstance(part, ImagePart):
                _append_image(part)
            else:
                parts.append(part)

        if system_prefix:
            parts.insert(0, f"System: {system_prefix}")

    elif isinstance(content, str):
        _append_text(content)
    else:
        _append_text(str(content))

    return parts


def _convert_messages_for_genai(
    messages: list[Message], system: str | None
) -> list[Any]:
    """Convert InnerLoop messages to google-genai SDK format.

    The new SDK uses a simpler format - just a list of content items.
    For multi-turn, it builds on the conversation naturally.
    """
    from google.genai import types

    contents: list[Any] = []

    for msg in messages:
        if isinstance(msg, UserMessage):
            # Build user content parts
            parts: list[Any] = []

            # Add system prompt to first user message
            if system and not contents:
                parts.append(types.Part.from_text(text=f"System: {system}\n\n"))

            # Process content
            if isinstance(msg.content, str):
                parts.append(types.Part.from_text(text=msg.content))
            elif isinstance(msg.content, list):
                for part in msg.content:
                    if isinstance(part, TextPart):
                        parts.append(types.Part.from_text(text=part.text))
                    elif isinstance(part, ImagePart):
                        if part.base64_data:
                            parts.append(
                                types.Part.from_bytes(
                                    data=base64.b64decode(part.base64_data),
                                    mime_type=part.media_type,
                                )
                            )
                        elif part.url:
                            try:
                                image_bytes = _fetch_image(part.url)
                                parts.append(
                                    types.Part.from_bytes(
                                        data=image_bytes,
                                        mime_type=part.media_type,
                                    )
                                )
                            except Exception:
                                pass

            contents.append(types.Content(role="user", parts=parts))

        elif isinstance(msg, AssistantMessage):
            # Build assistant content parts
            parts = []
            for part in msg.content:
                if isinstance(part, TextPart):
                    parts.append(types.Part.from_text(text=part.text))
                elif isinstance(part, ImagePart):
                    # Include generated images in conversation history
                    if part.base64_data:
                        parts.append(
                            types.Part.from_bytes(
                                data=base64.b64decode(part.base64_data),
                                mime_type=part.media_type,
                            )
                        )
            if parts:
                contents.append(types.Content(role="model", parts=parts))

    return contents


def _convert_tools(tools: list[Tool]) -> list[Any]:
    """Convert InnerLoop tools to Gemini format."""
    import google.generativeai as genai

    function_declarations = []
    for tool in tools:
        # Convert JSON Schema to Gemini format
        parameters = _convert_schema(tool.input_schema)
        function_declarations.append(
            genai.protos.FunctionDeclaration(
                name=tool.name,
                description=tool.get_description(),
                parameters=parameters,
            )
        )

    return [genai.protos.Tool(function_declarations=function_declarations)]


def _convert_schema(schema: dict[str, Any]) -> Any:
    """Convert JSON Schema to Gemini Schema format."""
    import google.generativeai as genai

    if not schema:
        return None

    schema_type = schema.get("type", "object")
    type_map = {
        "string": genai.protos.Type.STRING,
        "number": genai.protos.Type.NUMBER,
        "integer": genai.protos.Type.INTEGER,
        "boolean": genai.protos.Type.BOOLEAN,
        "array": genai.protos.Type.ARRAY,
        "object": genai.protos.Type.OBJECT,
    }

    gemini_schema = genai.protos.Schema(
        type=type_map.get(schema_type, genai.protos.Type.OBJECT),
        description=schema.get("description"),
    )

    # Handle properties for objects
    if schema_type == "object" and "properties" in schema:
        gemini_schema.properties = {
            key: _convert_schema(val) for key, val in schema["properties"].items()
        }
        if "required" in schema:
            gemini_schema.required = schema["required"]

    # Handle array items
    if schema_type == "array" and "items" in schema:
        gemini_schema.items = _convert_schema(schema["items"])

    return gemini_schema


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
register_provider("google", GoogleProvider)


__all__ = ["GoogleProvider"]
