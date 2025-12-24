"""
Anthropic Provider

Implements streaming for Claude models via the Anthropic Python SDK.
Handles:
- Message format conversion
- Extended thinking blocks
- Tool calls with partial JSON accumulation
- Prompt caching (cache_control on last user message)
- Tool ID sanitization
"""

from __future__ import annotations

import json
import re
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
    import anthropic

# Anthropic tool ID pattern
TOOL_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")


def _sanitize_tool_id(tool_id: str) -> str:
    """Ensure tool ID matches Anthropic's required pattern."""
    if TOOL_ID_PATTERN.match(tool_id):
        return tool_id
    # Replace invalid chars with underscore
    return re.sub(r"[^a-zA-Z0-9_-]", "_", tool_id)


def _check_anthropic_installed() -> None:
    """Check if anthropic SDK is installed, raise helpful error if not."""
    try:
        import anthropic  # noqa: F401
    except ImportError as e:
        raise ImportError(
            "Anthropic provider requires the 'anthropic' package. "
            "Install with: pip install innerloop[anthropic]"
        ) from e


class AnthropicProvider(Provider):
    """Anthropic Claude provider."""

    def __init__(
        self,
        model_id: str,
        api_key: str | None = None,
        base_url: str | None = None,
    ):
        _check_anthropic_installed()
        self._model_id = model_id
        self._api_key = api_key
        self._base_url = base_url
        self._client: anthropic.AsyncAnthropic | None = None

    @property
    def name(self) -> str:
        return "anthropic"

    @property
    def model_id(self) -> str:
        return self._model_id

    def _get_client(self) -> anthropic.AsyncAnthropic:
        """Lazy-load the Anthropic client."""
        if self._client is None:
            import anthropic

            kwargs: dict[str, Any] = {}
            if self._api_key:
                kwargs["api_key"] = self._api_key
            if self._base_url:
                kwargs["base_url"] = self._base_url

            self._client = anthropic.AsyncAnthropic(**kwargs)
        return self._client

    async def stream(
        self,
        messages: list[Message],
        tools: list[Tool] | None = None,
        config: Config | None = None,
        tool_choice: dict[str, str] | None = None,
    ) -> AsyncIterator[Event]:
        """Stream a response from Anthropic."""
        import anthropic

        config = config or Config()
        client = self._get_client()

        # Convert messages to Anthropic format
        api_messages = _convert_messages(messages)

        # Add cache control to last user message for prompt caching
        _add_cache_control(api_messages)

        # Build API kwargs
        kwargs: dict[str, Any] = {
            "model": self._model_id,
            "messages": api_messages,
            "max_tokens": config.max_output_tokens,
        }

        if config.system:
            kwargs["system"] = config.system

        if config.temperature is not None:
            kwargs["temperature"] = config.temperature

        # Tools
        if tools:
            kwargs["tools"] = _convert_tools(tools)

        # Tool choice
        if tool_choice:
            kwargs["tool_choice"] = {
                "type": "tool",
                "name": tool_choice.get("name"),
            }

        # Extended thinking
        thinking_config = config.thinking
        if thinking_config and thinking_config.level != ThinkingLevel.OFF:
            budget = _get_thinking_budget(thinking_config)
            kwargs["thinking"] = {
                "type": "enabled",
                "budget_tokens": budget,
            }
            # Thinking requires specific betas
            kwargs["betas"] = ["interleaved-thinking-2025-05-14"]

        # Stream the response
        try:
            async with client.messages.stream(**kwargs) as stream:
                # State for accumulating tool calls
                current_tool_id: str | None = None
                current_tool_name: str | None = None
                tool_input_json: str = ""

                # Track usage
                input_tokens = 0
                output_tokens = 0
                cache_read = 0
                cache_write = 0

                async for event in stream:
                    # Handle different event types
                    if event.type == "message_start":
                        # Extract usage from message start
                        if hasattr(event, "message") and hasattr(
                            event.message, "usage"
                        ):
                            usage = event.message.usage
                            input_tokens = getattr(usage, "input_tokens", 0)
                            cache_read = getattr(usage, "cache_read_input_tokens", 0)
                            cache_write = getattr(
                                usage, "cache_creation_input_tokens", 0
                            )

                    elif event.type == "content_block_start":
                        block = event.content_block
                        if block.type == "tool_use":
                            current_tool_id = _sanitize_tool_id(block.id)
                            current_tool_name = block.name
                            tool_input_json = ""

                    elif event.type == "content_block_delta":
                        delta = event.delta
                        if delta.type == "text_delta":
                            yield TextEvent(text=delta.text)
                        elif delta.type == "thinking_delta":
                            yield ThinkingEvent(text=delta.thinking)
                        elif delta.type == "input_json_delta":
                            # Accumulate tool input JSON
                            tool_input_json += delta.partial_json

                    elif event.type == "content_block_stop":
                        # Emit completed tool call (parse JSON first)
                        if current_tool_id and current_tool_name:
                            # Parse JSON before emitting
                            try:
                                tool_input = json.loads(tool_input_json)
                            except json.JSONDecodeError as e:
                                yield ErrorEvent(
                                    error=f"Malformed tool call JSON for '{current_tool_name}': {e}",
                                    recoverable=True,
                                )
                                current_tool_id = None
                                current_tool_name = None
                                tool_input_json = ""
                                continue

                            yield ToolCallEvent(
                                id=current_tool_id,
                                name=current_tool_name,
                                input=tool_input,
                            )
                            current_tool_id = None
                            current_tool_name = None
                            tool_input_json = ""

                    elif event.type == "message_delta":
                        # Extract output tokens and stop reason
                        if hasattr(event, "usage"):
                            output_tokens = getattr(event.usage, "output_tokens", 0)

                # Emit usage
                yield UsageEvent(
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cache_read_tokens=cache_read,
                    cache_write_tokens=cache_write,
                )

                # Get final message for stop reason
                final_message = await stream.get_final_message()
                stop_reason = _map_stop_reason(final_message.stop_reason)
                yield DoneEvent(stop_reason=stop_reason)

        except anthropic.APIError as e:
            yield ErrorEvent(
                error=str(e),
                code=getattr(e, "code", None),
                recoverable=_is_recoverable(e),
            )
            yield DoneEvent(stop_reason="error")


