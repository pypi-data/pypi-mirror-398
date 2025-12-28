"""Pretty printing utilities for hypervectors."""

from typing import Union

import jax.numpy as jnp

from vsax.core.base import AbstractHypervector
from vsax.utils.coerce import coerce_to_array


def pretty_repr(
    hv: Union[AbstractHypervector, jnp.ndarray],
    max_elements: int = 5,
) -> str:
    """Generate a pretty string representation of a hypervector.

    Creates a human-readable representation showing shape, dtype, and a sample
    of the vector values. Useful for debugging and interactive exploration.

    Args:
        hv: Hypervector to represent (AbstractHypervector or jnp.ndarray).
        max_elements: Maximum number of elements to display (default: 5).

    Returns:
        Formatted string representation.

    Example:
        >>> from vsax import create_fhrr_model, VSAMemory
        >>> from vsax.utils import pretty_repr
        >>> model = create_fhrr_model(dim=512)
        >>> memory = VSAMemory(model)
        >>> memory.add("example")
        >>> print(pretty_repr(memory["example"]))
        ComplexHypervector(dim=512, dtype=complex64)
        Sample: [0.123+0.456j, -0.789+0.234j, ..., 0.567-0.890j]
    """
    # Get the vector array
    vec = coerce_to_array(hv)

    # Determine type name
    if hasattr(hv, "__class__"):
        type_name = hv.__class__.__name__
    else:
        if jnp.iscomplexobj(vec):
            type_name = "ComplexVector"
        elif jnp.issubdtype(vec.dtype, jnp.floating):
            type_name = "RealVector"
        elif jnp.issubdtype(vec.dtype, jnp.integer):
            type_name = "BinaryVector"
        else:
            type_name = "Vector"

    # Build header
    dim = vec.size
    dtype = vec.dtype
    header = f"{type_name}(dim={dim}, dtype={dtype})"

    # Build sample values
    if dim <= max_elements:
        # Show all elements
        sample_str = _format_array(vec)
    else:
        # Show first and last few elements
        n_show = max_elements // 2
        first_part = _format_array(vec[:n_show])
        last_part = _format_array(vec[-n_show:])
        sample_str = f"{first_part}, ..., {last_part}"

    # Compute statistics
    if jnp.iscomplexobj(vec):
        magnitude = float(jnp.mean(jnp.abs(vec)))
        stats = f"Mean magnitude: {magnitude:.4f}"
    else:
        mean_val = float(jnp.mean(vec))
        std_val = float(jnp.std(vec))
        stats = f"Mean: {mean_val:.4f}, Std: {std_val:.4f}"

    # Combine into final representation
    result = f"{header}\nSample: [{sample_str}]\n{stats}"

    return result


def _format_array(arr: jnp.ndarray) -> str:
    """Format array elements for display."""
    if jnp.iscomplexobj(arr):
        # Format complex numbers
        elements = []
        for val in arr:
            real = float(val.real)
            imag = float(val.imag)
            if imag >= 0:
                elements.append(f"{real:.3f}+{imag:.3f}j")
            else:
                elements.append(f"{real:.3f}{imag:.3f}j")
        return ", ".join(elements)
    else:
        # Format real/binary numbers
        elements = [f"{float(val):.3f}" for val in arr]
        return ", ".join(elements)


def format_similarity_results(
    query_name: str,
    candidate_names: list[str],
    similarities: jnp.ndarray,
    top_k: int = 5,
) -> str:
    """Format similarity search results in a readable table.

    Args:
        query_name: Name of the query item.
        candidate_names: Names of candidate items.
        similarities: Array of similarity scores, shape (n_candidates,).
        top_k: Number of top results to display (default: 5).

    Returns:
        Formatted table string.

    Example:
        >>> from vsax.utils import format_similarity_results
        >>> import jax.numpy as jnp
        >>> results = format_similarity_results(
        ...     "dog",
        ...     ["cat", "wolf", "bird", "puppy"],
        ...     jnp.array([0.85, 0.92, 0.23, 0.95]),
        ...     top_k=3
        ... )
        >>> print(results)
        Query: dog
        Top 3 matches:
          1. puppy    0.950
          2. wolf     0.920
          3. cat      0.850
    """
    # Sort by similarity (descending)
    sorted_indices = jnp.argsort(similarities)[::-1]

    # Take top k
    top_indices = sorted_indices[:top_k]

    # Build table
    lines = [f"Query: {query_name}", f"Top {top_k} matches:"]

    for rank, idx in enumerate(top_indices, start=1):
        name = candidate_names[int(idx)]
        score = float(similarities[int(idx)])
        lines.append(f"  {rank}. {name:<12s} {score:.3f}")

    return "\n".join(lines)
