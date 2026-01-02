# =============================================================================
# Docstring
# =============================================================================

"""
Folder Content Delete Module
============================

Deletes all files and subdirectories inside a given folder.

"""


# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
from pathlib import Path
import shutil

# =============================================================================
# Functions
# =============================================================================


def delete_contents(
    folder: str | Path,
    *,
    dry_run: bool = False,
    verbose: bool = True,
) -> None:
    """
    Deletes all files and subdirectories inside a given folder.
    The folder itself is preserved.

    Args:
        folder (str | Path): The directory whose contents will be deleted.
        dry_run (bool): If True, shows what would be deleted without performing it.
        verbose (bool): If True, prints or logs deleted paths.
    """
    path = Path(folder)

    if not path.exists():
        raise FileNotFoundError(f"Folder does not exist: {path}")

    if not path.is_dir():
        raise NotADirectoryError(f"Not a directory: {path}")

    for item in path.iterdir():
        try:
            if item.is_file() or item.is_symlink():
                if dry_run:
                    print(f"[DRY-RUN] Would delete file: {item}")
                else:
                    item.unlink()
                    if verbose:
                        print(f"🗑️ Deleted file: {item}")
            elif item.is_dir():
                if dry_run:
                    print(f"[DRY-RUN] Would delete directory: {item}")
                else:
                    shutil.rmtree(item)
                    if verbose:
                        print(f"🗑️ Deleted folder: {item}")

        except Exception as e:
            print(f"ailed to delete {item}. Reason: {e}")
            raise


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "delete_contents",
]
