"""
Curryable Bash Tool

A bash tool that can be used directly or curried with constraints.

Usage:
    from innerloop.tooling import bash

    # Full reign - use bash directly as a tool
    loop = Loop(model="...", tools=[bash])

    # Soft guidance + best-effort blocking
    safe_bash = bash(
        use={"make": "Run make targets", "git": "Version control"},
        deny=["rm -rf", "sudo", "chmod 777"],
    )

    # Strict whitelist mode (maximum security)
    strict_bash = bash(
        allow=["make", "git", "uv"],
        strict=True,  # Disables shell features (pipes, globs, etc.)
    )

Security Notes:
    - `use`: Advisory only. Appears in tool description. All commands execute.
    - `allow`: Whitelist. Only commands starting with allowed prefixes execute.
    - `allow` + `strict=True`: Maximum security. No shell interpretation at all.
    - `deny`: Best-effort blocking with obfuscation detection. NOT a security boundary.

    For true isolation, use container-based sandboxing.
"""

from __future__ import annotations

import re
import shlex
import subprocess  # nosec B404
from dataclasses import dataclass
from typing import Any

from ..truncate import apply_head_tail
from ..types import TruncateConfig
from .base import LocalTool, ToolContext

# =============================================================================
# Shell feature detection for strict mode
# =============================================================================

# Patterns that detect shell features with helpful error messages
_SHELL_FEATURE_PATTERNS: list[tuple[re.Pattern[str], str, str]] = [
    # (pattern, feature_name, guidance)
    (
        re.compile(r"\|"),
        "pipe '|'",
        "Run each command separately and pass output between them manually.",
    ),
    (
        re.compile(r"&&"),
        "chain '&&'",
        "Run each command separately. Check the first result before running the next.",
    ),
    (
        re.compile(r"\|\|"),
        "chain '||'",
        "Run commands separately. Use conditional logic based on exit codes.",
    ),
    (
        re.compile(r";\s*\S"),  # Semicolon followed by another command
        "chain ';'",
        "Run each command as a separate tool call.",
    ),
    (
        re.compile(r"\$\([^)]+\)"),
        "command substitution '$(...)' ",
        "Run the inner command first, then use its output in the next command.",
    ),
    (
        re.compile(r"`[^`]+`"),
        "command substitution (backticks)",
        "Run the inner command first, then use its output in the next command.",
    ),
    (
        re.compile(r"(?<![\"'])\*(?![\"'])"),  # Glob * not in quotes
        "glob pattern '*'",
        "Use a glob/ls tool to find files first, then pass explicit paths.",
    ),
    (
        re.compile(r"(?<![\"'])\?(?![\"'])"),  # Glob ? not in quotes
        "glob pattern '?'",
        "Use a glob/ls tool to find files first, then pass explicit paths.",
    ),
    (
        re.compile(r"\[[^\]]+\]"),  # Bracket glob [abc]
        "glob pattern '[...]'",
        "Use a glob/ls tool to find files first, then pass explicit paths.",
    ),
    (
        re.compile(r">[^&]|>>"),  # Redirect > or >> (but not >&)
        "redirect '>' or '>>'",
        "Run the command, then use a file write tool to save the output.",
    ),
    (
        re.compile(r"<(?!\()"),  # Input redirect < (but not <() process sub)
        "redirect '<'",
        "Use a file read tool to get content, then pass it as an argument.",
    ),
    (
        re.compile(r"\$\{[^}]+\}"),
        "variable expansion '${...}'",
        "Variables are not expanded in strict mode. Use literal values.",
    ),
    (
        re.compile(r"\$[A-Za-z_][A-Za-z0-9_]*"),
        "variable '$VAR'",
        "Variables are not expanded in strict mode. Use literal values.",
    ),
]


