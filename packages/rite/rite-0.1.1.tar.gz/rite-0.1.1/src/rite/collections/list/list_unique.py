# =============================================================================
# Docstring
# =============================================================================

"""
List Unique
===========

Remove duplicate elements from a list while preserving order.

Functions
---------
- list_unique: Remove duplicates from a list.

Examples
--------
>>> from rite.collections.list import list_unique
>>> list_unique([1, 2, 2, 3, 3, 3])
[1, 2, 3]
>>> list_unique(['a', 'b', 'a', 'c'])
['a', 'b', 'c']
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

T = TypeVar("T")

# =============================================================================
# Functions
# =============================================================================


def list_unique(items: list[T]) -> list[T]:
    """
    Remove duplicate elements while preserving order.

    Uses a set to track seen elements and preserves first occurrence
    of each unique element.

    Args:
        items: List that may contain duplicates.

    Returns:
        New list with duplicates removed, order preserved.

    Examples:
        >>> list_unique([1, 2, 2, 3, 3, 3])
        [1, 2, 3]
        >>> list_unique(['a', 'b', 'a', 'c'])
        ['a', 'b', 'c']
        >>> list_unique([])
        []
    """
    seen: set[T] = set()
    result: list[T] = []

    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)

    return result


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["list_unique"]
