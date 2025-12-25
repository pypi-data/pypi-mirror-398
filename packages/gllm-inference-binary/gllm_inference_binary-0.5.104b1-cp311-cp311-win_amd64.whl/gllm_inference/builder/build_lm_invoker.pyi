from gllm_inference.lm_invoker import AnthropicLMInvoker as AnthropicLMInvoker, AzureOpenAILMInvoker as AzureOpenAILMInvoker, BedrockLMInvoker as BedrockLMInvoker, DatasaurLMInvoker as DatasaurLMInvoker, GoogleLMInvoker as GoogleLMInvoker, LangChainLMInvoker as LangChainLMInvoker, LiteLLMLMInvoker as LiteLLMLMInvoker, OpenAIChatCompletionsLMInvoker as OpenAIChatCompletionsLMInvoker, OpenAICompatibleLMInvoker as OpenAICompatibleLMInvoker, OpenAILMInvoker as OpenAILMInvoker, PortkeyLMInvoker as PortkeyLMInvoker, SeaLionLMInvoker as SeaLionLMInvoker, XAILMInvoker as XAILMInvoker
from gllm_inference.lm_invoker.lm_invoker import BaseLMInvoker as BaseLMInvoker
from gllm_inference.schema.model_id import ModelId as ModelId, ModelProvider as ModelProvider
from typing import Any

PROVIDER_TO_LM_INVOKER_MAP: dict[str, type[BaseLMInvoker]]

