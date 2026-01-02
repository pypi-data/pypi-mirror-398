# =============================================================================
# Docstring
# =============================================================================

"""
Functions Inspector
===================

Get all functions from a module.

Examples
--------
>>> from rite.reflection.inspection import inspection_get_functions
>>> import json
>>> funcs = inspection_get_functions(json)
>>> 'dumps' in [name for name, _ in funcs]
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


def inspection_get_functions(obj: Any) -> list[tuple[str, Any]]:
    """
    Get all functions from a module or class.

    Args:
        obj: Module or class to inspect.

    Returns:
        List of (function_name, function) tuples.

    Examples:
        >>> import json
        >>> funcs = inspection_get_functions(json)
        >>> 'dumps' in [name for name, _ in funcs]
        True

    Notes:
        Uses inspect.getmembers with isfunction filter.
    """
    return inspect.getmembers(obj, inspect.isfunction)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["inspection_get_functions"]
