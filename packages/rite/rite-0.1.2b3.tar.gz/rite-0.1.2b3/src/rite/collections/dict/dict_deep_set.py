# =============================================================================
# Docstring
# =============================================================================

"""
Dict Deep Set
=============

Set nested dictionary values, creating intermediate dicts as needed.

Functions
---------
- dict_deep_set: Set value at nested key path.

Examples
--------
>>> from rite.collections.dict import dict_deep_set
>>> d = {}
>>> dict_deep_set(d, ["user", "profile", "name"], "John")
>>> d
{'user': {'profile': {'name': 'John'}}}
"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from typing import Any

# =============================================================================
# Functions
# =============================================================================


def dict_deep_set(
    d: dict[str, Any],
    keys: list[str],
    value: Any,
) -> None:
    """
    Set nested dictionary value, creating intermediate dicts.

    Modifies dictionary in-place.

    Args:
        d: Dictionary to modify.
        keys: List of keys forming path where value should be set.
        value: Value to set at the key path.

    Examples:
        >>> d = {}
        >>> dict_deep_set(d, ["user", "profile", "name"], "John")
        >>> d
        {'user': {'profile': {'name': 'John'}}}
        >>> dict_deep_set(d, ["user", "age"], 30)
        >>> d['user']['age']
        30
    """
    current: dict[str, Any] = d

    for key in keys[:-1]:
        if key not in current or not isinstance(current[key], dict):
            current[key] = {}
        current = current[key]

    current[keys[-1]] = value


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["dict_deep_set"]
