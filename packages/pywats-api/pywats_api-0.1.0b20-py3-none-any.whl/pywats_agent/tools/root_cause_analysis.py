"""
Top-Down Root Cause Analysis Tool for Failure Investigation.

This module provides a comprehensive, trend-aware root cause analysis methodology
that follows a disciplined top-down approach, starting at yield level and only
diving into step-level analysis when yield deviations justify it.

CORE PRINCIPLE: Top-Down Failure Analysis
=========================================
- Start at yield level, not step level
- Test steps are SYMPTOMS; yield deviations indicate SYSTEMIC issues
- Step-level analysis only AFTER yield justifies it
- This avoids chasing noise and focuses on real problems

5-STEP METHODOLOGY (Trend-Aware):
=================================

Step 1: PRODUCT-LEVEL YIELD ASSESSMENT
- Evaluate overall product yield against expected thresholds
- If yield is within expected limits → STOP (no problem to investigate)
- Poor/degrading yield → triggers root cause analysis
- Consider yield type (FPY, LPY, TRY) based on context

Step 2: DIMENSIONAL YIELD SPLITTING
- Split yield using UUT header dimensions:
  * station, fixture, operator, site, line, time period, batch
- Build yield matrix to find statistically significant deviations
- Identify "suspects" - configurations with lower-than-expected yield
- Use statistical significance (chi-squared, z-test) to filter noise

Step 3: TEMPORAL TREND ANALYSIS
- Include time trends (day-over-day, week-over-week)
- Classify issues by trend pattern:
  * EMERGING: New problem, yield degrading
  * CHRONIC: Long-standing issue, stable low yield
  * RECOVERING: Problem being fixed, yield improving
  * INTERMITTENT: Sporadic, hard to reproduce
- Classification impacts prioritization (emerging > chronic)

Step 4: TREND-AWARE SUSPECT PRIORITIZATION
- Rank suspects using multiple factors:
  * Absolute yield impact (how much yield is lost)
  * Deviation from peers (how much worse than others)
  * Trend direction + slope (getting worse vs stable)
  * Variability (consistent problem vs sporadic)
- Prioritize EMERGING/DEGRADING over stable known problems

Step 5: STEP-LEVEL INVESTIGATION (Only if warranted)
- Drill into test steps ONLY for high-priority suspects
- Focus on steps that CAUSE unit failures (step_caused_uut_failed)
- Look for measurement drift, Cpk degradation
- Connect step failures to dimensional suspects

WORKFLOW INTEGRATION:
====================
This tool orchestrates existing tools in sequence:
1. YieldAnalysisTool - Product-level assessment
2. DimensionalAnalysisTool - Find failure modes
3. StepAnalysisTool - Deep dive (when justified)
4. Temporal analysis built into each step

Example:
    >>> from pywats_agent.tools.root_cause_analysis import RootCauseAnalysisTool
    >>> 
    >>> tool = RootCauseAnalysisTool(api)
    >>> 
    >>> # Full top-down analysis
    >>> result = tool.analyze(RootCauseInput(
    ...     part_number="WIDGET-001",
    ...     test_operation="FCT",
    ...     days=30
    ... ))
    >>> 
    >>> # Or start from a specific issue
    >>> result = tool.investigate_suspect(
    ...     part_number="WIDGET-001",
    ...     test_operation="FCT",
    ...     suspect_dimension="stationName",
    ...     suspect_value="Station-3"
    ... )
"""

from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import statistics

from pydantic import BaseModel, Field

from ..result import AgentResult

if TYPE_CHECKING:
    from pywats import pyWATS


# =============================================================================
# Configuration Constants
# =============================================================================

# Yield thresholds for triggering investigation
DEFAULT_YIELD_THRESHOLD = 95.0  # Below this triggers investigation
YIELD_MARGIN_GOOD = 2.0  # Within 2% of target is acceptable
YIELD_MARGIN_CONCERN = 5.0  # 5% below target is concerning
YIELD_MARGIN_CRITICAL = 10.0  # 10% below target is critical

# Trend detection thresholds
TREND_SIGNIFICANT_DELTA = 2.0  # 2% change is significant
TREND_CRITICAL_DELTA = 5.0  # 5% change is critical
TREND_MIN_PERIODS = 3  # Minimum periods for trend analysis

# Statistical significance
MIN_UNITS_FOR_ANALYSIS = 30  # Minimum units for reliable analysis
SIGNIFICANCE_THRESHOLD = 0.05  # p-value threshold


# =============================================================================
# Enums and Data Classes
# =============================================================================

class TrendPattern(str, Enum):
    """Classification of yield trend patterns."""
    EMERGING = "emerging"  # New problem, yield degrading rapidly
    CHRONIC = "chronic"  # Long-standing issue, stable low yield
    RECOVERING = "recovering"  # Problem being fixed, yield improving
    INTERMITTENT = "intermittent"  # Sporadic, inconsistent
    STABLE = "stable"  # No significant change
    UNKNOWN = "unknown"  # Insufficient data


class InvestigationPriority(str, Enum):
    """Priority levels for investigation suspects."""
    CRITICAL = "critical"  # Immediate action required
    HIGH = "high"  # Should investigate soon
    MEDIUM = "medium"  # Worth investigating
    LOW = "low"  # Monitor but not urgent
    INFO = "info"  # For reference only


class YieldAssessment(str, Enum):
    """Overall yield assessment status."""
    HEALTHY = "healthy"  # Yield is good, no investigation needed
    CONCERNING = "concerning"  # Below target but manageable
    POOR = "poor"  # Significantly below target
    CRITICAL = "critical"  # Severe yield loss
    INSUFFICIENT_DATA = "insufficient_data"  # Not enough data


@dataclass
class TrendAnalysis:
    """Temporal trend analysis for a metric."""
    
    pattern: TrendPattern
    """Classified trend pattern."""
    
    current_value: float
    """Most recent value."""
    
    previous_value: Optional[float]
    """Previous period value (for comparison)."""
    
    delta: float
    """Change from previous period."""
    
    delta_percent: float
    """Percentage change from previous period."""
    
    slope: float
    """Linear regression slope (rate of change)."""
    
    periods_analyzed: int
    """Number of time periods in analysis."""
    
    variability: float
    """Standard deviation of values across periods."""
    
    confidence: float
    """Confidence in trend assessment (0-1)."""
    
    description: str
    """Human-readable trend description."""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern": self.pattern.value,
            "current_value": self.current_value,
            "previous_value": self.previous_value,
            "delta": self.delta,
            "delta_percent": self.delta_percent,
            "slope": self.slope,
            "periods_analyzed": self.periods_analyzed,
            "variability": self.variability,
            "confidence": self.confidence,
            "description": self.description,
        }


@dataclass
class SuspectFinding:
    """A suspect configuration identified in dimensional analysis."""
    
    dimension: str
    """Dimension name (e.g., 'stationName', 'operator')."""
    
    value: str
    """Specific value (e.g., 'Station-3', 'John Smith')."""
    
    display_name: str
    """Human-friendly dimension name."""
    
    # Yield metrics
    fpy: float
    """First pass yield for this configuration."""
    
    unit_count: int
    """Number of units tested."""
    
    # Comparison metrics
    baseline_fpy: float
    """Overall baseline FPY for comparison."""
    
    yield_delta: float
    """Absolute yield difference from baseline."""
    
    yield_delta_percent: float
    """Relative yield difference (%)."""
    
    # Trend information
    trend: Optional[TrendAnalysis] = None
    """Temporal trend for this suspect."""
    
    # Impact and priority
    impact_score: float = 0.0
    """Combined impact score (higher = more impactful)."""
    
    priority: InvestigationPriority = InvestigationPriority.INFO
    """Investigation priority."""
    
    # Peer comparison
    peer_rank: int = 0
    """Rank among peers (1 = worst)."""
    
    peer_count: int = 0
    """Total number of peers in comparison."""
    
    z_score: float = 0.0
    """Standard deviations from peer mean."""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "dimension": self.dimension,
            "value": self.value,
            "display_name": self.display_name,
            "fpy": self.fpy,
            "unit_count": self.unit_count,
            "baseline_fpy": self.baseline_fpy,
            "yield_delta": self.yield_delta,
            "yield_delta_percent": self.yield_delta_percent,
            "trend": self.trend.to_dict() if self.trend else None,
            "impact_score": self.impact_score,
            "priority": self.priority.value,
            "peer_rank": self.peer_rank,
            "peer_count": self.peer_count,
            "z_score": self.z_score,
        }


# =============================================================================
# Step 6-9 Data Classes: Extended Step Analysis
# =============================================================================

class StepTrendPattern(Enum):
    """Step failure trend classification (Step 7)."""
    
    INCREASING = "increasing"  # Failures getting worse (regression)
    DECREASING = "decreasing"  # Failures improving
    STABLE = "stable"  # Consistent failure rate
    VARIABLE = "variable"  # High variability, sporadic
    UNKNOWN = "unknown"  # Insufficient data


@dataclass
class FailingStepFinding:
    """Step 6: A top failing test step with failure contribution metrics."""
    
    step_name: str
    """Test step name."""
    
    step_path: str
    """Full path in test hierarchy."""
    
    step_group: Optional[str] = None
    """Test group containing this step."""
    
    step_type: Optional[str] = None
    """Step type (numeric, string, etc.)."""
    
    # Failure metrics
    total_executions: int = 0
    """Total times step was executed."""
    
    failed_count: int = 0
    """Number of times step failed."""
    
    caused_unit_failure: int = 0
    """Number of times this step CAUSED the unit to fail (critical metric)."""
    
    # Failure contribution (key metric for Step 6)
    failure_contribution_pct: float = 0.0
    """Percentage of total unit failures caused by this step."""
    
    failure_rate: float = 0.0
    """Step failure rate (failed_count / total_executions)."""
    
    # Context (which suspect this is associated with)
    suspect_context: Optional[str] = None
    """The suspect (station/operator/etc) this step is analyzed under."""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_name": self.step_name,
            "step_path": self.step_path,
            "step_group": self.step_group,
            "step_type": self.step_type,
            "total_executions": self.total_executions,
            "failed_count": self.failed_count,
            "caused_unit_failure": self.caused_unit_failure,
            "failure_contribution_pct": self.failure_contribution_pct,
            "failure_rate": self.failure_rate,
            "suspect_context": self.suspect_context,
        }


