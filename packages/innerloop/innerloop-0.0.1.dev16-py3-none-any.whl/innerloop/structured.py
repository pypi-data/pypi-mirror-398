"""
Structured Output

Tool-based structured output using pluggable schema backends.
Forces the model to call a 'respond' tool with validated schema.

Supports Pydantic (BaseModel), msgspec (Struct), JsonSchema, and plain dict.
"""

from __future__ import annotations

from typing import Any

from .schema import get_backend_for_type
from .schema.wrappers import JsonSchema
from .types import Tool, ToolContext


def _get_type_name(output_type: Any) -> str:
    """Get a display name for the output type."""
    # Classes have __name__
    if hasattr(output_type, "__name__"):
        return output_type.__name__

    # JsonSchema wrapper - use title from schema or "object"
    if isinstance(output_type, JsonSchema):
        return output_type.schema.get("title", "object")

    # Plain dict schema - use title if present
    if isinstance(output_type, dict):
        return output_type.get("title", "object")

    # Fallback
    return "object"


class ResponseTool(Tool):
    """
    Special tool for structured output.

    The model is forced to call this tool (via tool_choice).
    The tool's input is validated against the schema.

    Supports Pydantic (BaseModel), msgspec (Struct), JsonSchema, and plain dict.
    """

    _output_type: Any

    def __init__(self, output_type: Any) -> None:
        # Get appropriate backend for this type
        backend = get_backend_for_type(output_type)

        # Get schema from the backend
        schema = backend.json_schema(output_type)

        # Inline $defs if present (simpler schema)
        if "$defs" in schema:
            schema = _inline_defs(schema)

        # Get display name for the type
        type_name = _get_type_name(output_type)

        super().__init__(
            name="respond",
            description=f"Submit your final response as {type_name}",
            input_schema=schema,
        )

        object.__setattr__(self, "_output_type", output_type)

    async def execute(
        self, input: dict[str, Any], context: ToolContext | None = None
    ) -> tuple[str, bool]:
        """
        Validate and return the structured output.

        Args:
            input: Tool input from LLM
            context: Unused (ResponseTool doesn't need context)

        Returns:
            ("Success", False) if valid
            (error_message, True) if validation fails
        """
        backend = get_backend_for_type(self._output_type)
        try:
            backend.validate(self._output_type, input)
            return "Success", False
        except Exception as e:
            # Catch validation errors from any backend (Pydantic or msgspec)
            error_msg = f"Validation error: {e}. Fix the errors and call respond again."
            return error_msg, True


def _inline_defs(schema: dict[str, Any]) -> dict[str, Any]:
    """Inline $defs references for simpler schema.

    Recursively resolves all $ref pointers by substituting the
    referenced definitions inline. This produces a schema without
    $defs that LLMs can properly interpret.

    For self-referential schemas (e.g., a Node with child: Node),
    returns the original schema unchanged since removing $defs would
    create invalid references.
    """
    from copy import deepcopy

    if "$defs" not in schema:
        return schema

    defs = schema.get("$defs", {})

    # Track if we encounter any recursive references
    has_recursion = False

    def check_recursion(obj: Any, expanding: frozenset[str] = frozenset()) -> None:
        """Check if schema has recursive references."""
        nonlocal has_recursion
        if has_recursion:
            return
        if isinstance(obj, dict):
            if "$ref" in obj:
                ref_path = obj["$ref"]
                if ref_path.startswith("#/$defs/"):
                    def_name = ref_path.split("/")[-1]
                    if def_name in defs:
                        if def_name in expanding:
                            has_recursion = True
                            return
                        check_recursion(defs[def_name], expanding | {def_name})
            else:
                for v in obj.values():
                    check_recursion(v, expanding)
        elif isinstance(obj, list):
            for item in obj:
                check_recursion(item, expanding)

    check_recursion(schema)

    # If recursive, return original schema with $defs intact
    if has_recursion:
        return schema

    # Otherwise, inline all refs and remove $defs
    result = deepcopy(schema)
    result.pop("$defs", None)

    def resolve_refs(obj: Any, expanding: frozenset[str] = frozenset()) -> Any:
        if isinstance(obj, dict):
            if "$ref" in obj:
                ref_path = obj["$ref"]
                if ref_path.startswith("#/$defs/"):
                    def_name = ref_path.split("/")[-1]
                    if def_name in defs:
                        resolved = deepcopy(defs[def_name])
                        return resolve_refs(resolved, expanding | {def_name})
                return obj
            else:
                return {k: resolve_refs(v, expanding) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [resolve_refs(item, expanding) for item in obj]
        return obj

    return resolve_refs(result)


__all__ = [
    "ResponseTool",
    "_inline_defs",
]
