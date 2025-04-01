# Typico

[![PyPI License](https://img.shields.io/pypi/l/typico.svg)](https://pypi.org/project/typico/)
[![Package status](https://img.shields.io/pypi/status/typico.svg)](https://pypi.org/project/typico/)
[![Daily downloads](https://img.shields.io/pypi/dd/typico.svg)](https://pypi.org/project/typico/)
[![Weekly downloads](https://img.shields.io/pypi/dw/typico.svg)](https://pypi.org/project/typico/)
[![Monthly downloads](https://img.shields.io/pypi/dm/typico.svg)](https://pypi.org/project/typico/)
[![Distribution format](https://img.shields.io/pypi/format/typico.svg)](https://pypi.org/project/typico/)
[![Wheel availability](https://img.shields.io/pypi/wheel/typico.svg)](https://pypi.org/project/typico/)
[![Python version](https://img.shields.io/pypi/pyversions/typico.svg)](https://pypi.org/project/typico/)
[![Implementation](https://img.shields.io/pypi/implementation/typico.svg)](https://pypi.org/project/typico/)
[![Releases](https://img.shields.io/github/downloads/phil65/typico/total.svg)](https://github.com/phil65/typico/releases)
[![Github Contributors](https://img.shields.io/github/contributors/phil65/typico)](https://github.com/phil65/typico/graphs/contributors)
[![Github Discussions](https://img.shields.io/github/discussions/phil65/typico)](https://github.com/phil65/typico/discussions)
[![Github Forks](https://img.shields.io/github/forks/phil65/typico)](https://github.com/phil65/typico/forks)
[![Github Issues](https://img.shields.io/github/issues/phil65/typico)](https://github.com/phil65/typico/issues)
[![Github Issues](https://img.shields.io/github/issues-pr/phil65/typico)](https://github.com/phil65/typico/pulls)
[![Github Watchers](https://img.shields.io/github/watchers/phil65/typico)](https://github.com/phil65/typico/watchers)
[![Github Stars](https://img.shields.io/github/stars/phil65/typico)](https://github.com/phil65/typico/stars)
[![Github Repository size](https://img.shields.io/github/repo-size/phil65/typico)](https://github.com/phil65/typico)
[![Github last commit](https://img.shields.io/github/last-commit/phil65/typico)](https://github.com/phil65/typico/commits)
[![Github release date](https://img.shields.io/github/release-date/phil65/typico)](https://github.com/phil65/typico/releases)
[![Github language count](https://img.shields.io/github/languages/count/phil65/typico)](https://github.com/phil65/typico)
[![Github commits this week](https://img.shields.io/github/commit-activity/w/phil65/typico)](https://github.com/phil65/typico)
[![Github commits this month](https://img.shields.io/github/commit-activity/m/phil65/typico)](https://github.com/phil65/typico)
[![Github commits this year](https://img.shields.io/github/commit-activity/y/phil65/typico)](https://github.com/phil65/typico)
[![Package status](https://codecov.io/gh/phil65/typico/branch/main/graph/badge.svg)](https://codecov.io/gh/phil65/typico/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![PyUp](https://pyup.io/repos/github/phil65/typico/shield.svg)](https://pyup.io/repos/github/phil65/typico/)

[Read the documentation!](https://phil65.github.io/typico/)


# Typico

Typico is a powerful introspection library for Python data models, making it easy to work with Pydantic models, dataclasses, and other structured data in UI frameworks, form generators, and more.

## Quick Start

```python
from dataclasses import dataclass
from typing import Annotated
from pydantic import BaseModel, Field
from typico import get_model, get_fields, bind_model

# Works with Pydantic models
class User(BaseModel):
    name: str = Field(description="User's full name")
    email: Annotated[str, {"field_type": "email"}]
    age: int = Field(ge=0, le=120, default=30)

# And with dataclasses
@dataclass
class Config:
    host: str = "localhost"
    """Server hostname"""
    port: int = 8080
    """Port number"""

# Get field information
user_fields = get_fields(User)
for field in user_fields:
    print(f"{field.name}: {field.raw_type} (required: {field.is_required})")

# Get complete model information
user_model = get_model(User)
print(f"Model: {user_model.name}, Fields: {len(user_model.fields)}")

# Create bindings to a specific instance
user = User(name="Jane", email="jane@example.com")
binding = bind_model(user)
print(f"Current name: {binding['name'].value}")
binding['name'].value = "Jane Doe"  # Update the value
```

## Top-Level API

| Function/Class   | Description                                                 |
|------------------|-------------------------------------------------------------|
| `PyField`        | Field metadata representation                               |
| `PyModel`        | Model metadata representation                               |
| `Constraints`    | Field validation constraints                                |
| `FieldBinding`   | Connects a field definition to an instance value            |
| `ModelBinding`   | Connects a model definition to an instance                  |
| `get_fields()`   | Extract field metadata from a model class                   |
| `get_model()`    | Create a PyModel from a model class                         |
| `bind_model()`   | Create bindings between a model definition and an instance  |

## Field Metadata (`PyField`)

The `PyField` class provides rich metadata about a field:

```python
@dataclass
class PyField:
    name: str                 # Field name
    raw_type: Any             # Python type annotation
    parent_model: type | None # Parent model class
    field_type: str | None    # Custom field type (from annotations)
    title: str | None         # Display title
    description: str | None   # Detailed description
    placeholder: str | None   # Placeholder text
    examples: list[Any] | None # Example values
    hidden: bool              # Whether field should be hidden
    readonly: bool            # Whether field is immutable
    deprecated: bool          # Whether field is deprecated
    is_required: bool         # Whether field is required
    default: Any              # Default value
    has_default: bool         # Whether field has a default
    constraints: Constraints  # Validation constraints
    metadata: dict[str, Any]  # Additional metadata
```

## Model Metadata (`PyModel`)

The `PyModel` class encapsulates metadata about a model:

```python
@dataclass
class PyModel:
    name: str                # Model class name
    fields: list[PyField]    # List of fields
    title: str               # Human-readable title
    description: str | None  # Detailed description
    frozen: bool            # Whether model is immutable
    metadata: dict[str, Any] # Additional metadata

    # Get fields with optional filtering
    def get_fields(
        self,
        required: bool | None = None,
        hidden: bool | None = None,
        readonly: bool | None = None,
        deprecated: bool | None = None,
        field_type: str | None = None,
    ) -> list[PyField]
```

## Validation Constraints (`Constraints`)

The `Constraints` class captures validation rules for a field:

```python
@dataclass
class Constraints:
    min_value: float | None = None      # Minimum value
    max_value: float | None = None      # Maximum value
    exclusive_min: bool = False         # Is min exclusive?
    exclusive_max: bool = False         # Is max exclusive?
    multiple_of: float | None = None    # Must be multiple of
    min_length: int | None = None       # Minimum length
    max_length: int | None = None       # Maximum length
    pattern: str | None = None          # Regex pattern
    min_items: int | None = None        # Min collection items
    max_items: int | None = None        # Max collection items
    allowed_values: list[Any] | None = None  # Allowed values
```

## Data Bindings

Typico provides powerful bindings to connect model definitions with actual instances:

### Field Binding

```python
@dataclass
class FieldBinding:
    field: PyField           # Field metadata
    instance: Any            # Model instance
    ui_state: dict[str, Any] # UI state
    @property
    def value(self) -> Any:  # Get current value
    @value.setter
    def value(self, new_value: Any): # Set new value
    @property
    def is_valid(self) -> bool:      # Check if valid
    @property
    def validation_errors(self) -> list[str]: # Get errors
    def set_validation_errors(self, errors: list[str]) -> None


### Model Binding

```python
@dataclass
class ModelBinding:
    model: PyModel           # Model metadata
    instance: Any            # Model instance
    fields: list[FieldBinding] # Field bindings
    # Access fields by name
    def __getitem__(self, key: str) -> FieldBinding
    def get_field_binding(self, name: str) -> FieldBinding
    @classmethod
    def from_instance(cls, instance: object) -> ModelBinding
```

## Custom Field Types

Typico supports custom field types through the `field_type` attribute in `PyField`. You can specify field types using the `Annotated` type:

```python
from typing import Annotated
from pydantic import BaseModel

class User(BaseModel):
    username: str
    email: Annotated[str, {"field_type": "email"}]
    password: Annotated[str, {"field_type": "password"}]
    avatar: Annotated[str, {"field_type": "image"}]
    bio: Annotated[str, {"field_type": "markdown"}]
```

UI frameworks can use this information to render appropriate controls.

## Integration with UI Frameworks

Typico is designed to work seamlessly with UI frameworks:

```python
# Example with a hypothetical UI library
from typico import bind_model
from my_ui_lib import Form, TextField, EmailField, NumberField

def create_form(model_instance):
    binding = bind_model(model_instance)
    form = Form(title=binding.model.title)

    for field_binding in binding.fields:
        if field_binding.field.hidden:
            continue

        # handle fields here

        form.add_field(field)

    return form
```

## License

MIT
