"""
KBKit - Knowledge Base toolkit for Senpai curator.

Provides semantic tools for curating the procedure knowledge base.
Used by SenpaiKit's internal Loop.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from innerloop import Kit, Tool, ToolContext, tool

from .models import Approach, Nudge, Problem
from .utils import (
    ISSUE_TEMPLATE,
    NUDGE_TEMPLATE,
    PROBLEM_TEMPLATE,
    SKILL_TEMPLATE,
    approach_path,
    issue_path,
    nudge_path,
    problem_path,
    skill_path,
    slugify,
)


def _parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """Parse YAML frontmatter from markdown content.

    Args:
        content: Markdown content with optional YAML frontmatter

    Returns:
        Tuple of (frontmatter dict, body markdown)
    """
    pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
    match = re.match(pattern, content, re.DOTALL)

    if not match:
        return {}, content

    yaml_content = match.group(1)
    body = match.group(2).strip()

    try:
        data = yaml.safe_load(yaml_content)
        if not isinstance(data, dict):
            return {}, content
        return data, body
    except yaml.YAMLError:
        return {}, content


def _update_frontmatter(content: str, updates: dict[str, Any]) -> str:
    """Update frontmatter values in markdown content.

    Args:
        content: Markdown content with YAML frontmatter
        updates: Dict of values to update

    Returns:
        Updated markdown content
    """
    frontmatter, body = _parse_frontmatter(content)
    frontmatter.update(updates)

    yaml_content = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)
    return f"---\n{yaml_content}---\n{body}"


class KBKit(Kit):
    """Knowledge Base toolkit for Senpai curator.

    Provides semantic tools for curating the procedure knowledge base.
    Used by SenpaiKit's internal Loop.
    """

    def __init__(self, kb_path: Path):
        """Initialize KBKit.

        Args:
            kb_path: Path to knowledge base directory
        """
        self.kb_path = kb_path.resolve()

    def get_tools(self) -> list[Tool]:
        """Return semantic KB tools."""
        return [
            self._list_problems_tool(),
            self._get_problem_tool(),
            self._list_skills_tool(),
            self._get_skill_tool(),
            self._get_procedure_tool(),
            self._create_nudge_tool(),
            self._promote_nudge_tool(),
            self._promote_to_skill_tool(),
            self._update_stats_tool(),
            self._create_issue_tool(),
            self._prune_nudges_tool(),
        ]

    # =========================================================================
    # Problem Tools
    # =========================================================================

    def _list_problems_tool(self) -> Tool:
        """Create list_problems tool."""
        kb_path = self.kb_path

        @tool
        def list_problems(ctx: ToolContext) -> str:
            """List all problems in the knowledge base.

            Returns one line per problem: slug | description
            Use this to find which problem a request relates to.
            """
            problems_dir = kb_path / "problems"
            if not problems_dir.exists():
                return "(no problems in KB yet)"

            lines = []
            for problem_dir in sorted(problems_dir.iterdir()):
                if not problem_dir.is_dir():
                    continue
                problem_md = problem_dir / "problem.md"
                if problem_md.exists():
                    content = problem_md.read_text()
                    frontmatter, body = _parse_frontmatter(content)
                    slug = frontmatter.get("slug", problem_dir.name)
                    # Extract first line of description
                    desc_match = re.search(
                        r"## Description\s*\n\n(.+?)(?:\n\n|$)", body, re.DOTALL
                    )
                    desc = desc_match.group(1).strip() if desc_match else "(no desc)"
                    lines.append(f"{slug} | {desc[:60]}")

            if not lines:
                return "(no problems in KB yet)"

            return "\n".join(lines)

        return list_problems

    def _get_problem_tool(self) -> Tool:
        """Create get_problem tool."""
        kb_path = self.kb_path

        @tool
        def get_problem(ctx: ToolContext, slug: str) -> str:
            """Get a problem and all its nudges and approaches.

            Args:
                slug: Problem slug (e.g., "extract-pdf-tables")

            Returns problem description, then lists all nudges and approaches
            with their IDs, pass/fail counts, and first line of content.
            """
            prob_path = problem_path(kb_path, slug)
            if not prob_path.exists():
                return f"Problem '{slug}' not found"

            problem_md = prob_path / "problem.md"
            if not problem_md.exists():
                return f"Problem '{slug}' has no problem.md"

            result = [f"# Problem: {slug}\n"]
            result.append(problem_md.read_text())
            result.append("\n## Nudges\n")

            nudges_dir = prob_path / "nudges"
            if nudges_dir.exists():
                for nudge_file in sorted(nudges_dir.glob("*.md")):
                    content = nudge_file.read_text()
                    frontmatter, body = _parse_frontmatter(content)
                    nid = frontmatter.get("id", nudge_file.stem)
                    passes = frontmatter.get("passes", 0)
                    fails = frontmatter.get("fails", 0)
                    first_line = body.split("\n")[0] if body else "(empty)"
                    result.append(f"- {nid} (p:{passes}/f:{fails}): {first_line[:50]}")
            else:
                result.append("(no nudges)")

            result.append("\n## Approaches\n")

            approaches_dir = prob_path / "approaches"
            if approaches_dir.exists():
                for approach_file in sorted(approaches_dir.glob("*.md")):
                    content = approach_file.read_text()
                    frontmatter, body = _parse_frontmatter(content)
                    aid = frontmatter.get("id", approach_file.stem)
                    passes = frontmatter.get("passes", 0)
                    fails = frontmatter.get("fails", 0)
                    first_line = body.split("\n")[0] if body else "(empty)"
                    result.append(f"- {aid} (p:{passes}/f:{fails}): {first_line[:50]}")
            else:
                result.append("(no approaches)")

            return "\n".join(result)

        return get_problem

    # =========================================================================
    # Skill Tools
    # =========================================================================

    def _list_skills_tool(self) -> Tool:
        """Create list_skills tool."""
        kb_path = self.kb_path

        @tool
        def list_skills(ctx: ToolContext) -> str:
            """List all validated skills in the knowledge base.

            Returns one line per skill: slug | purpose
            Skills are production-ready procedures that have been validated
            across multiple contexts.
            """
            skills_dir = kb_path / "skills"
            if not skills_dir.exists():
                return "(no skills yet)"

            lines = []
            for skill_dir in sorted(skills_dir.iterdir()):
                if not skill_dir.is_dir():
                    continue
                skill_md = skill_dir / "SKILL.md"
                if skill_md.exists():
                    content = skill_md.read_text()
                    frontmatter, body = _parse_frontmatter(content)
                    slug = frontmatter.get("slug", skill_dir.name)
                    # Extract purpose from body
                    purpose_match = re.search(
                        r"## Purpose\s*\n\n(.+?)(?:\n\n|$)", body, re.DOTALL
                    )
                    purpose = (
                        purpose_match.group(1).strip() if purpose_match else "(no desc)"
                    )
                    lines.append(f"{slug} | {purpose[:60]}")

            if not lines:
                return "(no skills yet)"

            return "\n".join(lines)

        return list_skills

    def _get_skill_tool(self) -> Tool:
        """Create get_skill tool."""
        kb_path = self.kb_path

        @tool
        def get_skill(ctx: ToolContext, slug: str) -> str:
            """Get full content of a skill.

            Args:
                slug: Skill slug (e.g., "extract-pdf-tables")

            Returns the complete skill including Purpose, Procedure,
            Validation, Guardrails, and Failure Handling sections.
            """
            path = skill_path(kb_path, slug)
            if not path.exists():
                return f"Skill '{slug}' not found"
            return path.read_text()

        return get_skill

    # =========================================================================
    # Procedure Tools
    # =========================================================================

    def _get_procedure_tool(self) -> Tool:
        """Create get_procedure tool."""
        kb_path = self.kb_path

        @tool
        def get_procedure(ctx: ToolContext, procedure_id: str) -> str:
            """Get full content of any procedure by ID.

            Args:
                procedure_id: Procedure ID (8-char alphanumeric)

            Works for nudges, approaches, or skills. Returns the full
            markdown content including frontmatter.
            """
            # Search nudges
            for nudge_file in kb_path.glob("problems/*/nudges/*.md"):
                content = nudge_file.read_text()
                frontmatter, _ = _parse_frontmatter(content)
                if frontmatter.get("id") == procedure_id:
                    return content

            # Search approaches
            for approach_file in kb_path.glob("problems/*/approaches/*.md"):
                content = approach_file.read_text()
                frontmatter, _ = _parse_frontmatter(content)
                if frontmatter.get("id") == procedure_id:
                    return content

            # Search skills
            for skill_file in kb_path.glob("skills/*/SKILL.md"):
                content = skill_file.read_text()
                frontmatter, _ = _parse_frontmatter(content)
                if frontmatter.get("id") == procedure_id:
                    return content

            return f"Procedure '{procedure_id}' not found"

        return get_procedure

    def _create_nudge_tool(self) -> Tool:
        """Create create_nudge tool."""
        kb_path = self.kb_path

        @tool(truncate=False)
        def create_nudge(
            ctx: ToolContext,
            problem_slug: str,
            title: str,
            procedure: str,
            nudge_id: str,
            ts: str,
        ) -> str:
            """Create a new nudge (untested idea) for a problem.

            Args:
                problem_slug: Which problem this nudge addresses
                title: Short title for the nudge
                procedure: The step-by-step procedure (markdown)
                nudge_id: ID to use (provided by host)
                ts: Creation timestamp (provided by host)

            If the problem doesn't exist yet, it will be created.
            """
            # Ensure problem exists
            prob_path = problem_path(kb_path, problem_slug)
            if not prob_path.exists():
                prob_path.mkdir(parents=True, exist_ok=True)
                problem_md = prob_path / "problem.md"
                problem_md.write_text(
                    PROBLEM_TEMPLATE.format(
                        slug=problem_slug,
                        created=ts,
                        title=problem_slug.replace("-", " ").title(),
                        description="(Auto-created from nudge)",
                    )
                )

            # Create nudge
            (prob_path / "nudges").mkdir(exist_ok=True)
            nudge_file = nudge_path(kb_path, problem_slug, nudge_id)
            nudge_file.write_text(
                NUDGE_TEMPLATE.format(
                    id=nudge_id,
                    created=ts,
                    title=title,
                    procedure=procedure,
                )
            )

            return f"Created nudge {nudge_id} for problem '{problem_slug}'"

        return create_nudge

    def _promote_nudge_tool(self) -> Tool:
        """Create promote_nudge tool."""
        kb_path = self.kb_path

        @tool
        def promote_nudge(ctx: ToolContext, nudge_id: str) -> str:
            """Promote a nudge to an approach after it succeeded.

            Args:
                nudge_id: ID of the nudge to promote

            Moves the nudge from nudges/ to approaches/ and sets passes=1.
            Call this when report_outcome indicates a nudge passed.
            """
            # Find the nudge
            for nudge_file in kb_path.glob("problems/*/nudges/*.md"):
                content = nudge_file.read_text()
                frontmatter, body = _parse_frontmatter(content)
                if frontmatter.get("id") == nudge_id:
                    # Get problem slug from path
                    problem_slug = nudge_file.parent.parent.name

                    # Create approach
                    (nudge_file.parent.parent / "approaches").mkdir(exist_ok=True)
                    approach_file = approach_path(kb_path, problem_slug, nudge_id)

                    # Update frontmatter and write
                    new_content = _update_frontmatter(
                        content, {"passes": 1, "parent": nudge_id}
                    )
                    approach_file.write_text(new_content)

                    # Delete nudge
                    nudge_file.unlink()

                    return f"Promoted nudge {nudge_id} to approach"

            return f"Nudge '{nudge_id}' not found"

        return promote_nudge

    def _promote_to_skill_tool(self) -> Tool:
        """Create promote_to_skill tool."""
        kb_path = self.kb_path

        @tool(truncate=False)
        def promote_to_skill(
            ctx: ToolContext,
            approach_id: str,
            skill_id: str,
            ts: str,
            purpose: str,
            when_to_use: str,
            validation: str,
            guardrails: str,
            failure_handling: str,
        ) -> str:
            """Promote an approach to a production skill.

            Args:
                approach_id: ID of the approach to promote
                skill_id: ID to use for the skill (provided by host)
                ts: Timestamp (provided by host)
                purpose: What this skill accomplishes (1-2 sentences)
                when_to_use: Conditions that indicate this skill applies
                validation: How to verify the skill worked correctly
                guardrails: Constraints and safety checks
                failure_handling: What to do when the procedure fails

            Call this when an approach has:
            - passes >= 5
            - unique_contexts >= 2
            - fail rate <= 0.25 (last 10 attempts)

            The approach is moved to skills/ and deleted from approaches/.
            """
            # Find the approach
            for approach_file in kb_path.glob("problems/*/approaches/*.md"):
                content = approach_file.read_text()
                frontmatter, body = _parse_frontmatter(content)
                if frontmatter.get("id") == approach_id:
                    # Get problem slug and stats from frontmatter
                    problem_slug = approach_file.parent.parent.name
                    passes = frontmatter.get("passes", 0)
                    fails = frontmatter.get("fails", 0)

                    # Extract title from body (first # heading or first line)
                    title_match = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
                    title = title_match.group(1) if title_match else problem_slug

                    # Extract procedure (everything after title)
                    procedure = body
                    if title_match:
                        procedure = body[title_match.end() :].strip()

                    # Create skill directory and file
                    skill_slug = slugify(title)
                    skill_dir = kb_path / "skills" / skill_slug
                    skill_dir.mkdir(parents=True, exist_ok=True)

                    skill_file = skill_path(kb_path, skill_slug)
                    skill_file.write_text(
                        SKILL_TEMPLATE.format(
                            id=skill_id,
                            slug=skill_slug,
                            promoted_from=approach_id,
                            passes=passes,
                            fails=fails,
                            unique_contexts="(see events.jsonl)",
                            title=title,
                            purpose=purpose,
                            when_to_use=when_to_use,
                            procedure=procedure,
                            validation=validation,
                            guardrails=guardrails,
                            failure_handling=failure_handling,
                        )
                    )

                    # Delete approach
                    approach_file.unlink()

                    return f"Promoted approach {approach_id} to skill '{skill_slug}'"

            return f"Approach '{approach_id}' not found"

        return promote_to_skill

    def _update_stats_tool(self) -> Tool:
        """Create update_procedure_stats tool."""
        kb_path = self.kb_path

        @tool
        def update_procedure_stats(
            ctx: ToolContext,
            procedure_id: str,
            passes_delta: int = 0,
            fails_delta: int = 0,
        ) -> str:
            """Update pass/fail counts for a procedure.

            Args:
                procedure_id: Procedure ID
                passes_delta: Amount to add to passes count
                fails_delta: Amount to add to fails count

            Note: These counts are informational. Authoritative stats
            come from events.jsonl.
            """
            # Find procedure in nudges, approaches, or skills
            for pattern in [
                "problems/*/nudges/*.md",
                "problems/*/approaches/*.md",
                "skills/*/SKILL.md",
            ]:
                for proc_file in kb_path.glob(pattern):
                    content = proc_file.read_text()
                    frontmatter, _ = _parse_frontmatter(content)
                    if frontmatter.get("id") == procedure_id:
                        passes = frontmatter.get("passes", 0) + passes_delta
                        fails = frontmatter.get("fails", 0) + fails_delta
                        new_content = _update_frontmatter(
                            content, {"passes": passes, "fails": fails}
                        )
                        proc_file.write_text(new_content)
                        return f"Updated {procedure_id}: passes={passes}, fails={fails}"

            return f"Procedure '{procedure_id}' not found"

        return update_procedure_stats

    def _create_issue_tool(self) -> Tool:
        """Create create_issue tool."""
        kb_path = self.kb_path

        @tool(truncate=False)
        def create_issue(
            ctx: ToolContext,
            skill_slug: str,
            note: str,
            issue_id: str,
            ts: str,
        ) -> str:
            """Create an issue for a skill that needs refinement.

            Args:
                skill_slug: Which skill the issue is about
                note: Description of what needs fixing
                issue_id: ID to use (provided by host)
                ts: Creation timestamp (provided by host)

            Use this when a skill worked but with caveats, or when
            feedback suggests improvements.
            """
            skill_dir = kb_path / "skills" / skill_slug
            if not skill_dir.exists():
                return f"Skill '{skill_slug}' not found"

            issues_dir = skill_dir / "issues"
            issues_dir.mkdir(exist_ok=True)

            issue_file = issue_path(kb_path, skill_slug, issue_id)
            issue_file.write_text(
                ISSUE_TEMPLATE.format(
                    id=issue_id,
                    issue_type="feedback",
                    created=ts,
                    title=f"Issue {issue_id}",
                    note=note,
                    attempt_id="(pending)",
                )
            )

            return f"Created issue {issue_id} for skill '{skill_slug}'"

        return create_issue

    def _prune_nudges_tool(self) -> Tool:
        """Create prune_nudges tool."""
        kb_path = self.kb_path

        @tool
        def prune_nudges(ctx: ToolContext, problem_slug: str, keep: int = 20) -> str:
            """Remove old nudges, keeping only the most recent.

            Args:
                problem_slug: Which problem's nudges to prune
                keep: Maximum number of nudges to keep (default 20)

            Deletes oldest nudges (by creation date) that have never succeeded.
            Call this after processing report_outcome to keep KB tidy.
            """
            nudges_dir = problem_path(kb_path, problem_slug) / "nudges"
            if not nudges_dir.exists():
                return "No nudges directory"

            # Get all nudges with their creation dates
            nudges: list[tuple[str, Path]] = []
            for nudge_file in nudges_dir.glob("*.md"):
                content = nudge_file.read_text()
                frontmatter, _ = _parse_frontmatter(content)
                created = frontmatter.get("created", "")
                nudges.append((created, nudge_file))

            # Sort by creation date (oldest first)
            nudges.sort(key=lambda x: x[0])

            # Delete oldest nudges beyond the keep limit
            removed = 0
            while len(nudges) > keep:
                _, nudge_file = nudges.pop(0)
                nudge_file.unlink()
                removed += 1

            return f"Pruned {removed} old nudges from '{problem_slug}'"

        return prune_nudges

    # =========================================================================
    # Utility Methods (for SenpaiKit to use directly)
    # =========================================================================

    def list_problems(self) -> list[Problem]:
        """List all problems in KB."""
        problems_dir = self.kb_path / "problems"
        if not problems_dir.exists():
            return []

        problems = []
        for problem_dir in sorted(problems_dir.iterdir()):
            if not problem_dir.is_dir():
                continue
            problem_md = problem_dir / "problem.md"
            if problem_md.exists():
                content = problem_md.read_text()
                frontmatter, body = _parse_frontmatter(content)
                desc_match = re.search(
                    r"## Description\s*\n\n(.+?)(?:\n\n|$)", body, re.DOTALL
                )
                desc = desc_match.group(1).strip() if desc_match else ""
                problems.append(
                    Problem(
                        slug=frontmatter.get("slug", problem_dir.name),
                        description=desc,
                        created=frontmatter.get("created", ""),
                    )
                )
        return problems

    def get_nudge(self, nudge_id: str) -> Nudge | None:
        """Get a nudge by ID."""
        for nudge_file in self.kb_path.glob("problems/*/nudges/*.md"):
            content = nudge_file.read_text()
            frontmatter, body = _parse_frontmatter(content)
            if frontmatter.get("id") == nudge_id:
                return Nudge(
                    id=nudge_id,
                    content=body,
                    created=frontmatter.get("created", ""),
                    passes=frontmatter.get("passes", 0),
                    fails=frontmatter.get("fails", 0),
                    problem_slug=nudge_file.parent.parent.name,
                )
        return None

    def get_approach(self, approach_id: str) -> Approach | None:
        """Get an approach by ID."""
        for approach_file in self.kb_path.glob("problems/*/approaches/*.md"):
            content = approach_file.read_text()
            frontmatter, body = _parse_frontmatter(content)
            if frontmatter.get("id") == approach_id:
                return Approach(
                    id=approach_id,
                    content=body,
                    created=frontmatter.get("created", ""),
                    passes=frontmatter.get("passes", 0),
                    fails=frontmatter.get("fails", 0),
                    problem_slug=approach_file.parent.parent.name,
                    parent=frontmatter.get("parent"),
                )
        return None


__all__ = ["KBKit"]
