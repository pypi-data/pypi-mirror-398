from gllm_core.event import EventEmitter
from gllm_inference.output_transformer.output_transformer import BaseOutputTransformer as BaseOutputTransformer
from gllm_inference.schema import LMOutputItem as LMOutputItem, LMOutputType as LMOutputType, Reasoning as Reasoning, ThinkingEvent as ThinkingEvent

class ThinkTag:
    """Defines special thinking tags constants."""
    PREFIX: str
    SUFFIX: str

class ThinkTagOutputTransformer(BaseOutputTransformer):
    '''An output transformer that handles special thinking tags used in certain open source language models.

    Some open source language models, such as `Qwen3-30B-A3B`, emits their thinking tokens as part of the text tokens,
    These thinking tokens are wrapped in special XML-like thinking tags to indicate the start and end of thinking.
    This transformer detects and separates these thinking tags from the text output to handle the thinking properly.

    Attributes:
        event_emitter (EventEmitter | None): The event emitter to use for streaming events.
        thinking (bool): Whether the transformer is currently in thinking mode.
        thinking_id (str): The ID of the current thinking.

    Examples:
        LMOutput transformation:
            Input:
            ```python
            LMOutput(outputs=[
                LMOutputItem(type="text", output="<think>I\'m thinking...</think>I\'m responding..."),
            ])
            ```

            Output:
            ```python
            LMOutput(outputs=[
                LMOutputItem(type="thinking", output=Reasoning(reasoning="I\'m thinking...")),
                LMOutputItem(type="text", output="I\'m responding..."),
            ])
            ```

        Streaming event transformation:
            Input:
            ```python
            Event(id=None, type="response", value="<think>")
            Event(id=None, type="response", value="I\'m thinking...")
            Event(id=None, type="response", value="leading text</think>trailing text")
            Event(id=None, type="response", value="I\'m responding...")
            ```

            Output:
            ```python
            Event(id=None, type="thinking_start", value="<think>")
            Event(id=None, type="thinking", value="I\'m thinking...")
            Event(id=None, type="thinking", value="leading text")
            Event(id=None, type="thinking_end", value="</think>")
            Event(id=None, type="response", value="trailing text")
            Event(id=None, type="response", value="I\'m responding...")
            ```
    '''
    thinking_id: str
    thinking: bool
    def __init__(self, event_emitter: EventEmitter | None = None) -> None:
        """Initializes a new instance of the ThinkTagOutputTransformer class.

        Args:
            event_emitter (EventEmitter | None, optional): The event emitter to use for streaming events.
                Defaults to None.
        """
