"""VSAModel dataclass for defining VSA algebras."""

from dataclasses import dataclass
from typing import Callable

import jax
import jax.numpy as jnp

from .base import AbstractHypervector, AbstractOpSet


@dataclass(frozen=True)
class VSAModel:
    """Immutable container defining a complete VSA algebra.

    VSAModel combines a representation type, operation set, and sampling function
    to define a complete VSA system. It does not perform operations itself, but
    serves as a configuration object used by VSAMemory and encoders.

    Attributes:
        dim: Dimensionality of all hypervectors in this model.
        rep_cls: The hypervector representation class (e.g., ComplexHypervector).
        opset: The operation set instance defining bind/bundle/inverse operations.
        sampler: Function to sample random vectors with signature
                 (dim: int, n: int, key: PRNGKey) -> jnp.ndarray.

    Example:
        >>> from vsax.representations import ComplexHypervector
        >>> from vsax.ops import FHRROperations
        >>> from vsax.sampling import sample_complex_random
        >>> model = VSAModel(
        ...     dim=512,
        ...     rep_cls=ComplexHypervector,
        ...     opset=FHRROperations(),
        ...     sampler=sample_complex_random
        ... )
    """

    dim: int
    rep_cls: type[AbstractHypervector]
    opset: AbstractOpSet
    sampler: Callable[[int, int, jax.random.PRNGKey], jnp.ndarray]

    def __post_init__(self) -> None:
        """Validate model parameters.

        Raises:
            ValueError: If dim is not positive.
        """
        if self.dim <= 0:
            raise ValueError(f"dim must be positive, got {self.dim}")
