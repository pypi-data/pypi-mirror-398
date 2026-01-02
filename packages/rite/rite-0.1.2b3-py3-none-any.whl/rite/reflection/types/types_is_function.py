# =============================================================================
# Docstring
# =============================================================================

"""
Function Type Checker
=====================

Check if object is a function.

Examples
--------
>>> from rite.reflection.types import types_is_function
>>> def my_func():
...     pass
>>> types_is_function(my_func)
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


def types_is_function(obj: Any) -> bool:
    """
    Check if object is a function.

    Args:
        obj: Object to check.

    Returns:
        True if object is a function.

    Examples:
        >>> def my_func():
        ...     pass
        >>> types_is_function(my_func)
        True
        >>> types_is_function(lambda x: x)
        True
        >>> types_is_function("not a function")
        False

    Notes:
        Uses inspect.isfunction.
        Does not match methods.
    """
    return inspect.isfunction(obj)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["types_is_function"]
