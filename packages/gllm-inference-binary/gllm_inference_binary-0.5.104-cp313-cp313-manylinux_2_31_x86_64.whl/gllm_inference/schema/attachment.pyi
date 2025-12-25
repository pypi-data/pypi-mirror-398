from _typeshed import Incomplete
from gllm_inference.utils import get_value_repr as get_value_repr
from pydantic import BaseModel
from typing import Any

HEX_REPR_LENGTH: int
logger: Incomplete

class Attachment(BaseModel):
    """Defines a file attachment schema.

    Attributes:
        data (bytes): The content data of the file attachment.
        filename (str): The filename of the file attachment.
        mime_type (str): The mime type of the file attachment.
        extension (str): The extension of the file attachment.
        url (str | None): The URL of the file attachment. Defaults to None.
        metadata (dict[str, Any]): The metadata of the file attachment. Defaults to an empty dictionary.
    """
    data: bytes
    filename: str
    mime_type: str
    extension: str
    url: str | None
    metadata: dict[str, Any]
    @classmethod
    def from_bytes(cls, bytes: bytes, filename: str | None = None, metadata: dict[str, Any] | None = None) -> Attachment:
        """Creates an Attachment from bytes.

        Args:
            bytes (bytes): The bytes of the file.
            filename (str | None, optional): The filename of the file. Defaults to None,
                in which case the filename will be derived from the extension.
            metadata (dict[str, Any] | None, optional): The metadata of the file attachment. Defaults to None,
                in which case an empty dictionary will be used.

        Returns:
            Attachment: The instantiated Attachment.
        """
    @classmethod
    def from_base64(cls, base64_data: str, filename: str | None = None, metadata: dict[str, Any] | None = None) -> Attachment:
        """Creates an Attachment from a base64 string.

        Args:
            base64_data (str): The base64 string of the file.
            filename (str | None, optional): The filename of the file. Defaults to None,
                in which case the filename will be derived from the mime type.
            metadata (dict[str, Any] | None, optional): The metadata of the file attachment. Defaults to None,
                in which case an empty dictionary will be used.

        Returns:
            Attachment: The instantiated Attachment.
        """
    @classmethod
    def from_data_url(cls, data_url: str, filename: str | None = None, metadata: dict[str, Any] | None = None) -> Attachment:
        """Creates an Attachment from a data URL (data:[mime/type];base64,[bytes]).

        Args:
            data_url (str): The data URL of the file.
            filename (str | None, optional): The filename of the file. Defaults to None,
                in which case the filename will be derived from the mime type.
            metadata (dict[str, Any] | None, optional): The metadata of the file attachment. Defaults to None,
                in which case an empty dictionary will be used.

        Returns:
            Attachment: The instantiated Attachment.
        """
    @classmethod
    def from_url(cls, url: str, filename: str | None = None, metadata: dict[str, Any] | None = None) -> Attachment:
        """Creates an Attachment from a URL.

        Args:
            url (str): The URL of the file.
            filename (str | None, optional): The filename of the file. Defaults to None,
                in which case the filename will be derived from the URL.
            metadata (dict[str, Any] | None, optional): The metadata of the file attachment. Defaults to None,
                in which case an empty dictionary will be used.

        Returns:
            Attachment: The instantiated Attachment.
        """
    @classmethod
    def from_path(cls, path: str, filename: str | None = None, metadata: dict[str, Any] | None = None) -> Attachment:
        """Creates an Attachment from a path.

        Args:
            path (str): The path to the file.
            filename (str | None, optional): The filename of the file. Defaults to None,
                in which case the filename will be derived from the path.
            metadata (dict[str, Any] | None, optional): The metadata of the file attachment. Defaults to None,
                in which case an empty dictionary will be used.

        Returns:
            Attachment: The instantiated Attachment.
        """
    def write_to_file(self, path: str | None = None) -> None:
        """Writes the Attachment to a file.

        Args:
            path (str | None, optional): The path to the file. Defaults to None,
                in which case the filename will be used as the path.
        """

class UploadedAttachment(Attachment):
    """Defines an uploaded file attachment schema.

    This class is used to represent a file attachment that has been uploaded to a certain LM provider's
    files management capabilities. It is recognized through the `id` attribute, which content depends on
    the nature of the LM provider's files management capabilities. It could be an ID, a URL, etc.

    Attributes:
        id (str): The identifier of the uploaded file.
        provider (str): The provider that stores and manages the uploaded file.
        data (bytes): The content data of the file attachment. Defaults to an empty bytes object.
        filename (str): The filename of the file attachment.
        mime_type (str): The mime type of the file attachment.
        extension (str): The extension of the file attachment.
        url (str | None): The URL of the file attachment. Defaults to None.
        metadata (dict[str, Any]): The metadata of the file attachment. Defaults to an empty dictionary.
    """
    id: str
    provider: str
    data: bytes
    filename: str
    mime_type: str
    extension: str
    def __init__(self, id: str, provider: str, url: str | None = None, metadata: dict[str, Any] | None = None, **kwargs: Any) -> None:
        """Initializes an UploadedAttachment.

        Args:
            id (str): The ID of the uploaded file attachment.
            provider (str): The provider that stores and manages the uploaded file.
            url (str | None, optional): The URL of the file attachment. Defaults to None.
            metadata (dict[str, Any] | None, optional): The metadata of the file attachment. Defaults to None,
                in which case an empty dictionary will be used.
            **kwargs (Any): Additional keyword arguments passed to the parent class.
        """
