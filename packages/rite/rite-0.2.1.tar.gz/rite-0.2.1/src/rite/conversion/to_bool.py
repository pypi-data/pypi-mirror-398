# =============================================================================
# Docstring
# =============================================================================

"""
Boolean Conversion
==================

Convert values to boolean representation.

This function converts various types of values to boolean, including strings
like "yes", "no", "true", "false", numbers, etc.

Example:
    >>> to_bool("yes")
    True
    >>> to_bool("no")
    False
    >>> to_bool(1)
    True
    >>> to_bool(0)
    False

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from typing import Any

# =============================================================================
# Constants
# =============================================================================

TRUTHY = {"true", "t", "yes", "y", "1", "on"}
FALSY = {"false", "f", "no", "n", "0", "off", ""}


# =============================================================================
# Functions
# =============================================================================


def to_bool(x: Any) -> bool | None:
    """
    Convert a value to a boolean.

    Args:
        x: Value to convert (string, number, bool, or None)

    Returns:
        Boolean representation or None if conversion fails

    Example:
        >>> to_bool("yes")
        True
        >>> to_bool(0)
        False
        >>> to_bool(None)
        None
    """
    # Handle None
    if x is None:
        return None

    # Handle booleans
    if isinstance(x, bool):
        return x

    # Handle numbers
    if isinstance(x, (int, float)):
        return bool(int(x))

    # Handle strings
    s = str(x).strip().lower()
    if s in TRUTHY:
        return True
    if s in FALSY:
        return False

    # Let validators raise if required
    return None


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "to_bool",
]
