from abc import ABC, abstractmethod
from gllm_inference.realtime_session.input_streamer.input_streamer import BaseInputStreamer as BaseInputStreamer
from gllm_inference.realtime_session.output_streamer.output_streamer import BaseOutputStreamer as BaseOutputStreamer

class BaseRealtimeSession(ABC):
    """[BETA] A base class for realtime session modules.

    The `BaseRealtimeSession` class provides a framework for processing real-time conversation sessions.
    """
    def __init__(self) -> None:
        """Initializes a new instance of the BaseRealtimeSession class."""
    @abstractmethod
    async def start(self, input_streamers: list[BaseInputStreamer] | None = None, output_streamers: list[BaseOutputStreamer] | None = None) -> None:
        """Starts the real-time conversation session using the provided input and output streamers.

        This abstract method must be implemented by subclasses to define the logic
        for starting the real-time conversation session.

        Args:
            input_streamers (list[BaseInputStreamer] | None, optional): The input streamers to use.
                Defaults to None.
            output_streamers (list[BaseOutputStreamer] | None, optional): The output streamers to use.
                Defaults to None.

        Raises:
            NotImplementedError: If the method is not implemented in a subclass.
        """
