# =============================================================================
# Docstring
# =============================================================================

"""
Platform Python Version
=======================

Get Python version information.

Examples
--------
>>> from rite.system.platform import platform_python_version
>>> platform_python_version()
'3.10.5'

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


def platform_python_version() -> str:
    """
    Get Python version string.

    Returns:
        Python version (e.g., '3.10.5').

    Examples:
        >>> platform_python_version()
        '3.10.5'
        >>> platform_python_version()
        '3.11.2'

    Notes:
        Returns version from platform.python_version().
    """
    result: str = platform.python_version()
    return result


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["platform_python_version"]
