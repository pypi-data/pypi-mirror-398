class Key:
    """Defines valid keys in Google."""
    ARGS: str
    CONTENT: str
    FILE_SEARCH: str
    FINISH_MESSAGE: str
    FINISH_REASON: str
    FUNCTION: str
    FUNCTION_CALL: str
    FUNCTION_DECLARATIONS: str
    HTTP_OPTIONS: str
    ID: str
    NAME: str
    RETRY_OPTIONS: str
    STATUS: str
    SYSTEM_INSTRUCTION: str
    TEXT: str
    THINKING_CONFIG: str
    TIMEOUT: str
    TOOLS: str
    RESPONSE_SCHEMA: str
    RESPONSE_MIME_TYPE: str
    URI: str
    VERTEXAI: str
    CUSTOM_REQUEST_IDS: str

class InputType:
    """Defines valid input types in Google."""
    APPLICATION_JSON: str
    MODEL: str
    USER: str

class JobState:
    """Defines valid output types in Google."""
    CANCELLED: str
    EXPIRED: str
    FAILED: str
    PENDING: str
    RUNNING: str
    SUCCEEDED: str