def _detect_shell_features(command: str) -> str | None:
    """
    Detect shell features in a command and return a helpful error message.

    Returns None if no shell features detected, otherwise returns error message.
    """
    for pattern, feature_name, guidance in _SHELL_FEATURE_PATTERNS:
        if pattern.search(command):
            return (
                f"Strict mode: command contains {feature_name}.\n"
                f"Shell features are disabled in strict mode.\n"
                f"Suggestion: {guidance}"
            )
    return None


# =============================================================================
# Command normalization (for deny mode)
# =============================================================================


def _normalize_command(command: str) -> str:
    """
    Normalize a shell command to defeat common obfuscation techniques.

    This helps catch bypass attempts like:
    - su""do -> sudo (empty quote removal)
    - su''do -> sudo (empty single quote removal)
    - s\\udo -> sudo (backslash removal for non-special chars)
    - $'\\x73\\x75\\x64\\x6f' -> sudo (hex escape expansion)
    - rm   -rf -> rm -rf (whitespace collapse)

    The normalized command is used for deny pattern matching,
    while the original command is still executed.
    """
    normalized = command

    # Remove empty quote pairs: "" and ''
    # These are no-ops in shell but can evade pattern matching
    normalized = re.sub(r'""', "", normalized)
    normalized = re.sub(r"''", "", normalized)

    # IMPORTANT: Expand $'...' escapes BEFORE removing backslashes,
    # otherwise \xHH patterns get destroyed

    # Expand ANSI-C quoting $'...' sequences
    # These can hide commands using hex (\xHH) or octal (\NNN) escapes
    def expand_ansi_c_quotes(match: re.Match[str]) -> str:
        content = match.group(1)

        # Expand hex escapes: \xHH or \\xHH
        def hex_to_char(hex_match: re.Match[str]) -> str:
            hex_val = hex_match.group(1)
            try:
                return chr(int(hex_val, 16))
            except ValueError:
                return hex_match.group(0)

        content = re.sub(r"\\{1,2}x([0-9a-fA-F]{2})", hex_to_char, content)

        # Expand octal escapes: \NNN or \\NNN
        def octal_to_char(octal_match: re.Match[str]) -> str:
            octal_val = octal_match.group(1)
            try:
                return chr(int(octal_val, 8))
            except ValueError:
                return octal_match.group(0)

        content = re.sub(r"\\{1,2}([0-7]{1,3})", octal_to_char, content)

        return content

    normalized = re.sub(r"\$'([^']*)'", expand_ansi_c_quotes, normalized)

    # Remove backslashes before regular (non-special) characters
    # In shell, \a (where a is not a special char) just becomes a
    # Special chars in shell escaping: \n \t \r \\ \' \" \$ \` \!
    # We preserve those but remove backslashes before letters/digits
    # This runs AFTER $'...' expansion so we don't break hex escapes
    normalized = re.sub(r"\\([a-zA-Z0-9])", r"\1", normalized)

    # Collapse multiple whitespace into single space
    # Catches attempts like "rm    -rf" or "rm\t-rf"
    normalized = re.sub(r"\s+", " ", normalized)

    return normalized


def _to_regex(pattern: str) -> str:
    """
    Convert human-readable deny pattern to regex.

    "rm -rf"  -> r"\\brm\\s+\\-rf\\b"
    "sudo"    -> r"\\bsudo\\b"
    ">/etc/"  -> r">/etc/"  (no word boundaries for punctuation)

    If pattern already looks like regex (contains \\b or ^), keep as-is.
    """
    # Already regex? Keep as-is
    if r"\b" in pattern or pattern.startswith("^"):
        return pattern

    # Escape regex special chars except spaces
    escaped = re.escape(pattern)

    # Convert escaped spaces (\\ ) back to flexible whitespace
    escaped = escaped.replace(r"\ ", r"\s+")

    # Only add word boundaries around word characters
    # \b doesn't work before/after punctuation like > or /
    prefix = r"\b" if pattern and pattern[0].isalnum() else ""
    suffix = r"\b" if pattern and pattern[-1].isalnum() else ""

    return f"{prefix}{escaped}{suffix}"


