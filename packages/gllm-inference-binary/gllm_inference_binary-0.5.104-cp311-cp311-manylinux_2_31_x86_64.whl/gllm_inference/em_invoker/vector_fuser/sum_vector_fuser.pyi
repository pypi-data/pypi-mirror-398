from gllm_inference.em_invoker.vector_fuser.vector_fuser import BaseVectorFuser as BaseVectorFuser
from gllm_inference.schema import Vector as Vector

class SumVectorFuser(BaseVectorFuser):
    """A vector fuser that sums up a list of vectors into a single vector.

    Examples:
        Input:
            [[a1, a2, a3, a4], [b1, b2, b3, b4]]
        Output:
            [a1 + b1, a2 + b2, a3 + b3, a4 + b4]
    """
