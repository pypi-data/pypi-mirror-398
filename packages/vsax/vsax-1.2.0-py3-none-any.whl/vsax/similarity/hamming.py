"""Hamming similarity metric for binary hypervectors."""

from typing import Union

import jax.numpy as jnp

from vsax.core.base import AbstractHypervector
from vsax.utils.coerce import coerce_to_array


def hamming_similarity(
    a: Union[AbstractHypervector, jnp.ndarray],
    b: Union[AbstractHypervector, jnp.ndarray],
) -> float:
    """Compute Hamming similarity between two binary hypervectors.

    Hamming similarity measures the proportion of matching bits between two
    binary vectors. It ranges from 0 (completely different) to 1 (identical).

    Primarily designed for binary hypervectors but works with any vector type
    by comparing element equality. For best results, use with bipolar {-1, +1}
    or binary {0, 1} vectors.

    Args:
        a: First hypervector (AbstractHypervector or jnp.ndarray).
        b: Second hypervector (AbstractHypervector or jnp.ndarray).

    Returns:
        Hamming similarity as a float in range [0, 1].
        1.0 means all bits match, 0.0 means no bits match.

    Raises:
        ValueError: If vectors have different shapes.

    Example:
        >>> from vsax import create_binary_model, VSAMemory
        >>> from vsax.similarity import hamming_similarity
        >>> model = create_binary_model(dim=10000, bipolar=True)
        >>> memory = VSAMemory(model)
        >>> memory.add_many(["cat", "dog", "bird"])
        >>> similarity = hamming_similarity(memory["cat"], memory["dog"])
        >>> print(f"Hamming similarity: {similarity:.3f}")
    """
    # Coerce to arrays
    vec_a = coerce_to_array(a)
    vec_b = coerce_to_array(b)

    # Validate shapes
    if vec_a.shape != vec_b.shape:
        raise ValueError(
            f"Shape mismatch: vectors must have same shape, got {vec_a.shape} and {vec_b.shape}"
        )

    # Count matching elements
    matches = jnp.sum(vec_a == vec_b)

    # Normalize by vector dimension
    similarity = matches / vec_a.size

    # Return as Python float
    return float(similarity)
