# =============================================================================
# Docstring
# =============================================================================

"""
Path Security Module
====================

Provides secure path operations preventing traversal attacks.

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


def path_secure(base_path: str | Path, user_path: str | Path) -> str:
    """
    Secure a file path against traversal attacks.

    Normalizes and secures a file path, ensuring it stays within the base
    directory by using only the basename of the user path.

    Args:
    ----
        base_path: The base directory path.
        user_path: The user-provided path to secure.

    Returns:
    -------
        str: A secured path string.

    Example:
    -------
        >>> path_secure("/var/data", "../../../etc/passwd")
        '/var/data/passwd'

    """
    base_path_resolved = Path(base_path).resolve()
    # Only use basename to prevent directory traversal
    file_name = Path(user_path).name
    secure_path = base_path_resolved / file_name
    return str(secure_path)


# =============================================================================
# Module Exports
# =============================================================================

__all__: list[str] = [
    "path_secure",
]
