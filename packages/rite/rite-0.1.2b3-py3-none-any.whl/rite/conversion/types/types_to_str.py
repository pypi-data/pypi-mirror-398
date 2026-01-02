# =============================================================================
# Docstring
# =============================================================================

"""
String Conversion
=================

Convert values to string representation.

Examples
--------
>>> from rite.conversion.types import types_to_str
>>> types_to_str(42)
'42'
>>> types_to_str([1, 2, 3])
'[1, 2, 3]'
>>> types_to_str(None)
''

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


def types_to_str(
    x: Any,
    none_as_empty: bool = True,
    encoding: str = "utf-8",
) -> str:
    """
    Convert a value to a string.

    Args:
        x: Value to convert to string.
        none_as_empty: If True, None converts to empty string.
        encoding: Encoding to use for bytes objects.

    Returns:
        String representation of the value.

    Examples:
        >>> types_to_str(42)
        '42'
        >>> types_to_str(None)
        ''
        >>> types_to_str(None, none_as_empty=False)
        'None'
        >>> types_to_str(b'hello')
        'hello'
        >>> types_to_str([1, 2, 3])
        '[1, 2, 3]'
    """
    if x is None:
        return "" if none_as_empty else "None"

    if isinstance(x, str):
        return x

    if isinstance(x, bytes):
        return x.decode(encoding, errors="replace")

    return str(x)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["types_to_str"]
