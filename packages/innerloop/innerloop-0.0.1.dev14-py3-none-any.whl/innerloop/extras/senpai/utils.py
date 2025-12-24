"""
Path utilities for Senpai knowledge base.

Pure functions for KB path resolution and text processing.
"""

from __future__ import annotations

import re
from pathlib import Path

# =============================================================================
# Path Helpers
# =============================================================================


def problem_path(kb_path: Path, slug: str) -> Path:
    """Get path to a problem directory."""
    return kb_path / "problems" / slug


def nudge_path(kb_path: Path, slug: str, nudge_id: str) -> Path:
    """Get path to a nudge file."""
    return kb_path / "problems" / slug / "nudges" / f"{nudge_id}.md"


def approach_path(kb_path: Path, slug: str, approach_id: str) -> Path:
    """Get path to an approach file."""
    return kb_path / "problems" / slug / "approaches" / f"{approach_id}.md"


def skill_path(kb_path: Path, slug: str) -> Path:
    """Get path to a skill file."""
    return kb_path / "skills" / slug / "SKILL.md"


def issue_path(kb_path: Path, skill_slug: str, issue_id: str) -> Path:
    """Get path to an issue file."""
    return kb_path / "skills" / skill_slug / "issues" / f"{issue_id}.md"


def events_path(kb_path: Path) -> Path:
    """Get path to events.jsonl file."""
    return kb_path / "events.jsonl"


def slugify(text: str) -> str:
    """Convert text to URL-safe slug (lowercase, hyphens).

    Args:
        text: Input text

    Returns:
        Slug like "extract-pdf-tables"
    """
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


# =============================================================================
# Templates
# =============================================================================


INDEX_TEMPLATE = """\
# Senpai Knowledge Base

Procedure repository for agent learning.

## Statistics

- Problems: {problem_count}
- Skills: {skill_count}

## Recent Activity

See events.jsonl for activity log.
"""


PROBLEM_TEMPLATE = """\
---
slug: {slug}
created: {created}
---
# Problem: {title}

## Description

{description}

## Best Approach

(No validated approaches yet)
"""


NUDGE_TEMPLATE = """\
---
id: {id}
parent: null
passes: 0
fails: 0
created: {created}
---
# {title}

{procedure}
"""


APPROACH_TEMPLATE = """\
---
id: {id}
parent: {parent}
passes: {passes}
fails: {fails}
created: {created}
---
# {title}

{procedure}
"""


SKILL_TEMPLATE = """\
---
id: {id}
slug: {slug}
promoted_from: {promoted_from}
passes: {passes}
fails: {fails}
unique_contexts: {unique_contexts}
---
# Skill: {title}

## Purpose

{purpose}

## When to Use

{when_to_use}

## Procedure

{procedure}

## Validation

{validation}

## Guardrails

{guardrails}

## Failure Handling

{failure_handling}
"""


ISSUE_TEMPLATE = """\
---
id: {id}
type: {issue_type}
resolved: false
created: {created}
---
# {title}

## Note

{note}

## Occurrences

- attempt {attempt_id}
"""


AGENTS_MD_TEMPLATE = """\
# Senpai Curator

You curate a knowledge base of procedures that help worker agents solve problems.

## Concepts

- **Problem**: A type of challenge (e.g., "extract tables from PDF")
- **Nudge**: Untested idea (0 successes)
- **Approach**: Worked at least once (1+ successes)
- **Skill**: Validated procedure (5+ successes, multiple contexts, documented)

## Lifecycle

```
Nudge (passes=0) → Approach (passes≥1) → Skill (passes≥5, contexts≥2)
```

## Handling get_help

1. `list_skills()` — Check if any skill matches the problem
2. `list_problems()` → `get_problem(slug)` — Check existing approaches/nudges
3. If no match, `create_nudge()` — Generate 1-3 new ideas

Return JSON: `{"recommendations": [{"id": "...", "procedure": "...", "maturity": "nudge|approach|skill", "artifact_path": "..."}]}`

## Handling report_outcome

1. For passed nudges → `promote_nudge(id)`
2. For all outcomes → `update_procedure_stats(id, passes_delta, fails_delta)`
3. **Check for skill promotion** (see below)
4. If skill needed tweak → `create_issue(slug, note)`
5. Finally → `prune_nudges(slug)` to clean up

## Skill Promotion

After updating stats, check if any approach should become a skill:

**Criteria** (ALL must be true):
- passes >= 5
- Multiple successful contexts (different workers/situations)
- Recent fail rate <= 25%

**Action**: Call `promote_to_skill()` with:
- approach_id: The approach to promote
- skill_id: From available_ids
- ts: From current_ts
- purpose: 1-2 sentence summary of what this accomplishes
- when_to_use: Conditions that indicate this skill applies
- validation: How to verify the procedure worked correctly
- guardrails: Constraints and safety limits
- failure_handling: What to do when things go wrong

## Rules

- **Use only host-provided IDs and timestamps** (passed in context)
- **Never fabricate** — Only reference what exists in KB
- **Search before creating** — Check existing procedures first
- **Promote proactively** — When approaches meet criteria, promote them!
"""


__all__ = [
    # Path helpers
    "problem_path",
    "nudge_path",
    "approach_path",
    "skill_path",
    "issue_path",
    "events_path",
    "slugify",
    # Templates
    "INDEX_TEMPLATE",
    "PROBLEM_TEMPLATE",
    "NUDGE_TEMPLATE",
    "APPROACH_TEMPLATE",
    "SKILL_TEMPLATE",
    "ISSUE_TEMPLATE",
    "AGENTS_MD_TEMPLATE",
]
