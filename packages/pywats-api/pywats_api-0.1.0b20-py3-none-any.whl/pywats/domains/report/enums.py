"""Report domain enums."""
from enum import IntEnum


class DateGrouping(IntEnum):
    """Date grouping options for filters."""
    NONE = -1
    YEAR = 0
    QUARTER = 1
    MONTH = 2
    WEEK = 3
    DAY = 4
    HOUR = 5
