"""
The entrypoint pywrb library for opening WRB files for reading and writing
"""

import os
from typing import Literal

from pywrb.io import WRBFile


def open(
    filename: os.PathLike, mode: Literal["r", "w"] = "r", **kwargs
) -> WRBFile:  # pylint: disable=redefined-builtin
    """
    Opens a WRB file for reading or writing.

    Args:
        filename: The path to the WRB file.
        mode: The mode to open the file in, either 'r' for reading or 'w' for writing. Defaults to 'r'.
        **kwargs: Additional arguments passed to WRBFile initialization.

    Returns:
        WRBFile: An instance of WRBFile opened in the specified mode.

    Raises:
        ValueError: If the mode is not 'r' or 'w'.
    """

    if mode == "r":
        return WRBFile(filename, mode="rb", **kwargs)
    if mode == "w":
        return WRBFile(filename, mode="wb", **kwargs)
    raise ValueError(f"Mode must be 'r' or 'w', {mode} given")
