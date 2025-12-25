from enum import StrEnum

class Key:
    """Defines valid keys in OpenAI Chat Completions."""
    API_KEY: str
    ARGUMENTS: str
    BASE_URL: str
    CONTENT: str
    CHOICES: str
    DATA: str
    DEFS: str
    DESCRIPTION: str
    EFFORT: str
    FILE: str
    FILE_DATA: str
    FILENAME: str
    FINISH_REASON: str
    FORMAT: str
    FUNCTION: str
    ID: str
    IMAGE_URL: str
    INPUT_AUDIO: str
    JSON_SCHEMA: str
    MAX_RETRIES: str
    MESSAGE: str
    NAME: str
    PARAMETERS: str
    REFUSAL: str
    RESPONSE_FORMAT: str
    ROLE: str
    SCHEMA: str
    STRICT: str
    TEXT: str
    TIMEOUT: str
    TITLE: str
    TOOLS: str
    TOOL_CALLS: str
    TOOL_CALL_ID: str
    TYPE: str
    URL: str
    USAGE: str
    REASONING: str
    REASONING_CONTENT: str
    REASONING_EFFORT: str
    SUMMARY: str

class InputType:
    """Defines valid input types in OpenAI Chat Completions."""
    FILE: str
    FUNCTION: str
    IMAGE_URL: str
    INPUT_AUDIO: str
    JSON_SCHEMA: str
    TEXT: str
    TOOL: str
    REASONING: str
    SUMMARY_TEXT: str

class ReasoningEffort(StrEnum):
    """Defines the reasoning effort for reasoning models."""
    HIGH: str
    MEDIUM: str
    LOW: str
