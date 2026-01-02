# =============================================================================
# Docstring
# =============================================================================

"""
JSON Encoding
=============

Convert Python objects to JSON strings.

Examples
--------
>>> from rite.conversion.formats import formats_json_encode
>>> formats_json_encode({"key": "value"})
'{"key": "value"}'
>>> formats_json_encode([1, 2, 3])
'[1, 2, 3]'

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
import json
from typing import Any

# =============================================================================
# Functions
# =============================================================================


def formats_json_encode(
    obj: Any,
    *,
    indent: int | None = None,
    sort_keys: bool = False,
    ensure_ascii: bool = True,
) -> str:
    """
    Convert Python object to JSON string.

    Args:
        obj: Python object to encode.
        indent: Number of spaces for indentation (None for compact).
        sort_keys: If True, sort dictionary keys.
        ensure_ascii: If True, escape non-ASCII characters.

    Returns:
        JSON string representation.

    Raises:
        TypeError: If object is not JSON serializable.

    Examples:
        >>> formats_json_encode({"b": 2, "a": 1})
        '{"b": 2, "a": 1}'
        >>> formats_json_encode({"b": 2, "a": 1}, sort_keys=True)
        '{"a": 1, "b": 2}'
        >>> formats_json_encode([1, 2, 3], indent=2)
        '[\\n  1,\\n  2,\\n  3\\n]'
    """
    return json.dumps(
        obj,
        indent=indent,
        sort_keys=sort_keys,
        ensure_ascii=ensure_ascii,
    )


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["formats_json_encode"]
