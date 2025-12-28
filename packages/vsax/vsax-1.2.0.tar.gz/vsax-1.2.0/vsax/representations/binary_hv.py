"""Binary hypervector representation for binary VSA."""

import jax.numpy as jnp

from vsax.core.base import AbstractHypervector


class BinaryHypervector(AbstractHypervector):
    """Binary hypervector with bipolar {-1, +1} or binary {0, 1} values.

    BinaryHypervector represents hypervectors using discrete binary values.
    It supports two modes:
    - Bipolar: values in {-1, +1} (default, recommended)
    - Binary: values in {0, 1}

    Binary hypervectors are efficient for hardware implementation and provide
    good performance with XOR binding and majority bundling operations.

    Args:
        vec: JAX array containing binary values.
        bipolar: If True, expects {-1, +1} values. If False, expects {0, 1} values.

    Raises:
        ValueError: If vec contains values outside the expected binary set.

    Example:
        >>> import jax.numpy as jnp
        >>> vec = jnp.array([1, -1, 1, -1])
        >>> hv = BinaryHypervector(vec, bipolar=True)
        >>> normalized = hv.normalize()  # No-op for binary
        >>> assert jnp.array_equal(normalized.vec, vec)
    """

    def __init__(self, vec: jnp.ndarray, bipolar: bool = True) -> None:
        """Initialize binary hypervector.

        Args:
            vec: JAX array with binary values.
            bipolar: If True, values should be {-1, +1}.
                    If False, values should be {0, 1}.

        Raises:
            ValueError: If vec contains invalid values for the chosen mode.
        """
        self._bipolar = bipolar

        # Validate binary values
        unique_vals = jnp.unique(vec)

        if bipolar:
            valid_set = jnp.array([-1, 1])
            if not jnp.all(jnp.isin(unique_vals, valid_set)):
                raise ValueError(
                    f"Bipolar binary vector must contain only -1 or +1, "
                    f"got unique values: {unique_vals}"
                )
        else:
            valid_set = jnp.array([0, 1])
            if not jnp.all(jnp.isin(unique_vals, valid_set)):
                raise ValueError(
                    f"Non-bipolar binary vector must contain only 0 or 1, "
                    f"got unique values: {unique_vals}"
                )

        super().__init__(vec)

    def normalize(self) -> "BinaryHypervector":
        """No-op normalization for binary hypervectors.

        Binary hypervectors are already in their normalized form.

        Returns:
            A new BinaryHypervector with the same values.

        Example:
            >>> import jax.numpy as jnp
            >>> vec = jnp.array([1, -1, 1])
            >>> hv = BinaryHypervector(vec)
            >>> normalized = hv.normalize()
            >>> assert jnp.array_equal(normalized.vec, vec)
        """
        return BinaryHypervector(self._vec, bipolar=self._bipolar)

    @property
    def bipolar(self) -> bool:
        """Check if hypervector uses bipolar {-1, +1} encoding.

        Returns:
            True if bipolar, False if binary {0, 1}.
        """
        return self._bipolar

    def to_bipolar(self) -> "BinaryHypervector":
        """Convert to bipolar {-1, +1} representation.

        Returns:
            New BinaryHypervector in bipolar form.

        Example:
            >>> import jax.numpy as jnp
            >>> vec = jnp.array([0, 1, 0, 1])
            >>> hv = BinaryHypervector(vec, bipolar=False)
            >>> bipolar_hv = hv.to_bipolar()
            >>> assert jnp.array_equal(bipolar_hv.vec, jnp.array([-1, 1, -1, 1]))
        """
        if self._bipolar:
            return self
        # Convert {0, 1} to {-1, +1}: 2*x - 1
        bipolar_vec = 2 * self._vec - 1
        return BinaryHypervector(bipolar_vec, bipolar=True)

    def to_binary(self) -> "BinaryHypervector":
        """Convert to binary {0, 1} representation.

        Returns:
            New BinaryHypervector in binary form.

        Example:
            >>> import jax.numpy as jnp
            >>> vec = jnp.array([-1, 1, -1, 1])
            >>> hv = BinaryHypervector(vec, bipolar=True)
            >>> binary_hv = hv.to_binary()
            >>> assert jnp.array_equal(binary_hv.vec, jnp.array([0, 1, 0, 1]))
        """
        if not self._bipolar:
            return self
        # Convert {-1, +1} to {0, 1}: (x + 1) / 2
        binary_vec = (self._vec + 1) // 2
        return BinaryHypervector(binary_vec, bipolar=False)
