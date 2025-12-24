"""
Filesystem Tools

Standard tools for file operations with jailed paths.
All file tools are jailed to workdir to prevent path traversal.

Usage:
    from innerloop.tooling import read, write, edit, glob, ls, grep

    loop = Loop(model="...", tools=[read, write, edit, glob, ls, grep])

    # Or use the collections
    from innerloop.tooling import FS_TOOLS, SAFE_FS_TOOLS
    loop = Loop(model="...", tools=SAFE_FS_TOOLS)  # read-only tools
"""

from __future__ import annotations

import hashlib
import mimetypes
import re
from pathlib import Path

from ..truncate import apply_head_tail
from ..types import ToolContext
from .base import LocalTool, tool


class SecurityError(ValueError):
    """Raised when a path escapes the allowed directory."""

    pass


class ConflictError(ValueError):
    """Raised when file was modified since last read.

    This exception is raised during optimistic concurrency control when
    the file's content hash doesn't match the expected hash from a prior read.
    The caller should re-read the file and retry the operation.
    """

    pass


def _compute_hash(content: str) -> str:
    """Compute short content hash for conflict detection.

    Uses SHA-256 truncated to 16 hex characters (64 bits), providing
    collision probability of ~1 in 2^32 for birthday attack.
    Sufficient for conflict detection (not cryptographic security).

    Args:
        content: File content to hash

    Returns:
        16-character hexadecimal hash string
    """
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]


def _resolve_path(user_path: str, ctx: ToolContext) -> Path:
    """Resolve a user path to an absolute path.

    Resolution strategy:
    1. Absolute paths in allowed directories (temp_dir, read_paths, write_paths,
       workdir) are kept as-is
    2. Other absolute paths are returned as-is (will fail permission check)
    3. Relative paths are resolved relative to workdir

    Args:
        user_path: User-provided path (relative or absolute)
        ctx: Tool context with workdir, temp_dir, read_paths, write_paths

    Returns:
        Resolved absolute Path object
    """
    # Check if it's an absolute path
    if user_path.startswith("/"):
        target = Path(user_path).resolve()

        # Check if it's in temp_dir
        if ctx.temp_dir:
            try:
                target.relative_to(ctx.temp_dir)
                return target
            except ValueError:
                pass

        # Check if it's in workdir
        try:
            target.relative_to(ctx.workdir)
            return target
        except ValueError:
            pass

        # Check if it's in any read_path
        for rp in ctx.read_paths:
            try:
                target.relative_to(rp)
                return target
            except ValueError:
                pass

        # Check if it's in any write_path
        for wp in ctx.write_paths:
            try:
                target.relative_to(wp)
                return target
            except ValueError:
                pass

        # Not in any allowed directory - return as-is (permission check will fail)
        return target

    # Relative path: resolve relative to workdir
    return (ctx.workdir / user_path).resolve()


def _secure_path(user_path: str, workdir: Path, temp_dir: Path | None = None) -> Path:
    """
    Resolve a path and verify it's inside workdir or temp_dir.

    DEPRECATED: Use _check_read_path or _check_write_path instead.
    This function is kept for backwards compatibility.

    Args:
        user_path: User-provided path (relative or absolute)
        workdir: The working directory to jail paths to
        temp_dir: Optional temp directory (for reading overflow files)

    Returns:
        Resolved Path object guaranteed to be inside workdir or temp_dir

    Raises:
        SecurityError: If path escapes both directories
    """
    # Check if this looks like a temp_dir path (absolute path starting with temp prefix)
    if temp_dir and user_path.startswith(str(temp_dir)):
        target = Path(user_path).resolve()
        try:
            target.relative_to(temp_dir)
            return target
        except ValueError:
            pass  # Fall through to workdir check

    # Handle absolute paths by making them relative to workdir
    if user_path.startswith("/"):
        user_path = user_path.lstrip("/")

    # Resolve relative to workdir
    target = (workdir / user_path).resolve()

    # Check for jailbreak (handles ../, symlinks, etc.)
    try:
        target.relative_to(workdir)
    except ValueError as e:
        raise SecurityError(
            f"Security error: path '{user_path}' escapes working directory"
        ) from e

    return target


