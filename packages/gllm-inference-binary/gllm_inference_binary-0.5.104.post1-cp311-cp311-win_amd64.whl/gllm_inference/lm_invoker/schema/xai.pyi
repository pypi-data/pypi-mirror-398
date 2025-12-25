from enum import StrEnum

class Key:
    """Defines valid keys in xAI."""
    ARGUMENTS: str
    CHANNEL_OPTIONS: str
    CITATIONS: str
    COMPLETION_TOKENS: str
    CONTENT: str
    FINISH_REASON: str
    FUNCTION: str
    ID: str
    IMAGE_FORMAT: str
    NAME: str
    ON: str
    PROMPT_TOKENS: str
    REASONING_CONTENT: str
    REASONING_EFFORT: str
    RESPONSE_FORMAT: str
    SEARCH_PARAMETERS: str
    TEXT: str
    TIMEOUT: str
    TOOL_CALLS: str
    TOOLS: str
    TYPE: str
    URL: str
    URL_CITATION: str
    USAGE: str

class ReasoningEffort(StrEnum):
    """Defines the reasoning effort for reasoning models."""
    HIGH: str
    LOW: str
