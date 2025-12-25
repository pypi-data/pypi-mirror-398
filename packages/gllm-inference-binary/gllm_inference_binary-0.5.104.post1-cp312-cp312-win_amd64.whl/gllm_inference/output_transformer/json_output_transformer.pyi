from gllm_inference.output_transformer.identity_output_transformer import IdentityOutputTransformer as IdentityOutputTransformer
from gllm_inference.schema.lm_output import LMOutputItem as LMOutputItem, LMOutputType as LMOutputType

class JSONOutputTransformer(IdentityOutputTransformer):
    '''An output transformer that parses the JSON string in the language model output into a Python dictionary.

    This output transformer is useful to parse a structured output from the output of a language model that doesn\'t
    support structured output natively. It only supports parsing a single JSON object from the text output.
    Text outputs that contain multiple JSON objects will be returned as the original text output.

    This output transformer will not perform any transformation for streaming events.

    Attributes:
        event_emitter (EventEmitter | None): The event emitter to use for streaming events.

    Examples:
        LMOutput transformation:
            Input:
            ```python
            LMOutput(outputs=[
                LMOutputItem(type="text", output=\'Here is the output: {"key": "value"}\'),
            ])
            ```

            Output:
            ```python
            LMOutput(outputs=[
                LMOutputItem(type="structured", output={"key": "value"}),
            ])
            ```
    '''
