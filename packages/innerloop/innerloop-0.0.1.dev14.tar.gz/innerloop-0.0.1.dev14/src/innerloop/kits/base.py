"""
Kit Base Classes

Kits are stateful tool bundles with lifecycle hooks.
They bundle tools + state + handlers into a single cohesive unit.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..types import Message, Tool


@dataclass
class KitContext:
    """Context passed to kit lifecycle handlers.

    Attributes:
        messages: Full conversation history.
        turn: Current turn number (0-indexed).
        model: Active model string.
        session_id: Current session identifier.
        workdir: Working directory for file operations.
        exit_attempts: Number of times on_exit has been called this session.
                      Used to prevent infinite loops.
    """

    messages: list[Message]
    turn: int
    model: str
    session_id: str | None = None
    workdir: Path | None = None
    exit_attempts: int = 0


class Kit(ABC):
    """Base class for tool kits with lifecycle management.

    Kits bundle related tools with shared state and lifecycle hooks.
    They solve the problem of tools that need to coordinate or
    participate in loop lifecycle events (like exit warnings).

    Example:
        class TodoKit(Kit):
            def __init__(self):
                self.items = []

            def get_tools(self) -> list[Tool]:
                return [self._add_todo(), self._mark_done()]

            def on_exit(self, ctx: KitContext) -> list[Message] | None:
                if self.pending_count() > 0:
                    return [UserMessage(content="You have pending todos!")]
                return None
    """

    @abstractmethod
    def get_tools(self) -> list[Tool]:
        """Return tools this kit provides.

        Tools returned here are added to the Loop's tool list.
        They can be closures that access self for shared state.
        """
        ...

    def on_exit(self, ctx: KitContext) -> list[Message] | None:
        """Called before loop exits (when LLM stops calling tools).

        Return messages to inject and continue the loop.
        Return None to allow exit.

        This is called when the LLM produces a response with no tool calls.
        If any kit returns messages, those are injected and the loop continues.

        Args:
            ctx: Context with current conversation state.

        Returns:
            List of messages to inject, or None to allow exit.
        """
        return None

    def on_tool_error(
        self, tool_name: str, error: str, ctx: KitContext
    ) -> list[Message] | None:
        """Called when a tool execution fails.

        Can inject recovery guidance or error context.
        Return None to not inject anything.

        Args:
            tool_name: Name of the tool that failed.
            error: Error message from the tool.
            ctx: Context with current conversation state.

        Returns:
            List of messages to inject, or None.
        """
        return None

    def on_turn_start(self, ctx: KitContext) -> list[Message] | None:
        """Called at the start of each turn.

        Can inject reminders or context refreshers.
        Return None to not inject anything.

        Args:
            ctx: Context with current conversation state.

        Returns:
            List of messages to inject, or None.
        """
        return None

    def on_turn_end(self, ctx: KitContext) -> list[Message] | None:
        """Called at the end of each turn (after tool execution).

        Can inject summaries or progress updates.
        Return None to not inject anything.

        Args:
            ctx: Context with current conversation state.

        Returns:
            List of messages to inject, or None.
        """
        return None

    def rehydrate(self, messages: list[Message]) -> None:  # noqa: B027
        """Restore state from session history.

        Called by Loop on session resume. Parse tool results
        from messages to rebuild internal state.

        Override in subclasses that need state persistence.
        Default implementation does nothing.

        Args:
            messages: Full message history from the session.
        """

    def get_state(self) -> Any:
        """Return kit state for external access.

        Override to expose internal state (e.g., todo items).
        Default returns None.
        """
        return None


# Maximum exit attempts before forcing exit (prevents infinite loops)
MAX_EXIT_ATTEMPTS = 3


__all__ = ["Kit", "KitContext", "MAX_EXIT_ATTEMPTS"]
