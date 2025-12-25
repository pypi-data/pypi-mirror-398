from gllm_core.utils import RetryConfig
from gllm_inference.lm_invoker.openai_chat_completions_lm_invoker import OpenAIChatCompletionsLMInvoker as OpenAIChatCompletionsLMInvoker
from gllm_inference.lm_invoker.schema.openai_chat_completions import ReasoningEffort as ReasoningEffort
from gllm_inference.schema import LMTool as LMTool, OutputTransformerType as OutputTransformerType, ResponseSchema as ResponseSchema
from typing import Any

DEPRECATION_MESSAGE: str

class OpenAICompatibleLMInvoker(OpenAIChatCompletionsLMInvoker):
    """A language model invoker to interact with endpoints compatible with OpenAI's chat completion API contract.

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

    This class is deprecated and will be removed in v0.6. Please use the `OpenAIChatCompletionsLMInvoker` class instead.
    """
    def __init__(self, model_name: str, base_url: str, api_key: str | None = None, model_kwargs: dict[str, Any] | None = None, default_hyperparameters: dict[str, Any] | None = None, tools: list[LMTool] | None = None, response_schema: ResponseSchema | None = None, output_analytics: bool = False, retry_config: RetryConfig | None = None, reasoning_effort: ReasoningEffort | None = None, output_transformer: OutputTransformerType = ..., simplify_events: bool = False) -> None:
        '''Initializes a new instance of the OpenAICompatibleLMInvoker class.

        Args:
            model_name (str): The name of the language model hosted on the OpenAI compatible endpoint.
            base_url (str): The base URL for the OpenAI compatible endpoint.
            api_key (str | None, optional): The API key for authenticating with the OpenAI compatible endpoint.
                Defaults to None, in which case the `OPENAI_API_KEY` environment variable will be used.
                If the endpoint does not require an API key, a dummy value can be passed (e.g. "<empty>").
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
