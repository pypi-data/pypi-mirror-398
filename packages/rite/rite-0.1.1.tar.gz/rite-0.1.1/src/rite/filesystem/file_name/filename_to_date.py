from __future__ import annotations

from datetime import datetime

from rite.filesystem.file_name.filename_to_datestring import (
    filename_to_datestring,
)


def filename_to_date(
    filename: str, date_format: str = "%Y-%m-%d-%H%M%S"
) -> datetime | None:
    """Extract a ``datetime`` from a filename using an embedded date segment.

    Args:
        filename: Filename to inspect.
        date_format: ``strftime`` format expected in the filename.

    Returns:
        Parsed ``datetime`` if the pattern is found, otherwise ``None``.
    """
    datestring = filename_to_datestring(filename, date_format)
    if datestring is None:
        return None
    return datetime.strptime(datestring, date_format)


# Backwards compatibility for previous misnamed function
filename_to_datefilename_to_date = filename_to_date


__all__ = ["filename_to_date", "filename_to_datefilename_to_date"]
