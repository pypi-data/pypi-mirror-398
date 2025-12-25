from gllm_core.schema import Chunk as Chunk
from pydantic import BaseModel
from typing import Any

class StreamBufferType:
    """Defines stream buffer type constants."""
    CITATION: str
    TEXT: str
    THINKING: str
    TOOL_CALL: str

class StreamBuffer(BaseModel):
    """Defines a schema for tracking LM invocation streaming buffer.

    Attributes:
        id (str): The ID of the buffer. Defaults to an empty string.
        type (str): The type of the buffer. Defaults to an empty string.
        text (str): The buffer accumulating text content. Defaults to empty string.
        thinking (str): The buffer accumulating thinking content. Defaults to empty string.
        tool_call (dict[str, Any]): The buffer accumulating tool call. Defaults to an empty dictionary.
        citations (list[Chunk]): The buffer accumulating citations. Defaults to an empty list.
    """
    id: str
    type: str
    text: str
    thinking: str
    tool_call: dict[str, Any]
    citations: list[Chunk]
