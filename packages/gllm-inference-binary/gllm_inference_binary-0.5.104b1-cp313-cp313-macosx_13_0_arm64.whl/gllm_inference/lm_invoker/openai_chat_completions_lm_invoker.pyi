from _typeshed import Incomplete
from gllm_core.utils import RetryConfig
from gllm_inference.constants import INVOKER_PROPAGATED_MAX_RETRIES as INVOKER_PROPAGATED_MAX_RETRIES, OPENAI_DEFAULT_URL as OPENAI_DEFAULT_URL
from gllm_inference.lm_invoker.lm_invoker import BaseLMInvoker as BaseLMInvoker
from gllm_inference.lm_invoker.schema.openai_chat_completions import InputType as InputType, Key as Key, ReasoningEffort as ReasoningEffort
from gllm_inference.output_transformer.output_transformer import BaseOutputTransformer as BaseOutputTransformer
from gllm_inference.schema import Attachment as Attachment, AttachmentType as AttachmentType, LMOutput as LMOutput, LMTool as LMTool, Message as Message, MessageRole as MessageRole, ModelId as ModelId, ModelProvider as ModelProvider, NativeTool as NativeTool, OutputTransformerType as OutputTransformerType, Reasoning as Reasoning, ResponseSchema as ResponseSchema, StreamBuffer as StreamBuffer, StreamBufferType as StreamBufferType, ThinkingEvent as ThinkingEvent, TokenUsage as TokenUsage, ToolCall as ToolCall, ToolResult as ToolResult
from gllm_inference.utils.validation import validate_enum as validate_enum
from typing import Any

SUPPORTED_ATTACHMENTS: Incomplete
MESSAGE_ATTR_MAP: Incomplete

