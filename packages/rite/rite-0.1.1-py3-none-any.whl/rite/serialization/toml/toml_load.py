# =============================================================================
# Docstring
# =============================================================================

"""
TOML Load
=========

Load TOML from file.

Examples
--------
>>> from rite.serialization.toml import toml_load
>>> config = toml_load("config.toml")

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from pathlib import Path
from typing import Any

# =============================================================================
# Functions
# =============================================================================


def toml_load(path: str | Path) -> dict[str, Any]:
    """
    Load TOML from file.

    Args:
        path: Path to TOML file.

    Returns:
        Parsed TOML as dictionary.

    Raises:
        ImportError: If Python version < 3.11.

    Examples:
        >>> toml_load("config.toml")
        {'section': {'key': 'value'}}

    Notes:
        Requires Python 3.11+ (tomllib).
        Read-only (no write support in stdlib).
    """
    try:
        # Import | Standard Library
        # pylint: disable=import-outside-toplevel
        import tomllib
    except ImportError as e:
        raise ImportError("tomllib requires Python 3.11+") from e

    file_path = Path(path)

    with file_path.open("rb") as f:
        result: dict[str, Any] = tomllib.load(f)

    return result


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["toml_load"]
