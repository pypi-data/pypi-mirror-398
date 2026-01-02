# =============================================================================
# Docstring
# =============================================================================

"""
List Group By
=============

Group list items by a key function or attribute.

Functions
---------
- list_group_by: Group items by key.

Examples
--------
>>> from rite.collections.list import list_group_by
>>> data = [{"type": "fruit", "name": "apple"}]
>>> list_group_by(data, key="type")
{'fruit': [{'type': 'fruit', 'name': 'apple'}]}
"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from collections import defaultdict
from typing import Any, Callable, TypeVar

# =============================================================================
# Type Variables
# =============================================================================

T = TypeVar("T")
K = TypeVar("K")

# =============================================================================
# Functions
# =============================================================================


def list_group_by(
    items: list[T],
    key: str | Callable[[T], K],
) -> dict[Any, list[T]]:
    """
    Group list items by a key function or dict key.

    Args:
        items: List of items to group.
        key: Either attribute name (str) or function to extract key.

    Returns:
        Dictionary mapping keys to lists of items.

    Examples:
        >>> data = [
        ...     {"type": "fruit", "name": "apple"},
        ...     {"type": "fruit", "name": "banana"},
        ...     {"type": "veg", "name": "carrot"}
        ... ]
        >>> list_group_by(data, key="type")
        {'fruit': [...], 'veg': [...]}
        >>> list_group_by([1, 2, 3, 4], key=lambda x: x % 2)
        {1: [1, 3], 0: [2, 4]}
    """
    grouped: dict[Any, list[T]] = defaultdict(list)

    if isinstance(key, str):
        # Key is attribute/dict key name
        for item in items:
            if isinstance(item, dict):
                group_key = item.get(key)
            else:
                group_key = getattr(item, key, None)
            grouped[group_key].append(item)
    else:
        # Key is a function
        for item in items:
            group_key = key(item)
            grouped[group_key].append(item)

    return dict(grouped)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["list_group_by"]
