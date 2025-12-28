"""Save VSAMemory basis vectors to JSON."""

import json
from pathlib import Path
from typing import Any, Union

from vsax.core.memory import VSAMemory
from vsax.representations.binary_hv import BinaryHypervector
from vsax.representations.complex_hv import ComplexHypervector
from vsax.representations.real_hv import RealHypervector


def save_basis(memory: VSAMemory, path: Union[str, Path]) -> None:
    """Save VSAMemory basis vectors to a JSON file.

    Args:
        memory: VSAMemory instance containing named basis vectors
        path: File path to save JSON (will be created/overwritten)

    Example:
        >>> model = create_fhrr_model(dim=128)
        >>> memory = VSAMemory(model)
        >>> memory.add_many(["apple", "orange", "banana"])
        >>> save_basis(memory, "fruit_basis.json")
    """
    path = Path(path)

    # Determine representation type
    rep_cls = memory.model.rep_cls
    if rep_cls == ComplexHypervector:
        rep_type = "complex"
    elif rep_cls == RealHypervector:
        rep_type = "real"
    elif rep_cls == BinaryHypervector:
        rep_type = "binary"
    else:
        raise ValueError(f"Unknown representation type: {rep_cls}")

    # Prepare data structure
    data: dict[str, Any] = {
        "metadata": {
            "dim": memory.model.dim,
            "rep_type": rep_type,
            "num_vectors": len(memory._symbols),
        },
        "vectors": {},
    }

    # Serialize each vector
    for name, hv in memory._symbols.items():
        vec = hv.vec

        if rep_type == "complex":
            # Split complex into real and imaginary parts
            data["vectors"][name] = {
                "real": vec.real.tolist(),
                "imag": vec.imag.tolist(),
            }
        elif rep_type == "real":
            # Store real vector
            data["vectors"][name] = vec.tolist()
        elif rep_type == "binary":
            # Store binary/bipolar vector as integers
            data["vectors"][name] = vec.astype(int).tolist()

    # Write to file
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
