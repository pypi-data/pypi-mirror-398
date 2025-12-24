"""
pywrb.io
~~~~~~~~

This module contains the implementation for reading and writing WRB files."""

import math
import numbers
import os
import struct
import warnings

import numpy as np

from pywrb.constants import (
    WRB_BLOCK_HEADER_STRUCT,
    WRB_BLOCK_MEANING,
    WRB_HEADER_STRUCT,
    WRB_NUMPY_DATA_TYPES,
    WRB_UNIT,
)


def crs_from_utmzone(zone) -> str:
    """Returns the EPSG code for a given UTM zone.

    Args:
        zone (str): The UTM zone name, i.e 17S.
        northern (bool): True if the zone is in the northern hemisphere, False otherwise.

    Returns:
        str: The EPSG code for the given UTM zone.
    """
    if zone[2].upper() in "CDEFGHJKLM":
        return f"epsg:{32700 + int(zone[:2])}"
    return f"epsg:{32600 + int(zone[:2])}"


class WRBFile:
    """
    A class for reading and writing WRB files analogous to the python file object
    """

    def __init__(
        self,
        filename: str,
        mode: str = "rb",
        *,
        minx: numbers.Number | None = None,
        miny: numbers.Number | None = None,
        maxx: numbers.Number | None = None,
        maxy: numbers.Number | None = None,
        resolutionx: numbers.Number | None = None,
        resolutiony: numbers.Number | None = None,
        crs: str = None,
        heights: list[numbers.Number] = None,
        wind_speeds: list[numbers.Number] = None,
        directions: int | None = None,
    ):

        if mode in ("r", "w"):
            mode += "b"

        if mode not in ("rb", "wb"):
            raise ValueError(f"Mode must be 'rb' or 'wb', {mode} given")

        self.type = 1001
        self.version = 2
        self.horizontal_units = WRB_UNIT.METER.value
        self.vertical_units = WRB_UNIT.METER.value

        if mode == "wb":
            self.minx = float(minx)
            self.miny = float(miny)
            self.maxx = float(maxx)
            self.maxy = float(maxy)
            self.resolutionx = float(resolutionx)
            self.resolutiony = float(resolutiony)
            self.crs = str(crs).lower()
            self.heights = sorted(tuple(set(heights)))
            self.wind_speeds = sorted(tuple(set(wind_speeds)))
            self.number_of_wind_directions = int(directions)

        self._filename = filename
        self._file = None
        self.mode = mode

        self.blocks = []
        self.number_of_blocks = 0

    @property
    def width(self):
        return math.floor((self.maxx - self.minx) / self.resolutionx) + 1

    @property
    def height(self):
        return math.floor((self.maxy - self.miny) / self.resolutiony) + 1

    @property
    def shape(self):
        return (self.width, self.height)

    @property
    def bounds(self):
        return (self.minx, self.miny, self.maxx, self.maxy)

    @property
    def res(self):
        return (self.resolutionx, self.resolutiony)

    @property
    def x(self):
        return np.arange(self.minx, self.maxx + 1, self.resolutionx)

    @property
    def y(self):
        return np.arange(self.miny, self.maxy + 1, self.resolutiony)

    @property
    def directions(self):
        return list(np.linspace(0, 360, self.number_of_wind_directions, endpoint=False))

    def __enter__(self):
        exists = os.path.exists(self._filename)
        self._file = open(self._filename, self.mode)  # pylint: disable=unspecified-encoding
        if self.mode == "rb" and exists:
            self.read_metadata()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._file.close()
        self._file = None
        self.blocks = []

    def find_blocks(self, meaning: WRB_BLOCK_MEANING) -> list[dict]:
        """
        Finds all blocks in the WRB file with the given meaning.

        Args:
            meaning: The meaning of the blocks to find. Must be a value from the WRB_BLOCK_MEANING enum.

        Returns:
            A list of dictionaries, each containing a block with the specified meaning.
        """
        return [block for block in self.blocks if block["meaning"] == meaning]

    def add_block(  # pylint: disable=too-many-arguments
        self,
        data: np.ndarray,
        meaning: WRB_BLOCK_MEANING | str,
        height: float = None,
        wind_speed: float = None,
        direction: int = None,
        probability: float = None,
        id: int = None,  # pylint: disable=invalid-name,redefined-builtin
        unit=WRB_UNIT.DEFAULT,
        **kwargs,
    ) -> None:
        """
        Adds a block to the WRB file.

        Args:
            data: The data to add to the block. Must have the same shape as the WRB file.
            meaning: The meaning of the data in the block. Must be a value from the WRB_BLOCK_MEANING enum.
            height: The height of the data in the block. Defaults to 0.0.
            wind_speed: The wind speed of the data in the block. Defaults to 0.0.
            direction: The direction of the data in the block. Defaults to 0.
            probability: The probability of the data in the block. Defaults to 0.0.
            id: The id of the block. Defaults to the next available id.
            unit: The unit of the data in the block, a value from the WRB_UNIT enum. Defaults to WRB_UNIT.DEFAULT.

        Raises:
            ValueError: If the shape of the data does not match the shape of the WRB file.
            ValueError: If the meaning is not a valid block meaning.
            ValueError: If the unit is not a valid block unit.
            ValueError: If direction is not a valid sector, or any float outside of a valid sector.

        """
        if data.shape != self.shape:
            raise ValueError(f"Shape of uploaded data {data.shape} is not equal to {self.shape}")

        if isinstance(meaning, str):
            meaning = WRB_BLOCK_MEANING[meaning.upper()]

        if meaning not in WRB_BLOCK_MEANING:
            raise ValueError(
                f"Meaning {meaning} is not a valid block meaning, supported are {tuple(WRB_BLOCK_MEANING)}"
            )

        if unit not in WRB_UNIT:
            raise ValueError(f"Unit {unit} is not a valid block unit, supported are {tuple(WRB_UNIT)}")

        if direction and isinstance(direction, (np.floating, float)):
            direction = self.directions.index(direction)  # will raise ValueError if not found
        if direction and not (0 <= direction < len(self.directions)):
            raise ValueError(f"Direction {direction} is not a valid block direction, supported are {self.directions}")

        if not id:
            id = len(self.blocks)

        block = dict(
            data_type=WRB_NUMPY_DATA_TYPES[data.dtype.type],
            direction=direction,
            meaning=meaning.value,
            height=height,
            wind_speed=wind_speed,
            probability=probability,
            unit=unit.value,
            id=id,
            data=data,
        )

        # Update or overwrite blocks
        for existing_block in self.blocks:
            if existing_block["id"] == id:
                self.blocks[self.blocks.index(existing_block)] = block
                break
        else:
            self.blocks.append(block)

    def read_metadata(
        self,
    ) -> "WRBFile":
        """
        Reads the WRB file from the beginning, extracting the header and block information.

        The method first reads the header to retrieve metadata including type, version,
        coordinate reference system (CRS), spatial extents, resolution, and number of blocks.
        Then, it iterates through each block to extract block-specific metadata and data.
        The data of each block is read into a NumPy array and reshaped according to the
        calculated shape derived from the spatial extents and resolution.

        Returns:
            WRBFile: The instance of the WRBFile with populated header and block information.
        """

        self._file.seek(0)

        # read the header
        header_data = struct.unpack(WRB_HEADER_STRUCT, self._file.read(100))

        crs = header_data[4].decode("ascii").strip().upper()
        if crs.startswith("UTM"):
            crs = crs_from_utmzone(crs.replace("UTM", ""))
        if not crs.lower().startswith("epsg:"):
            warnings.warn(f"CRS '{crs}' is not in EPSG format, unexpected behavior may occur")

        # extract the header information
        self.type = header_data[0]
        self.version = header_data[1]
        self.horizontal_units = header_data[2]
        self.vertical_units = header_data[3]
        self.crs = crs
        self.number_of_wind_directions = header_data[5]
        self.number_of_heights = header_data[6]
        self.number_of_wind_speeds = header_data[7]
        self.minx = header_data[8]
        self.maxx = header_data[9]
        self.miny = header_data[10]
        self.maxy = header_data[11]
        self.resolutionx = header_data[12]
        self.resolutiony = header_data[13]
        self.number_of_blocks = header_data[14]

        self.block_types = set()
        self.heights = set()
        self.wind_speeds = set()

        np_data_types = {v: k for k, v in WRB_NUMPY_DATA_TYPES.items()}
        directions = self.directions + [-1]

        for _ in range(self.number_of_blocks):
            block_metadata = self._file.read(64)
            block_header = struct.unpack(WRB_BLOCK_HEADER_STRUCT, block_metadata)

            meaning = WRB_BLOCK_MEANING(block_header[0])
            height = None if block_header[1] == -1.0 else block_header[1]
            direction = None if block_header[2] == -1 else directions[block_header[2]]
            wind_speed = None if block_header[3] == -1.0 else block_header[3]
            # TvW: Somehow parsing the unit value is not properly encoded as hex in python's struct module and comes back as b'00' instead of b'\x00'
            # This might be a result of the padding
            unit = block_header[8] - 12336 if block_header[8] >= 12336 else block_header[8]

            block = dict(
                meaning=meaning,
                height=height,
                direction=direction,
                wind_speed=wind_speed,
                probability=block_header[4],
                id=block_header[5],
                offset=block_header[6],
                data_type=np_data_types[block_header[7]],
                unit=WRB_UNIT(unit),
            )
            self.blocks.append(block)

            self.block_types |= {meaning}
            if height is not None:
                self.heights |= {height}
            if wind_speed is not None:
                self.wind_speeds |= {wind_speed}

        self.heights = np.array(sorted(self.heights))
        self.wind_speeds = np.array(sorted(self.wind_speeds))

        return self

    def read_block(self, block_id):
        block = self.blocks[block_id]
        self._file.seek(block["offset"])
        dtype = block["data_type"]
        return np.frombuffer(self._file.read(self.shape[0] * self.shape[1] * dtype().nbytes), dtype=dtype).reshape(
            self.shape
        )

    def __iter__(self):
        if not self._file:
            raise ValueError(f"File {self._filename} has not been opened")

        for i, block in enumerate(self.blocks):
            yield block, self.read_block(i)

    def write(
        self,
    ) -> bool:
        """
        Writes the WRB file to disk.

        Returns True on success, False on failure.
        """
        self._file.seek(0)
        self.number_of_blocks = len(self.blocks)

        header_string = struct.pack(
            WRB_HEADER_STRUCT,
            self.type,
            self.version,
            self.horizontal_units,
            self.vertical_units,
            self.crs.encode("ascii").rjust(30),
            len(self.directions),
            len(self.heights),
            len(self.wind_speeds),
            self.minx,
            self.maxx,
            self.miny,
            self.maxy,
            self.resolutionx,
            self.resolutiony,
            self.number_of_blocks,
        )

        self._file.write(header_string)

        cursor = len(header_string)
        cursor += 64 * len(self.blocks)

        for block in self.blocks:
            block_header = struct.pack(
                WRB_BLOCK_HEADER_STRUCT,
                block["meaning"],
                block["height"] or -1.0,
                block["direction"] or -1,
                block["wind_speed"] or -1.0,
                block["probability"] or 1,
                block["id"],
                cursor,
                block["data_type"],
                block["unit"],
            )

            cursor += block["data"].nbytes

            self._file.write(block_header)

        for block in self.blocks:
            block["data"].reshape(self.shape).tofile(self._file)

        return True
