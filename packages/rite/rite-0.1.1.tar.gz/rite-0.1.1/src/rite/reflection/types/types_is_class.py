# =============================================================================
# Docstring
# =============================================================================

"""
Class Type Checker
==================

Check if object is a class.

Examples
--------
>>> from rite.reflection.types import types_is_class
>>> types_is_class(str)
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


def types_is_class(obj: Any) -> bool:
    """
    Check if object is a class.

    Args:
        obj: Object to check.

    Returns:
        True if object is a class.

    Examples:
        >>> types_is_class(str)
        True
        >>> types_is_class("hello")
        False
        >>> types_is_class(list)
        True

    Notes:
        Uses inspect.isclass.
    """
    return inspect.isclass(obj)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["types_is_class"]
