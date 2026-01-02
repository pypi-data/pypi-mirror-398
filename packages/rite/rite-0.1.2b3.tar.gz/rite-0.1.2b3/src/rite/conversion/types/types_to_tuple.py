# =============================================================================
# Docstring
# =============================================================================

"""
Tuple Conversion
================

Convert iterables to tuple representation.

Examples
--------
>>> from rite.conversion.types import types_to_tuple
>>> types_to_tuple([1, 2, 3])
(1, 2, 3)
>>> types_to_tuple("hello")
('h', 'e', 'l', 'l', 'o')

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from collections.abc import Iterable
from typing import Any

# =============================================================================
# Functions
# =============================================================================


def types_to_tuple(x: Any) -> tuple[Any, ...]:
    """
    Convert a value to a tuple.

    Args:
        x: Value to convert to tuple (iterable or single value).

    Returns:
        Tuple representation of the value.

    Examples:
        >>> types_to_tuple([1, 2, 3])
        (1, 2, 3)
        >>> types_to_tuple({1, 2, 3})
        (1, 2, 3)
        >>> types_to_tuple("hello")
        ('h', 'e', 'l', 'l', 'o')
        >>> types_to_tuple(42)
        (42,)
    """
    if isinstance(x, tuple):
        return x

    if isinstance(x, Iterable) and not isinstance(x, (str, bytes)):
        return tuple(x)

    if isinstance(x, str):
        return tuple(x)

    return (x,)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["types_to_tuple"]
