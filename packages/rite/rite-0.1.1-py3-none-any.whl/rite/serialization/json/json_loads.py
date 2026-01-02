# =============================================================================
# Docstring
# =============================================================================

"""
JSON Loads
==========

Parse JSON from string.

Examples
--------
>>> from rite.serialization.json import json_loads
>>> json_loads('{"key": "value"}')
{'key': 'value'}

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


def json_loads(text: str) -> Any:
    """
    Parse JSON from string.

    Args:
        text: JSON string to parse.

    Returns:
        Parsed JSON data.

    Raises:
        json.JSONDecodeError: If JSON is invalid.

    Examples:
        >>> json_loads('{"key": "value"}')
        {'key': 'value'}
        >>> json_loads('[1, 2, 3]')
        [1, 2, 3]

    Notes:
        Wrapper around json.loads.
    """
    return json.loads(text)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["json_loads"]
