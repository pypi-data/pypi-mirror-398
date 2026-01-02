# =============================================================================
# Docstring
# =============================================================================

"""
File Write Text
===============

Write text to a file, creating parent directories if needed.

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


def file_write_text(
    path: str | Path,
    text: str,
    encoding: str = "utf-8",
) -> None:
    """Write text to a file, creating parent directories if needed.

    Args
    ----
        path: File path.
        text: Text content to write.
        encoding: Text encoding to use.

    """
    path_object = Path(path)
    path_object.parent.mkdir(parents=True, exist_ok=True)
    path_object.write_text(text, encoding=encoding)


# =============================================================================
# Module Exports
# =============================================================================

__all__: list[str] = [
    "file_write_text",
]
