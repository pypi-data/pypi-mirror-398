"""
Event logging for Senpai.

EventLog class for appending to and reading from events.jsonl.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class EventLog:
    """Event log for Senpai knowledge base.

    Appends events to events.jsonl and provides methods for querying.
    Events are the source of truth for procedure statistics.
    """

    def __init__(self, kb_path: Path):
        """Initialize event log.

        Args:
            kb_path: Path to knowledge base directory
        """
        self.kb_path = kb_path.resolve()
        self._events_file = self.kb_path / "events.jsonl"

    def _ensure_file(self) -> None:
        """Create events file if it doesn't exist."""
        if not self._events_file.exists():
            self._events_file.parent.mkdir(parents=True, exist_ok=True)
            self._events_file.touch()

    def append(self, event: dict[str, Any]) -> None:
        """Append an event to the log.

        Args:
            event: Event dict with at least event_type field
        """
        self._ensure_file()
        with self._events_file.open("a") as f:
            f.write(json.dumps(event) + "\n")

    def load_all(self) -> list[dict[str, Any]]:
        """Load all events from the log.

        Returns:
            List of event dicts
        """
        self._ensure_file()
        events = []
        with self._events_file.open() as f:
            for line in f:
                line = line.strip()
                if line:
                    events.append(json.loads(line))
        return events

    def get_procedure_stats(self, procedure_id: str) -> dict[str, Any]:
        """Compute statistics for a procedure from events.

        Args:
            procedure_id: Procedure ID to compute stats for

        Returns:
            Dict with passes, fails, unique_contexts, and statuses
        """
        events = self.load_all()
        attempts = [e for e in events if e.get("event_type") == "attempt"]

        passes = 0
        fails = 0
        context_hashes: set[str] = set()
        statuses: list[str] = []

        for attempt in attempts:
            for tried in attempt.get("tried", []):
                if tried.get("id") == procedure_id:
                    status = tried.get("status", "")
                    statuses.append(status)
                    if status == "passed":
                        passes += 1
                    elif status == "failed":
                        fails += 1
                    context_hashes.add(attempt.get("context_key_hash", ""))

        return {
            "passes": passes,
            "fails": fails,
            "unique_contexts": len(context_hashes),
            "statuses": statuses,
        }


__all__ = ["EventLog"]
