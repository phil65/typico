"""Base class for type-specific field handling."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, ClassVar


if TYPE_CHECKING:
    from collections.abc import Callable

    from typico.pyfield import FieldBinding, PyField


class TypeHandler(ABC):
    """Base class for type-specific field handling.

    Type handlers bridge between Python types and UI renderers by:
    1. Converting Python values to UI-friendly formats
    2. Setting up callbacks to convert UI values back to Python types
    3. Selecting the appropriate UI widget for each field type
    """

    # Handler priority (higher values = more specific handlers)
    priority: ClassVar[int] = 100

    @abstractmethod
    def can_handle(self, field: PyField) -> bool:
        """Check if this handler can process this field type."""

    @abstractmethod
    def prepare_for_render(self, binding: FieldBinding) -> tuple[str, dict[str, Any]]:
        """Convert field data to renderer-friendly format.

        Returns:
            Tuple of (renderer_method_name, kwargs_for_renderer)
        """

    def process_value(self, binding: FieldBinding, raw_value: Any) -> Any:
        """Process a value from the UI back into the appropriate Python type.

        Args:
            binding: The field binding being updated
            raw_value: The raw value from the UI widget

        Returns:
            Converted value in the appropriate Python type
        """
        # Default implementation just returns the raw value
        return raw_value

    def create_change_handler(self, binding: FieldBinding) -> Callable[[Any], None]:
        """Create a callback function for handling UI value changes.

        Args:
            binding: The field binding to update

        Returns:
            A callback function that can be passed to UI components
        """

        # This creates a closure capturing the binding
        def on_change(raw_value: Any) -> None:
            # Process the raw value from UI to Python type
            processed_value = self.process_value(binding, raw_value)
            # Update the binding with the processed value
            binding.value = processed_value

        return on_change
