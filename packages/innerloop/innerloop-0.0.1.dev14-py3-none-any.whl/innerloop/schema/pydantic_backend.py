"""
Pydantic Schema Backend

Full-featured schema backend using Pydantic models.
"""

from __future__ import annotations

from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from .base import SchemaBackend

T = TypeVar("T")


class PydanticBackend(SchemaBackend):
    """Pydantic-based schema backend."""

    @property
    def name(self) -> str:
        return "pydantic"

    def is_schema_type(self, type_: Any) -> bool:
        """Check if type is a Pydantic BaseModel subclass."""
        return isinstance(type_, type) and issubclass(type_, BaseModel)

    def _check_type(self, type_: type[Any]) -> None:
        """Raise TypeError if type is not a valid Pydantic model."""
        if not self.is_schema_type(type_):
            raise TypeError(
                f"Pydantic backend requires BaseModel subclass, got {type_.__name__}"
            )

    def json_schema(self, type_: type[T]) -> dict[str, Any]:
        """Generate JSON schema from Pydantic model."""
        self._check_type(type_)
        return type_.model_json_schema()

    def validate(self, type_: type[T], data: dict[str, Any]) -> T:
        """Validate data and return Pydantic model instance."""
        self._check_type(type_)
        return type_.model_validate(data)

    def decode_json(self, type_: type[T], data: bytes | str) -> T:
        """Decode JSON string and validate as Pydantic model."""
        self._check_type(type_)
        if isinstance(data, bytes):
            data = data.decode("utf-8")
        return type_.model_validate_json(data)


# Re-export ValidationError for consistent error handling
PydanticValidationError = ValidationError

__all__ = ["PydanticBackend", "PydanticValidationError"]
