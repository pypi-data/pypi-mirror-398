"""
SenpaiKit - Procedure curation LoopKit.

Main class that ties together the internal curator Loop,
KBKit tools, and external API.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from innerloop import Kit, KitContext, Loop, Message, Tool, UserMessage, tool

from .confidence import compute_confidence
from .context_hash import context_key_hash
from .events import EventLog
from .kb_kit import KBKit
from .models import (
    CuratorResponse,
    GetHelpResponse,
    Recommendation,
    ReportOutcomeResponse,
    TriedItem,
)
from .scripts import short_id, timestamp
from .utils import AGENTS_MD_TEMPLATE, INDEX_TEMPLATE


class SenpaiKit(Kit):
    """Procedure curation kit for agent learning.

    Exposes get_help and report_outcome tools to worker agents.
    Maintains an internal LLM Loop for KB curation.

    Args:
        model: Model string for internal curator (e.g., "anthropic/claude-sonnet-4")
        workdir: Directory for knowledge base storage
        api_key: Optional API key for model provider
    """

    def __init__(
        self,
        model: str,
        workdir: Path | str,
        api_key: str | None = None,
    ):
        self.model = model
        self.workdir = Path(workdir).resolve()
        self.api_key = api_key

        # KB path
        self.kb_path = self.workdir / "senpai-kb"

        # Track pending help requests (request_id -> context hash)
        self._pending_requests: dict[str, str] = {}

        # Initialize KB on first use (lazy)
        self._kb_initialized = False

        # Event log (lazy init)
        self._event_log: EventLog | None = None

    def _ensure_kb(self) -> None:
        """Initialize KB structure if needed."""
        if self._kb_initialized:
            return

        self.kb_path.mkdir(parents=True, exist_ok=True)

        # Create events.jsonl if missing
        events_file = self.kb_path / "events.jsonl"
        if not events_file.exists():
            events_file.touch()

        # Create index.md if missing
        index_file = self.kb_path / "index.md"
        if not index_file.exists():
            index_file.write_text(INDEX_TEMPLATE.format(problem_count=0, skill_count=0))

        # Create AGENTS.md for curator (auto-loaded by Loop)
        agents_md = self.kb_path / "AGENTS.md"
        if not agents_md.exists():
            agents_md.write_text(AGENTS_MD_TEMPLATE)

        # Create directories
        (self.kb_path / "problems").mkdir(exist_ok=True)
        (self.kb_path / "skills").mkdir(exist_ok=True)

        # Initialize event log
        self._event_log = EventLog(self.kb_path)

        self._kb_initialized = True

    def _make_curator_loop(self) -> Loop:
        """Create internal curator Loop."""
        self._ensure_kb()

        # KBKit provides semantic tools
        kb_kit = KBKit(self.kb_path)

        return Loop(
            model=self.model,
            api_key=self.api_key,
            kits=[kb_kit],  # Use KBKit for semantic tools
            workdir=self.kb_path,  # Loop auto-loads AGENTS.md from workdir
        )

    def _log_event(self, event: dict[str, Any]) -> None:
        """Append event to events.jsonl."""
        self._ensure_kb()
        if self._event_log:
            self._event_log.append(event)

    def _load_events(self) -> list[dict[str, Any]]:
        """Load all events from events.jsonl."""
        self._ensure_kb()
        if self._event_log:
            return self._event_log.load_all()
        return []

    def _get_procedure_stats(self, procedure_id: str) -> dict[str, Any]:
        """Compute statistics for a procedure from events."""
        self._ensure_kb()
        if self._event_log:
            return self._event_log.get_procedure_stats(procedure_id)
        return {"passes": 0, "fails": 0, "unique_contexts": 0, "statuses": []}

    def get_tools(self) -> list[Tool]:
        """Return tools exposed to workers."""
        return [self._get_help_tool(), self._report_outcome_tool()]

    def _get_help_tool(self) -> Tool:
        """Create the get_help tool."""
        kit = self

        @tool
        def get_help(
            ctx: Any,
            problem: str,
            context: dict[str, Any] | None = None,
        ) -> str:
            """Ask Senpai for procedure recommendations.

            Args:
                problem: Description of the problem to solve
                context: Optional context dict with relevant info
            """
            return json.dumps(kit._get_help(problem, context).model_dump())

        return get_help

    def _report_outcome_tool(self) -> Tool:
        """Create the report_outcome tool."""
        kit = self

        @tool
        def report_outcome(
            ctx: Any,
            request_id: str,
            tried: list[dict[str, Any]],
            custom_solution: str | None = None,
            summary: str = "",
            metrics: dict[str, Any] | None = None,
        ) -> str:
            """Report what happened when trying Senpai's recommendations.

            Args:
                request_id: The request_id from get_help response
                tried: List of {id, status, note?} for each recommendation tried
                custom_solution: Description if you invented your own solution
                summary: Free-form outcome description
                metrics: Optional structured metrics (turns, tool_calls, etc.)
            """
            tried_items = [TriedItem(**t) for t in tried]
            return json.dumps(
                kit._report_outcome(
                    request_id, tried_items, custom_solution, summary, metrics
                ).model_dump()
            )

        return report_outcome

    def _get_help(
        self,
        problem: str,
        context: dict[str, Any] | None = None,
    ) -> GetHelpResponse:
        """Internal get_help implementation."""
        self._ensure_kb()

        # Generate IDs and timestamp
        request_id = short_id()
        ts = timestamp()
        ck_hash = context_key_hash(context)

        # Pre-generate IDs for curator to use
        available_ids = [short_id() for _ in range(5)]

        # Log help_request event
        self._log_event(
            {
                "event_type": "help_request",
                "event_id": short_id(),
                "ts": ts,
                "request_id": request_id,
                "problem": problem,
                "context": context,
                "context_key_hash": ck_hash,
            }
        )

        # Track pending request
        self._pending_requests[request_id] = ck_hash

        # Build prompt for curator
        prompt = f"""get_help request:
