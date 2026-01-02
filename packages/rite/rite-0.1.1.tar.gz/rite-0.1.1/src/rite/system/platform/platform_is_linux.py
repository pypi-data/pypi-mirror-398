# =============================================================================
# Docstring
# =============================================================================

"""
Platform Is Linux
=================

Check if running on Linux.

Examples
--------
>>> from rite.system.platform import platform_is_linux
>>> platform_is_linux()
True

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
import platform

# =============================================================================
# Functions
# =============================================================================


def platform_is_linux() -> bool:
    """
    Check if running on Linux.

    Returns:
        True if Linux, False otherwise.

    Examples:
        >>> platform_is_linux()
        True
        >>> platform_is_linux()
        False

    Notes:
        Checks if platform.system() is 'Linux'.
    """
    return platform.system() == "Linux"


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["platform_is_linux"]
