# =============================================================================
# Docstring
# =============================================================================

"""
Set Conversion
==============

Convert iterables to set representation.

Examples
--------
>>> from rite.conversion.types import types_to_set
>>> types_to_set([1, 2, 2, 3])
{1, 2, 3}
>>> types_to_set("hello")
{'h', 'e', 'l', 'o'}

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from collections.abc import Iterable
from typing import Any

# =============================================================================
# Functions
# =============================================================================


def types_to_set(x: Any) -> set[Any]:
    """
    Convert a value to a set.

    Args:
        x: Value to convert to set (iterable or single value).

    Returns:
        Set representation of the value.

    Examples:
        >>> types_to_set([1, 2, 2, 3])
        {1, 2, 3}
        >>> types_to_set((1, 2, 3))
        {1, 2, 3}
        >>> types_to_set("hello")
        {'h', 'e', 'l', 'o'}
        >>> types_to_set(42)
        {42}

    Notes:
        Strings are treated as iterables of characters.
        Single values are wrapped in a set.
    """
    if isinstance(x, set):
        return x

    if isinstance(x, Iterable) and not isinstance(x, (str, bytes)):
        return set(x)

    if isinstance(x, str):
        return set(x)

    return {x}


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["types_to_set"]
