"""
Yield analysis tools for AI agents.

This package provides intelligent yield analysis with semantic dimension mapping.
Translates natural language concepts to WATS API dimensions and filters.

TOOLS:
- YieldAnalysisTool: General yield queries with flexible perspectives
- YieldTrendTool: Temporal analysis (yield over time, change detection)
- YieldDeviationTool: Configuration analysis (find failure modes by dimension)

ARCHITECTURE:
- Tools use sticky filter context (AnalysisContext) for conversational flow
- Analysis sessions cache data for efficient drill-downs
- Returns token-efficient summaries, not raw data

PROCESS TERMINOLOGY IN WATS:
- test_operation: For testing (UUT/UUTReport - Unit Under Test)
- repair_operation: For repair logging (UUR/UURReport - Unit Under Repair)  
- wip_operation: For production tracking (not used in analysis tools)

COMMON PROCESS PROBLEMS:
1. Mixed processes: Different tests (AOI, ICT) sent to same process causes
   second test to show 0 units (diagnosed by different sw_filename)
2. Name confusion: Users use "PCBA" instead of "PCBA test" - use fuzzy matching
"""

# Import from the main yield tool
from .tool import (
    # Models
    YieldFilter,
    # Perspectives
    AnalysisPerspective,
    PERSPECTIVE_TO_DIMENSIONS,
    PERSPECTIVE_TO_DATE_GROUPING,
    PERSPECTIVE_ALIASES,
    resolve_perspective,
    get_available_perspectives,
    # Tool
    YieldAnalysisTool,
    get_yield_tool_definition,
    get_yield_tool_openai_schema,
    # Helpers
    build_wats_filter,
)

# Import specialized tools
from .trend_tool import (
    YieldTrendTool,
    TrendInput,
    TimeGranularity,
    create_yield_trend_tool,
)
from .deviation_tool import (
    YieldDeviationTool,
    DeviationInput,
    StandardDimension,
    resolve_dimension,
    create_yield_deviation_tool,
)
from .discovery_tool import (
    DimensionDiscoveryTool,
    DiscoveryInput,
)

__all__ = [
    # Models
    "YieldFilter",
    "TrendInput",
    "DeviationInput",
    "DiscoveryInput",
    # Enums
    "AnalysisPerspective",
    "TimeGranularity",
    "StandardDimension",
    # Mappings
    "PERSPECTIVE_TO_DIMENSIONS",
    "PERSPECTIVE_TO_DATE_GROUPING",
    "PERSPECTIVE_ALIASES",
    # Functions
    "resolve_perspective",
    "get_available_perspectives",
    "resolve_dimension",
    "build_wats_filter",
    # Tools
    "YieldAnalysisTool",
    "YieldTrendTool",
    "YieldDeviationTool",
    "DimensionDiscoveryTool",
    # Factory functions
    "create_yield_trend_tool",
    "create_yield_deviation_tool",
    # Schema helpers
    "get_yield_tool_definition",
    "get_yield_tool_openai_schema",
]
