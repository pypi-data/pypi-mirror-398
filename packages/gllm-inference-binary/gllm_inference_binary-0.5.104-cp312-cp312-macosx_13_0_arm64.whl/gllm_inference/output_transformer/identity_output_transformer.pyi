from gllm_inference.output_transformer.output_transformer import BaseOutputTransformer as BaseOutputTransformer
from gllm_inference.schema.lm_output import LMOutputItem as LMOutputItem

class IdentityOutputTransformer(BaseOutputTransformer):
    """An output transformer that transforms the output of a language model into an identity function.

    This transformer simply returns the output and stream events of the language model as is.
    """
