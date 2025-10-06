from __future__ import annotations

from importlib.metadata import version

__version__ = version("typico")

from typico.pyfield import (
    Constraints,
    FieldBinding,
    ModelBinding,
    PyField,
    PyModel,
    bind_model,
    get_fields,
    get_model,
)

__all__ = [
    "Constraints",
    "FieldBinding",
    "ModelBinding",
    "PyField",
    "PyModel",
    "__version__",
    "bind_model",
    "get_fields",
    "get_model",
]
