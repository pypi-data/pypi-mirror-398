"""Resonator network for VSA factorization.

Implements the resonator network algorithm from:
Frady, E. P., Kleyko, D., & Sommer, F. T. (2020).
"""

from typing import Optional, Union, cast

import jax.numpy as jnp

from vsax.core import AbstractHypervector, AbstractOpSet
from vsax.resonator.cleanup import CleanupMemory


class Resonator:
    """Resonator network for factorizing composite VSA vectors.

    Given a composite vector s = a ⊙ b ⊙ c, this class implements an
    iterative algorithm to find the factors a, b, c from known codebooks.

    The algorithm alternates between:
    1. Unbinding current estimates of other factors from s
    2. Cleaning up the result using codebook projection

    Args:
        codebooks: List of CleanupMemory objects, one per factor position.
        opset: Operation set defining bind/unbind operations.
        max_iterations: Maximum number of iterations (default: 100).
        convergence_threshold: Stop if estimates don't change (default: 3).

    Example:
        >>> model = create_binary_model(dim=10000)
        >>> memory = VSAMemory(model)
        >>> memory.add_many(["red", "blue", "circle", "square"])
        >>>
        >>> # Create codebooks for two factor positions
        >>> colors = CleanupMemory(["red", "blue"], memory)
        >>> shapes = CleanupMemory(["circle", "square"], memory)
        >>>
        >>> # Create composite: red ⊙ circle
        >>> composite = model.opset.bind(
        ...     memory["red"].vec,
        ...     memory["circle"].vec
        ... )
        >>>
        >>> # Factorize
        >>> resonator = Resonator([colors, shapes], model.opset)
        >>> factors = resonator.factorize(composite)
        >>> print(factors)  # ["red", "circle"]
    """

    def __init__(
        self,
        codebooks: list[CleanupMemory],
        opset: AbstractOpSet,
        max_iterations: int = 100,
        convergence_threshold: int = 3,
    ) -> None:
        """Initialize resonator network."""
        if len(codebooks) < 2:
            raise ValueError("Need at least 2 codebooks for factorization")

        self.codebooks = codebooks
        self.opset = opset
        self.max_iterations = max_iterations
        self.convergence_threshold = convergence_threshold
        self.num_factors = len(codebooks)

    def factorize(
        self,
        composite: Union[jnp.ndarray, AbstractHypervector],
        initial_estimates: Optional[list[str]] = None,
        return_history: bool = False,
    ) -> Union[list[Optional[str]], tuple[list[Optional[str]], list[list[Optional[str]]]]]:
        """Factorize a composite vector into its constituent factors.

        Args:
            composite: Composite vector to factorize.
            initial_estimates: Optional initial guesses for factors.
                              If None, uses superposition of all codebook vectors.
            return_history: If True, return iteration history.

        Returns:
            If return_history=False: List of factor names (or None if not converged).
            If return_history=True: Tuple of (factors, history) where history is
                                    a list of factor estimates at each iteration.

        Example:
            >>> factors = resonator.factorize(composite)
            >>> factors, history = resonator.factorize(composite, return_history=True)
        """
        # Coerce to array if hypervector
        if isinstance(composite, AbstractHypervector):
            composite = composite.vec

        # Initialize estimates
        estimates = self._initialize_estimates(initial_estimates)
        history: list[list[Optional[str]]] = [estimates.copy()] if return_history else []

        # Track convergence
        stable_count = 0
        prev_estimates = estimates.copy()

        # Iterative resonance
        for iteration in range(self.max_iterations):
            # Update each factor estimate
            for i in range(self.num_factors):
                estimates[i] = self._update_factor(composite, estimates, i)

            # Track history
            if return_history:
                history.append(estimates.copy())

            # Check convergence
            if estimates == prev_estimates:
                stable_count += 1
                if stable_count >= self.convergence_threshold:
                    break
            else:
                stable_count = 0
                prev_estimates = estimates.copy()

        # Return results
        if return_history:
            return estimates, history
        return estimates

    def _initialize_estimates(
        self,
        initial_estimates: Optional[list[str]] = None,
    ) -> list[Optional[str]]:
        """Initialize factor estimates.

        If initial_estimates provided, validate and use them.
        Otherwise, use None (superposition initialization happens in update).
        """
        if initial_estimates is not None:
            if len(initial_estimates) != self.num_factors:
                raise ValueError(
                    f"Expected {self.num_factors} initial estimates, got {len(initial_estimates)}"
                )
            # Validate estimates exist in codebooks
            for i, est in enumerate(initial_estimates):
                if est not in self.codebooks[i].codebook:
                    raise ValueError(f"Initial estimate '{est}' not in codebook {i}")
            # Cast to list[Optional[str]] for type compatibility
            return cast(list[Optional[str]], initial_estimates.copy())

        # Start with None (will use superposition in first iteration)
        return [None] * self.num_factors

    def _update_factor(
        self,
        composite: jnp.ndarray,
        current_estimates: list[Optional[str]],
        factor_idx: int,
    ) -> Optional[str]:
        """Update estimate for a single factor.

        Implements: x̂(t+1) = g(XX^T(s ⊙ ŷ(t) ⊙ ẑ(t)))

        Args:
            composite: The composite vector s.
            current_estimates: Current estimates for all factors.
            factor_idx: Which factor to update.

        Returns:
            Updated factor name or None.
        """
        # Start with composite vector
        residual = composite

        # Unbind all OTHER factors from composite
        # s ⊙ inverse(ŷ) ⊙ inverse(ẑ) should leave x̂
        for i, estimate_name in enumerate(current_estimates):
            if i == factor_idx:
                continue

            if estimate_name is None:
                # No estimate yet - use superposition of all vectors in codebook
                # This is the initialization from the paper
                codebook_vecs = self.codebooks[i]._codebook_vecs
                superposition = jnp.sum(codebook_vecs, axis=0)
                residual = self.opset.bind(residual, self.opset.inverse(superposition))
            else:
                # Use the current estimate
                factor_vec = self.codebooks[i].memory[estimate_name].vec
                residual = self.opset.bind(residual, self.opset.inverse(factor_vec))

        # Cleanup: project residual onto codebook for this factor
        # This is g(XX^T(...)) from the paper
        # query with return_similarity=False returns Optional[str]
        result: Optional[str] = self.codebooks[factor_idx].query(residual)  # type: ignore[assignment]

        return result

    def factorize_batch(
        self,
        composites: jnp.ndarray,
        initial_estimates: Optional[list[list[str]]] = None,
    ) -> list[list[Optional[str]]]:
        """Factorize multiple composite vectors.

        Args:
            composites: Array of composite vectors, shape (batch_size, dim).
            initial_estimates: Optional initial guesses for each composite.

        Returns:
            List of factor lists, one per composite.

        Example:
            >>> composites = jnp.stack([comp1, comp2, comp3])
            >>> all_factors = resonator.factorize_batch(composites)
        """
        batch_size = composites.shape[0]
        results: list[list[Optional[str]]] = []

        for i in range(batch_size):
            init = initial_estimates[i] if initial_estimates else None
            # factorize returns list[Optional[str]] when return_history=False (default)
            factors = self.factorize(composites[i], initial_estimates=init, return_history=False)
            # Type narrowing: we know it's just the list, not the tuple
            assert isinstance(factors, list), "Expected list without history"
            results.append(factors)

        return results

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"Resonator(num_factors={self.num_factors}, "
            f"max_iterations={self.max_iterations}, "
            f"convergence_threshold={self.convergence_threshold})"
        )
