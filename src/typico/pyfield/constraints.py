from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    import fieldz


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

    @classmethod
    def from_jsonschema(cls, schema: dict[str, Any]) -> Constraints:
        """Create a Constraints instance from JSON Schema properties.

        Args:
            schema: Dictionary containing JSON Schema constraint properties

        Returns:
            A Constraints instance with values populated from the schema
        """
        constraints = cls()

        # Extract numeric constraints
        if "minimum" in schema:
            constraints.min_value = schema["minimum"]
        if "maximum" in schema:
            constraints.max_value = schema["maximum"]
        if "exclusiveMinimum" in schema:
            constraints.min_value = schema["exclusiveMinimum"]
            constraints.exclusive_min = True
        if "exclusiveMaximum" in schema:
            constraints.max_value = schema["exclusiveMaximum"]
            constraints.exclusive_max = True
        if "multipleOf" in schema:
            constraints.multiple_of = schema["multipleOf"]

        # Extract string/array constraints
        if "minLength" in schema:
            constraints.min_length = schema["minLength"]
        if "maxLength" in schema:
            constraints.max_length = schema["maxLength"]
        if "pattern" in schema:
            constraints.pattern = schema["pattern"]
        if "minItems" in schema:
            constraints.min_items = schema["minItems"]
        if "maxItems" in schema:
            constraints.max_items = schema["maxItems"]

        # Extract allowed values if enum is present
        if "enum" in schema:
            constraints.allowed_values = schema["enum"]

        return constraints
