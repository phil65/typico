# Typico

[![PyPI License](https://img.shields.io/pypi/l/typico.svg)](https://pypi.org/project/typico/)
[![Package status](https://img.shields.io/pypi/status/typico.svg)](https://pypi.org/project/typico/)
[![Monthly downloads](https://img.shields.io/pypi/dm/typico.svg)](https://pypi.org/project/typico/)
[![Distribution format](https://img.shields.io/pypi/format/typico.svg)](https://pypi.org/project/typico/)
[![Wheel availability](https://img.shields.io/pypi/wheel/typico.svg)](https://pypi.org/project/typico/)
[![Python version](https://img.shields.io/pypi/pyversions/typico.svg)](https://pypi.org/project/typico/)
[![Implementation](https://img.shields.io/pypi/implementation/typico.svg)](https://pypi.org/project/typico/)
[![Releases](https://img.shields.io/github/downloads/phil65/typico/total.svg)](https://github.com/phil65/typico/releases)
[![Github Contributors](https://img.shields.io/github/contributors/phil65/typico)](https://github.com/phil65/typico/graphs/contributors)
[![Github Forks](https://img.shields.io/github/forks/phil65/typico)](https://github.com/phil65/typico/forks)
[![Github Issues](https://img.shields.io/github/issues/phil65/typico)](https://github.com/phil65/typico/issues)
[![Github Issues](https://img.shields.io/github/issues-pr/phil65/typico)](https://github.com/phil65/typico/pulls)
[![Github Watchers](https://img.shields.io/github/watchers/phil65/typico)](https://github.com/phil65/typico/watchers)
[![Github Stars](https://img.shields.io/github/stars/phil65/typico)](https://github.com/phil65/typico/stars)
[![Github Repository size](https://img.shields.io/github/repo-size/phil65/typico)](https://github.com/phil65/typico)
[![Github last commit](https://img.shields.io/github/last-commit/phil65/typico)](https://github.com/phil65/typico/commits)
[![Github release date](https://img.shields.io/github/release-date/phil65/typico)](https://github.com/phil65/typico/releases)
[![Github language count](https://img.shields.io/github/languages/count/phil65/typico)](https://github.com/phil65/typico)
[![Github commits this month](https://img.shields.io/github/commit-activity/m/phil65/typico)](https://github.com/phil65/typico)
[![Package status](https://codecov.io/gh/phil65/typico/branch/main/graph/badge.svg)](https://codecov.io/gh/phil65/typico/)
[![PyUp](https://pyup.io/repos/github/phil65/typico/shield.svg)](https://pyup.io/repos/github/phil65/typico/)


[Read the documentation!](https://phil65.github.io/typico/)

Typico is an introspection layer for Python data models. It reads Pydantic models,
dataclasses and other [fieldz](https://github.com/pyapp-kit/fieldz)-supported classes and
describes them with one uniform set of objects: field metadata, validation constraints and
instance bindings. That makes it a good foundation for form generators, UI frameworks and
other tools that need to "understand" a model without caring which library defined it.

## Installation

```bash
pip install typico
```

Requires Python 3.13+.

## Quick start

```python
from dataclasses import dataclass
from typing import Annotated

from pydantic import BaseModel, Field

from typico import bind_model, get_fields, get_model


class User(BaseModel):
    name: str = Field(description="User's full name")
    email: Annotated[str, {"field_type": "email"}]
    age: int = Field(ge=0, le=120, default=30)


@dataclass
class Config:
    host: str = "localhost"
    """Server hostname"""

    port: int = 8080
    """Port number"""


# Field metadata, the same API for pydantic models and dataclasses
for field in get_fields(User):
    print(field.name, field.raw_type, field.field_type, field.is_required)
# name <class 'str'> None True
# email <class 'str'> email True
# age <class 'int'> None False

print(get_fields(Config)[0].description)  # "Server hostname" (from the attribute docstring)
print(get_fields(User)[2].constraints.max_value)  # 120

# Model metadata
model = get_model(User)
print(model.name, [f.name for f in model.get_fields(required=True)])  # User ['name', 'email']

# Bind metadata to an instance, read / write values and validate
user = User(name="Jane", email="jane@example.com")
binding = bind_model(user)
binding["name"].value = "Jane Doe"
binding["age"].value = 500
result = binding.validate()
print(result.is_valid, result.field_messages)
# False {'age': ['Input should be less than or equal to 120']}
```

## Key features

- **One API for many model libraries**: Pydantic models, dataclasses and anything
  [fieldz](https://github.com/pyapp-kit/fieldz) understands (attrs, msgspec, ...).
- **Rich field metadata** (`PyField`): type, title, description (also from dataclass
  attribute docstrings), examples / placeholder, default (`MISSING_VALUE` if none),
  required / hidden / readonly / deprecated flags and extra metadata.
- **Constraints** (`Constraints`): min / max values (inclusive or exclusive), `multiple_of`,
  string and collection length, regex pattern, allowed values.
- **Custom field types**: hint a widget with `Annotated[str, {"field_type": "email"}]` or
  `Field(json_schema_extra={"field_type": "email"})`; available as `PyField.field_type`.
- **Bindings** (`FieldBinding`, `ModelBinding`): connect metadata to an instance, get / set
  values and validate. Pydantic models are validated with pydantic itself, other models with
  the extracted constraints.
- **UI building blocks** (`typico.ui`): abstract `UIWidgetRenderer`, `TypeHandler` and
  `FormRenderer` classes to plug a concrete UI toolkit into.

## Top-level API

| Name             | Description                                                     |
|------------------|-----------------------------------------------------------------|
| `PyField`        | Field metadata                                                  |
| `PyModel`        | Model metadata (fields, title, description, frozen, validator)  |
| `Constraints`    | Validation constraints of a field                               |
| `FieldBinding`   | A field bound to an instance (`value`, `validate()`, `is_valid`) |
| `ModelBinding`   | A model bound to an instance (`binding["name"]`, `validate()`)  |
| `get_fields()`   | Extract the `PyField`s of a model class                         |
| `get_model()`    | Create a `PyModel` from a model class                           |
| `bind_model()`   | Create a `ModelBinding` for an instance                         |

## Custom field types

```python
from typing import Annotated

from pydantic import BaseModel

from typico import get_model


class Profile(BaseModel):
    username: str
    email: Annotated[str, {"field_type": "email"}]
    password: Annotated[str, {"field_type": "password"}]
    bio: Annotated[str, {"field_type": "markdown"}] = ""


model = get_model(Profile)
print([f.name for f in model.get_fields(field_type="email")])  # ['email']
```

## Building UI forms

`typico.ui` contains the abstractions for rendering forms; it ships no concrete UI backend:

- `UIWidgetRenderer[T]`: implement `render_text_input`, `render_text_area`,
  `render_number_input`, `render_checkbox`, `render_select`, `render_validation_errors`,
  `create_form_container` and `render_submit_button` for your toolkit.
- `TypeHandler`: decides whether it `can_handle(field)` and returns the renderer method name
  plus keyword arguments from `prepare_for_render(binding)`. Handlers have a `priority`.
- `FormRenderer`: register handlers with `register_handler()`, then call
  `render_model(instance)`, which renders all visible fields, the submit button and, after
  submission, validation errors.

```python
from typico.ui import FormRenderer

renderer = FormRenderer(MyToolkitRenderer())  # your UIWidgetRenderer implementation
renderer.register_handler(MyStringHandler())  # your TypeHandler implementations
submitted, result = renderer.render_model(user)
```

## License

MIT
