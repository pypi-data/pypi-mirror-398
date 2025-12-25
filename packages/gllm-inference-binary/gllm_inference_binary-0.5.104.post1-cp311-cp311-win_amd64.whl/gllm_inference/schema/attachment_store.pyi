from gllm_inference.utils import get_value_repr as get_value_repr
from pydantic import BaseModel
from typing import Any

class AttachmentStore(BaseModel):
    """Defines an attachment store schema.

    Attributes:
        id (str): The ID of the attachment store.
        provider (str): The provider that stores and manages the attachment store.
        metadata (dict[str, Any]): The metadata of the attachment store. Defaults to an empty dictionary.
    """
    id: str
    provider: str
    metadata: dict[str, Any]
