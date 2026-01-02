# =============================================================================
# Docstring
# =============================================================================

"""
CSV Writer
==========

Write list of dicts to CSV file.

Examples
--------
>>> from rite.serialization.csv import csv_write
>>> data = [{"col1": "val1", "col2": "val2"}]
>>> csv_write("output.csv", data)

"""

# =============================================================================
# Imports
# =============================================================================

# Import | Future
from __future__ import annotations

# Import | Standard Library
import csv
from pathlib import Path
from typing import Any

# =============================================================================
# Functions
# =============================================================================


def csv_write(
    path: str | Path,
    data: list[dict[str, Any]],
    delimiter: str = ",",
) -> None:
    """
    Write list of dictionaries to CSV file.

    Args:
        path: Path to output CSV file.
        data: List of row dictionaries.
        delimiter: CSV delimiter character.

    Returns:
        None

    Examples:
        >>> data = [{"col1": "val1", "col2": "val2"}]
        >>> csv_write("output.csv", data)
        >>> csv_write("output.tsv", data, delimiter="\\t")

    Notes:
        Creates parent directories if needed.
        Header from first row keys.
    """
    if not data:
        return

    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = list(data[0].keys())

    with file_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
        writer.writeheader()
        writer.writerows(data)


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = ["csv_write"]
