from __future__ import annotations

from dataclasses import dataclass, field
import inspect
from typing import Any, TypeVar

from typico.pyfield.pyfield import PyField, get_fields as get_model_fields


T = TypeVar("T")


@dataclass
class PyModel:
    """Container for model metadata and fields."""

    name: str
    """The name of the model class."""

    fields: list[PyField]
    """List of fields in the model."""

    title: str
    """Human-readable title for the model."""

    description: str | None = None
    """Detailed description of the model."""

    frozen: bool = False
    """Whether the model is immutable."""

    metadata: dict[str, Any] = field(default_factory=dict)
    """Additional metadata associated with the model."""

    @classmethod
    def from_class(cls, model_class: type[T]) -> PyModel:
        """Create a Model from a class (Pydantic model or dataclass).

        Args:
            model_class: The model class to analyze

        Returns:
            Model instance containing metadata about the class
        """
        from typico.pyfield import dataclass_adapter, pydantic_adapter

        try:
            from pydantic import BaseModel

            if issubclass(model_class, BaseModel):
                return pydantic_adapter.to_pymodel(model_class)
        except (ImportError, TypeError):
            pass

        # Handle dataclasses
        import dataclasses

        if dataclasses.is_dataclass(model_class):
            # Check if dataclass is frozen
            return dataclass_adapter.to_pymodel(model_class)
        # For other classes, just return basic info

        fields = get_model_fields(model_class)
        name = model_class.__name__
        title = name
        description = inspect.getdoc(model_class)
        return cls(
            name=name,
            fields=fields,
            title=title,
            description=description,
        )

    def get_fields(
        self,
        required: bool | None = None,
        hidden: bool | None = None,
        readonly: bool | None = None,
        deprecated: bool | None = None,
        field_type: str | None = None,
    ) -> list[PyField]:
        """Get fields with optional filtering.

        Args:
            required: If True, only include required. If False, only optional.
            hidden: If True, only include hidden. If False, only visible.
            readonly: If True, only include readonly. If False, only editable.
            deprecated: If True, only include deprecated. If False, only non-deprecated.
            field_type: Filter fields to include only those with specified field_type.

        Returns:
            List of fields matching the filter criteria
        """
        result = self.fields.copy()

        if required is not None:
            result = [f for f in result if f.is_required == required]

        if hidden is not None:
            result = [f for f in result if f.hidden == hidden]

        if readonly is not None:
            result = [f for f in result if f.readonly == readonly]

        if deprecated is not None:
            result = [f for f in result if f.deprecated == deprecated]

        if field_type is not None:
            result = [f for f in result if f.field_type == field_type]

        return result
