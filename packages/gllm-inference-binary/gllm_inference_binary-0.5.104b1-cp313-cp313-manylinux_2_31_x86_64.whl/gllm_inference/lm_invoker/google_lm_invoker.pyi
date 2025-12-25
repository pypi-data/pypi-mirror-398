from _typeshed import Incomplete
from gllm_core.utils import RetryConfig
from gllm_inference.constants import GOOGLE_SCOPES as GOOGLE_SCOPES, SECONDS_TO_MILLISECONDS as SECONDS_TO_MILLISECONDS
from gllm_inference.exceptions import BaseInvokerError as BaseInvokerError, convert_to_base_invoker_error as convert_to_base_invoker_error
from gllm_inference.lm_invoker.lm_invoker import BaseLMInvoker as BaseLMInvoker
from gllm_inference.lm_invoker.schema.google import InputType as InputType, JobState as JobState, Key as Key
from gllm_inference.output_transformer.output_transformer import BaseOutputTransformer as BaseOutputTransformer
from gllm_inference.schema import Attachment as Attachment, AttachmentStore as AttachmentStore, AttachmentType as AttachmentType, BatchStatus as BatchStatus, LMInput as LMInput, LMOutput as LMOutput, LMTool as LMTool, Message as Message, MessageContent as MessageContent, MessageRole as MessageRole, ModelId as ModelId, ModelProvider as ModelProvider, NativeTool as NativeTool, OutputTransformerType as OutputTransformerType, Reasoning as Reasoning, ResponseSchema as ResponseSchema, StreamBuffer as StreamBuffer, ThinkingEvent as ThinkingEvent, TokenUsage as TokenUsage, ToolCall as ToolCall, ToolResult as ToolResult, UploadedAttachment as UploadedAttachment
from gllm_inference.utils import SizeUnit as SizeUnit, get_size as get_size
from typing import Any

SUPPORTED_ATTACHMENTS: Incomplete
DEFAULT_THINKING_BUDGET: int
REQUIRE_THINKING_MODEL_PREFIX: Incomplete
IMAGE_GENERATION_MODELS: Incomplete
MAX_INLINE_ATTACHMENT_SIZE_MB: int
ADD_FILE_STATUS_CHECK_INTERVAL: float
JOB_STATE_MAP: Incomplete
BATCH_STATUS_MAP: Incomplete

class URLPattern:
    """Defines specific Google related URL patterns."""
    GOOGLE_FILE: Incomplete
    YOUTUBE: Incomplete

