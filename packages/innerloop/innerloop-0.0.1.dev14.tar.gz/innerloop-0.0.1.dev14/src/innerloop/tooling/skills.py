"""
Skills System

Claude Code compatible skills system for InnerLoop.

Skills are prompt templates that inject domain-specific instructions into the
conversation context. They consist of:
- SKILL.md file with YAML frontmatter + markdown body
- Optional scripts/ folder with executable scripts
- Optional references/ folder with documentation to load
- Optional templates/ folder with files referenced by path only

Skills are NOT executable code. They operate through prompt expansion and
context modification to change how the LLM processes subsequent requests.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

# Agent Skills spec: name must be 1-64 chars, lowercase alphanumeric + hyphens,
# no start/end hyphens, no consecutive hyphens
NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

# =============================================================================
# Skill Models
# =============================================================================


class SkillFrontmatter(BaseModel):
    """SKILL.md frontmatter - Agent Skills spec compliant.

    See: https://agentskills.io/specification

    Uses extra = "allow" to accept unknown fields for forward compatibility.
    """

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    # Required fields (Agent Skills spec)
    name: str = Field(min_length=1, max_length=64)
    description: str = Field(min_length=1, max_length=1024)

    # Optional fields (Agent Skills spec)
    license: str | None = None
    compatibility: str | None = Field(default=None, max_length=500)
    metadata: dict[str, Any] | None = None
    allowed_tools: str | None = Field(default=None, alias="allowed-tools")

    # InnerLoop extensions (not in Agent Skills spec)
    model: str | None = None  # "inherit" or specific model
    version: str | None = None
    disable_model_invocation: bool = Field(
        default=False, alias="disable-model-invocation"
    )
    mode: bool = False  # Is this a "mode command"?

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate name per Agent Skills spec.

        - Must be 1-64 characters (handled by Field)
        - Unicode lowercase alphanumeric and hyphens only
        - Cannot start or end with hyphens
        - No consecutive hyphens
        """
        if not NAME_PATTERN.match(v):
            raise ValueError(
                f"Invalid skill name '{v}': must be lowercase alphanumeric with "
                "single hyphens, cannot start/end with hyphens"
            )
        return v


class SkillScript(BaseModel):
    """A script bundled with a skill."""

    name: str  # Filename without extension
    path: Path  # Full path to script
    description: str = ""  # From /// script or docstring
    runner: list[str] = Field(
        default_factory=list
    )  # Command to run (e.g., ["python3"])
    dependencies: list[str] = Field(
        default_factory=list
    )  # From /// script dependencies


