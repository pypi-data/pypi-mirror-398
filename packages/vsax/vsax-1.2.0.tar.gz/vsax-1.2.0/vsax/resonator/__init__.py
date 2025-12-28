"""Resonator networks for VSA factorization.

This module implements resonator networks as described in:
Frady, E. P., Kleyko, D., & Sommer, F. T. (2020).
A Theory of Sequence Indexing and Working Memory in Recurrent Neural Networks.
Neural Computation.

Resonator networks solve the factorization problem: given a composite vector
s = a ⊙ b ⊙ c, find the factors a, b, c from known codebooks.
"""

from vsax.resonator.cleanup import CleanupMemory
from vsax.resonator.resonator import Resonator

__all__ = [
    "CleanupMemory",
    "Resonator",
]
