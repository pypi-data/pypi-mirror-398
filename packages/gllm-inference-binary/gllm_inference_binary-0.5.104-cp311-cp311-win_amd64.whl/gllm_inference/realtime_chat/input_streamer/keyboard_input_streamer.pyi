from gllm_inference.realtime_chat.input_streamer.input_streamer import DEPRECATION_MESSAGE as DEPRECATION_MESSAGE
from gllm_inference.realtime_session.input_streamer import KeyboardInputStreamer as _KeyboardInputStreamer

DEFAULT_QUIT_CMD: str

class KeyboardInputStreamer(_KeyboardInputStreamer):
    """[BETA] A keyboard input streamer that reads the input text from the keyboard.

    Attributes:
        state (BaseModel): The state of the input streamer.
        input_queue (asyncio.Queue): The queue to put the input events.
        quit_cmd (str): The command to quit the conversation.
    """
    def __init__(self, quit_cmd: str = ...) -> None:
        """Initializes a new instance of the KeyboardInputStreamer class.

        Args:
            quit_cmd (str, optional): The command to quit the conversation. Defaults to DEFAULT_QUIT_CMD.
        """
