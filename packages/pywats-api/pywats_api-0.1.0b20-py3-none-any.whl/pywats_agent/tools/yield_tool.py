"""
Re-export yield tool from yield_pkg for backward compatibility.

The actual implementation is in yield_pkg/tool.py
This module exists so that `from pywats_agent.tools.yield_tool import ...`
continues to work.
"""

# Re-export everything from yield_pkg
from .yield_pkg import (
    # Main tool
    YieldAnalysisTool,
    YieldFilter,
    
    # Perspectives and mapping
    AnalysisPerspective,
    PERSPECTIVE_TO_DIMENSIONS,
    PERSPECTIVE_TO_DATE_GROUPING,
    PERSPECTIVE_ALIASES,
    resolve_perspective,
    get_available_perspectives,
    
    # Helper
    build_wats_filter,
    
    # Schema helpers
    get_yield_tool_definition,
    get_yield_tool_openai_schema,
    
    # Specialized tools
    YieldTrendTool,
    YieldDeviationTool,
    DimensionDiscoveryTool,
    TrendInput,
    DeviationInput,
    DiscoveryInput,
    TimeGranularity,
    StandardDimension,
    resolve_dimension,
    create_yield_trend_tool,
    create_yield_deviation_tool,
)

__all__ = [
    # Main tool
    "YieldAnalysisTool",
    "YieldFilter",
    
    # Perspectives and mapping  
    "AnalysisPerspective",
    "PERSPECTIVE_TO_DIMENSIONS",
    "PERSPECTIVE_TO_DATE_GROUPING",
    "PERSPECTIVE_ALIASES",
    "resolve_perspective",
    "get_available_perspectives",
    
    # Helper
    "build_wats_filter",
    
    # Schema helpers
    "get_yield_tool_definition",
    "get_yield_tool_openai_schema",
    
    # Specialized tools
    "YieldTrendTool",
    "YieldDeviationTool",
    "DimensionDiscoveryTool",
    "TrendInput",
    "DeviationInput",
    "DiscoveryInput",
    "TimeGranularity",
    "StandardDimension",
    "resolve_dimension",
    "create_yield_trend_tool",
    "create_yield_deviation_tool",
]
