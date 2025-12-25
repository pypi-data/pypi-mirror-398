from _typeshed import Incomplete
from gllm_core.utils.retry import RetryConfig
from gllm_inference.constants import AZURE_OPENAI_URL_SUFFIX as AZURE_OPENAI_URL_SUFFIX, INVOKER_PROPAGATED_MAX_RETRIES as INVOKER_PROPAGATED_MAX_RETRIES
from gllm_inference.lm_invoker.openai_lm_invoker import OpenAILMInvoker as OpenAILMInvoker, ReasoningEffort as ReasoningEffort, ReasoningSummary as ReasoningSummary
from gllm_inference.lm_invoker.schema.openai import Key as Key
from gllm_inference.schema import LMTool as LMTool, ModelId as ModelId, ModelProvider as ModelProvider, OutputTransformerType as OutputTransformerType, ResponseSchema as ResponseSchema
from typing import Any

class AzureOpenAILMInvoker(OpenAILMInvoker):
    '''A language model invoker to interact with Azure OpenAI language models.

    Attributes:
        model_id (str): The model ID of the language model.
        model_provider (str): The provider of the language model.
        model_name (str): The name of the Azure OpenAI language model deployment.
        client_kwargs (dict[str, Any]): The keyword arguments for the Azure OpenAI client.
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
        mcp_servers (list[MCPServer]): The list of MCP servers to enable MCP tool calling.
        code_interpreter (bool): Whether to enable the code interpreter. Currently not supported.
        web_search (bool): Whether to enable the web search. Currently not supported.
        output_transformer (OutputTransformerType): The type of output transformer to use.

    Basic usage:
        The `AzureOpenAILMInvoker` can be used as follows:
        ```python
        lm_invoker = AzureOpenAILMInvoker(
            azure_endpoint="https://<your-azure-openai-endpoint>.openai.azure.com/openai/v1",
            azure_deployment="<your-azure-openai-deployment>",
        )
        result = await lm_invoker.invoke("Hi there!")
        ```

    Input types:
        The `AzureOpenAILMInvoker` supports the following input types: text, document, and image.
        Non-text inputs can be passed as an `Attachment` object with the `user` role.

        Usage example:
        ```python
        text = "What animal is in this image?"
        image = Attachment.from_path("path/to/local/image.png")
        result = await lm_invoker.invoke([text, image])
        ```

    Text output:
        The `AzureOpenAILMInvoker` generates text outputs by default.
        Text outputs are stored in the `outputs` attribute of the `LMOutput` object and can be accessed
        via the `texts` (all text outputs) or `text` (first text output) properties.

        Output example:
        ```python
        LMOutput(outputs=[LMOutputItem(type="text", output="Hello, there!")])
        ```

    Structured output:
        The `AzureOpenAILMInvoker` can be configured to generate structured outputs.
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

        lm_invoker = AzureOpenAILMInvoker(..., response_schema=Animal)  # Using Pydantic BaseModel class
        lm_invoker = AzureOpenAILMInvoker(..., response_schema=json_schema)  # Using JSON schema dictionary
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
        The `AzureOpenAILMInvoker` can be configured to call tools to perform certain tasks.
        This feature can be enabled by providing a list of `Tool` objects to the `tools` parameter.

        Tool calls outputs are stored in the `outputs` attribute of the `LMOutput` object and
        can be accessed via the `tool_calls` property.

        Usage example:
        ```python
        lm_invoker = AzureOpenAILMInvoker(..., tools=[tool_1, tool_2])
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
        The `AzureOpenAILMInvoker` performs step-by-step reasoning before generating a response when reasoning
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
        lm_invoker = AzureOpenAILMInvoker(..., reasoning_effort="high", reasoning_summary="detailed")
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

    Analytics tracking:
        The `AzureOpenAILMInvoker` can be configured to output additional information about the invocation.
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
        The `AzureOpenAILMInvoker` supports retry and timeout configuration.
        By default, the max retries is set to 0 and the timeout is set to 30.0 seconds.
        They can be customized by providing a custom `RetryConfig` object to the `retry_config` parameter.

        Retry config examples:
        ```python
        retry_config = RetryConfig(max_retries=0, timeout=None)  # No retry, no timeout
        retry_config = RetryConfig(max_retries=5, timeout=10.0)  # 5 max retries, 10.0 seconds timeout
        ```

        Usage example:
        ```python
        lm_invoker = AzureOpenAILMInvoker(..., retry_config=retry_config)
        ```
    '''
    client_kwargs: Incomplete
    def __init__(self, azure_endpoint: str, azure_deployment: str, api_key: str | None = None, api_version: str | None = None, model_kwargs: dict[str, Any] | None = None, default_hyperparameters: dict[str, Any] | None = None, tools: list[LMTool] | None = None, response_schema: ResponseSchema | None = None, output_analytics: bool = False, retry_config: RetryConfig | None = None, reasoning_effort: ReasoningEffort | None = None, reasoning_summary: ReasoningSummary | None = None, output_transformer: OutputTransformerType = ..., simplify_events: bool = False) -> None:
        """Initializes a new instance of the AzureOpenAILMInvoker class.

        Args:
            azure_endpoint (str): The endpoint of the Azure OpenAI service.
            azure_deployment (str): The deployment name of the Azure OpenAI service.
            api_key (str | None, optional): The API key for authenticating with Azure OpenAI. Defaults to None, in
                which case the `AZURE_OPENAI_API_KEY` environment variable will be used.
            api_version (str | None, optional): Deprecated parameter to be removed in v0.6. Defaults to None.
            model_kwargs (dict[str, Any] | None, optional): Additional model parameters. Defaults to None.
            default_hyperparameters (dict[str, Any] | None, optional): Default hyperparameters for invoking the model.
                Defaults to None, in which case an empty dictionary is used.
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
            output_transformer (OutputTransformerType, optional): The type of output transformer to use.
                Defaults to OutputTransformerType.IDENTITY, which returns the output without transformation.
            simplify_events (bool, optional): Temporary parameter to control the streamed events format.
                When True, uses the simplified events format. When False, uses the legacy events format for
                backward compatibility. Will be removed in v0.6. Defaults to False.

        Raises:
            ValueError:
            1. `reasoning_effort` is provided, but is not a valid ReasoningEffort.
            2. `reasoning_summary` is provided, but is not a valid ReasoningSummary.
        """
