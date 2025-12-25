from enum import StrEnum

class Key(StrEnum):
    """Defines valid keys in Cohere."""
    BASE_URL: str
    IMAGE_URL: str
    INPUT_TYPE: str
    MAX_RETRIES: str
    MODEL: str
    TIMEOUT: str
    TYPE: str
    URL: str

class CohereInputType(StrEnum):
    """Defines valid embedding input types for Cohere embedding API."""
    CLASSIFICATION: str
    CLUSTERING: str
    IMAGE: str
    SEARCH_DOCUMENT: str
    SEARCH_QUERY: str