class OpenAIChatCompletionsLMInvoker(BaseLMInvoker):
    '''A language model invoker to interact with OpenAI language models using the Chat Completions API.

    This class provides support for OpenAI\'s Chat Completions API schema. Use this class only when you have
    a specific reason to use the Chat Completions API over the Responses API, as OpenAI recommends using
    the Responses API whenever possible. The Responses API schema is supported through the `OpenAILMInvoker` class.

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
        retry_config (RetryConfig | None): The retry configuration for the language model.
        output_transformer (OutputTransformerType): The type of output transformer to use.

    Basic usage:
        The `OpenAIChatCompletionsLMInvoker` can be used as follows:
        ```python
        lm_invoker = OpenAIChatCompletionsLMInvoker(model_name="gpt-5-nano")
        result = await lm_invoker.invoke("Hi there!")
        ```

    OpenAI compatible endpoints:
        The `OpenAIChatCompletionsLMInvoker` can also be used to interact with endpoints that are compatible with
        OpenAI\'s Chat Completions API schema. This includes but are not limited to:
        1. DeepInfra (https://deepinfra.com/)
        2. DeepSeek (https://deepseek.com/)
        3. Groq (https://groq.com/)
        4. OpenRouter (https://openrouter.ai/)
        5. Text Generation Inference (https://github.com/huggingface/text-generation-inference)
        6. Together.ai (https://together.ai/)
        7. vLLM (https://vllm.ai/)
        Please note that the supported features and capabilities may vary between different endpoints and
        language models. Using features that are not supported by the endpoint will result in an error.

        This customization can be done by setting the `base_url` parameter to the base URL of the endpoint:
        ```python
        lm_invoker = OpenAIChatCompletionsLMInvoker(
            model_name="llama3-8b-8192",
            api_key="<your-api-key>",
            base_url="https://api.groq.com/openai/v1",
        )
        result = await lm_invoker.invoke("Hi there!")
        ```

    Input types:
        The `OpenAIChatCompletionsLMInvoker` supports the following input types: text, audio, document, and image.
        Non-text inputs can be passed as an `Attachment` object with the `user` role.

        Usage example:
        ```python
        text = "What animal is in this image?"
        image = Attachment.from_path("path/to/local/image.png")
        result = await lm_invoker.invoke([text, image])
        ```

    Text output:
        The `OpenAIChatCompletionsLMInvoker` generates text outputs by default.
        Text outputs are stored in the `outputs` attribute of the `LMOutput` object and can be accessed
        via the `texts` (all text outputs) or `text` (first text output) properties.

        Output example:
        ```python
        LMOutput(outputs=[LMOutputItem(type="text", output="Hello, there!")])
        ```

    Structured output:
        The `OpenAIChatCompletionsLMInvoker` can be configured to generate structured outputs.
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

        lm_invoker = OpenAIChatCompletionsLMInvoker(..., response_schema=Animal)  # Using Pydantic BaseModel class
        lm_invoker = OpenAIChatCompletionsLMInvoker(..., response_schema=json_schema)  # Using JSON schema dictionary
        ```

        Output example:
        ```python
        # Using Pydantic BaseModel class outputs a Pydantic model
        LMOutput(outputs=[LMOutputItem(type="structured", output=Animal(name="dog", color="white"))])

        # Using JSON schema dictionary outputs a dictionary
        LMOutput(outputs=[LMOutputItem(type="structured", output={"name": "dog", "color": "white"})])
        ```

        When structured output is enabled, streaming is disabled.

    Tool calling:
        The `OpenAIChatCompletionsLMInvoker` can be configured to call tools to perform certain tasks.
        This feature can be enabled by providing a list of `Tool` objects to the `tools` parameter.

        Tool calls outputs are stored in the `outputs` attribute of the `LMOutput` object and
        can be accessed via the `tool_calls` property.

        Usage example:
        ```python
        lm_invoker = OpenAIChatCompletionsLMInvoker(..., tools=[tool_1, tool_2])
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

    Reasoning:
        The `OpenAILMInvoker` performs step-by-step reasoning before generating a response when reasoning
        models are used, such as GPT-5 models and o-series models.

        The reasoning effort can be set via the `reasoning_effort` parameter, which guides the models on the amount
        of reasoning tokens to generate. Available options include `minimal`, `low`, `medium`, and `high`.

        Some models may also output the reasoning tokens. In this case, the reasoning tokens are stored in
        the `outputs` attribute of the `LMOutput` object and can be accessed via the `thinkings` property.

        Output example:
        ```python
        LMOutput(
            outputs=[
                LMOutputItem(type="thinking", output=Reasoning(reasoning="I\'m thinking...", ...)),
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

        Setting reasoning-related parameters for non-reasoning models will raise an error.

    Analytics tracking:
        The `OpenAIChatCompletionsLMInvoker` can be configured to output additional information about the invocation.
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

        When streaming is enabled, token usage is not supported.

    Retry and timeout:
        The `OpenAIChatCompletionsLMInvoker` supports retry and timeout configuration.
        By default, the max retries is set to 0 and the timeout is set to 30.0 seconds.
        They can be customized by providing a custom `RetryConfig` object to the `retry_config` parameter.

        Retry config examples:
        ```python
        retry_config = RetryConfig(max_retries=0, timeout=None)  # No retry, no timeout
        retry_config = RetryConfig(max_retries=5, timeout=10.0)  # 5 max retries, 10.0 seconds timeout
        ```

        Usage example:
        ```python
        lm_invoker = OpenAIChatCompletionsLMInvoker(..., retry_config=retry_config)
        ```
    '''
    client_kwargs: Incomplete
    def __init__(self, model_name: str, api_key: str | None = None, base_url: str = ..., model_kwargs: dict[str, Any] | None = None, default_hyperparameters: dict[str, Any] | None = None, tools: list[LMTool] | None = None, response_schema: ResponseSchema | None = None, output_analytics: bool = False, retry_config: RetryConfig | None = None, reasoning_effort: ReasoningEffort | None = None, output_transformer: OutputTransformerType = ..., simplify_events: bool = False) -> None:
        '''Initializes a new instance of the OpenAIChatCompletionsLMInvoker class.

        Args:
            model_name (str): The name of the OpenAI model.
            api_key (str | None, optional): The API key for authenticating with OpenAI. Defaults to None, in which
                case the `OPENAI_API_KEY` environment variable will be used. If the endpoint does not require an
                API key, a dummy value can be passed (e.g. "<empty>").
            base_url (str, optional): The base URL of a custom endpoint that is compatible with OpenAI\'s
                Chat Completions API schema. Defaults to OpenAI\'s default URL.
            model_kwargs (dict[str, Any] | None, optional): Additional model parameters. Defaults to None.
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
            reasoning_effort (str | None, optional): The reasoning effort for the language model. Defaults to None.
            output_transformer (OutputTransformerType, optional): The type of output transformer to use.
                Defaults to OutputTransformerType.IDENTITY, which returns the output without transformation.
            simplify_events (bool, optional): Temporary parameter to control the streamed events format.
                When True, uses the simplified events format. When False, uses the legacy events format for
                backward compatibility. Will be removed in v0.6. Defaults to False.
        '''
    def set_response_schema(self, response_schema: ResponseSchema | None) -> None:
        """Sets the response schema for the OpenAI language model.

        This method sets the response schema for the OpenAI language model.
        Any existing response schema will be replaced.

        Args:
            response_schema (ResponseSchema | None): The response schema to be used.
        """
