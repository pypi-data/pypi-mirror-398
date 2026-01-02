# =============================================================================
# Docstring
# =============================================================================

"""
JSON Dumper
===========

Save JSON to file.

Examples
--------
>>> from rite.serialization.json import json_dump
>>> json_dump("output.json", {"key": "value"})

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


def json_dump(path: str | Path, data: Any, indent: int | None = 2) -> None:
    """
    Save JSON data to file.

    Args:
        path: Path to output JSON file.
        data: Data to serialize.
        indent: Indentation spaces (None for compact).

    Returns:
        None

    Examples:
        >>> json_dump("output.json", {"key": "value"})
        >>> json_dump("compact.json", data, indent=None)

    Notes:
        Creates parent directories if needed.
        Uses UTF-8 encoding.
    """
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with file_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["json_dump"]
