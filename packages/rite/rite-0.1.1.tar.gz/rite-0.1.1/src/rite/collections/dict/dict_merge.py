# =============================================================================
# Docstring
# =============================================================================

"""
Dict Merge
==========

Merge multiple dictionaries with various strategies.

Functions
---------
- dict_merge: Merge dictionaries with configurable behavior.

Examples
--------
>>> from rite.collections.dict import dict_merge
>>> dict_merge({"a": 1, "b": 2}, {"b": 3, "c": 4})
{'a': 1, 'b': 3, 'c': 4}
"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from typing import TypeVar, cast

# =============================================================================
# Type Variables
# =============================================================================

K = TypeVar("K")
V = TypeVar("V")

# =============================================================================
# Functions
# =============================================================================


def dict_merge(
    *dicts: dict[K, V],
    deep: bool = False,
) -> dict[K, V]:
    """
    Merge multiple dictionaries.

    Later dictionaries override earlier ones for duplicate keys.

    Args:
        *dicts: Variable number of dictionaries to merge.
        deep: If True, recursively merge nested dicts.

    Returns:
        New merged dictionary.

    Examples:
        >>> dict_merge({"a": 1, "b": 2}, {"b": 3, "c": 4})
        {'a': 1, 'b': 3, 'c': 4}
        >>> dict_merge({"a": 1}, {"b": 2}, {"c": 3})
        {'a': 1, 'b': 2, 'c': 3}
        >>> d1 = {"a": {"x": 1}}
        >>> d2 = {"a": {"y": 2}}
        >>> dict_merge(d1, d2, deep=True)
        {'a': {'x': 1, 'y': 2}}
    """
    result: dict[K, V] = {}

    for d in dicts:
        if deep:
            for key, value in d.items():
                if (
                    key in result
                    and isinstance(result[key], dict)
                    and isinstance(value, dict)
                ):
                    result[key] = cast(
                        V,
                        dict_merge(
                            cast(dict[K, V], result[key]),
                            cast(dict[K, V], value),
                            deep=True,
                        ),
                    )
                else:
                    result[key] = value
        else:
            result.update(d)

    return result


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["dict_merge"]
