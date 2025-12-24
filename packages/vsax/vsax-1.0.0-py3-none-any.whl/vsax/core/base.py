"""Abstract base classes for VSA components."""

from abc import ABC, abstractmethod
from typing import cast

import jax.numpy as jnp
import numpy as np


class AbstractHypervector(ABC):
    """Base class for all hypervector representations.

    Wraps a JAX array and provides common operations for hypervectors.
    All concrete implementations must inherit from this class.

    Args:
        vec: The underlying JAX array representing the hypervector.
    """

    def __init__(self, vec: jnp.ndarray) -> None:
        """Initialize hypervector with underlying array.

        Args:
            vec: JAX array representing the hypervector.
        """
        self._vec = vec

    @property
    def vec(self) -> jnp.ndarray:
        """Return the underlying JAX array.

        Returns:
            The JAX array wrapped by this hypervector.
        """
        return self._vec

    @property
    def shape(self) -> tuple[int, ...]:
        """Return the shape of the hypervector.

        Returns:
            Tuple representing the shape of the underlying array.
        """
        return cast(tuple[int, ...], self._vec.shape)

    @property
    def dtype(self) -> jnp.dtype:
        """Return the data type of the hypervector.

        Returns:
            JAX dtype of the underlying array.
        """
        return self._vec.dtype

    @abstractmethod
    def normalize(self) -> "AbstractHypervector":
        """Normalize the hypervector.

        The normalization method depends on the representation type.
        For example, complex vectors normalize to unit magnitude (phase-only),
        while real vectors use L2 normalization.

        Returns:
            Normalized hypervector of the same type.
        """
        pass

    def to_numpy(self) -> np.ndarray:
        """Convert the hypervector to a NumPy array.

        Returns:
            NumPy array representation of the hypervector.
        """
        return np.array(self._vec)

    def __repr__(self) -> str:
        """Return string representation of the hypervector.

        Returns:
            String showing class name, shape, and dtype.
        """
        return f"{self.__class__.__name__}(shape={self.shape}, dtype={self.dtype})"


class AbstractOpSet(ABC):
    """Base class for VSA operation sets.

    Defines the symbolic algebra operations for binding and bundling hypervectors.
    All operations work directly on JAX arrays, not on AbstractHypervector instances.

    Concrete implementations (FHRR, MAP, Binary) must implement all abstract methods.
    """

    @abstractmethod
    def bind(self, a: jnp.ndarray, b: jnp.ndarray) -> jnp.ndarray:
        """Bind two hypervectors together.

        Binding creates a composite representation that is dissimilar to both inputs
        but can be unbound using the inverse operation. The specific binding operation
        depends on the algebra (e.g., circular convolution for FHRR, elementwise
        multiplication for MAP).

        Args:
            a: First hypervector as JAX array.
            b: Second hypervector as JAX array.

        Returns:
            Bound hypervector as JAX array.
        """
        pass

    @abstractmethod
    def bundle(self, *vecs: jnp.ndarray) -> jnp.ndarray:
        """Bundle multiple hypervectors into a single representation.

        Bundling creates a superposition that is similar to all inputs.
        The bundled vector can be queried to retrieve the constituent vectors.

        Args:
            *vecs: Variable number of hypervectors as JAX arrays.

        Returns:
            Bundled hypervector as JAX array.
        """
        pass

    @abstractmethod
    def inverse(self, a: jnp.ndarray) -> jnp.ndarray:
        """Compute the inverse of a hypervector.

        The inverse is used to unbind: if c = bind(a, b), then
        unbind(c, b) = bind(c, inverse(b)) ≈ a.

        Args:
            a: Hypervector as JAX array.

        Returns:
            Inverse hypervector as JAX array.
        """
        pass

    def permute(self, a: jnp.ndarray, shift: int) -> jnp.ndarray:
        """Permute a hypervector by circular shift.

        This is an optional operation. The default implementation performs
        a circular shift, but concrete classes may override with different
        permutation strategies.

        Args:
            a: Hypervector as JAX array.
            shift: Number of positions to shift (positive = right, negative = left).

        Returns:
            Permuted hypervector as JAX array.
        """
        return jnp.roll(a, shift)
