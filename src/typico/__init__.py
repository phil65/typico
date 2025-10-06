"""Typico: Type helpers and abstractions"""

from __future__ import annotations

from importlib.metadata import version

__version__ = version("typico")
__title__ = "Typico"
__description__ = "Type helpers and abstractions"
__author__ = "Philipp Temminghoff"
__author_email__ = "philipptemminghoff@googlemail.com"
__copyright__ = "Copyright (c) 2025 Philipp Temminghoff"
__license__ = "MIT"
__url__ = "https://github.com/phil65/typico"

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
