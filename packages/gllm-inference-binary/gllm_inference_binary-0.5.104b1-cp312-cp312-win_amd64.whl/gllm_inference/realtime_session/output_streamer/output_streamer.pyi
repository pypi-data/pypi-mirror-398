from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Any

class BaseOutputStreamer(ABC):
    """[BETA] A base class for output streamers.

    Attributes:
        state (BaseModel | None): The state of the output streamer.
    """
    state: BaseModel | None
    async def initialize(self, state: BaseModel) -> None:
        """Initializes the output streamer.

        Args:
            state (BaseModel): The state of the output streamer.
        """
    @abstractmethod
    async def handle(self, data: dict[str, Any]) -> None:
        """Handles output events streamed from the model.

        This method must be implemented by subclasses to define the logic for handling the output events.

        Raises:
            NotImplementedError: If the method is not implemented in a subclass.
        """
    async def close(self) -> None:
        """Closes the output streamer.

        This method is used to close the output streamer.
        It is used to clean up the output streamer.
        """
