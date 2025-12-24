"""
JsonSchema Backend

Backend for dict schemas with jsonschema validation.
Uses the jsonschema library to validate LLM output.
"""

from __future__ import annotations

from typing import Any, TypeVar

from .base import SchemaBackend
from .wrappers import JsonSchema

T = TypeVar("T")


class JsonSchemaBackend(SchemaBackend):
    """
    Dict-based schema backend with jsonschema validation.

    Accepts JsonSchema-wrapped dicts and validates LLM output
    using the jsonschema library. On validation failure, errors
    are propagated for LLM retry.
    """

    @property
    def name(self) -> str:
        return "jsonschema"

    def is_schema_type(self, type_: Any) -> bool:
        """Check if type is a JsonSchema wrapper."""
        return isinstance(type_, JsonSchema)

    def json_schema(self, type_: JsonSchema) -> dict[str, Any]:  # type: ignore[override]
        """Return the wrapped schema."""
        return type_.schema

    def validate(self, type_: JsonSchema, data: dict[str, Any]) -> dict[str, Any]:  # type: ignore[override]
        """Validate data against schema using jsonschema library."""
        try:
            import jsonschema
        except ImportError as e:
            raise ImportError(
                "jsonschema library required for JsonSchema validation. "
                "Install with: pip install innerloop[jsonschema]"
            ) from e

        jsonschema.validate(data, type_.schema)
        return data

    def decode_json(self, type_: JsonSchema, data: bytes | str) -> dict[str, Any]:  # type: ignore[override]
        """Decode JSON and validate against schema."""
        import json

        if isinstance(data, bytes):
            data = data.decode("utf-8")
        parsed = json.loads(data)
        return self.validate(type_, parsed)


__all__ = ["JsonSchemaBackend"]
