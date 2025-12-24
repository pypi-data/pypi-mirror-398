"""
OpenAI Provider

Implements streaming for OpenAI models via the OpenAI Python SDK.
Also supports OpenAI-compatible APIs (OpenRouter, Ollama, LM Studio, etc.).

Handles:
- Message format conversion
- Tool calls with partial JSON accumulation
- Reasoning content (o1/o3 models)
- Custom base URLs for compatible servers
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any

from ..types import (
    AssistantMessage,
    Config,
    DoneEvent,
    ErrorEvent,
    Event,
    ImagePart,
    Message,
    TextEvent,
    TextPart,
    ThinkingConfig,
    ThinkingEvent,
    ThinkingLevel,
    ThinkingPart,
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
    import openai


def _check_openai_installed() -> None:
    """Check if openai SDK is installed, raise helpful error if not."""
    try:
        import openai  # noqa: F401
    except ImportError as e:
        raise ImportError(
            "OpenAI provider requires the 'openai' package. "
            "Install with: pip install innerloop[openai]  "
            "(or innerloop[ollama] / innerloop[lmstudio] for local models)"
        ) from e


class OpenAIProvider(Provider):
    """OpenAI and OpenAI-compatible provider."""

    def __init__(
        self,
        model_id: str,
        api_key: str | None = None,
        base_url: str | None = None,
    ):
        _check_openai_installed()
        self._model_id = model_id
        self._api_key = api_key
        self._base_url = base_url
        self._client: openai.AsyncOpenAI | None = None

    @property
    def name(self) -> str:
        return "openai"

    @property
    def model_id(self) -> str:
        return self._model_id

    def _get_client(self) -> openai.AsyncOpenAI:
        """Lazy-load the OpenAI client."""
        if self._client is None:
            import openai

            kwargs: dict[str, Any] = {}
            if self._api_key:
                kwargs["api_key"] = self._api_key
            if self._base_url:
                kwargs["base_url"] = self._base_url

            # OpenRouter requires extra headers
            if self._base_url and "openrouter.ai" in self._base_url:
                kwargs["default_headers"] = {
                    "HTTP-Referer": "https://github.com/botassembly/innerloop",
                    "X-Title": "InnerLoop",
                }

            self._client = openai.AsyncOpenAI(**kwargs)
        return self._client

    async def stream(
        self,
        messages: list[Message],
        tools: list[Tool] | None = None,
        config: Config | None = None,
        tool_choice: dict[str, str] | None = None,
    ) -> AsyncIterator[Event]:
        """Stream a response from OpenAI."""
        import openai

        config = config or Config()
        client = self._get_client()

        # Convert messages to OpenAI format
        api_messages = _convert_messages(messages, config.system)

        is_lmstudio = self._base_url is not None and "localhost:1234" in self._base_url

        # Build API kwargs
        kwargs: dict[str, Any] = {
            "model": self._model_id,
            "messages": api_messages,
            "stream": True,
            "stream_options": {"include_usage": True},
        }

        # Some models (gpt-5+) use max_completion_tokens instead of max_tokens
        # Try max_completion_tokens first for newer models
        if (
            "gpt-5" in self._model_id
            or "o1" in self._model_id
            or "o3" in self._model_id
        ):
            kwargs["max_completion_tokens"] = config.max_output_tokens
        else:
            kwargs["max_tokens"] = config.max_output_tokens

        if config.temperature is not None:
            kwargs["temperature"] = config.temperature

        # Tools
        if tools:
            kwargs["tools"] = _convert_tools(tools)

        # Tool choice
        if tool_choice:
            if is_lmstudio:
                # LM Studio's OpenAI-compatible server expects a string
                # (none|auto|required) instead of the structured object.
                kwargs["tool_choice"] = "required"
            else:
                kwargs["tool_choice"] = {
                    "type": "function",
                    "function": {"name": tool_choice.get("name")},
                }

        # Reasoning (for o1/o3 models with thinking)
        thinking_config = config.thinking
        if thinking_config and thinking_config.level != ThinkingLevel.OFF:
            reasoning_param = _build_reasoning_param(thinking_config)
            if reasoning_param:
                kwargs["reasoning"] = reasoning_param

        # Stream the response
        try:
            # Try with forced tool_choice first
            try:
                stream = await client.chat.completions.create(**kwargs)
            except openai.BadRequestError as e:
                # Some models don't support forced tool_choice
                # (e.g., GLM via OpenRouter, LM Studio)
                # Retry with auto if we get tool_choice related errors
                error_str = str(e).lower()
                if tool_choice and (
                    "tool choice must be auto" in error_str
                    or "invalid tool_choice" in error_str
                ):
                    kwargs.pop("tool_choice", None)
                    stream = await client.chat.completions.create(**kwargs)
                else:
                    raise

            # State for accumulating tool calls
            tool_calls_accumulator: dict[int, dict[str, Any]] = {}
            usage_data = {"input": 0, "output": 0}
            stop_reason = "stop"

            async for chunk in stream:
                if not chunk.choices:
                    continue

                choice = chunk.choices[0]
                delta = choice.delta

                # Text content
                if delta.content:
                    yield TextEvent(text=delta.content)

                # Reasoning content (o1/o3 models)
                if hasattr(delta, "reasoning_content") and delta.reasoning_content:
                    yield ThinkingEvent(text=delta.reasoning_content)

                # Tool calls (streamed as deltas)
                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        idx = tc.index
                        if idx not in tool_calls_accumulator:
                            tool_calls_accumulator[idx] = {
                                "id": tc.id or f"call_{idx}",
                                "name": "",
                                "arguments": "",
                            }

                        if tc.id:
                            tool_calls_accumulator[idx]["id"] = tc.id
                        if tc.function.name:
                            tool_calls_accumulator[idx]["name"] = tc.function.name
                        if tc.function.arguments:
                            tool_calls_accumulator[idx]["arguments"] += (
                                tc.function.arguments
                            )

                # Finish reason
                if choice.finish_reason:
                    stop_reason = _map_stop_reason(choice.finish_reason)

                # Usage (appears in final chunk)
                if chunk.usage:
                    usage_data["input"] = chunk.usage.prompt_tokens
                    usage_data["output"] = chunk.usage.completion_tokens

            # Emit completed tool calls (parse JSON first)
            for tc in tool_calls_accumulator.values():
                # Parse JSON before emitting
                try:
                    tool_input = json.loads(tc["arguments"])
                except json.JSONDecodeError as e:
                    yield ErrorEvent(
                        error=f"Malformed tool call JSON for '{tc['name']}': {e}",
                        recoverable=True,
                    )
                    continue

                yield ToolCallEvent(
                    id=tc["id"],
                    name=tc["name"],
                    input=tool_input,
                )

            # Emit usage
            yield UsageEvent(
                input_tokens=usage_data["input"],
                output_tokens=usage_data["output"],
            )

            # Done
            yield DoneEvent(stop_reason=stop_reason)

        except openai.APIError as e:
            code = getattr(e, "code", None)
            yield ErrorEvent(
                error=str(e),
                code=str(code) if code else None,
                recoverable=_is_recoverable(e),
            )
            yield DoneEvent(stop_reason="error")


def _convert_user_content(
    content: str | list[TextPart | ImagePart],
) -> str | list[dict[str, Any]]:
    """Convert user message content to OpenAI format.

    Handles both simple strings (backward compatible) and lists of
    content parts (for multimodal messages with images).
    """
    if isinstance(content, str):
        return content

    result: list[dict[str, Any]] = []
    for part in content:
        if isinstance(part, TextPart):
            result.append({"type": "text", "text": part.text})
        elif isinstance(part, ImagePart):
            if part.url:
                img_url: dict[str, Any] = {"url": part.url}
            elif part.base64_data:
                img_url = {"url": f"data:{part.media_type};base64,{part.base64_data}"}
            else:
                continue  # Skip invalid image parts
            if part.detail:
                img_url["detail"] = part.detail
            result.append({"type": "image_url", "image_url": img_url})
    return result


def _convert_messages(
    messages: list[Message], system: str | None
) -> list[dict[str, Any]]:
    """Convert InnerLoop messages to OpenAI format."""
    result: list[dict[str, Any]] = []

    # System message goes first if present
    if system:
        result.append({"role": "system", "content": system})

    for msg in messages:
        if isinstance(msg, UserMessage):
            result.append(
                {
                    "role": "user",
                    "content": _convert_user_content(msg.content),
                }
            )

        elif isinstance(msg, AssistantMessage):
            content_parts: list[dict[str, Any]] = []
            tool_calls: list[dict[str, Any]] = []

            for part in msg.content:
                if isinstance(part, TextPart):
                    content_parts.append({"type": "text", "text": part.text})
                elif isinstance(part, ThinkingPart):
                    # Convert thinking to text for OpenAI
                    content_parts.append(
                        {"type": "text", "text": f"[Thinking: {part.text}]"}
                    )
                elif isinstance(part, ToolUsePart):
                    tool_calls.append(
                        {
                            "id": part.id,
                            "type": "function",
                            "function": {
                                "name": part.name,
                                "arguments": json.dumps(part.input),
                            },
                        }
                    )

            # Build message
            msg_dict: dict[str, Any] = {"role": "assistant"}
            if content_parts:
                # Concatenate text parts
                text = " ".join(p["text"] for p in content_parts)
                msg_dict["content"] = text
            if tool_calls:
                msg_dict["tool_calls"] = tool_calls

            result.append(msg_dict)

        elif isinstance(msg, ToolResultMessage):
            result.append(
                {
                    "role": "tool",
                    "tool_call_id": msg.tool_use_id,
                    "content": msg.content,
                }
            )

    return result


def _convert_tools(tools: list[Tool]) -> list[dict[str, Any]]:
    """Convert InnerLoop tools to OpenAI format."""
    return [
        {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.get_description(),
                "parameters": tool.input_schema,
            },
        }
        for tool in tools
    ]


def _build_reasoning_param(config: ThinkingConfig) -> dict[str, Any] | None:
    """Build reasoning parameter for OpenAI o1/o3 models."""
    if config.level == ThinkingLevel.OFF:
        return None

    effort_map = {
        ThinkingLevel.LOW: "low",
        ThinkingLevel.MEDIUM: "medium",
        ThinkingLevel.HIGH: "high",
    }

    return {
        "effort": effort_map.get(config.level, "medium"),
        "summary": config.summary or "auto",
    }


def _map_stop_reason(reason: str | None) -> str:
    """Map OpenAI stop reason to InnerLoop format."""
    if reason == "stop":
        return "end_turn"
    elif reason == "tool_calls":
        return "tool_use"
    elif reason == "length":
        return "max_tokens"
    else:
        return reason or "unknown"


def _is_recoverable(error: Exception) -> bool:
    """Check if an error is recoverable."""
    import openai

    if isinstance(error, openai.RateLimitError):
        return True
    if isinstance(error, openai.APIStatusError):
        return error.status_code >= 500
    return False


# Register this provider
register_provider("openai", OpenAIProvider)

# Also register as openrouter (uses same API)
register_provider("openrouter", OpenAIProvider)

# Local model providers (OpenAI-compatible)
register_provider("ollama", OpenAIProvider)
register_provider("lmstudio", OpenAIProvider)
register_provider("cerebras", OpenAIProvider)
register_provider("groq", OpenAIProvider)

# Z.ai (OpenAI-compatible)
register_provider("zai-org", OpenAIProvider)
register_provider("zai-coding", OpenAIProvider)

# Additional OpenAI-compatible providers
register_provider("mlx", OpenAIProvider)
register_provider("azure", OpenAIProvider)
register_provider("together", OpenAIProvider)
register_provider("fireworks", OpenAIProvider)
register_provider("perplexity", OpenAIProvider)
register_provider("deepseek", OpenAIProvider)
register_provider("nvidia", OpenAIProvider)
register_provider("xai", OpenAIProvider)
register_provider("mistral", OpenAIProvider)


__all__ = ["OpenAIProvider"]