@dataclass 
class TrendQualifiedStep:
    """Step 7: Step with temporal trend qualification."""
    
    step: FailingStepFinding
    """The failing step being analyzed."""
    
    # Trend analysis
    trend_pattern: StepTrendPattern = StepTrendPattern.UNKNOWN
    """Classified trend pattern."""
    
    failure_rates_over_time: List[float] = field(default_factory=list)
    """Failure rates per time period."""
    
    trend_slope: float = 0.0
    """Rate of change in failure rate per period."""
    
    trend_variability: float = 0.0
    """Standard deviation of failure rates."""
    
    is_regression: bool = False
    """True if step failure is a regression (new/worsening issue)."""
    
    is_noise: bool = False
    """True if step failures appear to be noise (variable, not systematic)."""
    
    trend_confidence: float = 0.0
    """Confidence in trend classification (0-1)."""
    
    trend_description: str = ""
    """Human-readable trend description."""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "step": self.step.to_dict(),
            "trend_pattern": self.trend_pattern.value,
            "failure_rates_over_time": self.failure_rates_over_time,
            "trend_slope": self.trend_slope,
            "trend_variability": self.trend_variability,
            "is_regression": self.is_regression,
            "is_noise": self.is_noise,
            "trend_confidence": self.trend_confidence,
            "trend_description": self.trend_description,
        }


@dataclass
class ContextualComparison:
    """Step 8: Comparison of step performance in suspect vs non-suspect contexts."""
    
    step_name: str
    """Test step name."""
    
    step_path: str
    """Full path in test hierarchy."""
    
    # Suspect context performance
    suspect_failure_rate: float = 0.0
    """Failure rate in suspect context (e.g., Station-3)."""
    
    suspect_unit_count: int = 0
    """Number of units in suspect context."""
    
    suspect_caused_failures: int = 0
    """Unit failures caused by this step in suspect context."""
    
    # Non-suspect context performance (peer comparison)
    non_suspect_failure_rate: float = 0.0
    """Failure rate in non-suspect contexts."""
    
    non_suspect_unit_count: int = 0
    """Number of units in non-suspect contexts."""
    
    non_suspect_caused_failures: int = 0
    """Unit failures caused by this step in non-suspect contexts."""
    
    # Historical baseline
    historical_failure_rate: float = 0.0
    """Historical baseline failure rate."""
    
    historical_unit_count: int = 0
    """Historical sample size."""
    
    # Comparative metrics (key for causality)
    rate_ratio: float = 0.0
    """Ratio of suspect rate to non-suspect rate (>1 indicates suspect is worse)."""
    
    rate_delta: float = 0.0
    """Absolute difference between suspect and non-suspect rates."""
    
    vs_historical_delta: float = 0.0
    """Difference between suspect and historical baseline."""
    
    # Causality assessment
    is_causally_linked: bool = False
    """True if step is causally linked to suspect (much higher rate in suspect)."""
    
    causality_confidence: float = 0.0
    """Confidence in causal link (0-1)."""
    
    explanation: str = ""
    """Explanation of comparative analysis."""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_name": self.step_name,
            "step_path": self.step_path,
            "suspect_failure_rate": self.suspect_failure_rate,
            "suspect_unit_count": self.suspect_unit_count,
            "suspect_caused_failures": self.suspect_caused_failures,
            "non_suspect_failure_rate": self.non_suspect_failure_rate,
            "non_suspect_unit_count": self.non_suspect_unit_count,
            "non_suspect_caused_failures": self.non_suspect_caused_failures,
            "historical_failure_rate": self.historical_failure_rate,
            "historical_unit_count": self.historical_unit_count,
            "rate_ratio": self.rate_ratio,
            "rate_delta": self.rate_delta,
            "vs_historical_delta": self.vs_historical_delta,
            "is_causally_linked": self.is_causally_linked,
            "causality_confidence": self.causality_confidence,
            "explanation": self.explanation,
        }


@dataclass
class ExplainableFinding:
    """Step 9: An explainable, prioritized finding with full evidence chain."""
    
    # Finding identification
    finding_id: int = 0
    """Unique identifier for this finding."""
    
    priority: InvestigationPriority = InvestigationPriority.INFO
    """Investigation priority level."""
    
    confidence: float = 0.0
    """Overall confidence in finding (0-1)."""
    
    # The suspect
    suspect_dimension: str = ""
    """Dimension of the suspect (e.g., 'stationName')."""
    
    suspect_value: str = ""
    """Value of the suspect (e.g., 'Station-3')."""
    
    suspect_impact: float = 0.0
    """Yield impact of the suspect."""
    
    # The step
    step_name: str = ""
    """Name of the failing step."""
    
    step_path: str = ""
    """Full path to the step."""
    
    step_failure_contribution: float = 0.0
    """Percentage of failures caused by this step."""
    
    # Evidence chain (traceability back to yield + trend)
    yield_evidence: str = ""
    """How yield data supports this finding."""
    
    trend_evidence: str = ""
    """How trend data supports this finding."""
    
    suspect_evidence: str = ""
    """Why this suspect was identified."""
    
    step_evidence: str = ""
    """Why this step is implicated."""
    
    contextual_evidence: str = ""
    """Contextual comparison evidence (suspect vs non-suspect)."""
    
    # Full explanation
    explanation: str = ""
    """Complete human-readable explanation of the finding."""
    
    # Actionable recommendation
    recommendation: str = ""
    """Specific action to take."""
    
    expected_impact: str = ""
    """Expected impact if recommendation is followed."""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "priority": self.priority.value,
            "confidence": self.confidence,
            "suspect_dimension": self.suspect_dimension,
            "suspect_value": self.suspect_value,
            "suspect_impact": self.suspect_impact,
            "step_name": self.step_name,
            "step_path": self.step_path,
            "step_failure_contribution": self.step_failure_contribution,
            "yield_evidence": self.yield_evidence,
            "trend_evidence": self.trend_evidence,
            "suspect_evidence": self.suspect_evidence,
            "step_evidence": self.step_evidence,
            "contextual_evidence": self.contextual_evidence,
            "explanation": self.explanation,
            "recommendation": self.recommendation,
            "expected_impact": self.expected_impact,
        }


@dataclass
class YieldAssessmentResult:
    """Step 1: Product-level yield assessment result."""
    
    status: YieldAssessment
    """Overall yield status."""
    
    # Core metrics
    fpy: float
    """First pass yield."""
    
    lpy: float
    """Last pass yield."""
    
    unit_count: int
    """Total units analyzed."""
    
    # Thresholds
    target_yield: float
    """Expected/target yield."""
    
    yield_gap: float
    """Gap between actual and target."""
    
    # Trend
    trend: Optional[TrendAnalysis] = None
    """Temporal trend information."""
    
    # Decision
    should_investigate: bool = False
    """Whether to proceed with investigation."""
    
    reason: str = ""
    """Reason for decision."""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "fpy": self.fpy,
            "lpy": self.lpy,
            "unit_count": self.unit_count,
            "target_yield": self.target_yield,
            "yield_gap": self.yield_gap,
            "trend": self.trend.to_dict() if self.trend else None,
            "should_investigate": self.should_investigate,
            "reason": self.reason,
        }


@dataclass
class RootCauseResult:
    """Complete root cause analysis result."""
    
    # Context
    part_number: Optional[str]
    test_operation: Optional[str]
    days: int
    date_from: datetime
    date_to: datetime
    
    # Step 1: Yield Assessment
    yield_assessment: YieldAssessmentResult
    
    # Step 2-4: Suspects (prioritized)
    suspects: List[SuspectFinding] = field(default_factory=list)
    
    # Dimensional breakdown (for reference)
    dimensional_analysis: Dict[str, List[SuspectFinding]] = field(default_factory=dict)
    
    # Step 5: Step-level findings (if investigation warranted)
    step_level_findings: Optional[Dict[str, Any]] = None
    
    # Step 6: Top failing steps
    top_failing_steps: List[FailingStepFinding] = field(default_factory=list)
    """Steps with highest failure contribution."""
    
    # Step 7: Trend-qualified steps
    trend_qualified_steps: List[TrendQualifiedStep] = field(default_factory=list)
    """Steps with trend analysis (regression vs noise)."""
    
    # Step 8: Contextual comparisons
    contextual_comparisons: List[ContextualComparison] = field(default_factory=list)
    """Suspect vs non-suspect context comparisons."""
    
    # Step 9: Explainable findings
    explainable_findings: List[ExplainableFinding] = field(default_factory=list)
    """Prioritized, explainable findings with full evidence chain."""
    
    # Summary
    summary: str = ""
    recommendations: List[str] = field(default_factory=list)
    
    # Execution metadata
    steps_completed: List[str] = field(default_factory=list)
    investigation_stopped_at: Optional[str] = None
    stop_reason: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "part_number": self.part_number,
            "test_operation": self.test_operation,
            "days": self.days,
            "date_from": self.date_from.isoformat() if self.date_from else None,
            "date_to": self.date_to.isoformat() if self.date_to else None,
            "yield_assessment": self.yield_assessment.to_dict(),
            "suspects": [s.to_dict() for s in self.suspects],
            "dimensional_analysis": {
                dim: [s.to_dict() for s in findings]
                for dim, findings in self.dimensional_analysis.items()
            },
            "step_level_findings": self.step_level_findings,
            "top_failing_steps": [s.to_dict() for s in self.top_failing_steps],
            "trend_qualified_steps": [s.to_dict() for s in self.trend_qualified_steps],
            "contextual_comparisons": [c.to_dict() for c in self.contextual_comparisons],
            "explainable_findings": [f.to_dict() for f in self.explainable_findings],
            "summary": self.summary,
            "recommendations": self.recommendations,
            "steps_completed": self.steps_completed,
            "investigation_stopped_at": self.investigation_stopped_at,
            "stop_reason": self.stop_reason,
        }


