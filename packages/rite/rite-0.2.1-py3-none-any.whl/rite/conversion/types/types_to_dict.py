# =============================================================================
# Docstring
# =============================================================================

"""
Dictionary Conversion
=====================

Convert sequences and mappings to dictionary representation.

Examples
--------
>>> from rite.conversion.types import types_to_dict
>>> types_to_dict([("a", 1), ("b", 2)])
{'a': 1, 'b': 2}
>>> types_to_dict({"x": 10})
{'x': 10}

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from collections.abc import Mapping, Sequence
from typing import Any

# =============================================================================
# Functions
# =============================================================================


def types_to_dict(x: Any, key_attr: str | None = None) -> dict[Any, Any]:
    """
    Convert a value to a dictionary.

    Args:
        x: Value to convert (mapping, sequence of pairs, or list).
        key_attr: Attribute name to use as key for object sequences.

    Returns:
        Dictionary representation of the value.

    Raises:
        ValueError: If conversion is not possible.

    Examples:
        >>> types_to_dict([("a", 1), ("b", 2)])
        {'a': 1, 'b': 2}
        >>> types_to_dict({"x": 10, "y": 20})
        {'x': 10, 'y': 20}
        >>> types_to_dict([("x", 1)])
        {'x': 1}

    Notes:
        Objects with key_attr will use obj.key_attr as dictionary key.
    """
    if isinstance(x, dict):
        return x

    if isinstance(x, Mapping):
        return dict(x)

    if isinstance(x, Sequence) and not isinstance(x, (str, bytes)):
        # Check if sequence of pairs
        if all(
            isinstance(item, (tuple, list)) and len(item) == 2 for item in x
        ):
            return dict(x)

        # If key_attr provided, use it
        if key_attr:
            result = {}
            for item in x:
                if hasattr(item, key_attr):
                    key = getattr(item, key_attr)
                    result[key] = item
            return result

    msg = f"Cannot convert {type(x).__name__} to dict"
    raise ValueError(msg)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["types_to_dict"]