# =============================================================================
# Configuration
# =============================================================================


@dataclass(frozen=True)
class BashConfig:
    """Configuration for bash tool constraints.

    Attributes:
        use: Recommended commands with descriptions (advisory only).
        allow: Whitelist of command prefixes (strict enforcement).
        deny: Patterns to block (best-effort, not a security boundary).
        deny_regex: Compiled regex patterns for deny list (internal).
        strict: If True, disable shell interpretation entirely (shell=False).
    """

    use: dict[str, str]  # {command: description} - advisory
    allow: tuple[str, ...]  # Command prefixes - strict whitelist
    deny: list[str]  # Patterns to block - best effort
    deny_regex: tuple[str, ...]  # Compiled regex patterns (internal)
    strict: bool  # If True, use shell=False


def _build_docstring(
    base: str,
    config: BashConfig | None,
) -> str:
    """Build docstring with use/allow/deny sections and security notes."""
    sections = [base.strip()]

    if config is None:
        return sections[0]

    # Strict mode notice
    if config.strict:
        sections.append(
            "\n[STRICT MODE] Shell features disabled. No pipes, globs, redirects, "
            "or variable expansion. Run commands individually with explicit arguments."
        )

    # Whitelist mode - strict security
    if config.allow:
        sections.append("\n[WHITELIST MODE] Only these command prefixes will execute:")
        for prefix in config.allow:
            sections.append(f"  - {prefix}")
        sections.append("\nAll other commands return an error without execution.")

    # Recommended commands - advisory only
    if config.use:
        sections.append("\nRecommended commands:")
        for cmd, desc in config.use.items():
            sections.append(f"  - {cmd}: {desc}")

    # Blocked patterns - best effort
    if config.deny:
        sections.append("\nBlocked patterns (best-effort, not a security boundary):")
        for pattern in config.deny:
            sections.append(f"  - {pattern}")

    return "\n".join(sections)


# =============================================================================
# Bash Tool
# =============================================================================


