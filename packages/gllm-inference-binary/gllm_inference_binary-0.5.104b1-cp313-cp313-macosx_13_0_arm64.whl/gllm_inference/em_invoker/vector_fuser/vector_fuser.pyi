from abc import ABC
from gllm_inference.schema import Vector as Vector

class BaseVectorFuser(ABC):
    """A base class for vector fusers used in EM invokers.

    The `BaseVectorFuser` class defines the interface for fusing a list of vectors into a single vector.
    Subclasses must implement the `fuse` method to fuse the list of vectors into a single vector.
    """
    async def fuse(self, vectors: list[Vector]) -> Vector:
        """Fuses a list of vectors into a single vector.

        This method validates the list of input vectors and then fuses them into a single vector.

        Args:
            vectors (list[Vector]): The list of vectors to fuse.

        Returns:
            Vector: The fused vector.
        """
