from _typeshed import Incomplete
from anthropic.types import Message as Message
from gllm_core.utils.retry import RetryConfig
from gllm_inference.constants import INVOKER_PROPAGATED_MAX_RETRIES as INVOKER_PROPAGATED_MAX_RETRIES
from gllm_inference.lm_invoker.lm_invoker import BaseLMInvoker as BaseLMInvoker
from gllm_inference.lm_invoker.schema.anthropic import InputType as InputType, Key as Key, OutputType as OutputType
from gllm_inference.output_transformer.output_transformer import BaseOutputTransformer as BaseOutputTransformer
from gllm_inference.schema import Attachment as Attachment, AttachmentType as AttachmentType, BatchStatus as BatchStatus, LMInput as LMInput, LMOutput as LMOutput, LMTool as LMTool, ModelId as ModelId, ModelProvider as ModelProvider, NativeTool as NativeTool, OutputTransformerType as OutputTransformerType, Reasoning as Reasoning, ResponseSchema as ResponseSchema, ThinkingEvent as ThinkingEvent, TokenUsage as TokenUsage, ToolCall as ToolCall, ToolResult as ToolResult
from typing import Any

SUPPORTED_ATTACHMENTS: Incomplete
DEFAULT_MAX_TOKENS: int
DEFAULT_THINKING_BUDGET: int
BATCH_STATUS_MAP: Incomplete

