# =============================================================================
# Docstring
# =============================================================================

"""
Path Is File Helper
===================

Provide a thin wrapper around ``Path.is_file``.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from pathlib import Path

# Import | Libraries

# Import | Local Modules


# =============================================================================
# Functions
# =============================================================================


def path_is_file(path: str | Path) -> bool:
    """Return ``True`` if a filesystem path is a regular file."""
    return Path(path).is_file()


# =============================================================================
# Module Exports
# =============================================================================

__all__: list[str] = [
    "path_is_file",
]
