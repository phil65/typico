from __future__ import annotations

from typing import Any

import pydantic


def get_json_schema_extra(field_info: pydantic.fields.FieldInfo) -> dict[str, Any]:
    """Extract JSON schema extra information from a field.

    Handles both when json_schema_extra is a dict and when it's a callable.

    Args:
        field_info: The Pydantic field info object

    Returns:
        A dictionary of schema extra information
    """
    if not field_info.json_schema_extra:
        return {}

    if isinstance(field_info.json_schema_extra, dict):
        return field_info.json_schema_extra

    # Handle callable json_schema_extra
    if callable(field_info.json_schema_extra):
        schema_dict: dict[str, Any] = {}
        field_info.json_schema_extra(schema_dict)
        return schema_dict
    return {}


def get_default_value[T](field_info: pydantic.fields.FieldInfo, fallback: T) -> T:
    """Get default value for an integer field.

    Args:
        field_info: Pydantic field info
        fallback: Default value to use if no default is defined

    Returns:
        Default value for the field
    """
    # Check for default value
    if (
        field_info.default is not None
        and field_info.default is not pydantic.fields.PydanticUndefined
    ):
        return field_info.default

    # Check for default factory
    if field_info.default_factory is not None:
        if field_info.default_factory_takes_validated_data:
            return field_info.default_factory({})  # type: ignore
        return field_info.default_factory()  # type: ignore
    return fallback
