from gllm_inference.realtime_session.output_streamer.output_streamer import BaseOutputStreamer as BaseOutputStreamer
from typing import Any

USER_HEADER: str
ASSISTANT_HEADER: str
FOOTER: str

class ConsoleOutputStreamer(BaseOutputStreamer):
    """[BETA] A console output streamer that prints the output to the console.

    Attributes:
        state (BaseModel): The state of the output streamer.
    """
    async def handle(self, data: dict[str, Any]) -> None:
        """Handles the output events.

        This method is used to handle the text output events and print them to the console.

        Args:
            data (dict[str, Any]): The output events.
        """
