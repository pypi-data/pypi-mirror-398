# =============================================================================
# Docstring
# =============================================================================

"""
Docstring Inspector
===================

Get docstring of an object.

Examples
--------
>>> from rite.reflection.documentation import (
...     documentation_get_docstring
... )
>>> def func():
...     '''This is a docstring.'''
...     pass
>>> documentation_get_docstring(func)
'This is a docstring.'

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


def documentation_get_docstring(obj: Any) -> str | None:
    """
    Get docstring of an object.

    Args:
        obj: Object to get docstring from.

    Returns:
        Docstring or None if not found.

    Examples:
        >>> def func():
        ...     '''This is a docstring.'''
        ...     pass
        >>> documentation_get_docstring(func)
        'This is a docstring.'

    Notes:
        Uses inspect.getdoc.
        Cleans up indentation.
    """
    return inspect.getdoc(obj)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["documentation_get_docstring"]
