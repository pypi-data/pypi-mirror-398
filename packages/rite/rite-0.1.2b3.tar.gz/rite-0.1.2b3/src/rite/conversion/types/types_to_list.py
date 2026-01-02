# =============================================================================
# Docstring
# =============================================================================

"""
List Conversion
===============

Convert values to list representation.

Examples
--------
>>> from rite.conversion.types import types_to_list
>>> types_to_list((1, 2, 3))
[1, 2, 3]
>>> types_to_list("hello")
['h', 'e', 'l', 'l', 'o']
>>> types_to_list(42)
[42]

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


def types_to_list(x: Any, split_strings: bool = False) -> list[Any]:
    """
    Convert a value to a list.

    Args:
        x: Value to convert to list.
        split_strings: If True, strings become list of chars.

    Returns:
        List representation of the value.

    Examples:
        >>> types_to_list((1, 2, 3))
        [1, 2, 3]
        >>> types_to_list({1, 2, 3})
        [1, 2, 3]
        >>> types_to_list("hello", split_strings=True)
        ['h', 'e', 'l', 'l', 'o']
        >>> types_to_list("hello", split_strings=False)
        ['hello']
        >>> types_to_list(42)
        [42]
        >>> types_to_list(None)
        [None]
    """
    if isinstance(x, list):
        return x

    if isinstance(x, str):
        if split_strings:
            return list(x)
        return [x]

    if isinstance(x, Iterable):
        return list(x)

    return [x]


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["types_to_list"]
