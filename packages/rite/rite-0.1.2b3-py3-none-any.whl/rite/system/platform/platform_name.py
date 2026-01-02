# =============================================================================
# Docstring
# =============================================================================

"""
Platform Name
=============

Get operating system name.

Examples
--------
>>> from rite.system.platform import platform_name
>>> platform_name()
'Linux'

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


def platform_name() -> str:
    """
    Get operating system name.

    Returns:
        OS name (Linux, Darwin, Windows, etc).

    Examples:
        >>> platform_name()
        'Linux'
        >>> platform_name()
        'Darwin'

    Notes:
        Returns system name from platform.system().
    """
    result: str = platform.system()
    return result


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["platform_name"]
