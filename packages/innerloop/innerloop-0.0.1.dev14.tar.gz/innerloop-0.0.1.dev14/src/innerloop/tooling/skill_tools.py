"""
Skill Tools

Tools for interacting with the skills system:
- Skill: Meta-tool for activating skills (injects prompts into conversation)
- skill_list: List all available skills
- skill_describe: Get full content of a skill
- skill_read: Read a resource file from a skill
- skill_invoke: Execute a script from a skill
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ..types import Tool, ToolContext
from .base import LocalTool
from .skills import (
    SkillContextModification,
    SkillMessage,
    SkillState,
    create_skill_context_modification,
    create_skill_messages,
    generate_skill_tool_description,
    invoke_skill_script,
    read_skill_resource,
    resolve_base_dir,
)

# =============================================================================
# Special Return Type for Skill Tool
# =============================================================================


class SkillActivationResult:
    """Result from Skill tool activation.

    This special result type signals to the loop that it should:
    1. Inject the provided messages into the conversation
    2. Apply context modifications (allowed tools, model override)

    The loop should check for this type and handle it specially.
    """

    def __init__(
        self,
        messages: list[SkillMessage],
        context_modification: SkillContextModification,
        skill_name: str,
    ):
        self.messages = messages
        self.context_modification = context_modification
        self.skill_name = skill_name

    def __str__(self) -> str:
        """String representation for tool result."""
        return f'Skill "{self.skill_name}" activated. Follow the instructions above.'


# =============================================================================
# Skill Meta-Tool
# =============================================================================


class SkillTool(Tool):
    """Skill meta-tool that activates skills via prompt injection.

    This tool is special:
    1. Its description is dynamically generated to include available skills
    2. When executed, it returns a SkillActivationResult instead of a string
    3. The loop should handle this result by injecting messages

    The actual skill prompt injection happens via the SkillActivationResult,
    which the loop handles specially.
    """

    _skill_state: SkillState
    _token_budget: int

    def __init__(
        self,
        skill_state: SkillState,
        token_budget: int = 15000,
    ):
        # Generate initial description with available skills
        description = generate_skill_tool_description(skill_state.skills, token_budget)

        super().__init__(
            name="Skill",
            description=description,
            input_schema={
                "type": "object",
                "properties": {
                    "skill": {
                        "type": "string",
                        "description": 'The skill name (no arguments). E.g., "pdf" or "xlsx"',
                    }
                },
                "required": ["skill"],
            },
        )
        object.__setattr__(self, "_skill_state", skill_state)
        object.__setattr__(self, "_token_budget", token_budget)

    def get_description(self) -> str:
        """Get dynamic description with current available skills."""
        return generate_skill_tool_description(
            self._skill_state.skills, self._token_budget
        )

    async def execute(
        self, input: dict[str, Any], context: ToolContext | None = None
    ) -> tuple[str, bool]:
        """Execute the skill tool.

        Note: Returns a string because the loop expects that.
        The actual message injection happens through a different mechanism.
        The SkillActivationResult is attached as an attribute for the loop to check.

        Args:
            input: Tool input with "skill" key
            context: Tool context

        Returns:
            (result_string, is_error) tuple
        """
        skill_name = input.get("skill", "")

        # Find skill
        skill = self._skill_state.get_skill(skill_name)
        if skill is None:
            available = self._skill_state.list_names()
            return f"Skill '{skill_name}' not found. Available: {available}", True

        # Check if already active
        if self._skill_state.active_skill == skill_name:
            return f"Skill '{skill_name}' is already active", True

        # Create activation result
        messages = create_skill_messages(skill)
        context_mod = create_skill_context_modification(skill)
        result = SkillActivationResult(messages, context_mod, skill_name)

        # Store the activation result for the loop to access
        # The loop should check for _skill_activation attribute on the tool
        object.__setattr__(self, "_skill_activation", result)

        # Mark as active
        self._skill_state.active_skill = skill_name

        return str(result), False

    def get_activation(self) -> SkillActivationResult | None:
        """Get and clear the pending skill activation.

        The loop should call this after execute() to get the activation result.
        """
        result = getattr(self, "_skill_activation", None)
        if result is not None:
            object.__setattr__(self, "_skill_activation", None)
        return result


# =============================================================================
# Utility Tools
# =============================================================================


def _make_skill_list_tool(skill_state: SkillState) -> LocalTool:
    """Create skill_list tool."""

    def skill_list() -> str:
        """List all available skills with names and descriptions."""
        if not skill_state.skills:
            return "No skills available."

        lines = ["Available skills:"]
        for skill in skill_state.skills:
            mode_tag = " [mode]" if skill.mode else ""
            lines.append(f"- {skill.name}{mode_tag}: {skill.description}")
        return "\n".join(lines)

    return LocalTool(
        name="skill_list",
        description="List all available skills with names and descriptions.",
        input_schema={"type": "object", "properties": {}, "required": []},
        handler=skill_list,
        truncate=None,  # No truncation needed for list
    )


def _make_skill_describe_tool(skill_state: SkillState) -> LocalTool:
    """Create skill_describe tool."""

    def skill_describe(skill_name: str) -> str:
        """Load full skill content (alternative to Skill tool invocation).

        Args:
            skill_name: Name of the skill to describe.
        """
        skill = skill_state.get_skill(skill_name)
        if skill is None:
            available = skill_state.list_names()
            return f"Skill '{skill_name}' not found. Available: {available}"

        # Build full description
        lines = [
            f"# {skill.name}",
            f"**Description:** {skill.description}",
        ]

        if skill.version:
            lines.append(f"**Version:** {skill.version}")
        if skill.license:
            lines.append(f"**License:** {skill.license}")
        if skill.allowed_tools:
            lines.append(f"**Allowed tools:** {', '.join(skill.allowed_tools)}")
        if skill.model_override:
            lines.append(f"**Model override:** {skill.model_override}")
        if skill.scripts:
            script_names = [s.name for s in skill.scripts]
            lines.append(f"**Scripts:** {', '.join(script_names)}")

        lines.append("")
        lines.append("## Content")
        lines.append(resolve_base_dir(skill.content, skill.base_dir))

        return "\n".join(lines)

    return LocalTool(
        name="skill_describe",
        description="Load full skill content without activating it.",
        input_schema={
            "type": "object",
            "properties": {
                "skill_name": {"type": "string", "description": "Name of skill"}
            },
            "required": ["skill_name"],
        },
        handler=skill_describe,
        truncate=None,
    )


def _make_skill_read_tool(skill_state: SkillState) -> LocalTool:
    """Create skill_read tool."""

    def skill_read(skill_name: str, resource_path: str) -> str:
        """Read a bundled resource file from a skill.

        Args:
            skill_name: Name of the skill.
            resource_path: Relative path to resource file within skill directory.
        """
        skill = skill_state.get_skill(skill_name)
        if skill is None:
            available = skill_state.list_names()
            return f"Skill '{skill_name}' not found. Available: {available}"

        content, is_error = read_skill_resource(skill, resource_path)
        if is_error:
            return f"Error: {content}"
        return content

    return LocalTool(
        name="skill_read",
        description="Read a bundled resource file from a skill.",
        input_schema={
            "type": "object",
            "properties": {
                "skill_name": {"type": "string", "description": "Name of skill"},
                "resource_path": {
                    "type": "string",
                    "description": "Relative path to resource (e.g., 'references/guide.md')",
                },
            },
            "required": ["skill_name", "resource_path"],
        },
        handler=skill_read,
        truncate=None,
    )


def _make_skill_invoke_tool(skill_state: SkillState) -> LocalTool:
    """Create skill_invoke tool."""

    def skill_invoke(
        skill_name: str,
        script_name: str,
        args: list[str] | None = None,
        ctx: ToolContext | None = None,
    ) -> str:
        """Execute a skill's bundled script.

        Args:
            skill_name: Name of the skill.
            script_name: Name of script (without extension).
            args: Command line arguments.
            ctx: Tool context.
        """
        skill = skill_state.get_skill(skill_name)
        if skill is None:
            available = skill_state.list_names()
            return f"Skill '{skill_name}' not found. Available: {available}"

        # Use workdir from context if available
        cwd = ctx.workdir if ctx else None
        timeout = ctx.tool_timeout if ctx else 60.0

        output, is_error = invoke_skill_script(
            skill, script_name, args, cwd=cwd, timeout=timeout
        )

        if is_error:
            return f"Error: {output}"
        return output

    return LocalTool(
        name="skill_invoke",
        description="Execute a skill's bundled script.",
        input_schema={
            "type": "object",
            "properties": {
                "skill_name": {"type": "string", "description": "Name of skill"},
                "script_name": {
                    "type": "string",
                    "description": "Name of script (without extension)",
                },
                "args": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Command line arguments",
                },
            },
            "required": ["skill_name", "script_name"],
        },
        handler=skill_invoke,
        context_params=["ctx"],
        truncate=None,
    )


def create_skill_tools(
    skill_state: SkillState, token_budget: int = 15000
) -> list[Tool]:
    """Create all skill tools.

    Args:
        skill_state: Shared skill state
        token_budget: Max characters for available_skills in Skill tool description

    Returns:
        List of skill tools: [Skill, skill_list, skill_describe, skill_read, skill_invoke]
    """
    return [
        SkillTool(skill_state, token_budget),
        _make_skill_list_tool(skill_state),
        _make_skill_describe_tool(skill_state),
        _make_skill_read_tool(skill_state),
        _make_skill_invoke_tool(skill_state),
    ]


# Bundle for easy import
SKILL_TOOLS: list[Callable[[SkillState, int], list[Tool]]] = [create_skill_tools]


__all__ = [
    "SkillActivationResult",
    "SkillTool",
    "create_skill_tools",
    "SKILL_TOOLS",
]
