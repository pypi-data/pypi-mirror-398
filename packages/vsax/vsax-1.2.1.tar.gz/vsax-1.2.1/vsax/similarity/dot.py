"""Dot product similarity metric for hypervectors."""

from typing import Union

import jax.numpy as jnp

from vsax.core.base import AbstractHypervector
from vsax.utils.coerce import coerce_to_array


def dot_similarity(
    a: Union[AbstractHypervector, jnp.ndarray],
    b: Union[AbstractHypervector, jnp.ndarray],
) -> float:
    """Compute dot product similarity between two hypervectors.

    The dot product provides an unnormalized similarity measure. Higher values
    indicate more similarity. For complex vectors, uses the real part of the
    complex dot product (conjugate dot product).

    Works with all hypervector types:
    - Complex hypervectors (FHRR): Real part of a* · b
    - Real hypervectors (MAP): Standard dot product a · b
    - Binary hypervectors: Dot product (count of matching bits)

    Args:
        a: First hypervector (AbstractHypervector or jnp.ndarray).
        b: Second hypervector (AbstractHypervector or jnp.ndarray).

    Returns:
        Dot product similarity as a float.

    Raises:
        ValueError: If vectors have different shapes.

    Example:
        >>> from vsax import create_map_model, VSAMemory
        >>> from vsax.similarity import dot_similarity
        >>> model = create_map_model(dim=512)
        >>> memory = VSAMemory(model)
        >>> memory.add_many(["apple", "orange", "fruit"])
        >>> similarity = dot_similarity(memory["apple"], memory["orange"])
        >>> print(f"Dot product: {similarity:.3f}")
    """
    # Coerce to arrays
    vec_a = coerce_to_array(a)
    vec_b = coerce_to_array(b)

    # Validate shapes
    if vec_a.shape != vec_b.shape:
        raise ValueError(
            f"Shape mismatch: vectors must have same shape, got {vec_a.shape} and {vec_b.shape}"
        )

    # Compute dot product
    if jnp.iscomplexobj(vec_a) or jnp.iscomplexobj(vec_b):
        # Complex dot product: a* · b (conjugate of a dot b)
        dot_product = jnp.vdot(vec_a, vec_b)
        # Take real part
        result = jnp.real(dot_product)
    else:
        # Real dot product
        result = jnp.dot(vec_a, vec_b)

    # Return as Python float
    return float(result)
