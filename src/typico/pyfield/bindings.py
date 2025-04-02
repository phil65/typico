from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from typing import TYPE_CHECKING, Any, TypeVar


if TYPE_CHECKING:
    from typico.pyfield.pyfield import PyField
    from typico.pyfield.pymodel import PyModel


T = TypeVar("T")


@dataclass
class ValidationResult:
    """Result of validating data against a model."""

    is_valid: bool = True
    field_errors: dict[str, list[str]] = dc_field(default_factory=dict)
    global_errors: list[str] = dc_field(default_factory=list)
    validated_instance: Any = None

    @property
    def errors(self) -> dict[str, list[str]]:
        """Legacy access to combined errors."""
        combined = self.field_errors.copy()
        if self.global_errors:
            combined["_errors"] = self.global_errors
        return combined

    def __bool__(self) -> bool:
        """Return True if validation was successful, False otherwise."""
        return self.is_valid


@dataclass
class FieldBinding:
    """Connects a PyField to a specific instance value."""

    field: PyField
    """The field metadata."""

    instance: Any
    """The model instance containing the value."""

    ui_state: dict[str, Any] = dc_field(default_factory=dict)
    """Additional UI state for this field (e.g., validation errors, dirty status)."""

    @property
    def value(self) -> Any:
        """Get the current value from the instance."""
        return getattr(self.instance, self.field.name, None)

    @value.setter
    def value(self, new_value: Any) -> None:
        """Set a new value on the instance."""
        setattr(self.instance, self.field.name, new_value)

    @property
    def is_valid(self) -> bool:
        """Check if the current value is valid."""
        return not self.validation_errors

    @property
    def validation_errors(self) -> list[str]:
        """Get validation errors for the current value."""
        return self.ui_state.get("validation_errors", [])

    def set_validation_errors(self, errors: list[str]) -> None:
        """Set validation errors for this field."""
        self.ui_state["validation_errors"] = errors


@dataclass
class ModelBinding:
    """Connects a PyModel to a specific instance."""

    model: PyModel
    """The model metadata."""

    instance: Any
    """The model instance."""

    fields: list[FieldBinding] = dc_field(default_factory=list)
    """Bindings for each field in the model."""

    ui_state: dict[str, Any] = dc_field(default_factory=dict)
    """Additional UI state for this model (e.g., form dirty status)."""

    def __getitem__(self, key: str) -> FieldBinding:
        """Get a field binding by name."""
        return self.get_field_binding(key)

    def validate(self) -> ValidationResult:
        """Validate the current state of this binding."""
        # If the model has a custom validator, use it with the binding itself
        if self.model.validator:
            return self.model.validator(self)

        # Basic validation if no custom validator
        errors: dict[str, Any] = {}
        for field_binding in self.fields:
            field = field_binding.field
            value = field_binding.value

            # Check required fields
            if value is None and not field.has_default and field.is_required:
                errors.setdefault(field.name, []).append("This field is required")

        return ValidationResult(
            is_valid=not errors,
            field_errors=errors,
            validated_instance=self.instance,
        )

    @classmethod
    def from_instance(cls, instance: object) -> ModelBinding:
        """Create a ModelBinding from a model instance.

        Args:
            instance: The model instance to bind to

        Returns:
            A ModelBinding connecting the model metadata to the instance
        """
        from typico.pyfield import get_model

        model = get_model(instance.__class__)
        fields = [FieldBinding(field=f, instance=instance) for f in model.fields]
        return cls(model=model, instance=instance, fields=fields)

    def get_field_binding(self, name: str) -> FieldBinding:
        """Get a field binding by name.

        Args:
            name: The field name

        Returns:
            The FieldBinding if found, otherwise None
        """
        for binding in self.fields:
            if binding.field.name == name:
                return binding
        msg = f"Field {name!r} not found in model {self.model.name!r}"
        raise KeyError(msg)


def bind_model(instance: Any) -> ModelBinding:
    """Create bindings for a model instance.

    This is a convenience function for creating a ModelBinding.

    Args:
        instance: The model instance to bind

    Returns:
        A ModelBinding for the instance
    """
    return ModelBinding.from_instance(instance)
