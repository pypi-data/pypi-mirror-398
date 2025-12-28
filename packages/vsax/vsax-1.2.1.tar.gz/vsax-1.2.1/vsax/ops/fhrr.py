"""Fourier Holographic Reduced Representation operations."""

from typing import Union

import jax.numpy as jnp

from vsax.core.base import AbstractOpSet


class FHRROperations(AbstractOpSet):
    """FHRR operations using FFT-based circular convolution.

    Fourier Holographic Reduced Representation (FHRR) uses circular convolution
    for binding and complex addition for bundling. These operations work best
    with complex-valued hypervectors.

    Binding is implemented via circular convolution in the frequency domain:
        bind(a, b) = IFFT(FFT(a) ⊙ FFT(b))

    where ⊙ denotes element-wise multiplication.

    Example:
        >>> import jax
        >>> import jax.numpy as jnp
        >>> from vsax.representations import ComplexHypervector
        >>>
        >>> ops = FHRROperations()
        >>> key = jax.random.PRNGKey(0)
        >>> a = jnp.exp(1j * jax.random.uniform(key, (512,), minval=0, maxval=2*jnp.pi))
        >>> b = jnp.exp(1j * jax.random.uniform(key, (512,), minval=0, maxval=2*jnp.pi))
        >>>
        >>> bound = ops.bind(a, b)
        >>> assert bound.shape == a.shape
    """

    def bind(self, a: jnp.ndarray, b: jnp.ndarray) -> jnp.ndarray:
        """Bind two hypervectors using circular convolution.

        Implemented via FFT: IFFT(FFT(a) * FFT(b))

        This operation is:
        - Commutative: bind(a, b) = bind(b, a)
        - Associative: bind(a, bind(b, c)) = bind(bind(a, b), c)
        - Invertible: bind(bind(a, b), inverse(b)) ≈ a

        Args:
            a: First hypervector as JAX array.
            b: Second hypervector as JAX array.

        Returns:
            Bound hypervector as JAX array.

        Example:
            >>> import jax.numpy as jnp
            >>> ops = FHRROperations()
            >>> a = jnp.exp(1j * jnp.array([0.5, 1.0, 1.5]))
            >>> b = jnp.exp(1j * jnp.array([0.3, 0.7, 1.1]))
            >>> result = ops.bind(a, b)
            >>> assert jnp.iscomplexobj(result)
        """
        # Circular convolution via FFT
        fft_a = jnp.fft.fft(a)
        fft_b = jnp.fft.fft(b)
        return jnp.fft.ifft(fft_a * fft_b)

    def bundle(self, *vecs: jnp.ndarray) -> jnp.ndarray:
        """Bundle multiple hypervectors using complex addition and normalization.

        The bundled vector is similar to all input vectors and can be queried
        to retrieve the constituents.

        Args:
            *vecs: Variable number of hypervectors as JAX arrays.

        Returns:
            Bundled hypervector as JAX array, normalized to unit magnitude.

        Raises:
            ValueError: If no vectors are provided.

        Example:
            >>> import jax.numpy as jnp
            >>> ops = FHRROperations()
            >>> a = jnp.exp(1j * jnp.array([0.0, 0.5, 1.0]))
            >>> b = jnp.exp(1j * jnp.array([0.3, 0.7, 1.1]))
            >>> c = jnp.exp(1j * jnp.array([0.6, 0.9, 1.3]))
            >>> result = ops.bundle(a, b, c)
            >>> assert jnp.allclose(jnp.abs(result), 1.0, atol=0.1)
        """
        if len(vecs) == 0:
            raise ValueError("bundle() requires at least one vector")

        # Sum all vectors
        result = jnp.sum(jnp.stack(vecs), axis=0)

        # Normalize to unit magnitude (phase-only)
        return result / jnp.abs(result)

    def inverse(self, a: jnp.ndarray) -> jnp.ndarray:
        """Compute the inverse for unbinding.

        For complex vectors, the inverse is the complex conjugate.
        For real vectors, the inverse is the reversed vector (circular convolution inverse).

        Args:
            a: Hypervector as JAX array.

        Returns:
            Inverse hypervector as JAX array.

        Example:
            >>> import jax.numpy as jnp
            >>> ops = FHRROperations()
            >>> a = jnp.exp(1j * jnp.array([0.5, 1.0, 1.5]))
            >>> inv_a = ops.inverse(a)
            >>> # Binding with inverse should approximate identity
            >>> result = ops.bind(a, inv_a)
            >>> # Result should be close to all-ones vector (DC component)
        """
        if jnp.iscomplexobj(a):
            # Complex conjugate for complex vectors
            return jnp.conj(a)
        else:
            # Reverse for real vectors (circular convolution inverse)
            # Note: index 0 stays in place, rest are reversed
            return jnp.concatenate([a[:1], jnp.flip(a[1:])])

    def fractional_power(self, a: jnp.ndarray, exponent: Union[float, jnp.ndarray]) -> jnp.ndarray:
        """Raise complex hypervector to fractional power.

        For complex vectors v = exp(i*θ), this computes v^r = exp(i*r*θ).
        This enables continuous encoding of scalar values using phase rotation.

        Properties:
            - Continuous: small changes in exponent produce small output changes
            - Compositional: (v^r1)^r2 = v^(r1*r2)
            - Invertible: v^r ⊗ v^(-r) = identity

        This operation is fundamental for:
            - Fractional Power Encoding (FPE)
            - Spatial Semantic Pointers (SSP)
            - Vector Function Architecture (VFA)

        Args:
            a: Complex hypervector as JAX array.
            exponent: Scalar or array of exponents to raise the vector to.

        Returns:
            Hypervector raised to the given power as JAX array.

        Raises:
            TypeError: If input array is not complex-valued.

        Example:
            >>> import jax.numpy as jnp
            >>> ops = FHRROperations()
            >>> # Create a unit complex vector
            >>> a = jnp.exp(1j * jnp.array([0.5, 1.0, 1.5]))
            >>> # Raise to fractional power
            >>> powered = ops.fractional_power(a, 0.5)
            >>> # Test compositionality: (a^0.5)^2 ≈ a
            >>> composed = ops.fractional_power(powered, 2.0)
            >>> assert jnp.allclose(composed, a, atol=1e-6)
        """
        if not jnp.iscomplexobj(a):
            raise TypeError(
                "fractional_power only works with complex-valued arrays. "
                "Use ComplexHypervector for fractional power encoding."
            )
        return jnp.power(a, exponent)

    def permute(self, a: jnp.ndarray, shift: int) -> jnp.ndarray:
        """Permute a hypervector by circular rotation.

        Args:
            a: Hypervector as JAX array.
            shift: Number of positions to rotate (positive = right, negative = left).

        Returns:
            Permuted hypervector as JAX array.

        Example:
            >>> import jax.numpy as jnp
            >>> ops = FHRROperations()
            >>> a = jnp.array([1, 2, 3, 4, 5])
            >>> rotated = ops.permute(a, 2)
            >>> assert jnp.array_equal(rotated, jnp.array([4, 5, 1, 2, 3]))
        """
        return jnp.roll(a, shift)
