"""
Senpai - Skill Expansion Nudging Promotes Agent Improvement

A LoopKit that curates procedures from agent experience.
Evolves untested ideas (nudges) into validated methods (approaches)
and production-ready skills.

Usage:
    from innerloop.extras.senpai import SenpaiKit

    senpai = SenpaiKit(model="anthropic/claude-sonnet-4", workdir="./myproject")

    worker = Loop(
        model="anthropic/claude-sonnet-4",
        kits=[senpai],
        tools=[my_tools],
    )

    response = worker.run("Process the document at /data/invoice.pdf")
"""

from .confidence import compute_confidence
from .context_hash import context_key_hash
from .events import EventLog
from .kb_kit import KBKit
from .kit import SenpaiKit
from .models import (
    Approach,
    CuratorRecommendation,
    CuratorResponse,
    GetHelpResponse,
    Nudge,
    Problem,
    Procedure,
    Recommendation,
    ReportOutcomeResponse,
    TriedItem,
)
from .scripts import short_id, timestamp

__all__ = [
    # Main kit
    "SenpaiKit",
    # Internal kit
    "KBKit",
    # Domain models
    "Procedure",
    "Nudge",
    "Approach",
    "Problem",
    # Response models
    "GetHelpResponse",
    "ReportOutcomeResponse",
    "Recommendation",
    "TriedItem",
    "CuratorResponse",
    "CuratorRecommendation",
    # Utilities
    "short_id",
    "timestamp",
    "compute_confidence",
    "context_key_hash",
    "EventLog",
]
