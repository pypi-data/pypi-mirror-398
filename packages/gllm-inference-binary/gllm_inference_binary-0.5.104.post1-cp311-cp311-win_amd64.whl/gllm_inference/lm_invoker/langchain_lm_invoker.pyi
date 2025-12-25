from _typeshed import Incomplete
from gllm_core.utils.retry import RetryConfig
from gllm_inference.constants import INVOKER_DEFAULT_TIMEOUT as INVOKER_DEFAULT_TIMEOUT, INVOKER_PROPAGATED_MAX_RETRIES as INVOKER_PROPAGATED_MAX_RETRIES
from gllm_inference.exceptions import BaseInvokerError as BaseInvokerError, convert_to_base_invoker_error as convert_to_base_invoker_error
from gllm_inference.exceptions.provider_error_map import LANGCHAIN_ERROR_CODE_MAPPING as LANGCHAIN_ERROR_CODE_MAPPING
from gllm_inference.lm_invoker.lm_invoker import BaseLMInvoker as BaseLMInvoker
from gllm_inference.lm_invoker.schema.langchain import InputType as InputType, Key as Key
from gllm_inference.output_transformer.output_transformer import BaseOutputTransformer as BaseOutputTransformer
from gllm_inference.schema import Attachment as Attachment, AttachmentType as AttachmentType, LMOutput as LMOutput, LMTool as LMTool, Message as Message, MessageRole as MessageRole, ModelId as ModelId, ModelProvider as ModelProvider, NativeTool as NativeTool, OutputTransformerType as OutputTransformerType, ResponseSchema as ResponseSchema, TokenUsage as TokenUsage, ToolCall as ToolCall, ToolResult as ToolResult
from gllm_inference.utils import load_langchain_model as load_langchain_model, parse_model_data as parse_model_data
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage as BaseMessage
from typing import Any

SUPPORTED_ATTACHMENTS: Incomplete
MESSAGE_CLASS_MAP: Incomplete

