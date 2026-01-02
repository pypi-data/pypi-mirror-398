# =============================================================================
# Docstring
# =============================================================================

"""
List Interleave
===============

Interleave multiple lists together.

Functions
---------
- list_interleave: Combine lists by alternating elements.

Examples
--------
>>> from rite.collections.list import list_interleave
>>> list_interleave([1, 2, 3], ['a', 'b', 'c'])
[1, 'a', 2, 'b', 3, 'c']
"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
import itertools
from typing import Any

# =============================================================================
# Functions
# =============================================================================


def list_interleave(*lists: list[Any]) -> list[Any]:
    """
    Interleave multiple lists by alternating elements.

    Args:
        *lists: Variable number of lists to interleave.

    Returns:
        New list with elements from all lists interleaved.

    Examples:
        >>> list_interleave([1, 2, 3], ['a', 'b', 'c'])
        [1, 'a', 2, 'b', 3, 'c']
        >>> list_interleave([1, 2], [10, 20], [100, 200])
        [1, 10, 100, 2, 20, 200]
        >>> list_interleave([1, 2, 3], ['a'])
        [1, 'a', 2, 3]
        >>> list_interleave([])
        []
    """
    return list(itertools.chain.from_iterable(zip(*lists)))


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["list_interleave"]