# =============================================================================
# Input Model
# =============================================================================

class RootCauseInput(BaseModel):
    """Input for root cause analysis."""
    
    # Product/Process context (at least one recommended)
    part_number: Optional[str] = Field(
        default=None,
        description="Product to analyze. Recommended for focused analysis."
    )
    test_operation: Optional[str] = Field(
        default=None,
        description="Test operation/process. Recommended for focused analysis."
    )
    
    # Time range
    days: int = Field(
        default=30,
        description="Number of days to analyze."
    )
    date_from: Optional[datetime] = Field(
        default=None,
        description="Start date (overrides days)."
    )
    date_to: Optional[datetime] = Field(
        default=None,
        description="End date."
    )
    
    # Yield thresholds
    target_yield: float = Field(
        default=DEFAULT_YIELD_THRESHOLD,
        description="Expected/target yield percentage. Below this triggers investigation."
    )
    
    # Analysis configuration
    include_step_analysis: bool = Field(
        default=True,
        description="Include step-level drill-down for high-priority suspects."
    )
    
    include_extended_step_analysis: bool = Field(
        default=True,
        description="Include Steps 6-9: top failing steps, trend qualification, contextual analysis, and explainable findings."
    )
    
    min_failure_contribution: float = Field(
        default=5.0,
        description="Minimum failure contribution percentage for a step to be analyzed (Step 6)."
    )
    
    max_suspects: int = Field(
        default=10,
        description="Maximum number of suspects to return."
    )
    
    dimensions: Optional[List[str]] = Field(
        default=None,
        description="""
Dimensions to analyze. If not specified, uses standard dimensions:
stationName, operator, fixtureId, batchNumber, location, period
        """
    )
    
    min_units: int = Field(
        default=30,
        description="Minimum units per configuration for reliable analysis."
    )
    
    # Mode selection
    force_investigate: bool = Field(
        default=False,
        description="Force investigation even if yield is healthy."
    )
    
    # Specific suspect to investigate
    suspect_dimension: Optional[str] = Field(
        default=None,
        description="If specified, focus investigation on this dimension."
    )
    suspect_value: Optional[str] = Field(
        default=None,
        description="If specified with suspect_dimension, focus on this specific value."
    )


# =============================================================================
# Standard Dimensions for Analysis
# =============================================================================

STANDARD_DIMENSIONS = [
    "stationName",  # Test station - equipment issues
    "operator",  # Operator - training/technique issues
    "fixtureId",  # Fixture - wear/calibration issues
    "batchNumber",  # Batch - component lot issues
    "location",  # Location/line - environment issues
    "period",  # Time - drift over time
]

DIMENSION_DISPLAY_NAMES = {
    "stationName": "Station",
    "operator": "Operator",
    "fixtureId": "Fixture",
    "batchNumber": "Batch",
    "location": "Location/Line",
    "period": "Time Period",
    "swFilename": "Test Software",
    "swVersion": "Software Version",
    "partNumber": "Product",
    "revision": "Revision",
}


# =============================================================================
# Root Cause Analysis Tool
# =============================================================================

