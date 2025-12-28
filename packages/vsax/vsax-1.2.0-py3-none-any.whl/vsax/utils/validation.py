"""Input validation utilities."""

from typing import Any


def validate_positive_int(value: Any, name: str) -> int:
    """Validate that a value is a positive integer.

    Args:
        value: Value to validate.
        name: Name of the parameter (for error messages).

    Returns:
        The validated integer value.

    Raises:
        TypeError: If value is not an integer.
        ValueError: If value is not positive.

    Example:
        >>> dim = validate_positive_int(512, "dim")
        >>> assert dim == 512
    """
    if not isinstance(value, int):
        raise TypeError(f"{name} must be an integer, got {type(value).__name__}")
    if value <= 0:
        raise ValueError(f"{name} must be positive, got {value}")
    return value


def validate_string(value: Any, name: str) -> str:
    """Validate that a value is a non-empty string.

    Args:
        value: Value to validate.
        name: Name of the parameter (for error messages).

    Returns:
        The validated string value.

    Raises:
        TypeError: If value is not a string.
        ValueError: If value is an empty string.

    Example:
        >>> symbol = validate_string("dog", "symbol")
        >>> assert symbol == "dog"
    """
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string, got {type(value).__name__}")
    if not value:
        raise ValueError(f"{name} cannot be empty")
    return value
