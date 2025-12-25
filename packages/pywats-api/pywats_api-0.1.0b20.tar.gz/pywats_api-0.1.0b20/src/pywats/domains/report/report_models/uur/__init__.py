"""
UUR (Unit Under Repair) report models.

Complete implementation based on C# specifications with full API compatibility.
"""

# Core UUR models
from .uur_report import UURReport
from .uur_info import UURInfo
from .uur_part_info import UURPartInfo
from .failure import Failure

# Support models
from .fail_code import FailCode, FailCodes, FailureTypeEnum
from .misc_uur_info import MiscUURInfo, MiscUURInfoCollection
from .uur_attachment import UURAttachment
from .uur_sub_unit import UURSubUnit, UURFailure

# Legacy import (for backward compatibility)
from .sub_repair import SubRepair

__all__ = [
    # Core models
    'UURReport',
    'UURInfo', 
    'UURPartInfo',
    'Failure',
    
    # Support models
    'FailCode',
    'FailCodes',
    'FailureTypeEnum',
    'MiscUURInfo',
    'MiscUURInfoCollection', 
    'UURAttachment',
    'UURSubUnit',
    'UURFailure',
    
    # Legacy
    'SubRepair'
]