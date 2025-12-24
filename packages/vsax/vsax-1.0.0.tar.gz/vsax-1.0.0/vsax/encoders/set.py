"""SetEncoder for encoding unordered sets into hypervectors."""

from typing import Union

from vsax.core.base import AbstractHypervector
from vsax.encoders.base import AbstractEncoder


class SetEncoder(AbstractEncoder):
    """Encoder for unordered sets using bundling.

    Encodes sets by simply bundling all element hypervectors together.
    Since bundling is commutative, the result is order-invariant.

    Attributes:
        model: The VSAModel instance defining the VSA algebra.
        memory: The VSAMemory instance for accessing basis hypervectors.

    Example:
        >>> from vsax import create_fhrr_model, VSAMemory
        >>> from vsax.encoders import SetEncoder
        >>> model = create_fhrr_model(dim=512)
        >>> memory = VSAMemory(model)
        >>> memory.add_many(["dog", "cat", "bird"])
        >>> encoder = SetEncoder(model, memory)
        >>> animals_set_hv = encoder.encode({"dog", "cat", "bird"})
    """

    def encode(self, elements: Union[set[str], list[str]]) -> AbstractHypervector:
        """Encode an unordered set of symbols.

        Args:
            elements: A set or list of symbol names in memory.

        Returns:
            The encoded hypervector representing the set.

        Raises:
            KeyError: If any symbol in the set is not in memory.
            ValueError: If the set is empty.

        Example:
            >>> encoder = SetEncoder(model, memory)
            >>> set_hv = encoder.encode({"dog", "cat", "bird"})
        """
        if len(elements) == 0:
            raise ValueError("Cannot encode empty set")

        # Get all element hypervectors
        elem_vecs = [self.memory[symbol].vec for symbol in elements]

        # Bundle all elements together
        result = self.model.opset.bundle(*elem_vecs)

        return self.model.rep_cls(result)
