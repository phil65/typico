"""Form renderer that connects type handlers with UI renderers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from typico.pyfield import bind_model


if TYPE_CHECKING:
    from typico.pyfield import FieldBinding
    from typico.pyfield.bindings import ModelValidationResult
    from typico.pyfield.pyfield import PyField
    from typico.ui.base_renderer import UIWidgetRenderer
    from typico.ui.base_type_handler import TypeHandler


class FormRenderer:
    """Renders form fields using appropriate type handlers and UI renderer.

    This is the main class for rendering forms, bridging between:
    1. Field bindings from the model layer
    2. Type handlers for Python type conversions
    3. UI widget renderers for the actual display
    """

    def __init__(self, ui_renderer: UIWidgetRenderer[Any]):
        """Create a form renderer with a UI-specific implementation.

        Args:
            ui_renderer: The UI framework-specific renderer implementation
        """
        self.ui_renderer = ui_renderer
        self.type_handlers: list[TypeHandler] = []

    def register_handler(self, handler: TypeHandler) -> None:
        """Register a type handler.

        Handlers are checked in order of priority (highest first) and
        the first matching handler is used.

        Args:
            handler: The type handler to register
        """
        self.type_handlers.append(handler)
        # Sort by priority (highest first)
        self.type_handlers.sort(key=lambda h: h.priority, reverse=True)

    def get_handler(self, field: PyField) -> TypeHandler:
        """Find the appropriate handler for this field type.

        Args:
            field: The field to find a handler for

        Returns:
            The first matching type handler

        Raises:
            ValueError: If no handler can process this field
        """
        for handler in self.type_handlers:
            if handler.can_handle(field):
                return handler

        msg = f"No type handler found for field '{field.name}' of type {field.raw_type}"
        raise ValueError(msg)

    def render_field(self, binding: FieldBinding) -> Any:
        """Render a field with the appropriate handler and widget.

        Args:
            binding: The field binding to render

        Returns:
            The UI element rendered by the UI renderer
        """
        if binding.field.hidden:
            return None

        handler = self.get_handler(binding.field)
        method_name, kwargs = handler.prepare_for_render(binding)
        renderer_method = getattr(self.ui_renderer, method_name)
        return renderer_method(**kwargs)

    def render_model(
        self, model_instance: Any
    ) -> tuple[bool, ModelValidationResult | None]:
        """Render a complete form for a model instance.

        Args:
            model_instance: The model instance to render

        Returns:
            Tuple of (was_submitted, validation_result)
            If the form wasn't submitted, validation_result will be None
        """
        binding = bind_model(model_instance)
        with self.ui_renderer.create_form_container(binding.model.name):
            # Render each field
            for field_binding in binding.fields:
                if not field_binding.field.hidden:
                    self.render_field(field_binding)
            submitted = self.ui_renderer.render_submit_button()

        if submitted:
            result = binding.validate()

            # Show validation errors if any
            if not result.is_valid:
                self.ui_renderer.render_validation_errors(
                    field_errors={
                        name: [err.msg for err in errors]
                        for name, errors in result.field_errors.items()
                    },
                    global_errors=[err.msg for err in result.global_errors],
                )

            return submitted, result

        return False, None
