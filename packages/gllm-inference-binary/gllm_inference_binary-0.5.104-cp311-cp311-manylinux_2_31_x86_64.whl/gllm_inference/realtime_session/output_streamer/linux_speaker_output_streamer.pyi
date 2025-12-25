import asyncio
from _typeshed import Incomplete
from gllm_inference.realtime_session.output_streamer.output_streamer import BaseOutputStreamer as BaseOutputStreamer
from pydantic import BaseModel
from typing import Any

PLAY_AUDIO_SAMPLE_RATE: int
CHANNELS: int
PLAY_CMD: Incomplete
OUTPUT_AUDIO_DELAY: float

class LinuxSpeakerOutputStreamer(BaseOutputStreamer):
    """[BETA] A Linux speaker output streamer that plays the output audio through the speakers.

    Attributes:
        state (BaseModel): The state of the output streamer.
        play_process (asyncio.subprocess.Process | None): The process to play the output audio.
    """
    play_process: asyncio.subprocess.Process | None
    async def initialize(self, state: BaseModel) -> None:
        """Initializes the LinuxSpeakerOutputStreamer.

        Args:
            state (BaseModel): The state of the output streamer.

        Raises:
            OSError: If the current system is not Linux.
        """
    async def handle(self, data: dict[str, Any]) -> None:
        """Handles the output events.

        This method is used to handle the audio output events and play them through the Linux system speakers.

        Args:
            data (dict[str, Any]): The output events.
        """
    async def close(self) -> None:
        """Closes the LinuxSpeakerOutputStreamer.

        This method is used to close the LinuxSpeakerOutputStreamer.
        It is used to clean up playing process.
        """
