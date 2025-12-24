"""
TodoKit - Task tracking with exit warnings.

A kit that provides todo management tools with automatic
exit warnings when todos are left incomplete.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

from ..types import Message, Tool, ToolResultMessage, UserMessage
from .base import MAX_EXIT_ATTEMPTS, Kit, KitContext

if TYPE_CHECKING:
    pass


class Status(Enum):
    """Todo status values."""

    TODO = "todo"
    DONE = "done"
    SKIP = "skip"


@dataclass
class Todo:
    """A single todo item."""

    id: int
    title: str
    note: str | None = None
    status: Status = Status.TODO


@dataclass
class TodoState:
    """Container for todo state."""

    items: list[Todo] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.items)

    def pending(self) -> list[Todo]:
        """Get todos with status=TODO."""
        return [t for t in self.items if t.status == Status.TODO]

    def counts(self) -> tuple[int, int, int]:
        """Return (todo_count, done_count, skip_count)."""
        todo = sum(1 for t in self.items if t.status == Status.TODO)
        done = sum(1 for t in self.items if t.status == Status.DONE)
        skip = sum(1 for t in self.items if t.status == Status.SKIP)
        return (todo, done, skip)

    def counts_str(self) -> str:
        """Format counts as string."""
        todo, done, skip = self.counts()
        parts = []
        if todo:
            parts.append(f"{todo} todo")
        if done:
            parts.append(f"{done} done")
        if skip:
            parts.append(f"{skip} skip")
        return ", ".join(parts) if parts else "empty"

    def next_id(self) -> int:
        return len(self.items) + 1


class TodoKit(Kit):
    """Task tracking kit with exit warnings.

    Provides tools for managing todos and automatically warns
    the LLM if it tries to exit with pending tasks.

    Example:
        kit = TodoKit()
        loop = Loop(model="...", kits=[kit])
        response = loop.run("Add 3 todos and complete them")
        print(kit.state.items)  # Access state after execution
    """

    def __init__(self) -> None:
        self.state = TodoState()

    def get_tools(self) -> list[Tool]:
        """Return todo management tools."""
        from ..tooling.base import tool

        @tool
        def add_todo(title: str, note: str | None = None) -> str:
            """Add a new todo item.

            Args:
                title: Brief description of the task
                note: Optional additional details
            """
            todo = Todo(
                id=self.state.next_id(),
                title=title,
                note=note,
            )
            self.state.items.append(todo)
            return f"Added [{todo.id}]: {title}\n({self.state.counts_str()})"

        @tool
        def list_todos(include_completed: bool = False) -> str:
            """List todos. By default shows only pending items.

            Args:
                include_completed: Whether to include done/skipped items
            """
            if include_completed:
                items = self.state.items
            else:
                items = self.state.pending()

            if not items:
                msg = "No todos." if include_completed else "No pending todos."
                return f"{msg}\n({self.state.counts_str()})"

            lines = []
            for t in items:
                status_str = f"[{t.status.value}] " if include_completed else ""
                note_str = f" - {t.note}" if t.note else ""
                lines.append(f"[{t.id}] {status_str}{t.title}{note_str}")

            lines.append(f"\n({self.state.counts_str()})")
            return "\n".join(lines)

        @tool
        def mark_done(todo_id: int) -> str:
            """Mark a todo as done by its ID.

            Args:
                todo_id: ID of the todo to mark as done
            """
            for t in self.state.items:
                if t.id == todo_id:
                    t.status = Status.DONE
                    return f"Done [{t.id}]: {t.title}\n({self.state.counts_str()})"
            return f"Todo [{todo_id}] not found."

        @tool
        def mark_skip(todo_id: int, reason: str | None = None) -> str:
            """Mark a todo as skipped by its ID.

            Args:
                todo_id: ID of the todo to skip
                reason: Optional explanation
            """
            for t in self.state.items:
                if t.id == todo_id:
                    t.status = Status.SKIP
                    if reason:
                        t.note = f"Skipped: {reason}"
                    return f"Skipped [{t.id}]: {t.title}\n({self.state.counts_str()})"
            return f"Todo [{todo_id}] not found."

        return [add_todo, list_todos, mark_done, mark_skip]

    def on_exit(self, ctx: KitContext) -> list[Message] | None:
        """Warn if there are pending todos."""
        pending = self.state.pending()

        if not pending:
            return None

        # Prevent infinite loops
        if ctx.exit_attempts >= MAX_EXIT_ATTEMPTS:
            return None

        # Build warning message
        titles = [t.title for t in pending[:3]]
        titles_str = ", ".join(titles)
        more = f" (+{len(pending) - 3} more)" if len(pending) > 3 else ""

        return [
            UserMessage(
                content=(
                    f"You have {len(pending)} pending todo(s): {titles_str}{more}\n\n"
                    "Please complete them, mark them done, or skip with a reason."
                ),
                is_meta=True,  # Hidden from user UI, visible to LLM
            )
        ]

    def rehydrate(self, messages: list[Message]) -> None:
        """Restore state from session history."""
        self.state = TodoState()

        for msg in messages:
            if not isinstance(msg, ToolResultMessage):
                continue

            if msg.tool_name == "add_todo":
                # Parse: "Added [3]: Write tests\n(3 todo, 1 done)"
                match = re.match(r"Added \[(\d+)\]: (.+?)\n", msg.content)
                if match:
                    self.state.items.append(
                        Todo(
                            id=int(match.group(1)),
                            title=match.group(2),
                            status=Status.TODO,
                        )
                    )

            elif msg.tool_name == "mark_done":
                # Parse: "Done [3]: Write tests\n(2 todo, 2 done)"
                match = re.match(r"Done \[(\d+)\]:", msg.content)
                if match:
                    todo_id = int(match.group(1))
                    for t in self.state.items:
                        if t.id == todo_id:
                            t.status = Status.DONE
                            break

            elif msg.tool_name == "mark_skip":
                # Parse: "Skipped [3]: Write tests\n(2 todo, 1 done, 1 skip)"
                match = re.match(r"Skipped \[(\d+)\]:", msg.content)
                if match:
                    todo_id = int(match.group(1))
                    for t in self.state.items:
                        if t.id == todo_id:
                            t.status = Status.SKIP
                            break

    def get_state(self) -> TodoState:
        """Return todo state for external access."""
        return self.state


__all__ = ["TodoKit", "TodoState", "Todo", "Status"]