class Skill(BaseModel):
    """A loaded skill."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Identity
    name: str
    description: str

    # Content
    content: str  # Markdown body (Level 2)
    base_dir: Path  # Skill directory path

    # Scripts (auto-discovered)
    scripts: list[SkillScript] = Field(default_factory=list)

    # Optional fields (Agent Skills spec)
    license: str | None = None
    compatibility: str | None = None  # Environment requirements
    metadata: dict[str, Any] | None = None
    allowed_tools: list[str] | None = None  # Parsed from space-delimited string

    # InnerLoop extensions
    model_override: str | None = None  # "inherit" or model name
    version: str | None = None
    disable_model_invocation: bool = False
    mode: bool = False
    extra_fields: dict[str, Any] = Field(
        default_factory=dict
    )  # Unknown fields preserved


@dataclass
class SkillMessage:
    """A message injected by skill execution."""

    role: Literal["user"] = "user"
    content: str = ""
    is_meta: bool = False  # If True, hidden from user UI


@dataclass
class SkillContextModification:
    """Execution context changes from skill activation."""

    allowed_tools: list[str] = field(default_factory=list)  # Pre-approve these tools
    model_override: str | None = None  # Switch to this model


# =============================================================================
# Parsing Functions
# =============================================================================


def parse_skill_frontmatter(content: str) -> tuple[SkillFrontmatter, str]:
    """Parse YAML frontmatter from SKILL.md content.

    Args:
        content: Raw SKILL.md file content

    Returns:
        Tuple of (parsed frontmatter, markdown body)

    Raises:
        ValueError: If frontmatter is missing or invalid
    """
    # Match YAML frontmatter between --- markers
    pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
    match = re.match(pattern, content, re.DOTALL)

    if not match:
        raise ValueError("SKILL.md must have YAML frontmatter between --- markers")

    yaml_content = match.group(1)
    markdown_body = match.group(2).strip()

    # Parse YAML
    try:
        data = yaml.safe_load(yaml_content)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML frontmatter: {e}") from e

    if not isinstance(data, dict):
        raise ValueError("YAML frontmatter must be a mapping")

    # Parse into SkillFrontmatter (extra fields are allowed)
    frontmatter = SkillFrontmatter.model_validate(data)

    return frontmatter, markdown_body


def parse_script_metadata(content: str) -> dict[str, Any]:
    """Parse /// script metadata block from script content.

    Looks for PEP 723-style inline script metadata:
    # /// script
    # description = "Extract text from PDFs"
    # requires-python = ">=3.11"
    # dependencies = ["pypdf2", "pandas"]
    # ///

    Args:
        content: Script file content

    Returns:
        Dictionary with extracted metadata (description, dependencies, requires-python)
    """
    # Match /// script ... /// block (handles # or // comment prefixes)
    pattern = r"(?:^|\n)\s*(?:#|//)\s*///\s*script\s*\n(.*?)(?:#|//)\s*///\s*(?:\n|$)"
    match = re.search(pattern, content, re.DOTALL)

    if not match:
        return {}

    block = match.group(1)
    metadata: dict[str, Any] = {}

    # Parse TOML-like key = value pairs
    for line in block.split("\n"):
        # Remove comment prefix
        line = re.sub(r"^\s*(?:#|//)\s*", "", line).strip()
        if not line or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        # Parse value (handle strings, arrays)
        try:
            if value.startswith("["):
                # Parse array (simple string array only)
                items = re.findall(r'"([^"]*)"', value)
                metadata[key] = items
            elif value.startswith('"') and value.endswith('"'):
                metadata[key] = value[1:-1]
            else:
                metadata[key] = value
        except Exception:
            metadata[key] = value

    return metadata


def detect_script_runner(path: Path, content: str | None = None) -> list[str]:
    """Detect the runner command for a script.

    Args:
        path: Path to script file
        content: Optional pre-read content

    Returns:
        Runner command as list (e.g., ["python3"] or ["bash"])
    """
    if content is None:
        content = path.read_text()

    # Check shebang
    if content.startswith("#!"):
        shebang = content.split("\n")[0]
        if "python" in shebang:
            return ["python3"]
        elif "bash" in shebang:
            return ["bash"]
        elif "sh" in shebang:
            return ["sh"]
        elif "node" in shebang:
            return ["node"]

    # Fall back to extension
    suffix = path.suffix.lower()
    runners: dict[str, list[str]] = {
        ".py": ["python3"],
        ".sh": ["bash"],
        ".bash": ["bash"],
        ".js": ["node"],
        ".mjs": ["node"],
        ".ts": ["npx", "ts-node"],
        ".rb": ["ruby"],
        ".pl": ["perl"],
    }
    return runners.get(suffix, [])


def extract_docstring(content: str, suffix: str) -> str:
    """Extract module docstring from script content.

    Args:
        content: Script file content
        suffix: File extension (e.g., ".py")

    Returns:
        Extracted docstring or empty string
    """
    if suffix == ".py":
        # Python module docstring
        pattern = r'^(?:#.*\n)*\s*(?:"""(.*?)"""|\'\'\'(.*?)\'\'\')'
        match = re.match(pattern, content, re.DOTALL)
        if match:
            return (match.group(1) or match.group(2) or "").strip()

    elif suffix in (".js", ".mjs", ".ts"):
        # JSDoc style
        pattern = r"^\s*/\*\*(.*?)\*/"
        match = re.match(pattern, content, re.DOTALL)
        if match:
            # Clean up * prefixes
            doc = match.group(1)
            lines = [re.sub(r"^\s*\*\s?", "", line) for line in doc.split("\n")]
            return "\n".join(lines).strip()

    elif suffix in (".sh", ".bash"):
        # Shell comments at top (after shebang)
        lines = content.split("\n")
        doc_lines: list[str] = []
        started = False
        for line in lines:
            if line.startswith("#!"):
                continue
            if line.startswith("#"):
                started = True
                doc_lines.append(line[1:].strip())
            elif started:
                break
        return "\n".join(doc_lines).strip()

    return ""


def discover_scripts(skill_dir: Path) -> list[SkillScript]:
    """Auto-discover scripts in a skill's scripts/ directory.

    Args:
        skill_dir: Path to skill directory

    Returns:
        List of SkillScript objects
    """
    scripts_dir = skill_dir / "scripts"
    if not scripts_dir.exists():
        return []

    scripts: list[SkillScript] = []
    for script_path in scripts_dir.iterdir():
        if script_path.is_file() and not script_path.name.startswith("."):
            try:
                content = script_path.read_text()

                # Try /// script metadata first
                metadata = parse_script_metadata(content)

                # Get description
                description = metadata.get("description", "")
                if not description:
                    description = extract_docstring(content, script_path.suffix)

                # Get dependencies
                dependencies = metadata.get("dependencies", [])
                if isinstance(dependencies, str):
                    dependencies = [dependencies]

                # Detect runner
                runner = detect_script_runner(script_path, content)

                scripts.append(
                    SkillScript(
                        name=script_path.stem,
                        path=script_path,
                        description=description,
                        runner=runner,
                        dependencies=dependencies,
                    )
                )
            except Exception:
                # Skip unreadable files
                continue

    return scripts


def load_skill(skill_dir: Path) -> Skill:
    """Load a skill from a directory.

    Args:
        skill_dir: Path to skill directory (must contain SKILL.md)

    Returns:
        Loaded Skill object

    Raises:
        FileNotFoundError: If SKILL.md doesn't exist
        ValueError: If SKILL.md is invalid or name doesn't match directory
    """
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        raise FileNotFoundError(f"SKILL.md not found in {skill_dir}")

    content = skill_md.read_text()
    frontmatter, body = parse_skill_frontmatter(content)

    # Agent Skills spec: name must match parent directory name
    dir_name = skill_dir.name
    if frontmatter.name != dir_name:
        raise ValueError(
            f"Skill name '{frontmatter.name}' must match directory name '{dir_name}'"
        )

    # Parse allowed_tools from space-delimited string (Agent Skills spec)
    allowed_tools: list[str] | None = None
    if frontmatter.allowed_tools:
        allowed_tools = frontmatter.allowed_tools.split()

    # Determine model override
    model_override: str | None = None
    if frontmatter.model and frontmatter.model != "inherit":
        model_override = frontmatter.model

    # Collect extra fields (fields not in schema)
    known_fields = set(SkillFrontmatter.model_fields.keys())
    # Add alias names
    for field_info in SkillFrontmatter.model_fields.values():
        if field_info.alias:
            known_fields.add(field_info.alias)
    extra_fields = {
        k: v for k, v in frontmatter.model_dump().items() if k not in known_fields
    }

    # Discover scripts
    scripts = discover_scripts(skill_dir)

    return Skill(
        name=frontmatter.name,
        description=frontmatter.description,
        content=body,
        base_dir=skill_dir.resolve(),
        scripts=scripts,
        license=frontmatter.license,
        compatibility=frontmatter.compatibility,
        metadata=frontmatter.metadata,
        allowed_tools=allowed_tools,
        model_override=model_override,
        version=frontmatter.version,
        disable_model_invocation=frontmatter.disable_model_invocation,
        mode=frontmatter.mode,
        extra_fields=extra_fields,
    )


def list_skills(skills_paths: list[Path]) -> list[Skill]:
    """List all skills from given paths.

    Later paths override earlier paths (same skill name = last one wins).

    Args:
        skills_paths: List of directories to search for skills

    Returns:
        List of loaded Skill objects
    """
    skill_map: dict[str, Skill] = {}

    for base_path in skills_paths:
        base_path = Path(base_path).expanduser()
        if not base_path.exists():
            continue

        for entry in base_path.iterdir():
            if entry.is_dir() and (entry / "SKILL.md").exists():
                try:
                    skill = load_skill(entry)
                    skill_map[skill.name] = skill  # Override earlier
                except Exception:
                    # Skip invalid skills
                    continue

    return list(skill_map.values())


def resolve_base_dir(content: str, base_dir: Path) -> str:
    """Resolve {baseDir} placeholders in skill content.

    Args:
        content: Skill content with placeholders
        base_dir: Skill directory path

    Returns:
        Content with placeholders resolved
    """
    return content.replace("{baseDir}", str(base_dir))


# =============================================================================
# Skill Service Functions
# =============================================================================


def invoke_skill_script(
    skill: Skill,
    script_name: str,
    args: list[str] | None = None,
    cwd: Path | None = None,
    timeout: float = 60.0,
) -> tuple[str, bool]:
    """Execute a skill's bundled script.

    Args:
        skill: The skill containing the script
        script_name: Name of script (without extension)
        args: Command line arguments
        cwd: Working directory
        timeout: Execution timeout in seconds

    Returns:
        Tuple of (output, is_error)
    """
    # Find script
    script = next((s for s in skill.scripts if s.name == script_name), None)
    if script is None:
        available = [s.name for s in skill.scripts]
        return f"Script '{script_name}' not found. Available: {available}", True

    if not script.runner:
        return f"Cannot determine how to run {script.path}", True

    # Build command
    cmd = [*script.runner, str(script.path), *(args or [])]

    try:
        result = subprocess.run(
            cmd,
            cwd=cwd or skill.base_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = result.stdout + result.stderr
        return output.strip(), result.returncode != 0
    except subprocess.TimeoutExpired:
        return f"Script timed out after {timeout}s", True
    except Exception as e:
        return f"Error running script: {e}", True


def read_skill_resource(skill: Skill, resource_path: str) -> tuple[str, bool]:
    """Read a bundled resource file from a skill.

    Only allows reading files within the skill directory.

    Args:
        skill: The skill to read from
        resource_path: Relative path to resource file

    Returns:
        Tuple of (content, is_error)
    """
    # Resolve path relative to skill base_dir
    full_path = (skill.base_dir / resource_path).resolve()

    # Security: ensure path is within skill directory
    try:
        full_path.relative_to(skill.base_dir.resolve())
    except ValueError:
        return f"Path '{resource_path}' escapes skill directory", True

    if not full_path.exists():
        return f"Resource '{resource_path}' not found", True

    if not full_path.is_file():
        return f"'{resource_path}' is not a file", True

    try:
        return full_path.read_text(), False
    except Exception as e:
        return f"Error reading resource: {e}", True


def format_available_skills(skills: list[Skill], token_budget: int = 15000) -> str:
    """Format skills for injection into Skill tool description.

    Args:
        skills: List of skills to format
        token_budget: Maximum characters (rough token estimate)

    Returns:
        Formatted XML string for <available_skills> section
    """
    lines: list[str] = ["<available_skills>"]
    current_length = len(lines[0])

    for skill in skills:
        # Skip skills with disable_model_invocation
        if skill.disable_model_invocation:
            continue

        skill_block = f"""<skill>
