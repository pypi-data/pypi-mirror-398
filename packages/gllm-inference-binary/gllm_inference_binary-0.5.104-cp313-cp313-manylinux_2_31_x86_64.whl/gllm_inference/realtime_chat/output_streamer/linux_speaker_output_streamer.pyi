from gllm_inference.realtime_chat.output_streamer.output_streamer import DEPRECATION_MESSAGE as DEPRECATION_MESSAGE
from gllm_inference.realtime_session.output_streamer import LinuxSpeakerOutputStreamer as _LinuxSpeakerOutputStreamer

class LinuxSpeakerOutputStreamer(_LinuxSpeakerOutputStreamer):
    """[BETA] A Linux speaker output streamer that plays the output audio through the speakers.

    Attributes:
        state (BaseModel): The state of the output streamer.
        play_process (asyncio.subprocess.Process | None): The process to play the output audio.
    """
    def __init__(self) -> None:
        """Initializes a new instance of the LinuxSpeakerOutputStreamer class."""
