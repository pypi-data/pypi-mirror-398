# =============================================================================
# Docstring
# =============================================================================

"""
Filesystem Module
=================

Provides core filesystem operations for paths, files, folders, and extensions.

Canonical functions are organized by domain:

- **Path:** path_clean, path_exists, path_is_dir, path_is_file, path_leaf,
  path_safe_join, path_secure
- **File:** file_read_bytes, file_read_text, file_write_bytes, file_write_text,
  copy_file, copy_files, delete_file, move_file, rename_file,
  file_size_to_string, create_spooled_temporary_file
- **Folder:** folder_ensure_exists, folder_list_files, folder_size_to_string
- **Extension:** extension_normalize, extension_validate, EXTENSION_REGEX
- **Compress:** compress_file, uncompress_file

All public symbols follow a consistent domain-prefixed naming convention.

Legacy symbols are available in the deprecated module for backwards compatibility.

Example:
    >>> from rite.filesystem import path_leaf, file_read_text
    >>> path_leaf("/path/to/file.txt")
    'file.txt'
    >>> text = file_read_text("docs/readme.md")

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Local Modules
# Compression operations
from .compress.gzip_compress import compress_file
from .compress.gzip_uncompress import uncompress_file

# File operations
from .file.file_copy import copy_file
from .file.file_copy_multiple import copy_files
from .file.file_delete import delete_file
from .file.file_move import move_file
from .file.file_read_bytes import file_read_bytes
from .file.file_read_text import file_read_text
from .file.file_rename import rename_file
from .file.file_size_to_string import file_size_to_string
from .file.file_spooled import create_spooled_temporary_file
from .file.file_write_bytes import file_write_bytes
from .file.file_write_text import file_write_text

# Extension operations
from .file_extension.extension_normalize import extension_normalize
from .file_extension.extension_regex import EXTENSION_REGEX
from .file_extension.extension_validate import extension_validate

# Folder operations
from .folder.folder_ensure_exists import folder_ensure_exists
from .folder.folder_list_files import folder_list_files
from .folder.folder_size_to_string import folder_size_to_string

# Path operations
from .path.path_clean import path_clean
from .path.path_exists import path_exists
from .path.path_is_dir import path_is_dir
from .path.path_is_file import path_is_file
from .path.path_leaf import path_leaf
from .path.path_safe_join import path_safe_join
from .path.path_secure import path_secure

# =============================================================================
# Module Exports
# =============================================================================

__all__: list[str] = [
    # Path operations
    "path_clean",
    "path_exists",
    "path_is_dir",
    "path_is_file",
    "path_leaf",
    "path_safe_join",
    "path_secure",
    # File operations
    "copy_file",
    "copy_files",
    "delete_file",
    "move_file",
    "rename_file",
    "file_size_to_string",
    "file_read_bytes",
    "file_read_text",
    "file_write_bytes",
    "file_write_text",
    "create_spooled_temporary_file",
    # Folder operations
    "folder_ensure_exists",
    "folder_list_files",
    "folder_size_to_string",
    # Extension operations
    "extension_normalize",
    "extension_validate",
    "EXTENSION_REGEX",
    # Compression operations
    "compress_file",
    "uncompress_file",
]
