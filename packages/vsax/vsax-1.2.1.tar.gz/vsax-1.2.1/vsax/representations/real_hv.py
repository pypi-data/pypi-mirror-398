"""Real-valued hypervector representation for MAP."""

import jax.numpy as jnp

from vsax.core.base import AbstractHypervector


class RealHypervector(AbstractHypervector):
    """Continuous real-valued hypervector for MAP operations.

    RealHypervector uses real numbers to represent hypervectors. This is
    commonly used with Multiply-Add-Permute (MAP) operations where element-wise
    multiplication and averaging are the primary operations.

    The normalization operation performs L2 normalization, scaling the vector
    to unit length.

    Args:
        vec: Real-valued JAX array representing the hypervector.

    Raises:
        TypeError: If vec is complex-valued.

    Example:
        >>> import jax.numpy as jnp
        >>> vec = jnp.array([1.0, 2.0, 3.0])
        >>> hv = RealHypervector(vec)
        >>> normalized = hv.normalize()
        >>> assert jnp.allclose(jnp.linalg.norm(normalized.vec), 1.0)
    """

    def __init__(self, vec: jnp.ndarray) -> None:
        """Initialize real hypervector.

        Args:
            vec: Real-valued JAX array.

        Raises:
            TypeError: If vec is complex-valued.
        """
        if jnp.iscomplexobj(vec):
            raise TypeError(f"RealHypervector requires real array, got complex dtype {vec.dtype}")
        super().__init__(vec)

    def normalize(self) -> "RealHypervector":
        """L2 normalization to unit length.

        Returns:
            New RealHypervector with L2 norm equal to 1.0.

        Example:
            >>> import jax.numpy as jnp
            >>> vec = jnp.array([3.0, 4.0])
            >>> hv = RealHypervector(vec)
            >>> normalized = hv.normalize()
            >>> assert jnp.allclose(jnp.linalg.norm(normalized.vec), 1.0)
            >>> assert jnp.allclose(normalized.vec, jnp.array([0.6, 0.8]))
        """
        norm = jnp.linalg.norm(self._vec)
        # Add small epsilon to avoid division by zero
        normalized = self._vec / (norm + 1e-8)
        return RealHypervector(normalized)
