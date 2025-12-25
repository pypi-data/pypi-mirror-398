from gllm_inference.lm_invoker.lm_invoker import BaseLMInvoker as BaseLMInvoker
from gllm_inference.schema import Attachment as Attachment, UploadedAttachment as UploadedAttachment

class FileOperations:
    """Handles file operations for an LM invoker.

    This class provides a wrapper around the file operations of an LM invoker.

    Examples:
        1. Upload a file:
        ```python
        uploaded_attachment = await lm_invoker.file.upload(attachment)
        ```

        2. List the files:
        ```python
        uploaded_attachments = await lm_invoker.file.list()
        ```

        3. Delete a file:
        ```python
        await lm_invoker.file.delete(uploaded_attachment)
        ```
    """
    def __init__(self, invoker: BaseLMInvoker) -> None:
        """Initializes the file operations.

        Args:
            invoker (BaseLMInvoker): The LM invoker to use for the file operations.
        """
    async def upload(self, file: Attachment) -> UploadedAttachment:
        """Uploads a file to the language model provider.

        Args:
            file (Attachment): The file to upload.

        Returns:
            UploadedAttachment: The uploaded attachment.
        """
    async def list(self) -> list[UploadedAttachment]:
        """Lists the files from the language model provider.

        Returns:
            list[UploadedAttachment]: The list of files.
        """
    async def delete(self, file: UploadedAttachment) -> None:
        """Deletes a file from the language model provider.

        Args:
            file (UploadedAttachment): The file to delete.
        """
