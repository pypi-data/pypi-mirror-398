"""
Provider Protocol

Abstract base for all LLM providers. Each provider implements streaming
and translates between InnerLoop types and provider-specific formats.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..types import Config, Event, Message, Tool


class Provider(ABC):
    """
    Abstract base class for LLM providers.

    All providers must implement:
    - stream(): Async generator yielding events

    Providers translate between InnerLoop's unified types and
    provider-specific API formats.
    """

    @abstractmethod
    def __init__(
        self,
        model_id: str,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        """Initialize the provider with model and credentials."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name (e.g., 'anthropic', 'openai')."""
        ...

    @property
    @abstractmethod
    def model_id(self) -> str:
        """Model identifier (without provider prefix)."""
        ...

    @abstractmethod
    async def stream(
        self,
        messages: list[Message],
        tools: list[Tool] | None = None,
        config: Config | None = None,
        tool_choice: dict[str, str] | None = None,
    ) -> AsyncIterator[Event]:
        """
        Stream a response from the provider.

        Args:
            messages: Conversation history
            tools: Available tools (optional)
            config: Execution configuration (optional)
            tool_choice: Force specific tool (optional)
                - {"type": "tool", "name": "tool_name"} for Anthropic
                - {"type": "function", "function": {"name": "..."}} for OpenAI

        Yields:
            Event objects (TextEvent, ToolCallEvent, UsageEvent, etc.)

        The stream should yield events in this order:
        1. ThinkingEvent (if thinking enabled, Anthropic/OpenAI reasoning)
        2. TextEvent (content tokens)
        3. ToolCallEvent (if tools used)
        4. UsageEvent (token counts)
        5. DoneEvent (always last)

        On error, yield ErrorEvent then DoneEvent with stop_reason="error".
        """
        ...
        # Yield statement for type checking (never reached)
        yield  # type: ignore


__all__ = ["Provider"]
