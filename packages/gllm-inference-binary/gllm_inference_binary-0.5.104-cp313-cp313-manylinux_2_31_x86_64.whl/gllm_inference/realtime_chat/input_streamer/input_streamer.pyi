from abc import ABC
from gllm_inference.realtime_session.input_streamer.input_streamer import BaseInputStreamer as _BaseInputStreamer

DEPRECATION_MESSAGE: str

class BaseInputStreamer(_BaseInputStreamer, ABC):
    """[BETA] A base class for input streamers.

    Attributes:
        state (BaseModel | None): The state of the input streamer.
        input_queue (asyncio.Queue | None): The queue to put the input events.
    """
    def __init__(self) -> None:
        """Initializes a new instance of the BaseInputStreamer class."""
