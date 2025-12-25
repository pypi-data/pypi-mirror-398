"""Asset enumerations."""
from enum import IntEnum


class AssetState(IntEnum):
    """
    Asset state enumeration.
    
    Values match the WATS API:
        0 = Unknown
        1 = In Operation
        2 = In Transit
        3 = In Maintenance
        4 = In Calibration
        5 = In Storage
        6 = Scrapped
    """
    UNKNOWN = 0
    IN_OPERATION = 1
    IN_TRANSIT = 2
    IN_MAINTENANCE = 3
    IN_CALIBRATION = 4
    IN_STORAGE = 5
    SCRAPPED = 6
    
    # Aliases for backward compatibility
    OK = 1  # Same as IN_OPERATION


class AssetAlarmState(IntEnum):
    """
    Asset alarm state as returned by the Status endpoint.
    
    This indicates alarm conditions based on thresholds configured
    on the asset type (running count, calibration due, etc.)
    """
    OK = 0
    WARNING = 1
    ALARM = 2


class AssetLogType(IntEnum):
    """
    Asset log entry type.
    
    Values from API documentation:
        0 = Message
        1 = Register (Asset created)
        2 = Update (Asset property updated)
        3 = Reset count (Running count has been reset)
        4 = Calibration (Asset has been calibrated)
        5 = Maintenance (Asset has had maintenance)
        6 = State change (Asset state was changed)
    """
    MESSAGE = 0
    REGISTER = 1
    UPDATE = 2
    RESET_COUNT = 3
    CALIBRATION = 4
    MAINTENANCE = 5
    STATE_CHANGE = 6
    
    # Aliases for backward compatibility
    UNKNOWN = 0
    CREATED = 1
    COUNT_RESET = 3
    COMMENT = 0
