import asyncio
from _typeshed import Incomplete
from gllm_inference.realtime_session.input_streamer.input_streamer import BaseInputStreamer as BaseInputStreamer

DEFAULT_QUIT_CMD: str

class KeyboardInputStreamer(BaseInputStreamer):
    """[BETA] A keyboard input streamer that reads the input text from the keyboard.

    Attributes:
        state (BaseModel): The state of the input streamer.
        input_queue (asyncio.Queue): The queue to put the input events.
        quit_cmd (str): The command to quit the conversation.
    """
    record_process: asyncio.subprocess.Process | None
    quit_cmd: Incomplete
    def __init__(self, quit_cmd: str = ...) -> None:
        """Initializes the KeyboardInputStreamer.

        Args:
            quit_cmd (str, optional): The command to quit the conversation. Defaults to DEFAULT_QUIT_CMD.
        """
    async def stream_input(self) -> None:
        """Streams the input from the keyboard.

        This method is used to stream the input text from the keyboard to the input queue.
        """
