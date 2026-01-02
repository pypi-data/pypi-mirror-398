# =============================================================================
# Docstring
# =============================================================================

"""
INI Writer
==========

Write nested dict to INI file.

Examples
--------
>>> from rite.serialization.ini import ini_write
>>> config = {"section": {"key": "value"}}
>>> ini_write("config.ini", config)

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


def ini_write(path: str | Path, data: dict[str, dict[str, str]]) -> None:
    """
    Write nested dictionary to INI file.

    Args:
        path: Path to output INI file.
        data: Nested dict of sections and key-value pairs.

    Returns:
        None

    Examples:
        >>> config = {"section": {"key": "value"}}
        >>> ini_write("config.ini", config)

    Notes:
        Creates parent directories if needed.
        Uses ConfigParser for formatting.
    """
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    parser = configparser.ConfigParser()

    for section, values in data.items():
        parser.add_section(section)
        for key, value in values.items():
            parser.set(section, key, str(value))

    with file_path.open("w", encoding="utf-8") as f:
        parser.write(f)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["ini_write"]