class BashTool(LocalTool):
    """Bash tool that can be curried with configuration."""

    _config: BashConfig | None
    _allow_prefixes: tuple[str, ...]
    _deny_patterns: list[re.Pattern[str]]
    _strict: bool

    def __init__(
        self,
        config: BashConfig | None = None,
    ):
        # Build docstring based on config
        description = _build_docstring(
            "Execute a shell command and return its output.",
            config,
        )

        # Build JSON schema with head/tail params
        input_schema = {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Shell command to execute",
                },
                "timeout": {
                    "type": "integer",
                    "description": "Optional timeout in seconds (overrides default)",
                },
                "head": {
                    "type": "integer",
                    "description": "Lines from start (0=none, default=0)",
                },
                "tail": {
                    "type": "integer",
                    "description": "Lines from end (0=none, default=200)",
                },
            },
            "required": ["command"],
        }

        # Configure truncation with temp_file for overflow
        truncate_config = TruncateConfig(
            max_bytes=50_000,
            max_lines=2000,
            strategy="tail",
            temp_file=True,
            line_max_chars=2000,
        )

        super().__init__(
            name="bash",
            description=description,
            input_schema=input_schema,
            handler=self._execute_handler,
            context_params=["ctx"],
            truncate=truncate_config,
        )

        # Store config using object.__setattr__ since LocalTool is frozen via Pydantic
        object.__setattr__(self, "_config", config)
        allow_prefixes = config.allow if config else ()
        object.__setattr__(self, "_allow_prefixes", allow_prefixes)
        deny_patterns = [re.compile(p) for p in config.deny_regex] if config else []
        object.__setattr__(self, "_deny_patterns", deny_patterns)
        strict = config.strict if config else False
        object.__setattr__(self, "_strict", strict)

    def _check_allowed(self, command: str) -> None:
        """Check if command starts with an allowed prefix.

        This is a strict whitelist check. Only commands that start with
        one of the allowed prefixes (followed by space or end-of-string)
        will be permitted to execute.

        Raises:
            ValueError: If command doesn't match any allowed prefix.
        """
        if not self._allow_prefixes:
            return  # No whitelist configured

        cmd = command.strip()
        for prefix in self._allow_prefixes:
            # Match exact prefix or prefix followed by space
            if cmd == prefix or cmd.startswith(prefix + " "):
                return  # Allowed

        raise ValueError(
            f"Command not in allowlist. Allowed prefixes: {list(self._allow_prefixes)}"
        )

    def _check_denied(self, command: str) -> None:
        """Check if command matches any deny pattern.

        Uses normalized command to defeat obfuscation attempts like:
        - Empty quote insertion: su""do -> sudo
        - Backslash escaping: s\\udo -> sudo
        - Hex/octal escapes: $'\\x73udo' -> sudo
        - Whitespace variations: rm   -rf -> rm -rf

        Note: This is best-effort blocking, NOT a security boundary.
        Sophisticated shell constructs can bypass pattern matching.
        """
        if not self._deny_patterns:
            return  # No deny patterns configured

        # Normalize the command to defeat obfuscation
        normalized = _normalize_command(command)

        for pattern in self._deny_patterns:
            # Check both original and normalized command
            if pattern.search(command) or pattern.search(normalized):
                raise ValueError(f"Command blocked by deny pattern: {command!r}")

    def _check_strict_mode(self, command: str) -> None:
        """Check for shell features that are not allowed in strict mode.

        Raises:
            ValueError: If shell features are detected, with helpful guidance.
        """
        if not self._strict:
            return  # Not in strict mode

        error_msg = _detect_shell_features(command)
        if error_msg:
            raise ValueError(error_msg)

    def _execute_handler(
        self,
        command: str,
        ctx: ToolContext | None = None,
        timeout: int | None = None,
        head: int | None = 0,
        tail: int | None = 200,
    ) -> str:
        """Execute the shell command.

        Args:
            command: Shell command to execute
            ctx: Tool context
            timeout: Optional timeout override
            head: Lines from start (0=none, default=0)
            tail: Lines from end (0=none, default=200)
        """
        # 1. Whitelist check (if allow mode)
        self._check_allowed(command)

        # 2. Strict mode check (if strict mode)
        self._check_strict_mode(command)

        # 3. Deny check (if deny mode)
        self._check_denied(command)

        # Determine timeout
        if timeout is not None:
            effective_timeout = timeout
        elif ctx is not None:
            effective_timeout = int(ctx.tool_timeout)
        else:
            effective_timeout = 60  # Default fallback

        # Determine working directory
        cwd = ctx.workdir if ctx else None

        # Execute based on strict mode
        if self._strict:
            # Strict mode: shell=False, parse with shlex
            try:
                args = shlex.split(command)
            except ValueError as e:
                raise ValueError(f"Failed to parse command: {e}") from e

            if not args:
                raise ValueError("Empty command")

            # Re-check allowlist against parsed command (first arg)
            if self._allow_prefixes:
                cmd_name = args[0]
                if cmd_name not in self._allow_prefixes:
                    raise ValueError(
                        f"Command '{cmd_name}' not in allowlist. "
                        f"Allowed: {list(self._allow_prefixes)}"
                    )

            result = subprocess.run(
                args,
                shell=False,
                capture_output=True,
                text=True,
                timeout=effective_timeout,
                cwd=cwd,
            )
        else:
            # Normal mode: shell=True
            # Security is handled via allow/deny lists and command normalization.
            result = subprocess.run(
                command,
                shell=True,  # nosec B602
                capture_output=True,
                text=True,
                timeout=effective_timeout,
                cwd=cwd,
            )

        output = result.stdout
        if result.stderr:
            output += f"\n[stderr]\n{result.stderr}"
        if result.returncode != 0:
            output += f"\n[exit code: {result.returncode}]"

        output = output.strip() or "(no output)"

        # Apply head/tail selection (framework truncation is the safety net)
        return apply_head_tail(output, head, tail, total_hint="lines")


