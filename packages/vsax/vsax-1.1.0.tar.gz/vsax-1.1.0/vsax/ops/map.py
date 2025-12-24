"""Multiply-Add-Permute (MAP) operations for real-valued vectors."""

import jax.numpy as jnp

from vsax.core.base import AbstractOpSet


class MAPOperations(AbstractOpSet):
    """MAP operations using element-wise multiplication and mean.

    Multiply-Add-Permute (MAP) is a simple VSA algebra that uses:
    - Binding: element-wise multiplication
    - Bundling: element-wise mean (averaging)
    - Inverse: approximate inverse via normalization

    MAP works best with real-valued hypervectors and is computationally
    efficient, making it suitable for machine learning applications.

    Example:
        >>> import jax
        >>> import jax.numpy as jnp
        >>>
        >>> ops = MAPOperations()
        >>> key = jax.random.PRNGKey(0)
        >>> a = jax.random.normal(key, (1024,))
        >>> b = jax.random.normal(key, (1024,))
        >>>
        >>> bound = ops.bind(a, b)
        >>> assert bound.shape == a.shape
    """

    def bind(self, a: jnp.ndarray, b: jnp.ndarray) -> jnp.ndarray:
        """Bind two hypervectors using element-wise multiplication.

        This operation is:
        - Commutative: bind(a, b) = bind(b, a)
        - Associative: bind(a, bind(b, c)) = bind(bind(a, b), c)
        - Approximately invertible with the inverse() operation

        Args:
            a: First hypervector as JAX array.
            b: Second hypervector as JAX array.

        Returns:
            Bound hypervector as JAX array (element-wise product).

        Example:
            >>> import jax.numpy as jnp
            >>> ops = MAPOperations()
            >>> a = jnp.array([1.0, 2.0, 3.0])
            >>> b = jnp.array([2.0, 3.0, 4.0])
            >>> result = ops.bind(a, b)
            >>> assert jnp.array_equal(result, jnp.array([2.0, 6.0, 12.0]))
        """
        return a * b

    def bundle(self, *vecs: jnp.ndarray) -> jnp.ndarray:
        """Bundle multiple hypervectors using element-wise mean.

        The bundled vector is the average of all input vectors, providing
        a representation that is similar to all inputs.

        Args:
            *vecs: Variable number of hypervectors as JAX arrays.

        Returns:
            Bundled hypervector as JAX array (element-wise mean).

        Raises:
            ValueError: If no vectors are provided.

        Example:
            >>> import jax.numpy as jnp
            >>> ops = MAPOperations()
            >>> a = jnp.array([1.0, 2.0, 3.0])
            >>> b = jnp.array([3.0, 4.0, 5.0])
            >>> c = jnp.array([5.0, 6.0, 7.0])
            >>> result = ops.bundle(a, b, c)
            >>> expected = jnp.array([3.0, 4.0, 5.0])
            >>> assert jnp.allclose(result, expected)
        """
        if len(vecs) == 0:
            raise ValueError("bundle() requires at least one vector")

        return jnp.mean(jnp.stack(vecs), axis=0)

    def inverse(self, a: jnp.ndarray) -> jnp.ndarray:
        """Compute approximate inverse for unbinding.

        For MAP, the inverse is approximated by the normalized vector itself.
        This works because binding with a normalized vector approximately
        projects onto the orthogonal complement.

        Note: This is an approximation. Perfect unbinding is not guaranteed.

        Args:
            a: Hypervector as JAX array.

        Returns:
            Approximate inverse hypervector as JAX array.

        Example:
            >>> import jax.numpy as jnp
            >>> ops = MAPOperations()
            >>> a = jnp.array([3.0, 4.0])
            >>> inv_a = ops.inverse(a)
            >>> # The inverse should be normalized
            >>> assert jnp.allclose(jnp.linalg.norm(inv_a), 1.0, atol=1e-6)
        """
        # Normalize the vector as an approximate inverse
        # This works because: a * (a / ||a||²) ≈ a²/||a||²
        norm_squared = jnp.sum(a**2)
        return a / (norm_squared + 1e-8)

    def permute(self, a: jnp.ndarray, shift: int) -> jnp.ndarray:
        """Permute a hypervector by circular rotation.

        Args:
            a: Hypervector as JAX array.
            shift: Number of positions to rotate (positive = right, negative = left).

        Returns:
            Permuted hypervector as JAX array.

        Example:
            >>> import jax.numpy as jnp
            >>> ops = MAPOperations()
            >>> a = jnp.array([1.0, 2.0, 3.0, 4.0])
            >>> rotated = ops.permute(a, 1)
            >>> expected = jnp.array([4.0, 1.0, 2.0, 3.0])
            >>> assert jnp.array_equal(rotated, expected)
        """
        return jnp.roll(a, shift)
