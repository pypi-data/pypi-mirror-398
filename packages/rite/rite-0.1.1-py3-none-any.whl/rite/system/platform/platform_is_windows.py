# =============================================================================
# Docstring
# =============================================================================

"""
Platform Is Windows
===================

Check if running on Windows.

Examples
--------
>>> from rite.system.platform import platform_is_windows
>>> platform_is_windows()
False

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


def platform_is_windows() -> bool:
    """
    Check if running on Windows.

    Returns:
        True if Windows, False otherwise.

    Examples:
        >>> platform_is_windows()
        False
        >>> platform_is_windows()
        True

    Notes:
        Checks if platform.system() is 'Windows'.
    """
    return platform.system() == "Windows"


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["platform_is_windows"]
