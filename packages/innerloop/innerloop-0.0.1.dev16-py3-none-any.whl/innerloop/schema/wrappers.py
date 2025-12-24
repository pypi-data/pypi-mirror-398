"""
Schema Wrappers

Wrapper types for dict-based JSON schemas.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class JsonSchema:
    """
    Dict schema with jsonschema validation.

    Wraps a JSON Schema dict to enable validation via the jsonschema library.
    On validation failure, errors are sent back to the LLM for retry.

    Example:
        from innerloop import Loop, JsonSchema

        city_schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "population": {"type": "integer"}
            },
            "required": ["name", "population"]
        }

        loop = Loop(model="anthropic/claude-sonnet-4")
        response = loop.run("Data about Tokyo", response_format=JsonSchema(city_schema))
        print(response.output)  # {"name": "Tokyo", "population": 13960000}
    """

    schema: dict[str, Any]

    def __post_init__(self) -> None:
        """Validate that schema is a dict."""
        if not isinstance(self.schema, dict):
            raise TypeError(f"JsonSchema requires a dict, got {type(self.schema)}")


__all__ = ["JsonSchema"]
