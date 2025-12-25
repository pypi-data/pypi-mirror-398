from _typeshed import Incomplete
from gllm_core.utils import RetryConfig
from gllm_inference.constants import INVOKER_PROPAGATED_MAX_RETRIES as INVOKER_PROPAGATED_MAX_RETRIES, OPENAI_DEFAULT_URL as OPENAI_DEFAULT_URL
from gllm_inference.exceptions import BaseInvokerError as BaseInvokerError, convert_to_base_invoker_error as convert_to_base_invoker_error
from gllm_inference.exceptions.provider_error_map import OPENAI_MESSAGE_MAPPING as OPENAI_MESSAGE_MAPPING, OPENAI_RESPONSE_DETAIL_MAPPING as OPENAI_RESPONSE_DETAIL_MAPPING
from gllm_inference.lm_invoker.lm_invoker import BaseLMInvoker as BaseLMInvoker
from gllm_inference.lm_invoker.schema.openai import InputType as InputType, Key as Key, OpenAIBatchStatus as OpenAIBatchStatus, OutputType as OutputType, ReasoningEffort as ReasoningEffort, ReasoningSummary as ReasoningSummary
from gllm_inference.output_transformer.output_transformer import BaseOutputTransformer as BaseOutputTransformer
from gllm_inference.schema import ActivityEvent as ActivityEvent, Attachment as Attachment, AttachmentType as AttachmentType, BatchStatus as BatchStatus, CodeEvent as CodeEvent, CodeExecResult as CodeExecResult, LMOutput as LMOutput, LMTool as LMTool, MCPCall as MCPCall, MCPCallActivity as MCPCallActivity, MCPListToolsActivity as MCPListToolsActivity, MCPServer as MCPServer, Message as Message, MessageContent as MessageContent, MessageRole as MessageRole, ModelId as ModelId, ModelProvider as ModelProvider, NativeTool as NativeTool, NativeToolType as NativeToolType, OutputTransformerType as OutputTransformerType, Reasoning as Reasoning, ResponseSchema as ResponseSchema, ThinkingEvent as ThinkingEvent, TokenUsage as TokenUsage, ToolCall as ToolCall, ToolResult as ToolResult, WebSearchActivity as WebSearchActivity
from gllm_inference.utils.validation import validate_enum as validate_enum
from typing import Any

BATCH_STATUS_MAP: Incomplete
OPENAI_RESPONSES_API_ENDPOINT: str
DEFAULT_BATCH_COMPLETION_WINDOW: str
SUPPORTED_ATTACHMENTS: Incomplete
STREAM_DATA_START_TYPE_MAP: Incomplete
STREAM_DATA_END_TYPE_MAP: Incomplete
STREAM_DATA_CONTENT_TYPE_MAP: Incomplete

