"""
Dict Schema Backend

Backend for plain dict schemas without validation.
Trusts the LLM output and returns it as-is.
"""

from __future__ import annotations

from typing import Any, TypeVar

from .base import SchemaBackend

T = TypeVar("T")


class DictBackend(SchemaBackend):
    """
    Dict-based schema backend without validation.

    Accepts plain dict JSON schemas and returns LLM output as dict.
    No validation is performed - trusts the LLM to produce valid JSON.
    """

    @property
    def name(self) -> str:
        return "dict"

    def is_schema_type(self, type_: Any) -> bool:
        """Check if type is a plain dict with schema-like structure."""
        if not isinstance(type_, dict):
            return False
        # Must have "type" or "properties" to be a JSON schema
        return "type" in type_ or "properties" in type_

    def json_schema(self, type_: dict[str, Any]) -> dict[str, Any]:  # type: ignore[override]
        """Return the schema as-is (already a JSON schema)."""
        return type_

    def validate(self, type_: dict[str, Any], data: dict[str, Any]) -> dict[str, Any]:  # type: ignore[override]
        """Return data as-is (no validation)."""
        return data

    def decode_json(self, type_: dict[str, Any], data: bytes | str) -> dict[str, Any]:  # type: ignore[override]
        """Decode JSON and return as dict (no validation)."""
        import json

        if isinstance(data, bytes):
            data = data.decode("utf-8")
        return json.loads(data)


__all__ = ["DictBackend"]
