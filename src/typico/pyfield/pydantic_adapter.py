from __future__ import annotations

import contextlib
import inspect
from typing import TYPE_CHECKING, Annotated, Any, get_args, get_origin

from pydantic import ValidationError

from typico.pyfield.bindings import ModelBinding, ModelValidationResult
from typico.pyfield.constraints import Constraints
from typico.pyfield.pyfield import MISSING_VALUE, PyField, get_fields
from typico.pyfield.pymodel import PyModel


if TYPE_CHECKING:
    from collections.abc import Sequence

    from pydantic import BaseModel


def to_pymodel(model_class: type[BaseModel]):
    fields = get_fields(model_class)
    name = model_class.__name__
    title = name
    description = inspect.getdoc(model_class)
    metadata = {}
    config = model_class.model_config
    schema = model_class.model_json_schema()  # type: ignore
    title = schema.get("title", title)
    # Get description from schema if available
    if not description and "description" in schema:
        description = schema["description"]

    frozen = config.get("frozen", False)

    # Extract any extra schema properties to metadata
    for k, v in schema.items():
        if k not in {
            "title",
            "description",
            "type",
            "properties",
            "required",
        }:
            metadata[k] = v  # noqa: PERF403

    def validator_wrapper(binding: ModelBinding) -> ModelValidationResult:
        try:
            data = {b.field.name: b.value for b in binding.fields}
            instance = model_class.model_validate(data)
            return ModelValidationResult(is_valid=True, validated_instance=instance)
        except ValidationError as e:
            field_errors: dict[str, Any] = {}
            global_errors = []
            for err in e.errors():
                loc: Sequence[Any] = err.get("loc", [])
                msg = err.get("msg", "")
                # If location is empty or points to "__root__", it's a global error
                if not loc or loc[0] == "__root__":
                    global_errors.append(msg)
                else:
                    # Otherwise it's a field error
                    field_name = ".".join(str(x) for x in loc)
                    field_errors.setdefault(field_name, []).append(msg)
            return ModelValidationResult(
                is_valid=False,
                field_errors=field_errors,
                global_errors=global_errors,
            )

    return PyModel(
        name=name,
        fields=fields,
        title=title,
        description=description,
        frozen=frozen,
        metadata=metadata,
        validator=validator_wrapper,
    )


def to_pyfield(name: str, parent_model: type[BaseModel]) -> PyField:
    field_info = parent_model.model_fields[name]
    raw_type = field_info.annotation
    field_type = None

    for meta in field_info.metadata:
        if isinstance(meta, dict) and "field_type" in meta:
            field_type = meta["field_type"]
            break

    # If not found and it's still an Annotated type, try direct extraction
    if field_type is None and get_origin(raw_type) is Annotated:
        args = get_args(raw_type)
        base_type = args[0]

        for arg in args[1:]:
            if isinstance(arg, dict) and "field_type" in arg:
                field_type = arg["field_type"]
                break

        raw_type = base_type

    # Check json_schema_extra for field_type if not found
    if (
        field_type is None
        and field_info.json_schema_extra
        and isinstance(field_info.json_schema_extra, dict)
    ):
        field_type = field_info.json_schema_extra.get("field_type")
        assert isinstance(field_type, str) or field_type is None

    # Get constraints from JSON schema
    schema = parent_model.model_json_schema()
    field_schema = schema.get("properties", {}).get(name, {})
    constraints = Constraints.from_jsonschema(field_schema)
    is_required = name in schema.get("required", [])
    from pydantic.fields import PydanticUndefined

    default_value = (
        MISSING_VALUE if field_info.default is PydanticUndefined else field_info.default
    )
    metadata = {}
    if field_info.json_schema_extra:
        if isinstance(field_info.json_schema_extra, dict):
            # Direct dictionary case
            metadata = field_info.json_schema_extra.copy()
        elif callable(field_info.json_schema_extra):
            with contextlib.suppress(Exception):
                field_info.json_schema_extra(metadata)
    metadata = {k: v for k, v in metadata.items() if k != "field_type"}

    return PyField(
        name=name,
        raw_type=raw_type,
        parent_model=parent_model,  # type: ignore
        field_type=field_type,
        title=field_info.title or name.replace("_", " ").capitalize(),
        description=field_info.description,
        placeholder=str(field_info.examples[0])
        if field_info.examples and field_info.examples[0] is not None
        else None,
        examples=field_info.examples,
        hidden=field_info.exclude or False,
        readonly=getattr(field_info, "frozen", False),
        deprecated=field_info.deprecated is not None,
        is_required=is_required,
        default=default_value,
        constraints=constraints,
        metadata=metadata,
    )
