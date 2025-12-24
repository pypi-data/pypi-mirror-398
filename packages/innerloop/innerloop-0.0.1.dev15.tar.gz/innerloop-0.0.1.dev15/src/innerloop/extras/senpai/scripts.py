"""
Host-controlled scripts for Senpai.

These functions are called by the host (Python), not the LLM,
to ensure consistent ID generation and timestamps.
"""

import secrets
import string
from datetime import datetime, timezone

BASE62 = string.ascii_letters + string.digits  # A-Za-z0-9


def short_id(length: int = 8) -> str:
    """Generate a random alphanumeric ID.

    Args:
        length: Number of characters (default 8)

    Returns:
        Random ID string from Base62 charset [A-Za-z0-9]
    """
    return "".join(secrets.choice(BASE62) for _ in range(length))


def timestamp() -> str:
    """Generate ISO 8601 UTC timestamp.

    Returns:
        Timestamp string like "2024-01-15T10:30:00Z"
    """
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