def _format_allowed_paths(ctx: ToolContext, for_write: bool = False) -> str:
    """Format allowed paths for error messages."""
    paths = [str(ctx.workdir)]
    if for_write:
        paths.extend(str(p) for p in ctx.write_paths)
    else:
        paths.extend(str(p) for p in ctx.read_paths)
        paths.extend(str(p) for p in ctx.write_paths)
    return ", ".join(paths[:3]) + ("..." if len(paths) > 3 else "")


def _check_read_path(user_path: str, ctx: ToolContext) -> Path:
    """Resolve a path and verify read access.

    Args:
        user_path: User-provided path (relative or absolute)
        ctx: Tool context with permission info

    Returns:
        Resolved Path object that is readable

    Raises:
        SecurityError: If path is not readable
    """
    target = _resolve_path(user_path, ctx)

    if not ctx.can_read(target):
        allowed = _format_allowed_paths(ctx, for_write=False)
        raise SecurityError(f"Read not allowed: {user_path} (allowed: {allowed})")

    return target


def _check_write_path(user_path: str, ctx: ToolContext) -> Path:
    """Resolve a path and verify write access.

    Args:
        user_path: User-provided path (relative or absolute)
        ctx: Tool context with permission info

    Returns:
        Resolved Path object that is writable

    Raises:
        SecurityError: If path is not writable
    """
    target = _resolve_path(user_path, ctx)

    if not ctx.can_write(target):
        allowed = _format_allowed_paths(ctx, for_write=True)
        raise SecurityError(f"Write not allowed: {user_path} (allowed: {allowed})")

    return target


@tool
def read(
    ctx: ToolContext,
    file_path: str,
    head: int | None = 100,
    tail: int | None = 100,
) -> str:
    """Read contents of a file.

    Returns content with hash header for use in subsequent writes:
        [hash:abc123def456]
        <file content>

    The hash enables optimistic concurrency control - pass it to write()
    or edit() via expect_hash to detect conflicts when multiple agents
    modify the same file.

    Args:
        file_path: Path to the file to read (relative to working directory)
        head: Lines from start (0=none, None=no limit, default=100)
        tail: Lines from end (0=none, None=no limit, default=100)

    Examples:
        read("log.txt", head=0, tail=100)  # Last 100 lines
        read("main.py", head=50, tail=50)  # First 50 + last 50
        read("config.json", head=None, tail=None)  # Entire file
    """
    target = _check_read_path(file_path, ctx)
    if not target.exists():
        raise FileNotFoundError(f"file not found: {file_path}")
    if target.is_dir():
        raise IsADirectoryError(f"{file_path} is a directory, not a file")
    content = target.read_text()
    content_hash = _compute_hash(content)
    truncated = apply_head_tail(content, head, tail, total_hint="lines")
    return f"[hash:{content_hash}]\n{truncated}"


@tool(truncate=False)
def write(
    ctx: ToolContext,
    file_path: str,
    content: str,
    expect_hash: str | None = None,
    force: bool = False,
) -> str:
    """Create or overwrite a file.

    Supports optimistic concurrency control via content hashing. When
    expect_hash is provided, the write will fail with ConflictError if
    the file was modified since the prior read.

    Args:
        file_path: Path to the file to write (relative to working directory)
        content: Content to write to the file
        expect_hash: Hash from prior read(). If provided and file has changed
                     since that read, raises ConflictError.
        force: Skip hash check (for intentional overwrites)

    Raises:
        ConflictError: File was modified since read. Re-read and retry.
    """
    target = _check_write_path(file_path, ctx)

    # Check for conflicts if hash provided
    if expect_hash and not force and target.exists():
        current_hash = _compute_hash(target.read_text())
        if current_hash != expect_hash:
            raise ConflictError(
                f"Conflict: file modified since read. "
                f"Expected hash {expect_hash}, current is {current_hash}. "
                f"Re-read the file and retry your edit."
            )

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)
    new_hash = _compute_hash(content)
    return f"Wrote {len(content)} bytes to {file_path} [hash:{new_hash}]"


