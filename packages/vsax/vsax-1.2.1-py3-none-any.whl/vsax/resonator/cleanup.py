"""Cleanup memory for VSA codebook projection.

Cleanup memory projects noisy vectors onto the nearest vector from a codebook,
similar to a Hopfield network's attractor dynamics.
"""

from typing import Optional, Union

import jax.numpy as jnp

from vsax.core import AbstractHypervector, VSAMemory


class CleanupMemory:
    """Cleanup memory for projecting vectors onto a codebook.

    This class implements codebook projection, which finds the nearest
    vector from a set of known vectors (codebook) to a query vector.

    Args:
        codebook: List of named symbols from VSAMemory to use as codebook.
        memory: VSAMemory containing the basis vectors.
        threshold: Optional similarity threshold for cleanup (default: 0.0).
                   If best match is below threshold, returns None.

    Example:
        >>> model = create_binary_model(dim=10000)
        >>> memory = VSAMemory(model)
        >>> memory.add_many(["red", "blue", "green"])
        >>> cleanup = CleanupMemory(["red", "blue", "green"], memory)
        >>> noisy = model.opset.bundle(memory["red"].vec, memory["blue"].vec)
        >>> result = cleanup.query(noisy)
        >>> print(result)  # Should return "red" or "blue"
    """

    def __init__(
        self,
        codebook: list[str],
        memory: VSAMemory,
        threshold: float = 0.0,
    ) -> None:
        """Initialize cleanup memory with codebook."""
        self.codebook = codebook
        self.memory = memory
        self.threshold = threshold

        # Validate codebook symbols exist in memory
        for symbol in codebook:
            if symbol not in memory:
                raise ValueError(f"Symbol '{symbol}' not found in memory")

        # Pre-compute codebook matrix for efficient lookup
        self._codebook_vecs = jnp.stack([memory[name].vec for name in codebook])

    def query(
        self,
        vec: Union[jnp.ndarray, AbstractHypervector],
        return_similarity: bool = False,
    ) -> Union[Optional[str], tuple[Optional[str], float]]:
        """Project vector onto codebook and return nearest symbol.

        Args:
            vec: Query vector to cleanup (array or hypervector).
            return_similarity: If True, also return similarity score.

        Returns:
            If return_similarity=False: Symbol name or None if below threshold.
            If return_similarity=True: Tuple of (symbol, similarity) or (None, similarity).

        Example:
            >>> result = cleanup.query(noisy_vec)
            >>> result_with_score = cleanup.query(noisy_vec, return_similarity=True)
            >>> print(result_with_score)  # ("red", 0.95)
        """
        # Coerce to array if hypervector
        if isinstance(vec, AbstractHypervector):
            vec = vec.vec

        # Compute similarities to all codebook vectors
        # For complex vectors, use conjugate dot product (inner product)
        # For real/binary vectors, use direct dot product
        if jnp.iscomplexobj(self._codebook_vecs):
            # Complex case: use conjugate dot product, then take abs for similarity
            similarities = jnp.abs(jnp.dot(self._codebook_vecs.conj(), vec))
        else:
            # Real/binary case: direct dot product
            similarities = jnp.dot(self._codebook_vecs, vec)

        # Find best match
        best_idx = int(jnp.argmax(similarities))
        best_sim = float(similarities[best_idx])

        # Check threshold
        if best_sim < self.threshold:
            return (None, best_sim) if return_similarity else None

        best_symbol = self.codebook[best_idx]
        return (best_symbol, best_sim) if return_similarity else best_symbol

    def query_top_k(
        self,
        vec: Union[jnp.ndarray, AbstractHypervector],
        k: int = 3,
    ) -> list[tuple[str, float]]:
        """Return top-k closest symbols with similarity scores.

        Args:
            vec: Query vector to cleanup.
            k: Number of top matches to return.

        Returns:
            List of (symbol, similarity) tuples sorted by similarity (descending).

        Example:
            >>> top_matches = cleanup.query_top_k(noisy_vec, k=3)
            >>> for symbol, sim in top_matches:
            ...     print(f"{symbol}: {sim:.3f}")
        """
        # Coerce to array if hypervector
        if isinstance(vec, AbstractHypervector):
            vec = vec.vec

        # Compute similarities
        if jnp.iscomplexobj(self._codebook_vecs):
            similarities = jnp.abs(jnp.dot(self._codebook_vecs.conj(), vec))
        else:
            similarities = jnp.dot(self._codebook_vecs, vec)

        # Get top-k indices
        top_k_indices = jnp.argsort(similarities)[-k:][::-1]

        # Build result list
        results = [(self.codebook[int(idx)], float(similarities[idx])) for idx in top_k_indices]

        return results

    def __len__(self) -> int:
        """Return number of vectors in codebook."""
        return len(self.codebook)

    def __repr__(self) -> str:
        """Return string representation."""
        return f"CleanupMemory(codebook_size={len(self.codebook)}, threshold={self.threshold})"
