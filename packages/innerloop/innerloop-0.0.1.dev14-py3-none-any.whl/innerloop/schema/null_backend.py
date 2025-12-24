"""
Null Schema Backend

No-op backend when structured outputs are not needed.
Raises clear errors if structured output operations are attempted.
"""

from __future__ import annotations

from typing import Any, TypeVar

from .base import SchemaBackend

T = TypeVar("T")


class NullBackend(SchemaBackend):
    """No-op backend when structured outputs not needed."""

    @property
    def name(self) -> str:
        return "none"

    def is_schema_type(self, type_: Any) -> bool:
        """Null backend doesn't support any schema types."""
        return False

    def json_schema(self, type_: type[T]) -> dict[str, Any]:
        raise NotImplementedError(
            "Structured outputs require a schema backend. "
            "Install with: pip install innerloop[pydantic] or innerloop[msgspec]"
        )

    def validate(self, type_: type[T], data: dict[str, Any]) -> T:
        raise NotImplementedError(
            "Validation requires a schema backend. "
            "Install with: pip install innerloop[pydantic] or innerloop[msgspec]"
        )

    def decode_json(self, type_: type[T], data: bytes | str) -> T:
        raise NotImplementedError(
            "JSON decoding requires a schema backend. "
            "Install with: pip install innerloop[pydantic] or innerloop[msgspec]"
        )


__all__ = ["NullBackend"]
