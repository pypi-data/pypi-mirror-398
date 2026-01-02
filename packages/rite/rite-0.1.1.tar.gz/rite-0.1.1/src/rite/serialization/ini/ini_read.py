# =============================================================================
# Docstring
# =============================================================================

"""
INI Reader
==========

Read INI configuration file.

Examples
--------
>>> from rite.serialization.ini import ini_read
>>> config = ini_read("config.ini")

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


def ini_read(path: str | Path) -> dict[str, dict[str, str]]:
    """
    Read INI file to nested dictionary.

    Args:
        path: Path to INI file.

    Returns:
        Nested dictionary of sections and key-value pairs.

    Examples:
        >>> ini_read("config.ini")
        {'section': {'key': 'value'}}

    Notes:
        Uses ConfigParser for INI parsing.
        Returns nested dict structure.
    """
    file_path = Path(path)
    parser = configparser.ConfigParser()
    parser.read(str(file_path), encoding="utf-8")

    result: dict[str, dict[str, str]] = {}
    for section in parser.sections():
        result[section] = dict(parser.items(section))

    return result


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["ini_read"]
