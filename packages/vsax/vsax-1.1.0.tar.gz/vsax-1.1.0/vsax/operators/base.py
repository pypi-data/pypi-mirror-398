"""Abstract base class for operators."""

from abc import ABC, abstractmethod

from vsax.core.base import AbstractHypervector


class AbstractOperator(ABC):
    """Abstract base class for all operators.

    Operators provide exact, compositional, invertible transformations
    for hypervectors. They represent "what happens" in a VSA system,
    while hypervectors represent "what exists".

    All concrete operator implementations must inherit from this class
    and implement the abstract methods: apply(), inverse(), and compose().

    Example:
        >>> from vsax.operators import CliffordOperator
        >>> import jax
        >>>
        >>> # Create operator
        >>> op = CliffordOperator.random(512, key=jax.random.PRNGKey(0))
        >>>
        >>> # Apply to hypervector
        >>> transformed = op.apply(hypervector)
        >>>
        >>> # Invert
        >>> original = op.inverse().apply(transformed)
    """

    @abstractmethod
    def apply(self, v: AbstractHypervector) -> AbstractHypervector:
        """Apply operator to hypervector.

        Transforms the input hypervector according to the operator's
        transformation rule. The specific transformation depends on the
        concrete operator implementation.

        Args:
            v: Hypervector to transform.

        Returns:
            Transformed hypervector of the same type as input.

        Raises:
            TypeError: If input hypervector type is not supported.
            ValueError: If dimensions don't match.
        """
        pass

    @abstractmethod
    def inverse(self) -> "AbstractOperator":
        """Return exact inverse operator.

        The inverse operator undoes the transformation of the original
        operator. For exact operators:

            op.inverse().apply(op.apply(v)) ≈ v

        with high precision (similarity > 0.999).

        Returns:
            Inverse operator that undoes this operator's transformation.
        """
        pass

    @abstractmethod
    def compose(self, other: "AbstractOperator") -> "AbstractOperator":
        """Compose with another operator.

        Creates a new operator that applies both transformations in sequence:

            composed = self.compose(other)
            composed.apply(v) ≈ self.apply(other.apply(v))

        Composition order follows mathematical convention (self ∘ other).

        Args:
            other: Operator to compose with.

        Returns:
            Composed operator representing both transformations.

        Raises:
            TypeError: If other is not compatible operator type.
            ValueError: If dimensions don't match.
        """
        pass

    @property
    @abstractmethod
    def dim(self) -> int:
        """Dimensionality of operator.

        Returns:
            Integer dimensionality that matches the hypervectors
            this operator can transform.
        """
        pass
