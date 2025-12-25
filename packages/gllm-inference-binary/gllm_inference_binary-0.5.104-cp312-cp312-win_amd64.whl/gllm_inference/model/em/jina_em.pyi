class JinaEM:
    '''Defines Jina embedding model names constants.

    Usage example:
    ```python
    from gllm_inference.model import JinaEM
    from gllm_inference.em_invoker import JinaEMInvoker

    em_invoker = JinaEMInvoker(JinaEM.JINA_EMBEDDINGS_V4)
    result = await em_invoker.invoke("Hello, world!")
    ```
    '''
    JINA_EMBEDDINGS_V4: str
    JINA_EMBEDDINGS_V3: str
    JINA_EMBEDDINGS_V2_BASE_EN: str
    JINA_EMBEDDINGS_V2_BASE_CODE: str
    JINA_CLIP_V2: str
    JINA_CLIP_V1: str
    JINA_CODE_EMBEDDINGS_1_5B: str
    JINA_CODE_EMBEDDINGS_0_5B: str
    JINA_COLBERT_V2: str
    JINA_COLBERT_V1_EN: str