class LangChainLMInvoker(BaseLMInvoker):
    '''A language model invoker to interact with LangChain\'s BaseChatModel.

    Attributes:
        model_id (str): The model ID of the language model.
        model_provider (str): The provider of the language model.
        model_name (str): The name of the language model.
        model (BaseChatModel): The LangChain\'s BaseChatModel instance.
        default_hyperparameters (dict[str, Any]): Default hyperparameters for invoking the model.
        tools (list[Any]): The list of tools provided to the model to enable tool calling.
        response_schema (ResponseSchema | None): The schema of the response. If provided, the model will output a
            structured response as defined by the schema. Supports both Pydantic BaseModel and JSON schema dictionary.
        output_analytics (bool): Whether to output the invocation analytics.
        retry_config (RetryConfig | None): The retry configuration for the language model.
        output_transformer (OutputTransformerType): The type of output transformer to use.

    Basic usage:
        The `LangChainLMInvoker` can be used as follows:
        ```python
        lm_invoker = LangChainLMInvoker(
            model_class_path="langchain_openai.ChatOpenAI",
            model_name="gpt-5-nano",
        )
        result = await lm_invoker.invoke("Hi there!")
        ```

    Initialization:
        The `LangChainLMInvoker` can be initialized by either passing:

        1. A LangChain\'s BaseChatModel instance:
        Usage example:
        ```python
        from langchain_openai import ChatOpenAI

        model = ChatOpenAI(model="gpt-5-nano", api_key="your_api_key")
        lm_invoker = LangChainLMInvoker(model=model)
        ```

        2. A model path in the format of "<package>.<class>":
        Usage example:
        ```python
        lm_invoker = LangChainLMInvoker(
            model_class_path="langchain_openai.ChatOpenAI",
            model_name="gpt-5-nano",
            model_kwargs={"api_key": "your_api_key"}
        )
        ```
        For the list of supported providers, please refer to the following table:
        https://python.langchain.com/docs/integrations/chat/#featured-providers

    Input types:
        The `LangChainLMInvoker` supports the following input types: text and image.
        Non-text inputs can be passed as an `Attachment` object and with specific roles,
        depending on the language model\'s capabilities.

        Usage example:
        ```python
        text = "What animal is in this image?"
        image = Attachment.from_path("path/to/local/image.png")
        result = await lm_invoker.invoke([text, image])
        ```

    Text output:
        The `LangChainLMInvoker` generates text outputs by default.
        Text outputs are stored in the `outputs` attribute of the `LMOutput` object and can be accessed
        via the `texts` (all text outputs) or `text` (first text output) properties.

        Output example:
        ```python
        LMOutput(outputs=[LMOutputItem(type="text", output="Hello, there!")])
        ```

    Structured output:
        The `LangChainLMInvoker` can be configured to generate structured outputs.
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

        lm_invoker = LangChainLMInvoker(..., response_schema=Animal)  # Using Pydantic BaseModel class
        lm_invoker = LangChainLMInvoker(..., response_schema=json_schema)  # Using JSON schema dictionary
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

    Tool calling:
        The `LangChainLMInvoker` can be configured to call tools to perform certain tasks.
        This feature can be enabled by providing a list of `Tool` objects to the `tools` parameter.

        Tool calls outputs are stored in the `outputs` attribute of the `LMOutput` object and
        can be accessed via the `tool_calls` property.

        Usage example:
        ```python
        lm_invoker = LangChainLMInvoker(..., tools=[tool_1, tool_2])
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

    Analytics tracking:
        The `LangChainLMInvoker` can be configured to output additional information about the invocation.
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
        The `LangChainLMInvoker` supports retry and timeout configuration.
        By default, the max retries is set to 0 and the timeout is set to 30.0 seconds.
        They can be customized by providing a custom `RetryConfig` object to the `retry_config` parameter.

        Retry config examples:
        ```python
        retry_config = RetryConfig(max_retries=0, timeout=None)  # No retry, no timeout
        retry_config = RetryConfig(max_retries=5, timeout=10.0)  # 5 max retries, 10.0 seconds timeout
        ```

        Usage example:
        ```python
        lm_invoker = LangChainLMInvoker(..., retry_config=retry_config)
        ```
    '''
    model: Incomplete
    def __init__(self, model: BaseChatModel | None = None, model_class_path: str | None = None, model_name: str | None = None, model_kwargs: dict[str, Any] | None = None, default_hyperparameters: dict[str, Any] | None = None, tools: list[LMTool] | None = None, response_schema: ResponseSchema | None = None, output_analytics: bool = False, retry_config: RetryConfig | None = None, output_transformer: OutputTransformerType = ...) -> None:
        '''Initializes a new instance of the LangChainLMInvoker class.

        Args:
            model (BaseChatModel | None, optional): The LangChain\'s BaseChatModel instance. If provided, will take
                precedence over the `model_class_path` parameter. Defaults to None.
            model_class_path (str | None, optional): The LangChain\'s BaseChatModel class path. Must be formatted as
                "<package>.<class>" (e.g. "langchain_openai.ChatOpenAI"). Ignored if `model` is provided.
                Defaults to None.
            model_name (str | None, optional): The model name. Only used if `model_class_path` is provided.
                Defaults to None.
            model_kwargs (dict[str, Any] | None, optional): The additional keyword arguments. Only used if
                `model_class_path` is provided. Defaults to None.
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
            output_transformer (OutputTransformerType, optional): The type of output transformer to use.
                Defaults to OutputTransformerType.IDENTITY, which returns the output without transformation.

        Raises:
            ValueError: If `response_schema` is provided, but `tools` are also provided.
        '''
    def set_tools(self, tools: list[LMTool]) -> None:
        """Sets the tools for LangChain's BaseChatModel.

        This method sets the tools for LangChain's BaseChatModel. Any existing tools will be replaced.

        Args:
            tools (list[Tool]): The list of tools to be used.

        Raises:
            ValueError: If `response_schema` exists.
        """
    def set_response_schema(self, response_schema: ResponseSchema | None) -> None:
        """Sets the response schema for the LangChain's BaseChatModel.

        This method sets the response schema for the LangChain's BaseChatModel. Any existing response schema will be
        replaced.

        Args:
            response_schema (ResponseSchema | None): The response schema to be used.

        Raises:
            ValueError: If `tools` exists.
        """
