# =============================================================================
# Docstring
# =============================================================================

"""
Method Type Checker
===================

Check if object is a method.

Examples
--------
>>> from rite.reflection.types import types_is_method
>>> types_is_method("hello".upper)
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


def types_is_method(obj: Any) -> bool:
    """
    Check if object is a method.

    Args:
        obj: Object to check.

    Returns:
        True if object is a method.

    Examples:
        >>> types_is_method("hello".upper)
        True
        >>> types_is_method([].append)
        True
        >>> types_is_method(str.upper)
        False

    Notes:
        Uses inspect.ismethod.
        Only bound methods return True.
    """
    return inspect.ismethod(obj)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["types_is_method"]
