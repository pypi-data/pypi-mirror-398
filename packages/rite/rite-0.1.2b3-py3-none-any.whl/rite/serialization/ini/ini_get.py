# =============================================================================
# Docstring
# =============================================================================

"""
INI Get Value
=============

Get value from INI configuration.

Examples
--------
>>> from rite.serialization.ini import ini_get
>>> ini_get("config.ini", "section", "key")
'value'

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
import configparser
from pathlib import Path

# =============================================================================
# Functions
# =============================================================================


def ini_get(
    path: str | Path, section: str, key: str, default: str | None = None
) -> str | None:
    """
    Get value from INI file.

    Args:
        path: Path to INI file.
        section: Section name.
        key: Key name.
        default: Default value if not found.

    Returns:
        Value string or default.

    Examples:
        >>> ini_get("config.ini", "section", "key")
        'value'
        >>> ini_get("config.ini", "section", "missing", "default")
        'default'

    Notes:
        Returns default if section or key not found.
    """
    file_path = Path(path)
    parser = configparser.ConfigParser()
    parser.read(str(file_path), encoding="utf-8")

    try:
        result: str = parser.get(section, key)
        return result
    except (configparser.NoSectionError, configparser.NoOptionError):
        return default


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["ini_get"]
