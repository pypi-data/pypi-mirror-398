"""
Context key hashing for Senpai.

Used to compute unique_contexts for promotion criteria.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any


def context_key_hash(context: dict[str, Any] | None) -> str:
    """Compute hash of context for uniqueness tracking.

    If context contains a 'context_key' field, only that is hashed.
    Otherwise the entire context is hashed.

    Args:
        context: Context dict or None

    Returns:
        Hash string like "ck_3f2a9c1e" (8 hex chars)
    """
    if context is None:
        return "ck_00000000"

    # Use context_key if present, otherwise full context
    key = context.get("context_key", context)

    # Canonicalize: sorted keys, no whitespace
    canonical = json.dumps(key, sort_keys=True, separators=(",", ":"))

    # SHA-256 hash, take first 8 hex chars
    h = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    return f"ck_{h[:8]}"
