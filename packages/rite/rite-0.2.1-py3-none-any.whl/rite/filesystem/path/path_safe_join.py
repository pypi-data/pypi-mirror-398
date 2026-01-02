# =============================================================================
# Docstring
# =============================================================================

"""
Safe Path Join Module
=====================

Provides safe path joining preventing traversal outside base directory.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
import posixpath
from typing import Any

# =============================================================================
# Functions
# =============================================================================


def path_safe_join(base_directory_path: str, *path_components: Any) -> str:
    """
    Safely join path components ensuring result stays under the base directory.

    This function prevents directory traversal attacks by ensuring the
    resulting path never escapes the base directory.

    Args:
    ----
        base_directory_path: Base directory path.
        *path_components: Path components to join.

    Returns:
    -------
        str: Joined path relative to base (without leading slash).

    Raises:
    ------
        ValueError: If joined path escapes base directory.

    Example:
    -------
        >>> path_safe_join("/var/data", "uploads", "file.txt")
        'var/data/uploads/file.txt'
        >>> path_safe_join("/var/data", "../etc/passwd")
        Traceback (most recent call last):
        ValueError: the joined path is located outside of the base path

    """
    base_path = base_directory_path.rstrip("/")
    final_path = base_path + "/"

    for path_component in path_components:
        _final_path = posixpath.normpath(
            posixpath.join(final_path, str(path_component)),
        )
        # Preserve trailing slash if original path had one
        if (
            str(path_component).endswith("/")
            or _final_path + "/" == final_path
        ):
            _final_path += "/"
        final_path = _final_path

    if final_path == base_path:
        final_path += "/"

    base_path_len = len(base_path)

    # Verify the path stays within base
    if (
        not final_path.startswith(base_path)
        or final_path[base_path_len] != "/"
    ):
        raise ValueError("the joined path is located outside of the base path")

    return final_path.lstrip("/")


# =============================================================================
# Module Exports
# =============================================================================

__all__: list[str] = [
    "path_safe_join",
]
