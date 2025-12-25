import asyncio
from _typeshed import Incomplete
from gllm_inference.realtime_session.input_streamer.input_streamer import BaseInputStreamer as BaseInputStreamer

SEND_SAMPLE_RATE: int
CHANNELS: int
RECORD_CMD: Incomplete
CHUNK_DURATION: float
CHUNK_SIZE: Incomplete

class LinuxMicInputStreamer(BaseInputStreamer):
    """[BETA] A Linux microphone input streamer that reads the input audio from the microphone.

    Attributes:
        state (BaseModel): The state of the input streamer.
        input_queue (asyncio.Queue): The queue to put the input events.
        record_process (asyncio.subprocess.Process | None): The process to record the input audio.
    """
    record_process: asyncio.subprocess.Process | None
    def __init__(self) -> None:
        """Initializes the LinuxMicInputStreamer.

        Raises:
            OSError: If the current system is not Linux.
        """
    async def stream_input(self) -> None:
        """Streams the input audio from the Linux system microphone.

        This method is used to stream the recorded input audio from the Linux system microphone to the input queue.
        """
    async def close(self) -> None:
        """Closes the LinuxMicInputStreamer.

        This method is used to close the LinuxMicInputStreamer.
        It is used to clean up the recording process.
        """
