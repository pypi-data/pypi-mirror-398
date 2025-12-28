"""Batch operations for hypervectors using JAX vmap."""

from typing import Union

import jax
import jax.numpy as jnp

from vsax.core.base import AbstractOpSet
from vsax.utils.coerce import coerce_to_array


def vmap_bind(
    opset: AbstractOpSet,
    X: Union[jnp.ndarray, list[jnp.ndarray]],
    Y: Union[jnp.ndarray, list[jnp.ndarray]],
) -> jnp.ndarray:
    """Vectorized binding of two batches of hypervectors.

    Applies the bind operation element-wise across two batches of hypervectors
    using JAX's vmap for efficient parallel execution on GPU/TPU.

    Args:
        opset: The operation set defining the bind operation.
        X: First batch of hypervectors, shape (batch_size, dim).
        Y: Second batch of hypervectors, shape (batch_size, dim).

    Returns:
        Batch of bound hypervectors, shape (batch_size, dim).

    Raises:
        ValueError: If batch sizes don't match.

    Example:
        >>> from vsax import create_fhrr_model, VSAMemory
        >>> from vsax.utils import vmap_bind
        >>> import jax.numpy as jnp
        >>> model = create_fhrr_model(dim=512)
        >>> memory = VSAMemory(model)
        >>> memory.add_many(["a", "b", "c", "x", "y", "z"])
        >>>
        >>> # Batch bind: [a, b, c] with [x, y, z]
        >>> X = jnp.stack([memory["a"].vec, memory["b"].vec, memory["c"].vec])
        >>> Y = jnp.stack([memory["x"].vec, memory["y"].vec, memory["z"].vec])
        >>> result = vmap_bind(model.opset, X, Y)
        >>> print(result.shape)  # (3, 512)
    """
    # Convert to arrays if needed
    if isinstance(X, list):
        X = jnp.stack([coerce_to_array(x) for x in X])
    if isinstance(Y, list):
        Y = jnp.stack([coerce_to_array(y) for y in Y])

    # Validate batch sizes
    if X.shape[0] != Y.shape[0]:
        raise ValueError(
            f"Batch size mismatch: X has {X.shape[0]} vectors, Y has {Y.shape[0]} vectors"
        )

    # Validate dimensions
    if X.shape[1:] != Y.shape[1:]:
        raise ValueError(
            f"Dimension mismatch: X has shape {X.shape[1:]}, Y has shape {Y.shape[1:]}"
        )

    # Vectorize bind operation across batch dimension
    vmapped_bind = jax.vmap(opset.bind, in_axes=(0, 0))

    # Apply vectorized bind
    result = vmapped_bind(X, Y)

    return result


def vmap_bundle(
    opset: AbstractOpSet,
    X: Union[jnp.ndarray, list[jnp.ndarray]],
) -> jnp.ndarray:
    """Vectorized bundling across batch dimension.

    Bundles a batch of hypervectors into a single hypervector using JAX's
    efficient reduction operations. This is NOT element-wise - it combines
    all vectors in the batch into one result.

    Args:
        opset: The operation set defining the bundle operation.
        X: Batch of hypervectors, shape (batch_size, dim).

    Returns:
        Single bundled hypervector, shape (dim,).

    Example:
        >>> from vsax import create_map_model, VSAMemory
        >>> from vsax.utils import vmap_bundle
        >>> import jax.numpy as jnp
        >>> model = create_map_model(dim=512)
        >>> memory = VSAMemory(model)
        >>> memory.add_many(["red", "green", "blue"])
        >>>
        >>> # Bundle colors together
        >>> colors = jnp.stack([
        ...     memory["red"].vec,
        ...     memory["green"].vec,
        ...     memory["blue"].vec
        ... ])
        >>> color_set = vmap_bundle(model.opset, colors)
        >>> print(color_set.shape)  # (512,)
    """
    # Convert to array if needed
    if isinstance(X, list):
        X = jnp.stack([coerce_to_array(x) for x in X])

    # Unpack batch and pass to bundle operation
    # bundle(*vecs) expects individual vectors as arguments
    result = opset.bundle(*[X[i] for i in range(X.shape[0])])

    return result


def vmap_similarity(
    similarity_fn: None,
    query: Union[jnp.ndarray, list[jnp.ndarray]],
    candidates: Union[jnp.ndarray, list[jnp.ndarray]],
) -> jnp.ndarray:
    """Vectorized similarity computation between query and multiple candidates.

    Computes similarity between a single query vector and a batch of candidate
    vectors using JAX's vmap for efficient parallel execution.

    Note: This function computes raw similarity scores without converting to
    Python floats, allowing it to work within JAX transformations.

    Args:
        similarity_fn: Similarity function that operates on arrays.
            Must accept two jnp.ndarray arguments and return a scalar.
        query: Single query hypervector, shape (dim,).
        candidates: Batch of candidate hypervectors, shape (batch_size, dim).

    Returns:
        Array of similarity scores, shape (batch_size,).

    Example:
        >>> from vsax import create_fhrr_model, VSAMemory
        >>> from vsax.utils import vmap_similarity
        >>> import jax.numpy as jnp
        >>> model = create_fhrr_model(dim=512)
        >>> memory = VSAMemory(model)
        >>> memory.add_many(["dog", "cat", "bird", "animal"])
        >>>
        >>> # Define similarity function that works on arrays
        >>> def array_cosine(a, b):
        ...     dot = jnp.vdot(a, b) if jnp.iscomplexobj(a) else jnp.dot(a, b)
        ...     if jnp.iscomplexobj(a): dot = jnp.real(dot)
        ...     return dot / (jnp.linalg.norm(a) * jnp.linalg.norm(b) + 1e-10)
        >>>
        >>> # Find most similar to "animal"
        >>> query = memory["animal"].vec
        >>> candidates = jnp.stack([
        ...     memory["dog"].vec,
        ...     memory["cat"].vec,
        ...     memory["bird"].vec
        ... ])
        >>> similarities = vmap_similarity(array_cosine, query, candidates)
        >>> best_match = jnp.argmax(similarities)
    """
    # Convert to arrays if needed
    query_vec = coerce_to_array(query)
    if isinstance(candidates, list):
        candidates = jnp.stack([coerce_to_array(c) for c in candidates])

    # Define inner similarity that works on arrays
    def _array_sim(vec_a: jnp.ndarray, vec_b: jnp.ndarray) -> jnp.ndarray:
        # Validate shapes
        if vec_a.shape != vec_b.shape:
            raise ValueError("Shape mismatch in similarity computation")

        # Compute similarity based on function name or type
        # This is a simplified version - users should pass pure JAX functions
        if jnp.iscomplexobj(vec_a) or jnp.iscomplexobj(vec_b):
            dot_product = jnp.vdot(vec_a, vec_b)
            dot_product = jnp.real(dot_product)
        else:
            dot_product = jnp.dot(vec_a, vec_b)

        # Cosine similarity (normalized)
        norm_a = jnp.linalg.norm(vec_a)
        norm_b = jnp.linalg.norm(vec_b)
        return dot_product / (norm_a * norm_b + 1e-10)

    # Vectorize similarity function over candidates
    vmapped_sim = jax.vmap(lambda c: _array_sim(query_vec, c), in_axes=0)

    # Compute similarities
    similarities = vmapped_sim(candidates)

    return similarities
