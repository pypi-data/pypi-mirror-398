from _typeshed import Incomplete
from abc import ABC
from functools import cached_property
from gllm_core.event import EventEmitter
from gllm_core.utils import RetryConfig
from gllm_inference.constants import DOCUMENT_MIME_TYPES as DOCUMENT_MIME_TYPES, INVOKER_DEFAULT_TIMEOUT as INVOKER_DEFAULT_TIMEOUT
from gllm_inference.exceptions import BaseInvokerError as BaseInvokerError, convert_to_base_invoker_error as convert_to_base_invoker_error
from gllm_inference.lm_invoker.operations import BatchOperations as BatchOperations, DataStoreOperations as DataStoreOperations, FileOperations as FileOperations
from gllm_inference.output_transformer import build_output_transformer as build_output_transformer
from gllm_inference.output_transformer.output_transformer import BaseOutputTransformer as BaseOutputTransformer
from gllm_inference.schema import Attachment as Attachment, AttachmentStore as AttachmentStore, AttachmentType as AttachmentType, BatchStatus as BatchStatus, LMInput as LMInput, LMOutput as LMOutput, LMTool as LMTool, Message as Message, MessageContent as MessageContent, MessageRole as MessageRole, ModelId as ModelId, NativeTool as NativeTool, NativeToolType as NativeToolType, OperationType as OperationType, OutputTransformerType as OutputTransformerType, Reasoning as Reasoning, ResponseSchema as ResponseSchema, ToolCall as ToolCall, ToolResult as ToolResult, UploadedAttachment as UploadedAttachment
from typing import Any

class Key:
    """Defines valid keys in LM invokers JSON schema."""
    ADDITIONAL_PROPERTIES: str
    ANY_OF: str
    DATA_TYPE: str
    DATA_VALUE: str
    DEFAULT: str
    ID: str
    PROPERTIES: str
    REQUIRED: str
    TITLE: str
    TYPE: str

class InputType:
    """Defines valid input types in LM invokers JSON schema."""
    NULL: str