<name>
{skill.name}
</name>
<description>
{skill.description}
</description>
<location>
{skill.base_dir.parent.name}
</location>
</skill>"""

        if current_length + len(skill_block) > token_budget:
            break

        lines.append(skill_block)
        current_length += len(skill_block)

    lines.append("</available_skills>")
    return "\n".join(lines)


def generate_skill_tool_description(
    skills: list[Skill], token_budget: int = 15000
) -> str:
    """Generate the full Skill tool description with available_skills.

    Args:
        skills: List of available skills
        token_budget: Maximum characters for available_skills section

    Returns:
        Complete Skill tool description
    """
    available_skills = format_available_skills(skills, token_budget)

    return f"""Execute a skill within the main conversation

<skills_instructions>
When users ask you to perform tasks, check if any of the available skills below can help complete the task more effectively. Skills provide specialized capabilities and domain knowledge.

How to use skills:
- Invoke skills using this tool with the skill name only (no arguments)
- When you invoke a skill, you will see <command-message>The "{{name}}" skill is loading</command-message>
- The skill's prompt will expand and provide detailed instructions on how to complete the task
- Examples:
  - `skill: "pdf"` - invoke the pdf skill
  - `skill: "xlsx"` - invoke the xlsx skill
  - `skill: "ms-office-suite:pdf"` - invoke using fully qualified name

