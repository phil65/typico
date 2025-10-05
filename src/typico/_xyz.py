from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
import inspect
from typing import TYPE_CHECKING, Any, Literal, TypeVar, get_args, get_origin

from pydantic import BaseModel, Field, SecretStr


if TYPE_CHECKING:
    from pydantic.fields import FieldInfo


T = TypeVar("T", bound=BaseModel)
AnyType = Any

PRIMITIVE_TYPES: set[type] = {
    str,
    int,
    float,
    bool,
    Decimal,
    date,
    datetime,
    time,
    SecretStr,
}


def is_primitive(typ) -> bool:
    """Check if a type is a primitive type."""
    if typ in PRIMITIVE_TYPES:
        return True
    try:
        return inspect.isclass(typ) and any(issubclass(typ, t) for t in PRIMITIVE_TYPES)
    except TypeError:
        return False


class PydanticField:
    """Represents metadata about a Pydantic model field."""

    def __init__(
        self,
        name: str,
        raw_type: AnyType,
        field_info: FieldInfo,
        parent_model: type[BaseModel],
        default: Any = None,
        description: str | None = None,
        is_required: bool = False,
    ):
        self.name: str = name
        self.default = default
        self.raw_type = raw_type
        self.field_info = field_info
        self.parent_model = parent_model
        self.description = description
        self.is_required = is_required

    @classmethod
    def from_model(cls, model: type[BaseModel] | BaseModel) -> list[PydanticField]:
        """Extract field information from a Pydantic model class or instance.

        Args:
            model: A Pydantic model class or instance

        Returns:
            List of PydanticField objects representing each field
        """
        model_class = model if inspect.isclass(model) else model.__class__
        schema = model_class.model_json_schema()  # type: ignore
        properties = schema.get("properties", {})
        required_fields = set(schema.get("required", []))
        result = []
        for field_name, field_info in model_class.model_fields.items():  # type: ignore
            field_schema = properties.get(field_name, {})
            description = field_schema.get("description")
            is_required = field_name in required_fields
            field_type = field_info.annotation if field_info.annotation != Any else Any
            default = field_info.default if field_info.default is not None else None
            field = cls(
                name=field_name,
                raw_type=field_type,
                field_info=field_info,
                parent_model=model_class,  # type: ignore
                default=default,
                description=description,
                is_required=is_required,
            )
            result.append(field)

        return result

    def is_literal_type(self) -> bool:
        """Check if this field's type is a Literal."""
        origin = get_origin(self.raw_type)
        return origin is Literal

    def is_union_type(self) -> bool:
        """Check if this field's type is a Union (including | syntax)."""
        origin = get_origin(self.raw_type)
        if origin is None:
            return False
        return origin.__name__ == "Union" if hasattr(origin, "__name__") else False

    def is_optional_type(self) -> bool:
        """Check if this field's type is Optional (T | None)."""
        if not self.is_union_type():
            return False
        return type(None) in get_args(self.raw_type)

    def is_list_type(self) -> bool:
        """Check if this field's type is a list."""
        origin = get_origin(self.raw_type)
        return origin is list

    def is_set_type(self) -> bool:
        """Check if this field's type is a set."""
        origin = get_origin(self.raw_type)
        return origin is set

    def is_dict_type(self) -> bool:
        """Check if this field's type is a dict."""
        origin = get_origin(self.raw_type)
        return origin is dict

    def is_nested_model(self) -> bool:
        """Check if this field's type is another Pydantic model."""
        if self.is_optional_type():
            args = get_args(self.raw_type)
            # Filter out None
            types = [t for t in args if t is not type(None)]
            if len(types) == 1:
                return self._is_pydantic_model(types[0])
        return self._is_pydantic_model(self.raw_type)

    def _is_pydantic_model(self, typ) -> bool:
        """Check if a type is a Pydantic model."""
        try:
            return (
                inspect.isclass(typ)
                and issubclass(typ, BaseModel)
                and typ is not BaseModel
            )
        except TypeError:
            return False

    def is_enum_type(self) -> bool:
        """Check if this field's type is an Enum."""
        if self.is_optional_type():
            args = get_args(self.raw_type)
            non_none_args = [t for t in args if t is not type(None)]
            if len(non_none_args) == 1:
                return inspect.isclass(non_none_args[0]) and issubclass(
                    non_none_args[0], Enum
                )
        return inspect.isclass(self.raw_type) and issubclass(self.raw_type, Enum)

    def is_primitive_type(self) -> bool:
        """Check if this field's type is a primitive type."""
        if self.is_optional_type():
            args = get_args(self.raw_type)
            non_none_args = [t for t in args if t is not type(None)]
            if len(non_none_args) == 1:
                return is_primitive(non_none_args[0])
        return is_primitive(self.raw_type)

    def get_inner_type(self) -> AnyType:
        """Extract the inner type from containers (List[T], Dict[K, V], etc)."""
        if not (self.is_list_type() or self.is_set_type() or self.is_dict_type()):
            msg = f"Field {self.name} is not a container type"
            raise TypeError(msg)

        args = get_args(self.raw_type)
        if self.is_dict_type():
            # For dictionaries, return the value type (second arg)
            return args[1] if len(args) > 1 else Any
        return args[0] if args else Any

    def get_literal_values(self) -> list[Any]:
        """Get the possible values for a Literal field."""
        if not self.is_literal_type():
            msg = f"Field {self.name} is not a Literal type"
            raise TypeError(msg)
        return list(get_args(self.raw_type))

    def get_union_types(self) -> list[type]:
        """Get the possible types for a Union field."""
        if not self.is_union_type():
            msg = f"Field {self.name} is not a Union type"
            raise TypeError(msg)
        return list(get_args(self.raw_type))

    def create_default_value(self) -> Any:  # noqa: PLR0911
        """Create a default value for this field based on its type."""
        # If field has a default, use it
        if self.default is not None and self.default is not ...:
            return self.default

        # Create type-appropriate defaults
        if self.is_literal_type():
            values = self.get_literal_values()
            return values[0] if values else None

        if self.is_optional_type():
            return None

        if self.is_list_type() or self.is_set_type():
            return [] if self.is_list_type() else set()

        if self.is_dict_type():
            return {}

        if self.is_enum_type():
            try:
                # Get the first enum value
                enum_class = self.raw_type
                if self.is_optional_type():
                    non_none_types = [
                        t for t in get_args(self.raw_type) if t is not type(None)
                    ]
                    enum_class = non_none_types[0] if non_none_types else None

                if enum_class:
                    values = list(enum_class.__members__.values())
                    return values[0] if values else None
            except (AttributeError, IndexError):
                return None

        if self.is_nested_model():
            model_class = self.raw_type
            if self.is_optional_type():
                non_none_types = [
                    t for t in get_args(self.raw_type) if t is not type(None)
                ]
                model_class = non_none_types[0] if non_none_types else None

            if model_class:
                try:
                    return model_class()
                except Exception:  # noqa: BLE001
                    return None

        # Primitive type defaults
        if (
            is_primitive(self.raw_type)
            or (
                self.is_optional_type()
                and any(
                    is_primitive(t)
                    for t in get_args(self.raw_type)
                    if t is not type(None)
                )
            )
        ) and isinstance(self.raw_type, type):
            if issubclass(self.raw_type, str):
                return ""
            if issubclass(self.raw_type, bool):
                return False
            if issubclass(self.raw_type, int):
                return 0
            if issubclass(self.raw_type, float):
                return 0.0
            if issubclass(self.raw_type, Decimal):
                return Decimal("0")
            if issubclass(self.raw_type, date | datetime):
                return datetime.now()
            if issubclass(self.raw_type, time):
                return datetime.now().time()
            if issubclass(self.raw_type, SecretStr):
                return SecretStr("")

        return None

    def get_json_schema_properties(self) -> dict[str, Any]:
        """Get JSON schema properties for this field."""
        schema = self.parent_model.model_json_schema()
        properties = schema.get("properties", {})
        return properties.get(self.name, {})

    def get_constraints(self) -> dict[str, Any]:
        """Get validation constraints for this field."""
        constraints = {}
        schema_props = self.get_json_schema_properties()
        for prop in [
            "minimum",
            "maximum",
            "exclusiveMinimum",
            "exclusiveMaximum",
            "minLength",
            "maxLength",
            "pattern",
            "minItems",
            "maxItems",
            "format",
            "multipleOf",
        ]:
            if prop in schema_props:
                constraints[prop] = schema_props[prop]

        return constraints

    def __repr__(self) -> str:
        type_name = getattr(self.raw_type, "__name__", str(self.raw_type))
        return f"PydanticField(name='{self.name}', type={type_name})"


if __name__ == "__main__":

    class Address(BaseModel):
        street: str
        city: str
        zip_code: str

    class UserStatus(str, Enum):
        ACTIVE = "active"
        INACTIVE = "inactive"
        PENDING = "pending"

    class User(BaseModel):
        id: int
        name: str = Field(description="The user's full name")
        email: str | None = None
        age: int = Field(ge=0, le=120)
        is_admin: bool = False
        status: UserStatus = UserStatus.PENDING
        address: Address | None = None
        tags: list[str] = []
        metadata: dict[str, Any] = {}

    fields = PydanticField.from_model(User)
    for field in fields:
        print(f"{field.name}: {field.raw_type}")
        print(f"  Required: {field.is_required}")
        print(f"  Description: {field.description}")
        print(f"  Default: {field.default}")

        if field.is_nested_model():
            print("  This is a nested model")
        elif field.is_enum_type():
            print("  This is an enum")
        elif field.is_list_type():
            print(f"  This is a list of {field.get_inner_type()}")
        elif field.is_dict_type():
            print(f"  This is a dict with values of type {field.get_inner_type()}")

        print(f"  Default value: {field.create_default_value()}")
        print()
