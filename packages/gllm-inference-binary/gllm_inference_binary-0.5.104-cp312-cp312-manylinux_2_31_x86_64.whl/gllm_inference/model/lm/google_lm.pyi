class GoogleLM:
    '''Defines Google language model names constants.

    Usage example:
    ```python
    from gllm_inference.model import GoogleLM
    from gllm_inference.lm_invoker import GoogleLMInvoker

    lm_invoker = GoogleLMInvoker(GoogleLM.GEMINI_2_5_FLASH)
    response = await lm_invoker.invoke("Hello, world!")
    ```
    '''
    GEMINI_3_PRO: str
    GEMINI_3_PRO_IMAGE: str
    GEMINI_2_5_PRO: str
    GEMINI_2_5_FLASH: str
    GEMINI_2_5_FLASH_IMAGE: str
    GEMINI_2_5_FLASH_LITE: str
    GEMINI_2_0_FLASH: str
    GEMINI_2_0_FLASH_LITE: str
