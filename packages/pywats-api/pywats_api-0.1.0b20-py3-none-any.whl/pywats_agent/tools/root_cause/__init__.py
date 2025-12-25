"""
Root Cause Analysis subpackage.

Provides tools for identifying failure root causes and performing
multi-dimensional analysis of manufacturing test data.
"""

from .analysis_tool import (
    # Filter
    RootCauseInput,
    
    # Tool
    RootCauseAnalysisTool,
    get_root_cause_analysis_tool_definition,
    
    # Enums
    TrendPattern,
    InvestigationPriority,
    YieldAssessment,
    StepTrendPattern,
    
    # Results
    RootCauseResult,
    TrendAnalysis,
    SuspectFinding,
    FailingStepFinding,
    TrendQualifiedStep,
    ContextualComparison,
    ExplainableFinding,
    YieldAssessmentResult,
)

from .dimensional_tool import (
    # Filter
    FailureModeFilter,
    
    # Tool
    DimensionalAnalysisTool,
    get_dimensional_analysis_tool_definition,
    
    # Enums
    SignificanceLevel,
    
    # Results
    DimensionYieldResult,
    FailureModeResult,
    
    # Constants
    STANDARD_DIMENSIONS,
)

# Aliases for consistency
RootCauseAnalysisFilter = RootCauseInput
RootCauseAnalysisResult = RootCauseResult
DimensionalAnalysisFilter = FailureModeFilter

__all__ = [
    # Filters
    "RootCauseInput",
    "RootCauseAnalysisFilter",
    "FailureModeFilter",
    "DimensionalAnalysisFilter",
    
    # Tools
    "RootCauseAnalysisTool",
    "get_root_cause_analysis_tool_definition",
    "DimensionalAnalysisTool",
    "get_dimensional_analysis_tool_definition",
    
    # Enums
    "TrendPattern",
    "InvestigationPriority",
    "YieldAssessment",
    "StepTrendPattern",
    "SignificanceLevel",
    
    # Results - Root Cause
    "RootCauseResult",
    "RootCauseAnalysisResult",
    "TrendAnalysis",
    "SuspectFinding",
    "FailingStepFinding",
    "TrendQualifiedStep",
    "ContextualComparison",
    "ExplainableFinding",
    "YieldAssessmentResult",
    
    # Results - Dimensional
    "DimensionYieldResult",
    "FailureModeResult",
    
    # Constants
    "STANDARD_DIMENSIONS",
]