@tool(truncate=False)
def edit(
    ctx: ToolContext,
    file_path: str,
    old_text: str,
    new_text: str,
    expect_hash: str | None = None,
) -> str:
    """Edit a file by replacing exact text.

    Supports optimistic concurrency control via content hashing. When
    expect_hash is provided, the edit will fail with ConflictError if
    the file was modified since the prior read.

    Args:
        file_path: Path to the file to edit (relative to working directory)
        old_text: Text to find and replace (must be unique in file)
        new_text: Text to replace with
        expect_hash: Hash from prior read(). Prevents lost updates.

    Raises:
        ConflictError: File was modified since read. Re-read and retry.
    """
    target = _check_write_path(file_path, ctx)
    if not target.exists():
        raise FileNotFoundError(f"file not found: {file_path}")

    content = target.read_text()
    current_hash = _compute_hash(content)

    # Check for conflicts
    if expect_hash and current_hash != expect_hash:
        raise ConflictError(
            "Conflict: file modified since read. Re-read the file and retry your edit."
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
    return f"Replaced text in {file_path} [hash:{new_hash}]"


@tool
def glob(
    ctx: ToolContext,
    pattern: str,
    directory: str = ".",
    head: int | None = 500,
    tail: int | None = 0,
) -> str:
    """Find files matching a glob pattern.

    Args:
        pattern: Glob pattern (e.g., "*.py", "src/**/*.js")
        directory: Directory to search in (relative to working directory)
        head: Results from start (0=none, None=no limit, default=500)
        tail: Results from end (0=none, None=no limit, default=0)
    """
    target = _check_read_path(directory, ctx)
    if not target.exists():
        raise FileNotFoundError(f"directory not found: {directory}")

    matches = list(target.glob(pattern))

    # Filter to only readable matches
    safe_matches = []
    for m in matches:
        resolved = m.resolve()
        if ctx.can_read(resolved):
            safe_matches.append(m)

    if not safe_matches:
        return f"No files found matching {pattern}"

    # Show paths relative to target directory
    result = "\n".join(str(p.relative_to(target)) for p in sorted(safe_matches))
    return apply_head_tail(result, head, tail, total_hint="matches")


@tool
def ls(
    ctx: ToolContext,
    directory: str = ".",
    head: int | None = 500,
    tail: int | None = 0,
) -> str:
    """List files and directories.

    Args:
        directory: Directory to list (relative to working directory)
        head: Entries from start (0=none, None=no limit, default=500)
        tail: Entries from end (0=none, None=no limit, default=0)
    """
    target = _check_read_path(directory, ctx)
    if not target.exists():
        raise FileNotFoundError(f"directory not found: {directory}")
    if not target.is_dir():
        raise NotADirectoryError(f"{directory} is not a directory")

    items = sorted(target.iterdir(), key=lambda p: p.name)
    lines = []
    for item in items:
        prefix = "[DIR] " if item.is_dir() else "      "
        lines.append(f"{prefix}{item.name}")

    if not lines:
        return "(empty directory)"

    result = "\n".join(lines)
    return apply_head_tail(result, head, tail, total_hint="entries")


@tool
def grep(
    ctx: ToolContext,
    pattern: str,
    path: str = ".",
    file_pattern: str | None = None,
    head: int | None = 100,
    tail: int | None = 0,
) -> str:
    """Search file contents for a regex pattern.

    Args:
        pattern: Regex to match in file contents (e.g., "def.*foo")
        path: File or directory to search
        file_pattern: Glob to filter which files to search (e.g., "*.py")
        head: Results from start (0=none, None=no limit, default=100)
        tail: Results from end (0=none, None=no limit, default=0)
    """
    target = _check_read_path(path, ctx)
    if not target.exists():
        raise FileNotFoundError(f"path not found: {path}")

    # Compile regex
    try:
        regex = re.compile(pattern)
    except re.error as e:
        raise ValueError(f"invalid regex: {e}") from e

    results: list[str] = []

    # Get files to search - use generator for lazy evaluation
    if target.is_file():
        files = iter([target])
    else:
        glob_pat = file_pattern or "**/*"
        # Use generator expression to avoid materializing all files at once
        files = (
            f
            for f in target.glob(glob_pat)
            if f.is_file() and ctx.can_read(f.resolve())
        )

    for file in files:
        try:
            # Read line-by-line to avoid loading entire file into memory
            with file.open(encoding="utf-8", errors="replace") as fh:
                for i, line in enumerate(fh, 1):
                    line = line.rstrip("\n\r")
                    if regex.search(line):
                        # Show path relative to target directory (or filename if target is file)
                        if target.is_file():
                            rel_path = file.name
                        else:
                            rel_path = str(file.relative_to(target))
                        results.append(f"{rel_path}:{i}: {line}")
        except (PermissionError, OSError):
            continue

    if not results:
        return f"No matches found for pattern: {pattern}"

    result = "\n".join(results)
    return apply_head_tail(result, head, tail, total_hint="matches")


@tool
def stat(
    ctx: ToolContext,
    path: str,
    target_chunk_bytes: int = 40_000,
    overlap_lines: int = 50,
) -> str:
    """Analyze file and calculate optimal chunking strategy.

    Args:
        path: Path to the file to analyze (relative to working directory)
        target_chunk_bytes: Target bytes per chunk (~30K tokens at 40KB default)
        overlap_lines: Lines of overlap between adjacent chunks (default=50)
    """
    target = _check_read_path(path, ctx)
    if not target.exists():
        raise FileNotFoundError(f"file not found: {path}")
    if target.is_dir():
        raise IsADirectoryError(f"{path} is a directory, not a file")

    content = target.read_text()
    lines = content.splitlines()
    total_lines = len(lines)
    total_bytes = len(content.encode("utf-8"))

    # Detect file type
    mime_type, _ = mimetypes.guess_type(str(target))
    file_type = mime_type or "text/plain"

    # Line analysis
    line_lengths = [len(line.encode("utf-8")) for line in lines]
    avg_line_bytes = total_bytes // total_lines if total_lines > 0 else 0

    # Find longest line
    longest_line_bytes = 0
    longest_line_num = 0
    soft_limit = 500
    long_lines: list[tuple[int, int]] = []

    for i, length in enumerate(line_lengths, 1):
        if length > longest_line_bytes:
            longest_line_bytes = length
            longest_line_num = i
        if length > soft_limit:
            long_lines.append((i, length))

    # Build output
    result = [
        "=== File Stats ===",
        f"path: {path}",
        f"lines: {total_lines:,}",
        f"bytes: {total_bytes:,}",
        f"type: {file_type}",
        "",
        "=== Line Analysis ===",
        f"avg_line_bytes: {avg_line_bytes}",
        f"longest_line: {longest_line_bytes} bytes (line {longest_line_num})",
    ]

    # Warn about long lines
    if long_lines:
        result.append(
            f"⚠️  Warning: {len(long_lines)} line(s) exceed {soft_limit} byte soft limit"
        )
        for line_num, length in long_lines[:5]:  # Show first 5
            result.append(f"   line {line_num}: {length} bytes")
        if len(long_lines) > 5:
            result.append(f"   ... and {len(long_lines) - 5} more")

    # Calculate chunking plan
    if total_lines == 0:
        result.extend(
            ["", "=== Chunking Plan ===", "File is empty, no chunking needed."]
        )
    else:
        # Calculate lines per chunk based on target bytes
        lines_per_chunk = (
            max(1, target_chunk_bytes // avg_line_bytes)
            if avg_line_bytes > 0
            else total_lines
        )

        # Calculate chunk count accounting for overlap
        if lines_per_chunk >= total_lines:
            chunk_count = 1
        else:
            effective_stride = lines_per_chunk - overlap_lines
            if effective_stride <= 0:
                effective_stride = max(1, lines_per_chunk // 2)
            chunk_count = 1 + (
                (total_lines - lines_per_chunk + effective_stride - 1)
                // effective_stride
            )

        result.extend(
            [
                "",
                f"=== Chunking Plan (target: {target_chunk_bytes // 1000}KB, overlap: {overlap_lines} lines) ===",
                f"recommended_chunk_size: {lines_per_chunk} lines",
                f"chunk_count: {chunk_count}",
                "",
                "chunks:",
            ]
        )

        # Generate chunk descriptions
        effective_stride = lines_per_chunk - overlap_lines
        if effective_stride <= 0:
            effective_stride = max(1, lines_per_chunk // 2)

        for i in range(chunk_count):
            start_line = i * effective_stride
            end_line = min(start_line + lines_per_chunk, total_lines)

            # Calculate approximate bytes for this chunk
            chunk_bytes = sum(line_lengths[start_line:end_line])

            result.append(
                f"  {i}: lines {start_line + 1}-{end_line} (~{chunk_bytes // 1000}KB)"
            )

        result.extend(
            [
                "",
                f'Use: chunk("{path}", index=0, size={lines_per_chunk}, overlap={overlap_lines})',
            ]
        )

    return "\n".join(result)


@tool
def chunk(
    ctx: ToolContext,
    path: str,
    index: int,
    size: int,
    overlap: int = 50,
) -> str:
    """Read a specific chunk of a file.

    Args:
        path: Path to the file to read (relative to working directory)
        index: Zero-based chunk index
        size: Lines per chunk
        overlap: Lines of overlap between chunks (default=50)
    """
    target = _check_read_path(path, ctx)
    if not target.exists():
        raise FileNotFoundError(f"file not found: {path}")
    if target.is_dir():
        raise IsADirectoryError(f"{path} is a directory, not a file")

    content = target.read_text()
    lines = content.splitlines()
    total_lines = len(lines)

    if total_lines == 0:
        return "(empty file)"

    if index < 0:
        raise ValueError(f"index must be non-negative, got {index}")
    if size <= 0:
        raise ValueError(f"size must be positive, got {size}")

    # Calculate effective stride and chunk count
    effective_stride = size - overlap
    if effective_stride <= 0:
        effective_stride = max(1, size // 2)

    if size >= total_lines:
        chunk_count = 1
    else:
        chunk_count = 1 + (
            (total_lines - size + effective_stride - 1) // effective_stride
        )

    if index >= chunk_count:
        raise ValueError(
            f"index {index} out of range (file has {chunk_count} chunk(s) with size={size})"
        )

    # Calculate start and end lines
    start_line = index * effective_stride
    end_line = min(start_line + size, total_lines)

    # Extract chunk content
    chunk_lines = lines[start_line:end_line]
    chunk_content = "\n".join(chunk_lines)

    # Build result with markers
    result = [
        f"=== chunk {index}/{chunk_count} (lines {start_line + 1}-{end_line}) ===",
        "",
        chunk_content,
        "",
        f"=== end chunk {index}/{chunk_count} ===",
    ]

    return "\n".join(result)


# Full filesystem tools (read and write operations)
FS_TOOLS: list[LocalTool] = [read, write, edit, glob, ls, grep, stat, chunk]

# Safe filesystem tools (read-only operations)
SAFE_FS_TOOLS: list[LocalTool] = [read, glob, ls, grep, stat, chunk]

__all__ = [
    # Individual tools
    "read",
    "write",
    "edit",
    "glob",
    "ls",
    "grep",
    "stat",
    "chunk",
    # Tool collections
    "FS_TOOLS",
    "SAFE_FS_TOOLS",
    # Exceptions
    "SecurityError",
    "ConflictError",
]
