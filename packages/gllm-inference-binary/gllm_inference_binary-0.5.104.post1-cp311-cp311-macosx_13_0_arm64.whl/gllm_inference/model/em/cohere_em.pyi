class CohereEM:
    '''Defines Cohere embedding model names constants.

    Usage example:
    ```python
    from gllm_inference.model import CohereEM
    from gllm_inference.em_invoker import CohereEMInvoker

    em_invoker = CohereEMInvoker(CohereEM.EMBED_V4_0)
    result = await em_invoker.invoke("Hello, world!")
    ```
    '''
    EMBED_V4_0: str
    EMBED_ENGLISH_V3_0: str
    EMBED_ENGLISH_LIGHT_V3_0: str
    EMBED_MULTILINGUAL_V3_0: str
    EMBED_MULTILINGUAL_LIGHT_V3_0: str
