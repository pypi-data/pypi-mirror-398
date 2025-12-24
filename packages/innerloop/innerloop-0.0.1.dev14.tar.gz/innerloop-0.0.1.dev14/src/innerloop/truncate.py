"""
Truncation utilities for tool output.

Two layers of truncation:
1. Tool-level head/tail params - LLM controls the slice
2. Framework-level truncation - safety net after tool returns

Usage:
    from innerloop.truncate import apply_head_tail, truncate_output

    # In tool implementation
    content = file.read_text()
    return apply_head_tail(content, head=100, tail=100)

    # In framework (LocalTool.execute)
    result = truncate_output(result, config, temp_dir, tool_name)
"""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from .types import TruncateConfig


def apply_head_tail(
    content: str,
    head: int | None,
    tail: int | None,
    *,
    total_hint: str = "lines",
) -> str:
    """Apply head/tail selection to content.

    Args:
        content: Full content string
        head: Lines from start (0=none, None=no limit)
        tail: Lines from end (0=none, None=no limit)
        total_hint: Word to use for count (e.g., "lines", "entries", "matches")

    Returns:
        Selected content with navigation hints
    """
    if not content:
        return content

    lines = content.splitlines()
    total = len(lines)

    # Both None = give everything (let framework handle)
    if head is None and tail is None:
        return content

    # Normalize: None means "no limit from this end"
    h = total if head is None else head
    t = total if tail is None else tail

    # Both explicitly 0 = give everything
    if head == 0 and tail == 0:
        return content

    # Requested more than exists - return all
    if h + t >= total:
        return content

    # Build result based on what was requested
    if t == 0:
        # Head only
        selected = lines[:h]
        hint = f"\n\n[Showing first {h} of {total} {total_hint}. Use tail=N to see end]"
    elif h == 0:
        # Tail only
        selected = lines[-t:]
        hint = (
            f"\n\n[Showing last {t} of {total} {total_hint}. Use head=N to see start]"
        )
    else:
        # Both - sandwich with omission notice
        omitted = total - h - t
        middle = ["", f"... [{omitted} {total_hint} omitted] ...", ""]
        selected = lines[:h] + middle + lines[-t:]
        hint = f"\n\n[Showing first {h} + last {t} of {total} {total_hint}]"

    return "\n".join(selected) + hint


def truncate_output(
    output: str,
    config: TruncateConfig,
    temp_dir: Path | None = None,
    tool_name: str = "tool",
) -> str:
    """Apply framework-level truncation as safety net.

    Called after tool returns, before output goes to LLM context.
    This is the last line of defense against context overflow.

    Args:
        output: Tool output string
        config: Truncation configuration
        temp_dir: Directory for overflow temp files
        tool_name: Name of tool (for temp file naming)

    Returns:
        Possibly truncated output with notice appended
    """
    if not output:
        return output

    # Check if truncation needed
    output_bytes = len(output.encode("utf-8"))
    lines = output.splitlines()
    output_lines = len(lines)

    needs_truncate = output_bytes > config.max_bytes or output_lines > config.max_lines

    if not needs_truncate:
        return output

    # Write full output to temp file if configured
    temp_path: Path | None = None
    if config.temp_file and temp_dir:
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_path = temp_dir / f"{tool_name}-{uuid4().hex[:8]}.log"
        temp_path.write_text(output)

    # Apply line-level truncation first
    if config.line_max_chars:
        lines = [_truncate_line(line, config.line_max_chars) for line in lines]

    # Truncate by strategy
    if config.strategy == "head":
        kept = lines[: config.max_lines]
    else:  # tail
        kept = lines[-config.max_lines :]

    # Ensure byte limit
    result = "\n".join(kept)
    result_bytes = len(result.encode("utf-8"))

    if result_bytes > config.max_bytes:
        if config.strategy == "head":
            # Keep head bytes
            result = result.encode("utf-8")[: config.max_bytes].decode(
                "utf-8", errors="ignore"
            )
        else:
            # Keep tail bytes
            result = result.encode("utf-8")[-config.max_bytes :].decode(
                "utf-8", errors="ignore"
            )
        result_bytes = len(result.encode("utf-8"))

    # Build truncation notice
    notice_parts = [
        f"\n\n[Truncated: {_fmt_bytes(result_bytes)} of {_fmt_bytes(output_bytes)}"
    ]
    if temp_path:
        notice_parts.append(f", full output: {temp_path}")
    notice_parts.append(". Use head/tail params to navigate]")

    return result + "".join(notice_parts)


def _truncate_line(line: str, max_chars: int) -> str:
    """Truncate a single line if too long."""
    if len(line) <= max_chars:
        return line
    return line[:max_chars] + "..."


def _fmt_bytes(n: int) -> str:
    """Format bytes as human-readable."""
    if n < 1024:
        return f"{n}B"
    elif n < 1024 * 1024:
        return f"{n / 1024:.1f}KB"
    else:
        return f"{n / 1024 / 1024:.1f}MB"


__all__ = [
    "apply_head_tail",
    "truncate_output",
]
