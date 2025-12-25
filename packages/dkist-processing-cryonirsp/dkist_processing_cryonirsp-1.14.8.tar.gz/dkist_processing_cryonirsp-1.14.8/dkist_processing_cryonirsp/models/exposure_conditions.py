"""Support classes for exposure conditions."""

from enum import StrEnum
from typing import NamedTuple

# Number of digits used to round the exposure when creating the ExposureConditions tuple in fits_access
CRYO_EXP_TIME_ROUND_DIGITS: int = 3


class ExposureConditions(NamedTuple):
    """Named tuple to hold exposure time and filter name."""

    exposure_time: float
    filter_name: str

    def __str__(self):
        return f"{self.exposure_time}_{self.filter_name}"


class AllowableOpticalDensityFilterNames(StrEnum):
    """Enum to implement list of allowable Optical Density Filter names."""

    G278 = "G278"
    G358 = "G358"
    G408 = "G408"
    OPEN = "OPEN"
    NONE = "NONE"
