from _typeshed import Incomplete
from gllm_inference.em_invoker.em_invoker import BaseEMInvoker as BaseEMInvoker
from gllm_inference.lm_invoker.lm_invoker import BaseLMInvoker as BaseLMInvoker
from gllm_inference.schema.model_id import ModelId as ModelId, ModelProvider as ModelProvider, PROVIDERS_OPTIONAL_PATH as PROVIDERS_OPTIONAL_PATH

logger: Incomplete

class Key:
    """Defines valid keys in the config."""
    ACCESS_KEY_ID: str
    API_KEY: str
    AZURE_DEPLOYMENT: str
    AZURE_ENDPOINT: str
    BASE_URL: str
    CONFIG: str
    CUSTOM_HOST: str
    CREDENTIALS_PATH: str
    MODEL_ID: str
    MODEL_KWARGS: str
    MODEL_NAME: str
    MODEL_CLASS_PATH: str
    PORTKEY_API_KEY: str
    PROVIDER: str
    SECRET_ACCESS_KEY: str

PROVIDERS_REQUIRE_BASE_URL: Incomplete
MODEL_NAME_KEY_MAP: Incomplete
DEFAULT_MODEL_NAME_KEY: Incomplete
