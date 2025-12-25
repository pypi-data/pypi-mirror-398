class XAILM:
    '''Defines XAI language model names constants.

    Usage example:
    ```python
    from gllm_inference.model import XAILM
    from gllm_inference.lm_invoker import XAILMInvoker

    lm_invoker = XAILMInvoker(XAILM.GROK_4_FAST_REASONING)
    response = await lm_invoker.invoke("Hello, world!")
    ```
    '''
    GROK_4_1: str
    GROK_4_1_THINKING: str
    GROK_CODE_FAST_1: str
    GROK_4_FAST_REASONING: str
    GROK_4_FAST_NON_REASONING: str
    GROK_4_0709: str
    GROK_3_MINI: str
    GROK_3: str
    GROK_2_VISION_1212: str
