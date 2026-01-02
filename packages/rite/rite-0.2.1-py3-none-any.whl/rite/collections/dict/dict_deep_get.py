# =============================================================================
# Docstring
# =============================================================================

"""
Dict Deep Get
=============

Safely get nested dictionary values using key paths.

Functions
---------
- dict_deep_get: Get nested value using list of keys.

Examples
--------
>>> from rite.collections.dict import dict_deep_get
>>> data = {"user": {"profile": {"name": "John"}}}
>>> dict_deep_get(data, ["user", "profile", "name"])
'John'
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


def dict_deep_get(
    d: dict[str, Any],
    keys: list[str],
    default: Any = None,
) -> Any:
    """
    Get nested dictionary value using key path.

    Args:
        d: Dictionary to traverse.
        keys: List of keys forming path to desired value.
        default: Value to return if path doesn't exist.

    Returns:
        Value at the key path or default.

    Examples:
        >>> data = {"user": {"profile": {"name": "John"}}}
        >>> dict_deep_get(data, ["user", "profile", "name"])
        'John'
        >>> dict_deep_get(data, ["user", "missing"], "N/A")
        'N/A'
        >>> dict_deep_get({}, ["a", "b"])
        None
    """
    current: Any = d

    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default

    return current


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["dict_deep_get"]
