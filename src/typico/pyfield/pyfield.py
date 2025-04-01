from __future__ import annotations

import ast
import contextlib
import dataclasses
from dataclasses import dataclass, field
import inspect
from textwrap import dedent
from typing import TYPE_CHECKING, Annotated, Any, TypeVar, get_args, get_origin

import fieldz


if TYPE_CHECKING:
    from pydantic import BaseModel


T = TypeVar("T", bound="BaseModel")


@dataclass
class Constraints:
    """Encapsulation of field validation constraints."""

    min_value: float | None = None
    """Minimum allowed value for numeric fields."""

    max_value: float | None = None
    """Maximum allowed value for numeric fields."""

    exclusive_min: bool = False
    """If True, the minimum value is exclusive (value must be greater than min_value)."""

    exclusive_max: bool = False
    """If True, the maximum value is exclusive (value must be less than max_value)."""

    multiple_of: float | None = None
    """If set, the value must be a multiple of this number."""

    min_length: int | None = None
    """Minimum length for strings or collections."""

    max_length: int | None = None
    """Maximum length for strings or collections."""

    pattern: str | None = None
    """Regular expression pattern that strings must match."""

    min_items: int | None = None
    """Minimum number of items for array/list types."""

    max_items: int | None = None
    """Maximum number of items for array/list types."""

    allowed_values: list[Any] | None = None
    """List of allowed values (for enums, literals, or constrained types)."""

    @classmethod
    def from_fieldz(cls, fieldz_constraints: fieldz.Constraints | None) -> Constraints:
        """Convert fieldz constraints to Constraints.

        Args:
            fieldz_constraints: Constraints from fieldz

        Returns:
            Equivalent Constraints
        """
        if not fieldz_constraints:
            return cls()

        constraints = cls()

        # Map direct equivalents
        if fieldz_constraints.gt is not None:
            constraints.min_value = fieldz_constraints.gt
            constraints.exclusive_min = True
        elif fieldz_constraints.ge is not None:
            constraints.min_value = fieldz_constraints.ge

        if fieldz_constraints.lt is not None:
            constraints.max_value = fieldz_constraints.lt
            constraints.exclusive_max = True
        elif fieldz_constraints.le is not None:
            constraints.max_value = fieldz_constraints.le

        constraints.multiple_of = fieldz_constraints.multiple_of
        constraints.min_length = fieldz_constraints.min_length
        constraints.max_length = fieldz_constraints.max_length
        constraints.pattern = fieldz_constraints.pattern

        return constraints


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

    @classmethod
    def from_fieldz(
        cls, fieldz_field: fieldz.Field, parent_model: type | None = None
    ) -> PyField:
        """Convert a fieldz Field to PyField.

        Args:
            fieldz_field: Field instance from fieldz
            parent_model: Optional parent model class

        Returns:
            Equivalent PyField instance
        """
        fieldz_field = fieldz_field.parse_annotated()

        # If this is a Pydantic field, delegate to from_pydantic
        if parent_model is not None:
            with contextlib.suppress(ImportError):
                from pydantic import BaseModel

                if (
                    isinstance(parent_model, type)
                    and issubclass(parent_model, BaseModel)
                    and hasattr(parent_model, "model_fields")
                ):
                    # For Pydantic models, use specialized method
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
            base_type, annotated_field_type = extract_from_annotated(
                fieldz_field.annotated_type,
                "field_type",
            )
            if annotated_field_type:
                field_type = annotated_field_type
            # Keep the base type, not the Annotated wrapper
            raw_type = base_type

        # Convert constraints
        constraints = Constraints.from_fieldz(fieldz_field.constraints)
        # Extract examples
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

        # Create the PyField
        meta = {
            k: v
            for k, v in fieldz_field.metadata.items()
            if k
            not in {
                "field_type",
                "exclude",
                "frozen",
                "deprecated",
                "examples",
                "placeholder",
            }
        }
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
        # Get field info directly from the model
        field_info = parent_model.model_fields.get(name)
        if field_info is None:
            msg = f"Field {name!r} not found in {parent_model.__name__}"
            raise ValueError(msg)

        # Extract raw type and handle Annotated types
        raw_type = field_info.annotation
        field_type = None

        # Check metadata from Annotated type
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
        constraints = Constraints()

        # Extract constraints
        if "minimum" in field_schema:
            constraints.min_value = field_schema["minimum"]
        if "maximum" in field_schema:
            constraints.max_value = field_schema["maximum"]
        if "exclusiveMinimum" in field_schema:
            constraints.min_value = field_schema["exclusiveMinimum"]
            constraints.exclusive_min = True
        if "exclusiveMaximum" in field_schema:
            constraints.max_value = field_schema["exclusiveMaximum"]
            constraints.exclusive_max = True
        if "minLength" in field_schema:
            constraints.min_length = field_schema["minLength"]
        if "maxLength" in field_schema:
            constraints.max_length = field_schema["maxLength"]
        if "pattern" in field_schema:
            constraints.pattern = field_schema["pattern"]

        # Determine required status and default value
        is_required = name in schema.get("required", [])
        from pydantic.fields import PydanticUndefined

        has_default = field_info.default is not PydanticUndefined
        default_value = (
            None if field_info.default is PydanticUndefined else field_info.default
        )
        metadata = {}
        if field_info.json_schema_extra:
            if isinstance(field_info.json_schema_extra, dict):
                # Direct dictionary case
                metadata = {
                    k: v
                    for k, v in field_info.json_schema_extra.items()
                    if k != "field_type"
                }
            elif callable(field_info.json_schema_extra):
                # Callable case - create a temporary schema dict to extract metadata
                tmp_schema: dict[str, Any] = {}
                try:
                    field_info.json_schema_extra(tmp_schema)
                    # After the callable modifies tmp_schema, extract any metadata
                    metadata = {k: v for k, v in tmp_schema.items() if k != "field_type"}
                except Exception:  # noqa: BLE001
                    # If calling the function fails, we just continue with empty metadata
                    pass
        # Create the PyField directly
        return cls(
            name=name,
            raw_type=raw_type,
            parent_model=parent_model,  # mypy: ignore
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
            has_default=has_default,
            constraints=constraints,
            metadata=metadata,
        )


def _get_dataclass_field_docs(cls: type) -> dict[str, str]:
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


def get_fields(model_class: type) -> list[PyField]:
    """Extract fields from a model class and convert to PyFields."""
    # First check if it's a dataclass and extract field docstrings
    field_docstrings = {}
    if dataclasses.is_dataclass(model_class):
        field_docstrings = _get_dataclass_field_docs(model_class)

    result = []
    for f in fieldz.fields(model_class, parse_annotated=True):
        # If this is a dataclass field with no description but has a docstring, use it
        if not f.description and f.name in field_docstrings:
            f.description = field_docstrings[f.name]

        result.append(PyField.from_fieldz(f, parent_model=model_class))
    return result


if __name__ == "__main__":
    import dataclasses

    @dataclasses.dataclass
    class TestConfig:
        host: str = "localhost"
        """Server hostname."""

        port: int = 8080
        """Port number to connect to."""

        debug: bool = False
        """Enable debug mode."""

    # Test our field docstring parsing
    field_docs = _get_dataclass_field_docs(TestConfig)

    print("Parsed field docstrings:")
    for name, doc in field_docs.items():
        print(f"  {name}: {doc!r}")