class AnthropicLMInvoker(BaseLMInvoker):
    '''A language model invoker to interact with Anthropic language models.

    Attributes:
        model_id (str): The model ID of the language model.
        model_provider (str): The provider of the language model.
        model_name (str): The name of the language model.
        client (AsyncAnthropic): The Anthropic client instance.
        default_hyperparameters (dict[str, Any]): Default hyperparameters for invoking the model.
        tools (list[Tool]): Tools provided to the model to enable tool calling.
        response_schema (ResponseSchema | None): The schema of the response. If provided, the model will output a
            structured response as defined by the schema. Supports both Pydantic BaseModel and JSON schema dictionary.
        output_analytics (bool): Whether to output the invocation analytics.
        retry_config (RetryConfig): The retry configuration for the language model.
        thinking (bool): Whether to enable thinking. Only allowed for thinking models.
        thinking_budget (int): The tokens allocated for the thinking process. Only allowed for thinking models.
        output_transformer (OutputTransformerType): The type of output transformer to use.

    Basic usage:
        The `AnthropicLMInvoker` can be used as follows:
        ```python
        lm_invoker = AnthropicLMInvoker(model_name="claude-sonnet-4-20250514")
        result = await lm_invoker.invoke("Hi there!")
        ```

    Input types:
        The `AnthropicLMInvoker` supports the following input types: text, image, and document.
        Non-text inputs can be passed as an `Attachment` object with the `user` role.

        Usage example:
        ```python
        text = "What animal is in this image?"
        image = Attachment.from_path("path/to/local/image.png")
        result = await lm_invoker.invoke([text, image])
        ```

    Text output:
        The `AnthropicLMInvoker` generates text outputs by default.
        Text outputs are stored in the `outputs` attribute of the `LMOutput` object and can be accessed
        via the `texts` (all text outputs) or `text` (first text output) properties.

        Output example:
        ```python
        LMOutput(outputs=[LMOutputItem(type="text", output="Hello, there!")])
        ```

    Structured output:
        The `AnthropicLMInvoker` can be configured to generate structured outputs.
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

        lm_invoker = AnthropicLMInvoker(..., response_schema=Animal)  # Using Pydantic BaseModel class
        lm_invoker = AnthropicLMInvoker(..., response_schema=json_schema)  # Using JSON schema dictionary
        ```

        Output example:
        ```python
        # Using Pydantic BaseModel class outputs a Pydantic model
        LMOutput(outputs=[LMOutputItem(type="structured", output=Animal(name="dog", color="white"))])

        # Using JSON schema dictionary outputs a dictionary
        LMOutput(outputs=[LMOutputItem(type="structured", output={"name": "dog", "color": "white"})])
        ```

        Structured output is not compatible with tool calling or thinking.
        When structured output is enabled, streaming is disabled.

    Tool calling:
        The `AnthropicLMInvoker` can be configured to call tools to perform certain tasks.
        This feature can be enabled by providing a list of `Tool` objects to the `tools` parameter.

        Tool calls outputs are stored in the `outputs` attribute of the `LMOutput` object and
        can be accessed via the `tool_calls` property.

        Usage example:
        ```python
        lm_invoker = AnthropicLMInvoker(..., tools=[tool_1, tool_2])
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
        The `AnthropicLMInvoker` can be configured to perform step-by-step thinking process before answering.
        This feature can be enabled by setting the `thinking` parameter to `True`.

        Thinking outputs are stored in the `outputs` attribute of the `LMOutput` object
        and can be accessed via the `thinkings` property.

        Usage example:
        ```python
        lm_invoker = AnthropicLMInvoker(..., thinking=True, thinking_budget=1024)
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
        https://docs.claude.com/en/docs/build-with-claude/extended-thinking#working-with-thinking-budgets.

        Thinking is only available for certain models, starting from Claude Sonnet 3.7.

    Analytics tracking:
        The `AnthropicLMInvoker` can be configured to output additional information about the invocation.
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
        The `AnthropicLMInvoker` supports retry and timeout configuration.
        By default, the max retries is set to 0 and the timeout is set to 30.0 seconds.
        They can be customized by providing a custom `RetryConfig` object to the `retry_config` parameter.

        Retry config examples:
        ```python
        retry_config = RetryConfig(max_retries=0, timeout=None)  # No retry, no timeout
        retry_config = RetryConfig(max_retries=5, timeout=10.0)  # 5 max retries, 10.0 seconds timeout
        ```

        Usage example:
        ```python
        lm_invoker = AnthropicLMInvoker(..., retry_config=retry_config)
        ```

    Batch processing:
        The `AnthropicLMInvoker` supports batch processing, which allows the language model to process multiple
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

        The `AnthropicLMInvoker` also supports the following standalone batch processing operations:

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
    client: Incomplete
    thinking: Incomplete
    thinking_budget: Incomplete
    def __init__(self, model_name: str, api_key: str | None = None, model_kwargs: dict[str, Any] | None = None, default_hyperparameters: dict[str, Any] | None = None, tools: list[LMTool] | None = None, response_schema: ResponseSchema | None = None, output_analytics: bool = False, retry_config: RetryConfig | None = None, thinking: bool = False, thinking_budget: int = ..., output_transformer: OutputTransformerType = ..., simplify_events: bool = False) -> None:
        """Initializes the AnthropicLmInvoker instance.

        Args:
            model_name (str): The name of the Anthropic language model.
            api_key (str | None, optional): The Anthropic API key. Defaults to None, in which case the
                `ANTHROPIC_API_KEY` environment variable will be used.
            model_kwargs (dict[str, Any] | None, optional): Additional keyword arguments for the Anthropic client.
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
            thinking (bool, optional): Whether to enable thinking. Only allowed for thinking models. Defaults to False.
            thinking_budget (int, optional): The tokens allocated for the thinking process. Must be greater than or
                equal to 1024. Only allowed for thinking models. Defaults to DEFAULT_THINKING_BUDGET.
            output_transformer (OutputTransformerType, optional): The type of output transformer to use.
                Defaults to OutputTransformerType.IDENTITY, which returns the output without transformation.
            simplify_events (bool, optional): Temporary parameter to control the streamed events format.
                When True, uses the simplified events format. When False, uses the legacy events format for
                backward compatibility. Will be removed in v0.6. Defaults to False.

        Raises:
            ValueError:
            1. `thinking` is True, but the `thinking_budget` is less than 1024.
            3. `response_schema` is provided, but `tools` or `thinking` are also provided.
        """
    def set_tools(self, tools: list[LMTool]) -> None:
        """Sets the tools for the Anthropic language model.

        This method sets the tools for the Anthropic language model. Any existing tools will be replaced.

        Args:
            tools (list[LMTool]): The list of tools to be used.

        Raises:
            ValueError: If `response_schema` exists.
        """
    def set_response_schema(self, response_schema: ResponseSchema | None) -> None:
        """Sets the response schema for the Anthropic language model.

        This method sets the response schema for the Anthropic language model. Any existing response schema will be
        replaced.

        Args:
            response_schema (ResponseSchema | None): The response schema to be used.

        Raises:
            ValueError: If `tools` exists.
        """
