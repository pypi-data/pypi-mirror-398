"""ScalarEncoder for encoding numeric values into hypervectors."""

from typing import Optional

import jax.numpy as jnp

from vsax.core.base import AbstractHypervector
from vsax.core.memory import VSAMemory
from vsax.core.model import VSAModel
from vsax.encoders.base import AbstractEncoder


class ScalarEncoder(AbstractEncoder):
    """Encoder for numeric scalar values using power encoding.

    For complex hypervectors (FHRR), encodes values by raising the basis
    hypervector to the power of the value, which rotates the phase.

    For real and binary hypervectors, encodes by iterated binding of the
    basis vector with itself.

    Attributes:
        model: The VSAModel instance defining the VSA algebra.
        memory: The VSAMemory instance for accessing basis hypervectors.
        min_val: Minimum value for the encoding range (optional).
        max_val: Maximum value for the encoding range (optional).

    Example:
        >>> from vsax import create_fhrr_model, VSAMemory
        >>> from vsax.encoders import ScalarEncoder
        >>> model = create_fhrr_model(dim=512)
        >>> memory = VSAMemory(model)
        >>> memory.add("temperature")
        >>> encoder = ScalarEncoder(model, memory)
        >>> temp_hv = encoder.encode("temperature", 23.5)
    """

    def __init__(
        self,
        model: VSAModel,
        memory: VSAMemory,
        min_val: Optional[float] = None,
        max_val: Optional[float] = None,
    ) -> None:
        """Initialize the ScalarEncoder.

        Args:
            model: The VSAModel instance.
            memory: The VSAMemory instance with basis symbols.
            min_val: Minimum value for normalization (optional).
            max_val: Maximum value for normalization (optional).
        """
        super().__init__(model, memory)
        self.min_val = min_val
        self.max_val = max_val

    def encode(self, symbol_name: str, value: float) -> AbstractHypervector:
        """Encode a scalar value.

        Args:
            symbol_name: Name of the basis symbol in memory to use.
            value: The numeric value to encode.

        Returns:
            The encoded hypervector.

        Raises:
            KeyError: If symbol_name is not in memory.
            ValueError: If value is outside the specified range.

        Example:
            >>> encoder = ScalarEncoder(model, memory)
            >>> temp_hv = encoder.encode("temperature", 23.5)
        """
        # Normalize value if range is specified
        if self.min_val is not None and self.max_val is not None:
            if not (self.min_val <= value <= self.max_val):
                raise ValueError(
                    f"Value {value} outside range [{self.min_val}, {self.max_val}]"
                )
            # Normalize to 0-1 range
            value = (value - self.min_val) / (self.max_val - self.min_val)

        # Get basis hypervector
        basis_hv = self.memory[symbol_name]

        # For complex hypervectors, use power encoding
        if jnp.iscomplexobj(basis_hv.vec):
            # Power encoding: v ** value rotates the phase
            powered_vec = jnp.power(basis_hv.vec, value)
            return self.model.rep_cls(powered_vec)

        # For real and binary hypervectors, use iterated binding
        # Bind the vector with itself 'value' times
        # For fractional values, we approximate with integer binding
        iterations = int(jnp.round(value * 10))  # Scale for finer granularity

        if iterations == 0:
            # Return normalized zero-like vector
            return basis_hv.normalize()

        result = basis_hv.vec
        for _ in range(iterations - 1):
            result = self.model.opset.bind(result, basis_hv.vec)

        return self.model.rep_cls(result)
