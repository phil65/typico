"""PyField abstraction for model fields."""

from typico.pyfield.pyfield import PyField, get_fields
from typico.pyfield.pymodel import PyModel
from typico.pyfield.constraints import Constraints
from typico.pyfield.bindings import FieldBinding, ModelBinding, bind_model

get_model = PyModel.from_class

__all__ = [
    "Constraints",
    "FieldBinding",
    "ModelBinding",
    "PyField",
    "PyModel",
    "bind_model",
    "get_fields",
    "get_model",
]
