"""VSAX: JAX-native Vector Symbolic Algebra library.

VSAX provides composable symbolic representations using hypervectors, algebraic operations
for binding and bundling, and encoding strategies for symbolic and structured data.

Example:
    >>> from vsax import create_fhrr_model, VSAMemory
    >>>
    >>> # Create an FHRR model with factory function
    >>> model = create_fhrr_model(dim=512)
    >>>
    >>> # Create memory for symbol management
    >>> memory = VSAMemory(model)
    >>> memory.add_many(["dog", "cat", "animal"])
    >>>
    >>> # Access and manipulate symbols
    >>> dog = memory["dog"]
    >>> animal = memory["animal"]
    >>> dog_is_animal = model.opset.bind(dog.vec, animal.vec)
"""

__version__ = "1.2.1"

from vsax.core.base import AbstractHypervector, AbstractOpSet
from vsax.core.factory import create_binary_model, create_fhrr_model, create_map_model
from vsax.core.memory import VSAMemory
from vsax.core.model import VSAModel
from vsax.encoders import (
    AbstractEncoder,
    DictEncoder,
    GraphEncoder,
    ScalarEncoder,
    SequenceEncoder,
    SetEncoder,
)
from vsax.io import load_basis, save_basis
from vsax.ops import BinaryOperations, FHRROperations, MAPOperations
from vsax.representations import BinaryHypervector, ComplexHypervector, RealHypervector
from vsax.resonator import CleanupMemory, Resonator
from vsax.sampling import sample_binary_random, sample_complex_random, sample_random
from vsax.similarity import cosine_similarity, dot_similarity, hamming_similarity
from vsax.utils import (
    format_similarity_results,
    pretty_repr,
    vmap_bind,
    vmap_bundle,
    vmap_similarity,
)

__all__ = [
    # Core
    "AbstractHypervector",
    "AbstractOpSet",
    "VSAMemory",
    "VSAModel",
    # Factory Functions
    "create_binary_model",
    "create_fhrr_model",
    "create_map_model",
    # Encoders
    "AbstractEncoder",
    "DictEncoder",
    "GraphEncoder",
    "ScalarEncoder",
    "SequenceEncoder",
    "SetEncoder",
    # Representations
    "BinaryHypervector",
    "ComplexHypervector",
    "RealHypervector",
    # Operations
    "BinaryOperations",
    "FHRROperations",
    "MAPOperations",
    # Sampling
    "sample_binary_random",
    "sample_complex_random",
    "sample_random",
    # Similarity
    "cosine_similarity",
    "dot_similarity",
    "hamming_similarity",
    # Resonator
    "CleanupMemory",
    "Resonator",
    # I/O
    "load_basis",
    "save_basis",
    # Utilities
    "format_similarity_results",
    "pretty_repr",
    "vmap_bind",
    "vmap_bundle",
    "vmap_similarity",
    # Version
    "__version__",
]
