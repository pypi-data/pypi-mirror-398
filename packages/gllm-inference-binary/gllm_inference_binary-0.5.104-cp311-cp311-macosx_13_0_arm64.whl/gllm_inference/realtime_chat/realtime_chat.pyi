from abc import ABC
from gllm_inference.realtime_session.realtime_session import BaseRealtimeSession as BaseRealtimeSession

DEPRECATION_MESSAGE: str

class BaseRealtimeChat(BaseRealtimeSession, ABC):
    """[BETA] A base class for realtime chat modules.

    The `BaseRealtimeChat` class provides a framework for processing real-time conversations.
    """
    def __init__(self) -> None:
        """Initializes a new instance of the BaseRealtimeChat class."""
