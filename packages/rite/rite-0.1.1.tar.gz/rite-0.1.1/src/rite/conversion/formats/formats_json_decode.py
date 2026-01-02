# =============================================================================
# Docstring
# =============================================================================

"""
JSON Decoding
=============

Convert JSON strings to Python objects.

Examples
--------
>>> from rite.conversion.formats import formats_json_decode
>>> formats_json_decode('{"key": "value"}')
{'key': 'value'}
>>> formats_json_decode('[1, 2, 3]')
[1, 2, 3]

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


def formats_json_decode(s: str | bytes, default: Any = None) -> Any:
    """
    Convert JSON string to Python object.

    Args:
        s: JSON string or bytes to decode.
        default: Value to return if decoding fails.

    Returns:
        Decoded Python object or default if decoding fails.

    Examples:
        >>> formats_json_decode('{"key": "value"}')
        {'key': 'value'}
        >>> formats_json_decode('[1, 2, 3]')
        [1, 2, 3]
        >>> formats_json_decode('invalid')

        >>> formats_json_decode('invalid', {})
        {}
        >>> formats_json_decode(b'{"a": 1}')
        {'a': 1}
    """
    try:
        if isinstance(s, bytes):
            s = s.decode("utf-8")
        return json.loads(s)
    except (json.JSONDecodeError, ValueError, TypeError):
        return default


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["formats_json_decode"]