def build_lm_invoker(model_id: str | ModelId, credentials: str | dict[str, Any] | None = None, config: dict[str, Any] | None = None) -> BaseLMInvoker:
    '''Build a language model invoker based on the provided configurations.

    Args:
        model_id (str | ModelId): The model id, can either be a ModelId instance or a string in a format defined
            in the following page: https://gdplabs.gitbook.io/sdk/resources/supported-models#language-models-lms
        credentials (str | dict[str, Any] | None, optional): The credentials for the language model. Can either be:
            1. An API key.
            2. A path to a credentials JSON file, currently only supported for Google Vertex AI.
            3. A dictionary of credentials, currently supported for Bedrock and LangChain.
            Defaults to None, in which case the credentials will be loaded from the appropriate environment variables.
        config (dict[str, Any] | None, optional): Additional configuration for the language model. Defaults to None.

    Returns:
        BaseLMInvoker: The initialized language model invoker.

    Raises:
        ValueError: If the provider is invalid.

    Usage examples:
        # Using Anthropic
        ```python
        lm_invoker = build_lm_invoker(
            model_id="anthropic/claude-3-5-sonnet-latest",
            credentials="sk-ant-api03-..."
        )
        ```
        The credentials can also be provided through the `ANTHROPIC_API_KEY` environment variable.

        # Using Bedrock
        ```python
        lm_invoker = build_lm_invoker(
            model_id="bedrock/us.anthropic.claude-sonnet-4-20250514-v1:0",
            credentials={
                "access_key_id": "Abc123...",
                "secret_access_key": "Xyz123...",
            },
        )
        ```
        The credentials can also be provided through the `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`
        environment variables.

        # Using Datasaur LLM Projects Deployment API
        ```python
        lm_invoker = build_lm_invoker(
            model_id="datasaur/https://deployment.datasaur.ai/api/deployment/teamId/deploymentId/",
            credentials="..."
        )
        ```
        The credentials can also be provided through the `DATASAUR_API_KEY` environment variable.

        # Using Google Gen AI (via API key)
        ```python
        lm_invoker = build_lm_invoker(
            model_id="google/gemini-2.5-flash-lite",
            credentials="AIzaSyD..."
        )
        ```
        The credentials can also be provided through the `GOOGLE_API_KEY` environment variable.

        # Using Google Vertex AI (via service account)
        ```python
        lm_invoker = build_lm_invoker(
            model_id="google/gemini-2.5-flash-lite",
            credentials="/path/to/google-credentials.json"
        )
        ```
        Providing credentials through environment variable is not supported for Google Vertex AI.

        # Using OpenAI
        ```python
        lm_invoker = build_lm_invoker(
            model_id="openai/gpt-5-nano",
            credentials="sk-..."
        )
        ```
        The credentials can also be provided through the `OPENAI_API_KEY` environment variable.

        # Using OpenAI with Chat Completions API
        ```python
        lm_invoker = build_lm_invoker(
            model_id="openai-chat-completions/gpt-5-nano",
            credentials="sk-..."
        )
        ```
        The credentials can also be provided through the `OPENAI_API_KEY` environment variable.

        # Using OpenAI Responses API-compatible endpoints (e.g. SGLang)
        ```python
        lm_invoker = build_lm_invoker(
            model_id="openai/https://my-sglang-url:8000/v1:my-model-name",
            credentials="sk-..."
        )
        ```
        The credentials can also be provided through the `OPENAI_API_KEY` environment variable.

        # Using OpenAI Chat Completions API-compatible endpoints (e.g. Groq)
        ```python
        lm_invoker = build_lm_invoker(
            model_id="openai-chat-completions/https://api.groq.com/openai/v1:llama3-8b-8192",
            credentials="gsk_..."
        )
        ```
        The credentials can also be provided through the `OPENAI_API_KEY` environment variable.

        # Using Azure OpenAI
        ```python
        lm_invoker = build_lm_invoker(
            model_id="azure-openai/https://my-resource.openai.azure.com/openai/v1:my-deployment",
            credentials="azure-api-key"
        )
        ```
        The credentials can also be provided through the `AZURE_OPENAI_API_KEY` environment variable.

        # Using SEA-LION
        ```python
        lm_invoker = build_lm_invoker(
            model_id="sea-lion/aisingapore/Qwen-SEA-LION-v4-32B-IT",
            credentials="sk-..."
        )
        ```
        The credentials can also be provided through the `SEA_LION_API_KEY` environment variable.

        # Using LangChain
        ```python
        lm_invoker = build_lm_invoker(
            model_id="langchain/langchain_openai.ChatOpenAI:gpt-4o-mini",
            credentials={"api_key": "sk-..."}
        )
        ```
        The credentials can also be provided through various environment variables depending on the
        LangChain module being used. For the list of supported providers and the supported environment
        variables credentials, please refer to the following table:
        https://python.langchain.com/docs/integrations/chat/#featured-providers

        # Using LiteLLM
        ```python
        os.environ["OPENAI_API_KEY"] = "sk-..."
        lm_invoker = build_lm_invoker(
            model_id="litellm/openai/gpt-4o-mini",
        )
        ```
        For the list of supported providers, please refer to the following page:
        https://docs.litellm.ai/docs/providers/

        # Using Portkey
        Portkey supports multiple authentication methods with strict precedence order.
        Authentication methods are mutually exclusive and cannot be combined.

        ## Config ID Authentication (Highest Precedence)
        ```python
        lm_invoker = build_lm_invoker(
            model_id="portkey/any-model",
            credentials="portkey-api-key",
            config={"config": "pc-openai-4f6905"}
        )
        ```

        ## Model Catalog Authentication (Combined Format)
        ```python
        lm_invoker = build_lm_invoker(
            model_id="portkey/@openai-custom/gpt-4o",
            credentials="portkey-api-key"
        )
        ```

        ## Model Catalog Authentication (Separate Parameters)
        ```python
        lm_invoker = build_lm_invoker(
            model_id="portkey/gpt-4o",
            credentials="portkey-api-key",
            config={"provider": "@openai-custom"}
        )
        ```

        ## Direct Provider Authentication
        ```python
        lm_invoker = build_lm_invoker(
            model_id="portkey/gpt-4o",
            credentials={
                "portkey_api_key": "portkey-api-key",
                "api_key": "sk-...",  # Provider\'s API key
                "provider": "openai"  # Direct provider (no \'@\' prefix)
            }
        )
        ```

        ## Custom Host Override
        ```python
        lm_invoker = build_lm_invoker(
            model_id="portkey/@custom-provider/gpt-4o",
            credentials="portkey-api-key",
            config={"custom_host": "https://your-custom-endpoint.com"}
        )
        ```

        The Portkey API key can also be provided through the `PORTKEY_API_KEY` environment variable.
        For more details on authentication methods, please refer to:
        https://portkey.ai/docs/product/ai-gateway/universal-api

        # Using xAI
        ```python
        lm_invoker = build_lm_invoker(
            model_id="xai/grok-3",
            credentials="xai-..."
        )
        ```
        The credentials can also be provided through the `XAI_API_KEY` environment variable.
        For the list of supported models, please refer to the following page:
        https://docs.x.ai/docs/models

    Security warning:
        Please provide the LM invoker credentials ONLY to the `credentials` parameter. Do not put any kind of
        credentials in the `config` parameter as the content of the `config` parameter will be logged.
    '''
