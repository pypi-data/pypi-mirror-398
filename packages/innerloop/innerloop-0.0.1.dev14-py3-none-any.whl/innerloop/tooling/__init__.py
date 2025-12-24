"""
InnerLoop Tooling Subpackage

Provides curryable, stateful, and specialized tools for the agent loop.

Bash (curryable):
    from innerloop.tooling import bash

    # Full reign
    loop = Loop(model="...", tools=[bash])

    # Constrained
    safe_bash = bash(
        allow={"make": "Run make targets"},
        deny=["rm -rf", "sudo"],
        usage="Use make for builds"
    )
    loop = Loop(model="...", tools=[safe_bash])

Filesystem:
    from innerloop.tooling import read, write, edit, glob, ls, grep
    from innerloop.tooling import FS_TOOLS, SAFE_FS_TOOLS

    loop = Loop(model="...", tools=SAFE_FS_TOOLS)  # read-only tools

Web:
    from innerloop.tooling import fetch, download, search, WEB_TOOLS

    loop = Loop(model="...", tools=WEB_TOOLS)
"""

# Base infrastructure (re-exported)
from .base import LocalTool, ToolContext, tool

# Curryable bash
from .bash import BashConfig, BashTool, bash

# Filesystem tools
from .filesystem import (
    FS_TOOLS,
    SAFE_FS_TOOLS,
    SecurityError,
    chunk,
    edit,
    glob,
    grep,
    ls,
    read,
    stat,
    write,
)

# Web tools - optional, requires [web] extra
try:
    from .web import WEB_TOOLS, download, fetch, search

    _WEB_AVAILABLE = True
except ImportError:
    # Web extra not installed - provide placeholder that raises helpful error
    _WEB_AVAILABLE = False
    WEB_TOOLS: list[object] = []  # type: ignore[no-redef]

    def _web_not_installed(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise ImportError(
            "Web tools require the 'web' extra. "
            "Install with: pip install innerloop[web]"
        )

    fetch = download = search = _web_not_installed  # type: ignore[assignment]

# Skill tools
from .skill_tools import (
    SkillActivationResult,
    SkillTool,
    create_skill_tools,
)
from .skills import (
    Skill,
    SkillContextModification,
    SkillFrontmatter,
    SkillMessage,
    SkillScript,
    SkillState,
    create_skill_context_modification,
    create_skill_messages,
    discover_scripts,
    format_available_skills,
    generate_skill_tool_description,
    invoke_skill_script,
    list_skills,
    load_skill,
    parse_script_metadata,
    parse_skill_frontmatter,
    read_skill_resource,
    resolve_base_dir,
)

# Combined bundles
ALL_TOOLS = [*FS_TOOLS, bash, *WEB_TOOLS]

__all__ = [
    # Base
    "tool",
    "LocalTool",
    "ToolContext",
    # Bash
    "bash",
    "BashTool",
    "BashConfig",
    # Filesystem
    "read",
    "write",
    "edit",
    "glob",
    "ls",
    "grep",
    "stat",
    "chunk",
    "FS_TOOLS",
    "SAFE_FS_TOOLS",
    "SecurityError",
    # Web (available if [web] extra installed)
    "fetch",
    "download",
    "search",
    "WEB_TOOLS",
    # Skills
    "Skill",
    "SkillFrontmatter",
    "SkillScript",
    "SkillMessage",
    "SkillContextModification",
    "SkillState",
    "SkillActivationResult",
    "SkillTool",
    "parse_skill_frontmatter",
    "parse_script_metadata",
    "discover_scripts",
    "load_skill",
    "list_skills",
    "resolve_base_dir",
    "invoke_skill_script",
    "read_skill_resource",
    "format_available_skills",
    "generate_skill_tool_description",
    "create_skill_messages",
    "create_skill_context_modification",
    "create_skill_tools",
    # Bundles
    "ALL_TOOLS",
]
