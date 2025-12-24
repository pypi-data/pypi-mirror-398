"""
Models for Senpai.

Pydantic models for procedures, problems, and API responses.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# =============================================================================
# Domain Models (Procedures and Problems)
# =============================================================================


class Procedure(BaseModel):
    """Base for all Senpai procedures."""

    id: str = Field(description="8-char alphanumeric identifier")
    content: str = Field(description="Markdown body with procedure steps")
    created: str = Field(description="ISO 8601 timestamp")
    passes: int = Field(default=0, description="Number of successful attempts")
    fails: int = Field(default=0, description="Number of failed attempts")


class Nudge(Procedure):
    """Untested idea. passes=0 by definition."""

    problem_slug: str = Field(description="Slug of the problem this addresses")


class Approach(Procedure):
    """Worked at least once. passes>=1."""

    problem_slug: str = Field(description="Slug of the problem this addresses")
    parent: str | None = Field(
        default=None, description="ID of nudge it was promoted from"
    )


class Problem(BaseModel):
    """Problem definition."""

    slug: str = Field(description="URL-safe identifier")
    description: str = Field(description="Problem description")
    created: str = Field(description="ISO 8601 timestamp")


# =============================================================================
# API Response Models
# =============================================================================


class Recommendation(BaseModel):
    """A procedure recommendation returned by get_help."""

    id: str = Field(description="Procedure identifier")
    procedure: str = Field(description="Step-by-step procedure text")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score 0.0-1.0")


class GetHelpResponse(BaseModel):
    """Response from get_help tool."""

    request_id: str = Field(description="Unique ID for this help request")
    recommendations: list[Recommendation] = Field(
        default_factory=list,
        description="1-3 procedure recommendations",
    )


class TriedItem(BaseModel):
    """An attempt outcome for a recommendation."""

    id: str = Field(description="Recommendation ID that was tried")
    status: Literal["passed", "failed", "partial", "aborted"] = Field(
        description="Outcome status"
    )
    note: str | None = Field(default=None, description="Optional feedback")


class ReportOutcomeResponse(BaseModel):
    """Response from report_outcome tool."""

    recorded: bool = Field(default=True, description="Whether outcome was recorded")


class CuratorRecommendation(BaseModel):
    """Recommendation from the internal curator (includes maturity)."""

    id: str = Field(description="Procedure ID from frontmatter")
    procedure: str = Field(description="Procedure steps text")
    maturity: Literal["nudge", "approach", "skill"] = Field(
        description="Procedure maturity level"
    )
    artifact_path: str = Field(description="Path to procedure file in KB")


class CuratorResponse(BaseModel):
    """Internal response from curator for get_help."""

    recommendations: list[CuratorRecommendation] = Field(
        default_factory=list,
        description="Recommendations from curator",
    )
