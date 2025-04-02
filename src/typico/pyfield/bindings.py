from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from typico.pyfield.pyfield import PyField
    from typico.pyfield.pymodel import PyModel


@dataclass
class ValidationErrorDetail:
    """Structured information about a validation error."""

    type: str = "value_error"
    msg: str = "Validation error"
    loc: tuple[str | int, ...] = dc_field(default_factory=tuple)
    input_value: Any = None
    ctx: dict[str, Any] = dc_field(default_factory=dict)

    def __str__(self) -> str:
        return f"{self.type}: {self.msg}"


@dataclass
class ModelValidationResult:
    """Result of validating data against a model."""

    is_valid: bool = True
    field_errors: dict[str, list[ValidationErrorDetail]] = dc_field(default_factory=dict)
    global_errors: list[ValidationErrorDetail] = dc_field(default_factory=list)
    validated_instance: Any = None

    @property
    def field_messages(self) -> dict[str, list[str]]:
        """Get human-readable error messages by field."""
        return {
            field: [err.msg for err in errors]
            for field, errors in self.field_errors.items()
        }

    @property
    def global_messages(self) -> list[str]:
        """Get human-readable global error messages."""
        return [err.msg for err in self.global_errors]

    def __bool__(self) -> bool:
        """Return True if validation was successful."""
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
        return not self.validate()

    # @property
    # def validation_errors(self) -> list[str]:
    #     """Get validation errors for the current value."""
    #     return self.ui_state.get("validation_errors", [])

    # def set_validation_errors(self, errors: list[str]) -> None:
    #     """Set validation errors for this field."""
    #     self.ui_state["validation_errors"] = errors

    def validate(self) -> list[ValidationErrorDetail]:
        """Validate this field's current value.

        Performs basic validation including required fields and constraint checks.

        Returns:
            List of validation error details, empty if valid
        """
        errors: list[ValidationErrorDetail] = []
        value = self.value
        field = self.field

        # Check if required
        if value is None and not field.has_default and field.is_required:
            detail = ValidationErrorDetail(
                type="value_error.missing",
                msg="This field is required",
                loc=(field.name,),
                input_value=value,
            )
            errors.append(detail)
            return errors

        # Skip constraint validation for None values
        if value is None:
            return errors

        # Constraint validation
        constraints = field.constraints

        # Number constraints
        if isinstance(value, int | float):
            if constraints.min_value is not None:
                if constraints.exclusive_min and value <= constraints.min_value:
                    detail = ValidationErrorDetail(
                        type="value_error.number.not_gt",
                        msg=f"Must be greater than {constraints.min_value}",
                        loc=(field.name,),
                        input_value=value,
                        ctx={"limit_value": constraints.min_value},
                    )
                    errors.append(detail)
                elif not constraints.exclusive_min and value < constraints.min_value:
                    detail = ValidationErrorDetail(
                        type="value_error.number.not_ge",
                        msg=f"Must be greater than or equal to {constraints.min_value}",
                        loc=(field.name,),
                        input_value=value,
                        ctx={"limit_value": constraints.min_value},
                    )
                    errors.append(detail)

            if constraints.max_value is not None:
                if constraints.exclusive_max and value >= constraints.max_value:
                    detail = ValidationErrorDetail(
                        type="value_error.number.not_lt",
                        msg=f"Must be less than {constraints.max_value}",
                        loc=(field.name,),
                        input_value=value,
                        ctx={"limit_value": constraints.max_value},
                    )
                    errors.append(detail)
                elif not constraints.exclusive_max and value > constraints.max_value:
                    detail = ValidationErrorDetail(
                        type="value_error.number.not_le",
                        msg=f"Must be less than or equal to {constraints.max_value}",
                        loc=(field.name,),
                        input_value=value,
                        ctx={"limit_value": constraints.max_value},
                    )
                    errors.append(detail)

            if (
                constraints.multiple_of is not None
                and value % constraints.multiple_of != 0
            ):
                detail = ValidationErrorDetail(
                    type="value_error.number.not_multiple",
                    msg=f"Must be a multiple of {constraints.multiple_of}",
                    loc=(field.name,),
                    input_value=value,
                    ctx={"multiple_of": constraints.multiple_of},
                )
                errors.append(detail)

        # String constraints
        if isinstance(value, str):
            if constraints.min_length is not None and len(value) < constraints.min_length:
                detail = ValidationErrorDetail(
                    type="value_error.string.min_length",
                    msg=f"Must be at least {constraints.min_length} characters",
                    loc=(field.name,),
                    input_value=value,
                    ctx={"min_length": constraints.min_length},
                )
                errors.append(detail)

            if constraints.max_length is not None and len(value) > constraints.max_length:
                detail = ValidationErrorDetail(
                    type="value_error.string.max_length",
                    msg=f"Must be at most {constraints.max_length} characters",
                    loc=(field.name,),
                    input_value=value,
                    ctx={"max_length": constraints.max_length},
                )
                errors.append(detail)

            if constraints.pattern is not None:
                import re

                if not re.match(constraints.pattern, value):
                    detail = ValidationErrorDetail(
                        type="value_error.string.pattern",
                        msg=f"Must match pattern: {constraints.pattern}",
                        loc=(field.name,),
                        input_value=value,
                        ctx={"pattern": constraints.pattern},
                    )
                    errors.append(detail)

        # Collection constraints
        if isinstance(value, list | tuple | set):
            if constraints.min_items is not None and len(value) < constraints.min_items:
                detail = ValidationErrorDetail(
                    type="value_error.collection.min_items",
                    msg=f"Must have at least {constraints.min_items} items",
                    loc=(field.name,),
                    input_value=value,
                    ctx={"min_items": constraints.min_items},
                )
                errors.append(detail)

            if constraints.max_items is not None and len(value) > constraints.max_items:
                detail = ValidationErrorDetail(
                    type="value_error.collection.max_items",
                    msg=f"Must have at most {constraints.max_items} items",
                    loc=(field.name,),
                    input_value=value,
                    ctx={"max_items": constraints.max_items},
                )
                errors.append(detail)

        # Check allowed values
        if (
            constraints.allowed_values is not None
            and value not in constraints.allowed_values
        ):
            vals = ", ".join(str(v) for v in constraints.allowed_values)
            detail = ValidationErrorDetail(
                type="value_error.not_in_enum",
                msg=f"Value must be one of: {vals}",
                loc=(field.name,),
                input_value=value,
                ctx={"allowed_values": constraints.allowed_values},
            )
            errors.append(detail)

        return errors


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

    def validate(self) -> ModelValidationResult:
        """Validate the current state of this binding."""
        # If the model has a custom validator, use it with the binding itself
        if self.model.validator:
            return self.model.validator(self)

        # Basic validation if no custom validator
        field_errors: dict[str, list[ValidationErrorDetail]] = {}
        global_errors: list[ValidationErrorDetail] = []

        for field_binding in self.fields:
            # Get field-level validation errors
            field_validation_details = field_binding.validate()
            if field_validation_details:
                field_errors[field_binding.field.name] = field_validation_details

        return ModelValidationResult(
            is_valid=not field_errors and not global_errors,
            field_errors=field_errors,
            global_errors=global_errors,
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
