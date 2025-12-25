from _typeshed import Incomplete
from gllm_core.utils.retry import RetryConfig
from gllm_inference.constants import INVOKER_PROPAGATED_MAX_RETRIES as INVOKER_PROPAGATED_MAX_RETRIES, OPENAI_DEFAULT_URL as OPENAI_DEFAULT_URL
from gllm_inference.em_invoker.em_invoker import BaseEMInvoker as BaseEMInvoker
from gllm_inference.em_invoker.schema.openai import Key as Key
from gllm_inference.em_invoker.vector_fuser.vector_fuser import BaseVectorFuser as BaseVectorFuser
from gllm_inference.exceptions.error_parser import convert_to_base_invoker_error as convert_to_base_invoker_error
from gllm_inference.exceptions.exceptions import BaseInvokerError as BaseInvokerError
from gllm_inference.exceptions.provider_error_map import OPENAI_MESSAGE_MAPPING as OPENAI_MESSAGE_MAPPING, OPENAI_RESPONSE_DETAIL_MAPPING as OPENAI_RESPONSE_DETAIL_MAPPING
from gllm_inference.schema import ModelId as ModelId, ModelProvider as ModelProvider, TruncationConfig as TruncationConfig, Vector as Vector, VectorFuserType as VectorFuserType
from typing import Any

SUPPORTED_ATTACHMENTS: Incomplete

class OpenAIEMInvoker(BaseEMInvoker):
    '''An embedding model invoker to interact with OpenAI embedding models.

    Attributes:
        model_id (str): The model ID of the embedding model.
        model_provider (str): The provider of the embedding model.
        model_name (str): The name of the embedding model.
        client_kwargs (dict[str, Any]): The keyword arguments for the OpenAI client.
        default_hyperparameters (dict[str, Any]): Default hyperparameters for invoking the embedding model.
        retry_config (RetryConfig): The retry configuration for the embedding model.
        truncation_config (TruncationConfig | None): The truncation configuration for the embedding model.
        vector_fuser (BaseVectorFuser | None): The vector fuser to handle mixed content.

    Basic usage:
        The `OpenAIEMInvoker` can be used as follows:
        ```python
        em_invoker = OpenAIEMInvoker(model_name="text-embedding-3-small")
        result = await em_invoker.invoke("Hi there!")
        ```

    OpenAI compatible endpoints:
        The `OpenAIEMInvoker` can also be used to interact with endpoints that are compatible with
        OpenAI\'s Embeddings API schema. This includes but are not limited to:
        1. Text Embeddings Inference (https://github.com/huggingface/text-embeddings-inference)
        2. vLLM (https://vllm.ai/)
        Please note that the supported features and capabilities may vary between different endpoints and
        language models. Using features that are not supported by the endpoint will result in an error.

        This customization can be done by setting the `base_url` parameter to the base URL of the endpoint:
        ```python
        em_invoker = OpenAIEMInvoker(
            model_name="<model-name>",
            api_key="<your-api-key>",
            base_url="<https://base-url>",
        )
        result = await em_invoker.invoke("Hi there!")
        ```

    Input types:
        The `OpenAIEMInvoker` only supports text inputs.

    Output format:
        The `OpenAIEMInvoker` can embed either:
        1. A single content.
           1. A single content is a single text.
           2. The output will be a `Vector`, representing the embedding of the content.

           # Example 1: Embedding a text content.
           ```python
           text = "This is a text"
           result = await em_invoker.invoke(text)
           ```

           The above examples will return a `Vector` with a size of (embedding_size,).

        2. A list of contents.
           1. A list of contents is a list of texts.
           2. The output will be a `list[Vector]`, where each element is a `Vector` representing the
              embedding of each single content.

           # Example: Embedding a list of contents.
           ```python
           text1 = "This is a text"
           text2 = "This is another text"
           text3 = "This is yet another text"
           result = await em_invoker.invoke([text1, text2, text3])
           ```

           The above examples will return a `list[Vector]` with a size of (3, embedding_size).

    Vector fusion:
        The `OpenAIEMInvoker` supports vector fusion, which allows fusing multiple results into a single vector.
        This feature allows the module to embed mixed modality contents, represented as tuples of contents.
        This feature can be enabled by providing a vector fuser to the `vector_fuser` parameter.

        Usage example:
        ```python
        em_invoker = OpenAIEMInvoker(..., vector_fuser=SumVectorFuser())  # Using a vector fuser class
        em_invoker = OpenAIEMInvoker(..., vector_fuser="sum")  # Using a vector fuser type

        text = "What animal is in this image?"
        image = Attachment.from_path("path/to/local/image.png")
        mix_content = (text, image)
        result = await em_invoker.invoke([text, image, mix_content])
        ```

        The above example will return a `list[Vector]` with a size of (3, embedding_size).

    Retry and timeout:
        The `OpenAIEMInvoker` supports retry and timeout configuration.
        By default, the max retries is set to 0 and the timeout is set to 30.0 seconds.
        They can be customized by providing a custom `RetryConfig` object to the `retry_config` parameter.

        Retry config examples:
        ```python
        retry_config = RetryConfig(max_retries=0, timeout=None)  # No retry, no timeout
        retry_config = RetryConfig(max_retries=5, timeout=10.0)  # 5 max retries, 10.0 seconds timeout
        ```

        Usage example:
        ```python
        em_invoker = OpenAIEMInvoker(..., retry_config=retry_config)
        ```
    '''
    client_kwargs: Incomplete
    def __init__(self, model_name: str, api_key: str | None = None, base_url: str = ..., model_kwargs: dict[str, Any] | None = None, default_hyperparameters: dict[str, Any] | None = None, retry_config: RetryConfig | None = None, truncation_config: TruncationConfig | None = None, vector_fuser: BaseVectorFuser | VectorFuserType | None = None) -> None:
        '''Initializes a new instance of the OpenAIEMInvoker class.

        Args:
            model_name (str): The name of the OpenAI embedding model to be used.
            api_key (str | None, optional): The API key for authenticating with OpenAI. Defaults to None, in which
                case the `OPENAI_API_KEY` environment variable will be used. If the endpoint does not require an
                API key, a dummy value can be passed (e.g. "<empty>").
            base_url (str, optional): The base URL of a custom endpoint that is compatible with OpenAI\'s
                Embeddings API schema. Defaults to OpenAI\'s default URL.
            model_kwargs (dict[str, Any] | None, optional): Additional keyword arguments for the OpenAI client.
                Defaults to None.
            default_hyperparameters (dict[str, Any] | None, optional): Default hyperparameters for invoking the model.
                Defaults to None.
            retry_config (RetryConfig | None, optional): The retry configuration for the embedding model.
                Defaults to None, in which case a default config with no retry and 30.0 seconds timeout will be used.
            truncation_config (TruncationConfig | None, optional): Configuration for text truncation behavior.
                Defaults to None, in which case no truncation is applied.
            vector_fuser (BaseVectorFuser | VectorFuserType | None, optional): The vector fuser to handle mixed content.
                Defaults to None, in which case handling the mixed modality content depends on the EM\'s capabilities.
        '''
