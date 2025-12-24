"""
InnerLoop SDK

Lightweight Python SDK for building LLM agent loops.

Features:
- Tool calling via @tool decorator
- Core tools (read, write, edit, bash, etc.)
- Structured output with Pydantic
- Session management (JSONL)
- Streaming (sync/async)
- Direct provider APIs (Anthropic, OpenAI, OpenRouter, local models)
"""

from .api import Loop, arun, astream, run, stream
from .call import CallResponse, ToolCall, acall, call
from .kits import Kit, KitContext, TodoKit
from .schema import JsonSchema
from .structured import ResponseTool
from .tooling import (
    # Base
    LocalTool,
    ToolContext,
    tool,
    # Bash (curryable)
    bash,
    BashTool,
    BashConfig,
    # Filesystem tools
    read,
    write,
    edit,
    glob,
    ls,
    grep,
    stat,
    chunk,
    FS_TOOLS,
    SAFE_FS_TOOLS,
    SecurityError,
    ConflictError,
    # Web tools
    fetch,
    download,
    search,
    WEB_TOOLS,
    # Skills
    Skill,
    SkillFrontmatter,
    SkillScript,
    SkillMessage,
    SkillContextModification,
    SkillState,
    SkillTool,
    load_skill,
    list_skills,
    create_skill_tools,
    # Bundles
    ALL_TOOLS,
)
from .types import (
    AssistantMessage,
    Config,
    DoneEvent,
    ErrorEvent,
    ImageEvent,
    ImagePart,
    Message,
    MessageEvent,
    Response,
    SessionUsageEvent,
    StructuredOutputEvent,
    TextEvent,
    TextPart,
    ThinkingConfig,
    ThinkingEvent,
    ThinkingLevel,
    Tool,
    ToolCallEvent,
    ToolResultMessage,
    ToolResultEvent,
    TurnStartEvent,
    Usage,
    UsageEvent,
    UserMessage,
)

__all__ = [
    # Core API
    "Loop",
    "run",
    "arun",
    "stream",
    "astream",
    # One-shot calls
    "call",
    "acall",
    "CallResponse",
    "ToolCall",
    # Schema
    "JsonSchema",
    # Tool decorator & types
    "tool",
    "Tool",
    "LocalTool",
    "ResponseTool",
    "ToolContext",
    # Bash (curryable)
    "bash",
    "BashTool",
    "BashConfig",
    # Filesystem tools
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
    "ConflictError",
    # Web tools
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
    "SkillTool",
    "load_skill",
    "list_skills",
    "create_skill_tools",
    # Kits
    "Kit",
    "KitContext",
    "TodoKit",
    # Bundles
    "ALL_TOOLS",
    # Events
    "TextEvent",
    "ThinkingEvent",
    "ImageEvent",
    "ToolCallEvent",
    "ToolResultEvent",
    "UsageEvent",
    "SessionUsageEvent",
    "TurnStartEvent",
    "ErrorEvent",
    "DoneEvent",
    "StructuredOutputEvent",
    "MessageEvent",
    # Config & Response
    "Config",
    "ThinkingLevel",
    "ThinkingConfig",
    "Response",
    "Usage",
    # Content parts (for vision)
    "TextPart",
    "ImagePart",
    # Message types
    "Message",
    "UserMessage",
    "AssistantMessage",
    "ToolResultMessage",
]
