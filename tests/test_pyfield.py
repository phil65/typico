"""Tests for the PyField class."""

from __future__ import annotations

from typing import Annotated, Optional

from pydantic import BaseModel, Field
import pytest

from typico.pyfield import PyField


class Address(BaseModel):
    """Test nested model."""

    street: str
    city: str
    zip_code: str


class _TestModel(BaseModel):
    """Test model with various field types."""

    id: int = Field(description="Unique identifier")
    name: str = Field(title="Full Name")
    email: Annotated[str, {"field_type": "email"}]
    age: int = Field(ge=0, le=120)
    is_active: bool = True
    tags: list[str] = []
    address: Address | None = None
    notes: str = Field(min_length=5, max_length=1000, default="")
    model_id: Annotated[str, {"field_type": "llm_model_identifier"}] = Field(
        default="gpt-3.5-turbo",
        description="The LLM model to use",
        examples=["gpt-3.5-turbo", "gpt-4"],
    )


def test_basic_field_extraction():
    """Test extraction of basic field information."""
    # Create PyField from the 'name' field
    field = PyField.from_pydantic("name", _TestModel)

    assert field.name == "name"
    assert field.title == "Full Name"  # Uses title from Field
    assert field.raw_type is str
    assert field.parent_model is _TestModel
    assert field.field_type is None  # No field_type specified


def test_annotated_field_type():
    """Test extraction of field_type from Annotated fields."""
    # Create PyField from the 'email' field which has Annotated field_type
    field = PyField.from_pydantic("email", _TestModel)

    assert field.name == "email"
    assert field.field_type == "email"
    assert field.raw_type is str  # Should extract the actual type from Annotated


def test_domain_specific_field_type():
    """Test extraction of domain-specific field types."""
    # Test the model_id field with custom field_type
    field = PyField.from_pydantic("model_id", _TestModel)

    assert field.field_type == "llm_model_identifier"
    assert field.default == "gpt-3.5-turbo"
    assert field.description == "The LLM model to use"
    assert field.examples is not None
    assert field.examples[0] == "gpt-3.5-turbo"


def test_constraints_extraction():
    """Test extraction of validation constraints."""
    # Test the 'age' field with constraints
    field = PyField.from_pydantic("age", _TestModel)

    assert field.constraints.min_value == 0
    assert field.constraints.max_value == 120  # noqa: PLR2004
    assert field.constraints.exclusive_min is False
    assert field.constraints.exclusive_max is False

    # Test the 'notes' field with length constraints
    field = PyField.from_pydantic("notes", _TestModel)

    assert field.constraints.min_length == 5  # noqa: PLR2004
    assert field.constraints.max_length == 1000  # noqa: PLR2004


def test_required_and_default():
    """Test required status and default value extraction."""
    # 'id' is required and has no default
    field = PyField.from_pydantic("id", _TestModel)

    assert field.is_required is True
    assert field.has_default is False

    # 'is_active' has a default value
    field = PyField.from_pydantic("is_active", _TestModel)

    assert field.has_default is True
    assert field.default is True


def test_nested_model_field():
    """Test handling of nested model fields."""
    field = PyField.from_pydantic("address", _TestModel)

    assert field.raw_type == Optional[Address]  # noqa: UP045
    assert field.is_required is False  # Should be optional


def test_examples_and_placeholder():
    """Test extraction of examples and placeholder."""
    field = PyField.from_pydantic("model_id", _TestModel)

    assert field.examples is not None
    assert len(field.examples) == 2  # noqa: PLR2004
    assert field.examples[0] == "gpt-3.5-turbo"
    assert field.placeholder == "gpt-3.5-turbo"  # First example becomes placeholder


if __name__ == "__main__":
    pytest.main([__file__])
