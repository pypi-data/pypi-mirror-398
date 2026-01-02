# =============================================================================
# Docstring
# =============================================================================

"""
Set Attribute
=============

Set attribute value on object.

Examples
--------
>>> from rite.reflection.attributes import attributes_set_attr
>>> class MyClass:
...     pass
>>> obj = MyClass()
>>> attributes_set_attr(obj, "value", 42)
>>> obj.value
42

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


def attributes_set_attr(obj: Any, name: str, value: Any) -> None:
    """
    Set attribute value on object.

    Args:
        obj: Object to set attribute on.
        name: Attribute name.
        value: Value to set.

    Returns:
        None

    Examples:
        >>> class MyClass:
        ...     pass
        >>> obj = MyClass()
        >>> attributes_set_attr(obj, "value", 42)
        >>> obj.value
        42

    Notes:
        Wrapper around setattr().
        Creates attribute if doesn't exist.
    """
    setattr(obj, name, value)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["attributes_set_attr"]