Important:
- Only use skills listed in <available_skills> below
- Do not invoke a skill that is already running
- Do not use this tool for built-in CLI commands (like /help, /clear, etc.)
</skills_instructions>

{available_skills}
"""


# =============================================================================
# Skill Tool Implementation
# =============================================================================


@dataclass
class SkillState:
    """Shared state for skill tools.

    Tracks loaded skills and provides access to skill information.
    Passed via ToolContext.
    """

    skills: list[Skill] = field(default_factory=list)
    active_skill: str | None = None
    skills_paths: list[Path] = field(default_factory=list)

    def get_skill(self, name: str) -> Skill | None:
        """Get a skill by name."""
        return next((s for s in self.skills if s.name == name), None)

    def list_names(self) -> list[str]:
        """List all skill names."""
        return [s.name for s in self.skills]


def create_skill_messages(skill: Skill) -> list[SkillMessage]:
    """Create the two-message injection for skill activation.

    Args:
        skill: The skill to activate

    Returns:
        List of two SkillMessages (visible metadata + hidden prompt)
    """
    # Message 1: Visible metadata (command-message format)
    visible_content = (
        f'<command-message>The "{skill.name}" skill is loading</command-message>\n'
        f"<command-name>{skill.name}</command-name>"
    )

    # Message 2: Hidden skill prompt with {baseDir} resolved
    prompt_content = resolve_base_dir(skill.content, skill.base_dir)

    return [
        SkillMessage(content=visible_content, is_meta=False),
        SkillMessage(content=prompt_content, is_meta=True),
    ]


def create_skill_context_modification(skill: Skill) -> SkillContextModification:
    """Create context modification for skill activation.

    Args:
        skill: The activated skill

    Returns:
        SkillContextModification with tool permissions and model override
    """
    return SkillContextModification(
        allowed_tools=skill.allowed_tools or [],
        model_override=skill.model_override,
    )


__all__ = [
    # Models
    "SkillFrontmatter",
    "SkillScript",
    "Skill",
    "SkillMessage",
    "SkillContextModification",
    "SkillState",
    # Parsing
    "parse_skill_frontmatter",
    "parse_script_metadata",
    "detect_script_runner",
    "extract_docstring",
    "discover_scripts",
    "load_skill",
    "list_skills",
    "resolve_base_dir",
    # Service
    "invoke_skill_script",
    "read_skill_resource",
    "format_available_skills",
    "generate_skill_tool_description",
    # Two-message injection
    "create_skill_messages",
    "create_skill_context_modification",
]
