"""Cosine similarity metric for hypervectors."""

from typing import Union

import jax.numpy as jnp

from vsax.core.base import AbstractHypervector
from vsax.utils.coerce import coerce_to_array


def cosine_similarity(
    a: Union[AbstractHypervector, jnp.ndarray],
    b: Union[AbstractHypervector, jnp.ndarray],
) -> float:
    """Compute cosine similarity between two hypervectors.

    Cosine similarity measures the cosine of the angle between two vectors,
    ranging from -1 (opposite) to 1 (identical direction). For complex vectors,
    uses the real part of the complex dot product.

    Works with all hypervector types:
    - Complex hypervectors (FHRR): Uses conjugate dot product
    - Real hypervectors (MAP): Standard cosine similarity
    - Binary hypervectors: Normalized dot product

    Args:
        a: First hypervector (AbstractHypervector or jnp.ndarray).
        b: Second hypervector (AbstractHypervector or jnp.ndarray).

    Returns:
        Cosine similarity as a float in range [-1, 1].

    Raises:
        ValueError: If vectors have different shapes.

    Example:
        >>> from vsax import create_fhrr_model, VSAMemory
        >>> from vsax.similarity import cosine_similarity
        >>> model = create_fhrr_model(dim=512)
        >>> memory = VSAMemory(model)
        >>> memory.add_many(["dog", "cat", "animal"])
        >>> similarity = cosine_similarity(memory["dog"], memory["cat"])
        >>> print(f"Similarity: {similarity:.3f}")
    """
    # Coerce to arrays
    vec_a = coerce_to_array(a)
    vec_b = coerce_to_array(b)

    # Validate shapes
    if vec_a.shape != vec_b.shape:
        raise ValueError(
            f"Shape mismatch: vectors must have same shape, got {vec_a.shape} and {vec_b.shape}"
        )

    # Compute dot product (handles complex automatically)
    if jnp.iscomplexobj(vec_a) or jnp.iscomplexobj(vec_b):
        # Complex dot product: a* · b (conjugate of a dot b)
        dot_product = jnp.vdot(vec_a, vec_b)
        # Take real part for similarity
        dot_product = jnp.real(dot_product)
    else:
        # Real dot product
        dot_product = jnp.dot(vec_a, vec_b)

    # Compute magnitudes
    norm_a = jnp.linalg.norm(vec_a)
    norm_b = jnp.linalg.norm(vec_b)

    # Avoid division by zero
    epsilon = 1e-10
    cosine_sim = dot_product / (norm_a * norm_b + epsilon)

    # Return as Python float
    return float(cosine_sim)
