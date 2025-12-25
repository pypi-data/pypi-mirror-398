"""Utility module related to Pydantic models and fields."""

# ───────────────────────────────────────────────────── imports ────────────────────────────────────────────────────── #
from copy import deepcopy
from typing import Any, TypeVar

from pydantic import BaseModel, create_model
from pydantic.alias_generators import to_camel
from pydantic.fields import FieldInfo

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#         Defines the public interface of the module that will be imported when using 'from package import *'.         #
#    This helps control what is exposed to the global namespace, limiting imports to only those listed in __all__.     #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #

__all__ = [
    "AnnotationType",
    "BaseModelT",
    "update_field_default",
    "new_base_model_class",
    "is_camel_case",
    "to_lower_camel",
]

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                                                        Typing                                                        #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #

AnnotationType = tuple[Any, FieldInfo]

BaseModelT = TypeVar("BaseModelT", bound=BaseModel)


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                                                Module Implementation                                                 #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #


def update_field_default(field: FieldInfo, default: Any) -> AnnotationType:
    """Update the default value of a Pydantic field.

    Args:
        field (FieldInfo): The field to modify.
        default (Any): The new default value.

    Returns:
        AnnotationType: A tuple containing the field's annotation and updated FieldInfo.
    """
    new = deepcopy(field)
    new.default = default
    return new.annotation, new


def new_base_model_class(cls: type[BaseModelT], new_annotations: dict[str, AnnotationType]) -> type[BaseModelT]:
    """Create a new Pydantic `BaseModel` class with updated annotations.

    Args:
        cls (type[BaseModelT]): The original `BaseModel` class.
        new_annotations (dict[str, AnnotationType]): A dictionary of field names and their updated annotations.

    Returns:
        type[BaseModelT]: A new `BaseModel` class with the specified annotations.
    """
    field_definitions = {name: (field.annotation, field) for name, field in cls.model_fields.items()}
    field_definitions.update(new_annotations)
    return create_model(
        cls.__name__,
        __config__=None,
        __doc__=cls.__doc__,
        __base__=cls,
        __module__=cls.__module__,
        __validators__=None,
        __cls_kwargs__=None,
        __slots__=None,
        **field_definitions,
    )


def is_camel_case(value: str) -> bool:
    """Check if a string is in camelCase format.

    Args:
        value (str): The string to check.

    Returns:
        bool: True if the string is in camelCase, False otherwise.
    """
    return value != value.lower() and value != value.upper() and "_" not in value


def to_lower_camel(value: str) -> str:
    """Convert a string to lowerCamelCase format.

    Args:
        value (str): The string to convert.

    Returns:
        str: The string in lowerCamelCase format.
    """
    return value if is_camel_case(value=value) else to_camel(value)
