

# =============================================================================
# Docstring
# =============================================================================

"""
Mimetype Guess From Path
========================

Guess the mimetype and encoding from a file path using ``mimetypes``.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
import mimetypes
from pathlib import Path
from typing import Tuple

# =============================================================================
# Functions
# =============================================================================


def mimetype_guess_from_path(
    path: str | Path,
) -> Tuple[str | None, str | None]:
    """Return mimetype and encoding guessed from the file name.

    Args
    ----
        path: File path.

    Returns
    -------
        (type, encoding): Tuple of strings or ``None`` values.

    """
    return mimetypes.guess_type(str(Path(path)))


# =============================================================================
# Module Exports
# =============================================================================

__all__: list[str] = [
    "mimetype_guess_from_path",
]
