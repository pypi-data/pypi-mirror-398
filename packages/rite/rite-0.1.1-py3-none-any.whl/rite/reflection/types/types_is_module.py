# =============================================================================
# Docstring
# =============================================================================

"""
Module Type Checker
===================

Check if object is a module.

Examples
--------
>>> from rite.reflection.types import types_is_module
>>> import json
>>> types_is_module(json)
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


def types_is_module(obj: Any) -> bool:
    """
    Check if object is a module.

    Args:
        obj: Object to check.

    Returns:
        True if object is a module.

    Examples:
        >>> import json
        >>> types_is_module(json)
        True
        >>> types_is_module("not a module")
        False

    Notes:
        Uses inspect.ismodule.
    """
    return inspect.ismodule(obj)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["types_is_module"]
