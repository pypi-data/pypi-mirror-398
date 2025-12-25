from _typeshed import Incomplete
from gllm_core.constants import EventType
from gllm_core.schema import Event
from gllm_inference.schema.activity import Activity as Activity
from typing import Any, Literal, Self

CodeEventType: Incomplete
ThinkingEventType: Incomplete

class ActivityEvent(Event):
    """Event schema for model-triggered activities (e.g. web search, MCP call, etc.).

    Attributes:
        id (str): The ID of the activity event. Defaults to None.
        value (dict[str, Any]): The value of the activity event.
        level (EventLevel): The severity level of the activity event. Defaults to EventLevel.INFO.
        type (Literal[EventType.ACTIVITY]): The type of the activity event. Defaults to EventType.ACTIVITY.
        timestamp (datetime): The timestamp of the activity event. Defaults to the current timestamp.
        metadata (dict[str, Any]): The metadata of the activity event. Defaults to an empty dictionary.
    """
    value: dict[str, Any]
    type: Literal[EventType.ACTIVITY]
    @classmethod
    def from_activity(cls, id_: str | None = None, activity: Activity | None = None) -> ActivityEvent:
        """Create an activity event from an Activity object.

        Args:
            id_ (str | None, optional): The ID of the activity event. Defaults to None.
            activity (Activity | None, optional): The activity object to create the event from.
                Defaults to None, in which case the value will be an empty dictionary.

        Returns:
            ActivityEvent: The activity event.
        """

class BlockBasedEvent(Event):
    """Event schema block-based events, which are limited by start and end events.

    Attributes:
        id (str): The ID of the block-based event. Defaults to None.
        value (str): The value of the block-based event. Defaults to an empty string.
        level (EventLevel): The severity level of the block-based event. Defaults to EventLevel.INFO.
        type (str): The type of the block-based event. Defaults to an empty string.
        timestamp (datetime): The timestamp of the block-based event. Defaults to the current timestamp.
        metadata (dict[str, Any]): The metadata of the block-based event. Defaults to an empty dictionary.
    """
    value: str
    type: str
    @classmethod
    def start(cls, id_: str | None = None) -> Self:
        """Create a block-based start event.

        Args:
            id_ (str | None, optional): The ID of the block-based event. Defaults to None.

        Returns:
            Self: The block-based start event.
        """
    @classmethod
    def content(cls, id_: str | None = None, value: str = '') -> Self:
        """Create a block-based content event.

        Args:
            id_ (str | None, optional): The ID of the block-based event. Defaults to None.
            value (str, optional): The block-based content. Defaults to an empty string.

        Returns:
            Self: The block-based content event.
        """
    @classmethod
    def end(cls, id_: str | None = None) -> Self:
        """Create a block-based end event.

        Args:
            id_ (str | None, optional): The ID of the block-based event. Defaults to None.

        Returns:
            Self: The block-based end event.
        """

class CodeEvent(BlockBasedEvent):
    """Event schema for model-generated code to be executed.

    Attributes:
        id (str): The ID of the code event. Defaults to None.
        value (str): The value of the code event. Defaults to an empty string.
        level (EventLevel): The severity level of the code event. Defaults to EventLevel.INFO.
        type (CodeEventType): The type of the code event. Defaults to EventType.CODE.
        timestamp (datetime): The timestamp of the code event. Defaults to the current timestamp.
        metadata (dict[str, Any]): The metadata of the code event. Defaults to an empty dictionary.
    """
    type: CodeEventType

class ThinkingEvent(BlockBasedEvent):
    """Event schema for model-generated thinking.

    Attributes:
        id (str): The ID of the thinking event. Defaults to None.
        value (str): The value of the thinking event. Defaults to an empty string.
        level (EventLevel): The severity level of the thinking event. Defaults to EventLevel.INFO.
        type (ThinkingEventType): The type of the thinking event. Defaults to EventType.THINKING.
        timestamp (datetime): The timestamp of the thinking event. Defaults to the current timestamp.
        metadata (dict[str, Any]): The metadata of the thinking event. Defaults to an empty dictionary.
    """
    type: ThinkingEventType
