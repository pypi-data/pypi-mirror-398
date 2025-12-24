"""
SafeFileKit - Automatic hash tracking for filesystem concurrency control.

A kit that wraps read/write/edit tools to automatically track and use
content hashes, preventing lost updates in multi-agent scenarios.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from ..types import Message, Tool, ToolContext, ToolResultMessage, UserMessage
from .base import Kit, KitContext


@dataclass
class SafeFileState:
    """Container for file hash state."""

    hashes: dict[str, str] = field(default_factory=dict)

    def get_hash(self, path: str) -> str | None:
        """Get stored hash for a file path."""
        return self.hashes.get(path)

    def set_hash(self, path: str, content_hash: str) -> None:
        """Store hash for a file path."""
        self.hashes[path] = content_hash

    def clear_hash(self, path: str) -> None:
        """Remove stored hash for a file path."""
        self.hashes.pop(path, None)


class SafeFileKit(Kit):
    """Filesystem kit with automatic hash tracking.

    Wraps the standard read/write/edit tools to automatically:
    - Track hashes when files are read
    - Use tracked hashes when files are written/edited
    - Handle conflict detection transparently

    This eliminates the need for agents to manually parse and pass hashes.

    Example:
        kit = SafeFileKit()
        loop = Loop(model="...", kits=[kit])

        # Agent can just read and write - hashes are tracked automatically
        response = loop.run("Read config.json, modify the timeout, and save it")

        # Access state
        print(kit.state.hashes)  # {'config.json': 'abc123...'}
    """

    def __init__(self) -> None:
        self.state = SafeFileState()

    def get_tools(self) -> list[Tool]:
        """Return filesystem tools with automatic hash tracking."""
        from ..tooling.base import tool
        from ..tooling.filesystem import (
            ConflictError,
            _check_read_path,
            _check_write_path,
            _compute_hash,
        )
        from ..truncate import apply_head_tail

        @tool
        def safe_read(
            ctx: ToolContext,
            file_path: str,
            head: int | None = 100,
            tail: int | None = 100,
        ) -> str:
            """Read contents of a file with automatic hash tracking.

            The hash is automatically stored and will be used for subsequent
            write/edit operations to detect conflicts.

            Args:
                file_path: Path to the file to read (relative to working directory)
                head: Lines from start (0=none, None=no limit, default=100)
                tail: Lines from end (0=none, None=no limit, default=100)
            """
            target = _check_read_path(file_path, ctx)
            if not target.exists():
                raise FileNotFoundError(f"file not found: {file_path}")
            if target.is_dir():
                raise IsADirectoryError(f"{file_path} is a directory, not a file")

            content = target.read_text()
            content_hash = _compute_hash(content)

            # Store hash for later use
            self.state.set_hash(file_path, content_hash)

            truncated = apply_head_tail(content, head, tail, total_hint="lines")
            return f"[hash:{content_hash}]\n{truncated}"

        @tool(truncate=False)
        def safe_write(
            ctx: ToolContext,
            file_path: str,
            content: str,
            force: bool = False,
        ) -> str:
            """Create or overwrite a file with automatic conflict detection.

            Uses the hash from the last read of this file to detect conflicts.
            If the file was modified since you read it, raises ConflictError.

            Args:
                file_path: Path to the file to write (relative to working directory)
                content: Content to write to the file
                force: Skip hash check (for intentional overwrites)

            Raises:
                ConflictError: File was modified since read. Re-read and retry.
            """
            target = _check_write_path(file_path, ctx)

            # Get stored hash (if any)
            expect_hash = self.state.get_hash(file_path)

            # Check for conflicts if hash available
            if expect_hash and not force and target.exists():
                current_hash = _compute_hash(target.read_text())
                if current_hash != expect_hash:
                    raise ConflictError(
                        f"Conflict: file modified since read. "
                        f"Expected hash {expect_hash}, current is {current_hash}. "
                        f"Use safe_read to re-read the file and retry."
                    )

            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
            new_hash = _compute_hash(content)

            # Update stored hash
            self.state.set_hash(file_path, new_hash)

            return f"Wrote {len(content)} bytes to {file_path} [hash:{new_hash}]"

        @tool(truncate=False)
        def safe_edit(
            ctx: ToolContext,
            file_path: str,
            old_text: str,
            new_text: str,
        ) -> str:
            """Edit a file by replacing exact text with automatic conflict detection.

            Uses the hash from the last read of this file to detect conflicts.

            Args:
                file_path: Path to the file to edit (relative to working directory)
                old_text: Text to find and replace (must be unique in file)
                new_text: Text to replace with

            Raises:
                ConflictError: File was modified since read. Re-read and retry.
            """
            target = _check_write_path(file_path, ctx)
            if not target.exists():
                raise FileNotFoundError(f"file not found: {file_path}")

            content = target.read_text()
            current_hash = _compute_hash(content)

            # Get stored hash and check for conflicts
            expect_hash = self.state.get_hash(file_path)
            if expect_hash and current_hash != expect_hash:
                raise ConflictError(
                    "Conflict: file modified since read. "
                    "Use safe_read to re-read the file and retry your edit."
                )

            if old_text not in content:
                raise ValueError(f"text not found in {file_path}")

            count = content.count(old_text)
            if count > 1:
                raise ValueError(
                    f"found {count} matches. Provide more context for unique match."
                )

            new_content = content.replace(old_text, new_text, 1)
            target.write_text(new_content)
            new_hash = _compute_hash(new_content)

            # Update stored hash
            self.state.set_hash(file_path, new_hash)

            return f"Replaced text in {file_path} [hash:{new_hash}]"

        return [safe_read, safe_write, safe_edit]

    def on_tool_error(
        self, tool_name: str, error: str, ctx: KitContext
    ) -> list[Message] | None:
        """Provide guidance on conflict errors."""
        if "Conflict" in error and tool_name in ("safe_write", "safe_edit"):
            return [
                UserMessage(
                    content=(
                        "The file was modified by another agent. "
                        "Use safe_read to get the current content and hash, "
                        "then retry your modification."
                    ),
                    is_meta=True,
                )
            ]
        return None

    def rehydrate(self, messages: list[Message]) -> None:
        """Restore hash state from session history."""
        self.state = SafeFileState()

        for msg in messages:
            if not isinstance(msg, ToolResultMessage):
                continue

            # Parse hashes from tool results
            if msg.tool_name in ("safe_read", "safe_write", "safe_edit"):
                # All these tools return hash in format [hash:xxx]
                hash_match = re.search(r"\[hash:([a-f0-9]+)\]", msg.content)
                if hash_match:
                    content_hash = hash_match.group(1)
                    # Try to extract file path from the result
                    if msg.tool_name == "safe_read":
                        # For read, we need to look at the tool call input
                        # which we don't have here - just store the hash
                        # with a placeholder (will be overwritten on next read)
                        pass
                    elif "to " in msg.content:
                        # "Wrote X bytes to path [hash:...]"
                        path_match = re.search(r"to (\S+) \[hash:", msg.content)
                        if path_match:
                            self.state.set_hash(path_match.group(1), content_hash)
                    elif "in " in msg.content:
                        # "Replaced text in path [hash:...]"
                        path_match = re.search(r"in (\S+) \[hash:", msg.content)
                        if path_match:
                            self.state.set_hash(path_match.group(1), content_hash)

    def get_state(self) -> SafeFileState:
        """Return file hash state for external access."""
        return self.state


__all__ = ["SafeFileKit", "SafeFileState"]
