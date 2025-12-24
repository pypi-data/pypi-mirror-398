"""
pywrb.constants
~~~~~~~~~~~~~~~

This module contains constants used in the pywrb library."""

import enum

import numpy


class WRB_BLOCK_MEANING(enum.Enum):  # pylint: disable=invalid-name
    """Meaning of a block in a WRB file."""

    UNKNOWN = 0
    ELEVATION = 1
    MEAN_WIND_SPEED = 2
    WEIBULL_SCALE = 3
    WEIBULL_SHAPE = 4
    POWER = 5
    TURBULENCE_INTENSITY = 6
    INFLOW_ANGLE = 7
    PROBABILITY = 8
    DIRECTION = 9
    ROUGHNESS_LENGTH = 10
    AIR_DENSITY = 11
    VERTICAL_VELOCITY = 12
    WIND_SHEAR_EXPONENT = 13
    GROUND_POROSITY = 14
    VEGETATION_HEIGHT = 15
    ELOSS = 16
    UNCERTAINTY = 17


class WRB_UNIT(enum.Enum):  # pylint: disable=invalid-name
    """Unit of a block in a WRB file."""

    DEFAULT = 0
    METER = 1
    METER_PER_SECOND = 2
    DEGREE_360 = 3
    DEGREE_180 = 4  # this is the only one getting actively used just now (for inflow angle layers)
    PERCENT = 5


# Mapping of numpy data types to WRB data types
WRB_NUMPY_DATA_TYPES = {numpy.float32: 0, numpy.float64: 1, numpy.byte: 2, numpy.int16: 3, numpy.int32: 4}

# Header structure of a WRB file
WRB_HEADER_STRUCT = "=HHbb30sHHHddddddH8x"

# Block header structure of a WRB file
WRB_BLOCK_HEADER_STRUCT = "=HfhfdlqbH29x"
