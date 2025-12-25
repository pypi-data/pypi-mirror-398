from gllm_inference.exceptions import InvokerRuntimeError as InvokerRuntimeError
from gllm_inference.lm_invoker.lm_invoker import BaseLMInvoker as BaseLMInvoker
from gllm_inference.schema import BatchStatus as BatchStatus, LMInput as LMInput, LMOutput as LMOutput
from typing import Any

DEFAULT_STATUS_CHECK_INTERVAL: float

class BatchOperations:
    """Handles batch operations for an LM invoker.

    This class provides a wrapper around the batch operations of an LM invoker.

    Examples:
        Invoke the language model in batch mode:
        ```python
        results = await lm_invoker.batch.invoke(...)
        ```

        Standalone batch operations:
        1. Create a batch job:
        ```python
        batch_id = await lm_invoker.batch.create(...)
        ```

        2. Get the status of a batch job:
        ```python
        status = await lm_invoker.batch.status(batch_id)
        ```

        3. Retrieve the results of a batch job:
        ```python
        results = await lm_invoker.batch.retrieve(batch_id)
        ```

        4. List the batch jobs:
        ```python
        batch_jobs = await lm_invoker.batch.list()
        ```

        5. Cancel a batch job:
        ```python
        await lm_invoker.batch.cancel(batch_id)
        ```
    """
    def __init__(self, invoker: BaseLMInvoker) -> None:
        """Initializes the batch operations.

        Args:
            invoker (BaseLMInvoker): The LM invoker to use for the batch operations.
        """
    async def invoke(self, requests: dict[str, LMInput], hyperparameters: dict[str, Any] | None = None, status_check_interval: float = ..., max_iterations: int | None = None) -> dict[str, LMOutput]:
        """Invokes the language model in batch mode.

        This method orchestrates the entire batch invocation process, including;
        1. Creating a batch job.
        2. Iteratively checking the status of the batch job until it is finished.
        3. Retrieving the results of the batch job.
        The method includes retry logic with exponential backoff for transient failures.

        Args:
            requests (dict[str, LMInput]): The dictionary of requests that maps request ID to the request.
                Each request must be a valid input for the language model.
                1. If the request is a list of Message objects, it is used as is.
                2. If the request is a list of MessageContent or a string, it is converted into a user message.
            hyperparameters (dict[str, Any] | None, optional): A dictionary of hyperparameters for the language model.
                Defaults to None, in which case the default hyperparameters are used.
            status_check_interval (float, optional): The interval in seconds to check the status of the batch job.
                Defaults to DEFAULT_STATUS_CHECK_INTERVAL.
            max_iterations (int | None, optional): The maximum number of iterations to check the status of the batch
                job. Defaults to None, in which case the number of iterations is infinite.

        Returns:
            dict[str, LMOutput]: The results of the batch job.

        Raises:
            CancelledError: If the invocation is cancelled.
            ModelNotFoundError: If the model is not found.
            ProviderAuthError: If the model authentication fails.
            ProviderInternalError: If the model internal error occurs.
            ProviderInvalidArgsError: If the model parameters are invalid.
            ProviderOverloadedError: If the model is overloaded.
            ProviderRateLimitError: If the model rate limit is exceeded.
            TimeoutError: If the invocation times out.
            ValueError: If the messages are not in the correct format.
        """
    async def create(self, requests: dict[str, LMInput], hyperparameters: dict[str, Any] | None = None) -> str:
        """Creates a new batch job.

        Args:
            requests (dict[str, LMInput]): The dictionary of requests that maps request ID to the request.
                Each request must be a valid input for the language model.
                1. If the request is a list of Message objects, it is used as is.
                2. If the request is a list of MessageContent or a string, it is converted into a user message.
            hyperparameters (dict[str, Any] | None, optional): A dictionary of hyperparameters for the language model.
                Defaults to None, in which case the default hyperparameters are used.

        Returns:
            str: The ID of the batch job.
        """
    async def status(self, batch_id: str) -> BatchStatus:
        """Gets the status of a batch job.

        Args:
            batch_id (str): The ID of the batch job to get the status of.

        Returns:
            BatchStatus: The status of the batch job.
        """
    async def retrieve(self, batch_id: str, **kwargs: Any) -> dict[str, LMOutput]:
        """Retrieves the results of a batch job.

        Args:
            batch_id (str): The ID of the batch job to get the results of.
            **kwargs (Any): Additional keyword arguments.

        Returns:
            dict[str, LMOutput]: The results of the batch job.
        """
    async def list(self) -> list[dict[str, Any]]:
        """Lists the batch jobs.

        Returns:
            list[dict[str, Any]]: The list of batch jobs.
        """
    async def cancel(self, batch_id: str) -> None:
        """Cancels a batch job.

        Args:
            batch_id (str): The ID of the batch job to cancel.
        """
