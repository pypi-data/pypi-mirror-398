from _typeshed import Incomplete
from gllm_core.utils import RetryConfig
from gllm_inference.constants import INVOKER_PROPAGATED_MAX_RETRIES as INVOKER_PROPAGATED_MAX_RETRIES
from gllm_inference.lm_invoker.openai_chat_completions_lm_invoker import OpenAIChatCompletionsLMInvoker as OpenAIChatCompletionsLMInvoker
from gllm_inference.lm_invoker.schema.openai_chat_completions import Key as Key
from gllm_inference.schema import LMTool as LMTool, ModelId as ModelId, ModelProvider as ModelProvider, OutputTransformerType as OutputTransformerType, ResponseSchema as ResponseSchema
from typing import Any

SEA_LION_URL: str
SUPPORTED_ATTACHMENTS: Incomplete

class SeaLionLMInvoker(OpenAIChatCompletionsLMInvoker):
    """A language model invoker to interact with SEA-LION API.

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
    """
    client_kwargs: Incomplete
    def __init__(self, model_name: str, api_key: str | None = None, model_kwargs: dict[str, Any] | None = None, default_hyperparameters: dict[str, Any] | None = None, tools: list[LMTool] | None = None, response_schema: ResponseSchema | None = None, output_analytics: bool = False, retry_config: RetryConfig | None = None, output_transformer: OutputTransformerType = ...) -> None:
        """Initializes a new instance of the SeaLionLMInvoker class.

        Args:
            model_name (str): The name of the SEA-LION language model.
            api_key (str | None, optional): The API key for authenticating with the SEA-LION API.
                Defaults to None, in which case the `SEA_LION_API_KEY` environment variable will be used.
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
            output_transformer (OutputTransformerType, optional): The type of output transformer to use.
                Defaults to OutputTransformerType.IDENTITY, which returns the output without transformation.
        """
