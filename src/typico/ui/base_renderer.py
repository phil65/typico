"""Base interface for UI widget renderers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Generic, TypeVar


if TYPE_CHECKING:
    from collections.abc import Callable


# Generic type for UI component/element return values
T = TypeVar("T")


class UIWidgetRenderer(Generic[T], ABC):
    """Low-level UI widget rendering interface.

    UI libraries implementing this interface should render widgets using their
    native components and handle value changes through the provided callbacks.
    """

    @abstractmethod
    def render_text_input(
        self,
        value: str,
        label: str,
        placeholder: str = "",
        help_text: str | None = None,
        required: bool = False,
        readonly: bool = False,
        on_change: Callable[[str], None] | None = None,
    ) -> T:
        """Render a single-line text input."""

    @abstractmethod
    def render_text_area(
        self,
        value: str,
        label: str,
        placeholder: str = "",
        help_text: str | None = None,
        required: bool = False,
        readonly: bool = False,
        on_change: Callable[[str], None] | None = None,
    ) -> T:
        """Render a multi-line text input."""

    @abstractmethod
    def render_number_input(
        self,
        value: float | None,
        label: str,
        min_value: float | None = None,
        max_value: float | None = None,
        step: float = 1,
        help_text: str | None = None,
        required: bool = False,
        readonly: bool = False,
        on_change: Callable[[float | int | None], None] | None = None,
    ) -> T:
        """Render a number input."""

    @abstractmethod
    def render_checkbox(
        self,
        value: bool,
        label: str,
        help_text: str | None = None,
        readonly: bool = False,
        on_change: Callable[[bool], None] | None = None,
    ) -> T:
        """Render a checkbox for boolean values."""

    @abstractmethod
    def render_select(
        self,
        value: Any,
        options: list[tuple[Any, str]],  # (value, label) pairs
        label: str,
        multiple: bool = False,
        help_text: str | None = None,
        required: bool = False,
        readonly: bool = False,
        on_change: Callable[[Any], None] | None = None,
    ) -> T:
        """Render a dropdown/select widget."""

    @abstractmethod
    def render_validation_errors(
        self,
        field_errors: dict[str, list[str]],
        global_errors: list[str],
    ) -> None:
        """Display validation error messages."""

    @abstractmethod
    def create_form_container(
        self,
        name: str,
        on_submit: Callable[[], None] | None = None,
    ) -> Any:
        """Create a form container.

        Returns a context manager or object representing the form container.
        """

    @abstractmethod
    def render_submit_button(
        self,
        label: str = "Submit",
    ) -> bool:
        """Render a form submit button.

        Returns:
            True if the button was clicked/form was submitted, False otherwise
        """
