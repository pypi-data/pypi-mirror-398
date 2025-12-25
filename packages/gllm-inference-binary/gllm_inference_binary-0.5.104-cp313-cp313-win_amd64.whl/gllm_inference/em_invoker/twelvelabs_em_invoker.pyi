from _typeshed import Incomplete
from gllm_core.utils.retry import RetryConfig
from gllm_inference.em_invoker.em_invoker import BaseEMInvoker as BaseEMInvoker
from gllm_inference.em_invoker.schema.twelvelabs import InputType as InputType, Key as Key, OutputType as OutputType, TaskStatus as TaskStatus, VideoEmbeddingParams as VideoEmbeddingParams, VideoEmbeddingScope as VideoEmbeddingScope
from gllm_inference.em_invoker.vector_fuser.vector_fuser import BaseVectorFuser as BaseVectorFuser
from gllm_inference.schema import Attachment as Attachment, AttachmentType as AttachmentType, EMContent as EMContent, ModelId as ModelId, ModelProvider as ModelProvider, TruncationConfig as TruncationConfig, Vector as Vector, VectorFuserType as VectorFuserType
from typing import Any

SUPPORTED_ATTACHMENTS: Incomplete
VIDEO_EMBEDDING_PARAMS: Incomplete

class TwelveLabsEMInvoker(BaseEMInvoker):
    '''An embedding model invoker to interact with TwelveLabs embedding models.

    Attributes:
        model_id (str): The model ID of the embedding model.
        model_provider (str): The provider of the embedding model.
        model_name (str): The name of the embedding model.
        client (Client): The client for the TwelveLabs API.
        default_hyperparameters (dict[str, Any]): Default hyperparameters for invoking the embedding model.
        retry_config (RetryConfig): The retry configuration for the embedding model.
        truncation_config (TruncationConfig | None): The truncation configuration for the embedding model.
        vector_fuser (BaseVectorFuser | None): The vector fuser to handle mixed content.

    Input types:
        The `TwelveLabsEMInvoker` supports the following input types: text, audio, and image.
        Non-text inputs must be passed as a `Attachment` object.

    Output format:
        The `TwelveLabsEMInvoker` can embed either:
        1. A single content.
            1. A single content is either a text, an audio, or an image.
            2. The output will be a `Vector`, representing the embedding of the content.

            # Example 1: Embedding a text content.
            ```python
            text = "What animal is in this image?"
            result = await em_invoker.invoke(text)
            ```

            # Example 2: Embedding an audio content.
            ```python
            audio = Attachment.from_path("path/to/local/audio.mp3")
            result = await em_invoker.invoke(audio)
            ```

            # Example 3: Embedding an image content.
            ```python
            image = Attachment.from_path("path/to/local/image.png")
            result = await em_invoker.invoke(image)
            ```

            # Example 4: Embedding a video content.
            ```python
            video = Attachment.from_path("path/to/local/video.mp4")
            result = await em_invoker.invoke(video)
            ```


           The above examples will return a `Vector` with a size of (embedding_size,).

        2. A list of contents.
           1. A list of contents is a list that consists of any of the above single contents.
           2. The output will be a `list[Vector]`, where each element is a `Vector` representing the
              embedding of each single content.

           # Example: Embedding a list of contents.
           ```python
           text = "What animal is in this image?"
           audio = Attachment.from_path("path/to/local/audio.mp3")
           image = Attachment.from_path("path/to/local/image.png")
           video = Attachment.from_path("path/to/local/video.mp4")
           result = await em_invoker.invoke([text, audio, image, video])
           ```

           The above examples will return a `list[Vector]` with a size of (4, embedding_size).

    Video embedding:
        For advanced video embedding customization, you can pass hyperparameters to control the embedding process:
        ```python
        hyperparameters={
            "video_embed_create_params": {}, # optional parameters for EmbedClient.TasksClient.create(),
            "video_embed_retrieve_params": {}, # optional parameters for EmbedClient.TasksClient.retrieve()
            "wait_for_done_params": {}, # optional parameters for EmbedClient.TasksClient.wait_for_done()
        }

        video = Attachment.from_path("path/to/local/video.mp4")
        result = await em_invoker.invoke(video, hyperparameters)
        ```
        For video related hyperparameters, see https://docs.twelvelabs.io/sdk-reference/python/create-embeddings-v-1/create-video-embeddings.

        Furthermore, when embedding video:
        1. The video format should meet the requirements of TwelveLabs embedding model. For more details, see
        [Marengo requirements](https://docs.twelvelabs.io/v1.3/docs/concepts/models/marengo#video-file-requirements)
        2. VectorFuser is required to embed video content.

    Vector fusion:
        The `TwelveLabsEMInvoker` supports vector fusion, which allows fusing multiple results into a single vector.
        This feature allows the module to embed mixed modality contents, represented as tuples of contents.
        This feature can be enabled by providing a vector fuser to the `vector_fuser` parameter.

        Usage example:
        ```python
        em_invoker = TwelveLabsEMInvoker(..., vector_fuser=SumVectorFuser())  # Using a vector fuser class
        em_invoker = TwelveLabsEMInvoker(..., vector_fuser="sum")  # Using a vector fuser type

        text = "What animal is in this image?"
        image = Attachment.from_path("path/to/local/image.png")
        mix_content = (text, image)
        result = await em_invoker.invoke([text, image, mix_content])
        ```

        The above example will return a `list[Vector]` with a size of (3, embedding_size).

    Retry and timeout:
        The `TwelveLabsEMInvoker` supports retry and timeout configuration.
        By default, the max retries is set to 0 and the timeout is set to 30.0 seconds.
        They can be customized by providing a custom `RetryConfig` object to the `retry_config` parameter.

        Retry config examples:
        ```python
        retry_config = RetryConfig(max_retries=0, timeout=None)  # No retry, no timeout
        retry_config = RetryConfig(max_retries=5, timeout=10.0)  # 5 max retries, 10.0 seconds timeout
        ```

        Usage example:
        ```python
        em_invoker = TwelveLabsEMInvoker(..., retry_config=retry_config)
        ```
    '''
    client: Incomplete
    def __init__(self, model_name: str, api_key: str | None = None, model_kwargs: dict[str, Any] | None = None, default_hyperparameters: dict[str, Any] | None = None, retry_config: RetryConfig | None = None, truncation_config: TruncationConfig | None = None, vector_fuser: BaseVectorFuser | VectorFuserType | None = None) -> None:
        """Initializes a new instance of the TwelveLabsEMInvoker class.

        Args:
            model_name (str): The name of the TwelveLabs embedding model to be used.
            api_key (str | None, optional): The API key for the TwelveLabs API. Defaults to None, in which
                case the `TWELVELABS_API_KEY` environment variable will be used.
            model_kwargs (dict[str, Any] | None, optional): Additional keyword arguments for the TwelveLabs client.
                Defaults to None.
            default_hyperparameters (dict[str, Any] | None, optional): Default hyperparameters for invoking the model.
                Defaults to None.
            retry_config (RetryConfig | None, optional): The retry configuration for the embedding model.
                Defaults to None, in which case a default config with no retry and 30.0 seconds timeout will be used.
            truncation_config (TruncationConfig | None, optional): Configuration for text truncation behavior.
                Defaults to None, in which case no truncation is applied.
            vector_fuser (BaseVectorFuser | VectorFuserType | None, optional): The vector fuser to handle mixed content.
                Defaults to None, in which case handling the mixed modality content depends on the EM's capabilities.
        """
