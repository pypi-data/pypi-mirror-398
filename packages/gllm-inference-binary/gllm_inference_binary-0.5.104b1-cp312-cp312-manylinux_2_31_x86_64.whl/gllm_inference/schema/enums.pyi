from enum import StrEnum

class AttachmentType(StrEnum):
    """Defines valid attachment types."""
    AUDIO: str
    DOCUMENT: str
    IMAGE: str
    VIDEO: str

class BatchStatus(StrEnum):
    """Defines the status of a batch job."""
    IN_PROGRESS: str
    FINISHED: str
    FAILED: str
    CANCELING: str
    EXPIRED: str
    UNKNOWN: str

class LMEventType(StrEnum):
    """Defines event types to be emitted by the LM invoker."""
    ACTIVITY: str
    CODE: str
    THINKING: str

class LMEventTypeSuffix(StrEnum):
    """Defines suffixes for LM event types."""
    START: str
    END: str

class EmitDataType(StrEnum):
    """Defines valid data types for emitting events."""
    ACTIVITY: str
    CODE: str
    CODE_START: str
    CODE_END: str
    THINKING: str
    THINKING_START: str
    THINKING_END: str

class NativeToolType(StrEnum):
    """Defines valid types for native tools."""
    CODE_INTERPRETER: str

class LMOutputType(StrEnum):
    """Defines valid types for language model outputs."""
    TEXT: str
    STRUCTURED: str
    ATTACHMENT: str
    TOOL_CALL: str
    THINKING: str
    CITATION: str
    CODE_EXEC_RESULT: str
    MCP_CALL: str

class OutputTransformerType(StrEnum):
    """Defines valid types for output transformers."""
    IDENTITY: str
    JSON: str
    THINK_TAG: str

class OperationType(StrEnum):
    """Defines valid operation types."""
    BATCH: str
    DATA_STORE: str
    FILE: str

class ActivityType(StrEnum):
    """Defines valid activity types."""
    FIND_IN_PAGE: str
    MCP_CALL: str
    MCP_LIST_TOOLS: str
    OPEN_PAGE: str
    SEARCH: str
    WEB_SEARCH: str

class MessageRole(StrEnum):
    """Defines valid message roles."""
    SYSTEM: str
    USER: str
    ASSISTANT: str

class VectorFuserType(StrEnum):
    """Defines valid types for vector fusers."""
    SUM: str

class TruncateSide(StrEnum):
    """Enumeration for truncation sides."""
    RIGHT: str
    LEFT: str

class JinjaEnvType(StrEnum):
    """Enumeration for Jinja environment types."""
    JINJA_DEFAULT: str
    RESTRICTED: str

class WebSearchKey(StrEnum):
    """Defines valid web search keys."""
    PATTERN: str
    QUERY: str
    SOURCES: str
    TYPE: str
    URL: str
