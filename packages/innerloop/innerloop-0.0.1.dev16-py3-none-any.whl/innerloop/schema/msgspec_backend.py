"""
msgspec Schema Backend

High-performance schema backend using msgspec Structs.

Note on coercion:
- msgspec by default performs limited coercion (e.g., int -> float)
- Use strict=True in convert/decode to disable coercion if needed
- Pydantic performs more aggressive coercion by default
"""

from __future__ import annotations

from typing import Any, TypeVar

from .base import SchemaBackend

T = TypeVar("T")


class MsgspecBackend(SchemaBackend):
    """msgspec-based schema backend (high performance)."""

    def __init__(self, strict: bool = False):
        """
        Initialize msgspec backend.

        Args:
            strict: If True, disable type coercion (e.g., int -> float).
                   Default False for Pydantic-like behavior.
        """
        self._strict = strict

    @property
    def name(self) -> str:
        return "msgspec"

    def is_schema_type(self, type_: Any) -> bool:
        """Check if type is a msgspec Struct subclass."""
        try:
            from msgspec import Struct

            return isinstance(type_, type) and issubclass(type_, Struct)
        except ImportError:
            return False

    def _check_type(self, type_: type[Any]) -> None:
        """Raise TypeError if type is not a valid msgspec Struct."""
        if not self.is_schema_type(type_):
            raise TypeError(
                f"msgspec backend requires Struct subclass, got {type_.__name__}"
            )

    def json_schema(self, type_: type[T]) -> dict[str, Any]:
        """Generate JSON schema from msgspec Struct."""
        from msgspec.json import schema

        self._check_type(type_)
        return schema(type_)

    def validate(self, type_: type[T], data: dict[str, Any]) -> T:
        """Validate data and return msgspec Struct instance."""
        from msgspec import convert

        self._check_type(type_)
        return convert(data, type_, strict=self._strict)

    def decode_json(self, type_: type[T], data: bytes | str) -> T:
        """Decode JSON and return msgspec Struct instance."""
        from msgspec.json import decode

        self._check_type(type_)
        if isinstance(data, str):
            data = data.encode("utf-8")
        # Note: msgspec.json.decode doesn't have strict param,
        # it uses the Struct's field types directly
        return decode(data, type=type_)


# Alias for consistent error handling across backends
try:
    from msgspec import ValidationError as MsgspecValidationError
except ImportError:
    # Placeholder if msgspec not installed (runtime fallback)
    class MsgspecValidationError(Exception):  # type: ignore[no-redef]
        pass


__all__ = ["MsgspecBackend", "MsgspecValidationError"]
