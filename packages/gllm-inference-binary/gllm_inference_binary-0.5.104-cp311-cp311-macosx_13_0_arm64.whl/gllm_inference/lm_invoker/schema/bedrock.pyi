class Key:
    """Defines valid keys in Bedrock."""
    BYTES: str
    CONTENT: str
    DELTA: str
    DESCRIPTION: str
    ERROR: str
    CODE: str
    FORMAT: str
    FUNCTION: str
    HTTP_STATUS_CODE: str
    INFERENCE_CONFIG: str
    INPUT: str
    INPUT_SCHEMA: str
    INPUT_TOKENS: str
    JSON: str
    MESSAGE: str
    NAME: str
    RESPONSE: str
    OUTPUT: str
    OUTPUT_TOKENS: str
    PARAMETERS: str
    RESPONSE_METADATA: str
    ROLE: str
    SOURCE: str
    START: str
    STOP_REASON: str
    STREAM: str
    SYSTEM: str
    TEXT: str
    TOOL: str
    TOOLS: str
    TOOL_CHOICE: str
    TOOL_CONFIG: str
    TOOL_SPEC: str
    TOOL_USE_ID: str
    USAGE: str

class InputType:
    """Defines valid input types in Bedrock."""
    TEXT: str
    TOOL_RESULT: str
    TOOL_USE: str

class OutputType:
    """Defines valid output types in Bedrock."""
    CONTENT_BLOCK_START: str
    CONTENT_BLOCK_DELTA: str
    CONTENT_BLOCK_STOP: str
    MESSAGE_STOP: str
    METADATA: str
    TEXT: str
    TOOL_USE: str
