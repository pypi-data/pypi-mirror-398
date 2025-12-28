"""Clifford-inspired operator for FHRR hypervectors."""

from dataclasses import dataclass
from typing import Optional

import jax
import jax.numpy as jnp

from vsax.core.base import AbstractHypervector
from vsax.operators.base import AbstractOperator
from vsax.operators.kinds import OperatorKind, OperatorMetadata
from vsax.representations import ComplexHypervector


@dataclass(frozen=True)
class CliffordOperator(AbstractOperator):
    """Clifford-inspired operator for FHRR hypervectors.

    Represents a phase-based transformation that compiles to FHRR operations.
    The operator applies element-wise phase rotation to complex hypervectors:

        apply(v) = v * exp(i * params)

    This provides exact, compositional, invertible transformations inspired
    by Clifford algebra, where:
    - Elementary operators act as bivectors (phase generators)
    - Composed operators act as rotors (sum of generators)
    - Operator composition uses phase addition
    - Inversion uses phase negation

    The operator is compatible with FHRR's phase algebra and preserves
    the unit-magnitude property of complex hypervectors.

    Attributes:
        params: Phase rotation parameters as JAX array (shape: dim).
                Each element specifies the phase shift for that dimension.
        metadata: Optional semantic metadata (kind, name, description).

    Example:
        >>> from vsax import create_fhrr_model, VSAMemory
        >>> from vsax.operators import CliffordOperator
        >>> import jax
        >>>
        >>> model = create_fhrr_model(dim=512)
        >>> memory = VSAMemory(model)
        >>> memory.add("test")
        >>>
        >>> # Create operator
        >>> op = CliffordOperator.random(512, key=jax.random.PRNGKey(0))
        >>>
        >>> # Apply transformation
        >>> transformed = op.apply(memory["test"])
        >>>
        >>> # Verify exact inversion
        >>> recovered = op.inverse().apply(transformed)
        >>> from vsax.similarity import cosine_similarity
        >>> similarity = cosine_similarity(recovered.vec, memory["test"].vec)
        >>> assert similarity > 0.999  # Exact inverse
    """

    params: jnp.ndarray
    metadata: Optional[OperatorMetadata] = None

    def __post_init__(self) -> None:
        """Validate and convert parameters to JAX array."""
        # Ensure params is JAX array
        if not isinstance(self.params, jnp.ndarray):
            object.__setattr__(self, "params", jnp.array(self.params))

        # Validate shape
        if len(self.params.shape) != 1:
            raise ValueError(f"params must be 1-dimensional, got shape {self.params.shape}")

    @property
    def dim(self) -> int:
        """Dimensionality of operator.

        Returns:
            Integer dimension matching the hypervectors this operator
            can transform.
        """
        return int(self.params.shape[0])

    def apply(self, v: AbstractHypervector) -> ComplexHypervector:
        """Apply phase rotation to hypervector.

        Transforms the input hypervector by applying element-wise phase rotation:

            result = v * exp(i * params)

        This operation is:
        - Norm-preserving (maintains unit magnitude for FHRR)
        - Exactly invertible
        - Compatible with FHRR circular convolution

        Args:
            v: ComplexHypervector to transform. Must have same dimensionality
               as operator.

        Returns:
            Transformed ComplexHypervector with same shape as input.

        Raises:
            TypeError: If v is not a ComplexHypervector. CliffordOperator only
                       works with FHRR (complex-valued) representations.
            ValueError: If dimension of v doesn't match operator dimension.

        Example:
            >>> from vsax import create_fhrr_model, VSAMemory
            >>> from vsax.operators import CliffordOperator
            >>> import jax
            >>>
            >>> model = create_fhrr_model(dim=512)
            >>> memory = VSAMemory(model)
            >>> memory.add("test")
            >>>
            >>> op = CliffordOperator.random(512, key=jax.random.PRNGKey(0))
            >>> transformed = op.apply(memory["test"])
            >>> print(transformed.shape)
            (512,)
        """
        if not isinstance(v, ComplexHypervector):
            raise TypeError(
                f"CliffordOperator only works with ComplexHypervector "
                f"(FHRR model), got {type(v).__name__}. "
                f"Hint: Use create_fhrr_model() to create compatible hypervectors."
            )

        if v.vec.shape[0] != self.dim:
            raise ValueError(
                f"Dimension mismatch: operator has dim={self.dim}, "
                f"hypervector has dim={v.vec.shape[0]}"
            )

        # Apply phase rotation: v * exp(i * params)
        # This is compatible with FHRR's phase-based algebra
        phase_shift = jnp.exp(1j * self.params)
        transformed = v.vec * phase_shift

        return ComplexHypervector(transformed)

    def inverse(self) -> "CliffordOperator":
        """Return exact inverse operator.

        For phase rotations, the inverse is phase negation:

            inverse(params) = -params
            exp(i * (-params)) = exp(-i * params) = conj(exp(i * params))

        This provides exact inversion with similarity > 0.999:

            op.inverse().apply(op.apply(v)) ≈ v

        Returns:
            CliffordOperator with negated phase parameters that exactly
            undoes this operator's transformation.

        Example:
            >>> from vsax import create_fhrr_model, VSAMemory
            >>> from vsax.operators import CliffordOperator
            >>> from vsax.similarity import cosine_similarity
            >>> import jax
            >>>
            >>> model = create_fhrr_model(dim=512)
            >>> memory = VSAMemory(model)
            >>> memory.add("test")
            >>>
            >>> op = CliffordOperator.random(512, key=jax.random.PRNGKey(0))
            >>> transformed = op.apply(memory["test"])
            >>> recovered = op.inverse().apply(transformed)
            >>>
            >>> similarity = cosine_similarity(recovered.vec, memory["test"].vec)
            >>> print(f"Inversion accuracy: {similarity:.6f}")
            Inversion accuracy: 1.000000
        """
        return CliffordOperator(params=-self.params, metadata=self.metadata)

    def compose(self, other: AbstractOperator) -> "CliffordOperator":
        """Compose two operators.

        Creates a new operator that applies both transformations in sequence.
        For phase-based operators, composition uses phase addition:

            compose(op1, op2).params = op1.params + op2.params
            exp(i * (params1 + params2)) applies both rotations

        Composition is:
        - Associative: (op1 ∘ op2) ∘ op3 = op1 ∘ (op2 ∘ op3)
        - Commutative: op1 ∘ op2 = op2 ∘ op1 (for phase addition)

        Args:
            other: Another CliffordOperator to compose with. Must have
                   same dimensionality.

        Returns:
            Composed CliffordOperator representing both transformations.

        Raises:
            TypeError: If other is not a CliffordOperator.
            ValueError: If dimensions don't match.

        Example:
            >>> from vsax.operators import CliffordOperator
            >>> import jax
            >>>
            >>> op1 = CliffordOperator.random(512, name="OP1",
            ...                               key=jax.random.PRNGKey(0))
            >>> op2 = CliffordOperator.random(512, name="OP2",
            ...                               key=jax.random.PRNGKey(1))
            >>>
            >>> composed = op1.compose(op2)
            >>> print(composed.metadata.name)
            compose(OP1, OP2)
        """
        if not isinstance(other, CliffordOperator):
            raise TypeError(f"Can only compose with CliffordOperator, got {type(other).__name__}")

        if self.dim != other.dim:
            raise ValueError(
                f"Dimension mismatch: self has dim={self.dim}, other has dim={other.dim}"
            )

        # Compose by adding phases
        composed_params = self.params + other.params

        # Create metadata for composed operator
        if self.metadata or other.metadata:
            self_name = self.metadata.name if self.metadata else "op1"
            other_name = other.metadata.name if other.metadata else "op2"
            composed_metadata = OperatorMetadata(
                kind=OperatorKind.TRANSFORM,
                name=f"compose({self_name}, {other_name})",
                description="Composed operator",
            )
        else:
            composed_metadata = None

        return CliffordOperator(params=composed_params, metadata=composed_metadata)

    @staticmethod
    def random(
        dim: int,
        kind: OperatorKind = OperatorKind.GENERAL,
        name: str = "random_op",
        key: Optional[jax.Array] = None,
    ) -> "CliffordOperator":
        """Create random operator with uniform phase distribution.

        Samples phase parameters uniformly from [0, 2π) to create a random
        operator. Useful for generating basis operators for spatial relations,
        semantic roles, or other symbolic transformations.

        Args:
            dim: Dimensionality of the operator.
            kind: Semantic type of the operator (default: GENERAL).
            name: Human-readable name for the operator.
            key: JAX random key for reproducibility. If None, uses key(0).

        Returns:
            Random CliffordOperator with uniformly distributed phase parameters.

        Example:
            >>> from vsax.operators import CliffordOperator, OperatorKind
            >>> import jax
            >>>
            >>> # Create reproducible random operator
            >>> op = CliffordOperator.random(
            ...     dim=512,
            ...     kind=OperatorKind.SPATIAL,
            ...     name="LEFT_OF",
            ...     key=jax.random.PRNGKey(42)
            ... )
            >>> print(op.metadata.name)
            LEFT_OF
        """
        if key is None:
            key = jax.random.PRNGKey(0)

        # Sample uniform phases in [0, 2π)
        params = jax.random.uniform(key, (dim,), minval=0, maxval=2 * jnp.pi)

        metadata = OperatorMetadata(kind=kind, name=name)
        return CliffordOperator(params=params, metadata=metadata)

    def __repr__(self) -> str:
        """String representation of operator.

        Returns:
            String showing operator name, dimension, and kind.
        """
        name = self.metadata.name if self.metadata else "CliffordOperator"
        kind = self.metadata.kind.value if self.metadata else "unknown"
        return f"{name}(dim={self.dim}, kind={kind})"
