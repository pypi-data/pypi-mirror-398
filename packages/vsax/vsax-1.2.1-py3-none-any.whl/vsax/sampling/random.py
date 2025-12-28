"""Random sampling functions for generating basis hypervectors."""

from typing import Optional

import jax
import jax.numpy as jnp


def sample_random(dim: int, n: int, key: Optional[jax.random.PRNGKey] = None) -> jnp.ndarray:
    """Sample n random real-valued vectors from normal distribution.

    Generates random vectors with elements drawn from a standard normal
    distribution N(0, 1). These are suitable for use with MAP operations.

    Args:
        dim: Dimensionality of each vector.
        n: Number of vectors to sample.
        key: JAX random key. If None, uses PRNGKey(0).

    Returns:
        JAX array of shape (n, dim) containing sampled vectors.

    Example:
        >>> import jax
        >>> key = jax.random.PRNGKey(42)
        >>> vectors = sample_random(512, 10, key)
        >>> assert vectors.shape == (10, 512)
        >>> assert not jnp.iscomplexobj(vectors)
    """
    if key is None:
        key = jax.random.PRNGKey(0)

    return jax.random.normal(key, shape=(n, dim))


def sample_complex_random(
    dim: int, n: int, key: Optional[jax.random.PRNGKey] = None
) -> jnp.ndarray:
    """Sample n random complex-valued vectors with random phases.

    Generates unit-magnitude complex vectors with uniformly random phases
    in [0, 2π). These are suitable for use with FHRR operations.

    The vectors have the form: exp(i * θ) where θ ~ Uniform(0, 2π).

    Args:
        dim: Dimensionality of each vector.
        n: Number of vectors to sample.
        key: JAX random key. If None, uses PRNGKey(0).

    Returns:
        JAX array of shape (n, dim) containing complex unit-magnitude vectors.

    Example:
        >>> import jax
        >>> key = jax.random.PRNGKey(42)
        >>> vectors = sample_complex_random(512, 10, key)
        >>> assert vectors.shape == (10, 512)
        >>> assert jnp.iscomplexobj(vectors)
        >>> # All magnitudes should be 1.0
        >>> assert jnp.allclose(jnp.abs(vectors), 1.0)
    """
    if key is None:
        key = jax.random.PRNGKey(0)

    # Sample random phases uniformly in [0, 2π)
    phases = jax.random.uniform(key, shape=(n, dim), minval=0, maxval=2 * jnp.pi)

    # Convert to complex unit vectors
    return jnp.exp(1j * phases)


def sample_binary_random(
    dim: int, n: int, key: Optional[jax.random.PRNGKey] = None, bipolar: bool = True
) -> jnp.ndarray:
    """Sample n random binary vectors.

    Generates random binary vectors with values uniformly sampled from:
    - Bipolar mode: {-1, +1}
    - Binary mode: {0, 1}

    These are suitable for use with Binary VSA operations.

    Args:
        dim: Dimensionality of each vector.
        n: Number of vectors to sample.
        key: JAX random key. If None, uses PRNGKey(0).
        bipolar: If True, sample from {-1, +1}. If False, sample from {0, 1}.

    Returns:
        JAX array of shape (n, dim) containing binary values.

    Example:
        >>> import jax
        >>> key = jax.random.PRNGKey(42)
        >>>
        >>> # Bipolar sampling
        >>> bipolar_vecs = sample_binary_random(512, 10, key, bipolar=True)
        >>> assert bipolar_vecs.shape == (10, 512)
        >>> assert jnp.all(jnp.isin(bipolar_vecs, jnp.array([-1, 1])))
        >>>
        >>> # Binary sampling
        >>> binary_vecs = sample_binary_random(512, 10, key, bipolar=False)
        >>> assert jnp.all(jnp.isin(binary_vecs, jnp.array([0, 1])))
    """
    if key is None:
        key = jax.random.PRNGKey(0)

    if bipolar:
        # Sample from {-1, +1}
        return jax.random.choice(key, jnp.array([-1, 1]), shape=(n, dim))
    else:
        # Sample from {0, 1}
        return jax.random.choice(key, jnp.array([0, 1]), shape=(n, dim))
