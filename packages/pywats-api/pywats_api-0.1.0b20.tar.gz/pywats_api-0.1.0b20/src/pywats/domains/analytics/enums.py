"""App domain enumerations.

Enumerations for statistics, KPI, and app-related operations.
"""
from enum import IntEnum


class YieldDataType(IntEnum):
    """Types of yield data calculations."""
    FIRST_PASS = 1
    """First pass yield (passed on first attempt)."""
    
    FINAL = 2
    """Final yield (eventually passed after repairs)."""
    
    ROLLED = 3
    """Rolled throughput yield."""


class ProcessType(IntEnum):
    """Process/operation categories."""
    TEST = 1
    """Test operation."""
    
    REPAIR = 2
    """Repair operation."""
    
    CALIBRATION = 3
    """Calibration operation."""
