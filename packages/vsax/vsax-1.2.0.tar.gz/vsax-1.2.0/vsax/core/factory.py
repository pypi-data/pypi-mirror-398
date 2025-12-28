"""Factory functions for creating VSA models with sensible defaults."""

from typing import Optional

import jax

from vsax.core.model import VSAModel
from vsax.ops import BinaryOperations, FHRROperations, MAPOperations
from vsax.representations import BinaryHypervector, ComplexHypervector, RealHypervector
from vsax.sampling import sample_binary_random, sample_complex_random, sample_random


def create_fhrr_model(dim: int = 512, key: Optional[jax.Array] = None) -> VSAModel:
    """Create a FHRR model (Complex hypervectors with FFT-based operations).

    FHRR (Fourier Holographic Reduced Representation) uses complex-valued
    hypervectors with circular convolution for binding. It provides exact
    unbinding via complex conjugation.

    Args:
        dim: Dimensionality of hypervectors. Default: 512.
        key: Optional JAX PRNG key for reproducible sampling. Not used in
            model creation but can be passed to VSAMemory.

    Returns:
        VSAModel configured for FHRR operations.

    Example:
        >>> from vsax import create_fhrr_model, VSAMemory
        >>> model = create_fhrr_model(dim=512)
        >>> memory = VSAMemory(model)
        >>> memory.add("symbol")
    """
    return VSAModel(
        dim=dim,
        rep_cls=ComplexHypervector,
        opset=FHRROperations(),
        sampler=sample_complex_random,
    )


def create_map_model(dim: int = 512, key: Optional[jax.Array] = None) -> VSAModel:
    """Create a MAP model (Real hypervectors with element-wise operations).

    MAP (Multiply-Add-Permute) uses real-valued hypervectors with
    element-wise multiplication for binding and averaging for bundling.
    It provides approximate unbinding.

    Args:
        dim: Dimensionality of hypervectors. Default: 512.
        key: Optional JAX PRNG key for reproducible sampling. Not used in
            model creation but can be passed to VSAMemory.

    Returns:
        VSAModel configured for MAP operations.

    Example:
        >>> from vsax import create_map_model, VSAMemory
        >>> model = create_map_model(dim=1024)
        >>> memory = VSAMemory(model)
        >>> memory.add_many(["red", "green", "blue"])
    """
    return VSAModel(
        dim=dim,
        rep_cls=RealHypervector,
        opset=MAPOperations(),
        sampler=sample_random,
    )


def create_binary_model(
    dim: int = 10000, bipolar: bool = True, key: Optional[jax.Array] = None
) -> VSAModel:
    """Create a Binary model (Binary hypervectors with XOR/majority operations).

    Binary VSA uses discrete {-1, +1} (bipolar) or {0, 1} (binary) hypervectors
    with XOR for binding and majority voting for bundling. It provides exact
    unbinding (self-inverse property).

    Note: Binary models typically require higher dimensionality (10000+) for
    good performance due to discrete representation.

    Args:
        dim: Dimensionality of hypervectors. Default: 10000 (higher than
            continuous models due to discrete representation).
        bipolar: If True, use {-1, +1} representation. If False, use {0, 1}.
            Default: True (bipolar is more common).
        key: Optional JAX PRNG key for reproducible sampling. Not used in
            model creation but can be passed to VSAMemory.

    Returns:
        VSAModel configured for Binary operations.

    Example:
        >>> from vsax import create_binary_model, VSAMemory
        >>> model = create_binary_model(dim=10000, bipolar=True)
        >>> memory = VSAMemory(model)
        >>> memory.add("concept")
    """

    # Create a wrapper sampler that passes bipolar parameter
    def binary_sampler(dim: int, n: int, key: jax.Array) -> jax.Array:
        """Wrapper sampler that includes bipolar parameter."""
        return sample_binary_random(dim=dim, n=n, key=key, bipolar=bipolar)

    return VSAModel(
        dim=dim,
        rep_cls=BinaryHypervector,
        opset=BinaryOperations(),
        sampler=binary_sampler,
    )
