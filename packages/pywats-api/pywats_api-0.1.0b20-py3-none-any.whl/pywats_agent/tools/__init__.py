"""
Agent tools for pyWATS.

Smart tools that translate semantic concepts to WATS API calls.

ANALYSIS WORKFLOW:
1. YieldAnalysisTool - Top-level yield by product/process
2. RootCauseAnalysisTool - Top-down, trend-aware failure investigation (9 steps)
3. DimensionalAnalysisTool - Find which factors affect yield (failure modes)
4. StepAnalysisTool - Comprehensive step analysis (Cpk, root cause)
5. ProcessCapabilityTool - Advanced capability analysis (stability, dual Cpk)
6. MeasurementDataTool - Analyze measurement distributions and raw data
7. UnitAnalysisTool - Individual unit status, history, verification, sub-units
8. SubUnitAnalysisTool - Deep sub-unit analysis for large datasets (query headers)
9. ControlPanelTool - Administrative management across all domains

UNIT ANALYSIS WORKFLOW:
┌─────────────────────────────────────────────────────────────────────────────────┐
│ UNIT = Unique combination of Part Number + Serial Number                        │
│ Multiple revisions = same unit (upgraded/reworked)                             │
└─────────────────────────────────────────────────────────────────────────────────┘

Unit Analysis provides:
- Complete test history (all UUT/UUR reports)
- Production tracking (MES phase, batch, location)
- Unit verification/grading (if rules configured)
- Sub-unit (component) tracking
- Status classification (passing/failing/in-progress/repaired/scrapped)

Data Sources:
- Analytics: Serial number history (primary source for test records)
- Production: Unit info, verification rules, phase tracking
- Report: Full test details, sub-unit assembly information

CONTROL PANEL MANAGER:
┌─────────────────────────────────────────────────────────────────────────────────┐
│ Unified administrative tool for managing WATS configuration                      │
│ Single tool handles: Asset, Product, Production, Software, Process              │
└─────────────────────────────────────────────────────────────────────────────────┘

Domains:
- ASSET: Equipment, fixtures, calibration, state management
- PRODUCT: Part numbers, revisions, BOM, box build
- PRODUCTION: Units, phases, assembly relationships
- SOFTWARE: Packages, releases, deployment
- PROCESS: Test/repair/WIP operations (read-only)

Operations:
- Read: list, get, search
- Write: create, update, delete (requires confirmation)
- Domain-specific: set_state, set_phase, add_child, verify, release, revoke

TOP-DOWN ROOT CAUSE ANALYSIS (9-Step Methodology):
┌─────────────────────────────────────────────────────────────────────────────────┐
│ CORE PRINCIPLE: Start at yield level. Test steps are SYMPTOMS.                  │
│ Only dive into step-level analysis when yield deviations justify it.            │
└─────────────────────────────────────────────────────────────────────────────────┘

Step 1: PRODUCT-LEVEL YIELD ASSESSMENT
    - Evaluate overall yield against expected thresholds
    - If yield is healthy → STOP (no problem to investigate)
    - Poor/degrading yield → triggers root cause analysis

Step 2: DIMENSIONAL YIELD SPLITTING
    - Split yield using UUT header dimensions (station, fixture, operator, etc.)
    - Build yield matrix to find statistically significant deviations
    - Identify "suspects" - configurations with lower-than-expected yield

Step 3: TEMPORAL TREND ANALYSIS
    - Include time trends (day-over-day, week-over-week)
    - Classify issues: EMERGING | CHRONIC | RECOVERING | INTERMITTENT
    - Classification impacts prioritization (emerging > chronic)

Step 4: TREND-AWARE SUSPECT PRIORITIZATION
    - Rank by: absolute impact, peer deviation, trend direction, variability
    - Prioritize EMERGING/DEGRADING over stable known problems

Step 5: STEP-LEVEL INVESTIGATION (Only if warranted)
    - Drill into test steps ONLY for high-priority suspects
    - Focus on steps that CAUSE unit failures

Step 6: IDENTIFICATION OF TOP FAILING STEPS
    - Identify steps using failure contribution metrics (step_caused_uut_failed)
    - Only highest-impact steps proceed for detailed analysis

Step 7: TREND-QUALIFIED STEP ANALYSIS
    - Classify step failure patterns: INCREASING | DECREASING | STABLE | VARIABLE
    - Separate regressions from noise using trend analysis

Step 8: CONTEXTUAL ANALYSIS BASED ON SUSPECTS
    - Compare step failure rates: suspect context vs non-suspect context
    - Compare vs historical baseline to confirm causality

Step 9: EXPLAINABLE PRIORITIZED FINDINGS
    - Each finding traces: yield → suspect → step → trend
    - Includes evidence chain, confidence score, recommendations
    - Supports efficient, high-confidence corrective actions

LEGACY ANALYSIS PATH:
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│ Yield       │ --> │ Dimensional  │ --> │ Step        │ --> │ Process      │ --> │ Measurement │
│ Analysis    │     │ Analysis     │     │ Analysis    │     │ Capability   │     │ Deep Dive   │
│             │     │ (optional)   │     │ (TSA)       │     │ Analysis     │     │             │
└─────────────┘     └──────────────┘     └─────────────┘     └──────────────┘     └─────────────┘
     |                    |                    |                    |                    |
"What's failing?"   "Where/when?"      "Which step?"     "Is it stable?"      "Why exactly?"
                                                          "Cpk vs Cpk_wof?"
                                                          "Hidden modes?"

PROCESS CAPABILITY WORKFLOW:
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 1. DATA INTEGRITY CHECK                                                         │
│    - Verify single product/process configuration                                │
│    - Check SW version consistency                                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│ 2. STABILITY ASSESSMENT (MUST DO FIRST!)                                        │
│    - Is process under statistical control?                                      │
│    - Detect trends, shifts, outliers                                           │
│    - If NOT stable → Cpk is meaningless!                                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│ 3. DUAL CpK ANALYSIS                                                            │
│    - Cpk (all): Actual capability including failures                           │
│    - Cpk_wof: Potential without failures                                       │
│    - Compare: Cpk << Cpk_wof means failures hurt capability                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│ 4. HIDDEN MODE DETECTION                                                        │
│    - Outliers beyond 3σ                                                        │
│    - Trends (drift up/down)                                                    │
│    - Approaching specification limits                                          │
│    - Centering issues (Cp >> Cpk)                                              │
│    - Bimodal distributions                                                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│ 5. IMPROVEMENT RECOMMENDATIONS                                                  │
│    - Prioritized: Critical → High → Medium → Low                               │
│    - Specific actions based on findings                                        │
└─────────────────────────────────────────────────────────────────────────────────┘
"""

