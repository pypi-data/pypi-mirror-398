# =============================================================================
# Docstring
# =============================================================================

"""
Source Inspector
================

Get source code of an object.

Examples
--------
>>> from rite.reflection.inspection import inspection_get_source
>>> def my_func():
...     return 42
>>> source = inspection_get_source(my_func)
>>> 'return 42' in source
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


def inspection_get_source(obj: Any) -> str:
    """
    Get source code of an object.

    Args:
        obj: Function, method, or class to inspect.

    Returns:
        Source code as string.

    Raises:
        OSError: If source cannot be retrieved.

    Examples:
        >>> def my_func():
        ...     return 42
        >>> source = inspection_get_source(my_func)
        >>> 'return 42' in source
        True

    Notes:
        Uses inspect.getsource.
        May fail for built-in functions.
    """
    return inspect.getsource(obj)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["inspection_get_source"]
