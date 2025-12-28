"""DictEncoder for encoding dictionaries into hypervectors using role-filler binding."""

from vsax.core.base import AbstractHypervector
from vsax.encoders.base import AbstractEncoder


class DictEncoder(AbstractEncoder):
    """Encoder for dictionaries using role-filler binding.

    Encodes dictionaries by binding each key (role) with its value (filler),
    then bundling all key-value pairs together.

    Both keys and values must be symbols that exist in memory.

    Attributes:
        model: The VSAModel instance defining the VSA algebra.
        memory: The VSAMemory instance for accessing basis hypervectors.

    Example:
        >>> from vsax import create_fhrr_model, VSAMemory
        >>> from vsax.encoders import DictEncoder
        >>> model = create_fhrr_model(dim=512)
        >>> memory = VSAMemory(model)
        >>> memory.add_many(["subject", "action", "dog", "run"])
        >>> encoder = DictEncoder(model, memory)
        >>> sentence_hv = encoder.encode({"subject": "dog", "action": "run"})
    """

    def encode(self, mapping: dict[str, str]) -> AbstractHypervector:
        """Encode a dictionary of key-value pairs.

        Args:
            mapping: A dictionary mapping role names to filler names.
                     Both keys and values must be symbols in memory.

        Returns:
            The encoded hypervector representing the dictionary.

        Raises:
            KeyError: If any key or value is not in memory.
            ValueError: If the dictionary is empty.

        Example:
            >>> encoder = DictEncoder(model, memory)
            >>> dict_hv = encoder.encode({"subject": "dog", "action": "run"})
        """
        if len(mapping) == 0:
            raise ValueError("Cannot encode empty dictionary")

        # Bind each key with its value and collect results
        bound_pairs = []
        for key, value in mapping.items():
            key_hv = self.memory[key]
            value_hv = self.memory[value]

            # Bind key (role) with value (filler)
            bound = self.model.opset.bind(key_hv.vec, value_hv.vec)
            bound_pairs.append(bound)

        # Bundle all key-value pairs
        result = self.model.opset.bundle(*bound_pairs)

        return self.model.rep_cls(result)