# =============================================================================
# Bash Factory
# =============================================================================


class BashFactory:
    """
    Dual-purpose bash: use directly as a tool or curry with config.

    # Direct use as tool:
    loop = Loop(model="...", tools=[bash])

    # Curry with config (returns new tool):
    safe_bash = bash(use={...}, deny=[...])  # Soft guidance + blocking
    strict_bash = bash(allow=[...], strict=True)  # Maximum security
    """

    def __init__(self) -> None:
        self._default = BashTool()

    def __call__(
        self,
        *,
        use: dict[str, str] | None = None,
        allow: list[str] | None = None,
        deny: list[str] | None = None,
        strict: bool = False,
    ) -> BashTool:
        """Create a new bash tool with constraints.

        Args:
            use: Recommended commands with descriptions (advisory only).
                 Example: {"git": "Version control", "make": "Build system"}
            allow: Strict whitelist of command prefixes. Only commands starting
                   with these prefixes will execute. All others return an error.
                   Example: ["git", "make", "uv"]
            deny: Patterns to block (best-effort). Catches common obfuscation
                  but NOT a security boundary. Example: ["sudo", "rm -rf"]
            strict: If True, disable shell interpretation entirely (shell=False).
                    This prevents pipes, globs, redirects, and variable expansion.
                    Requires `allow` to be set. Provides maximum security.

        Returns:
            Configured BashTool instance.

        Raises:
            ValueError: If invalid combination of arguments is provided.
                - allow + use: Confusing semantics (use is advisory, allow is strict)
                - allow + deny: Redundant (allow is already a whitelist)
                - strict without allow: Strict mode requires a whitelist

        Security Notes:
            - For advisory guidance, use `use` + optional `deny`
            - For real security, use `allow` alone (whitelist mode)
            - For maximum security, use `allow` + `strict=True`
            - For true isolation, use container-based sandboxing
        """
        # Validate combinations
        if allow is not None and use is not None:
            raise ValueError(
                "Cannot combine 'allow' (strict whitelist) with 'use' (advisory). "
                "Use 'allow' alone for whitelist mode, or 'use' + 'deny' for guidance mode."
            )

        if allow is not None and deny is not None:
            raise ValueError(
                "Cannot combine 'allow' (strict whitelist) with 'deny' (best-effort block). "
                "'allow' already restricts to specific commands. Use 'allow' alone."
            )

        if strict and allow is None:
            raise ValueError(
                "Strict mode requires 'allow' (whitelist). "
                "Use bash(allow=['cmd1', 'cmd2'], strict=True)."
            )

        if use is None and allow is None and deny is None and not strict:
            # No config - return unconstrained tool
            return self._default

        deny_list = deny or []
        config = BashConfig(
            use=use or {},
            allow=tuple(allow) if allow else (),
            deny=deny_list,
            deny_regex=tuple(_to_regex(p) for p in deny_list),
            strict=strict,
        )
        return BashTool(config)

    # Forward tool protocol attributes to default tool
    @property
    def name(self) -> str:
        return self._default.name

    @property
    def description(self) -> str:
        return self._default.description

    def get_description(self) -> str:
        """Get the tool description (supports dynamic descriptions)."""
        return self._default.get_description()

    @property
    def input_schema(self) -> dict[str, Any]:
        return self._default.input_schema

    async def execute(
        self, input: dict[str, Any], context: ToolContext | None = None
    ) -> tuple[str, bool]:
        """Execute the default bash tool."""
        return await self._default.execute(input, context)


# The exported bash object - can be used directly or curried
bash = BashFactory()

__all__ = [
    "bash",
    "BashTool",
    "BashConfig",
    "_normalize_command",  # Exposed for testing
    "_to_regex",  # Exposed for testing
    "_detect_shell_features",  # Exposed for testing
]