class BaseLMInvoker(ABC):
    """A base class for language model invokers used in Gen AI applications.

    The `BaseLMInvoker` class provides a framework for invoking language models.
    It handles both standard and streaming invocation.

    Attributes:
        model_id (str): The model ID of the language model.
        model_provider (str): The provider of the language model.
        model_name (str): The name of the language model.
        default_hyperparameters (dict[str, Any]): Default hyperparameters for invoking the language model.
        tools (list[Tool]): Tools provided to the language model to enable tool calling.
        response_schema (ResponseSchema | None): The schema of the response. If provided, the model will output a
            structured response as defined by the schema. Supports both Pydantic BaseModel and JSON schema dictionary.
        output_analytics (bool): Whether to output the invocation analytics.
        retry_config (RetryConfig): The retry configuration for the language model.
        output_transformer (OutputTransformerType): The type of output transformer to use.
    """
    default_hyperparameters: Incomplete
    response_schema: Incomplete
    output_analytics: Incomplete
    retry_config: Incomplete
    output_transformer: Incomplete
    def __init__(self, model_id: ModelId, default_hyperparameters: dict[str, Any] | None = None, supported_attachments: set[str] | None = None, tools: list[LMTool] | None = None, response_schema: ResponseSchema | None = None, output_analytics: bool = False, retry_config: RetryConfig | None = None, output_transformer: OutputTransformerType = ..., simplify_events: bool = False) -> None:
        """Initializes a new instance of the BaseLMInvoker class.

        Args:
            model_id (ModelId): The model ID of the language model.
            default_hyperparameters (dict[str, Any] | None, optional): Default hyperparameters for invoking the
                language model. Defaults to None, in which case an empty dictionary is used.
            supported_attachments (set[str] | None, optional): A set of supported attachment types. Defaults to None,
                in which case an empty set is used (indicating that no attachments are supported).
            tools (list[LMTool] | None, optional): Tools provided to the model to enable tool calling.
                Defaults to None, in which case an empty list is used.
            response_schema (ResponseSchema | None, optional): The schema of the response. If provided, the model will
                output a structured response as defined by the schema. Supports both Pydantic BaseModel and JSON schema
                dictionary. Defaults to None.
            output_analytics (bool, optional): Whether to output the invocation analytics. Defaults to False.
            retry_config (RetryConfig | None, optional): The retry configuration for the language model.
                Defaults to None, in which case a default config with no retry and 30.0 seconds timeout will be used.
            output_transformer (OutputTransformerType, optional): The type of output transformer to use.
                Defaults to OutputTransformerType.IDENTITY, which returns the output without transformation.
            simplify_events (bool, optional): Temporary parameter to control the streamed events format.
                When True, uses the simplified events format. When False, uses the legacy events format for
                backward compatibility. Will be removed in v0.6. Defaults to False.
        """
    @property
    def model_id(self) -> str:
        """The model ID of the language model.

        Returns:
            str: The model ID of the language model.
        """
    @property
    def model_provider(self) -> str:
        """The provider of the language model.

        Returns:
            str: The provider of the language model.
        """
    @property
    def model_name(self) -> str:
        """The name of the language model.

        Returns:
            str: The name of the language model.
        """
    @cached_property
    def batch(self) -> BatchOperations:
        """The batch operations for the language model.

        Returns:
            BatchOperations: The batch operations for the language model.
        """
    @cached_property
    def file(self) -> FileOperations:
        """The file operations for the language model.

        Returns:
            FileOperations: The file operations for the language model.
        """
    @cached_property
    def data_store(self) -> DataStoreOperations:
        """The data store operations for the language model.

        Returns:
            DataStoreOperations: The data store operations for the language model.
        """
    def set_tools(self, tools: list[LMTool]) -> None:
        """Sets the tools for the language model.

        This method sets the tools for the language model. Any existing tools will be replaced.

        Args:
            tools (list[LMTool]): The list of tools to be used.
        """
    def clear_tools(self) -> None:
        """Clears the tools for the language model.

        This method clears the tools for the language model by calling the `set_tools` method with an empty list.
        """
    def set_response_schema(self, response_schema: ResponseSchema | None) -> None:
        """Sets the response schema for the language model.

        This method sets the response schema for the language model. Any existing response schema will be replaced.

        Args:
            response_schema (ResponseSchema | None): The response schema to be used.
        """
    def clear_response_schema(self) -> None:
        """Clears the response schema for the language model.

        This method clears the response schema for the language model by calling the `set_response_schema` method with
        None.
        """
    async def count_input_tokens(self, messages: LMInput) -> int:
        """Counts the input tokens for an invocation request inputs.

        This method counts the input tokens for an invocation request inputs. This method is useful for:
        1. Estimating the cost of an invocation request before invoking the language model.
        2. Checking if the invocation request is too large to be processed by the language model.

        Args:
            messages (LMInput): The input messages for the language model.
                1. If a list of Message objects is provided, it is used as is.
                2. If a list of MessageContent or a string is provided, it is converted into a user message.

        Returns:
            int: The number of input tokens for the invocation request.

        Raises:
            TimeoutError: If the invocation times out.
        """
    async def invoke(self, messages: LMInput, hyperparameters: dict[str, Any] | None = None, event_emitter: EventEmitter | None = None) -> str | LMOutput:
        """Invokes the language model.

        This method validates the messages and invokes the language model. It handles both standard
        and streaming invocation. Streaming mode is enabled if an event emitter is provided.
        The method includes retry logic with exponential backoff for transient failures.

        Args:
            messages (LMInput): The input messages for the language model.
                1. If a list of Message objects is provided, it is used as is.
                2. If a list of MessageContent or a string is provided, it is converted into a user message.
            hyperparameters (dict[str, Any] | None, optional): A dictionary of hyperparameters for the language model.
                Defaults to None, in which case the default hyperparameters are used.
            event_emitter (EventEmitter | None, optional): The event emitter for streaming tokens. If provided,
                streaming invocation is enabled. Defaults to None.

        Returns:
            str | LMOutput: The generated response from the language model.

        Raises:
            CancelledError: If the invocation is cancelled.
            ModelNotFoundError: If the model is not found.
            ProviderAuthError: If the model authentication fails.
            ProviderInternalError: If the model internal error occurs.
            ProviderInvalidArgsError: If the model parameters are invalid.
            ProviderOverloadedError: If the model is overloaded.
            ProviderRateLimitError: If the model rate limit is exceeded.
            TimeoutError: If the invocation times out.
            ValueError: If the messages are not in the correct format.
        """
