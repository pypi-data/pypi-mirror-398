"""Type coercion utilities for hypervectors and arrays."""

from typing import Union

import jax.numpy as jnp

from vsax.core.base import AbstractHypervector


def coerce_to_array(obj: Union[AbstractHypervector, jnp.ndarray]) -> jnp.ndarray:
    """Coerce a hypervector or array to a JAX array.

    Args:
        obj: Either an AbstractHypervector or a JAX array.

    Returns:
        JAX array (unwrapped if input was a hypervector).

    Example:
        >>> from vsax import ComplexHypervector
        >>> import jax.numpy as jnp
        >>> vec = jnp.array([1+2j, 3+4j])
        >>> hv = ComplexHypervector(vec)
        >>> arr = coerce_to_array(hv)
        >>> assert isinstance(arr, jnp.ndarray)
    """
    if isinstance(obj, AbstractHypervector):
        return obj.vec
    return obj