class GoogleLMInvoker(BaseLMInvoker):
    '''A language model invoker to interact with Google language models.

    Attributes:
        model_id (str): The model ID of the language model.
        model_provider (str): The provider of the language model.
        model_name (str): The name of the language model.
        client_params (dict[str, Any]): The Google client instance init parameters.
        default_hyperparameters (dict[str, Any]): Default hyperparameters for invoking the model.
        tools (list[Tool]): The list of tools provided to the model to enable tool calling.
        response_schema (ResponseSchema | None): The schema of the response. If provided, the model will output a
            structured response as defined by the schema. Supports both Pydantic BaseModel and JSON schema dictionary.
        output_analytics (bool): Whether to output the invocation analytics.
        retry_config (RetryConfig | None): The retry configuration for the language model.
        thinking (bool): Whether to enable thinking. Only allowed for thinking models.
        thinking_budget (int): The tokens allowed for thinking process. Only allowed for thinking models.
            If set to -1, the model will control the budget automatically.
        image_generation (bool): Whether to generate image. Only allowed for image generation models.
        data_stores (list[AttachmentStore]): The data stores to retrieve internal knowledge from.
        auto_upload (bool): Whether to automatically upload attachments to files API if the inputs total
            size exceeds the threshold of 20MB.
        output_transformer (OutputTransformerType): The type of output transformer to use.

    Basic usage:
        The `GoogleLMInvoker` can be used as follows:
        ```python
        lm_invoker = GoogleLMInvoker(model_name="gemini-2.5-flash")
        result = await lm_invoker.invoke("Hi there!")
        ```

    Authentication:
        The `GoogleLMInvoker` can use either Google Gen AI or Google Vertex AI.

        Google Gen AI is recommended for quick prototyping and development.
        It requires a Gemini API key for authentication.

        Usage example:
        ```python
        lm_invoker = GoogleLMInvoker(
            model_name="gemini-2.5-flash",
            api_key="your_api_key"
        )
        ```

        Google Vertex AI is recommended to build production-ready applications.
        It requires a service account JSON file for authentication.

        Usage example:
        ```python
        lm_invoker = GoogleLMInvoker(
            model_name="gemini-2.5-flash",
            credentials_path="path/to/service_account.json"
        )
        ```

        If neither `api_key` nor `credentials_path` is provided, Google Gen AI will be used by default.
        The `GOOGLE_API_KEY` environment variable will be used for authentication.

    Input types:
        The `GoogleLMInvoker` supports the following input types: text, audio, document, image, and video.
        Non-text inputs can be passed as an `Attachment` object with either the `user` or `assistant` role.

        Usage example:
        ```python
        text = "What animal is in this image?"
        image = Attachment.from_path("path/to/local/image.png")
        result = await lm_invoker.invoke([text, image])
        ```

    Text output:
        The `GoogleLMInvoker` generates text outputs by default.
        Text outputs are stored in the `outputs` attribute of the `LMOutput` object and can be accessed
        via the `texts` (all text outputs) or `text` (first text output) properties.

        Output example:
        ```python
        LMOutput(outputs=[LMOutputItem(type="text", output="Hello, there!")])
        ```

    Structured output:
        The `GoogleLMInvoker` can be configured to generate structured outputs.
        This feature can be enabled by providing a schema to the `response_schema` parameter.

        Structured outputs are stored in the `outputs` attribute of the `LMOutput` object and can be accessed
        via the `structureds` (all structured outputs) or `structured` (first structured output) properties.

        The schema must either be one of the following:
        1. A Pydantic BaseModel class
            The structured output will be a Pydantic model.
        2. A JSON schema dictionary
            JSON dictionary schema must be compatible with Pydantic\'s JSON schema, especially for complex schemas.
            Thus, it is recommended to create the JSON schema using Pydantic\'s `model_json_schema` method.
            The structured output will be a dictionary.

        Usage example:
        ```python
        class Animal(BaseModel):
            name: str
            color: str

        json_schema = Animal.model_json_schema()

        lm_invoker = GoogleLMInvoker(..., response_schema=Animal)  # Using Pydantic BaseModel class
        lm_invoker = GoogleLMInvoker(..., response_schema=json_schema)  # Using JSON schema dictionary
        ```

        Output example:
        ```python
        # Using Pydantic BaseModel class outputs a Pydantic model
        LMOutput(outputs=[LMOutputItem(type="structured", output=Animal(name="dog", color="white"))])

        # Using JSON schema dictionary outputs a dictionary
        LMOutput(outputs=[LMOutputItem(type="structured", output={"name": "dog", "color": "white"})])
        ```

        Structured output is not compatible with tool calling.
        When structured output is enabled, streaming is disabled.

    Image generation:
        The `GoogleLMInvoker` can be configured to generate images.
        This feature can be enabled by using an image generation model, such as `gemini-2.5-flash-image`.

        Image outputs are stored in the `outputs` attribute of the `LMOutput` object and can be accessed
        via the `attachments` property.

        Usage example:
        ```python
        lm_invoker = GoogleLMInvoker("gemini-2.5-flash-image")
        result = await lm_invoker.invoke("Create a picture...")
        result.attachments[0].write_to_file("path/to/local/image.png")
        ```

        Output example:
        ```python
        LMOutput(
            outputs=[
                LMOutputItem(type="text", output="Creating a picture..."),
                LMOutputItem(
                    type="attachment",
                    output=Attachment(filename="image.png", mime_type="image/png", data=b"..."),
                ),
            ],
        )
        ```

        Image generation is not compatible with tool calling and thinking.
        When image generation is enabled, streaming is disabled.

    Tool calling:
        The `GoogleLMInvoker` can be configured to call tools to perform certain tasks.
        This feature can be enabled by providing a list of `Tool` objects to the `tools` parameter.

        Tool calls outputs are stored in the `outputs` attribute of the `LMOutput` object and
        can be accessed via the `tool_calls` property.

        Usage example:
        ```python
        lm_invoker = GoogleLMInvoker(..., tools=[tool_1, tool_2])
        ```

        Output example:
        ```python
        LMOutput(
            outputs=[
                LMOutputItem(type="text", output="I\'m using tools..."),
                LMOutputItem(type="tool_call", output=ToolCall(id="123", name="tool_1", args={"key": "value"})),
                LMOutputItem(type="tool_call", output=ToolCall(id="456", name="tool_2", args={"key": "value"})),
            ]
        )
        ```

    Thinking:
        The `GoogleLMInvoker` can be configured to perform step-by-step thinking process before answering.
        This feature can be enabled by setting the `thinking` parameter to `True`.

        Thinking outputs are stored in the `outputs` attribute of the `LMOutput` object
        and can be accessed via the `thinkings` property.

        Usage example:
        ```python
        lm_invoker = GoogleLMInvoker(..., thinking=True, thinking_budget=1024)
        ```

        Output example:
        ```python
        LMOutput(
            outputs=[
                LMOutputItem(type="thinking", output=Reasoning(type="thinking", reasoning="I\'m thinking...", ...)),
                LMOutputItem(type="text", output="Golden retriever is a good dog breed."),
            ]
        )
        ```

        Streaming output example:
        ```python
        {"type": "thinking_start", "value": "", ...}
        {"type": "thinking", "value": "I\'m ", ...}
        {"type": "thinking", "value": "thinking...", ...}
        {"type": "thinking_end", "value": "", ...}
        {"type": "response", "value": "Golden retriever ", ...}
        {"type": "response", "value": "is a good dog breed.", ...}
        ```
        Note: By default, the thinking token will be streamed with the legacy `data` event type.
        To use the new simplified streamed event format, set the `simplify_events` parameter to `True` during
        LM invoker initialization. The legacy event format support will be removed in v0.6.

        The amount of tokens allocated for the thinking process can be set via the `thinking_budget` parameter.
        For more information, please refer to the following documentation:
        https://ai.google.dev/gemini-api/docs/thinking

        Thinking is only available for certain models, starting from Gemini 2.5 series.
        Thinking is required for Gemini 2.5 Pro models.

    Analytics tracking:
        The `GoogleLMInvoker` can be configured to output additional information about the invocation.
        This feature can be enabled by setting the `output_analytics` parameter to `True`.

        When enabled, the following attributes will be stored in the output:
        1. `token_usage`: The token usage.
        2. `duration`: The duration in seconds.
        3. `finish_details`: The details about how the generation finished.

        Output example:
        ```python
        LMOutput(
            outputs=[...],
            token_usage=TokenUsage(input_tokens=100, output_tokens=50),
            duration=0.729,
            finish_details={"stop_reason": "end_turn"},
        )
        ```

    Retry and timeout:
        The `GoogleLMInvoker` supports retry and timeout configuration.
        By default, the max retries is set to 0 and the timeout is set to 30.0 seconds.
        They can be customized by providing a custom `RetryConfig` object to the `retry_config` parameter.

        Retry config examples:
        ```python
        retry_config = RetryConfig(max_retries=0, timeout=None)  # No retry, no timeout
        retry_config = RetryConfig(max_retries=5, timeout=10.0)  # 5 max retries, 10.0 seconds timeout
        ```

        Usage example:
        ```python
        lm_invoker = GoogleLMInvoker(..., retry_config=retry_config)
        ```

    Batch processing:
        The `GoogleLMInvoker` supports batch processing, which allows the language model to process multiple
        requests in a single call. Batch processing is supported through the `batch` attribute.

        Due to Google SDK limitations with batch processing:
        1. Only inline requests are currently supported (not file-based or BigQuery sources).
        2. The total size of all requests must be under 20MB.
        3. Original request indices are not preserved in the results. The results are keyed by request index in the
        format \'1\', \'2\', etc, in which order are preserved based on the original request order. If you want to use
        custom request IDs, you can pass them as a list of strings to the `custom_request_ids` keyword argument

        Usage example:
        ```python
        requests = {"1": "What color is the sky?", "2": "What color is the grass?"}
        results = await lm_invoker.batch.invoke(requests)
        ```

        Output example:
        ```python
        {
            "1": LMOutput(outputs=[LMOutputItem(type="text", output="The sky is blue.")]),
            "2": LMOutput(finish_details={"type": "error", "message": "..."}),
        }
        ```

        The `GoogleLMInvoker` also supports the following standalone batch processing operations:

        1. Create a batch job:
            ```python
            requests = {"1": "What color is the sky?", "2": "What color is the grass?"}
            batch_id = await lm_invoker.batch.create(requests)
            ```

        2. Get the status of a batch job:
            ```python
            status = await lm_invoker.batch.status(batch_id)
            ```

        3. Retrieve the results of a batch job:

            In default, the results will be keyed by request index in the format \'1\', \'2\', etc,
            in which order are preserved based on the original request order.


            ```python
            results = await lm_invoker.batch.retrieve(batch_id)
            ```

            Output example:
            ```python
            {
                "1": LMOutput(outputs=[LMOutputItem(type="text", output="The sky is blue.")]),
                "2": LMOutput(finish_details={"type": "error", "error": {"message": "...", ...}, ...}),
            }
            ```

            If you pass custom_request_ids to the create method, the results will be keyed by the custom_request_ids.
            ```python
            results = await lm_invoker.batch.retrieve(batch_id, custom_request_ids=["request_1", "request_2"])
            ```

            Output example:
            ```python
            {
                "request_1": LMOutput(outputs=[LMOutputItem(type="text", output="The sky is blue.")]),
                "request_2": LMOutput(finish_details={"type": "error", "error": {"message": "...", ...}, ...}),
            }
            ```

        4. List the batch jobs:
            ```python
            batch_jobs = await lm_invoker.batch.list()
            ```

            Output example:
            ```python
            [
                {"id": "batch_123", "status": "finished"},
                {"id": "batch_456", "status": "in_progress"},
                {"id": "batch_789", "status": "canceling"},
            ]
            ```

        5. Cancel a batch job:
            ```python
            await lm_invoker.batch.cancel(batch_id)
            ```

    File processing:
        The `GoogleLMInvoker` supports file processing, which allows managing files through Google\'s files API.
        File processing is supported through the `file` attribute.

        The following file operations are supported:

        1. Upload a file:
            ```python
            uploaded_attachment = await lm_invoker.file.upload(attachment)
            ```

        2. List the files:
            ```python
            uploaded_attachments = await lm_invoker.file.list()
            ```

        3. Delete a file:
            ```python
            await lm_invoker.file.delete(uploaded_attachment)
            ```

        The uploaded attachments can be used as attachments in invocation requests:
        ```python
        result = await lm_invoker.invoke(["Explain this file!", uploaded_attachment])
        ```

    Data store operations:
        The `GoogleLMInvoker` supports data store operations, which allows managing file search stores through
        Google\'s file search API. Data store operations is supported through the `data_store` attribute.

        The following data store operations are supported:

        1. Create a data store:
            ```python
            store = await lm_invoker.data_store.create()
            ```

        2. List the data stores:
            ```python
            stores = await lm_invoker.data_store.list()
            ```

        3. Delete a data store:
            ```python
            await lm_invoker.data_store.delete(store)
            ```

        4. Add a file to a data store:
            ```python
            attachment = Attachment.from_path("path/to/file.pdf")
            await lm_invoker.data_store.add_file(store, file)
            ```

        The stores can be assigned to the invoker and used as internal knowledge in invocation requests:

        1. Assign to new instance:
            ```python
            lm_invoker = GoogleLMInvoker(..., data_stores=[store])
            ```

        2. Assign to existing instance:
            ```python
            lm_invoker.set_data_stores([store])
            ```
    '''
    client_params: Incomplete
    image_generation: Incomplete
    thinking: Incomplete
    thinking_budget: Incomplete
    auto_upload: Incomplete
    def __init__(self, model_name: str, api_key: str | None = None, credentials_path: str | None = None, project_id: str | None = None, location: str = 'us-central1', model_kwargs: dict[str, Any] | None = None, default_hyperparameters: dict[str, Any] | None = None, tools: list[LMTool] | None = None, response_schema: ResponseSchema | None = None, output_analytics: bool = False, retry_config: RetryConfig | None = None, thinking: bool | None = None, thinking_budget: int = ..., data_stores: list[AttachmentStore] | None = None, auto_upload: bool = True, output_transformer: OutputTransformerType = ..., simplify_events: bool = False) -> None:
        '''Initializes a new instance of the GoogleLMInvoker class.

        Args:
            model_name (str): The name of the model to use.
            api_key (str | None, optional): Required for Google Gen AI authentication. Cannot be used together
                with `credentials_path`. Defaults to None.
            credentials_path (str | None, optional): Required for Google Vertex AI authentication. Path to the service
                account credentials JSON file. Cannot be used together with `api_key`. Defaults to None.
            project_id (str | None, optional): The Google Cloud project ID for Vertex AI. Only used when authenticating
                with `credentials_path`. Defaults to None, in which case it will be loaded from the credentials file.
            location (str, optional): The location of the Google Cloud project for Vertex AI. Only used when
                authenticating with `credentials_path`. Defaults to "us-central1".
            model_kwargs (dict[str, Any] | None, optional): Additional keyword arguments for the Google Vertex AI
                client.
            default_hyperparameters (dict[str, Any] | None, optional): Default hyperparameters for invoking the model.
                Defaults to None.
            tools (list[LMTool] | None, optional): Tools provided to the model to enable tool calling.
                Defaults to None.
            response_schema (ResponseSchema | None, optional): The schema of the response. If provided, the model will
                output a structured response as defined by the schema. Supports both Pydantic BaseModel and JSON schema
                dictionary. Defaults to None.
            output_analytics (bool, optional): Whether to output the invocation analytics. Defaults to False.
            retry_config (RetryConfig | None, optional): The retry configuration for the language model.
                Defaults to None, in which case a default config with no retry and 30.0 seconds timeout will be used.
            thinking (bool | None, optional): Whether to enable thinking. Only allowed for thinking models.
                Defaults to True for Gemini 2.5 Pro models and False for other models.
            thinking_budget (int, optional): The tokens allowed for thinking process. Only allowed for thinking models.
                Defaults to -1, in which case the model will control the budget automatically.
            data_stores (list[AttachmentStore] | None, optional): The data stores to retrieve internal knowledge from.
                Defaults to None, in which case no data stores will be used.
            auto_upload (bool, optional): Whether to automatically upload attachments to files API if the inputs total
                size exceeds the threshold of 20MB. Defaults to True.
            output_transformer (OutputTransformerType, optional): The type of output transformer to use.
                Defaults to OutputTransformerType.IDENTITY, which returns the output without transformation.
            simplify_events (bool, optional): Temporary parameter to control the streamed events format.
                When True, uses the simplified events format. When False, uses the legacy events format for
                backward compatibility. Will be removed in v0.6. Defaults to False.

        Note:
            If neither `api_key` nor `credentials_path` is provided, Google Gen AI will be used by default.
            The `GOOGLE_API_KEY` environment variable will be used for authentication.
        '''
    def set_tools(self, tools: list[LMTool]) -> None:
        """Sets the tools for the Google language model.

        This method sets the tools for the Google language model. Any existing tools will be replaced.

        Args:
            tools (list[LMTool]): The list of tools to be used.

        Raises:
            ValueError: If `response_schema` exists.
        """
    def set_response_schema(self, response_schema: ResponseSchema | None) -> None:
        """Sets the response schema for the Google language model.

        This method sets the response schema for the Google language model. Any existing response schema will be
        replaced.

        Args:
            response_schema (ResponseSchema | None): The response schema to be used.

        Raises:
            ValueError: If `tools` exists.
        """
    data_stores: Incomplete
    def set_data_stores(self, data_stores: list[AttachmentStore]) -> None:
        """Sets the data stores for the Google language model.

        This method sets the data stores for the Google language model. Any existing data stores will be replaced.

        Args:
            data_stores (list[AttachmentStore]): The list of data stores to be used.
        """
