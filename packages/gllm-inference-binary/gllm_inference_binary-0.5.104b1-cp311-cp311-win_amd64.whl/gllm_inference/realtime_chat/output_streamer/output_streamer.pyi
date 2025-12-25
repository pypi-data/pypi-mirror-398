from abc import ABC
from gllm_inference.realtime_session.output_streamer.output_streamer import BaseOutputStreamer as _BaseOutputStreamer

DEPRECATION_MESSAGE: str

class BaseOutputStreamer(_BaseOutputStreamer, ABC):
    """[BETA] A base class for output streamers.

    Attributes:
        state (BaseModel | None): The state of the output streamer.
    """
    def __init__(self) -> None:
        """Initializes a new instance of the BaseOutputStreamer class."""
