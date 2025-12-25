from enum import StrEnum

class Key:
    """Defines valid keys in OpenAI."""
    ALLOWED_TOOLS: str
    API_KEY: str
    ARGS: str
    ARGUMENTS: str
    BASE_URL: str
    BODY: str
    CALL_ID: str
    CONTAINER: str
    CONTENT: str
    CUSTOM_ID: str
    DEFAULT: str
    DEFS: str
    DESCRIPTION: str
    EFFORT: str
    FILE_DATA: str
    FILENAME: str
    FORMAT: str
    ID: str
    IMAGE_GENERATION_CALL: str
    IMAGE_URL: str
    INCLUDE: str
    INCOMPLETE_DETAILS: str
    INPUT: str
    INSTRUCTIONS: str
    JSON_SCHEMA: str
    MAX_RETRIES: str
    METHOD: str
    METHOD_POST: str
    MODEL: str
    NAME: str
    OUTPUT: str
    OUTPUTS: str
    PARAMETERS: str
    REASON: str
    REASONING: str
    REFUSAL: str
    ROLE: str
    SCHEMA: str
    REQUIRE_APPROVAL: str
    REQUIRED: str
    SERVER_LABEL: str
    SERVER_NAME: str
    SERVER_URL: str
    STATUS: str
    STRICT: str
    SUMMARY: str
    TEXT: str
    TIMEOUT: str
    TITLE: str
    TOOL_NAME: str
    TOOLS: str
    TYPE: str
    URL: str
    USAGE: str

class InputType:
    """Defines valid input types in OpenAI."""
    AUTO: str
    CODE_INTERPRETER: str
    CODE_INTERPRETER_CALL_OUTPUTS: str
    FUNCTION: str
    FUNCTION_CALL: str
    FUNCTION_CALL_OUTPUT: str
    IMAGE_GENERATION: str
    INPUT_FILE: str
    INPUT_IMAGE: str
    INPUT_TEXT: str
    JSON_SCHEMA: str
    MCP: str
    MCP_CALL: str
    NEVER: str
    NULL: str
    OUTPUT_TEXT: str
    REASONING: str
    SUMMARY_TEXT: str
    WEB_SEARCH_PREVIEW: str

class OutputType:
    """Defines valid output types in OpenAI."""
    CODE_INTERPRETER_CALL: str
    CODE_INTERPRETER_CALL_DELTA: str
    CODE_INTERPRETER_CALL_DONE: str
    CODE_INTERPRETER_CALL_IN_PROGRESS: str
    COMPLETED: str
    CONTAINER_FILE_CITATION: str
    FIND_IN_PAGE: str
    FUNCTION_CALL: str
    IMAGE: str
    IMAGE_GENERATION_CALL: str
    INCOMPLETE: str
    ITEM_DONE: str
    MCP_CALL: str
    MCP_LIST_TOOLS: str
    MESSAGE: str
    OPEN_PAGE: str
    REASONING: str
    REASONING_ADDED: str
    REASONING_DELTA: str
    REASONING_DONE: str
    REFUSAL: str
    SEARCH: str
    TEXT_DELTA: str
    WEB_SEARCH_CALL: str

class OpenAIBatchStatus:
    """Defines valid batch statuses in OpenAI."""
    CANCELLED: str
    CANCELLING: str
    COMPLETED: str
    EXPIRED: str
    FAILED: str
    FINALIZING: str
    IN_PROGRESS: str
    VALIDATING: str

class ReasoningEffort(StrEnum):
    """Defines the reasoning effort for reasoning models."""
    HIGH: str
    MEDIUM: str
    LOW: str
    MINIMAL: str

class ReasoningSummary(StrEnum):
    """Defines the reasoning summary for reasoning models."""
    AUTO: str
    DETAILED: str
