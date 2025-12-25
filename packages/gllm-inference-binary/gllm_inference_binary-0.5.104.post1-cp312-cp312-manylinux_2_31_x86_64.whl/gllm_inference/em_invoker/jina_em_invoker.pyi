from _typeshed import Incomplete
from gllm_core.utils.retry import RetryConfig
from gllm_inference.constants import EMBEDDING_ENDPOINT as EMBEDDING_ENDPOINT, JINA_DEFAULT_URL as JINA_DEFAULT_URL
from gllm_inference.em_invoker.em_invoker import BaseEMInvoker as BaseEMInvoker
from gllm_inference.em_invoker.schema.jina import Key as Key
from gllm_inference.em_invoker.vector_fuser.vector_fuser import BaseVectorFuser as BaseVectorFuser
from gllm_inference.exceptions import BaseInvokerError as BaseInvokerError, ProviderInternalError as ProviderInternalError
from gllm_inference.exceptions.error_parser import convert_to_base_invoker_error as convert_to_base_invoker_error
from gllm_inference.schema import Attachment as Attachment, AttachmentType as AttachmentType, EMContent as EMContent, ModelId as ModelId, ModelProvider as ModelProvider, TruncationConfig as TruncationConfig, Vector as Vector, VectorFuserType as VectorFuserType
from typing import Any

SUPPORTED_ATTACHMENTS: Incomplete
MULTIMODAL_MODELS: Incomplete

class JinaEMInvoker(BaseEMInvoker):
    '''An embedding model invoker to interact with Jina AI embedding models.

    Attributes:
        model_id (str): The model ID of the embedding model.
        model_provider (str): The provider of the embedding model.
        model_name (str): The name of the embedding model.
        client (AsyncClient): The client for the Jina AI API.
        default_hyperparameters (dict[str, Any]): Default hyperparameters for invoking the embedding model.
        retry_config (RetryConfig): The retry configuration for the embedding model.
        truncation_config (TruncationConfig | None): The truncation configuration for the embedding model.
        vector_fuser (BaseVectorFuser | None): The vector fuser to handle mixed content.

    Input types:
        The `JinaEMInvoker` supports the following input types: text and image.
        Non-text inputs must be passed as a `Attachment` object.

    Output format:
        The `JinaEMInvoker` can embed either:
        1. A single content.
           1. A single content is either a text or an image.
           2. The output will be a `Vector`, representing the embedding of the content.

           # Example 1: Embedding a text content.
           ```python
           text = "What animal is in this image?"
           result = await em_invoker.invoke(text)
           ```

           # Example 2: Embedding an image content.
           ```python
           image = Attachment.from_path("path/to/local/image.png")
           result = await em_invoker.invoke(image)
           ```

           The above examples will return a `Vector` with a size of (embedding_size,).

        2. A list of contents.
           1. A list of contents is a list that consists of any of the above single contents.
           2. The output will be a `list[Vector]`, where each element is a `Vector` representing the
              embedding of each single content.

           # Example: Embedding a list of contents.
           ```python
           text = "What animal is in this image?"
           image = Attachment.from_path("path/to/local/image.png")
           result = await em_invoker.invoke([text, image])
           ```

           The above examples will return a `list[Vector]` with a size of (2, embedding_size).

    Vector fusion:
        The `JinaEMInvoker` supports vector fusion, which allows fusing multiple results into a single vector.
        This feature allows the module to embed mixed modality contents, represented as tuples of contents.
        This feature can be enabled by providing a vector fuser to the `vector_fuser` parameter.

        Usage example:
        ```python
        em_invoker = JinaEMInvoker(..., vector_fuser=SumVectorFuser())  # Using a vector fuser class
        em_invoker = JinaEMInvoker(..., vector_fuser="sum")  # Using a vector fuser type

        text = "What animal is in this image?"
        image = Attachment.from_path("path/to/local/image.png")
        mix_content = (text, image)
        result = await em_invoker.invoke([text, image, mix_content])
        ```

        The above example will return a `list[Vector]` with a size of (3, embedding_size).

    Retry and timeout:
        The `JinaEMInvoker` supports retry and timeout configuration.
        By default, the max retries is set to 0 and the timeout is set to 30.0 seconds.
        They can be customized by providing a custom `RetryConfig` object to the `retry_config` parameter.

        Retry config examples:
        ```python
        retry_config = RetryConfig(max_retries=0, timeout=None)  # No retry, no timeout
        retry_config = RetryConfig(max_retries=5, timeout=10.0)  # 5 max retries, 10.0 seconds timeout
        ```

        Usage example:
        ```python
        em_invoker = JinaEMInvoker(..., retry_config=retry_config)
        ```
    '''
    client: Incomplete
    model_kwargs: Incomplete
    def __init__(self, model_name: str, api_key: str | None = None, base_url: str = ..., model_kwargs: dict[str, Any] | None = None, default_hyperparameters: dict[str, Any] | None = None, retry_config: RetryConfig | None = None, truncation_config: TruncationConfig | None = None, vector_fuser: BaseVectorFuser | VectorFuserType | None = None) -> None:
        '''Initializes a new instance of the JinaEMInvoker class.

        Args:
            model_name (str): The name of the Jina embedding model to be used.
            api_key (str | None, optional): The API key for authenticating with Jina AI.
                Defaults to None, in which case the `JINA_API_KEY` environment variable will be used.
            base_url (str, optional): The base URL for the Jina AI API. Defaults to "https://api.jina.ai/v1".
            model_kwargs (dict[str, Any] | None, optional): Additional keyword arguments for the HTTP client.
                Defaults to None.
            default_hyperparameters (dict[str, Any] | None, optional): Default hyperparameters for invoking the model.
                Defaults to None.
            retry_config (RetryConfig | None, optional): The retry configuration for the embedding model.
                Defaults to None, in which case a default config with no retry and 30.0 seconds timeout will be used.
            truncation_config (TruncationConfig | None, optional): Configuration for text truncation behavior.
                Defaults to None, in which case no truncation is applied.
            vector_fuser (BaseVectorFuser | VectorFuserType | None, optional): The vector fuser to handle mixed content.
                Defaults to None, in which case handling the mixed modality content depends on the EM\'s capabilities.

        Raises:
            ValueError: If neither `api_key` nor `JINA_API_KEY` environment variable is provided.
        '''