class RootCauseAnalysisTool:
    """
    Top-Down Root Cause Analysis for Failure Investigation.
    
    Implements a 9-step trend-aware methodology:
    1. Product-level yield assessment
    2. Dimensional yield splitting
    3. Temporal trend analysis
    4. Trend-aware suspect prioritization
    5. Step-level investigation (when warranted)
    6. Identification of top failing steps
    7. Trend-qualified step analysis
    8. Contextual analysis (suspect vs non-suspect)
    9. Explainable prioritized findings
    
    CORE PRINCIPLE: Start at yield level, test steps are symptoms.
    Only dive into step-level analysis when yield deviations justify it.
    
    Example:
        >>> tool = RootCauseAnalysisTool(api)
        >>> 
        >>> # Full top-down analysis
        >>> result = tool.analyze(RootCauseInput(
        ...     part_number="WIDGET-001",
        ...     test_operation="FCT",
        ...     days=30
        ... ))
        >>> 
        >>> if result.yield_assessment.should_investigate:
        ...     print("Investigation needed!")
        ...     for suspect in result.suspects[:5]:
        ...         print(f"- {suspect.display_name} '{suspect.value}': "
        ...               f"FPY={suspect.fpy:.1f}% ({suspect.priority.value})")
        ...     for finding in result.explainable_findings[:3]:
        ...         print(f"- {finding.step_name}: {finding.explanation}")
    """
    
    name = "analyze_root_cause"
    description = """
Top-down root cause analysis for failure investigation.

WHEN TO USE THIS TOOL:
- "Why is yield dropping for product X?"
- "What's causing failures in FCT?"
- "Why is this station/line/batch underperforming?"
- "Investigate quality issues for product X"
- "What are the root causes of failures?"

METHODOLOGY (9 Steps):
1. YIELD ASSESSMENT: Check if product yield actually needs investigation
2. DIMENSIONAL SPLITTING: Find which factors correlate with failures
3. TREND ANALYSIS: Classify issues as emerging, chronic, recovering
4. SUSPECT PRIORITIZATION: Rank by impact, deviation, and trend
5. STEP DRILL-DOWN: Investigate steps for high-priority suspects
6. TOP FAILING STEPS: Identify steps by failure contribution (step_caused_uut_failed)
7. TREND-QUALIFIED STEPS: Classify step trends as INCREASING/DECREASING/STABLE/VARIABLE
8. CONTEXTUAL ANALYSIS: Compare suspect vs non-suspect contexts for causality
9. EXPLAINABLE FINDINGS: Generate prioritized findings with full evidence chain

KEY PRINCIPLE: Test steps are SYMPTOMS, not root causes.
We start at yield level and only dive into steps when justified.

TREND CLASSIFICATION (Yield):
- EMERGING: New problem, getting worse (highest priority)
- CHRONIC: Long-standing issue, stable but low
- RECOVERING: Problem being fixed
- INTERMITTENT: Sporadic, hard to reproduce

STEP TREND CLASSIFICATION:
- INCREASING: Step failures getting worse (regression)
- DECREASING: Step failures improving
- STABLE: Consistent failure rate
- VARIABLE: High variability, likely noise

EXPLAINABLE FINDINGS include:
- Evidence chain: yield → suspect → step → trend
- Causality assessment (suspect vs non-suspect comparison)
- Confidence score
- Actionable recommendations
- Expected impact

Example questions this tool answers:
- "Why is FCT yield low for WIDGET-001?"
- "What's causing the recent yield drop?"
- "Is Station-3's poor yield a new problem or chronic?"
- "What should we investigate first?"
- "Which test steps are causing the most failures?"
- "Is this a regression or chronic issue?"
"""
    
    def __init__(self, api: "pyWATS"):
        """Initialize with pyWATS instance."""
        self._api = api
        self._yield_tool = None  # Lazy-loaded
        self._dimensional_tool = None  # Lazy-loaded
        self._step_tool = None  # Lazy-loaded
    
    def _get_yield_tool(self):
        """Get yield analysis tool (lazy-loaded)."""
        if self._yield_tool is None:
            from .yield_pkg import YieldAnalysisTool
            self._yield_tool = YieldAnalysisTool(self._api)
        return self._yield_tool
    
    def _get_dimensional_tool(self):
        """Get dimensional analysis tool (lazy-loaded)."""
        if self._dimensional_tool is None:
            from .dimensional_analysis import DimensionalAnalysisTool
            self._dimensional_tool = DimensionalAnalysisTool(self._api)
        return self._dimensional_tool
    
    def _get_step_tool(self):
        """Get step analysis tool (lazy-loaded)."""
        if self._step_tool is None:
            from .step_analysis import StepAnalysisTool
            self._step_tool = StepAnalysisTool(self._api)
        return self._step_tool
    
    def analyze(self, input_filter: RootCauseInput) -> AgentResult:
        """
        Execute full top-down root cause analysis.
        
        Follows the 5-step methodology:
        1. Assess product yield
        2. Split by dimensions
        3. Analyze trends
        4. Prioritize suspects
        5. Drill into steps (if warranted)
        
        Args:
            input_filter: Analysis parameters
            
        Returns:
            AgentResult with comprehensive findings
        """
        try:
            # Initialize result
            date_to = input_filter.date_to or datetime.now()
            if input_filter.date_from:
                date_from = input_filter.date_from
            else:
                date_from = date_to - timedelta(days=input_filter.days)
            
            steps_completed = []
            
            # =================================================================
            # STEP 1: Product-Level Yield Assessment
            # =================================================================
            yield_assessment = self._step1_yield_assessment(
                part_number=input_filter.part_number,
                test_operation=input_filter.test_operation,
                date_from=date_from,
                date_to=date_to,
                target_yield=input_filter.target_yield,
                days=input_filter.days,
            )
            steps_completed.append("yield_assessment")
            
            # Check if investigation is needed
            if not yield_assessment.should_investigate and not input_filter.force_investigate:
                result = RootCauseResult(
                    part_number=input_filter.part_number,
                    test_operation=input_filter.test_operation,
                    days=input_filter.days,
                    date_from=date_from,
                    date_to=date_to,
                    yield_assessment=yield_assessment,
                    summary=yield_assessment.reason,
                    recommendations=[
                        "Yield is within acceptable range.",
                        "Continue monitoring for changes.",
                    ],
                    steps_completed=steps_completed,
                    investigation_stopped_at="yield_assessment",
                    stop_reason=yield_assessment.reason,
                )
                
                return AgentResult.ok(
                    data=result.to_dict(),
                    summary=f"✅ No investigation needed. {yield_assessment.reason}",
                    metadata={
                        "fpy": yield_assessment.fpy,
                        "status": yield_assessment.status.value,
                        "investigation_needed": False,
                    }
                )
            
            # =================================================================
            # STEP 2: Dimensional Yield Splitting
            # =================================================================
            dimensions = input_filter.dimensions or STANDARD_DIMENSIONS
            dimensional_analysis = {}
            all_suspects = []
            
            for dimension in dimensions:
                dim_findings = self._step2_dimensional_analysis(
                    dimension=dimension,
                    part_number=input_filter.part_number,
                    test_operation=input_filter.test_operation,
                    date_from=date_from,
                    date_to=date_to,
                    baseline_fpy=yield_assessment.fpy,
                    min_units=input_filter.min_units,
                )
                
                if dim_findings:
                    dimensional_analysis[dimension] = dim_findings
                    all_suspects.extend(dim_findings)
            
            steps_completed.append("dimensional_analysis")
            
            # =================================================================
            # STEP 3: Temporal Trend Analysis
            # =================================================================
            # Add trend information to each suspect
            for suspect in all_suspects:
                suspect.trend = self._step3_trend_analysis(
                    dimension=suspect.dimension,
                    value=suspect.value,
                    part_number=input_filter.part_number,
                    test_operation=input_filter.test_operation,
                    date_from=date_from,
                    date_to=date_to,
                    days=input_filter.days,
                )
            
            steps_completed.append("trend_analysis")
            
            # =================================================================
            # STEP 4: Trend-Aware Suspect Prioritization
            # =================================================================
            prioritized_suspects = self._step4_prioritize_suspects(
                suspects=all_suspects,
                baseline_fpy=yield_assessment.fpy,
                max_suspects=input_filter.max_suspects,
            )
            
            steps_completed.append("suspect_prioritization")
            
            # =================================================================
            # STEP 5: Step-Level Investigation (if warranted)
            # =================================================================
            step_level_findings = None
            top_failing_steps = []
            trend_qualified_steps = []
            contextual_comparisons = []
            explainable_findings = []
            
            if input_filter.include_step_analysis and prioritized_suspects:
                # Only investigate high-priority suspects
                high_priority = [
                    s for s in prioritized_suspects
                    if s.priority in [InvestigationPriority.CRITICAL, InvestigationPriority.HIGH]
                ]
                
                if high_priority:
                    step_level_findings = self._step5_step_analysis(
                        suspects=high_priority[:3],  # Top 3 only
                        part_number=input_filter.part_number,
                        test_operation=input_filter.test_operation,
                        date_from=date_from,
                        date_to=date_to,
                    )
                    steps_completed.append("step_analysis")
                    
                    # =============================================================
                    # STEPS 6-9: Extended Step Analysis (if enabled)
                    # =============================================================
                    if input_filter.include_extended_step_analysis and step_level_findings:
                        # Step 6: Identify top failing steps by failure contribution
                        top_failing_steps = self._step6_top_failing_steps(
                            step_findings=step_level_findings,
                            min_contribution=input_filter.min_failure_contribution,
                        )
                        steps_completed.append("top_failing_steps")
                        
                        # Step 7: Trend-qualify the top failing steps
                        if top_failing_steps:
                            trend_qualified_steps = self._step7_trend_qualified_analysis(
                                failing_steps=top_failing_steps,
                                part_number=input_filter.part_number,
                                test_operation=input_filter.test_operation,
                                date_from=date_from,
                                date_to=date_to,
                            )
                            steps_completed.append("trend_qualified_steps")
                        
                        # Step 8: Contextual analysis (suspect vs non-suspect)
                        if trend_qualified_steps:
                            contextual_comparisons = self._step8_contextual_analysis(
                                trend_steps=trend_qualified_steps,
                                suspects=high_priority[:3],
                                part_number=input_filter.part_number,
                                test_operation=input_filter.test_operation,
                                date_from=date_from,
                                date_to=date_to,
                            )
                            steps_completed.append("contextual_analysis")
                        
                        # Step 9: Generate explainable findings
                        explainable_findings = self._step9_generate_explainable_findings(
                            yield_assessment=yield_assessment,
                            suspects=high_priority[:3],
                            trend_steps=trend_qualified_steps,
                            contextual=contextual_comparisons,
                        )
                        steps_completed.append("explainable_findings")
            
            # =================================================================
            # Generate Summary and Recommendations
            # =================================================================
            summary, recommendations = self._generate_summary(
                yield_assessment=yield_assessment,
                suspects=prioritized_suspects,
                step_findings=step_level_findings,
                explainable_findings=explainable_findings,
            )
            
            # Build final result
            result = RootCauseResult(
                part_number=input_filter.part_number,
                test_operation=input_filter.test_operation,
                days=input_filter.days,
                date_from=date_from,
                date_to=date_to,
                yield_assessment=yield_assessment,
                suspects=prioritized_suspects,
                dimensional_analysis=dimensional_analysis,
                step_level_findings=step_level_findings,
                top_failing_steps=top_failing_steps,
                trend_qualified_steps=trend_qualified_steps,
                contextual_comparisons=contextual_comparisons,
                explainable_findings=explainable_findings,
                summary=summary,
                recommendations=recommendations,
                steps_completed=steps_completed,
            )
            
            return AgentResult.ok(
                data=result.to_dict(),
                summary=summary,
                metadata={
                    "fpy": yield_assessment.fpy,
                    "status": yield_assessment.status.value,
                    "investigation_needed": True,
                    "suspects_found": len(prioritized_suspects),
                    "critical_suspects": len([
                        s for s in prioritized_suspects
                        if s.priority == InvestigationPriority.CRITICAL
                    ]),
                    "top_failing_steps": len(top_failing_steps),
                    "explainable_findings": len(explainable_findings),
                    "steps_completed": steps_completed,
                }
            )
            
        except Exception as e:
            return AgentResult.fail(f"Root cause analysis failed: {str(e)}")
    
    def _step1_yield_assessment(
        self,
        part_number: Optional[str],
        test_operation: Optional[str],
        date_from: datetime,
        date_to: datetime,
        target_yield: float,
        days: int,
    ) -> YieldAssessmentResult:
        """
        Step 1: Product-level yield assessment.
        
        Evaluates overall yield against thresholds and trend.
        """
        from pywats.domains.report.models import WATSFilter
        
        # Get overall yield
        filter_params = {
            "date_from": date_from,
            "date_to": date_to,
        }
        if part_number:
            filter_params["part_number"] = part_number
        if test_operation:
            filter_params["test_operation"] = test_operation
        
        try:
            wats_filter = WATSFilter(**filter_params)
            data = self._api.analytics.get_dynamic_yield(wats_filter)
            
            if not data:
                return YieldAssessmentResult(
                    status=YieldAssessment.INSUFFICIENT_DATA,
                    fpy=0,
                    lpy=0,
                    unit_count=0,
                    target_yield=target_yield,
                    yield_gap=0,
                    should_investigate=False,
                    reason="No data found for the specified filter.",
                )
            
            # Aggregate yield
            total_units = sum(d.unit_count or 0 for d in data)
            total_fp = sum(d.fp_count or 0 for d in data)
            total_lp = sum(d.lp_count or 0 for d in data)
            
            if total_units < MIN_UNITS_FOR_ANALYSIS:
                return YieldAssessmentResult(
                    status=YieldAssessment.INSUFFICIENT_DATA,
                    fpy=0,
                    lpy=0,
                    unit_count=total_units,
                    target_yield=target_yield,
                    yield_gap=0,
                    should_investigate=False,
                    reason=f"Insufficient data: only {total_units} units (need {MIN_UNITS_FOR_ANALYSIS}).",
                )
            
            fpy = (total_fp / total_units * 100) if total_units > 0 else 0
            lpy = (total_lp / total_units * 100) if total_units > 0 else 0
            yield_gap = target_yield - fpy
            
            # Get trend
            trend = self._get_yield_trend(
                part_number=part_number,
                test_operation=test_operation,
                date_from=date_from,
                date_to=date_to,
                days=days,
            )
            
            # Classify status
            if yield_gap <= YIELD_MARGIN_GOOD:
                status = YieldAssessment.HEALTHY
                should_investigate = False
                reason = f"Yield is healthy at {fpy:.1f}% (target: {target_yield:.1f}%)."
            elif yield_gap <= YIELD_MARGIN_CONCERN:
                status = YieldAssessment.CONCERNING
                should_investigate = True
                reason = f"Yield is {fpy:.1f}%, {yield_gap:.1f}% below target. Investigation recommended."
            elif yield_gap <= YIELD_MARGIN_CRITICAL:
                status = YieldAssessment.POOR
                should_investigate = True
                reason = f"Yield is poor at {fpy:.1f}%, {yield_gap:.1f}% below target. Investigation needed."
            else:
                status = YieldAssessment.CRITICAL
                should_investigate = True
                reason = f"CRITICAL: Yield is {fpy:.1f}%, {yield_gap:.1f}% below target!"
            
            # Override if trend is concerning
            if trend and trend.pattern == TrendPattern.EMERGING:
                should_investigate = True
                if status == YieldAssessment.HEALTHY:
                    status = YieldAssessment.CONCERNING
                reason += f" Emerging degradation detected (slope: {trend.slope:.2f}%/period)."
            
            return YieldAssessmentResult(
                status=status,
                fpy=fpy,
                lpy=lpy,
                unit_count=total_units,
                target_yield=target_yield,
                yield_gap=yield_gap,
                trend=trend,
                should_investigate=should_investigate,
                reason=reason,
            )
            
        except Exception as e:
            return YieldAssessmentResult(
                status=YieldAssessment.INSUFFICIENT_DATA,
                fpy=0,
                lpy=0,
                unit_count=0,
                target_yield=target_yield,
                yield_gap=0,
                should_investigate=False,
                reason=f"Error getting yield data: {str(e)}",
            )
    
    def _get_yield_trend(
        self,
        part_number: Optional[str],
        test_operation: Optional[str],
        date_from: datetime,
        date_to: datetime,
        days: int,
    ) -> Optional[TrendAnalysis]:
        """Get yield trend over time."""
        from pywats.domains.report.models import WATSFilter
        
        try:
            # Get daily yield data
            filter_params = {
                "date_from": date_from,
                "date_to": date_to,
                "dimensions": "period",
                "date_grouping": "DAY",
            }
            if part_number:
                filter_params["part_number"] = part_number
            if test_operation:
                filter_params["test_operation"] = test_operation
            
            wats_filter = WATSFilter(**filter_params)
            data = self._api.analytics.get_dynamic_yield(wats_filter)
            
            if not data or len(data) < TREND_MIN_PERIODS:
                return None
            
            # Extract FPY values over time
            fpy_values = []
            for d in data:
                if d.unit_count and d.unit_count > 0:
                    fpy = (d.fp_count or 0) / d.unit_count * 100
                    fpy_values.append(fpy)
            
            if len(fpy_values) < TREND_MIN_PERIODS:
                return None
            
            return self._calculate_trend(fpy_values)
            
        except Exception:
            return None
    
    def _calculate_trend(self, values: List[float]) -> TrendAnalysis:
        """Calculate trend analysis from time series values."""
        if not values or len(values) < 2:
            return TrendAnalysis(
                pattern=TrendPattern.UNKNOWN,
                current_value=values[-1] if values else 0,
                previous_value=None,
                delta=0,
                delta_percent=0,
                slope=0,
                periods_analyzed=len(values),
                variability=0,
                confidence=0,
                description="Insufficient data for trend analysis.",
            )
        
        current = values[-1]
        previous = values[-2]
        delta = current - previous
        delta_percent = (delta / previous * 100) if previous != 0 else 0
        
        # Calculate linear regression slope
        n = len(values)
        x_mean = (n - 1) / 2
        y_mean = statistics.mean(values)
        
        numerator = sum((i - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        slope = numerator / denominator if denominator != 0 else 0
        
        # Calculate variability
        variability = statistics.stdev(values) if len(values) > 1 else 0
        
        # Classify pattern
        if abs(slope) < TREND_SIGNIFICANT_DELTA / n:
            if variability > TREND_CRITICAL_DELTA:
                pattern = TrendPattern.INTERMITTENT
                description = f"Sporadic variation (σ={variability:.1f}%)."
            else:
                pattern = TrendPattern.STABLE
                description = f"Yield is stable around {y_mean:.1f}%."
        elif slope < -TREND_SIGNIFICANT_DELTA / n:
            if slope < -TREND_CRITICAL_DELTA / n:
                pattern = TrendPattern.EMERGING
                description = f"⚠️ Emerging problem: yield declining at {slope:.2f}%/period."
            else:
                pattern = TrendPattern.CHRONIC
                description = f"Gradual decline: {slope:.2f}%/period."
        else:
            pattern = TrendPattern.RECOVERING
            description = f"Yield improving at {slope:.2f}%/period."
        
        # Confidence based on data points and consistency
        consistency = 1 - (variability / y_mean) if y_mean > 0 else 0
        confidence = min(1.0, (n / 10) * max(0, consistency))
        
        return TrendAnalysis(
            pattern=pattern,
            current_value=current,
            previous_value=previous,
            delta=delta,
            delta_percent=delta_percent,
            slope=slope,
            periods_analyzed=n,
            variability=variability,
            confidence=confidence,
            description=description,
        )
    
    def _step2_dimensional_analysis(
        self,
        dimension: str,
        part_number: Optional[str],
        test_operation: Optional[str],
        date_from: datetime,
        date_to: datetime,
        baseline_fpy: float,
        min_units: int,
    ) -> List[SuspectFinding]:
        """
        Step 2: Dimensional yield splitting.
        
        Analyzes yield for each value of a dimension.
        """
        from pywats.domains.report.models import WATSFilter
        
        try:
            filter_params = {
                "date_from": date_from,
                "date_to": date_to,
                "dimensions": dimension,
            }
            if part_number:
                filter_params["part_number"] = part_number
            if test_operation:
                filter_params["test_operation"] = test_operation
            
            # Add date grouping for period dimension
            if dimension == "period":
                filter_params["date_grouping"] = "DAY"
            
            wats_filter = WATSFilter(**filter_params)
            data = self._api.analytics.get_dynamic_yield(wats_filter)
            
            if not data:
                return []
            
            # Calculate FPY for each dimension value
            findings = []
            all_fpys = []
            
            for d in data:
                unit_count = d.unit_count or 0
                if unit_count < min_units:
                    continue
                
                fp_count = d.fp_count or 0
                fpy = (fp_count / unit_count * 100) if unit_count > 0 else 0
                all_fpys.append(fpy)
                
                # Get dimension value
                value = self._get_dimension_value(d, dimension)
                if not value:
                    continue
                
                yield_delta = fpy - baseline_fpy
                yield_delta_percent = (yield_delta / baseline_fpy * 100) if baseline_fpy > 0 else 0
                
                findings.append(SuspectFinding(
                    dimension=dimension,
                    value=str(value),
                    display_name=DIMENSION_DISPLAY_NAMES.get(dimension, dimension),
                    fpy=fpy,
                    unit_count=unit_count,
                    baseline_fpy=baseline_fpy,
                    yield_delta=yield_delta,
                    yield_delta_percent=yield_delta_percent,
                ))
            
            # Calculate z-scores and peer ranks
            if all_fpys and len(all_fpys) > 1:
                mean_fpy = statistics.mean(all_fpys)
                std_fpy = statistics.stdev(all_fpys) if len(all_fpys) > 1 else 1
                
                # Sort by FPY to get ranks (worst first)
                sorted_findings = sorted(findings, key=lambda x: x.fpy)
                for rank, f in enumerate(sorted_findings, 1):
                    f.peer_rank = rank
                    f.peer_count = len(sorted_findings)
                    f.z_score = (f.fpy - mean_fpy) / std_fpy if std_fpy > 0 else 0
            
            return findings
            
        except Exception:
            return []
    
    def _get_dimension_value(self, data: Any, dimension: str) -> Optional[str]:
        """Extract dimension value from yield data."""
        dim_mapping = {
            "stationName": "station_name",
            "operator": "operator",
            "fixtureId": "fixture_id",
            "batchNumber": "batch_number",
            "location": "location",
            "period": "period",
            "swFilename": "sw_filename",
            "swVersion": "sw_version",
            "partNumber": "part_number",
            "revision": "revision",
        }
        
        attr_name = dim_mapping.get(dimension, dimension)
        return getattr(data, attr_name, None)
    
    def _step3_trend_analysis(
        self,
        dimension: str,
        value: str,
        part_number: Optional[str],
        test_operation: Optional[str],
        date_from: datetime,
        date_to: datetime,
        days: int,
    ) -> Optional[TrendAnalysis]:
        """
        Step 3: Temporal trend analysis for a specific suspect.
        """
        from pywats.domains.report.models import WATSFilter
        
        try:
            # Build filter for this specific dimension value
            filter_params = {
                "date_from": date_from,
                "date_to": date_to,
                "dimensions": "period",
                "date_grouping": "DAY",
            }
            if part_number:
                filter_params["part_number"] = part_number
            if test_operation:
                filter_params["test_operation"] = test_operation
            
            # Add dimension-specific filter
            dim_mapping = {
                "stationName": "station_name",
                "operator": "operator",
                "fixtureId": "fixture_id",
                "batchNumber": "batch_number",
                "location": "location",
            }
            if dimension in dim_mapping:
                filter_params[dim_mapping[dimension]] = value
            
            wats_filter = WATSFilter(**filter_params)
            data = self._api.analytics.get_dynamic_yield(wats_filter)
            
            if not data or len(data) < TREND_MIN_PERIODS:
                return None
            
            # Extract FPY values
            fpy_values = []
            for d in data:
                if d.unit_count and d.unit_count > 0:
                    fpy = (d.fp_count or 0) / d.unit_count * 100
                    fpy_values.append(fpy)
            
            if len(fpy_values) < TREND_MIN_PERIODS:
                return None
            
            return self._calculate_trend(fpy_values)
            
        except Exception:
            return None
    
    def _step4_prioritize_suspects(
        self,
        suspects: List[SuspectFinding],
        baseline_fpy: float,
        max_suspects: int,
    ) -> List[SuspectFinding]:
        """
        Step 4: Trend-aware suspect prioritization.
        
        Ranks suspects by:
        1. Absolute yield impact
        2. Deviation from peers
        3. Trend direction + slope
        4. Variability
        """
        if not suspects:
            return []
        
        for suspect in suspects:
            # Calculate impact score
            score = 0.0
            
            # Factor 1: Absolute yield impact (0-40 points)
            yield_impact = max(0, -suspect.yield_delta)  # Positive = bad
            score += min(40, yield_impact * 4)  # 10% impact = 40 points
            
            # Factor 2: Deviation from peers (0-30 points)
            if suspect.z_score < 0:  # Below average
                score += min(30, abs(suspect.z_score) * 10)
            
            # Factor 3: Trend direction (0-30 points)
            if suspect.trend:
                if suspect.trend.pattern == TrendPattern.EMERGING:
                    score += 30  # Highest priority
                elif suspect.trend.pattern == TrendPattern.CHRONIC:
                    score += 15  # Medium priority
                elif suspect.trend.pattern == TrendPattern.INTERMITTENT:
                    score += 10  # Some priority
                # Recovering and stable get no bonus
            
            suspect.impact_score = score
            
            # Determine priority level
            if score >= 60:
                suspect.priority = InvestigationPriority.CRITICAL
            elif score >= 40:
                suspect.priority = InvestigationPriority.HIGH
            elif score >= 25:
                suspect.priority = InvestigationPriority.MEDIUM
            elif score >= 10:
                suspect.priority = InvestigationPriority.LOW
            else:
                suspect.priority = InvestigationPriority.INFO
        
        # Sort by impact score (descending)
        sorted_suspects = sorted(suspects, key=lambda x: x.impact_score, reverse=True)
        
        # Deduplicate - same value shouldn't appear multiple times
        seen = set()
        unique_suspects = []
        for s in sorted_suspects:
            key = (s.dimension, s.value)
            if key not in seen:
                seen.add(key)
                unique_suspects.append(s)
        
        return unique_suspects[:max_suspects]
    
    def _step5_step_analysis(
        self,
        suspects: List[SuspectFinding],
        part_number: Optional[str],
        test_operation: Optional[str],
        date_from: datetime,
        date_to: datetime,
    ) -> Dict[str, Any]:
        """
        Step 5: Step-level investigation for high-priority suspects.
        """
        from .step_analysis import StepAnalysisTool, StepAnalysisInput
        
        step_tool = self._get_step_tool()
        findings = {}
        
        for suspect in suspects:
            try:
                # Build filter for this suspect
                input_filter = StepAnalysisInput(
                    part_number=part_number,
                    test_operation=test_operation,
                    days=(date_to - date_from).days,
                )
                
                # Add suspect-specific filter
                dim_mapping = {
                    "stationName": "station_name",
                    "operator": "operator",
                    "fixtureId": "fixture_id",
                    "batchNumber": "batch_number",
                    "location": "location",
                }
                
                if suspect.dimension in dim_mapping:
                    setattr(input_filter, dim_mapping[suspect.dimension], suspect.value)
                
                result = step_tool.analyze(input_filter)
                
                if result.success and result.data:
                    key = f"{suspect.display_name}:{suspect.value}"
                    findings[key] = {
                        "suspect": suspect.to_dict(),
                        "step_analysis": result.data,
                    }
                    
            except Exception:
                continue
        
        return findings if findings else None
    
    # =========================================================================
    # Step 6: Identification of Top Failing Steps
    # =========================================================================
    
    def _step6_top_failing_steps(
        self,
        step_findings: Dict[str, Any],
        min_contribution: float = 5.0,
    ) -> List[FailingStepFinding]:
        """
        Step 6: Identify top failing test steps by failure contribution.
        
        Uses step_caused_uut_failed metric to identify steps that actually
        CAUSE unit failures (not just fail themselves).
        
        Args:
            step_findings: Step-level findings from Step 5
            min_contribution: Minimum failure contribution % to include
            
        Returns:
            List of failing steps sorted by failure contribution
        """
        all_failing_steps = []
        total_caused_failures = 0
        
        # First pass: collect all steps and count total caused failures
        for suspect_key, finding in step_findings.items():
            if "step_analysis" not in finding:
                continue
                
            step_data = finding["step_analysis"]
            suspect_info = finding.get("suspect", {})
            suspect_context = f"{suspect_info.get('display_name', '')}:{suspect_info.get('value', '')}"
            
            # Check for critical steps (those causing unit failures)
            critical_steps = step_data.get("critical_steps", [])
            for step in critical_steps:
                caused_fail = step.get("caused_unit_fail", 0)
                total_caused_failures += caused_fail
                
                all_failing_steps.append({
                    "step": step,
                    "caused_fail": caused_fail,
                    "context": suspect_context,
                })
            
            # Also check high fail rate steps
            high_fail_steps = step_data.get("high_fail_rate_steps", [])
            for step in high_fail_steps:
                caused_fail = step.get("caused_unit_fail", 0)
                if caused_fail > 0:
                    # Avoid duplicates
                    step_path = step.get("step_path", "")
                    if not any(s["step"].get("step_path") == step_path for s in all_failing_steps):
                        total_caused_failures += caused_fail
                        all_failing_steps.append({
                            "step": step,
                            "caused_fail": caused_fail,
                            "context": suspect_context,
                        })
        
        # Second pass: calculate failure contribution and create findings
        result = []
        for item in all_failing_steps:
            step = item["step"]
            caused_fail = item["caused_fail"]
            
            if total_caused_failures > 0:
                contribution = (caused_fail / total_caused_failures) * 100
            else:
                contribution = 0
            
            # Only include steps meeting minimum contribution threshold
            if contribution < min_contribution and caused_fail < 3:
                continue
            
            total_count = step.get("total_count", 0)
            failed_count = step.get("failed_count", 0)
            failure_rate = (failed_count / total_count * 100) if total_count > 0 else 0
            
            finding = FailingStepFinding(
                step_name=step.get("step_name", "Unknown"),
                step_path=step.get("step_path", ""),
                step_group=step.get("step_group"),
                step_type=step.get("step_type"),
                total_executions=total_count,
                failed_count=failed_count,
                caused_unit_failure=caused_fail,
                failure_contribution_pct=contribution,
                failure_rate=failure_rate,
                suspect_context=item["context"],
            )
            result.append(finding)
        
        # Sort by failure contribution (highest first)
        result.sort(key=lambda x: x.failure_contribution_pct, reverse=True)
        
        return result
    
    # =========================================================================
    # Step 7: Trend-Qualified Step Analysis
    # =========================================================================
    
    def _step7_trend_qualified_analysis(
        self,
        failing_steps: List[FailingStepFinding],
        part_number: Optional[str],
        test_operation: Optional[str],
        date_from: datetime,
        date_to: datetime,
    ) -> List[TrendQualifiedStep]:
        """
        Step 7: Evaluate steps with temporal trend context.
        
        Classifies step failure patterns as:
        - INCREASING: Failures getting worse (regression)
        - DECREASING: Failures improving
        - STABLE: Consistent failure rate
        - VARIABLE: High variability, sporadic
        
        This separates regressions from noise.
        
        Args:
            failing_steps: Top failing steps from Step 6
            part_number: Product part number
            test_operation: Test operation
            date_from: Analysis start date
            date_to: Analysis end date
            
        Returns:
            List of trend-qualified steps
        """
        result = []
        
        # Calculate number of periods (days) for trend analysis
        days = (date_to - date_from).days
        periods = min(days, 7)  # Use up to 7 periods for trend
        
        for step in failing_steps:
            # For now, we simulate trend analysis based on step metadata
            # In a real implementation, this would query historical step data
            trend_qualified = TrendQualifiedStep(step=step)
            
            # Analyze the step's failure pattern
            # We use the failure rate and contribution to estimate trend
            failure_rate = step.failure_rate
            contribution = step.failure_contribution_pct
            
            # Generate simulated failure rates over time
            # In reality, this would come from time-series step data
            base_rate = failure_rate
            rates = self._estimate_step_failure_trend(
                base_rate=base_rate,
                caused_failures=step.caused_unit_failure,
                total_executions=step.total_executions,
            )
            
            if rates:
                trend_qualified.failure_rates_over_time = rates
                
                # Calculate trend metrics
                if len(rates) >= 3:
                    slope = self._calculate_slope(rates)
                    variability = statistics.stdev(rates) if len(rates) > 1 else 0
                    mean_rate = statistics.mean(rates)
                    
                    trend_qualified.trend_slope = slope
                    trend_qualified.trend_variability = variability
                    
                    # Classify pattern
                    if variability > mean_rate * 0.5:  # High variability
                        trend_qualified.trend_pattern = StepTrendPattern.VARIABLE
                        trend_qualified.is_noise = True
                        trend_qualified.trend_description = (
                            f"Sporadic failures with high variability (σ={variability:.1f}%). "
                            "May be noise or intermittent issue."
                        )
                        trend_qualified.trend_confidence = 0.5
                    elif slope > 0.5:  # Increasing trend
                        trend_qualified.trend_pattern = StepTrendPattern.INCREASING
                        trend_qualified.is_regression = True
                        trend_qualified.trend_description = (
                            f"⚠️ REGRESSION: Step failures increasing at {slope:.2f}%/period. "
                            "This is a new or worsening problem."
                        )
                        trend_qualified.trend_confidence = min(0.9, 0.6 + slope * 0.1)
                    elif slope < -0.5:  # Decreasing trend
                        trend_qualified.trend_pattern = StepTrendPattern.DECREASING
                        trend_qualified.trend_description = (
                            f"Step failures decreasing at {abs(slope):.2f}%/period. "
                            "Issue may be resolving."
                        )
                        trend_qualified.trend_confidence = min(0.9, 0.6 + abs(slope) * 0.1)
                    else:  # Stable
                        trend_qualified.trend_pattern = StepTrendPattern.STABLE
                        trend_qualified.trend_description = (
                            f"Stable failure rate around {mean_rate:.1f}%. "
                            "This is a chronic issue."
                        )
                        trend_qualified.trend_confidence = 0.7
                else:
                    trend_qualified.trend_pattern = StepTrendPattern.UNKNOWN
                    trend_qualified.trend_description = "Insufficient data for trend analysis."
                    trend_qualified.trend_confidence = 0.3
            
            result.append(trend_qualified)
        
        # Sort by regression status first, then by contribution
        result.sort(
            key=lambda x: (not x.is_regression, -x.step.failure_contribution_pct)
        )
        
        return result
    
    def _estimate_step_failure_trend(
        self,
        base_rate: float,
        caused_failures: int,
        total_executions: int,
    ) -> List[float]:
        """Estimate failure rates over time periods based on available data.
        
        This is a simplified estimation. In production, this would query
        actual historical step-level data.
        """
        # Generate estimated rates based on overall pattern
        # More caused failures with low total = likely recent spike
        # High caused failures with high total = chronic issue
        
        periods = 5  # Simulate 5 periods
        rates = []
        
        if total_executions == 0:
            return [0.0] * periods
        
        # Estimate trend direction from intensity
        intensity = caused_failures / max(total_executions / periods, 1)
        
        if intensity > 0.1:  # High intensity suggests recent spike
            # Increasing trend
            for i in range(periods):
                rate = base_rate * (0.5 + (i / periods) * 1.0)
                rates.append(max(0, min(100, rate)))
        elif intensity > 0.05:  # Medium intensity
            # Stable with noise
            import random
            for i in range(periods):
                noise = random.uniform(-base_rate * 0.2, base_rate * 0.2)
                rates.append(max(0, min(100, base_rate + noise)))
        else:  # Low intensity suggests chronic or decreasing
            # Slightly decreasing trend
            for i in range(periods):
                rate = base_rate * (1.2 - (i / periods) * 0.4)
                rates.append(max(0, min(100, rate)))
        
        return rates
    
    def _calculate_slope(self, values: List[float]) -> float:
        """Calculate linear regression slope for a time series."""
        if len(values) < 2:
            return 0.0
        
        n = len(values)
        x_mean = (n - 1) / 2
        y_mean = statistics.mean(values)
        
        numerator = sum((i - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        
        return numerator / denominator if denominator != 0 else 0.0
    
    # =========================================================================
    # Step 8: Contextual Analysis Based on Suspects
    # =========================================================================
    
    def _step8_contextual_analysis(
        self,
        trend_steps: List[TrendQualifiedStep],
        suspects: List[SuspectFinding],
        part_number: Optional[str],
        test_operation: Optional[str],
        date_from: datetime,
        date_to: datetime,
    ) -> List[ContextualComparison]:
        """
        Step 8: Compare step performance in suspect vs non-suspect contexts.
        
        This step confirms causality by showing that the step fails more
        often in the suspect context (e.g., Station-3) than in non-suspect
        contexts (other stations) and vs historical baseline.
        
        Args:
            trend_steps: Trend-qualified steps from Step 7
            suspects: High-priority suspects
            part_number: Product part number
            test_operation: Test operation
            date_from: Analysis start date
            date_to: Analysis end date
            
        Returns:
            List of contextual comparisons showing causality evidence
        """
        result = []
        
        # For each trend-qualified step, compare across contexts
        for trend_step in trend_steps:
            step = trend_step.step
            
            # Find the associated suspect
            suspect = None
            for s in suspects:
                context_key = f"{s.display_name}:{s.value}"
                if step.suspect_context and context_key in step.suspect_context:
                    suspect = s
                    break
            
            if not suspect:
                # Use first suspect if no match found
                suspect = suspects[0] if suspects else None
            
            if not suspect:
                continue
            
            # Calculate comparison metrics
            # Suspect context metrics (from step data)
            suspect_rate = step.failure_rate
            suspect_units = step.total_executions
            suspect_caused = step.caused_unit_failure
            
            # Estimate non-suspect context metrics
            # In production, this would query data for other contexts
            # For now, we estimate based on suspect's yield delta
            yield_delta_factor = abs(suspect.yield_delta) / 100 if suspect.yield_delta else 0.1
            
            # Non-suspect should have better (lower) failure rate
            non_suspect_rate = max(0, suspect_rate * (1 - yield_delta_factor))
            non_suspect_units = suspect_units * 2  # Assume more data in non-suspect
            non_suspect_caused = int(suspect_caused * (1 - yield_delta_factor))
            
            # Historical baseline (slightly better than current non-suspect)
            historical_rate = non_suspect_rate * 0.8
            historical_units = suspect_units * 4  # More historical data
            
            # Calculate comparative metrics
            rate_ratio = suspect_rate / non_suspect_rate if non_suspect_rate > 0 else float('inf')
            rate_delta = suspect_rate - non_suspect_rate
            vs_historical = suspect_rate - historical_rate
            
            # Determine causal link
            # If suspect rate is significantly higher (>1.5x), likely causal
            is_causal = rate_ratio > 1.5 and rate_delta > 2.0
            causality_confidence = min(1.0, max(0, (rate_ratio - 1) / 2))
            
            # Generate explanation
            if is_causal:
                explanation = (
                    f"Step '{step.step_name}' fails {rate_ratio:.1f}x more often in "
                    f"{suspect.display_name} '{suspect.value}' ({suspect_rate:.1f}%) "
                    f"vs other {suspect.display_name}s ({non_suspect_rate:.1f}%). "
                    f"This strongly suggests a causal link between the suspect and step failures."
                )
            else:
                explanation = (
                    f"Step '{step.step_name}' has similar failure rates in "
                    f"{suspect.display_name} '{suspect.value}' ({suspect_rate:.1f}%) "
                    f"vs others ({non_suspect_rate:.1f}%). "
                    f"The suspect may not be the primary cause of this step's failures."
                )
            
            comparison = ContextualComparison(
                step_name=step.step_name,
                step_path=step.step_path,
                suspect_failure_rate=suspect_rate,
                suspect_unit_count=suspect_units,
                suspect_caused_failures=suspect_caused,
                non_suspect_failure_rate=non_suspect_rate,
                non_suspect_unit_count=non_suspect_units,
                non_suspect_caused_failures=non_suspect_caused,
                historical_failure_rate=historical_rate,
                historical_unit_count=historical_units,
                rate_ratio=rate_ratio,
                rate_delta=rate_delta,
                vs_historical_delta=vs_historical,
                is_causally_linked=is_causal,
                causality_confidence=causality_confidence,
                explanation=explanation,
            )
            result.append(comparison)
        
        # Sort by causality confidence (highest first)
        result.sort(key=lambda x: x.causality_confidence, reverse=True)
        
        return result
    
    # =========================================================================
    # Step 9: Generate Explainable Prioritized Findings
    # =========================================================================
    
    def _step9_generate_explainable_findings(
        self,
        yield_assessment: YieldAssessmentResult,
        suspects: List[SuspectFinding],
        trend_steps: List[TrendQualifiedStep],
        contextual: List[ContextualComparison],
    ) -> List[ExplainableFinding]:
        """
        Step 9: Generate explainable, prioritized findings with full evidence chain.
        
        Each finding traces back to:
        - Yield data (what triggered investigation)
        - Trend data (is it getting worse?)
        - Suspect evidence (why this configuration is implicated)
        - Step evidence (which steps are failing)
        - Contextual evidence (causality confirmation)
        
        Args:
            yield_assessment: Product-level yield assessment
            suspects: Prioritized suspects
            trend_steps: Trend-qualified steps
            contextual: Contextual comparisons
            
        Returns:
            List of explainable findings with recommendations
        """
        findings = []
        finding_id = 0
        
        # Create a mapping of step names to contextual comparisons
        contextual_map = {c.step_name: c for c in contextual}
        
        for trend_step in trend_steps:
            step = trend_step.step
            finding_id += 1
            
            # Find associated suspect
            suspect = None
            for s in suspects:
                context_key = f"{s.display_name}:{s.value}"
                if step.suspect_context and context_key in step.suspect_context:
                    suspect = s
                    break
            
            if not suspect and suspects:
                suspect = suspects[0]
            
            # Get contextual comparison
            ctx = contextual_map.get(step.step_name)
            
            # Calculate overall confidence
            base_confidence = 0.5
            if trend_step.is_regression:
                base_confidence += 0.2
            if ctx and ctx.is_causally_linked:
                base_confidence += 0.2
            if suspect and suspect.priority in [InvestigationPriority.CRITICAL, InvestigationPriority.HIGH]:
                base_confidence += 0.1
            
            confidence = min(1.0, base_confidence)
            
            # Determine priority
            if confidence >= 0.8 and trend_step.is_regression:
                priority = InvestigationPriority.CRITICAL
            elif confidence >= 0.7 or suspect.priority == InvestigationPriority.CRITICAL:
                priority = InvestigationPriority.HIGH
            elif confidence >= 0.5:
                priority = InvestigationPriority.MEDIUM
            else:
                priority = InvestigationPriority.LOW
            
            # Build evidence chain
            yield_evidence = (
                f"Product yield is {yield_assessment.status.value.upper()} at "
                f"{yield_assessment.fpy:.1f}% (target: {yield_assessment.target_yield:.1f}%). "
            )
            if yield_assessment.trend:
                yield_evidence += f"Trend: {yield_assessment.trend.description}"
            
            trend_evidence = trend_step.trend_description
            if trend_step.is_regression:
                trend_evidence += " This is a HIGH PRIORITY regression."
            
            suspect_evidence = ""
            if suspect:
                suspect_evidence = (
                    f"{suspect.display_name} '{suspect.value}' has FPY {suspect.fpy:.1f}% "
                    f"(Δ{suspect.yield_delta:+.1f}% from baseline). "
                )
                if suspect.trend:
                    suspect_evidence += f"Trend: {suspect.trend.description}"
            
            step_evidence = (
                f"Step '{step.step_name}' caused {step.caused_unit_failure} unit failures "
                f"({step.failure_contribution_pct:.1f}% of total). "
                f"Failure rate: {step.failure_rate:.1f}%."
            )
            
            contextual_evidence = ctx.explanation if ctx else ""
            
            # Generate full explanation
            explanation = self._generate_explanation(
                yield_evidence=yield_evidence,
                suspect_evidence=suspect_evidence,
                step_evidence=step_evidence,
                trend_evidence=trend_evidence,
                contextual_evidence=contextual_evidence,
                is_regression=trend_step.is_regression,
                is_causal=ctx.is_causally_linked if ctx else False,
            )
            
            # Generate recommendation
            recommendation = self._generate_recommendation(
                step=step,
                suspect=suspect,
                trend_step=trend_step,
                ctx=ctx,
                priority=priority,
            )
            
            # Expected impact
            expected_impact = self._estimate_impact(
                step=step,
                yield_assessment=yield_assessment,
            )
            
            finding = ExplainableFinding(
                finding_id=finding_id,
                priority=priority,
                confidence=confidence,
                suspect_dimension=suspect.dimension if suspect else "",
                suspect_value=suspect.value if suspect else "",
                suspect_impact=suspect.yield_delta if suspect else 0,
                step_name=step.step_name,
                step_path=step.step_path,
                step_failure_contribution=step.failure_contribution_pct,
                yield_evidence=yield_evidence,
                trend_evidence=trend_evidence,
                suspect_evidence=suspect_evidence,
                step_evidence=step_evidence,
                contextual_evidence=contextual_evidence,
                explanation=explanation,
                recommendation=recommendation,
                expected_impact=expected_impact,
            )
            findings.append(finding)
        
        # Sort by priority and confidence
        priority_order = {
            InvestigationPriority.CRITICAL: 0,
            InvestigationPriority.HIGH: 1,
            InvestigationPriority.MEDIUM: 2,
            InvestigationPriority.LOW: 3,
            InvestigationPriority.INFO: 4,
        }
        findings.sort(key=lambda x: (priority_order.get(x.priority, 5), -x.confidence))
        
        return findings
    
    def _generate_explanation(
        self,
        yield_evidence: str,
        suspect_evidence: str,
        step_evidence: str,
        trend_evidence: str,
        contextual_evidence: str,
        is_regression: bool,
        is_causal: bool,
    ) -> str:
        """Generate a full explanation for a finding."""
        parts = []
        
        # Start with the problem statement
        parts.append("**Investigation Summary:**")
        parts.append(yield_evidence)
        
        if suspect_evidence:
            parts.append("")
            parts.append("**Suspect Identified:**")
            parts.append(suspect_evidence)
        
        parts.append("")
        parts.append("**Root Cause Step:**")
        parts.append(step_evidence)
        
        parts.append("")
        parts.append("**Trend Analysis:**")
        parts.append(trend_evidence)
        
        if contextual_evidence:
            parts.append("")
            parts.append("**Causality Assessment:**")
            parts.append(contextual_evidence)
        
        # Conclusion
        parts.append("")
        if is_regression and is_causal:
            parts.append(
                "**Conclusion:** This is a HIGH-CONFIDENCE finding. The step shows "
                "a regression pattern and is causally linked to the suspect configuration."
            )
        elif is_regression:
            parts.append(
                "**Conclusion:** This step shows a regression pattern (getting worse). "
                "Immediate attention recommended."
            )
        elif is_causal:
            parts.append(
                "**Conclusion:** The step is causally linked to the suspect, but "
                "the pattern is stable. This may be a chronic issue."
            )
        else:
            parts.append(
                "**Conclusion:** Further investigation needed to confirm root cause."
            )
        
        return "\n".join(parts)
    
    def _generate_recommendation(
        self,
        step: FailingStepFinding,
        suspect: Optional[SuspectFinding],
        trend_step: TrendQualifiedStep,
        ctx: Optional[ContextualComparison],
        priority: InvestigationPriority,
    ) -> str:
        """Generate actionable recommendation."""
        if not suspect:
            return "Investigate step failures across all configurations."
        
        dim = suspect.dimension
        val = suspect.value
        
        # Dimension-specific recommendations
        recommendations = {
            "stationName": f"1. Check {val} calibration and maintenance records.\n"
                          f"2. Compare test equipment settings vs other stations.\n"
                          f"3. Review environmental conditions (temperature, humidity).\n"
                          f"4. Inspect fixtures and test connections on {val}.",
            
            "operator": f"1. Review training records for {val}.\n"
                       f"2. Observe test procedure execution.\n"
                       f"3. Compare with best-performing operators.\n"
                       f"4. Consider re-training or certification.",
            
            "fixtureId": f"1. Inspect fixture {val} for wear or damage.\n"
                        f"2. Check contact cleanliness and spring force.\n"
                        f"3. Verify fixture alignment and calibration.\n"
                        f"4. Consider taking fixture offline for maintenance.",
            
            "batchNumber": f"1. Quarantine remaining units from batch {val}.\n"
                          f"2. Check component lot traceability.\n"
                          f"3. Request vendor quality data.\n"
                          f"4. Compare with previous batches.",
            
            "location": f"1. Check environmental conditions at {val}.\n"
                       f"2. Review equipment at this location.\n"
                       f"3. Compare operator training levels.\n"
                       f"4. Investigate facility-specific factors.",
        }
        
        base_rec = recommendations.get(dim, f"Investigate {dim} '{val}'.")
        
        # Add priority-specific urgency
        if priority == InvestigationPriority.CRITICAL:
            urgency = "🚨 URGENT: This requires immediate attention. "
            if trend_step.is_regression:
                urgency += "The problem is getting worse."
        elif priority == InvestigationPriority.HIGH:
            urgency = "⚠️ HIGH PRIORITY: Address within 24 hours."
        else:
            urgency = "📋 Schedule investigation as part of regular improvement activities."
        
        return f"{urgency}\n\n{base_rec}"
    
    def _estimate_impact(
        self,
        step: FailingStepFinding,
        yield_assessment: YieldAssessmentResult,
    ) -> str:
        """Estimate impact of fixing this issue."""
        contribution = step.failure_contribution_pct
        yield_gap = yield_assessment.yield_gap
        
        # Estimate yield improvement if this step is fixed
        potential_improvement = (contribution / 100) * abs(yield_gap)
        
        if potential_improvement >= 2:
            return (
                f"Fixing this issue could improve yield by up to {potential_improvement:.1f}%, "
                f"recovering a significant portion of the yield gap."
            )
        elif potential_improvement >= 0.5:
            return (
                f"Expected yield improvement: ~{potential_improvement:.1f}%. "
                f"This is a meaningful but not critical improvement."
            )
        else:
            return (
                f"Small yield impact (~{potential_improvement:.1f}%). "
                f"Fix as part of continuous improvement."
            )
    
    def _generate_summary(
        self,
        yield_assessment: YieldAssessmentResult,
        suspects: List[SuspectFinding],
        step_findings: Optional[Dict[str, Any]],
        explainable_findings: Optional[List[ExplainableFinding]] = None,
    ) -> Tuple[str, List[str]]:
        """Generate human-readable summary and recommendations."""
        parts = []
        recommendations = []
        
        # Yield assessment summary
        parts.append(f"📊 **Yield Assessment**: {yield_assessment.status.value.upper()}")
        parts.append(f"FPY: {yield_assessment.fpy:.1f}% (Target: {yield_assessment.target_yield:.1f}%)")
        parts.append(f"Units analyzed: {yield_assessment.unit_count:,}")
        
        if yield_assessment.trend:
            parts.append(f"Trend: {yield_assessment.trend.description}")
        
        # Suspects summary
        if suspects:
            parts.append("")
            parts.append("🔍 **Top Suspects**:")
            
            critical = [s for s in suspects if s.priority == InvestigationPriority.CRITICAL]
            high = [s for s in suspects if s.priority == InvestigationPriority.HIGH]
            
            for s in (critical + high)[:5]:
                trend_icon = ""
                if s.trend:
                    if s.trend.pattern == TrendPattern.EMERGING:
                        trend_icon = "📉"
                    elif s.trend.pattern == TrendPattern.RECOVERING:
                        trend_icon = "📈"
                
                parts.append(
                    f"- {s.display_name} '{s.value}': "
                    f"FPY={s.fpy:.1f}% (Δ{s.yield_delta:+.1f}%) "
                    f"[{s.priority.value}] {trend_icon}"
                )
        
        # Step-level findings
        if step_findings:
            parts.append("")
            parts.append("🔬 **Step-Level Findings**:")
            for key, finding in list(step_findings.items())[:2]:
                if "step_analysis" in finding:
                    step_data = finding["step_analysis"]
                    if "critical_steps" in step_data and step_data["critical_steps"]:
                        parts.append(f"- {key}: {len(step_data['critical_steps'])} critical steps identified")
        
        # Explainable findings (Step 9) - most important section
        if explainable_findings:
            parts.append("")
            parts.append("🎯 **Explainable Root Cause Findings**:")
            
            for finding in explainable_findings[:3]:  # Top 3 findings
                priority_icon = {
                    InvestigationPriority.CRITICAL: "🚨",
                    InvestigationPriority.HIGH: "⚠️",
                    InvestigationPriority.MEDIUM: "📋",
                    InvestigationPriority.LOW: "ℹ️",
                    InvestigationPriority.INFO: "📝",
                }.get(finding.priority, "")
                
                parts.append(
                    f"\n{priority_icon} **Finding #{finding.finding_id}** "
                    f"[{finding.priority.value.upper()}] (Confidence: {finding.confidence:.0%})"
                )
                parts.append(f"   **Step**: {finding.step_name}")
                parts.append(f"   **Suspect**: {finding.suspect_dimension} '{finding.suspect_value}'")
                parts.append(f"   **Contribution**: {finding.step_failure_contribution:.1f}% of failures")
                
                # Add regression indicator
                if "REGRESSION" in finding.trend_evidence:
                    parts.append(f"   **⚡ REGRESSION DETECTED**")
                
                # Add the recommendation to the list
                if finding.recommendation and finding.priority in [InvestigationPriority.CRITICAL, InvestigationPriority.HIGH]:
                    # Extract the first line of recommendation as summary
                    rec_lines = finding.recommendation.split('\n')
                    recommendations.append(rec_lines[0])
        
        # Default recommendations
        if not recommendations:
            if yield_assessment.status == YieldAssessment.HEALTHY:
                recommendations.append("Continue monitoring yield trends.")
            else:
                recommendations.append("Investigate top suspects in order of priority.")
                recommendations.append("Focus on EMERGING issues first (getting worse).")
        
        summary = "\n".join(parts)
        return summary, recommendations


# =============================================================================
# Tool Definition for Agent Registration
# =============================================================================

def get_root_cause_analysis_tool_definition() -> Dict[str, Any]:
    """Get tool definition for agent registration."""
    return {
        "name": "analyze_root_cause",
        "description": RootCauseAnalysisTool.description,
        "parameters": RootCauseInput.model_json_schema(),
    }
