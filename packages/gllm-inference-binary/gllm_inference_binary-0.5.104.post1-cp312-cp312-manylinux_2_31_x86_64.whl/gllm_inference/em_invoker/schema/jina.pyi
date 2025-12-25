from enum import StrEnum

class Key(StrEnum):
    """Defines key constants used in the Jina AI API payloads."""
    DATA: str
    EMBEDDING: str
    EMBEDDINGS: str
    ERROR: str
    IMAGE: str
    INPUT: str
    JSON: str
    MESSAGE: str
    MODEL: str
    RESPONSE: str
    STATUS: str
    TASK: str
    TEXT: str

class OutputType(StrEnum):
    """Defines the expected output types returned by the Jina AI embedding API."""
    DATA: str
    EMBEDDING: str
