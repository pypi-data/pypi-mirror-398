from _typeshed import Incomplete
from typing import Any

class BaseInvokerError(Exception):
    """Base exception class for all gllm_inference invoker errors.

    Attributes:
        class_name (str): The name of the class that raised the error.
        message (str): The error message.
        debug_info (dict[str, Any]): Additional debug information for developers.
        default_message (str): Default error message for the exception class.
    """
    default_message: str
    debug_info: Incomplete
    class_name: Incomplete
    message: Incomplete
    def __init__(self, class_name: str, message: str = '', debug_info: dict[str, Any] | None = None) -> None:
        """Initialize the base exception.

        Args:
            class_name (str): The name of the class that raised the error.
            message (str, optional): The error message. If empty, uses the class's default_message.
                Defaults to empty string.
            debug_info (dict[str, Any] | None, optional): Additional debug information for developers.
                Defaults to None.
        """
    def verbose(self) -> str:
        """Verbose error message with debug information.

        Returns:
            str: The verbose error message with debug information.
        """

class ProviderInvalidArgsError(BaseInvokerError):
    """Exception for bad or malformed requests, invalid parameters or structure.

    Attributes:
        class_name (str): The name of the class that raised the error.
        message (str): The error message.
        debug_info (dict[str, Any]): Additional debug information for developers.
        default_message (str): Default error message for the exception class.
    """
    default_message: str

class ContextOverflowError(BaseInvokerError):
    """Exception for when input size exceeds the model's context length limit.

    Attributes:
        class_name (str): The name of the class that raised the error.
        message (str): The error message.
        debug_info (dict[str, Any]): Additional debug information for developers.
        default_message (str): Default error message for the exception class.
    """
    default_message: str

class ProviderAuthError(BaseInvokerError):
    """Exception for authorization failures due to API key issues.

    Attributes:
        class_name (str): The name of the class that raised the error.
        message (str): The error message.
        debug_info (dict[str, Any]): Additional debug information for developers.
        default_message (str): Default error message for the exception class.
    """
    default_message: str
    @classmethod
    def no_organization(cls, class_name: str, debug_info: dict[str, Any] | None = None) -> ProviderAuthError:
        """Factory for 'no organization' variant."""

class ProviderRateLimitError(BaseInvokerError):
    """Exception for rate limit violations.

    Attributes:
        class_name (str): The name of the class that raised the error.
        message (str): The error message.
        debug_info (dict[str, Any]): Additional debug information for developers.
        default_message (str): Default error message for the exception class.
    """
    default_message: str

class ProviderInternalError(BaseInvokerError):
    """Exception for unexpected server-side errors.

    Attributes:
        class_name (str): The name of the class that raised the error.
        message (str): The error message.
        debug_info (dict[str, Any]): Additional debug information for developers.
        default_message (str): Default error message for the exception class.
    """
    default_message: str

class ProviderOverloadedError(BaseInvokerError):
    """Exception for when the engine is currently overloaded.

    Attributes:
        class_name (str): The name of the class that raised the error.
        message (str): The error message.
        debug_info (dict[str, Any]): Additional debug information for developers.
        default_message (str): Default error message for the exception class.
    """
    default_message: str

class ModelNotFoundError(BaseInvokerError):
    """Exception for model not found errors.

    Attributes:
        class_name (str): The name of the class that raised the error.
        message (str): The error message.
        debug_info (dict[str, Any]): Additional debug information for developers.
        default_message (str): Default error message for the exception class.
    """
    default_message: str

class APIConnectionError(BaseInvokerError):
    """Exception for when the client fails to connect to the model provider.

    Attributes:
        class_name (str): The name of the class that raised the error.
        message (str): The error message.
        debug_info (dict[str, Any]): Additional debug information for developers.
        default_message (str): Default error message for the exception class.
    """
    default_message: str

class APITimeoutError(BaseInvokerError):
    """Exception for when the request to the model provider times out.

    Attributes:
        class_name (str): The name of the class that raised the error.
        message (str): The error message.
        debug_info (dict[str, Any]): Additional debug information for developers.
        default_message (str): Default error message for the exception class.
    """
    default_message: str

class ProviderConflictError(BaseInvokerError):
    """Exception for when the request to the model provider conflicts.

    Attributes:
        class_name (str): The name of the class that raised the error.
        message (str): The error message.
        debug_info (dict[str, Any]): Additional debug information for developers.
        default_message (str): Default error message for the exception class.
    """
    default_message: str

class InvokerRuntimeError(BaseInvokerError):
    """Exception for runtime errors that occur during the invocation of the model.

    Attributes:
        class_name (str): The name of the class that raised the error.
        message (str): The error message.
        debug_info (dict[str, Any]): Additional debug information for developers.
        default_message (str): Default error message for the exception class.
    """
    default_message: str
