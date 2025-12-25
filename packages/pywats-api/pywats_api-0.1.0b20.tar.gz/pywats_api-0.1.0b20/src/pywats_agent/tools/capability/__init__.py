"""
Process Capability Analysis subpackage.

Provides SPC (Statistical Process Control) and capability metrics
for manufacturing quality assessment.
"""

from .tool import (
    # Filter
    ProcessCapabilityInput,
    
    # Tool
    ProcessCapabilityTool,
    get_process_capability_tool_definition,
    
    # Enums
    StabilityStatus,
    CapabilityStatus,
    ImprovementPriority,
    HiddenModeType,
    
    # Results
    ProcessCapabilityResult,
    MeasurementCapabilityResult,
    DualCpkAnalysis,
    StabilityAnalysis,
    HiddenMode,
    
    # Constants
    CPK_CAPABLE,
    CPK_MARGINAL,
    CPK_CRITICAL,
    CPK_EXCELLENT,
)

# Alias for consistency
ProcessCapabilityFilter = ProcessCapabilityInput

__all__ = [
    # Filter
    "ProcessCapabilityFilter",
    "ProcessCapabilityInput",
    
    # Tool
    "ProcessCapabilityTool",
    "get_process_capability_tool_definition",
    
    # Enums
    "StabilityStatus",
    "CapabilityStatus",
    "ImprovementPriority",
    "HiddenModeType",
    
    # Results
    "ProcessCapabilityResult",
    "MeasurementCapabilityResult",
    "DualCpkAnalysis",
    "StabilityAnalysis",
    "HiddenMode",
    
    # Constants
    "CPK_CAPABLE",
    "CPK_MARGINAL",
    "CPK_CRITICAL",
    "CPK_EXCELLENT",
]
