from _typeshed import Incomplete
from gllm_core.event import EventEmitter
from gllm_inference.output_transformer.identity_output_transformer import IdentityOutputTransformer as IdentityOutputTransformer
from gllm_inference.output_transformer.json_output_transformer import JSONOutputTransformer as JSONOutputTransformer
from gllm_inference.output_transformer.output_transformer import BaseOutputTransformer as BaseOutputTransformer
from gllm_inference.output_transformer.think_tag_output_transformer import ThinkTagOutputTransformer as ThinkTagOutputTransformer
from gllm_inference.schema.enums import OutputTransformerType as OutputTransformerType
from typing import Any

OUTPUT_TRANSFORMER_TYPE_MAP: Incomplete

def build_output_transformer(type: OutputTransformerType, event_emitter: EventEmitter | None = None, **kwargs: Any) -> BaseOutputTransformer:
    """Build an output transformer based on the provided configurations.

    Examples:
        # Using identity output transformer
        ```python
        output_transformer = build_output_transformer(OutputTransformerType.IDENTITY)
        ```

        # Using JSON output transformer
        ```python
        output_transformer = build_output_transformer(OutputTransformerType.JSON)
        ```

        # Using think tag output transformer
        ```python
        output_transformer = build_output_transformer(OutputTransformerType.THINK_TAG)
        ```

    Args:
        type (OutputTransformerType): The type of output transformer to use.
        event_emitter (EventEmitter | None, optional): The event emitter to use for streaming events. Defaults to None.
        **kwargs (Any): Additional keyword arguments to pass to the output transformer constructor.

    Returns:
        BaseOutputTransformer: The initialized output transformer.

    Raises:
        ValueError: If the provided type is not supported.
    """
