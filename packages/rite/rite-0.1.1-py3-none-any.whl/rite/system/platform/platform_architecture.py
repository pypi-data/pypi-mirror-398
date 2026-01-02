# =============================================================================
# Docstring
# =============================================================================

"""
Platform Architecture
=====================

Get system architecture.

Examples
--------
>>> from rite.system.platform import platform_architecture
>>> platform_architecture()
'x86_64'

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


def platform_architecture() -> str:
    """
    Get system architecture.

    Returns:
        Architecture string (x86_64, arm64, etc).

    Examples:
        >>> platform_architecture()
        'x86_64'
        >>> platform_architecture()
        'arm64'

    Notes:
        Returns machine type from platform.machine().
    """
    result: str = platform.machine()
    return result


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["platform_architecture"]
