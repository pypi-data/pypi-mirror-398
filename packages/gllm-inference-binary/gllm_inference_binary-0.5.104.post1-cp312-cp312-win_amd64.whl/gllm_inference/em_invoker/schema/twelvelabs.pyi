class Key:
    """Defines valid keys in TwelveLabs."""
    INPUT_KEY: str
    MAX_RETRIES: str
    OUTPUT_KEY: str
    TIMEOUT: str
    VALUE: str
    SEGMENTS: str

class InputType:
    """Defines valid input types in TwelveLabs."""
    FILE_SUFFIX: str
    TEXT: str

class OutputType:
    """Defines valid output types in TwelveLabs."""
    EMBEDDING_SUFFIX: str
    TEXT_EMBEDDING: str

class TaskStatus:
    """Enum for task status."""
    READY: str
    FAILED: str

class VideoEmbeddingOption:
    """Defines the types of content that can be embedded from a video."""
    AUDIO: str
    TRANSCRIPTION: str
    VISUAL: str

class VideoEmbeddingScope:
    """Defines the scope of video embeddings."""
    CLIP: str
    VIDEO: str

class VideoEmbeddingParams:
    """String enum for TwelveLabs video-related hyperparameter keys."""
    VIDEO_EMBED_CREATE_PARAMS: str
    VIDEO_EMBED_RETRIEVE_PARAMS: str
    VIDEO_EMBEDDING_OPTIONS: str
    WAIT_FOR_DONE_PARAMS: str
