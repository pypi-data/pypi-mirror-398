# =============================================================================
# Docstring
# =============================================================================

"""
JSON Loader
===========

Load JSON from file.

Examples
--------
>>> from rite.serialization.json import json_load
>>> data = json_load("data.json")

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
import json
from pathlib import Path
from typing import Any

# =============================================================================
# Functions
# =============================================================================


def json_load(path: str | Path) -> Any:
    """
    Load JSON data from file.

    Args:
        path: Path to JSON file.

    Returns:
        Parsed JSON data.

    Raises:
        FileNotFoundError: If file doesn't exist.
        json.JSONDecodeError: If JSON is invalid.

    Examples:
        >>> json_load("config.json")
        {'key': 'value'}

    Notes:
        Uses UTF-8 encoding.
    """
    file_path = Path(path)
    with file_path.open("r", encoding="utf-8") as f:
        return json.load(f)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["json_load"]
