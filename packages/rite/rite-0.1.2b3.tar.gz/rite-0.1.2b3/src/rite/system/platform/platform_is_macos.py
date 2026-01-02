# =============================================================================
# Docstring
# =============================================================================

"""
Platform Is MacOS
=================

Check if running on macOS.

Examples
--------
>>> from rite.system.platform import platform_is_macos
>>> platform_is_macos()
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


def platform_is_macos() -> bool:
    """
    Check if running on macOS.

    Returns:
        True if macOS, False otherwise.

    Examples:
        >>> platform_is_macos()
        True
        >>> platform_is_macos()
        False

    Notes:
        Checks if platform.system() is 'Darwin'.
    """
    return platform.system() == "Darwin"


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["platform_is_macos"]
