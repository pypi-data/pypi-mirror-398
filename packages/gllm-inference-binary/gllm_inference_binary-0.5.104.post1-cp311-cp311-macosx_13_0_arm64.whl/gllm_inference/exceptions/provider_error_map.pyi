from _typeshed import Incomplete
from enum import IntEnum
from gllm_inference.exceptions.exceptions import APIConnectionError as APIConnectionError, APITimeoutError as APITimeoutError, BaseInvokerError as BaseInvokerError, ContextOverflowError as ContextOverflowError, ModelNotFoundError as ModelNotFoundError, ProviderAuthError as ProviderAuthError, ProviderConflictError as ProviderConflictError, ProviderInternalError as ProviderInternalError, ProviderInvalidArgsError as ProviderInvalidArgsError, ProviderOverloadedError as ProviderOverloadedError, ProviderRateLimitError as ProviderRateLimitError

class ExtendedHTTPStatus(IntEnum):
    """HTTP status codes outside of the standard HTTPStatus enum.

    Attributes:
        SERVICE_OVERLOADED (int): HTTP status code for service overloaded.
    """
    SERVICE_OVERLOADED: int

HTTP_STATUS_TO_EXCEPTION_MAP: dict[int, type[BaseInvokerError]]
ANTHROPIC_ERROR_MAPPING: Incomplete
BEDROCK_ERROR_MAPPING: Incomplete
COHERE_ERROR_MAPPING: Incomplete
GOOGLE_ERROR_MAPPING: Incomplete
LANGCHAIN_ERROR_CODE_MAPPING: Incomplete
LITELLM_ERROR_MAPPING: Incomplete
OPENAI_ERROR_MAPPING: Incomplete
OPENAI_RESPONSE_DETAIL_MAPPING: Incomplete
OPENAI_MESSAGE_MAPPING: Incomplete
TWELVELABS_ERROR_MAPPING: Incomplete
VOYAGE_ERROR_MAPPING: Incomplete
GRPC_STATUS_CODE_MAPPING: Incomplete
GENERAL_CONNECTION_ERROR_MAPPING: Incomplete
ALL_PROVIDER_ERROR_MAPPINGS: Incomplete
