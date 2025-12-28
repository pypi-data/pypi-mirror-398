"""Kernel functions for Vector Function Architecture.

Based on:
    Frady et al. 2021: "Computing on Functions Using Randomized Vector
    Representations"
"""

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional

import jax
import jax.numpy as jnp


class KernelType(Enum):
    """Kernel types for VFA basis vector sampling.

    Different kernel types correspond to different frequency sampling
    distributions, which affect the smoothness and approximation
    properties of encoded functions.

    Attributes:
        UNIFORM: Uniform distribution over unit circle (standard FHRR).
            Equivalent to sampling phases uniformly from [0, 2π).
            Default choice, works well for most applications.

        GAUSSIAN: Gaussian-weighted frequency distribution.
            Concentrates frequencies near center, produces smoother functions.
            Better for low-frequency functions.

        LAPLACE: Laplace (double exponential) distribution.
            Heavier tails than Gaussian, allows more high-frequency content.
            Good for functions with sharp features.

        CUSTOM: User-defined sampling function.
            Allows complete control over frequency distribution.
    """

    UNIFORM = "uniform"
    GAUSSIAN = "gaussian"
    LAPLACE = "laplace"
    CUSTOM = "custom"


@dataclass
class KernelConfig:
    """Configuration for VFA kernel basis vectors.

    Attributes:
        kernel_type: Type of kernel (UNIFORM, GAUSSIAN, LAPLACE, or CUSTOM).
        bandwidth: Kernel bandwidth parameter (default: 1.0).
            For GAUSSIAN: standard deviation of frequency distribution.
            For LAPLACE: scale parameter.
            For UNIFORM: ignored (uses full frequency range).
        dim: Dimensionality of basis vectors (default: 512).
        custom_sampler: Optional custom sampling function for CUSTOM kernel.
            Should have signature: (key, dim) -> complex array of shape (dim,)

    Example:
        >>> # Default: uniform kernel (standard FHRR)
        >>> config = KernelConfig()
        >>>
        >>> # Gaussian kernel with specific bandwidth
        >>> config = KernelConfig(
        ...     kernel_type=KernelType.GAUSSIAN,
        ...     bandwidth=2.0,
        ...     dim=1024
        ... )
    """

    kernel_type: KernelType = KernelType.UNIFORM
    bandwidth: float = 1.0
    dim: int = 512
    custom_sampler: Optional[Callable[[jax.Array, int], jnp.ndarray]] = None

    def __post_init__(self) -> None:
        """Validate configuration."""
        if self.bandwidth <= 0:
            raise ValueError(f"bandwidth must be positive, got {self.bandwidth}")
        if self.dim <= 0:
            raise ValueError(f"dim must be positive, got {self.dim}")
        if self.kernel_type == KernelType.CUSTOM and self.custom_sampler is None:
            raise ValueError("custom_sampler must be provided for CUSTOM kernel type")


def sample_kernel_basis(config: KernelConfig, key: jax.Array) -> jnp.ndarray:
    """Sample a basis vector according to kernel configuration.

    Generates a random complex hypervector with frequency distribution
    determined by the kernel type. For VFA, these basis vectors are raised
    to fractional powers to encode function values.

    Args:
        config: KernelConfig specifying kernel type and parameters.
        key: JAX random key for sampling.

    Returns:
        Complex array of shape (config.dim,) representing a basis vector.
        All elements have unit magnitude (phase-only representation).

    Raises:
        ValueError: If kernel_type is not recognized.

    Example:
        >>> key = jax.random.PRNGKey(42)
        >>> config = KernelConfig(kernel_type=KernelType.UNIFORM, dim=512)
        >>> basis = sample_kernel_basis(config, key)
        >>> assert basis.shape == (512,)
        >>> assert jnp.iscomplexobj(basis)
        >>> # All magnitudes should be 1.0
        >>> assert jnp.allclose(jnp.abs(basis), 1.0)

    Note:
        Currently only UNIFORM is fully implemented. GAUSSIAN and LAPLACE
        are placeholders for future extension.
    """
    if config.kernel_type == KernelType.UNIFORM:
        # Standard FHRR: sample phases uniformly from [0, 2π)
        phases = jax.random.uniform(key, shape=(config.dim,), minval=0, maxval=2 * jnp.pi)
        return jnp.exp(1j * phases)

    elif config.kernel_type == KernelType.GAUSSIAN:
        # Gaussian kernel: sample phases with Gaussian-weighted frequencies
        # For future implementation: sample frequencies from Gaussian,
        # then construct phases
        # For now, fall back to uniform
        phases = jax.random.uniform(key, shape=(config.dim,), minval=0, maxval=2 * jnp.pi)
        # TODO: Implement Gaussian frequency weighting
        # frequencies = jax.random.normal(key, (config.dim,)) * config.bandwidth
        # phases = ...
        return jnp.exp(1j * phases)

    elif config.kernel_type == KernelType.LAPLACE:
        # Laplace kernel: sample phases with Laplace-distributed frequencies
        # For future implementation
        phases = jax.random.uniform(key, shape=(config.dim,), minval=0, maxval=2 * jnp.pi)
        # TODO: Implement Laplace frequency weighting
        return jnp.exp(1j * phases)

    elif config.kernel_type == KernelType.CUSTOM:
        # Use custom sampler
        if config.custom_sampler is None:
            raise ValueError("custom_sampler must be provided for CUSTOM kernel")
        return config.custom_sampler(key, config.dim)

    else:
        raise ValueError(f"Unknown kernel type: {config.kernel_type}")


def sample_kernel_basis_batch(config: KernelConfig, key: jax.Array, n_vectors: int) -> jnp.ndarray:
    """Sample multiple basis vectors in batch.

    Convenience function for sampling multiple basis vectors at once,
    useful for initializing VFA encoders.

    Args:
        config: KernelConfig specifying kernel type and parameters.
        key: JAX random key for sampling.
        n_vectors: Number of basis vectors to sample.

    Returns:
        Complex array of shape (n_vectors, config.dim).

    Example:
        >>> key = jax.random.PRNGKey(42)
        >>> config = KernelConfig(dim=512)
        >>> bases = sample_kernel_basis_batch(config, key, n_vectors=10)
        >>> assert bases.shape == (10, 512)
    """
    keys = jax.random.split(key, n_vectors)
    return jnp.stack([sample_kernel_basis(config, k) for k in keys])


def get_kernel_name(kernel_type: KernelType) -> str:
    """Get human-readable name for kernel type.

    Args:
        kernel_type: KernelType enum value.

    Returns:
        String name of the kernel.

    Example:
        >>> get_kernel_name(KernelType.UNIFORM)
        'Uniform'
        >>> get_kernel_name(KernelType.GAUSSIAN)
        'Gaussian'
    """
    names = {
        KernelType.UNIFORM: "Uniform",
        KernelType.GAUSSIAN: "Gaussian",
        KernelType.LAPLACE: "Laplace",
        KernelType.CUSTOM: "Custom",
    }
    return names.get(kernel_type, "Unknown")
