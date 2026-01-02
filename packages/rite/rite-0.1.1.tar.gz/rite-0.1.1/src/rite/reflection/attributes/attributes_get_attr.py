# =============================================================================
# Docstring
# =============================================================================

"""
Get Attribute
=============

Get attribute value from object.

Examples
--------
>>> from rite.reflection.attributes import attributes_get_attr
>>> attributes_get_attr("hello", "upper")
<built-in method upper of str object at 0x...>

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


def attributes_get_attr(obj: Any, name: str, default: Any = None) -> Any:
    """
    Get attribute value from object.

    Args:
        obj: Object to get attribute from.
        name: Attribute name.
        default: Default value if not found.

    Returns:
        Attribute value or default.

    Examples:
        >>> attributes_get_attr("hello", "upper")
        <built-in method upper of str object at 0x...>
        >>> attributes_get_attr("hello", "missing", "default")
        'default'

    Notes:
        Wrapper around getattr().
        Returns default if attribute not found.
    """
    return getattr(obj, name, default)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["attributes_get_attr"]
