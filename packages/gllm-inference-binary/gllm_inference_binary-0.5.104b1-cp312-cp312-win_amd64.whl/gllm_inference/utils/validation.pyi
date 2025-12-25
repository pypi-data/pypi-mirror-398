from _typeshed import Incomplete
from enum import Enum, StrEnum as StrEnum
from typing import TypeVar

E = TypeVar('E', bound=Enum)
logger: Incomplete

def validate_string_enum(enum_type: type[StrEnum], value: str) -> None:
    """Validates that the provided value is a valid string enum value.

    Args:
        enum_type (type[StrEnum]): The type of the string enum.
        value (str): The value to validate.

    Raises:
        ValueError: If the provided value is not a valid string enum value.
    """
def validate_enum(enum_type: type[E], value: object) -> None:
    """Validates that the provided value is a valid enum value.

    Args:
        enum_type (type[E]): The type of the enum.
        value (object): The value to validate.

    Raises:
        ValueError: If the provided value is not a valid enum value.
    """
