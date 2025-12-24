"""
Schema Backend Protocol

Abstract interface for schema backends (Pydantic, msgspec, etc.).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, TypeVar

T = TypeVar("T")


class SchemaBackend(ABC):
    """Protocol for schema backends."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Backend name for logging/debugging."""
        ...

    @abstractmethod
    def json_schema(self, type_: type[T]) -> dict[str, Any]:
        """Generate JSON schema for a type."""
        ...

    @abstractmethod
    def validate(self, type_: type[T], data: dict[str, Any]) -> T:
        """Validate data against type, return instance."""
        ...

    @abstractmethod
    def decode_json(self, type_: type[T], data: bytes | str) -> T:
        """Decode JSON and validate in one step."""
        ...

    @abstractmethod
    def is_schema_type(self, type_: Any) -> bool:
        """Check if a type is a valid schema type for this backend."""
        ...


__all__ = ["SchemaBackend"]
