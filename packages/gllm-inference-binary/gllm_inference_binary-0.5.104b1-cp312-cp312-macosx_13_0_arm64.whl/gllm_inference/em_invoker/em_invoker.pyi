from _typeshed import Incomplete
from abc import ABC
from gllm_core.utils.retry import RetryConfig
from gllm_inference.constants import DOCUMENT_MIME_TYPES as DOCUMENT_MIME_TYPES, INVOKER_DEFAULT_TIMEOUT as INVOKER_DEFAULT_TIMEOUT
from gllm_inference.em_invoker.vector_fuser import build_vector_fuser as build_vector_fuser
from gllm_inference.em_invoker.vector_fuser.vector_fuser import BaseVectorFuser as BaseVectorFuser
from gllm_inference.exceptions import BaseInvokerError as BaseInvokerError, convert_to_base_invoker_error as convert_to_base_invoker_error
from gllm_inference.schema import Attachment as Attachment, AttachmentType as AttachmentType, EMContent as EMContent, ModelId as ModelId, TruncateSide as TruncateSide, TruncationConfig as TruncationConfig, Vector as Vector, VectorFuserType as VectorFuserType
from typing import Any

FusionBlueprint = list[int | tuple[int, ...]]

class BaseEMInvoker(ABC):
    """A base class for embedding model invokers used in Gen AI applications.

    The `BaseEMInvoker` class provides a framework for invoking embedding models.

    Attributes:
        model_id (str): The model ID of the embedding model.
        model_provider (str): The provider of the embedding model.
        model_name (str): The name of the embedding model.
        default_hyperparameters (dict[str, Any]): Default hyperparameters for invoking the
            embedding model. Defaults to None, in which case an empty dictionary is used.
        retry_config (RetryConfig): The retry configuration for the embedding model.
            Defaults to None, in which case a default config with no retry and 30.0 seconds timeout will be used.
        truncation_config (TruncationConfig | None): The truncation configuration for the embedding model.
            Defaults to None, in which case no truncation is applied.
        vector_fuser (BaseVectorFuser | None): The vector fuser to handle mixed content.
    """
    default_hyperparameters: Incomplete
    retry_config: Incomplete
    truncation_config: Incomplete
    vector_fuser: Incomplete
    def __init__(self, model_id: ModelId, default_hyperparameters: dict[str, Any] | None = None, supported_attachments: set[str] | None = None, retry_config: RetryConfig | None = None, truncation_config: TruncationConfig | None = None, vector_fuser: BaseVectorFuser | VectorFuserType | None = None) -> None:
        """Initializes a new instance of the BaseEMInvoker class.

        Args:
            model_id (ModelId): The model ID of the embedding model.
            default_hyperparameters (dict[str, Any] | None, optional): Default hyperparameters for invoking the
                embedding model. Defaults to None, in which case an empty dictionary is used.
            supported_attachments (set[str] | None, optional): A set of supported attachment types. Defaults to None,
                in which case an empty set is used (indicating that no attachments are supported).
            retry_config (RetryConfig | None, optional): The retry configuration for the embedding model.
                Defaults to None, in which case a default config with no retry and 30.0 seconds timeout will be used.
            truncation_config (TruncationConfig | None, optional): Configuration for text truncation behavior.
                Defaults to None, in which case no truncation is applied.
            vector_fuser (BaseVectorFuser | VectorFuserType | None, optional): The vector fuser to handle mixed content.
                Defaults to None, in which case handling the mixed modality content depends on the EM's capabilities.
        """
    @property
    def model_id(self) -> str:
        """The model ID of the embedding model.

        Returns:
            str: The model ID of the embedding model.
        """
    @property
    def model_provider(self) -> str:
        """The provider of the embedding model.

        Returns:
            str: The provider of the embedding model.
        """
    @property
    def model_name(self) -> str:
        """The name of the embedding model.

        Returns:
            str: The name of the embedding model.
        """
    async def invoke(self, content: EMContent | list[EMContent], hyperparameters: dict[str, Any] | None = None) -> Vector | list[Vector]:
        """Invokes the embedding model with the provided content or list of contents.

        This method invokes the embedding model with the provided content or list of contents.
        It includes retry logic with exponential backoff for transient failures.

        Args:
            content (EMContent | list[EMContent]): The input or list of inputs to be embedded using the embedding model.
            hyperparameters (dict[str, Any] | None, optional): A dictionary of hyperparameters for the embedding model.
                Defaults to None, in which case the default hyperparameters are used.

        Returns:
            Vector | list[Vector]: The vector representations of the input contents:
                1. If the input is an `EMContent`, the output is a `Vector`.
                2. If the input is a `list[EMContent]`, the output is a `list[Vector]`.

        Raises:
            CancelledError: If the invocation is cancelled.
            ModelNotFoundError: If the model is not found.
            ProviderAuthError: If the model authentication fails.
            ProviderInternalError: If the model internal error occurs.
            ProviderInvalidArgsError: If the model parameters are invalid.
            ProviderOverloadedError: If the model is overloaded.
            ProviderRateLimitError: If the model rate limit is exceeded.
            TimeoutError: If the invocation times out.
            ValueError: If the input content is invalid.
        """
