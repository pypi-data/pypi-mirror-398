"""Binary VSA operations using XOR and majority voting."""

import jax.numpy as jnp

from vsax.core.base import AbstractOpSet


class BinaryOperations(AbstractOpSet):
    """Binary VSA operations for bipolar {-1, +1} vectors.

    Binary VSA uses:
    - Binding: XOR (element-wise multiplication in bipolar representation)
    - Bundling: Majority vote
    - Inverse: Self-inverse (XOR is its own inverse)

    This algebra is particularly efficient for hardware implementation and
    provides exact unbinding (unlike MAP).

    Note: Operations assume bipolar {-1, +1} encoding. For {0, 1} encoding,
    convert to bipolar first.

    Example:
        >>> import jax
        >>> import jax.numpy as jnp
        >>>
        >>> ops = BinaryOperations()
        >>> key = jax.random.PRNGKey(0)
        >>> a = jax.random.choice(key, jnp.array([-1, 1]), shape=(1024,))
        >>> b = jax.random.choice(key, jnp.array([-1, 1]), shape=(1024,))
        >>>
        >>> bound = ops.bind(a, b)
        >>> assert jnp.all(jnp.isin(bound, jnp.array([-1, 1])))
    """

    def bind(self, a: jnp.ndarray, b: jnp.ndarray) -> jnp.ndarray:
        """Bind two hypervectors using XOR (element-wise multiplication).

        In bipolar {-1, +1} representation, XOR is implemented as
        element-wise multiplication:
        - (+1) XOR (+1) = +1 (same)
        - (+1) XOR (-1) = -1 (different)
        - (-1) XOR (+1) = -1 (different)
        - (-1) XOR (-1) = +1 (same)

        This operation is:
        - Commutative: bind(a, b) = bind(b, a)
        - Associative: bind(a, bind(b, c)) = bind(bind(a, b), c)
        - Self-inverse: bind(bind(a, b), b) = a (exact unbinding)

        Args:
            a: First hypervector as JAX array (bipolar values).
            b: Second hypervector as JAX array (bipolar values).

        Returns:
            Bound hypervector as JAX array (bipolar values).

        Example:
            >>> import jax.numpy as jnp
            >>> ops = BinaryOperations()
            >>> a = jnp.array([1, -1, 1, -1])
            >>> b = jnp.array([1, 1, -1, -1])
            >>> result = ops.bind(a, b)
            >>> expected = jnp.array([1, -1, -1, 1])
            >>> assert jnp.array_equal(result, expected)
        """
        # XOR in bipolar is multiplication
        return a * b

    def bundle(self, *vecs: jnp.ndarray) -> jnp.ndarray:
        """Bundle multiple hypervectors using majority vote.

        Each element in the bundled vector is determined by the majority
        value at that position across all input vectors.

        For even counts, ties are broken by the sign of the sum.

        Args:
            *vecs: Variable number of hypervectors as JAX arrays (bipolar values).

        Returns:
            Bundled hypervector as JAX array (bipolar values).

        Raises:
            ValueError: If no vectors are provided.

        Example:
            >>> import jax.numpy as jnp
            >>> ops = BinaryOperations()
            >>> a = jnp.array([1, -1, 1, -1])
            >>> b = jnp.array([1, 1, -1, -1])
            >>> c = jnp.array([1, 1, 1, 1])
            >>> result = ops.bundle(a, b, c)
            >>> expected = jnp.array([1, 1, 1, -1])  # Majority at each position
            >>> assert jnp.array_equal(result, expected)
        """
        if len(vecs) == 0:
            raise ValueError("bundle() requires at least one vector")

        # Stack all vectors
        stacked = jnp.stack(vecs)

        # Sum across vectors (majority has positive/negative sum)
        summed = jnp.sum(stacked, axis=0)

        # Convert to bipolar: positive sum -> +1, negative sum -> -1
        # Use sign function (0 maps to 0, but we'll handle that)
        result = jnp.sign(summed)

        # Handle zeros (ties) by defaulting to +1
        result = jnp.where(result == 0, 1, result)

        return result.astype(jnp.int32)

    def inverse(self, a: jnp.ndarray) -> jnp.ndarray:
        """Compute the inverse for unbinding.

        For binary XOR, the inverse is the vector itself (self-inverse property).
        This means: bind(bind(a, b), b) = a (exact unbinding).

        Args:
            a: Hypervector as JAX array (bipolar values).

        Returns:
            Inverse hypervector (same as input for XOR).

        Example:
            >>> import jax.numpy as jnp
            >>> ops = BinaryOperations()
            >>> a = jnp.array([1, -1, 1, -1])
            >>> inv_a = ops.inverse(a)
            >>> assert jnp.array_equal(inv_a, a)
        """
        # XOR is self-inverse
        return a

    def permute(self, a: jnp.ndarray, shift: int) -> jnp.ndarray:
        """Permute a hypervector by circular rotation.

        Args:
            a: Hypervector as JAX array (bipolar values).
            shift: Number of positions to rotate (positive = right, negative = left).

        Returns:
            Permuted hypervector as JAX array.

        Example:
            >>> import jax.numpy as jnp
            >>> ops = BinaryOperations()
            >>> a = jnp.array([1, -1, 1, -1])
            >>> rotated = ops.permute(a, 1)
            >>> expected = jnp.array([-1, 1, -1, 1])
            >>> assert jnp.array_equal(rotated, expected)
        """
        return jnp.roll(a, shift)
