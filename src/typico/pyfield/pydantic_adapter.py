from __future__ import annotations

import inspect
from typing import TYPE_CHECKING

from typico.pyfield.pyfield import get_fields
from typico.pyfield.pymodel import PyModel


if TYPE_CHECKING:
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

    return PyModel(
        name=name,
        fields=fields,
        title=title,
        description=description,
        frozen=frozen,
        metadata=metadata,
    )
