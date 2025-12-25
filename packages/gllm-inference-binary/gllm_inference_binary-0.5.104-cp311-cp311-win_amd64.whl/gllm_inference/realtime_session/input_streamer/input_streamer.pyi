import asyncio
from abc import ABC, abstractmethod
from pydantic import BaseModel

class BaseInputStreamer(ABC):
    """[BETA] A base class for input streamers.

    Attributes:
        state (BaseModel | None): The state of the input streamer.
        input_queue (asyncio.Queue | None): The queue to put the input events.
    """
    state: BaseModel | None
    input_queue: asyncio.Queue | None
    async def initialize(self, state: BaseModel, input_queue: asyncio.Queue) -> None:
        """Initializes the input streamer.

        Args:
            input_queue (asyncio.Queue): The queue to put the input events.
            state (BaseModel): The state of the input streamer.
        """
    @abstractmethod
    async def stream_input(self) -> None:
        """Streams the input from a certain source.

        This method must be implemented by subclasses to define the logic for streaming the input.

        Raises:
            NotImplementedError: If the method is not implemented in a subclass.
        """
    async def close(self) -> None:
        """Closes the input streamer.

        This method is used to close the input streamer.
        It is used to clean up the input streamer.
        """
