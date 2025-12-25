from gllm_inference.em_invoker.base_em_invoker import BaseEMInvoker as BaseEMInvoker
from gllm_inference.exceptions.exceptions import BaseInvokerError as BaseInvokerError, InvokerRuntimeError as InvokerRuntimeError
from gllm_inference.exceptions.provider_error_map import ALL_PROVIDER_ERROR_MAPPINGS as ALL_PROVIDER_ERROR_MAPPINGS, HTTP_STATUS_TO_EXCEPTION_MAP as HTTP_STATUS_TO_EXCEPTION_MAP
from gllm_inference.lm_invoker.base_lm_invoker import BaseLMInvoker as BaseLMInvoker
from typing import Any, Callable

def get_exception_key(error: Exception) -> str:
    '''Generate the fully-qualified name key for an exception.

    Args:
        error (Exception): The exception object.

    Returns:
        str: The fully-qualified name in format "module.ClassName".
    '''
def build_debug_info(error: Any, class_name: str) -> dict[str, Any]:
    """Build debug information for an error.

    Args:
        error (Any): The error to extract debug information from.
        class_name (str): The name of the class that raised the error.

    Returns:
        dict[str, Any]: A dictionary containing debug information about the error.
    """
def convert_to_base_invoker_error(error: Exception, invoker: BaseLMInvoker | BaseEMInvoker, status_code_extractor: Callable[[Exception], int | None] | None = None, response_detail_extractor: Callable[[Exception], str | None] | None = None, message_extractor: Callable[[Exception], str | None] | None = None, response_detail_mapping: dict[str, type[BaseInvokerError]] | None = None, message_mapping: dict[str, type[BaseInvokerError]] | None = None) -> BaseInvokerError:
    """Convert provider error from exception to BaseInvokerError.

    The resolution follows this priority (stops at first match):
      1. Provider-specific error details (via `response_detail_extractor` + `response_detail_mapping`).
      2. Error message regex matching (via `message_extractor` + `message_mapping`).
      3. HTTP status code mapping (via `status_code_extractor`).
      4. Generic provider exception from class module and name.
      5. If all extraction attempts fail, fall back to `InvokerRuntimeError`.

    Args:
        error (Exception): The error to convert.
        invoker (BaseEMInvoker | BaseLMInvoker): The invoker instance that raised the error.
        status_code_extractor (Callable[[Exception], int | None] | None, optional): Function to extract
            HTTP status code from the error. Defaults to None.
        response_detail_extractor (Callable[[Exception], str | None] | None, optional): Function to extract
            error code/type from the error. Defaults to None.
        message_extractor (Callable[[Exception], str | None] | None, optional): Function to extract
            error message from the error. Defaults to None, in which case the error message will be extracted from
            the error's `str(error)`.
        response_detail_mapping (dict[str, type[BaseInvokerError]] | None, optional):
            Fine-grained mapping from provider error codes/types that overrides the default error mapping.
            The mapping key is the response detail string, and the value is the exception class object.
            Defaults to None.
        message_mapping (dict[str, type[BaseInvokerError]] | None, optional):
            Fine-grained mapping from provider error messages that overrides the default error mapping.
            The mapping key is the regex, and the value is the exception class object. Defaults to None.

    Returns:
        BaseInvokerError: The converted error.
    """
