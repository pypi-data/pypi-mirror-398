# =============================================================================
# Docstring
# =============================================================================

"""
Platform Module
===============

Platform and OS detection utilities.

This submodule provides utilities for detecting the operating system,
architecture, and platform information.

Examples
--------
>>> from rite.system.platform import platform_name, platform_is_linux
>>> platform_name()
'Linux'
>>> platform_is_linux()
True

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .platform_architecture import platform_architecture
from .platform_is_linux import platform_is_linux
from .platform_is_macos import platform_is_macos
from .platform_is_windows import platform_is_windows
from .platform_name import platform_name
from .platform_python_version import platform_python_version

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "platform_name",
    "platform_architecture",
    "platform_is_windows",
    "platform_is_linux",
    "platform_is_macos",
    "platform_python_version",
]
