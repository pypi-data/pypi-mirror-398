# =============================================================================
# Docstring
# =============================================================================

"""
JSON Dumps
==========

Serialize data to JSON string.

Examples
--------
>>> from rite.serialization.json import json_dumps
>>> json_dumps({"key": "value"})
'{"key": "value"}'

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


def json_dumps(data: Any, indent: int | None = None) -> str:
    """
    Serialize data to JSON string.

    Args:
        data: Data to serialize.
        indent: Indentation spaces (None for compact).

    Returns:
        JSON string.

    Examples:
        >>> json_dumps({"key": "value"})
        '{"key": "value"}'
        >>> json_dumps({"key": "value"}, indent=2)
        '{\\n  "key": "value"\\n}'

    Notes:
        Wrapper around json.dumps.
    """
    return json.dumps(data, indent=indent)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["json_dumps"]
