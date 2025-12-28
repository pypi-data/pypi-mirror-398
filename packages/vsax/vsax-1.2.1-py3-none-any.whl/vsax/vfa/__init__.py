"""Vector Function Architecture for computing with functions.

This module implements Vector Function Architecture (VFA) based on Frady et al. 2021,
enabling function approximation in Reproducing Kernel Hilbert Spaces (RKHS) using
hyperdimensional computing.
"""

from vsax.vfa.applications import (
    DensityEstimator,
    ImageProcessor,
    NonlinearRegressor,
)
from vsax.vfa.function_encoder import VectorFunctionEncoder
from vsax.vfa.kernels import (
    KernelConfig,
    KernelType,
    get_kernel_name,
    sample_kernel_basis,
    sample_kernel_basis_batch,
)

__all__ = [
    "KernelType",
    "KernelConfig",
    "sample_kernel_basis",
    "sample_kernel_basis_batch",
    "get_kernel_name",
    "VectorFunctionEncoder",
    "DensityEstimator",
    "NonlinearRegressor",
    "ImageProcessor",
]
