# =============================================================================
# Docstring
# =============================================================================

"""
Methods Inspector
=================

Get all methods of a class or object.

Examples
--------
>>> from rite.reflection.inspection import inspection_get_methods
>>> methods = inspection_get_methods(str)
>>> 'upper' in [name for name, _ in methods]
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


def inspection_get_methods(obj: Any) -> list[tuple[str, Any]]:
    """
    Get all methods of a class or object.

    Args:
        obj: Class or object to inspect.

    Returns:
        List of (method_name, method) tuples.

    Examples:
        >>> methods = inspection_get_methods(str)
        >>> 'upper' in [name for name, _ in methods]
        True
        >>> methods = inspection_get_methods([])
        >>> 'append' in [name for name, _ in methods]
        True

    Notes:
        Uses inspect.getmembers with ismethod filter.
        Includes both instance and class methods.
    """
    return inspect.getmembers(obj, inspect.ismethod)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["inspection_get_methods"]
