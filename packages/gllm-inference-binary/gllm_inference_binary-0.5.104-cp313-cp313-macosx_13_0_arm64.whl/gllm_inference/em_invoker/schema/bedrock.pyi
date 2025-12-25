class Key:
    """Defines valid keys in Bedrock."""
    ACCEPT: str
    BASE64_STRING: str
    CONTENT_TYPE: str
    HTTP_STATUS_CODE: str
    INPUT_TEXT: str
    INPUT_TYPE: str
    INPUT_TYPE_MARENGO: str
    MEDIA_SOURCE: str
    MODEL_ID: str
    RESPONSE_METADATA: str
    TEXT_TRUNCATE: str
    TEXTS: str

class InputType:
    """Defines valid input types in Bedrock."""
    APPLICATION_JSON: str
    IMAGE: str
    SEARCH_DOCUMENT: str
    SEARCH_QUERY: str
    TEXT: str

class OutputType:
    """Defines valid output types in Bedrock."""
    BODY: str
    DATA: str
    EMBEDDING: str
    EMBEDDINGS: str
