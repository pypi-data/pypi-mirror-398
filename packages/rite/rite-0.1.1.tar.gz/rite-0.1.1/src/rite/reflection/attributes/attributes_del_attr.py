# =============================================================================
# Docstring
# =============================================================================

"""
Delete Attribute
================

Delete attribute from object.

Examples
--------
>>> from rite.reflection.attributes import attributes_del_attr
>>> class MyClass:
...     value = 42
>>> obj = MyClass()
>>> attributes_del_attr(obj, "value")

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


def attributes_del_attr(obj: Any, name: str) -> None:
    """
    Delete attribute from object.

    Args:
        obj: Object to delete attribute from.
        name: Attribute name.

    Returns:
        None

    Raises:
        AttributeError: If attribute doesn't exist.

    Examples:
        >>> class MyClass:
        ...     value = 42
        >>> obj = MyClass()
        >>> attributes_del_attr(obj, "value")
        >>> hasattr(obj, "value")
        False

    Notes:
        Wrapper around delattr().
    """
    delattr(obj, name)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["attributes_del_attr"]
