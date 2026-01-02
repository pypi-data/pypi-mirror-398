# =============================================================================
# Docstring
# =============================================================================

"""
INI Set Value
=============

Set value in INI configuration.

Examples
--------
>>> from rite.serialization.ini import ini_set
>>> ini_set("config.ini", "section", "key", "value")

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


def ini_set(path: str | Path, section: str, key: str, value: str) -> None:
    """
    Set value in INI file.

    Args:
        path: Path to INI file.
        section: Section name.
        key: Key name.
        value: Value to set.

    Returns:
        None

    Examples:
        >>> ini_set("config.ini", "section", "key", "value")

    Notes:
        Creates section if not exists.
        Creates file if not exists.
    """
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    parser = configparser.ConfigParser()
    if file_path.exists():
        parser.read(str(file_path), encoding="utf-8")

    if not parser.has_section(section):
        parser.add_section(section)

    parser.set(section, key, str(value))

    with file_path.open("w", encoding="utf-8") as f:
        parser.write(f)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["ini_set"]
