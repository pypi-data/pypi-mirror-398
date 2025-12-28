"""VSAMemory: Symbol table for storing and managing named hypervectors."""

from collections.abc import Iterable
from typing import Optional

import jax

from vsax.core.base import AbstractHypervector
from vsax.core.model import VSAModel


class VSAMemory:
    """Symbol table for storing and managing named basis vectors.

    VSAMemory provides a dictionary-style interface for creating, storing, and
    retrieving named hypervectors. Each symbol is associated with a randomly
    sampled hypervector from the model's sampling distribution.

    Args:
        model: VSAModel instance defining the representation and operations.
        key: Optional JAX PRNG key for reproducible sampling. If None, uses a
            default key.

    Example:
        >>> from vsax import create_fhrr_model, VSAMemory
        >>> model = create_fhrr_model(dim=512)
        >>> memory = VSAMemory(model)
        >>> memory.add("dog")
        >>> memory.add_many(["cat", "bird"])
        >>> dog = memory["dog"]
        >>> assert "cat" in memory
        >>> print(memory.keys())
        ['dog', 'cat', 'bird']
    """

    def __init__(self, model: VSAModel, key: Optional[jax.Array] = None) -> None:
        """Initialize VSAMemory with a model.

        Args:
            model: VSAModel instance defining the VSA algebra.
            key: Optional JAX PRNG key for reproducible sampling.
        """
        self._model = model
        self._symbols: dict[str, AbstractHypervector] = {}
        self._key = key if key is not None else jax.random.PRNGKey(0)
        self._counter = 0

    @property
    def model(self) -> VSAModel:
        """Get the underlying VSAModel."""
        return self._model

    def add(self, name: str) -> AbstractHypervector:
        """Add a new symbol to memory with a randomly sampled hypervector.

        If the symbol already exists, returns the existing hypervector without
        resampling.

        Args:
            name: Name of the symbol to add.

        Returns:
            The hypervector associated with the symbol.

        Example:
            >>> memory = VSAMemory(model)
            >>> dog = memory.add("dog")
            >>> assert "dog" in memory
        """
        if name in self._symbols:
            return self._symbols[name]

        # Split key for this sample
        self._key, subkey = jax.random.split(self._key)

        # Sample a new vector
        vec = self._model.sampler(self._model.dim, 1, subkey)[0]

        # Wrap in representation
        hv = self._model.rep_cls(vec)

        # Store and return
        self._symbols[name] = hv
        self._counter += 1
        return hv

    def add_many(self, names: Iterable[str]) -> list[AbstractHypervector]:
        """Add multiple symbols to memory.

        Args:
            names: Iterable of symbol names to add.

        Returns:
            List of hypervectors corresponding to the added symbols.

        Example:
            >>> memory = VSAMemory(model)
            >>> colors = memory.add_many(["red", "green", "blue"])
            >>> assert len(colors) == 3
        """
        return [self.add(name) for name in names]

    def get(self, name: str) -> AbstractHypervector:
        """Get a hypervector by name.

        Args:
            name: Name of the symbol to retrieve.

        Returns:
            The hypervector associated with the symbol.

        Raises:
            KeyError: If the symbol does not exist in memory.

        Example:
            >>> memory = VSAMemory(model)
            >>> memory.add("dog")
            >>> dog = memory.get("dog")
        """
        return self._symbols[name]

    def __getitem__(self, name: str) -> AbstractHypervector:
        """Get a hypervector by name using dictionary syntax.

        Args:
            name: Name of the symbol to retrieve.

        Returns:
            The hypervector associated with the symbol.

        Raises:
            KeyError: If the symbol does not exist in memory.

        Example:
            >>> memory = VSAMemory(model)
            >>> memory.add("dog")
            >>> dog = memory["dog"]
        """
        return self.get(name)

    def __contains__(self, name: str) -> bool:
        """Check if a symbol exists in memory.

        Args:
            name: Name of the symbol to check.

        Returns:
            True if the symbol exists, False otherwise.

        Example:
            >>> memory = VSAMemory(model)
            >>> memory.add("dog")
            >>> assert "dog" in memory
            >>> assert "cat" not in memory
        """
        return name in self._symbols

    def keys(self) -> list[str]:
        """Get all symbol names in memory.

        Returns:
            List of symbol names.

        Example:
            >>> memory = VSAMemory(model)
            >>> memory.add_many(["a", "b", "c"])
            >>> assert memory.keys() == ["a", "b", "c"]
        """
        return list(self._symbols.keys())

    def __len__(self) -> int:
        """Get the number of symbols in memory.

        Returns:
            Number of stored symbols.

        Example:
            >>> memory = VSAMemory(model)
            >>> memory.add_many(["a", "b", "c"])
            >>> assert len(memory) == 3
        """
        return len(self._symbols)

    def clear(self) -> None:
        """Remove all symbols from memory.

        Example:
            >>> memory = VSAMemory(model)
            >>> memory.add_many(["a", "b", "c"])
            >>> memory.clear()
            >>> assert len(memory) == 0
        """
        self._symbols.clear()
        self._counter = 0

    def __repr__(self) -> str:
        """String representation of VSAMemory."""
        return f"VSAMemory(model={self._model.rep_cls.__name__}, symbols={len(self._symbols)})"
