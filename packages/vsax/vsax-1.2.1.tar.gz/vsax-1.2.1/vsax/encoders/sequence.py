"""SequenceEncoder for encoding ordered sequences (lists, tuples) into hypervectors."""

from collections.abc import Sequence

from vsax.core.base import AbstractHypervector
from vsax.encoders.base import AbstractEncoder


class SequenceEncoder(AbstractEncoder):
    """Encoder for ordered sequences using positional binding.

    Encodes sequences by binding each element with a position hypervector,
    then bundling all position-element pairs. This preserves order information.

    Position hypervectors are automatically added to memory with names "pos_0",
    "pos_1", etc.

    Attributes:
        model: The VSAModel instance defining the VSA algebra.
        memory: The VSAMemory instance for accessing basis hypervectors.

    Example:
        >>> from vsax import create_fhrr_model, VSAMemory
        >>> from vsax.encoders import SequenceEncoder
        >>> model = create_fhrr_model(dim=512)
        >>> memory = VSAMemory(model)
        >>> memory.add_many(["red", "green", "blue"])
        >>> encoder = SequenceEncoder(model, memory)
        >>> color_sequence_hv = encoder.encode(["red", "green", "blue"])
    """

    def encode(self, sequence: Sequence[str]) -> AbstractHypervector:
        """Encode an ordered sequence of symbols.

        Args:
            sequence: A list or tuple of symbol names in memory.

        Returns:
            The encoded hypervector representing the sequence.

        Raises:
            KeyError: If any symbol in the sequence is not in memory.
            ValueError: If the sequence is empty.

        Example:
            >>> encoder = SequenceEncoder(model, memory)
            >>> seq_hv = encoder.encode(["red", "green", "blue"])
        """
        if len(sequence) == 0:
            raise ValueError("Cannot encode empty sequence")

        # Ensure position hypervectors exist in memory
        for i in range(len(sequence)):
            pos_name = f"pos_{i}"
            if pos_name not in self.memory:
                self.memory.add(pos_name)

        # Bind each element with its position and collect results
        bound_pairs = []
        for i, symbol in enumerate(sequence):
            pos_hv = self.memory[f"pos_{i}"]
            elem_hv = self.memory[symbol]

            # Bind position with element
            bound = self.model.opset.bind(pos_hv.vec, elem_hv.vec)
            bound_pairs.append(bound)

        # Bundle all position-element pairs
        result = self.model.opset.bundle(*bound_pairs)

        return self.model.rep_cls(result)