def _convert_user_content(
    content: str | list[TextPart | ImagePart],
) -> str | list[dict[str, Any]]:
    """Convert user message content to Anthropic format.

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
                source: dict[str, Any] = {"type": "url", "url": part.url}
            elif part.base64_data:
                source = {
                    "type": "base64",
                    "media_type": part.media_type,
                    "data": part.base64_data,
                }
            else:
                continue  # Skip invalid image parts
            result.append({"type": "image", "source": source})
    return result


def _convert_messages(messages: list[Message]) -> list[dict[str, Any]]:
    """Convert InnerLoop messages to Anthropic format."""
    result: list[dict[str, Any]] = []

    for msg in messages:
        if isinstance(msg, UserMessage):
            result.append(
                {
                    "role": "user",
                    "content": _convert_user_content(msg.content),
                }
            )

        elif isinstance(msg, AssistantMessage):
            content: list[dict[str, Any]] = []
            for part in msg.content:
                if isinstance(part, TextPart):
                    content.append({"type": "text", "text": part.text})
                elif isinstance(part, ThinkingPart):
                    block: dict[str, Any] = {
                        "type": "thinking",
                        "thinking": part.text,
                    }
                    if part.signature:
                        block["signature"] = part.signature
                    content.append(block)
                elif isinstance(part, ToolUsePart):
                    content.append(
                        {
                            "type": "tool_use",
                            "id": _sanitize_tool_id(part.id),
                            "name": part.name,
                            "input": part.input,
                        }
                    )

            result.append(
                {
                    "role": "assistant",
                    "content": content,
                }
            )

        elif isinstance(msg, ToolResultMessage):
            result.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": _sanitize_tool_id(msg.tool_use_id),
                            "content": msg.content,
                            "is_error": msg.is_error,
                        }
                    ],
                }
            )

    return result


def _add_cache_control(messages: list[dict[str, Any]]) -> None:
    """Add cache_control to the last user message for prompt caching."""
    # Find last user message
    for i in range(len(messages) - 1, -1, -1):
        if messages[i].get("role") == "user":
            content = messages[i].get("content")
            if isinstance(content, str):
                # Convert to block format for cache control
                messages[i]["content"] = [
                    {
                        "type": "text",
                        "text": content,
                        "cache_control": {"type": "ephemeral"},
                    }
                ]
            elif isinstance(content, list) and content:
                # Add cache control to last block
                content[-1]["cache_control"] = {"type": "ephemeral"}
            break


def _convert_tools(tools: list[Tool]) -> list[dict[str, Any]]:
    """Convert InnerLoop tools to Anthropic format."""
    return [
        {
            "name": tool.name,
            "description": tool.get_description(),
            "input_schema": tool.input_schema,
        }
        for tool in tools
    ]


def _get_thinking_budget(config: ThinkingConfig) -> int:
    """Get thinking budget tokens from config."""
    if config.budget_tokens:
        return config.budget_tokens

    # Map level to budget
    budgets = {
        ThinkingLevel.LOW: 1024,
        ThinkingLevel.MEDIUM: 8192,
        ThinkingLevel.HIGH: 32768,
    }
    return budgets.get(config.level, 8192)


def _map_stop_reason(reason: str | None) -> str:
    """Map Anthropic stop reason to InnerLoop format."""
    if reason == "end_turn":
        return "end_turn"
    elif reason == "tool_use":
        return "tool_use"
    elif reason == "max_tokens":
        return "max_tokens"
    else:
        return reason or "unknown"


def _is_recoverable(error: Exception) -> bool:
    """Check if an error is recoverable (can retry)."""
    import anthropic

    if isinstance(error, anthropic.RateLimitError):
        return True
    if isinstance(error, anthropic.APIStatusError):
        return error.status_code >= 500
    return False


# Register this provider
register_provider("anthropic", AnthropicProvider)


__all__ = ["AnthropicProvider"]
