# =============================================================================
# Docstring
# =============================================================================

"""
TOML Loads
==========

Parse TOML from string.

Examples
--------
>>> from rite.serialization.toml import toml_loads
>>> config = toml_loads('[section]\\nkey = "value"')

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


def toml_loads(text: str) -> dict[str, Any]:
    """
    Parse TOML from string.

    Args:
        text: TOML string to parse.

    Returns:
        Parsed TOML as dictionary.

    Raises:
        ImportError: If Python version < 3.11.

    Examples:
        >>> toml_loads('[section]\\nkey = "value"')
        {'section': {'key': 'value'}}

    Notes:
        Requires Python 3.11+ (tomllib).
    """
    try:
        # Import | Standard Library
        # pylint: disable=import-outside-toplevel
        import tomllib
    except ImportError as e:
        raise ImportError("tomllib requires Python 3.11+") from e

    result: dict[str, Any] = tomllib.loads(text)
    return result


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["toml_loads"]
