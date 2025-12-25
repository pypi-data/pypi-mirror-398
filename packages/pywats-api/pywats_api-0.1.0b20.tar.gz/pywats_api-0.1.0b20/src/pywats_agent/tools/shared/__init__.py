"""
Shared utilities for agent tools.

This package contains utilities used across multiple tool domains:
- adaptive_time: Smart time window selection based on volume
- process_resolver: Fuzzy process name matching
- context: Sticky filter memory for conversational context
- session: Analysis session caching for efficient drill-downs
- computations: Statistical calculations and insight generation
"""

from .adaptive_time import (
    AdaptiveTimeFilter,
    AdaptiveTimeConfig,
    AdaptiveTimeResult,
    VolumeCategory,
)
from .process_resolver import (
    ProcessResolver,
    PROCESS_ALIASES,
    normalize_process_name,
    diagnose_mixed_process_problem,
)
from .context import (
    AnalysisContext,
    FilterMemory,
    ContextConfidence,
    get_context,
)
from .session import (
    AnalysisSession,
    SessionManager,
    SessionType,
    TemporalMatrix,
    DeviationMatrix,
    DeviationCell,
    get_session_manager,
    create_trend_session,
    create_deviation_session,
)
from .computations import (
    TrendDirection,
    Volatility,
    SignificanceLevel,
    TrendAnalysis,
    DeviationAnalysis,
    calculate_trend,
    calculate_deviation_significance,
    rank_deviations,
    generate_trend_insight,
    generate_deviation_insight,
    generate_failure_mode_hypothesis,
    summarize_for_agent,
)
from .statistics import (
    AnalysisType,
    MetricType,
    SampleSizeThresholds,
    DeviationThresholds,
    DimensionCardinalityLimits,
    StatisticalConfig,
    DimensionInfo,
    DimensionCombinationStats,
    DimensionDiscovery,
    get_statistical_config,
    set_statistical_config,
    reset_statistical_config,
    discover_dimensions,
)

__all__ = [
    # Adaptive time
    "AdaptiveTimeFilter",
    "AdaptiveTimeConfig",
    "AdaptiveTimeResult",
    "VolumeCategory",
    # Process resolver
    "ProcessResolver",
    "PROCESS_ALIASES",
    "normalize_process_name",
    "diagnose_mixed_process_problem",
    # Context
    "AnalysisContext",
    "FilterMemory",
    "ContextConfidence",
    "get_context",
    # Session
    "AnalysisSession",
    "SessionManager",
    "SessionType",
    "TemporalMatrix",
    "DeviationMatrix",
    "DeviationCell",
    "get_session_manager",
    "create_trend_session",
    "create_deviation_session",
    # Computations
    "TrendDirection",
    "Volatility",
    "SignificanceLevel",
    "TrendAnalysis",
    "DeviationAnalysis",
    "calculate_trend",
    "calculate_deviation_significance",
    "rank_deviations",
    "generate_trend_insight",
    "generate_deviation_insight",
    "generate_failure_mode_hypothesis",
    "summarize_for_agent",
    # Statistics
    "AnalysisType",
    "MetricType",
    "SampleSizeThresholds",
    "DeviationThresholds",
    "DimensionCardinalityLimits",
    "StatisticalConfig",
    "DimensionInfo",
    "DimensionCombinationStats",
    "DimensionDiscovery",
    "get_statistical_config",
    "set_statistical_config",
    "reset_statistical_config",
    "discover_dimensions",
]
