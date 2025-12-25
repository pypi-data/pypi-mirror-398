from gllm_inference.lm_invoker.lm_invoker import BaseLMInvoker as BaseLMInvoker
from gllm_inference.schema import Attachment as Attachment, AttachmentStore as AttachmentStore
from typing import Any

class DataStoreOperations:
    """Handles data store operations for an LM invoker.

    This class provides a wrapper around the data store operations of an LM invoker.
    It provides a simple interface to perform data store operations.

    Examples:
        1. Create a data store:
        ```python
        data_store = await lm_invoker.data_store.create()
        ```

        2. List the data stores:
        ```python
        data_stores = await lm_invoker.data_store.list()
        ```

        3. Delete a data store:
        ```python
        await lm_invoker.data_store.delete(data_store)
        ```

        4. Upload attachments to a data store:
        ```python
        await lm_invoker.data_store.add_file(data_store, file)
        ```
    """
    def __init__(self, invoker: BaseLMInvoker) -> None:
        """Initializes the data store operations.

        Args:
            invoker (BaseLMInvoker): The LM invoker to use for the data store operations.
        """
    async def create(self, **kwargs: Any) -> AttachmentStore:
        """Creates a new data store.

        Args:
            **kwargs (Any): Additional keyword arguments to create a data store.

        Returns:
            AttachmentStore: The created data store.
        """
    async def list(self) -> list[AttachmentStore]:
        """Lists the data stores.

        Returns:
            list[AttachmentStore]: The list of data stores.
        """
    async def delete(self, data_store: AttachmentStore) -> None:
        """Deletes a data store.

        Args:
            data_store (AttachmentStore): The data store to delete.
        """
    async def add_file(self, data_store: AttachmentStore, file: Attachment, **kwargs: Any) -> None:
        """Adds an attachment file to a data store.

        Args:
            data_store (AttachmentStore): The data store to add the attachment file to.
            file (Attachment): The attachment file to add.
            **kwargs (Any): Additional keyword arguments to add the attachment file to the data store.
        """
