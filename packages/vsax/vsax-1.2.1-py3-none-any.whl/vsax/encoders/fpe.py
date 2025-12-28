"""FractionalPowerEncoder for continuous spatial and function encoding."""

from typing import Optional

import jax.numpy as jnp

from vsax.core.memory import VSAMemory
from vsax.core.model import VSAModel
from vsax.encoders.base import AbstractEncoder
from vsax.representations import ComplexHypervector


class FractionalPowerEncoder(AbstractEncoder):
    """Fractional power encoder for continuous spatial and function encoding.

    This encoder uses fractional powers of complex hypervectors to encode
    continuous values. It only works with ComplexHypervector (FHRR) models
    since they support true fractional power encoding via phase rotation.

    For a basis vector v = exp(i*θ) and value r:
        encode(v, r) = v^r = exp(i*r*θ)

    This is the foundation for:
        - Spatial Semantic Pointers (SSP): S(x, y) = X^x ⊗ Y^y
        - Vector Function Architecture (VFA): f(x) = Σ α_i * z_i^x

    Properties:
        - Continuous: small changes in value produce small output changes
        - Compositional: (v^r1)^r2 = v^(r1*r2)
        - Invertible: v^r ⊗ v^(-r) gives identity-like pattern

    Attributes:
        model: The VSAModel instance (must use ComplexHypervector).
        memory: The VSAMemory instance for accessing basis hypervectors.
        scale: Optional scaling factor for encoded values.

    Example:
        >>> from vsax import create_fhrr_model, VSAMemory
        >>> from vsax.encoders import FractionalPowerEncoder
        >>> model = create_fhrr_model(dim=512)
        >>> memory = VSAMemory(model)
        >>> memory.add("x")
        >>> encoder = FractionalPowerEncoder(model, memory)
        >>> x_pos = encoder.encode("x", 3.5)  # x^3.5

    See Also:
        - Komer et al. 2019: "A neural representation of continuous space
          using fractional binding"
        - Frady et al. 2021: "Computing on Functions Using Randomized
          Vector Representations"
    """

    def __init__(
        self,
        model: VSAModel,
        memory: VSAMemory,
        scale: Optional[float] = None,
    ) -> None:
        """Initialize the FractionalPowerEncoder.

        Args:
            model: The VSAModel instance (must use ComplexHypervector).
            memory: The VSAMemory instance with basis symbols.
            scale: Optional scaling factor applied to all encoded values.
                   If provided, encoded value becomes: basis^(value * scale)

        Raises:
            TypeError: If model does not use ComplexHypervector representation.

        Example:
            >>> model = create_fhrr_model(dim=512)
            >>> memory = VSAMemory(model)
            >>> encoder = FractionalPowerEncoder(model, memory, scale=0.1)
        """
        super().__init__(model, memory)

        # Verify model uses ComplexHypervector
        if model.rep_cls != ComplexHypervector:
            raise TypeError(
                "FractionalPowerEncoder requires ComplexHypervector (FHRR) model. "
                f"Got {model.rep_cls.__name__}. "
                "Use create_fhrr_model() to create a compatible model."
            )

        self.scale = scale

    def encode(self, symbol_name: str, value: float) -> ComplexHypervector:
        """Encode a single continuous value using fractional power.

        For basis vector v and value r:
            result = v^r = v^(r * scale) if scale is set

        Args:
            symbol_name: Name of the basis symbol in memory to use.
            value: The continuous value to encode.

        Returns:
            The encoded complex hypervector: basis^value

        Raises:
            KeyError: If symbol_name is not in memory.

        Example:
            >>> encoder = FractionalPowerEncoder(model, memory)
            >>> x_pos = encoder.encode("x", 3.5)  # Encode x=3.5
            >>> x_neg = encoder.encode("x", -2.0)  # Encode x=-2.0
        """
        # Get basis hypervector
        basis_hv = self.memory[symbol_name]

        # Apply scaling if specified
        exponent = value * self.scale if self.scale is not None else value

        # Use fractional_power from opset if available, otherwise use jnp.power
        if hasattr(self.model.opset, "fractional_power"):
            powered_vec = self.model.opset.fractional_power(basis_hv.vec, exponent)
        else:
            powered_vec = jnp.power(basis_hv.vec, exponent)

        return ComplexHypervector(powered_vec)

    def encode_multi(
        self,
        symbol_names: list[str],
        values: list[float],
    ) -> ComplexHypervector:
        """Encode multiple dimensions using fractional powers and binding.

        For basis vectors X, Y, Z and values x, y, z:
            result = X^x ⊗ Y^y ⊗ Z^z

        This is fundamental for Spatial Semantic Pointers (SSP):
            S(x, y) = X^x ⊗ Y^y

        Args:
            symbol_names: List of basis symbol names (e.g., ["x", "y", "z"]).
            values: List of continuous values corresponding to each symbol.

        Returns:
            The encoded complex hypervector representing the multi-dimensional point.

        Raises:
            ValueError: If symbol_names and values have different lengths.
            KeyError: If any symbol_name is not in memory.

        Example:
            >>> memory.add("x")
            >>> memory.add("y")
            >>> encoder = FractionalPowerEncoder(model, memory)
            >>> # Encode 2D position (x=3.5, y=2.1)
            >>> pos = encoder.encode_multi(["x", "y"], [3.5, 2.1])
            >>> # This is equivalent to: X^3.5 ⊗ Y^2.1
        """
        if len(symbol_names) != len(values):
            raise ValueError(
                f"symbol_names and values must have same length. "
                f"Got {len(symbol_names)} symbols and {len(values)} values."
            )

        if len(symbol_names) == 0:
            raise ValueError("Must provide at least one symbol and value.")

        # Encode each dimension
        encoded_dims = [self.encode(name, val) for name, val in zip(symbol_names, values)]

        # Bind all dimensions together using circular convolution
        result = encoded_dims[0].vec
        for hv in encoded_dims[1:]:
            result = self.model.opset.bind(result, hv.vec)

        return ComplexHypervector(result)

    def unbind_dimension(
        self,
        encoded: ComplexHypervector,
        symbol_name: str,
        value: float,
    ) -> ComplexHypervector:
        """Unbind a specific dimension from a multi-dimensional encoding.

        For an encoded vector E = X^x ⊗ Y^y and known x:
            result = E ⊗ X^(-x) ≈ Y^y

        Args:
            encoded: The multi-dimensional encoded hypervector.
            symbol_name: Name of the dimension to unbind.
            value: The value of that dimension.

        Returns:
            The result after unbinding the specified dimension.

        Raises:
            KeyError: If symbol_name is not in memory.

        Example:
            >>> # Encode 2D position
            >>> pos = encoder.encode_multi(["x", "y"], [3.5, 2.1])
            >>> # Unbind x to get Y^2.1
            >>> y_component = encoder.unbind_dimension(pos, "x", 3.5)
        """
        # Encode the dimension to unbind with negative exponent
        to_unbind = self.encode(symbol_name, -value)

        # Bind (which unbinds due to negative exponent)
        result = self.model.opset.bind(encoded.vec, to_unbind.vec)

        return ComplexHypervector(result)