class OpenAILMInvoker(BaseLMInvoker):
    '''A language model invoker to interact with OpenAI language models.

    This class provides support for OpenAI\'s Responses API schema, which is recommended by OpenAI as the preferred API
    to use whenever possible. Use this class unless you have a specific reason to use the Chat Completions API instead.
    The Chat Completions API schema is supported through the `OpenAIChatCompletionsLMInvoker` class.

    Attributes:
        model_id (str): The model ID of the language model.
        model_provider (str): The provider of the language model.
        model_name (str): The name of the language model.
        client_kwargs (dict[str, Any]): The keyword arguments for the OpenAI client.
        default_hyperparameters (dict[str, Any]): Default hyperparameters for invoking the model.
        tools (list[Tool]): The list of tools provided to the model to enable tool calling.
        response_schema (ResponseSchema | None): The schema of the response. If provided, the model will output a
            structured response as defined by the schema. Supports both Pydantic BaseModel and JSON schema dictionary.
        output_analytics (bool): Whether to output the invocation analytics.
        retry_config (RetryConfig): The retry configuration for the language model.
        reasoning_effort (ReasoningEffort | None): The reasoning effort for reasoning models. Not allowed
            for non-reasoning models. If None, the model will perform medium reasoning effort.
        reasoning_summary (ReasoningSummary | None): The reasoning summary level for reasoning models. Not allowed
            for non-reasoning models. If None, no summary will be generated.
        image_generation (bool): Whether to enable image generation.
        mcp_servers (list[MCPServer]): The list of MCP servers to enable MCP tool calling.
        code_interpreter (bool): Whether to enable the code interpreter.
        web_search (bool): Whether to enable the web search.
        output_transformer (OutputTransformerType): The type of output transformer to use.

    Basic usage:
        The `OpenAILMInvoker` can be used as follows:
        ```python
        lm_invoker = OpenAILMInvoker(model_name="gpt-5-nano")
        result = await lm_invoker.invoke("Hi there!")
        ```

    OpenAI compatible endpoints:
        The `OpenAILMInvoker` can also be used to interact with endpoints that are compatible with
        OpenAI\'s Responses API schema. This includes but are not limited to:
        1. SGLang (https://github.com/sgl-project/sglang)
        Please note that the supported features and capabilities may vary between different endpoints and
        language models. Using features that are not supported by the endpoint will result in an error.

        This customization can be done by setting the `base_url` parameter to the base URL of the endpoint:
        ```python
        lm_invoker = OpenAILMInvoker(
            model_name="<model-name>",
            api_key="<your-api-key>",
            base_url="<https://base-url>",
        )
        result = await lm_invoker.invoke("Hi there!")
        ```

    Input types:
        The `OpenAILMInvoker` supports the following input types: text, document, and image.
        Non-text inputs can be passed as an `Attachment` object with the `user` role.

        Usage example:
        ```python
        text = "What animal is in this image?"
        image = Attachment.from_path("path/to/local/image.png")
        result = await lm_invoker.invoke([text, image])
        ```

    Text output:
        The `OpenAILMInvoker` generates text outputs by default.
        Text outputs are stored in the `outputs` attribute of the `LMOutput` object and can be accessed
        via the `texts` (all text outputs) or `text` (first text output) properties.

        Output example:
        ```python
        LMOutput(outputs=[LMOutputItem(type="text", output="Hello, there!")])
        ```

    Structured output:
        The `OpenAILMInvoker` can be configured to generate structured outputs.
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

        lm_invoker = OpenAILMInvoker(..., response_schema=Animal)  # Using Pydantic BaseModel class
        lm_invoker = OpenAILMInvoker(..., response_schema=json_schema)  # Using JSON schema dictionary
        ```

        Output example:
        ```python
        # Using Pydantic BaseModel class outputs a Pydantic model
        LMOutput(outputs=[LMOutputItem(type="structured", output=Animal(name="dog", color="white"))])

        # Using JSON schema dictionary outputs a dictionary
        LMOutput(outputs=[LMOutputItem(type="structured", output={"name": "dog", "color": "white"})])
        ```

        When structured output is enabled, streaming is disabled.

    Image generation:
        The `OpenAILMInvoker` can be configured to generate images.
        This feature can be enabled by setting the `image_generation` parameter to `True`.

        Image outputs are stored in the `outputs` attribute of the `LMOutput` object and can be accessed
        via the `attachments` property.

        Usage example:
        ```python
        lm_invoker = OpenAILMInvoker(..., image_generation=True)
        result = await lm_invoker.invoke("Create a picture...")
        result.attachments[0].write_to_file("path/to/local/image.png")
        ```

        Output example:
        ```python
        LMOutput(
            outputs=[
                LMOutputItem(
                    type="attachment",
                    output=Attachment(filename="image.png", mime_type="image/png", data=b"..."),
                ),
            ],
        )
        ```

        When image generation is enabled, streaming is disabled.
        Image generation is only available for certain models.

    Tool calling:
        The `OpenAILMInvoker` can be configured to call tools to perform certain tasks.
        This feature can be enabled by providing a list of `Tool` objects to the `tools` parameter.

        Tool calls outputs are stored in the `outputs` attribute of the `LMOutput` object and
        can be accessed via the `tool_calls` property.

        Usage example:
        ```python
        lm_invoker = OpenAILMInvoker(..., tools=[tool_1, tool_2])
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

    MCP tool calling:
        The `OpenAILMInvoker` can be configured to call MCP tools to perform certain tasks.
        This feature can be enabled by providing a list of MCP servers to the `mcp_servers` parameter.

        MCP calls outputs are stored in the `outputs` attribute of the `LMOutput` object and
        can be accessed via the `mcp_calls` property.

        Usage example:
        ```python
        from gllm_inference.schema import MCPServer

        mcp_server_1 = MCPServer(url="https://mcp_server_1.com", name="mcp_server_1")
        lm_invoker = OpenAILMInvoker(..., mcp_servers=[mcp_server_1])
        ```

        Output example:
        ```python
        LMOutput(
            outputs=[
                LMOutputItem(type="text", output="I\'m using MCP tools..."),
                LMOutputItem(
                    type="mcp_call",
                    output=MCPCall(
                        id="123",
                        server_name="mcp_server_1",
                        tool_name="mcp_tool_1",
                        args={"key": "value"},
                        output="The result is 10."
                    ),
                ),
            ],
        )
        ```

        Streaming output example:
        ```python
        {"type": "activity", "value": {"type": "mcp_list_tools", ...}, ...}
        {"type": "activity", "value": {"type": "mcp_call", ...}, ...}
        {"type": "response", "value": "The result ", ...}
        {"type": "response", "value": "is 10.", ...}
        ```
        Note: By default, the activity token will be streamed with the legacy `data` event type.
        To use the new simplified streamed event format, set the `simplify_events` parameter to `True` during
        LM invoker initialization. The legacy event format support will be removed in v0.6.

    Reasoning:
        The `OpenAILMInvoker` performs step-by-step reasoning before generating a response when reasoning
        models are used, such as GPT-5 models and o-series models.

        The reasoning effort can be set via the `reasoning_effort` parameter, which guides the models on the amount
        of reasoning tokens to generate. Available options include `minimal`, `low`, `medium`, and `high`.

        While the raw reasoning tokens are not available, the summary of the reasoning tokens can still be generated.
        This can be done by passing the desired summary level via the `reasoning_summary` parameter.
        Available options include `auto` and `detailed`.

        Reasoning summaries are stored in the `outputs` attribute of the `LMOutput` object
        and can be accessed via the `thinkings` property.

        Usage example:
        ```python
        lm_invoker = OpenAILMInvoker(..., reasoning_effort="high", reasoning_summary="detailed")
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

        Reasoning summary is not compatible with tool calling.

    Code interpreter:
        The `OpenAILMInvoker` can be configured to write and run Python code in a sandboxed environment.
        This is useful for solving complex problems in domains like data analysis, coding, and math.
        This feature can be enabled by adding code interpreter as a native tool in the `tools` parameter.

        When code interpreter is enabled, it is highly recommended to instruct the model to use the "python tool"
        in the system message, as "python tool" is the term recognized by the model to refer to the code interpreter.

        Code execution results are stored in the `outputs` attribute of the `LMOutput` object and
        can be accessed via the `code_exec_results` property.

        Usage example:
        ```python
        lm_invoker = OpenAILMInvoker(..., tools=[..., "code_interpreter"])
        messages = [
            Message.system("You are a data analyst. Use the python tool to generate a file."]),
            Message.user("Show an histogram of the following data: [1, 2, 1, 4, 1, 2, 4, 2, 3, 1]"),
        ]
        result = await lm_invoker.invoke(messages)
        ```

        Output example:
        ```python
        LMOutput(
            outputs=[
                LMOutputItem(type="text", output="The histogram is attached."),
                LMOutputItem(
                    type="code_exec_result",
                    output=CodeExecResult(
                        id="123",
                        code="import matplotlib.pyplot as plt...",
                        output=[Attachment(data=b"...", mime_type="image/png")],
                    ),
                ),
            ],
        )
        ```

        Streaming output example:
        ```python
        {"type": "code_start", "value": ""}\', ...}
        {"type": "code", "value": "import matplotlib"}\', ...}
        {"type": "code", "value": ".pyplot as plt..."}\', ...}
        {"type": "code_end", "value": ""}\', ...}
        {"type": "response", "value": "The histogram ", ...}
        {"type": "response", "value": "is attached.", ...}
        ```
        Note: By default, the code token will be streamed with the legacy `data` event type.
        To use the new simplified streamed event format, set the `simplify_events` parameter to `True` during
        LM invoker initialization. The legacy event format support will be removed in v0.6.

    Web Search:
        The `OpenAILMInvoker` can be configured to search the web for relevant information.
        This feature can be enabled by setting the `web_search` parameter to `True`.

        Web search citations are stored in the `outputs` attribute of the `LMOutput` object and
        can be accessed via the `citations` property.

        Usage example:
        ```python
        lm_invoker = OpenAILMInvoker(..., web_search=True)
        ```

        Output example:
        ```python
        LMOutput(
            outputs=[
                LMOutputItem(type="citation", output=Chunk(id="123", content="...", metadata={...}, score=None)),
                LMOutputItem(type="text", output="According to recent reports... ([Source](https://example.com))."),
            ],
        )
        ```

        Streaming output example:
        ```python
        {"type": "activity", "value": {"query": "search query"}, ...}
        {"type": "response", "value": "According to recent ", ...}
        {"type": "response", "value": "reports... ([Source](https://example.com)).", ...}
        ```
        Note: By default, the activity token will be streamed with the legacy `data` event type.
        To use the new simplified streamed event format, set the `simplify_events` parameter to `True` during
        LM invoker initialization. The legacy event format support will be removed in v0.6.

    Analytics tracking:
        The `OpenAILMInvoker` can be configured to output additional information about the invocation.
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
        The `OpenAILMInvoker` supports retry and timeout configuration.
        By default, the max retries is set to 0 and the timeout is set to 30.0 seconds.
        They can be customized by providing a custom `RetryConfig` object to the `retry_config` parameter.

        Retry config examples:
        ```python
        retry_config = RetryConfig(max_retries=0, timeout=None)  # No retry, no timeout
        retry_config = RetryConfig(max_retries=5, timeout=10.0)  # 5 max retries, 10.0 seconds timeout
        ```

        Usage example:
        ```python
        lm_invoker = OpenAILMInvoker(..., retry_config=retry_config)
        ```

    Batch processing:
        The `OpenAILMInvoker` supports batch processing, which allows the language model to process multiple
        requests in a single call. Batch processing is supported through the `batch` attribute.

        Usage example:
        ```python
        requests = {"request_1": "What color is the sky?", "request_2": "What color is the grass?"}
        results = await lm_invoker.batch.invoke(requests)
        ```

        Output example:
        ```python
        {
            "request_1": LMOutput(outputs=[LMOutputItem(type="text", output="The sky is blue.")]),
            "request_2": LMOutput(finish_details={"type": "error", "error": {"message": "...", ...}, ...}),
        }
        ```

        The `OpenAILMInvoker` also supports the following standalone batch processing operations:

          1. Create a batch job:
            ```python
            requests = {"request_1": "What color is the sky?", "request_2": "What color is the grass?"}
            batch_id = await lm_invoker.batch.create(requests)
            ```
        2. Get the status of a batch job:
            ```python
            status = await lm_invoker.batch.status(batch_id)
            ```
        3. Retrieve the results of a batch job:
            Results are keyed by the request indices provided during batch creation.

            ```python
            results = await lm_invoker.batch.retrieve(batch_id)
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
    '''
    client_kwargs: Incomplete
    def __init__(self, model_name: str, api_key: str | None = None, base_url: str = ..., model_kwargs: dict[str, Any] | None = None, default_hyperparameters: dict[str, Any] | None = None, tools: list[LMTool] | None = None, response_schema: ResponseSchema | None = None, output_analytics: bool = False, retry_config: RetryConfig | None = None, reasoning_effort: ReasoningEffort | None = None, reasoning_summary: ReasoningSummary | None = None, image_generation: bool = False, mcp_servers: list[MCPServer] | None = None, code_interpreter: bool = False, web_search: bool = False, output_transformer: OutputTransformerType = ..., simplify_events: bool = False) -> None:
        '''Initializes a new instance of the OpenAILMInvoker class.

        Args:
            model_name (str): The name of the OpenAI model.
            api_key (str | None, optional): The API key for authenticating with OpenAI. Defaults to None, in which
                case the `OPENAI_API_KEY` environment variable will be used. If the endpoint does not require an
                API key, a dummy value can be passed (e.g. "<empty>").
            base_url (str, optional): The base URL of a custom endpoint that is compatible with OpenAI\'s
                Responses API schema. Defaults to OpenAI\'s default URL.
            model_kwargs (dict[str, Any] | None, optional): Additional model parameters. Defaults to None.
            default_hyperparameters (dict[str, Any] | None, optional): Default hyperparameters for invoking the model.
                Defaults to None.
            tools (list[LMTool] | None, optional): Tools provided to the model to enable tool calling.
                Defaults to None, in which case an empty list is used.
            response_schema (ResponseSchema | None, optional): The schema of the response. If provided, the model will
                output a structured response as defined by the schema. Supports both Pydantic BaseModel and JSON schema
                dictionary. Defaults to None.
            output_analytics (bool, optional): Whether to output the invocation analytics. Defaults to False.
            retry_config (RetryConfig | None, optional): The retry configuration for the language model.
                Defaults to None, in which case a default config with no retry and 30.0 seconds timeout will be used.
            reasoning_effort (ReasoningEffort | None, optional): The reasoning effort for reasoning models. Not allowed
                for non-reasoning models. If None, the model will perform medium reasoning effort. Defaults to None.
            reasoning_summary (ReasoningSummary | None, optional): The reasoning summary level for reasoning models.
                Not allowed for non-reasoning models. If None, no summary will be generated. Defaults to None.
            image_generation (bool, optional): Whether to enable image generation. Defaults to False.
            mcp_servers (list[MCPServer] | None, optional): The MCP servers containing tools to be accessed by the
                language model. Defaults to None.
            code_interpreter (bool, optional): Whether to enable the code interpreter. Defaults to False.
            web_search (bool, optional): Whether to enable the web search. Defaults to False.
            output_transformer (OutputTransformerType, optional): The type of output transformer to use.
                Defaults to OutputTransformerType.IDENTITY, which returns the output without transformation.
            simplify_events (bool, optional): Temporary parameter to control the streamed events format.
                When True, uses the simplified events format. When False, uses the legacy events format for
                backward compatibility. Will be removed in v0.6. Defaults to False.

        Raises:
            ValueError:
            1. `reasoning_effort` is provided, but is not a valid ReasoningEffort.
            2. `reasoning_summary` is provided, but is not a valid ReasoningSummary.
        '''
    def set_response_schema(self, response_schema: ResponseSchema | None) -> None:
        """Sets the response schema for the OpenAI language model.

        This method sets the response schema for the OpenAI language model. Any existing response schema will be
        replaced.

        Args:
            response_schema (ResponseSchema | None): The response schema to be used.
        """
