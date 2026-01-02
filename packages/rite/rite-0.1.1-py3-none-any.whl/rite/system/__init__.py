# =============================================================================
# Docstring
# =============================================================================

"""
System Module
=============

System-level operations and utilities.

This module provides comprehensive utilities for system operations
including process management, environment variables, platform detection,
path operations, and shell command handling.

Submodules
----------
- process: Process and subprocess management
- environment: Environment variable operations
- platform: Platform and OS detection
- path: Path operations and queries
- shell: Shell command utilities

Examples
--------
>>> from rite.system import process_run, env_get, platform_name
>>> code, out, err = process_run(["ls"], Path.cwd())
>>> home = env_get("HOME")
>>> os_name = platform_name()

Notes
-----
Legacy functions run_command and get_escaped_command_arg
are still available for backward compatibility.
"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
from .environment import env_delete, env_get, env_list, env_set
from .get_escaped_command_arg import get_escaped_command_arg
from .path import (
    path_absolute,
    path_exists,
    path_is_dir,
    path_is_file,
    path_join,
)
from .platform import (
    platform_architecture,
    platform_is_linux,
    platform_is_macos,
    platform_is_windows,
    platform_name,
    platform_python_version,
)
from .process import process_call, process_check_output, process_run
from .run_command import run_command
from .shell import shell_escape, shell_join, shell_split

# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    # Process
    "process_run",
    "process_check_output",
    "process_call",
    # Environment
    "env_get",
    "env_set",
    "env_delete",
    "env_list",
    # Platform
    "platform_name",
    "platform_architecture",
    "platform_is_windows",
    "platform_is_linux",
    "platform_is_macos",
    "platform_python_version",
    # Path
    "path_exists",
    "path_is_file",
    "path_is_dir",
    "path_absolute",
    "path_join",
    # Shell
    "shell_escape",
    "shell_split",
    "shell_join",
    # Legacy
    "run_command",
    "get_escaped_command_arg",
]
