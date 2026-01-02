# =============================================================================
# Docstring
# =============================================================================

"""
Members Inspector
=================

Get all members of an object.

Examples
--------
>>> from rite.reflection.inspection import inspection_get_members
>>> import json
>>> members = inspection_get_members(json)
>>> 'dumps' in dict(members)
True

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
import inspect
from typing import Any

# =============================================================================
# Functions
# =============================================================================


def inspection_get_members(
    obj: Any, predicate: Any = None
) -> list[tuple[str, Any]]:
    """
    Get all members of an object.

    Args:
        obj: Object to inspect.
        predicate: Optional filter function.

    Returns:
        List of (name, value) tuples.

    Examples:
        >>> import json
        >>> members = inspection_get_members(json)
        >>> len(members) > 0
        True
        >>> inspection_get_members(json, inspect.isfunction)
        [('dump', ...), ('dumps', ...), ...]

    Notes:
        Uses inspect.getmembers.
        Predicate can filter by type.
    """
    return inspect.getmembers(obj, predicate)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["inspection_get_members"]
