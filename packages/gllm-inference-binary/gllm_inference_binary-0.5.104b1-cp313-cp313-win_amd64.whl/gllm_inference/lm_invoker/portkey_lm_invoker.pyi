from _typeshed import Incomplete
from gllm_core.utils.retry import RetryConfig
from gllm_inference.constants import SECONDS_TO_MILLISECONDS as SECONDS_TO_MILLISECONDS
from gllm_inference.lm_invoker.openai_chat_completions_lm_invoker import OpenAIChatCompletionsLMInvoker as OpenAIChatCompletionsLMInvoker
from gllm_inference.lm_invoker.schema.portkey import InputType as InputType, Key as Key
from gllm_inference.output_transformer.output_transformer import BaseOutputTransformer as BaseOutputTransformer
from gllm_inference.schema import AttachmentType as AttachmentType, LMOutput as LMOutput, LMTool as LMTool, ModelId as ModelId, ModelProvider as ModelProvider, OutputTransformerType as OutputTransformerType, ResponseSchema as ResponseSchema
from typing import Any

MIN_THINKING_BUDGET: int
SUPPORTED_ATTACHMENTS: Incomplete
VALID_AUTH_METHODS: str
logger: Incomplete

class PortkeyLMInvoker(OpenAIChatCompletionsLMInvoker):
    '''A language model invoker to interact with Portkey\'s Universal API.

    This class provides support for Portkey’s Universal AI Gateway, which enables unified access to
    multiple providers (e.g., OpenAI, Anthropic, Google, Cohere, Bedrock) via a single API key.
    The `PortkeyLMInvoker` is compatible with all Portkey model routing configurations, including
    model catalog entries, direct providers, and pre-defined configs.

    Attributes:
        model_id (str): The model ID of the language model.
        model_provider (str): The provider of the language model.
        model_name (str): The catalog name of the language model.
        client_kwargs (dict[str, Any]): The keyword arguments for the Portkey client.
        default_hyperparameters (dict[str, Any]): Default hyperparameters for invoking the model.
        tools (list[Tool]): The list of tools provided to the model to enable tool calling.
        response_schema (ResponseSchema | None): The schema of the response. If provided, the model will output a
            structured response as defined by the schema. Supports both Pydantic BaseModel and JSON schema dictionary.
        output_analytics (bool): Whether to output the invocation analytics.
        retry_config (RetryConfig): The retry configuration for the language model.
        thinking (bool): Whether to enable thinking mode for supported models.
        thinking_budget (int): The maximum reasoning token budget for thinking mode.
        output_transformer (OutputTransformerType): The type of output transformer to use.

    Basic usage:
        The `PortkeyLMInvoker` supports multiple authentication methods with strict precedence order.
        Authentication methods are mutually exclusive and cannot be combined.

        **Authentication Precedence (Highest to Lowest):**
        1. **Config ID Authentication (Highest precedence)**
           Use a pre-configured routing setup from Portkey’s dashboard.
           ```python
           lm_invoker = PortkeyLMInvoker(
               portkey_api_key="<your-portkey-api-key>",
               config="pc-openai-4f6905",
           )
           ```

        2. **Model Catalog Authentication**
           Provider name must match the provider name set in the model catalog.
           More details to set up the model catalog can be found in https://portkey.ai/docs/product/model-catalog#model-catalog.
           There are two ways to specify the model name:

           2.1. Using Combined Model Name Format
           Specify the `model_name` in \'@provider-name/model-name\' format.
           ```python
           lm_invoker = PortkeyLMInvoker(
               portkey_api_key="<your-portkey-api-key>",
               model_name="@openai-custom/gpt-4o"
           )
           ```

           2.2. Using Separate Provider and Model Name Parameters
           Specify the `provider` in \'@provider-name\' format and `model_name` separately.
           ```python
           lm_invoker = PortkeyLMInvoker(
               portkey_api_key="<your-portkey-api-key>",
               provider="@openai-custom",
               model_name="gpt-4o",
           )
           ```

        3. **Direct Provider Authentication**
           Use the `provider` in \'provider-name\' format and `model_name` parameters.
           ```python
           lm_invoker = PortkeyLMInvoker(
               portkey_api_key="<your-portkey-api-key>",
               provider="openai",
               model_name="gpt-4o",
               api_key="sk-...",
           )
           ```

    Custom Host:
        You can also use the `custom_host` parameter to override the default host. This is available
        for all authentication methods except for Config ID authentication.
        ```python
        lm_invoker = PortkeyLMInvoker(..., custom_host="https://your-custom-endpoint.com")
        ```

    Input types:
        The `PortkeyLMInvoker` supports text, image, document, and audio inputs.
        Non-text inputs can be passed as an `Attachment` object with the `user` role.

        ```python
        text = "What animal is in this image?"
        image = Attachment.from_path("path/to/image.png")
        result = await lm_invoker.invoke([text, image])
        ```

    Text output:
        The `PortkeyLMInvoker` generates text outputs by default.
        Text outputs are stored in the `outputs` attribute of the `LMOutput` object and can be accessed
        via the `texts` (all text outputs) or `text` (first text output) properties.

        Output example:
        ```python
        LMOutput(outputs=[LMOutputItem(type="text", output="Hello, there!")])
        ```

    Structured output:
        The `PortkeyLMInvoker` can be configured to generate structured outputs.
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

        lm_invoker = PortkeyLMInvoker(..., response_schema=Animal)  # Using Pydantic BaseModel class
        lm_invoker = PortkeyLMInvoker(..., response_schema=json_schema)  # Using JSON schema dictionary
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
        The `PortkeyLMInvoker` can be configured to call tools to perform certain tasks.
        This feature can be enabled by providing a list of `Tool` objects to the `tools` parameter.

        Tool calls outputs are stored in the `outputs` attribute of the `LMOutput` object and
        can be accessed via the `tool_calls` property.

        Usage example:
        ```python
        lm_invoker = PortkeyLMInvoker(..., tools=[tool_1, tool_2])
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
        The `PortkeyLMInvoker` can be configured to perform step-by-step thinking process before answering.
        This feature can be enabled by setting the `thinking` parameter to `True`.

        Thinking outputs are stored in the `outputs` attribute of the `LMOutput` object
        and can be accessed via the `thinkings` property.

        Usage example:
        ```python
        lm_invoker = PortkeyLMInvoker(..., thinking=True, thinking_budget=1024)
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
        https://portkey.ai/docs/product/ai-gateway/multimodal-capabilities/thinking-mode.

        Thinking is only available for certain models depending on capabilities

    Analytics tracking:
        The `PortkeyLMInvoker` can be configured to output additional information about the invocation.
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
        The `PortkeyLMInvoker` supports retry and timeout configuration.
        By default, the max retries is set to 0 and the timeout is set to 30.0 seconds.
        They can be customized by providing a custom `RetryConfig` object to the `retry_config` parameter.

        Retry config examples:
        ```python
        retry_config = RetryConfig(max_retries=0, timeout=None)  # No retry, no timeout
        retry_config = RetryConfig(max_retries=5, timeout=10.0)  # 5 max retries, 10.0 seconds timeout
        ```

        Usage example:
        ```python
        lm_invoker = PortkeyLMInvoker(..., retry_config=retry_config)
        ```
    '''
    model_kwargs: Incomplete
    thinking: Incomplete
    thinking_budget: Incomplete
    client_kwargs: Incomplete
    client: Incomplete
    def __init__(self, model_name: str | None = None, portkey_api_key: str | None = None, provider: str | None = None, api_key: str | None = None, config: str | None = None, custom_host: str | None = None, model_kwargs: dict[str, Any] | None = None, default_hyperparameters: dict[str, Any] | None = None, tools: list[LMTool] | None = None, response_schema: ResponseSchema | None = None, output_analytics: bool = False, retry_config: RetryConfig | None = None, thinking: bool | None = None, thinking_budget: int | None = None, output_transformer: OutputTransformerType = ..., simplify_events: bool = False) -> None:
        """Initializes a new instance of the PortkeyLMInvoker class.

        Args:
            model_name (str | None, optional): The name of the model to use. Acceptable formats:
                1. 'model' for direct authentication,
                2. '@provider-slug/model' for model catalog authentication.
                Defaults to None.
            portkey_api_key (str | None, optional): The Portkey API key. Defaults to None, in which
                case the `PORTKEY_API_KEY` environment variable will be used.
            provider (str | None, optional): Provider name or catalog slug. Acceptable formats:
                1. '@provider-slug' for model catalog authentication (no api_key needed),
                2. 'provider' for direct authentication (requires api_key).
                Will be combined with model_name if model name is not in the format '@provider-slug/model'.
                Defaults to None.
            api_key (str | None, optional): Provider's API key for direct authentication.
                Must be used with 'provider' parameter (without '@' prefix). Not needed for catalog providers.
                Defaults to None.
            config (str | None, optional): Portkey config ID for complex routing configurations,
                load balancing, or fallback scenarios. Defaults to None.
            custom_host (str | None, optional): Custom host URL for self-hosted or custom endpoints.
                Can be combined with catalog providers. Defaults to None.
            model_kwargs (dict[str, Any] | None, optional): Additional model parameters and authentication.
                Defaults to None.
            default_hyperparameters (dict[str, Any] | None, optional): Default hyperparameters for model
                invocation (temperature, max_tokens, etc.). Defaults to None.
            tools (list[LMTool] | None, optional): Tools for enabling tool calling functionality.
                Defaults to None.
            response_schema (ResponseSchema | None, optional): Schema for structured output generation.
                Defaults to None.
            output_analytics (bool, optional): Whether to output detailed invocation analytics including
                token usage and timing. Defaults to False.
            retry_config (RetryConfig | None, optional): Configuration for retry behavior on failures.
                Defaults to None.
            thinking (bool | None, optional): Whether to enable thinking mode. Defaults to None.
            thinking_budget (int | None, optional): Thinking budget in tokens. Defaults to None.
            output_transformer (OutputTransformerType, optional): The type of output transformer to use.
                Defaults to OutputTransformerType.IDENTITY, which returns the output without transformation.
            simplify_events (bool, optional): Whether to use simplified event schemas. Defaults to False.
        """
