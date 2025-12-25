from _typeshed import Incomplete
from gllm_inference.em_invoker.vector_fuser.sum_vector_fuser import SumVectorFuser as SumVectorFuser
from gllm_inference.em_invoker.vector_fuser.vector_fuser import BaseVectorFuser as BaseVectorFuser
from gllm_inference.schema.enums import VectorFuserType as VectorFuserType
from typing import Any

VECTOR_FUSER_TYPE_MAP: Incomplete

def build_vector_fuser(type_: VectorFuserType, **kwargs: Any) -> BaseVectorFuser:
    """Build a vector fuser based on the provided configurations.

    Examples:
        # Using sum vector fuser
        ```python
        vector_fuser = build_vector_fuser(VectorFuserType.SUM)
        ```

    Args:
        type_ (VectorFuserType): The type of vector fuser to use.
        **kwargs (Any): Additional keyword arguments to pass to the vector fuser constructor.

    Returns:
        BaseVectorFuser: The initialized vector fuser.

    Raises:
        ValueError: If the provided type is not supported.
    """
