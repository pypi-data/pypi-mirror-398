# =============================================================================
# Docstring
# =============================================================================

"""
List Flatten
============

Flatten nested lists into a single-level list.

Functions
---------
- list_flatten: Flatten nested lists recursively.

Examples
--------
>>> from rite.collections.list import list_flatten
>>> list_flatten([[1, 2], [3, 4], [5]])
[1, 2, 3, 4, 5]
>>> list_flatten([[1, [2, 3]], [4, 5]])
[1, 2, 3, 4, 5]
"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from typing import Any, TypeVar

# =============================================================================
# Type Variables
# =============================================================================

T = TypeVar("T")

# =============================================================================
# Functions
# =============================================================================


def list_flatten(items: list[Any], depth: int | None = None) -> list[Any]:
    """
    Flatten nested lists recursively.

    Args:
        items: List that may contain nested lists.
        depth: Maximum depth to flatten. None for full recursion.

    Returns:
        Flattened list.

    Examples:
        >>> list_flatten([[1, 2], [3, 4], [5]])
        [1, 2, 3, 4, 5]
        >>> list_flatten([[1, [2, 3]], [4, 5]])
        [1, 2, 3, 4, 5]
        >>> list_flatten([[1, [2, [3]]], [4]], depth=1)
        [1, [2, [3]], 4]
        >>> list_flatten([])
        []
    """
    result: list[Any] = []
    current_depth = 0 if depth is not None else None

    def _flatten(lst: list[Any], current: int | None) -> None:
        """Recursive helper to flatten lists."""
        for item in lst:
            if isinstance(item, list):
                if current is None or current < (depth or 0):
                    next_depth = None if current is None else current + 1
                    _flatten(item, next_depth)
                else:
                    result.append(item)
            else:
                result.append(item)

    _flatten(items, current_depth)
    return result


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["list_flatten"]
