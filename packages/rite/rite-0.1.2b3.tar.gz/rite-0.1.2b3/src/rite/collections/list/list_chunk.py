# =============================================================================
# Docstring
# =============================================================================

"""
List Chunk
==========

Split a list into chunks of specified size.

Functions
---------
- list_chunk: Split list into smaller chunks.

Examples
--------
>>> from rite.collections.list import list_chunk
>>> list_chunk([1, 2, 3, 4, 5], size=2)
[[1, 2], [3, 4], [5]]
>>> list_chunk([1, 2, 3, 4, 5, 6], size=3)
[[1, 2, 3], [4, 5, 6]]
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


def list_chunk(items: list[T], size: int) -> list[list[T]]:
    """
    Split a list into chunks of specified size.

    Args:
        items: List to split into chunks.
        size: Size of each chunk. Must be positive.

    Returns:
        List of chunks, last chunk may be smaller.

    Raises:
        ValueError: If size is not positive.

    Examples:
        >>> list_chunk([1, 2, 3, 4, 5], size=2)
        [[1, 2], [3, 4], [5]]
        >>> list_chunk([1, 2, 3, 4, 5, 6], size=3)
        [[1, 2, 3], [4, 5, 6]]
        >>> list_chunk([], size=2)
        []
        >>> list_chunk([1, 2, 3], size=5)
        [[1, 2, 3]]
    """
    if size <= 0:
        raise ValueError("Chunk size must be positive")

    return [items[i : i + size] for i in range(0, len(items), size)]


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["list_chunk"]
