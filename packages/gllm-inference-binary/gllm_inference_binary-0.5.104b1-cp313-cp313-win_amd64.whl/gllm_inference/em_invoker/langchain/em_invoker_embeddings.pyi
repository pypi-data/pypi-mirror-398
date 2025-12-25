from gllm_inference.em_invoker.em_invoker import BaseEMInvoker as BaseEMInvoker
from gllm_inference.schema import Attachment as Attachment, Vector as Vector
from gllm_inference.utils.io_utils import DEFAULT_BASE64_ALLOWED_MIMETYPES as DEFAULT_BASE64_ALLOWED_MIMETYPES, base64_to_bytes as base64_to_bytes
from langchain_core.embeddings import Embeddings
from pydantic import BaseModel
from typing import Any

class EMInvokerEmbeddings(BaseModel, Embeddings, arbitrary_types_allowed=True):
    '''An adapter class that enables an `EMInvoker` to be used as a LangChain `Embeddings`.

    Attributes:
        em_invoker (BaseEMInvoker): The `EMInvoker` instance to be interacted with.
        use_base64 (bool):
            Whether to apply strict base64 encoding to the input.
            1, If `True`, only inputs with specific MIME types (e.g. images,
              audio, and video) will be converted into base64 strings before being sent.
            2. If `False`, each input is treated as a raw string.

            This ensures "strict" handling: base64 encoding is not applied
            universally, but only when required for those MIME types.

    Usage example:
    ```python
    from gllm_inference.em_invoker.langchain import EMInvokerEmbeddings
    from gllm_inference.em_invoker import OpenAIEMInvoker

    em_invoker = OpenAIEMInvoker(...)
    embeddings = EMInvokerEmbeddings(em_invoker=em_invoker)
    ```
    '''
    em_invoker: BaseEMInvoker
    use_base64: bool
    async def aembed_documents(self, texts: list[str], **kwargs: Any) -> list[Vector]:
        """Asynchronously embed documents using the `EMInvoker`.

        Args:
            texts (list[str]): The list of texts to embed.
            **kwargs (Any): Additional keyword arguments to pass to the EMInvoker's `invoke` method.

        Returns:
            list[Vector]: List of embeddings, one for each text.

        Raises:
            ValueError: If `texts` is not a list of strings.
        """
    async def aembed_query(self, text: str, **kwargs: Any) -> Vector:
        """Asynchronously embed query using the `EMInvoker`.

        Args:
            text (str): The text to embed.
            **kwargs (Any): Additional keyword arguments to pass to the EMInvoker's `invoke` method.

        Returns:
            Vector: Embeddings for the text.

        Raises:
            ValueError: If `text` is not a string.
        """
    def embed_documents(self, texts: list[str], **kwargs: Any) -> list[Vector]:
        """Embed documents using the `EMInvoker`.

        Args:
            texts (list[str]): The list of texts to embed.
            **kwargs (Any): Additional keyword arguments to pass to the EMInvoker's `invoke` method.

        Returns:
            list[Vector]: List of embeddings, one for each text.

        Raises:
            ValueError: If `texts` is not a list of strings.
        """
    def embed_query(self, text: str, **kwargs: Any) -> Vector:
        """Embed query using the `EMInvoker`.

        Args:
            text (str): The text to embed.
            **kwargs (Any): Additional keyword arguments to pass to the EMInvoker's `invoke` method.

        Returns:
            Vector: Embeddings for the text.

        Raises:
            ValueError: If `text` is not a string.
        """
