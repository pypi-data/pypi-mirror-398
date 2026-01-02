# =============================================================================
# Docstring
# =============================================================================

"""
Set Operations Module
=====================

Utilities for set operations and transformations.

Functions
---------
- set_union: Union of multiple sets.
- set_intersection: Intersection of multiple sets.
- set_difference: Difference of sets.
- set_symmetric_difference: Symmetric difference of two sets.

Examples
--------
>>> from rite.collections.set import set_union
>>> set_union({1, 2}, {2, 3}, {3, 4})
{1, 2, 3, 4}
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


def set_union(*sets: set[T]) -> set[T]:
    """
    Return union of multiple sets.

    Args:
        *sets: Variable number of sets to unite.

    Returns:
        New set containing all unique elements.

    Examples:
        >>> set_union({1, 2}, {2, 3}, {3, 4})
        {1, 2, 3, 4}
        >>> set_union({1}, {2}, {3})
        {1, 2, 3}
    """
    result: set[T] = set()
    for s in sets:
        result |= s
    return result


def set_intersection(*sets: set[T]) -> set[T]:
    """
    Return intersection of multiple sets.

    Args:
        *sets: Variable number of sets to intersect.

    Returns:
        New set containing only common elements.

    Examples:
        >>> set_intersection({1, 2, 3}, {2, 3, 4}, {2, 3, 5})
        {2, 3}
        >>> set_intersection({1, 2}, {3, 4})
        set()
    """
    if not sets:
        return set()

    result = sets[0].copy()
    for s in sets[1:]:
        result &= s
    return result


def set_difference(first: set[T], *others: set[T]) -> set[T]:
    """
    Return difference of first set minus all others.

    Args:
        first: Base set to subtract from.
        *others: Sets to subtract.

    Returns:
        New set with elements in first but not in others.

    Examples:
        >>> set_difference({1, 2, 3}, {2}, {3})
        {1}
        >>> set_difference({1, 2, 3, 4}, {2, 3})
        {1, 4}
    """
    result = first.copy()
    for s in others:
        result -= s
    return result


def set_symmetric_difference(first: set[T], second: set[T]) -> set[T]:
    """
    Return symmetric difference (elements in either but not both).

    Args:
        first: First set.
        second: Second set.

    Returns:
        New set with elements in first or second but not both.

    Examples:
        >>> set_symmetric_difference({1, 2, 3}, {2, 3, 4})
        {1, 4}
        >>> set_symmetric_difference({1, 2}, {3, 4})
        {1, 2, 3, 4}
    """
    return first ^ second


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "set_difference",
    "set_intersection",
    "set_symmetric_difference",
    "set_union",
]
