from gllm_inference.schema.enums import NativeToolType as NativeToolType
from gllm_inference.utils.validation import validate_enum as validate_enum
from pydantic import BaseModel
from typing import Any

class Key:
    """Defines valid keys in native tool."""
    TYPE: str

class NativeTool(BaseModel):
    """Defines the native tool schema.

    Attributes:
        type (NativeToolType): The type of the native tool.
        kwargs (dict[str, Any]): The additional keyword arguments of the native tool.
    """
    type: NativeToolType
    kwargs: dict[str, Any]
    @classmethod
    def code_interpreter(cls, **kwargs: Any) -> NativeTool:
        """Create a code interpreter native tool.

        Args:
            **kwargs (Any): The keyword arguments of the code interpreter native tool.

        Returns:
            NativeTool: A new code interpreter native tool.
        """
    @classmethod
    def from_str_or_dict(cls, data: str | dict[str, Any]) -> NativeTool:
        """Create a native tool from a string or a dictionary.

        Args:
            data (str | dict[str, Any]): The string or dictionary that represents the native tool.

        Returns:
            NativeTool: A new native tool.
        """
