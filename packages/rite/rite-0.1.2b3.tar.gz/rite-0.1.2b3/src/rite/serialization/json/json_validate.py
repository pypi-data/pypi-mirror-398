# =============================================================================
# Docstring
# =============================================================================

"""
JSON Validator
==============

Validate JSON string.

Examples
--------
>>> from rite.serialization.json import json_validate
>>> json_validate('{"key": "value"}')
True

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
import json

# =============================================================================
# Functions
# =============================================================================


def json_validate(text: str) -> bool:
    """
    Validate JSON string.

    Args:
        text: JSON string to validate.

    Returns:
        True if valid JSON, False otherwise.

    Examples:
        >>> json_validate('{"key": "value"}')
        True
        >>> json_validate('{invalid}')
        False
        >>> json_validate('[1, 2, 3]')
        True

    Notes:
        Returns False on any JSON decode error.
    """
    try:
        json.loads(text)
        return True
    except json.JSONDecodeError:
        return False


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["json_validate"]
