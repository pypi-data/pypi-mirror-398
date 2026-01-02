# =============================================================================
# Docstring
# =============================================================================

"""
File Inspector
==============

Get file path of an object.

Examples
--------
>>> from rite.reflection.documentation import (
...     documentation_get_file
... )
>>> import json
>>> path = documentation_get_file(json)
>>> path.endswith('json/__init__.py')
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


def documentation_get_file(obj: Any) -> str | None:
    """
    Get file path of an object.

    Args:
        obj: Object to get file path from.

    Returns:
        File path or None if not found.

    Examples:
        >>> import json
        >>> path = documentation_get_file(json)
        >>> path.endswith('.py')
        True

    Notes:
        Uses inspect.getfile.
        Returns source file path.
    """
    try:
        return inspect.getfile(obj)
    except TypeError:
        return None


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["documentation_get_file"]
