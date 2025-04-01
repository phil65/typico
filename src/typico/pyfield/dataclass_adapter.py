from __future__ import annotations

import ast
import inspect
from textwrap import dedent
from typing import Any, cast


def get_dataclass_field_docs(cls: type) -> dict[str, str]:
    """Extract field docstrings from a dataclass by parsing its source code."""
    try:
        source = dedent(inspect.getsource(cls))
        tree = ast.parse(source)
        docstrings = {}
        for cls_node in ast.iter_child_nodes(tree):
            if not isinstance(cls_node, ast.ClassDef):
                continue
            field_name = None
            for node in cls_node.body:
                # If this is a field assignment, remember the field name
                if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                    field_name = node.target.id
                # If we have a field name and the next node is a docstring, capture it
                elif (
                    field_name
                    and isinstance(node, ast.Expr)
                    and isinstance(node.value, ast.Constant)
                    and isinstance(node.value.value, str)
                ):
                    docstrings[field_name] = node.value.value
                    field_name = None  # Reset for next field
                else:
                    field_name = None  # Reset if it's not followed by a docstring
    except (OSError, TypeError, SyntaxError):
        return {}
    else:
        return docstrings


def to_pymodel(model_class: type):
    from typico.pyfield.pyfield import get_fields
    from typico.pyfield.pymodel import PyModel

    fields = get_fields(model_class)
    name = model_class.__name__
    title = name
    description = inspect.getdoc(model_class)
    metadata: dict[str, Any] = {}
    try:
        from pydantic import BaseModel

        if issubclass(model_class, BaseModel):
            pass
    except (ImportError, TypeError):
        pass

    # Handle dataclasses
    import dataclasses

    frozen = False
    try:
        dc_params = cast(dict[str, Any], getattr(model_class, "__dataclass_params__", {}))
        if isinstance(dc_params, dataclasses.Field):
            frozen = getattr(dc_params, "frozen", False)
        else:
            frozen = dc_params.get("frozen", False)
    except (AttributeError, TypeError):
        pass

    # Return dataclass model
    return PyModel(
        name=name,
        fields=fields,
        title=title,
        description=description,
        frozen=frozen,
        metadata=metadata,
    )
