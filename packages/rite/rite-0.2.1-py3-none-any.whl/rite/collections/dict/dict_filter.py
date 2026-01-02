# =============================================================================
# Docstring
# =============================================================================

"""
Dict Filter
===========

Filter dictionary entries based on key or value predicates.

Functions
---------
- dict_filter: Filter dictionary by predicate.

Examples
--------
>>> from rite.collections.dict import dict_filter
>>> dict_filter({"a": 1, "b": 2, "c": 3}, lambda k, v: v > 1)
{'b': 2, 'c': 3}
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

K = TypeVar("K")
V = TypeVar("V")

# =============================================================================
# Functions
# =============================================================================


def dict_filter(
    d: dict[K, V],
    predicate: Callable[[K, V], bool],
) -> dict[K, V]:
    """
    Filter dictionary entries based on predicate function.

    Args:
        d: Dictionary to filter.
        predicate: Function taking (key, value) returning True to keep.

    Returns:
        New dictionary with filtered entries.

    Examples:
        >>> dict_filter({"a": 1, "b": 2, "c": 3}, lambda k, v: v > 1)
        {'b': 2, 'c': 3}
        >>> dict_filter({"a": 1, "b": 2}, lambda k, v: k == "a")
        {'a': 1}
        >>> dict_filter({}, lambda k, v: True)
        {}
    """
    return {k: v for k, v in d.items() if predicate(k, v)}


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["dict_filter"]
