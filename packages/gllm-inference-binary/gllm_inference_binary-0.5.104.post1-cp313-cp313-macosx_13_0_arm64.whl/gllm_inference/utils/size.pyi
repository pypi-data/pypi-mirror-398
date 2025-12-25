from enum import IntEnum
from gllm_inference.utils.validation import validate_enum as validate_enum
from typing import Any

class SizeUnit(IntEnum):
    """Defines the valid size units."""
    BYTES: int
    KB: int
    MB: int
    GB: int

def get_size(obj: Any, unit: SizeUnit = ...) -> float:
    """Get the pickle-serialized size of an object in the given unit.

    Note:
        This measures the size of the object when serialized using pickle,
        NOT its in-memory footprint.

    Args:
        obj (Any): The object to get the size of.
        unit (SizeUnit, optional): The unit to get the size in. Defaults to SizeUnit.BYTES.

    Returns:
        float: The size of the object in the given mode.
    """