- request_id: {request_id}
- problem: {problem}
- context: {json.dumps(context) if context else "null"}
- available_ids: {json.dumps(available_ids)}
- current_ts: {ts}

Search for matching procedures and return 1-3 recommendations.
If nothing matches, create new nudges using the available_ids.

Return JSON with your recommendations."""

        # Run curator
        try:
            loop = self._make_curator_loop()
            response = loop.run(prompt, response_format=CuratorResponse)
            curator_resp = response.output
            # Check if we got a valid response
            if not isinstance(curator_resp, CuratorResponse):
                raise ValueError("Curator did not return valid response")
        except Exception as e:
            # Graceful degradation
            self._log_event(
                {
                    "event_type": "curator_error",
                    "event_id": short_id(),
                    "ts": timestamp(),
                    "request_id": request_id,
                    "error": str(e),
                }
            )
            return GetHelpResponse(request_id=request_id, recommendations=[])

        # Convert curator recommendations to external format
        recommendations: list[Recommendation] = []
        for rec in curator_resp.recommendations[:3]:
            # Get stats for confidence computation
            stats = self._get_procedure_stats(rec.id)
            confidence = compute_confidence(rec.maturity, stats["statuses"])

            recommendations.append(
                Recommendation(
                    id=rec.id,
                    procedure=rec.procedure,
                    confidence=round(confidence, 2),
                )
            )

        # Log help_response event
        self._log_event(
            {
                "event_type": "help_response",
                "event_id": short_id(),
                "ts": timestamp(),
                "request_id": request_id,
                "recommendations": [
                    {
                        "id": r.id,
                        "confidence": r.confidence,
                        "maturity": curator_resp.recommendations[i].maturity
                        if i < len(curator_resp.recommendations)
                        else "nudge",
                        "artifact_path": curator_resp.recommendations[i].artifact_path
                        if i < len(curator_resp.recommendations)
                        else "",
                    }
                    for i, r in enumerate(recommendations)
                ],
            }
        )

        return GetHelpResponse(request_id=request_id, recommendations=recommendations)

    def _report_outcome(
        self,
        request_id: str,
        tried: list[TriedItem],
        custom_solution: str | None = None,
        summary: str = "",
        metrics: dict[str, Any] | None = None,
    ) -> ReportOutcomeResponse:
        """Internal report_outcome implementation."""
        self._ensure_kb()

        ts = timestamp()
        event_id = short_id()

        # Get context hash from pending request
        ck_hash = self._pending_requests.pop(request_id, "ck_unknown")

        # Pre-generate IDs for curator
        available_ids = [short_id() for _ in range(5)]

        # Log attempt event
        self._log_event(
            {
                "event_type": "attempt",
                "event_id": event_id,
                "ts": ts,
                "request_id": request_id,
                "context_key_hash": ck_hash,
                "tried": [t.model_dump() for t in tried],
                "custom_solution": custom_solution,
                "summary": summary,
                "metrics": metrics,
            }
        )

        # Build prompt for curator
        prompt = f"""report_outcome:
- request_id: {request_id}
- tried: {json.dumps([t.model_dump() for t in tried])}
- custom_solution: {json.dumps(custom_solution) if custom_solution else "null"}
- summary: {summary}
- available_ids: {json.dumps(available_ids)}
- current_ts: {ts}

Process this outcome:
1. For passed items: if nudge, promote_nudge(id); update stats
2. For failed items: update_procedure_stats with fails_delta=1
3. If custom_solution provided: create new approach
4. Prune old nudges (keep ~20 per problem)

No response needed, just update the KB."""

        # Run curator
        try:
            loop = self._make_curator_loop()
            loop.run(prompt)
        except Exception as e:
            # Log error but don't fail
            self._log_event(
                {
                    "event_type": "curator_error",
                    "event_id": short_id(),
                    "ts": timestamp(),
                    "request_id": request_id,
                    "error": str(e),
                }
            )

        return ReportOutcomeResponse(recorded=True)

    def on_exit(self, ctx: KitContext) -> list[Message] | None:
        """Remind worker to report outcomes before exiting."""
        if not self._pending_requests:
            return None

        # Allow exit after 2 attempts
        if ctx.exit_attempts >= 2:
            return None

        pending_count = len(self._pending_requests)
        return [
            UserMessage(
                content=f"You received help from Senpai but haven't reported outcomes for {pending_count} request(s). Please call report_outcome before finishing.",
                is_meta=True,
            )
        ]

    def on_tool_error(
        self, tool_name: str, error: str, ctx: KitContext
    ) -> list[Message] | None:
        """Log tool errors for debugging."""
        if tool_name in ("get_help", "report_outcome"):
            self._log_event(
                {
                    "event_type": "tool_error",
                    "event_id": short_id(),
                    "ts": timestamp(),
                    "tool_name": tool_name,
                    "error": error,
                }
            )
        return None


__all__ = ["SenpaiKit"]
