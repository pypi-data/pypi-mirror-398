# =============================================================================
# Docstring
# =============================================================================

"""
Comments Inspector
==================

Get comments for an object.

Examples
--------
>>> from rite.reflection.documentation import (
...     documentation_get_comments
... )
>>> def func():
...     pass
>>> comments = documentation_get_comments(func)

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


def documentation_get_comments(obj: Any) -> str | None:
    """
    Get comments for an object.

    Args:
        obj: Object to get comments from.

    Returns:
        Comments string or None.

    Examples:
        >>> def func():
        ...     pass
        >>> comments = documentation_get_comments(func)

    Notes:
        Uses inspect.getcomments.
        Returns source code comments.
    """
    return inspect.getcomments(obj)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["documentation_get_comments"]
