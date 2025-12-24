"""
Schema Backend Abstraction

Provides pluggable schema backends for structured outputs (response_format).
Automatically selects the appropriate backend based on the type passed.

Pydantic is included in core deps, alternatives are optional extras:
    pip install innerloop[msgspec]    # msgspec (performance)
    pip install innerloop[jsonschema] # JsonSchema validation

Plain dict schemas work without any extras (no validation).

Usage:
    # With Pydantic (included in core deps)
    from pydantic import BaseModel

    class MyModel(BaseModel):
        name: str

    schema = json_schema(MyModel)
    instance = validate(MyModel, {"name": "test"})

    # With msgspec (install: pip install innerloop[msgspec])
    from msgspec import Struct

    class MyStruct(Struct):
        name: str

    schema = json_schema(MyStruct)
    instance = validate(MyStruct, {"name": "test"})

    # With JsonSchema wrapper (install: pip install innerloop[jsonschema])
    from innerloop import JsonSchema

    my_schema = JsonSchema({"type": "object", "properties": {"name": {"type": "string"}}})
    result = validate(my_schema, {"name": "test"})  # Returns dict

    # With plain dict (no extras needed, no validation)
    my_schema = {"type": "object", "properties": {"name": {"type": "string"}}}
    result = validate(my_schema, {"name": "test"})  # Returns dict, no validation
"""

from __future__ import annotations

from typing import Any, TypeVar

from .base import SchemaBackend
from .wrappers import JsonSchema

T = TypeVar("T")

# Cached backend instances
_pydantic_backend: SchemaBackend | None = None
_msgspec_backend: SchemaBackend | None = None
_jsonschema_backend: SchemaBackend | None = None
_dict_backend: SchemaBackend | None = None
_null_backend: SchemaBackend | None = None


def _get_pydantic_backend() -> SchemaBackend | None:
    """Get or create the Pydantic backend."""
    global _pydantic_backend
    if _pydantic_backend is not None:
        return _pydantic_backend
    try:
        from .pydantic_backend import PydanticBackend

        _pydantic_backend = PydanticBackend()
        return _pydantic_backend
    except ImportError:
        return None


def _get_msgspec_backend() -> SchemaBackend | None:
    """Get or create the msgspec backend."""
    global _msgspec_backend
    if _msgspec_backend is not None:
        return _msgspec_backend
    try:
        from .msgspec_backend import MsgspecBackend

        _msgspec_backend = MsgspecBackend()
        return _msgspec_backend
    except ImportError:
        return None


def _get_jsonschema_backend() -> SchemaBackend:
    """Get or create the jsonschema backend."""
    global _jsonschema_backend
    if _jsonschema_backend is not None:
        return _jsonschema_backend
    from .jsonschema_backend import JsonSchemaBackend

    _jsonschema_backend = JsonSchemaBackend()
    return _jsonschema_backend


def _get_dict_backend() -> SchemaBackend:
    """Get or create the dict backend."""
    global _dict_backend
    if _dict_backend is not None:
        return _dict_backend
    from .dict_backend import DictBackend

    _dict_backend = DictBackend()
    return _dict_backend


def _get_null_backend() -> SchemaBackend:
    """Get or create the null backend."""
    global _null_backend
    if _null_backend is not None:
        return _null_backend
    from .null_backend import NullBackend

    _null_backend = NullBackend()
    return _null_backend


def get_backend_for_type(type_: Any) -> SchemaBackend:
    """
    Get the appropriate backend for a given type.

    Automatically detects the type and returns the corresponding backend:
    - Pydantic BaseModel → PydanticBackend
    - msgspec Struct → MsgspecBackend
    - JsonSchema wrapper → JsonSchemaBackend (with validation)
    - Plain dict → DictBackend (no validation)

    Args:
        type_: The schema type

    Returns:
        The appropriate SchemaBackend

    Raises:
        TypeError: If the type is not supported by any available backend
    """
    # Check for JsonSchema wrapper first (validated dict)
    jsonschema_backend = _get_jsonschema_backend()
    if jsonschema_backend.is_schema_type(type_):
        return jsonschema_backend

    # Check for plain dict (no validation)
    dict_backend = _get_dict_backend()
    if dict_backend.is_schema_type(type_):
        return dict_backend

    # Try Pydantic (if installed)
    pydantic = _get_pydantic_backend()
    if pydantic is not None and pydantic.is_schema_type(type_):
        return pydantic

    # Try msgspec
    msgspec = _get_msgspec_backend()
    if msgspec is not None and msgspec.is_schema_type(type_):
        return msgspec

    # No backend supports this type
    type_name = getattr(type_, "__name__", str(type_))
    raise TypeError(
        f"Unsupported schema type: {type_name}. "
        f"Use pydantic.BaseModel, msgspec.Struct, JsonSchema(dict), or plain dict."
    )


def get_backend(name: str | None = None) -> SchemaBackend:
    """
    Get a schema backend by name.

    Args:
        name: Backend name ("pydantic", "msgspec", "jsonschema", "dict", or None for default)

    Returns:
        The requested SchemaBackend

    Raises:
        ValueError: If the named backend is not available
    """
    if name == "pydantic":
        backend = _get_pydantic_backend()
        if backend is not None:
            return backend
        raise ValueError(
            "Pydantic backend not available. Install with: pip install innerloop[pydantic]"
        )

    if name == "msgspec":
        backend = _get_msgspec_backend()
        if backend is not None:
            return backend
        raise ValueError(
            "msgspec backend not available. Install with: pip install innerloop[msgspec]"
        )

    if name == "jsonschema":
        return _get_jsonschema_backend()

    if name == "dict":
        return _get_dict_backend()

    if name == "none":
        return _get_null_backend()

    if name is None:
        # Default: try pydantic, then msgspec, then dict
        pydantic = _get_pydantic_backend()
        if pydantic is not None:
            return pydantic
        msgspec = _get_msgspec_backend()
        if msgspec is not None:
            return msgspec
        # Fall back to dict backend (always available, no validation)
        return _get_dict_backend()

    raise ValueError(f"Unknown backend: {name}")


# Convenience functions that auto-detect backend from type


def json_schema(type_: Any) -> dict[str, Any]:
    """Generate JSON schema for a type."""
    return get_backend_for_type(type_).json_schema(type_)


def validate(type_: Any, data: dict[str, Any]) -> Any:
    """Validate data against type, return instance."""
    return get_backend_for_type(type_).validate(type_, data)


def decode_json(type_: Any, data: bytes | str) -> Any:
    """Decode JSON and validate in one step."""
    return get_backend_for_type(type_).decode_json(type_, data)


def is_schema_type(type_: Any) -> bool:
    """Check if a type is a valid schema type for any available backend."""
    # JsonSchema wrapper
    jsonschema_backend = _get_jsonschema_backend()
    if jsonschema_backend.is_schema_type(type_):
        return True

    # Plain dict
    dict_backend = _get_dict_backend()
    if dict_backend.is_schema_type(type_):
        return True

    # Pydantic
    pydantic = _get_pydantic_backend()
    if pydantic is not None and pydantic.is_schema_type(type_):
        return True

    # msgspec
    msgspec = _get_msgspec_backend()
    if msgspec is not None and msgspec.is_schema_type(type_):
        return True

    return False


__all__ = [
    "SchemaBackend",
    "JsonSchema",
    "get_backend",
    "get_backend_for_type",
    "json_schema",
    "validate",
    "decode_json",
    "is_schema_type",
]
