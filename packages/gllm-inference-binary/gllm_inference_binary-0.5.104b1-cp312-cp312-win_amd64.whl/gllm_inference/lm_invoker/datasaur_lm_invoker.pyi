from _typeshed import Incomplete
from gllm_core.utils.retry import RetryConfig
from gllm_inference.constants import INVOKER_PROPAGATED_MAX_RETRIES as INVOKER_PROPAGATED_MAX_RETRIES
from gllm_inference.lm_invoker.openai_chat_completions_lm_invoker import OpenAIChatCompletionsLMInvoker as OpenAIChatCompletionsLMInvoker
from gllm_inference.lm_invoker.schema.datasaur import InputType as InputType, Key as Key
from gllm_inference.output_transformer.output_transformer import BaseOutputTransformer as BaseOutputTransformer
from gllm_inference.schema import Attachment as Attachment, AttachmentType as AttachmentType, LMOutput as LMOutput, LMTool as LMTool, Message as Message, ModelId as ModelId, ModelProvider as ModelProvider, OutputTransformerType as OutputTransformerType, ResponseSchema as ResponseSchema, StreamBuffer as StreamBuffer, StreamBufferType as StreamBufferType, ToolCall as ToolCall, ToolResult as ToolResult
from typing import Any

SUPPORTED_ATTACHMENTS: Incomplete
TOOL_CALLING_NOT_SUPPORTED_MESSAGE: str

class DatasaurLMInvoker(OpenAIChatCompletionsLMInvoker):
    '''A language model invoker to interact with Datasaur LLM Projects Deployment API.

    Attributes:
        model_id (str): The model ID of the language model.
        model_provider (str): The provider of the language model.
        model_name (str): The name of the language model.
        client_kwargs (dict[str, Any]): The keyword arguments for the OpenAI client.
        default_hyperparameters (dict[str, Any]): Default hyperparameters for invoking the model.
        tools (list[Any]): The list of tools provided to the model to enable tool calling. Currently not supported.
        response_schema (ResponseSchema | None): The schema of the response. Currently not supported.
        output_analytics (bool): Whether to output the invocation analytics.
        retry_config (RetryConfig | None): The retry configuration for the language model.
        citations (bool): Whether to output the citations.
        output_transformer (OutputTransformerType): The type of output transformer to use.

    Basic usage:
        The `DatasaurLMInvoker` can be used as follows:
        ```python
        lm_invoker = DatasaurLMInvoker(base_url="https://deployment.datasaur.ai/api/deployment/teamId/deploymentId/")
        result = await lm_invoker.invoke("Hi there!")
        ```

    Input types:
        The `DatasaurLMInvoker` supports the following input types: text, audio, image, and document.
        Non-text inputs can be passed as an `Attachment` object with the `user` role.

        Usage example:
        ```python
        text = "What animal is in this image?"
        image = Attachment.from_path("path/to/local/image.png")
        result = await lm_invoker.invoke([text, image])
        ```

    Text output:
        The `DatasaurLMInvoker` generates text outputs by default.
        Text outputs are stored in the `outputs` attribute of the `LMOutput` object and can be accessed
        via the `texts` (all text outputs) or `text` (first text output) properties.

        Output example:
        ```python
        LMOutput(outputs=[LMOutputItem(type="text", output="Hello, there!")])
        ```

    Citations:
        The `DatasaurLMInvoker` can be configured to output the citations used to generate the response.
        This feature can be enabled by setting the `citations` parameter to `True`.

        Citations outputs are stored in the `outputs` attribute of the `LMOutput` object and
        can be accessed via the `citations` property.

        Usage example:
        ```python
        lm_invoker = DatasaurLMInvoker(..., citations=True)
        ```

        Output example:
        ```python
        LMOutput(
            outputs=[
                LMOutputItem(type="citation", output=Chunk(id="123", content="...", metadata={...}, score=0.95)),
                LMOutputItem(type="text", output="According to recent reports... ([Source](https://www.example.com))."),
            ],
        )
        ```

    Analytics tracking:
        The `DatasaurLMInvoker` can be configured to output additional information about the invocation.
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
        The `DatasaurLMInvoker` supports retry and timeout configuration.
        By default, the max retries is set to 0 and the timeout is set to 30.0 seconds.
        They can be customized by providing a custom `RetryConfig` object to the `retry_config` parameter.

        Retry config examples:
        ```python
        retry_config = RetryConfig(max_retries=0, timeout=None)  # No retry, no timeout
        retry_config = RetryConfig(max_retries=5, timeout=10.0)  # 5 max retries, 10.0 seconds timeout
        ```

        Usage example:
        ```python
        lm_invoker = DatasaurLMInvoker(..., retry_config=retry_config)
        ```
    '''
    client_kwargs: Incomplete
    citations: Incomplete
    def __init__(self, base_url: str, api_key: str | None = None, model_kwargs: dict[str, Any] | None = None, default_hyperparameters: dict[str, Any] | None = None, output_analytics: bool = False, retry_config: RetryConfig | None = None, citations: bool = False, output_transformer: OutputTransformerType = ...) -> None:
        """Initializes a new instance of the DatasaurLMInvoker class.

        Args:
            base_url (str): The base URL of the Datasaur LLM Projects Deployment API.
            api_key (str | None, optional): The API key for authenticating with Datasaur LLM Projects Deployment API.
                Defaults to None, in which case the `DATASAUR_API_KEY` environment variable will be used.
            model_kwargs (dict[str, Any] | None, optional): Additional model parameters. Defaults to None.
            default_hyperparameters (dict[str, Any] | None, optional): Default hyperparameters for invoking the model.
                Defaults to None.
            output_analytics (bool, optional): Whether to output the invocation analytics. Defaults to False.
            retry_config (RetryConfig | None, optional): The retry configuration for the language model.
                Defaults to None, in which case a default config with no retry and 30.0 seconds timeout will be used.
            citations (bool, optional): Whether to output the citations. Defaults to False.
            output_transformer (OutputTransformerType, optional): The type of output transformer to use.
                Defaults to OutputTransformerType.IDENTITY, which returns the output without transformation.

        Raises:
            ValueError: If the `api_key` is not provided and the `DATASAUR_API_KEY` environment variable is not set.
        """
    def set_tools(self, tools: list[LMTool]) -> None:
        """Sets the tools for the Datasaur LLM Projects Deployment API.

        This method is raises a `NotImplementedError` because the Datasaur LLM Projects Deployment API does not
        support tools.

        Args:
            tools (list[LMTool]): The list of tools to be used.

        Raises:
            NotImplementedError: This method is not supported for the Datasaur LLM Projects Deployment API.
        """
    def set_response_schema(self, response_schema: ResponseSchema | None) -> None:
        """Sets the response schema for the Datasaur LLM Projects Deployment API.

        This method is raises a `NotImplementedError` because the Datasaur LLM Projects Deployment API does not
        support response schema.

        Args:
            response_schema (ResponseSchema | None): The response schema to be used.

        Raises:
            NotImplementedError: This method is not supported for the Datasaur LLM Projects Deployment API.
        """
