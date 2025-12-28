"""Load VSAMemory basis vectors from JSON."""

import json
from pathlib import Path
from typing import Union

import jax.numpy as jnp

from vsax.core.memory import VSAMemory
from vsax.representations.binary_hv import BinaryHypervector
from vsax.representations.complex_hv import ComplexHypervector
from vsax.representations.real_hv import RealHypervector


def load_basis(memory: VSAMemory, path: Union[str, Path]) -> None:
    """Load basis vectors from a JSON file into VSAMemory.

    Args:
        memory: VSAMemory instance to populate (must be empty)
        path: File path to load JSON from

    Raises:
        ValueError: If dimension or representation type doesn't match
        ValueError: If memory is not empty
        FileNotFoundError: If file doesn't exist

    Example:
        >>> model = create_fhrr_model(dim=128)
        >>> memory = VSAMemory(model)
        >>> load_basis(memory, "fruit_basis.json")
        >>> "apple" in memory
        True
    """
    path = Path(path)

    # Check that memory is empty
    if len(memory._symbols) > 0:
        raise ValueError(
            f"Memory must be empty to load basis. "
            f"Current memory contains {len(memory._symbols)} vectors."
        )

    # Load JSON file
    with open(path) as f:
        data = json.load(f)

    # Validate metadata
    metadata = data["metadata"]
    saved_dim = metadata["dim"]
    saved_rep_type = metadata["rep_type"]

    # Check dimension matches
    if saved_dim != memory.model.dim:
        raise ValueError(
            f"Dimension mismatch: memory has dim={memory.model.dim}, but file has dim={saved_dim}"
        )

    # Check representation type matches
    rep_cls = memory.model.rep_cls
    if rep_cls == ComplexHypervector:
        expected_type = "complex"
    elif rep_cls == RealHypervector:
        expected_type = "real"
    elif rep_cls == BinaryHypervector:
        expected_type = "binary"
    else:
        raise ValueError(f"Unknown representation type: {rep_cls}")

    if saved_rep_type != expected_type:
        raise ValueError(
            f"Representation type mismatch: memory expects {expected_type}, "
            f"but file has {saved_rep_type}"
        )

    # Load vectors
    vectors_data = data["vectors"]

    for name, vec_data in vectors_data.items():
        if saved_rep_type == "complex":
            # Reconstruct complex vector from real and imaginary parts
            real_part = jnp.array(vec_data["real"], dtype=jnp.float32)
            imag_part = jnp.array(vec_data["imag"], dtype=jnp.float32)
            vec = real_part + 1j * imag_part
        elif saved_rep_type == "real":
            # Reconstruct real vector
            vec = jnp.array(vec_data, dtype=jnp.float32)
        elif saved_rep_type == "binary":
            # Reconstruct binary vector
            vec = jnp.array(vec_data, dtype=jnp.float32)
        else:
            raise ValueError(f"Unknown rep_type: {saved_rep_type}")

        # Create hypervector and add to memory
        hv = rep_cls(vec)
        memory._symbols[name] = hv
