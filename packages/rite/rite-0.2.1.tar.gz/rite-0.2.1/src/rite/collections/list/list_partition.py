# =============================================================================
# Docstring
# =============================================================================

"""
List Partition
==============

Partition a list into two lists based on a predicate function.

Functions
---------
- list_partition: Split list into matching and non-matching items.

Examples
--------
>>> from rite.collections.list import list_partition
>>> list_partition([1, 2, 3, 4, 5], lambda x: x % 2 == 0)
([2, 4], [1, 3, 5])
"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from typing import Callable, TypeVar

# =============================================================================
# Type Variables
# =============================================================================

T = TypeVar("T")

# =============================================================================
# Functions
# =============================================================================


def list_partition(
    items: list[T],
    predicate: Callable[[T], bool],
) -> tuple[list[T], list[T]]:
    """
    Partition a list based on a predicate function.

    Args:
        items: List to partition.
        predicate: Function that returns True for items in first list.

    Returns:
        Tuple of (matching_items, non_matching_items).

    Examples:
        >>> list_partition([1, 2, 3, 4, 5], lambda x: x % 2 == 0)
        ([2, 4], [1, 3, 5])
        >>> list_partition(['a', 'bb', 'ccc'], lambda x: len(x) > 1)
        (['bb', 'ccc'], ['a'])
        >>> list_partition([], lambda x: True)
        ([], [])
    """
    matching: list[T] = []
    non_matching: list[T] = []

    for item in items:
        if predicate(item):
            matching.append(item)
        else:
            non_matching.append(item)

    return (matching, non_matching)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["list_partition"]
