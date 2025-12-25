"""
Asset Analysis subpackage for AI agents.

Provides tools for analyzing assets (fixtures, stations) as failure mode
dimensions, checking calibration/maintenance health, and analyzing quality
degradation over calibration cycles.

TOOL WORKFLOW:
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. AssetDimensionTool                                                       │
│    → Identifies assets with lower-than-baseline yield (suspects)            │
│    → Use when DimensionalAnalysisTool flags fixtureId/stationName          │
│                                                                             │
│ 2. AssetHealthTool                                                          │
│    → Checks calibration and maintenance status of suspect assets            │
│    → Use after AssetDimensionTool identifies suspects                       │
│                                                                             │
│ 3. AssetDegradationTool                                                     │
│    → Analyzes quality trends over calibration cycles                        │
│    → Use to fine-tune calibration intervals                                 │
│    → Use when "healthy" asset still shows yield problems                    │
└─────────────────────────────────────────────────────────────────────────────┘

INTEGRATION WITH ROOT CAUSE ANALYSIS:
Assets are ONE DIMENSION of multi-dimensional root cause analysis.
When yield drops correlate with specific asset serials, those assets
become root cause suspects that may need calibration or maintenance.
"""

# Models
from .models import (
    # Enums
    AssetHealthStatus,
    CalibrationStatus,
    AssetImpactLevel,
    DegradationTrend,
    
    # Filter models (input)
    AssetDimensionFilter,
    AssetHealthFilter,
    AssetDegradationFilter,
    
    # Result models (output)
    AssetYieldImpact,
    AssetHealthInfo,
    CalibrationCycleMetrics,
    AssetDegradationAnalysis,
    AssetDimensionResult,
    AssetHealthResult,
)

# Tools
from .dimension_tool import (
    AssetDimensionTool,
    get_asset_dimension_tool_definition,
)

from .health_tool import (
    AssetHealthTool,
    get_asset_health_tool_definition,
)

from .degradation_tool import (
    AssetDegradationTool,
    get_asset_degradation_tool_definition,
)


__all__ = [
    # Enums
    "AssetHealthStatus",
    "CalibrationStatus",
    "AssetImpactLevel",
    "DegradationTrend",
    
    # Filter models
    "AssetDimensionFilter",
    "AssetHealthFilter",
    "AssetDegradationFilter",
    
    # Result models
    "AssetYieldImpact",
    "AssetHealthInfo",
    "CalibrationCycleMetrics",
    "AssetDegradationAnalysis",
    "AssetDimensionResult",
    "AssetHealthResult",
    
    # Tools
    "AssetDimensionTool",
    "AssetHealthTool",
    "AssetDegradationTool",
    
    # Tool definitions
    "get_asset_dimension_tool_definition",
    "get_asset_health_tool_definition",
    "get_asset_degradation_tool_definition",
]
