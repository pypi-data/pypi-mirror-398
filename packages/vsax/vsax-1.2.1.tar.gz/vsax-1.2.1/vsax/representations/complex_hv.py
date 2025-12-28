"""Complex-valued hypervector representation for FHRR."""

import jax.numpy as jnp

from vsax.core.base import AbstractHypervector


class ComplexHypervector(AbstractHypervector):
    """Phase-based complex-valued hypervector for FHRR.

    ComplexHypervector uses complex numbers to represent hypervectors, where
    the phase component encodes information. This is particularly useful for
    Fourier Holographic Reduced Representation (FHRR) operations.

    The normalization operation sets all elements to unit magnitude, preserving
    only the phase information.

    Args:
        vec: Complex-valued JAX array representing the hypervector.

    Raises:
        TypeError: If vec is not a complex array.

    Example:
        >>> import jax.numpy as jnp
        >>> vec = jnp.exp(1j * jnp.array([0.5, 1.0, 1.5]))
        >>> hv = ComplexHypervector(vec)
        >>> normalized = hv.normalize()
        >>> assert jnp.allclose(jnp.abs(normalized.vec), 1.0)
    """

    def __init__(self, vec: jnp.ndarray) -> None:
        """Initialize complex hypervector.

        Args:
            vec: Complex-valued JAX array.

        Raises:
            TypeError: If vec is not complex-valued.
        """
        if not jnp.iscomplexobj(vec):
            raise TypeError(f"ComplexHypervector requires complex array, got {vec.dtype}")
        super().__init__(vec)

    def normalize(self) -> "ComplexHypervector":
        """Normalize to unit magnitude (phase-only representation).

        Returns:
            New ComplexHypervector with all elements having magnitude 1.0,
            preserving the phase angles.

        Example:
            >>> import jax.numpy as jnp
            >>> vec = jnp.array([3+4j, 5+12j])
            >>> hv = ComplexHypervector(vec)
            >>> normalized = hv.normalize()
            >>> magnitudes = jnp.abs(normalized.vec)
            >>> assert jnp.allclose(magnitudes, 1.0)
        """
        # Normalize to unit magnitude: z / |z|
        normalized = self._vec / jnp.abs(self._vec)
        return ComplexHypervector(normalized)

    @property
    def phase(self) -> jnp.ndarray:
        """Extract phase component of the complex hypervector.

        Returns:
            Real-valued array of phase angles in radians, in the range [-π, π].

        Example:
            >>> import jax.numpy as jnp
            >>> vec = jnp.exp(1j * jnp.array([0.0, jnp.pi/2, jnp.pi]))
            >>> hv = ComplexHypervector(vec)
            >>> phases = hv.phase
            >>> assert phases.shape == vec.shape
        """
        return jnp.angle(self._vec)

    @property
    def magnitude(self) -> jnp.ndarray:
        """Extract magnitude component of the complex hypervector.

        Returns:
            Real-valued array of magnitudes.

        Example:
            >>> import jax.numpy as jnp
            >>> vec = jnp.array([3+4j, 5+12j])
            >>> hv = ComplexHypervector(vec)
            >>> mags = hv.magnitude
            >>> assert jnp.allclose(mags, jnp.array([5.0, 13.0]))
        """
        return jnp.abs(self._vec)
