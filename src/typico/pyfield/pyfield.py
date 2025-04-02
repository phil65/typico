from __future__ import annotations

import contextlib
import dataclasses
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Annotated, Any, TypeVar, get_args, get_origin

import fieldz

from typico.pyfield.constraints import Constraints


if TYPE_CHECKING:
    from pydantic import BaseModel


T = TypeVar("T", bound="BaseModel")


def extract_from_annotated(type_annotation: Any, name: str) -> tuple[Any, Any | None]:
    """Extract the base type and a named metadata value from an Annotated type.

    Args:
        type_annotation: The type annotation to analyze
        name: The metadata key to extract

    Returns:
        Tuple containing (base_type, metadata_value or None)
    """
    if get_origin(type_annotation) != Annotated:
        return type_annotation, None

    args = get_args(type_annotation)
    base_type = args[0]
    value = None

    # Look for the named value in metadata arguments
    for arg in args[1:]:
        if isinstance(arg, dict) and name in arg:
            value = arg[name]
            break

    return base_type, value


@dataclass
class PyField[T]:
    """Generic representation of a field focused on type semantics."""

    name: str
    """The name of the field in the model."""

    raw_type: Any
    """The Python type annotation of the field."""

    parent_model: type[T] | None = None
    """The parent model class containing this field."""

    field_type: str | None = None
    """The field type, based on Annoated convention."""

    title: str | None = None
    """Display title for the field."""

    description: str | None = None
    """Detailed description of the field."""

    placeholder: str | None = None
    """Placeholder text to show when the field is empty."""

    examples: list[Any] | None = None
    """Example values for the field."""

    hidden: bool = False
    """Whether the field should be hidden from serialization or presentation."""

    readonly: bool = False
    """Whether the field is immutable after initialization."""

    deprecated: bool = False
    """Whether the field is marked as deprecated."""

    is_required: bool = True
    """Whether the field is required for validation."""

    default: Any = None
    """The default value for the field."""

    has_default: bool = False
    """Whether the field has a default value defined."""

    constraints: Constraints = field(default_factory=Constraints)
    """Validation constraints for the field."""

    metadata: dict[str, Any] = field(default_factory=dict)
    """Additional metadata associated with the field."""

    # @property
    # def field_type(self) -> str | None:
    #     """Determine the appropriate field type based on the raw type and metadata."""
    #     # Check explicit field_type in metadata
    #     if "field_type" in self.metadata:
    #         return self.metadata["field_type"]
    #     origin = get_origin(self.raw_type)
    #     if origin is Annotated:
    #         args = get_args(self.raw_type)
    #         for arg in args[1:]:
    #             if isinstance(arg, dict) and "field_type" in arg:
    #                 return arg["field_type"]
    #     return None

    @classmethod
    def from_fieldz(cls, fieldz_field: fieldz.Field, parent_model: type) -> PyField:
        """Convert a fieldz Field to PyField.

        Args:
            fieldz_field: Field instance from fieldz
            parent_model: Optional parent model class

        Returns:
            Equivalent PyField instance
        """
        fieldz_field = fieldz_field.parse_annotated()

        # If this is a Pydantic field, delegate to from_pydantic
        with contextlib.suppress(ImportError):
            from pydantic import BaseModel

            if isinstance(parent_model, type) and issubclass(parent_model, BaseModel):
                return cls.from_pydantic(fieldz_field.name, parent_model)

        # Extract field_type from fieldz metadata or json_schema_extra
        field_type = None
        if fieldz_field.metadata:
            if "field_type" in fieldz_field.metadata:
                field_type = fieldz_field.metadata["field_type"]
            elif "json_schema_extra" in fieldz_field.metadata and isinstance(
                fieldz_field.metadata["json_schema_extra"], dict
            ):
                field_type = fieldz_field.metadata["json_schema_extra"].get("field_type")

        # If we have an annotated type, check it for field_type too
        raw_type = fieldz_field.type
        if fieldz_field.annotated_type:
            base_type, annotated_type = extract_from_annotated(
                fieldz_field.annotated_type,
                "field_type",
            )
            if annotated_type:
                field_type = annotated_type
            raw_type = base_type

        constraints = Constraints.from_fieldz(fieldz_field.constraints)
        examples = fieldz_field.metadata.get("examples")
        placeholder = None
        # 1. Check direct metadata
        if "placeholder" in fieldz_field.metadata:
            placeholder = fieldz_field.metadata["placeholder"]
        # 2. Check json_schema_extra
        elif (
            "json_schema_extra" in fieldz_field.metadata
            and isinstance(fieldz_field.metadata["json_schema_extra"], dict)
            and "placeholder" in fieldz_field.metadata["json_schema_extra"]
        ):
            placeholder = fieldz_field.metadata["json_schema_extra"]["placeholder"]
        # 3. Check Annotated metadata if still not found
        elif fieldz_field.annotated_type:
            _, annotated_placeholder = extract_from_annotated(
                fieldz_field.annotated_type, "placeholder"
            )
            if annotated_placeholder is not None:
                placeholder = annotated_placeholder
        # 4. Fall back to first example if still not found
        elif examples and examples[0] is not None:
            placeholder = str(examples[0])

        # Determine if field has default or is required
        has_default = (
            fieldz_field.default != fieldz.Field.MISSING
            or fieldz_field.default_factory != fieldz.Field.MISSING
        )
        default = None
        if fieldz_field.default != fieldz.Field.MISSING:
            default = fieldz_field.default
        elif fieldz_field.default_factory != fieldz.Field.MISSING:
            with contextlib.suppress(Exception):
                default = fieldz_field.default_factory()
        is_required = not has_default
        hidden = fieldz_field.metadata.get("exclude", False) is True
        readonly = fieldz_field.metadata.get("frozen", False) is True
        deprecated = fieldz_field.metadata.get("deprecated", False) is True
        exclude = {
            "field_type",
            "exclude",
            "frozen",
            "deprecated",
            "examples",
            "placeholder",
        }
        meta = {k: v for k, v in fieldz_field.metadata.items() if k not in exclude}
        return cls(
            name=fieldz_field.name,
            raw_type=raw_type,
            parent_model=parent_model,  # pyright: ignore
            field_type=field_type,
            title=fieldz_field.title or fieldz_field.name.replace("_", " ").capitalize(),
            description=fieldz_field.description,
            placeholder=placeholder,
            examples=examples,
            hidden=hidden,
            readonly=readonly,
            deprecated=deprecated,
            is_required=is_required,
            default=default,
            has_default=has_default,
            constraints=constraints,
            metadata=meta,
        )

    @classmethod
    def from_pydantic(cls, name: str, parent_model: type[BaseModel]) -> PyField:
        """Create a PyField from a field in a Pydantic model.

        Args:
            name: Field name
            parent_model: Pydantic model class containing the field

        Returns:
            PyField representation of the model field
        """
        from typico.pyfield import pydantic_adapter

        return pydantic_adapter.to_pyfield(name, parent_model)

    def is_of_type(self, target_type: type | tuple[type, ...]) -> bool:
        """Check if this field's type matches the target type.

        Handles both direct types and type annotations with origins.

        Args:
            target_type: The type or tuple of types to check against

        Returns:
            True if the field is of the target type, False otherwise
        """
        if self.raw_type is target_type:
            return True
        if isinstance(target_type, tuple):
            if self.raw_type in target_type:
                return True
            origin = getattr(self.raw_type, "__origin__", None)
            return origin in target_type if origin is not None else False
        origin = getattr(self.raw_type, "__origin__", None)
        return origin is target_type if origin is not None else False


def get_fields(model_class: type) -> list[PyField]:
    """Extract fields from a model class and convert to PyFields."""
    from typico.pyfield.dataclass_adapter import get_dataclass_field_docs

    # First check if it's a dataclass and extract field docstrings
    field_docstrings = {}
    if dataclasses.is_dataclass(model_class):
        field_docstrings = get_dataclass_field_docs(model_class)

    result = []
    for f in fieldz.fields(model_class, parse_annotated=True):
        # If this is a dataclass field with no description but has a docstring, use it
        if not f.description and f.name in field_docstrings:
            f.description = field_docstrings[f.name]

        result.append(PyField.from_fieldz(f, parent_model=model_class))
    return result


if __name__ == "__main__":
    import dataclasses

    from typico.pyfield.dataclass_adapter import get_dataclass_field_docs

    @dataclasses.dataclass
    class TestConfig:
        host: str = "localhost"
        """Server hostname."""

        port: int = 8080
        """Port number to connect to."""

        debug: bool = False
        """Enable debug mode."""

    field_docs = get_dataclass_field_docs(TestConfig)
    print("Parsed field docstrings:")
    for name, doc in field_docs.items():
        print(f"  {name}: {doc!r}")