# =============================================================================
# BACKWARD COMPATIBLE IMPORTS FROM SUBPACKAGES
# =============================================================================
# These imports provide backward compatibility with the old flat structure.
# New code should import directly from the subpackages.
# =============================================================================

# Yield tools (yield_pkg because 'yield' is a Python keyword)
from .yield_pkg import (
    YieldAnalysisTool,
    YieldFilter,
    AnalysisPerspective,
    PERSPECTIVE_ALIASES,
    resolve_perspective,
    get_yield_tool_definition,
    # New specialized tools
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

# Step analysis tools
from .step import (
    TestStepAnalysisTool,
    TestStepAnalysisFilter,
    get_test_step_analysis_tool_definition,
    StepAnalysisTool,
    StepAnalysisInput,
    StepSummary,
    TSAResult,
    OverallProcessSummary,
    DataIntegrityResult,
    CpkStatus,
    CPK_CAPABLE_THRESHOLD,
    CPK_MARGINAL_THRESHOLD,
    CPK_CRITICAL_THRESHOLD,
    get_step_analysis_tool_definition,
)

# Process capability tools
from .capability import (
    ProcessCapabilityTool,
    ProcessCapabilityFilter,
    ProcessCapabilityInput,
    ProcessCapabilityResult,
    MeasurementCapabilityResult,
    DualCpkAnalysis,
    StabilityAnalysis,
    HiddenMode,
    StabilityStatus,
    CapabilityStatus,
    ImprovementPriority,
    HiddenModeType,
    CPK_CAPABLE,
    CPK_MARGINAL,
    CPK_CRITICAL,
    CPK_EXCELLENT,
    get_process_capability_tool_definition,
)

# Measurement tools
from .measurement import (
    AggregatedMeasurementTool,
    MeasurementDataTool,
    MeasurementFilter,
    get_aggregated_measurement_tool_definition,
    get_measurement_data_tool_definition,
)

# Root cause analysis tools
from .root_cause import (
    RootCauseAnalysisTool,
    RootCauseInput,
    RootCauseResult,
    YieldAssessmentResult,
    SuspectFinding,
    TrendAnalysis,
    TrendPattern,
    YieldAssessment,
    InvestigationPriority,
    # Step 6-9 classes
    StepTrendPattern,
    FailingStepFinding,
    TrendQualifiedStep,
    ContextualComparison,
    ExplainableFinding,
    get_root_cause_analysis_tool_definition,
    # Dimensional analysis
    DimensionalAnalysisTool,
    DimensionYieldResult,
    FailureModeResult,
    FailureModeFilter,
    SignificanceLevel,
    STANDARD_DIMENSIONS,
    get_dimensional_analysis_tool_definition,
)

# Legacy aliases for backward compatibility
RootCauseAnalysisFilter = RootCauseInput
RootCauseAnalysisResult = RootCauseResult
DimensionalAnalysisFilter = FailureModeFilter

# Shared utilities
from .shared import (
    AdaptiveTimeFilter,
    AdaptiveTimeConfig,
    AdaptiveTimeResult,
    VolumeCategory,
    ProcessResolver,
    PROCESS_ALIASES,
    diagnose_mixed_process_problem,
    # New context and session infrastructure
    AnalysisContext,
    FilterMemory,
    ContextConfidence,
    get_context,
    AnalysisSession,
    SessionManager,
    SessionType,
    TemporalMatrix,
    DeviationMatrix,
    DeviationCell,
    get_session_manager,
    create_trend_session,
    create_deviation_session,
    # Computation helpers
    TrendDirection,
    Volatility,
    TrendAnalysis as TrendAnalysisResult,  # Renamed to avoid conflict
    calculate_trend,
    calculate_deviation_significance,
    generate_trend_insight,
    generate_deviation_insight,
    summarize_for_agent,
    # Statistical configuration
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

# Asset analysis tools
from .asset import (
    # Tools
    AssetDimensionTool,
    AssetHealthTool,
    AssetDegradationTool,
    # Tool definitions
    get_asset_dimension_tool_definition,
    get_asset_health_tool_definition,
    get_asset_degradation_tool_definition,
    # Enums
    AssetHealthStatus,
    CalibrationStatus,
    AssetImpactLevel,
    DegradationTrend,
    # Filter models
    AssetDimensionFilter,
    AssetHealthFilter,
    AssetDegradationFilter,
    # Result models
    AssetYieldImpact,
    AssetHealthInfo,
    CalibrationCycleMetrics,
    AssetDegradationAnalysis,
    AssetDimensionResult,
    AssetHealthResult,
)

# Unit analysis tools
from .unit import (
    UnitAnalysisTool,
    UnitAnalysisInput,
    UnitInfo,
    UnitStatus,
    TestSummary,
    SubUnitInfo,
)

# Sub-unit analysis tools
from .subunit import (
    SubUnitAnalysisTool,
)

# Control Panel Manager
from .control_panel import (
    ControlPanelTool,
    ControlPanelInput,
    ControlPanelResult,
    ManagementDomain,
    OperationType,
    DOMAIN_ENTITIES,
)

# Base infrastructure (new)
from ._base import (
    ToolInput,
    AgentTool,
    AnalysisTool,
)

# Debug / connectivity tool
from .debug_tool import DebugTool, get_debug_tool_definition
from ._registry import (
    register_tool,
    get_all_tools,
    get_tools_by_category,
    create_tool_instance,
)

# Agent variants and profiles
from .variants import (
    ToolProfile,
    ExperimentalVariant,
    ToolCategory,
    PROFILES,
    TOOL_CATEGORIES,
    get_profile,
    list_profiles,
    create_agent_tools,
    get_tool_definitions,
    register_variant,
    get_variant,
    list_variants,
    print_profiles,
    print_variant_diff,
)

# Load user-defined variants
from . import variant_config  # noqa: F401

__all__ = [
    # Base infrastructure
    "ToolInput",
    "AgentTool",
    "AnalysisTool",
    "register_tool",
    "get_all_tools",
    "get_tools_by_category",
    "create_tool_instance",

    # Debug tool
    "DebugTool",
    "get_debug_tool_definition",
    
    # Yield tools
    "YieldAnalysisTool",
    "YieldFilter",
    "AnalysisPerspective",
    "PERSPECTIVE_ALIASES",
    "resolve_perspective",
    "get_yield_tool_definition",
    # New specialized yield tools
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
    
    # Step analysis
    "StepAnalysisTool",
    "StepAnalysisInput",
    "StepSummary",
    "TSAResult",
    "OverallProcessSummary",
    "DataIntegrityResult",
    "CpkStatus",
    "CPK_CAPABLE_THRESHOLD",
    "CPK_MARGINAL_THRESHOLD",
    "CPK_CRITICAL_THRESHOLD",
    "get_step_analysis_tool_definition",
    "TestStepAnalysisTool",
    "TestStepAnalysisFilter",
    "get_test_step_analysis_tool_definition",
    
    # Process capability
    "ProcessCapabilityTool",
    "ProcessCapabilityFilter",
    "ProcessCapabilityInput",
    "ProcessCapabilityResult",
    "MeasurementCapabilityResult",
    "DualCpkAnalysis",
    "StabilityAnalysis",
    "HiddenMode",
    "StabilityStatus",
    "CapabilityStatus",
    "ImprovementPriority",
    "HiddenModeType",
    "CPK_CAPABLE",
    "CPK_MARGINAL",
    "CPK_CRITICAL",
    "CPK_EXCELLENT",
    "get_process_capability_tool_definition",
    
    # Measurement tools
    "AggregatedMeasurementTool",
    "MeasurementDataTool",
    "MeasurementFilter",
    "get_aggregated_measurement_tool_definition",
    "get_measurement_data_tool_definition",
    
    # Root cause analysis
    "RootCauseAnalysisTool",
    "RootCauseInput",
    "RootCauseAnalysisFilter",
    "RootCauseResult",
    "RootCauseAnalysisResult",
    "YieldAssessmentResult",
    "SuspectFinding",
    "TrendAnalysis",
    "TrendPattern",
    "YieldAssessment",
    "InvestigationPriority",
    "StepTrendPattern",
    "FailingStepFinding",
    "TrendQualifiedStep",
    "ContextualComparison",
    "ExplainableFinding",
    "get_root_cause_analysis_tool_definition",
    
    # Dimensional analysis
    "DimensionalAnalysisTool",
    "DimensionYieldResult",
    "FailureModeResult",
    "FailureModeFilter",
    "DimensionalAnalysisFilter",
    "SignificanceLevel",
    "STANDARD_DIMENSIONS",
    "get_dimensional_analysis_tool_definition",
    
    # Shared utilities
    "AdaptiveTimeFilter",
    "AdaptiveTimeConfig",
    "AdaptiveTimeResult",
    "VolumeCategory",
    "ProcessResolver",
    "PROCESS_ALIASES",
    "diagnose_mixed_process_problem",
    # Context and session infrastructure
    "AnalysisContext",
    "FilterMemory",
    "ContextConfidence",
    "get_context",
    "AnalysisSession",
    "SessionManager",
    "SessionType",
    "TemporalMatrix",
    "DeviationMatrix",
    "DeviationCell",
    "get_session_manager",
    "create_trend_session",
    "create_deviation_session",
    # Computation helpers
    "TrendDirection",
    "Volatility",
    "TrendAnalysisResult",
    "calculate_trend",
    "calculate_deviation_significance",
    "generate_trend_insight",
    "generate_deviation_insight",
    "summarize_for_agent",
    # Statistical configuration
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
    
    # Asset analysis tools
    "AssetDimensionTool",
    "AssetHealthTool",
    "AssetDegradationTool",
    "get_asset_dimension_tool_definition",
    "get_asset_health_tool_definition",
    "get_asset_degradation_tool_definition",
    # Asset enums
    "AssetHealthStatus",
    "CalibrationStatus",
    "AssetImpactLevel",
    "DegradationTrend",
    # Asset filters
    "AssetDimensionFilter",
    "AssetHealthFilter",
    "AssetDegradationFilter",
    # Asset results
    "AssetYieldImpact",
    "AssetHealthInfo",
    "CalibrationCycleMetrics",
    "AssetDegradationAnalysis",
    "AssetDimensionResult",
    "AssetHealthResult",
    
    # Unit analysis tools
    "UnitAnalysisTool",
    "UnitAnalysisInput",
    "UnitInfo",
    "UnitStatus",
    "TestSummary",
    "SubUnitInfo",
    
    # Sub-unit analysis tools
    "SubUnitAnalysisTool",
    
    # Control Panel Manager
    "ControlPanelTool",
    "ControlPanelInput",
    "ControlPanelResult",
    "ManagementDomain",
    "OperationType",
    "DOMAIN_ENTITIES",
    
    # Agent variants and profiles
    "ToolProfile",
    "ExperimentalVariant",
    "ToolCategory",
    "PROFILES",
    "TOOL_CATEGORIES",
    "get_profile",
    "list_profiles",
    "create_agent_tools",
    "get_tool_definitions",
    "register_variant",
    "get_variant",
    "list_variants",
    "print_profiles",
    "print_variant_diff",
]
