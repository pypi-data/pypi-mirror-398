# =============================================================================
# Docstring
# =============================================================================

"""
Dict Invert
===========

Invert dictionary keys and values.

Functions
---------
- dict_invert: Swap dictionary keys and values.

Examples
--------
>>> from rite.collections.dict import dict_invert
>>> dict_invert({"a": 1, "b": 2})
{1: 'a', 2: 'b'}
"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from typing import TypeVar

# =============================================================================
# Type Variables
# =============================================================================

K = TypeVar("K")
V = TypeVar("V")

# =============================================================================
# Functions
# =============================================================================


def dict_invert(d: dict[K, V]) -> dict[V, K]:
    """
    Invert dictionary keys and values.

    Args:
        d: Dictionary to invert.

    Returns:
        New dictionary with keys and values swapped.

    Raises:
        TypeError: If values are not hashable.

    Examples:
        >>> dict_invert({"a": 1, "b": 2})
        {1: 'a', 2: 'b'}
        >>> dict_invert({1: "one", 2: "two"})
        {'one': 1, 'two': 2}
        >>> dict_invert({})
        {}
    """
    return {v: k for k, v in d.items()}


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["dict_invert"]
