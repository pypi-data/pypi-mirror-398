from _typeshed import Incomplete
from gllm_inference.realtime_chat.input_streamer.input_streamer import DEPRECATION_MESSAGE as DEPRECATION_MESSAGE
from gllm_inference.realtime_session.input_streamer import LinuxMicInputStreamer as _LinuxMicInputStreamer

SEND_SAMPLE_RATE: int
CHANNELS: int
RECORD_CMD: Incomplete
CHUNK_DURATION: float
CHUNK_SIZE: Incomplete

class LinuxMicInputStreamer(_LinuxMicInputStreamer):
    """[BETA] A Linux microphone input streamer that reads the input audio from the microphone.

    Attributes:
        state (BaseModel): The state of the input streamer.
        input_queue (asyncio.Queue): The queue to put the input events.
        record_process (asyncio.subprocess.Process | None): The process to record the input audio.
    """
    def __init__(self) -> None:
        """Initializes the LinuxMicInputStreamer."""
