# =============================================================================
# Docstring
# =============================================================================

"""
Has Attribute Checker
======================

Check if object has an attribute.

Examples
--------
>>> from rite.reflection.attributes import attributes_has_attr
>>> attributes_has_attr("hello", "upper")
True

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from typing import Any

# =============================================================================
# Functions
# =============================================================================


def attributes_has_attr(obj: Any, name: str) -> bool:
    """
    Check if object has an attribute.

    Args:
        obj: Object to check.
        name: Attribute name.

    Returns:
        True if attribute exists.

    Examples:
        >>> attributes_has_attr("hello", "upper")
        True
        >>> attributes_has_attr("hello", "nonexistent")
        False
        >>> attributes_has_attr([], "append")
        True

    Notes:
        Wrapper around hasattr().
    """
    return hasattr(obj, name)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["attributes_has_attr"]
