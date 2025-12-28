"""Abstract base class for all encoders."""

from abc import ABC, abstractmethod
from typing import Any

from vsax.core.base import AbstractHypervector
from vsax.core.memory import VSAMemory
from vsax.core.model import VSAModel


class AbstractEncoder(ABC):
    """Abstract base class for encoding structured data into hypervectors.

    All encoders must implement the `encode()` method. Encoders can optionally
    implement `fit()` for learned encodings and `decode()` for reconstruction.

    Attributes:
        model: The VSAModel instance defining the VSA algebra.
        memory: The VSAMemory instance for accessing basis hypervectors.

    Example:
        >>> class MyEncoder(AbstractEncoder):
        ...     def encode(self, data):
        ...         # Custom encoding logic
        ...         return self.memory["basis"]
        >>> encoder = MyEncoder(model, memory)
        >>> hv = encoder.encode(some_data)
    """

    def __init__(self, model: VSAModel, memory: VSAMemory) -> None:
        """Initialize the encoder.

        Args:
            model: The VSAModel instance.
            memory: The VSAMemory instance with basis symbols.
        """
        self.model = model
        self.memory = memory

    @abstractmethod
    def encode(self, *args: Any, **kwargs: Any) -> AbstractHypervector:
        """Encode data into a hypervector.

        Args:
            *args: Positional arguments (encoder-specific).
            **kwargs: Keyword arguments (encoder-specific).

        Returns:
            The encoded hypervector.

        Raises:
            NotImplementedError: This is an abstract method.

        Note:
            Different encoders may have different signatures. See specific
            encoder documentation for details.
        """
        pass

    def fit(self, data: Any) -> None:
        """Optionally fit encoder parameters to data.

        This method is optional and can be used for learned encodings.
        By default, it does nothing.

        Args:
            data: The training data.
        """
        pass
