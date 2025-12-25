class SeaLionLM:
    '''Defines SEA-LION language model names constants.

    Usage example:
    ```python
    from gllm_inference.model import SeaLionLM
    from gllm_inference.lm_invoker import SeaLionLMInvoker

    lm_invoker = SeaLionLMInvoker(SeaLionLM.GEMMA_SEA_LION_V4_27B_IT)
    response = await lm_invoker.invoke("Hello, world!")
    ```
    '''
    GEMMA_SEA_LION_V4_27B_IT: str
    LLAMA_SEA_LION_V3_5_70B_R: str
    LLAMA_SEA_LION_V3_70B_IT: str
    QWEN_SEA_LION_V4_32B_IT: str
