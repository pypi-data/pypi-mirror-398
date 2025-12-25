from gllm_inference.realtime_chat.output_streamer.output_streamer import DEPRECATION_MESSAGE as DEPRECATION_MESSAGE
from gllm_inference.realtime_session.output_streamer import ConsoleOutputStreamer as _ConsoleOutputStreamer

class ConsoleOutputStreamer(_ConsoleOutputStreamer):
    """[BETA] A console output streamer that prints the output to the console.

    Attributes:
        state (BaseModel): The state of the output streamer.
    """
    def __init__(self) -> None:
        """Initializes a new instance of the ConsoleOutputStreamer class."""
