"""Production domain enums."""
from enum import IntEnum, IntFlag


class SerialNumberIdentifier(IntEnum):
    """Serial number identifier type."""
    SERIAL_NUMBER = 0
    MAC_ADDRESS = 1
    IMEI = 2


class UnitPhaseFlag(IntFlag):
    """
    Unit phase flags representing lifecycle states.
    
    Each value is a power of 2, allowing potential combination via bitwise OR
    for filtering or querying multiple phases. For setting a unit's phase,
    use a single value.
    
    Example:
        # Single phase
        phase = UnitPhaseFlag.FINALIZED
        
        # Multiple phases for filtering (future use)
        phases = UnitPhaseFlag.UNDER_PRODUCTION | UnitPhaseFlag.FINALIZED
    """
    UNKNOWN = 1
    UNDER_PRODUCTION = 2
    PRODUCTION_REPAIR = 4
    SERVICE_REPAIR = 8
    FINALIZED = 16
    SCRAPPED = 32
    EXTENDED_TEST = 64
    CUSTOMIZATION = 128
    REPAIRED = 256
    MISSING = 512
    IN_STORAGE = 1024
    SHIPPED = 2048
