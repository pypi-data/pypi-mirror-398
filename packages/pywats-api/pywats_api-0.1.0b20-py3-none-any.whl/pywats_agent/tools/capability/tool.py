"""
Process Capability Analysis for manufacturing quality assessment.

This module provides advanced statistical process control (SPC) and capability
analysis tools that build on top of Test Step Analysis (TSA). Use these tools
when TSA shows capability concerns and deeper investigation is needed.

ANALYSIS WORKFLOW:
1. TSA identifies steps with Cpk concerns
2. Process Capability Analysis provides:
   - Stability assessment (is the process under statistical control?)
   - Dual Cpk comparison (Cpk vs Cpk_wof - with and without failures)
   - Hidden mode detection (outliers, trends, drift)
   - Improvement recommendations

KEY CONCEPTS:

Dual Cpk Datasets:
┌─────────────────────────────────────────────────────────────────────────────┐
│ Cpk (All Data)         │ Includes ALL measurements including failures      │
│ Cpk_wof (Without Fail) │ Excludes failed measurements - shows "good" data  │
└─────────────────────────────────────────────────────────────────────────────┘

- Cpk (all): Shows ACTUAL process performance including failures
- Cpk_wof: Shows what the process COULD achieve if failures are addressed

Interpretation:
- Cpk ≈ Cpk_wof: Process is stable, failures are not distorting capability
- Cpk << Cpk_wof: Failures are significantly impacting capability
  → Address the failure root cause first
- Cpk >> Cpk_wof: Unusual - failures may be correctly catching bad units

Stability Assessment:
Before trusting Cpk numbers, verify the process is STABLE:
- No significant trends (drift up or down)
- No cyclic patterns (alternating baselines)
- No excessive outliers (beyond 3σ)
- Consistent mean and variance over time

If NOT stable, the Cpk is meaningless - fix stability first!

Hidden Modes & Deviations:
- Bimodal distributions: Two populations mixed together
- Outliers: Measurements beyond 3σ control limits
- Trends: Gradual drift up or down over time
- Shifts: Sudden jumps in mean value
- Alternating baselines: Cyclic variation patterns

Statistical Indicators:
- Cp vs Cpk difference: Process centering issue if Cp >> Cpk
- Upper vs Lower Cpk: Which limit is at risk
- σ_high_3 / σ_low_3: 3-sigma control limits

Example:
    >>> from pywats_agent.tools.process_capability import ProcessCapabilityTool
    >>> 
    >>> tool = ProcessCapabilityTool(api)
    >>> result = tool.analyze(ProcessCapabilityInput(
    ...     part_number="PCBA-001",
    ...     test_operation="FCT",
    ...     step_path="Main/Voltage Test/*"
    ... ))
    >>> 
    >>> # Result includes:
    >>> # - Stability assessment for each measurement
    >>> # - Dual Cpk comparison (with/without failures)
    >>> # - Hidden mode alerts
    >>> # - Prioritized improvement recommendations
"""

from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import statistics

from pydantic import BaseModel, Field

from ...result import AgentResult

if TYPE_CHECKING:
    from pywats import pyWATS
    from pywats.domains.analytics.models import StepAnalysisRow


# =============================================================================
# Stability Status
# =============================================================================

class StabilityStatus(Enum):
    """Process stability status levels."""
    STABLE = "stable"           # Process is under statistical control
    WARNING = "warning"         # Minor stability concerns
    UNSTABLE = "unstable"       # Process is NOT under control
    INSUFFICIENT_DATA = "insufficient_data"  # Not enough data to assess


class CapabilityStatus(Enum):
    """Process capability status."""
    CAPABLE = "capable"           # Cpk ≥ 1.33
    MARGINAL = "marginal"         # 1.0 ≤ Cpk < 1.33
    INCAPABLE = "incapable"       # Cpk < 1.0
    CRITICAL = "critical"         # Cpk < 0.67
    NO_DATA = "no_data"           # No Cpk available


class ImprovementPriority(Enum):
    """Priority level for improvements."""
    CRITICAL = "critical"     # Immediate action required
    HIGH = "high"             # Should address soon
    MEDIUM = "medium"         # Plan for improvement
    LOW = "low"               # Monitor and optimize
    NONE = "none"             # No action needed


class HiddenModeType(Enum):
    """Types of hidden modes/deviations detected."""
    OUTLIERS = "outliers"                 # Data points beyond 3σ
    TREND_UP = "trend_up"                 # Gradual increase over time
    TREND_DOWN = "trend_down"             # Gradual decrease over time
    SHIFT = "shift"                       # Sudden mean change
    BIMODAL = "bimodal"                   # Two populations
    ALTERNATING = "alternating"           # Cyclic variation
    HIGH_VARIANCE = "high_variance"       # Excessive spread
    CENTERING = "centering"               # Off-center from spec midpoint
    APPROACHING_LIMIT = "approaching_limit"  # Measurements near limits


# =============================================================================
# Capability Thresholds (Industry Standards)
# =============================================================================

CPK_CAPABLE = 1.33        # Industry standard - 3 sigma coverage
CPK_MARGINAL = 1.0        # Minimum acceptable
CPK_CRITICAL = 0.67       # Urgent attention needed
CPK_EXCELLENT = 1.67      # 5 sigma equivalent

# Stability thresholds
MIN_SAMPLES_FOR_STABILITY = 30   # Minimum for reliable statistics
OUTLIER_SIGMA = 3.0              # Beyond this is an outlier
TREND_SIGNIFICANCE = 0.05        # 5% significance for trend detection


# =============================================================================
# Data Classes for Analysis Results
# =============================================================================

@dataclass
class DualCpkAnalysis:
    """Comparison of Cpk (all) vs Cpk_wof (without failures).
    
    This analysis helps understand if failures are distorting the
    process capability assessment.
    """
    
    cpk_all: Optional[float] = None
    """Cpk including all measurements (failures included)."""
    
    cpk_wof: Optional[float] = None
    """Cpk without failures - shows process potential."""
    
    cp_all: Optional[float] = None
    """Cp including all measurements."""
    
    cp_wof: Optional[float] = None
    """Cp without failures."""
    
    cpk_upper: Optional[float] = None
    """Cpk against upper limit only."""
    
    cpk_lower: Optional[float] = None
    """Cpk against lower limit only."""
    
    cpk_upper_wof: Optional[float] = None
    cpk_lower_wof: Optional[float] = None
    
    # Derived insights
    cpk_difference: Optional[float] = None
    """Difference: Cpk_wof - Cpk_all. Positive = failures hurting capability."""
    
    cpk_ratio: Optional[float] = None
    """Ratio: Cpk_wof / Cpk_all. > 1.2 suggests significant failure impact."""
    
    failure_impact: str = "unknown"
    """Assessment of failure impact on capability."""
    
    centering_issue: bool = False
    """True if Cp >> Cpk, indicating centering problem."""
    
    critical_limit: Optional[str] = None
    """Which limit is most at risk: 'upper', 'lower', or None."""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "cpk_all": self.cpk_all,
            "cpk_wof": self.cpk_wof,
            "cp_all": self.cp_all,
            "cp_wof": self.cp_wof,
            "cpk_upper": self.cpk_upper,
            "cpk_lower": self.cpk_lower,
            "cpk_upper_wof": self.cpk_upper_wof,
            "cpk_lower_wof": self.cpk_lower_wof,
            "cpk_difference": self.cpk_difference,
            "cpk_ratio": self.cpk_ratio,
            "failure_impact": self.failure_impact,
            "centering_issue": self.centering_issue,
            "critical_limit": self.critical_limit,
        }


@dataclass
class HiddenMode:
    """A detected hidden mode or deviation in the data."""
    
    mode_type: HiddenModeType
    """Type of hidden mode detected."""
    
    severity: str
    """Severity: 'high', 'medium', 'low'."""
    
    description: str
    """Human-readable description of the issue."""
    
    evidence: Dict[str, Any] = field(default_factory=dict)
    """Supporting data for the detection."""
    
    recommendation: str = ""
    """Suggested action to address this mode."""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "mode_type": self.mode_type.value,
            "severity": self.severity,
            "description": self.description,
            "evidence": self.evidence,
            "recommendation": self.recommendation,
        }


@dataclass
class StabilityAnalysis:
    """Results of process stability assessment."""
    
    status: StabilityStatus
    """Overall stability status."""
    
    sample_count: int = 0
    """Number of samples analyzed."""
    
    sample_count_wof: int = 0
    """Number of samples without failures."""
    
    # Statistical metrics
    mean: Optional[float] = None
    mean_wof: Optional[float] = None
    stdev: Optional[float] = None
    stdev_wof: Optional[float] = None
    
    # Control limits
    ucl_3sigma: Optional[float] = None
    """Upper control limit (mean + 3σ)."""
    
    lcl_3sigma: Optional[float] = None
    """Lower control limit (mean - 3σ)."""
    
    ucl_3sigma_wof: Optional[float] = None
    lcl_3sigma_wof: Optional[float] = None
    
    # Stability issues found
    issues: List[str] = field(default_factory=list)
    """List of stability issues detected."""
    
    # Hidden modes detected
    hidden_modes: List[HiddenMode] = field(default_factory=list)
    """Hidden modes and deviations found."""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "sample_count": self.sample_count,
            "sample_count_wof": self.sample_count_wof,
            "mean": self.mean,
            "mean_wof": self.mean_wof,
            "stdev": self.stdev,
            "stdev_wof": self.stdev_wof,
            "ucl_3sigma": self.ucl_3sigma,
            "lcl_3sigma": self.lcl_3sigma,
            "ucl_3sigma_wof": self.ucl_3sigma_wof,
            "lcl_3sigma_wof": self.lcl_3sigma_wof,
            "issues": self.issues,
            "hidden_modes": [m.to_dict() for m in self.hidden_modes],
        }


@dataclass
class MeasurementCapabilityResult:
    """Complete capability analysis for a single measurement."""
    
    step_name: str
    step_path: str
    measure_name: Optional[str] = None
    
    # Limits
    limit_low: Optional[float] = None
    limit_high: Optional[float] = None
    
    # Dual Cpk analysis
    dual_cpk: DualCpkAnalysis = field(default_factory=DualCpkAnalysis)
    
    # Stability
    stability: StabilityAnalysis = field(default_factory=lambda: StabilityAnalysis(
        status=StabilityStatus.INSUFFICIENT_DATA
    ))
    
    # Overall assessment
    capability_status: CapabilityStatus = CapabilityStatus.NO_DATA
    improvement_priority: ImprovementPriority = ImprovementPriority.NONE
    
    # Summary
    summary: str = ""
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_name": self.step_name,
            "step_path": self.step_path,
            "measure_name": self.measure_name,
            "limit_low": self.limit_low,
            "limit_high": self.limit_high,
            "dual_cpk": self.dual_cpk.to_dict(),
            "stability": self.stability.to_dict(),
            "capability_status": self.capability_status.value,
            "improvement_priority": self.improvement_priority.value,
            "summary": self.summary,
            "recommendations": self.recommendations,
        }


@dataclass
class ProcessCapabilityResult:
    """Complete process capability analysis result."""
    
    # Overall metrics
    total_measurements: int = 0
    measurements_analyzed: int = 0
    
    # Status counts
    capable_count: int = 0
    marginal_count: int = 0
    incapable_count: int = 0
    critical_count: int = 0
    
    # Stability counts
    stable_count: int = 0
    warning_count: int = 0
    unstable_count: int = 0
    
    # Aggregate statistics
    avg_cpk_all: Optional[float] = None
    avg_cpk_wof: Optional[float] = None
    min_cpk_all: Optional[float] = None
    min_cpk_wof: Optional[float] = None
    
    # Measurements needing attention (prioritized)
    critical_measurements: List[MeasurementCapabilityResult] = field(default_factory=list)
    unstable_measurements: List[MeasurementCapabilityResult] = field(default_factory=list)
    failure_impacted: List[MeasurementCapabilityResult] = field(default_factory=list)
    approaching_limits: List[MeasurementCapabilityResult] = field(default_factory=list)
    
    # All measurements analyzed
    all_measurements: List[MeasurementCapabilityResult] = field(default_factory=list)
    
    # Summary and recommendations
    analysis_summary: str = ""
    top_recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_measurements": self.total_measurements,
            "measurements_analyzed": self.measurements_analyzed,
            "capable_count": self.capable_count,
            "marginal_count": self.marginal_count,
            "incapable_count": self.incapable_count,
            "critical_count": self.critical_count,
            "stable_count": self.stable_count,
            "warning_count": self.warning_count,
            "unstable_count": self.unstable_count,
            "avg_cpk_all": self.avg_cpk_all,
            "avg_cpk_wof": self.avg_cpk_wof,
            "min_cpk_all": self.min_cpk_all,
            "min_cpk_wof": self.min_cpk_wof,
            "critical_measurements": [m.to_dict() for m in self.critical_measurements],
            "unstable_measurements": [m.to_dict() for m in self.unstable_measurements],
            "failure_impacted": [m.to_dict() for m in self.failure_impacted],
            "approaching_limits": [m.to_dict() for m in self.approaching_limits],
            "all_measurements_count": len(self.all_measurements),
            "analysis_summary": self.analysis_summary,
            "top_recommendations": self.top_recommendations,
        }


# =============================================================================
# Input Model
# =============================================================================

class ProcessCapabilityInput(BaseModel):
    """Input for process capability analysis.
    
    This analysis provides deep capability assessment with stability checking,
    dual Cpk comparison, and hidden mode detection.
    """
    
    part_number: str = Field(
        description="Product part number (REQUIRED)."
    )
    test_operation: str = Field(
        description="Test operation name (REQUIRED, e.g., 'FCT', 'EOL')."
    )
    
    # Optional filters
    revision: Optional[str] = Field(
        default=None,
        description="Product revision to analyze."
    )
    step_path: Optional[str] = Field(
        default=None,
        description=(
            "Filter to specific step path (supports wildcards). "
            "Example: 'Main/Voltage Test/*' or specific step path."
        )
    )
    step_name: Optional[str] = Field(
        default=None,
        description="Filter to specific step name."
    )
    
    # Time range
    days: int = Field(
        default=30,
        description="Number of days to analyze (default: 30)."
    )
    date_from: Optional[datetime] = Field(
        default=None,
        description="Start date (overrides 'days')."
    )
    date_to: Optional[datetime] = Field(
        default=None,
        description="End date (default: now)."
    )
    
    # Analysis options
    run: int = Field(
        default=1,
        description="Run number to analyze (default: 1)."
    )
    cpk_threshold: float = Field(
        default=CPK_CAPABLE,
        description=f"Cpk threshold for 'capable' (default: {CPK_CAPABLE})."
    )
    include_stable_only: bool = Field(
        default=False,
        description="If True, only include measurements that are stable."
    )
    max_measurements: int = Field(
        default=50,
        description="Maximum measurements to analyze in detail (default: 50)."
    )


# =============================================================================
# Process Capability Tool
# =============================================================================

class ProcessCapabilityTool:
    """
    Advanced Process Capability Analysis Tool.
    
    This tool builds on TSA to provide deeper statistical analysis:
    
    1. STABILITY CHECK (First!)
       - Is the process under statistical control?
       - Are there trends, shifts, or excessive variation?
       - If NOT stable, Cpk numbers are meaningless!
    
    2. DUAL CpK ANALYSIS
       - Cpk (all): Actual capability including failures
       - Cpk_wof: Potential capability without failures
       - Compare to understand failure impact
    
    3. HIDDEN MODE DETECTION
       - Outliers beyond 3σ
       - Trends (drift up/down)
       - Bimodal distributions
       - Approaching specification limits
       - Centering issues (Cp >> Cpk)
    
    4. IMPROVEMENT RECOMMENDATIONS
       - Prioritized by impact
       - Specific actions based on findings
    
    WHEN TO USE:
    - After TSA shows Cpk concerns
    - When investigating process capability issues
    - For deep-dive statistical analysis
    - To validate process improvements
    
    IMPORTANT NOTES:
    - This tool requires sufficient data (30+ samples preferred)
    - Each measurement is analyzed separately
    - For dimensional analysis (station, SW version, etc.), use separate calls
    
    Example:
        >>> tool = ProcessCapabilityTool(api)
        >>> result = tool.analyze(ProcessCapabilityInput(
        ...     part_number="PCBA-001",
        ...     test_operation="FCT"
        ... ))
        >>> print(result.summary)
    """
    
    name = "analyze_process_capability"
    description = """
Perform advanced process capability analysis with stability assessment.

Use this tool when:
- TSA shows measurements with Cpk concerns
- You need to understand if failures are distorting capability
- Investigating process stability issues
- Looking for hidden modes (outliers, trends, drift)
- Validating process improvements

KEY ANALYSIS PROVIDED:

1. STABILITY ASSESSMENT:
   - Checks if process is under statistical control
   - Detects trends, shifts, excessive variation
   - IMPORTANT: If unstable, Cpk is not reliable!

2. DUAL CpK COMPARISON:
   - Cpk (all): Includes all measurements
   - Cpk_wof: Without failures - shows potential
   - Interprets the difference:
     • Similar values = stable process
     • Cpk << Cpk_wof = failures hurting capability

3. HIDDEN MODE DETECTION:
   - Outliers beyond 3-sigma
   - Trends (measurements drifting)
   - Approaching specification limits
   - Centering issues (process not centered)

4. PRIORITIZED RECOMMENDATIONS:
   - Critical: Immediate action needed
   - High: Should address soon
   - Medium: Plan for improvement
   - Low: Monitor and optimize

IMPORTANT: For dimensional analysis (by station, SW version, etc.),
you need to make separate API calls with the appropriate filters.
This tool analyzes ONE configuration at a time.
"""
    
    def __init__(self, api: "pyWATS"):
        """Initialize with pyWATS API instance."""
        self._api = api
    
    @staticmethod
    def get_parameters_schema() -> Dict[str, Any]:
        """Get OpenAI-compatible parameter schema."""
        return {
            "type": "object",
            "properties": {
                "part_number": {
                    "type": "string",
                    "description": "Product part number (REQUIRED)"
                },
                "test_operation": {
                    "type": "string",
                    "description": "Test operation name (REQUIRED)"
                },
                "revision": {
                    "type": "string",
                    "description": "Product revision"
                },
                "step_path": {
                    "type": "string",
                    "description": "Filter to step path (supports wildcards)"
                },
                "step_name": {
                    "type": "string",
                    "description": "Filter to specific step name"
                },
                "days": {
                    "type": "integer",
                    "description": "Days to analyze (default: 30)",
                    "default": 30
                },
                "run": {
                    "type": "integer",
                    "description": "Run number (default: 1)",
                    "default": 1
                },
                "cpk_threshold": {
                    "type": "number",
                    "description": "Cpk threshold for 'capable' (default: 1.33)",
                    "default": 1.33
                },
                "include_stable_only": {
                    "type": "boolean",
                    "description": "Only include stable measurements",
                    "default": False
                },
                "max_measurements": {
                    "type": "integer",
                    "description": "Max measurements to analyze (default: 50)",
                    "default": 50
                },
            },
            "required": ["part_number", "test_operation"]
        }
    
    def analyze(self, filter_input: ProcessCapabilityInput) -> AgentResult:
        """
        Perform comprehensive process capability analysis.
        
        Args:
            filter_input: Analysis parameters
            
        Returns:
            AgentResult with ProcessCapabilityResult
        """
        try:
            # Step 1: Get step analysis data with all Cpk fields
            from pywats.domains.report.models import WATSFilter
            
            # NOTE: step_path and step_name are filtered locally after API call
            # because WATSFilter doesn't support these fields
            filter_params = {
                "part_number": filter_input.part_number,
                "test_operation": filter_input.test_operation,
                "run": filter_input.run,
            }
            
            if filter_input.revision:
                filter_params["revision"] = filter_input.revision
            
            # Date handling
            if filter_input.date_from:
                filter_params["date_from"] = filter_input.date_from
            else:
                filter_params["date_from"] = datetime.now() - timedelta(days=filter_input.days)
            
            if filter_input.date_to:
                filter_params["date_to"] = filter_input.date_to
            
            wats_filter = WATSFilter(**filter_params)
            data = self._api.analytics.get_test_step_analysis(wats_filter)
            
            if not data:
                return AgentResult.ok(
                    data={"measurements_analyzed": 0},
                    summary=self._build_no_data_summary(filter_input),
                )
            
            # Step 1.5: Apply local step_path/step_name filtering
            # (The API doesn't support these filters directly)
            if filter_input.step_path or filter_input.step_name:
                data = self._filter_by_step(data, filter_input.step_path, filter_input.step_name)
                if not data:
                    return AgentResult.ok(
                        data={"measurements_analyzed": 0},
                        summary=self._build_no_data_summary(filter_input),
                    )
            
            # Step 2: Analyze each measurement
            result = self._analyze_measurements(data, filter_input)
            
            # Step 3: Build summary
            summary = self._build_analysis_summary(result, filter_input)
            
            return AgentResult.ok(
                data=result.to_dict(),
                summary=summary,
                metadata={
                    "total_measurements": result.total_measurements,
                    "critical_count": result.critical_count,
                    "unstable_count": result.unstable_count,
                }
            )
            
        except Exception as e:
            return AgentResult.fail(f"Process capability analysis failed: {str(e)}")
    
    def analyze_from_dict(self, params: Dict[str, Any]) -> AgentResult:
        """Analyze from dictionary parameters (for LLM tool calls)."""
        filter_input = ProcessCapabilityInput(**params)
        return self.analyze(filter_input)
    
    def _filter_by_step(
        self,
        data: List["StepAnalysisRow"],
        step_path: Optional[str],
        step_name: Optional[str],
    ) -> List["StepAnalysisRow"]:
        """
        Filter step analysis results by step_path or step_name locally.
        
        The WATSFilter doesn't support step filtering, so we do it locally.
        
        Args:
            data: List of StepAnalysisRow from API
            step_path: Optional step path filter (supports * wildcard)
            step_name: Optional step name filter
            
        Returns:
            Filtered list of StepAnalysisRow
        """
        import fnmatch
        
        filtered = data
        
        if step_path:
            # Support wildcards in step_path
            if '*' in step_path or '?' in step_path:
                filtered = [
                    row for row in filtered
                    if row.step_path and fnmatch.fnmatch(row.step_path, step_path)
                ]
            else:
                # Exact or prefix match
                filtered = [
                    row for row in filtered
                    if row.step_path and (
                        row.step_path == step_path or
                        row.step_path.startswith(step_path + "/") or
                        row.step_path.startswith(step_path + "¶")
                    )
                ]
        
        if step_name:
            # Support wildcards in step_name
            if '*' in step_name or '?' in step_name:
                filtered = [
                    row for row in filtered
                    if row.step_name and fnmatch.fnmatch(row.step_name, step_name)
                ]
            else:
                # Case-insensitive exact match
                step_name_lower = step_name.lower()
                filtered = [
                    row for row in filtered
                    if row.step_name and row.step_name.lower() == step_name_lower
                ]
        
        return filtered
    
    def _analyze_measurements(
        self,
        data: List["StepAnalysisRow"],
        filter_input: ProcessCapabilityInput
    ) -> ProcessCapabilityResult:
        """Analyze all measurements and create comprehensive result."""
        
        result = ProcessCapabilityResult()
        
        # Filter to measurements (rows with Cpk data)
        measurements = [r for r in data if r.cpk is not None or r.cpk_wof is not None]
        result.total_measurements = len(measurements)
        
        # Limit detailed analysis
        measurements = measurements[:filter_input.max_measurements]
        result.measurements_analyzed = len(measurements)
        
        # Track aggregate Cpk values
        cpk_all_values = []
        cpk_wof_values = []
        
        for row in measurements:
            meas_result = self._analyze_single_measurement(row, filter_input)
            result.all_measurements.append(meas_result)
            
            # Update counts
            if meas_result.capability_status == CapabilityStatus.CAPABLE:
                result.capable_count += 1
            elif meas_result.capability_status == CapabilityStatus.MARGINAL:
                result.marginal_count += 1
            elif meas_result.capability_status == CapabilityStatus.INCAPABLE:
                result.incapable_count += 1
            elif meas_result.capability_status == CapabilityStatus.CRITICAL:
                result.critical_count += 1
            
            if meas_result.stability.status == StabilityStatus.STABLE:
                result.stable_count += 1
            elif meas_result.stability.status == StabilityStatus.WARNING:
                result.warning_count += 1
            elif meas_result.stability.status == StabilityStatus.UNSTABLE:
                result.unstable_count += 1
            
            # Track Cpk values for aggregates
            if meas_result.dual_cpk.cpk_all is not None:
                cpk_all_values.append(meas_result.dual_cpk.cpk_all)
            if meas_result.dual_cpk.cpk_wof is not None:
                cpk_wof_values.append(meas_result.dual_cpk.cpk_wof)
            
            # Categorize for priority lists
            if meas_result.improvement_priority == ImprovementPriority.CRITICAL:
                result.critical_measurements.append(meas_result)
            if meas_result.stability.status == StabilityStatus.UNSTABLE:
                result.unstable_measurements.append(meas_result)
            if meas_result.dual_cpk.failure_impact == "significant":
                result.failure_impacted.append(meas_result)
            
            # Check for approaching limits
            for mode in meas_result.stability.hidden_modes:
                if mode.mode_type == HiddenModeType.APPROACHING_LIMIT:
                    result.approaching_limits.append(meas_result)
                    break
        
        # Calculate aggregates
        if cpk_all_values:
            result.avg_cpk_all = sum(cpk_all_values) / len(cpk_all_values)
            result.min_cpk_all = min(cpk_all_values)
        if cpk_wof_values:
            result.avg_cpk_wof = sum(cpk_wof_values) / len(cpk_wof_values)
            result.min_cpk_wof = min(cpk_wof_values)
        
        # Sort priority lists
        result.critical_measurements.sort(key=lambda m: m.dual_cpk.cpk_all or 0)
        result.unstable_measurements.sort(
            key=lambda m: len(m.stability.issues), reverse=True
        )
        
        # Generate top recommendations
        result.top_recommendations = self._generate_top_recommendations(result)
        
        return result
    
    def _analyze_single_measurement(
        self,
        row: "StepAnalysisRow",
        filter_input: ProcessCapabilityInput
    ) -> MeasurementCapabilityResult:
        """Analyze a single measurement for capability and stability."""
        
        meas = MeasurementCapabilityResult(
            step_name=row.step_name or "Unknown",
            step_path=row.step_path or "",
            measure_name=row.measure_name,
            limit_low=row.limit1,
            limit_high=row.limit2,
        )
        
        # --- Dual Cpk Analysis ---
        meas.dual_cpk = self._analyze_dual_cpk(row)
        
        # --- Stability Analysis ---
        meas.stability = self._analyze_stability(row)
        
        # --- Determine Overall Status ---
        # Use Cpk_wof if available and process appears stable, else Cpk_all
        primary_cpk = meas.dual_cpk.cpk_wof if (
            meas.stability.status == StabilityStatus.STABLE and 
            meas.dual_cpk.cpk_wof is not None
        ) else meas.dual_cpk.cpk_all
        
        if primary_cpk is not None:
            if primary_cpk >= filter_input.cpk_threshold:
                meas.capability_status = CapabilityStatus.CAPABLE
                meas.improvement_priority = ImprovementPriority.LOW
            elif primary_cpk >= CPK_MARGINAL:
                meas.capability_status = CapabilityStatus.MARGINAL
                meas.improvement_priority = ImprovementPriority.MEDIUM
            elif primary_cpk >= CPK_CRITICAL:
                meas.capability_status = CapabilityStatus.INCAPABLE
                meas.improvement_priority = ImprovementPriority.HIGH
            else:
                meas.capability_status = CapabilityStatus.CRITICAL
                meas.improvement_priority = ImprovementPriority.CRITICAL
        
        # Upgrade priority if unstable
        if meas.stability.status == StabilityStatus.UNSTABLE:
            if meas.improvement_priority.value in ("low", "medium"):
                meas.improvement_priority = ImprovementPriority.HIGH
        
        # Generate measurement-specific recommendations
        meas.recommendations = self._generate_measurement_recommendations(meas)
        meas.summary = self._build_measurement_summary(meas)
        
        return meas
    
    def _analyze_dual_cpk(self, row: "StepAnalysisRow") -> DualCpkAnalysis:
        """Analyze both Cpk datasets and their relationship."""
        
        analysis = DualCpkAnalysis(
            cpk_all=row.cpk,
            cpk_wof=row.cpk_wof,
            cp_all=row.cp,
            cp_wof=row.cp_wof,
            cpk_upper=row.cp_upper,
            cpk_lower=row.cp_lower,
            cpk_upper_wof=row.cp_upper_wof,
            cpk_lower_wof=row.cp_lower_wof,
        )
        
        # Calculate difference and ratio
        if analysis.cpk_all is not None and analysis.cpk_wof is not None:
            analysis.cpk_difference = analysis.cpk_wof - analysis.cpk_all
            
            if analysis.cpk_all > 0:
                analysis.cpk_ratio = analysis.cpk_wof / analysis.cpk_all
            
            # Interpret failure impact
            if analysis.cpk_ratio is not None:
                if analysis.cpk_ratio > 1.3:
                    analysis.failure_impact = "significant"
                elif analysis.cpk_ratio > 1.1:
                    analysis.failure_impact = "moderate"
                elif analysis.cpk_ratio >= 0.9:
                    analysis.failure_impact = "minimal"
                else:
                    analysis.failure_impact = "unusual"  # Cpk_all > Cpk_wof
        elif analysis.cpk_all is not None:
            analysis.failure_impact = "unknown_wof"
        elif analysis.cpk_wof is not None:
            analysis.failure_impact = "unknown_all"
        
        # Check for centering issue (Cp >> Cpk)
        if analysis.cp_all is not None and analysis.cpk_all is not None:
            if analysis.cp_all > 0 and analysis.cpk_all > 0:
                cp_cpk_ratio = analysis.cp_all / analysis.cpk_all
                if cp_cpk_ratio > 1.3:  # More than 30% difference
                    analysis.centering_issue = True
        
        # Determine critical limit
        if analysis.cpk_upper is not None and analysis.cpk_lower is not None:
            if analysis.cpk_upper < analysis.cpk_lower:
                analysis.critical_limit = "upper"
            elif analysis.cpk_lower < analysis.cpk_upper:
                analysis.critical_limit = "lower"
        elif analysis.cpk_upper is not None:
            analysis.critical_limit = "upper"
        elif analysis.cpk_lower is not None:
            analysis.critical_limit = "lower"
        
        return analysis
    
    def _analyze_stability(self, row: "StepAnalysisRow") -> StabilityAnalysis:
        """Analyze process stability using available statistics."""
        
        stability = StabilityAnalysis(status=StabilityStatus.INSUFFICIENT_DATA)
        
        # Get sample counts
        count = row.measure_count or row.step_count or 0
        count_wof = row.measure_count_wof or count
        
        stability.sample_count = count
        stability.sample_count_wof = count_wof
        
        if count < MIN_SAMPLES_FOR_STABILITY:
            stability.issues.append(
                f"Insufficient data ({count} samples, need {MIN_SAMPLES_FOR_STABILITY}+)"
            )
            return stability
        
        # Get statistics
        stability.mean = row.avg
        stability.mean_wof = row.avg_wof
        stability.stdev = row.stdev
        stability.stdev_wof = row.stdev_wof
        
        # Calculate control limits from sigma values if available
        stability.ucl_3sigma = row.sigma_high_3
        stability.lcl_3sigma = row.sigma_low_3
        stability.ucl_3sigma_wof = row.sigma_high_3_wof
        stability.lcl_3sigma_wof = row.sigma_low_3_wof
        
        # Or calculate from mean/stdev
        if stability.ucl_3sigma is None and stability.mean is not None and stability.stdev is not None:
            stability.ucl_3sigma = stability.mean + 3 * stability.stdev
            stability.lcl_3sigma = stability.mean - 3 * stability.stdev
        
        # --- Detect Hidden Modes ---
        hidden_modes = []
        issues = []
        
        # 1. Check for high variance (stdev relative to spec range)
        if row.limit1 is not None and row.limit2 is not None and stability.stdev is not None:
            spec_range = abs(row.limit2 - row.limit1)
            if spec_range > 0:
                # 6-sigma spread vs spec range
                process_spread = 6 * stability.stdev
                spread_ratio = process_spread / spec_range
                
                if spread_ratio > 1.0:
                    issues.append("Process spread exceeds specification range")
                    hidden_modes.append(HiddenMode(
                        mode_type=HiddenModeType.HIGH_VARIANCE,
                        severity="high",
                        description=f"6σ spread ({process_spread:.4f}) exceeds spec range ({spec_range:.4f})",
                        evidence={"spread_ratio": spread_ratio},
                        recommendation="Reduce process variation or widen specifications"
                    ))
                elif spread_ratio > 0.75:
                    issues.append("Process spread is close to specification range")
                    hidden_modes.append(HiddenMode(
                        mode_type=HiddenModeType.HIGH_VARIANCE,
                        severity="medium",
                        description=f"6σ spread uses {spread_ratio*100:.0f}% of spec range",
                        evidence={"spread_ratio": spread_ratio},
                        recommendation="Monitor for increasing variation"
                    ))
        
        # 2. Check for centering issues
        if row.limit1 is not None and row.limit2 is not None and stability.mean is not None:
            spec_center = (row.limit1 + row.limit2) / 2
            spec_range = abs(row.limit2 - row.limit1)
            
            if spec_range > 0:
                center_offset = abs(stability.mean - spec_center)
                offset_ratio = center_offset / (spec_range / 2)
                
                if offset_ratio > 0.5:
                    issues.append("Process mean significantly off-center")
                    hidden_modes.append(HiddenMode(
                        mode_type=HiddenModeType.CENTERING,
                        severity="high",
                        description=f"Mean ({stability.mean:.4f}) is {offset_ratio*100:.0f}% off spec center ({spec_center:.4f})",
                        evidence={
                            "mean": stability.mean,
                            "spec_center": spec_center,
                            "offset_ratio": offset_ratio
                        },
                        recommendation="Adjust process to center on specification"
                    ))
                elif offset_ratio > 0.25:
                    hidden_modes.append(HiddenMode(
                        mode_type=HiddenModeType.CENTERING,
                        severity="medium",
                        description=f"Mean is {offset_ratio*100:.0f}% off spec center",
                        evidence={"offset_ratio": offset_ratio},
                        recommendation="Consider centering adjustment"
                    ))
        
        # 3. Check for approaching limits
        if stability.mean is not None and stability.stdev is not None:
            if row.limit2 is not None:  # Upper limit
                upper_margin = row.limit2 - stability.mean
                upper_sigma = upper_margin / stability.stdev if stability.stdev > 0 else float('inf')
                
                if upper_sigma < 3:
                    severity = "high" if upper_sigma < 2 else "medium"
                    issues.append(f"Mean is only {upper_sigma:.1f}σ from upper limit")
                    hidden_modes.append(HiddenMode(
                        mode_type=HiddenModeType.APPROACHING_LIMIT,
                        severity=severity,
                        description=f"Only {upper_sigma:.1f}σ margin to upper limit ({row.limit2})",
                        evidence={"sigma_margin": upper_sigma, "limit": row.limit2},
                        recommendation="Risk of upper limit violations - reduce mean or variation"
                    ))
            
            if row.limit1 is not None:  # Lower limit
                lower_margin = stability.mean - row.limit1
                lower_sigma = lower_margin / stability.stdev if stability.stdev > 0 else float('inf')
                
                if lower_sigma < 3:
                    severity = "high" if lower_sigma < 2 else "medium"
                    issues.append(f"Mean is only {lower_sigma:.1f}σ from lower limit")
                    hidden_modes.append(HiddenMode(
                        mode_type=HiddenModeType.APPROACHING_LIMIT,
                        severity=severity,
                        description=f"Only {lower_sigma:.1f}σ margin to lower limit ({row.limit1})",
                        evidence={"sigma_margin": lower_sigma, "limit": row.limit1},
                        recommendation="Risk of lower limit violations - increase mean or reduce variation"
                    ))
        
        # 4. Compare wof vs all data for anomalies
        if stability.mean_wof is not None and stability.mean is not None:
            mean_diff = abs(stability.mean_wof - stability.mean)
            if stability.stdev and stability.stdev > 0:
                mean_diff_sigma = mean_diff / stability.stdev
                if mean_diff_sigma > 0.5:
                    issues.append("Significant mean difference when excluding failures")
                    hidden_modes.append(HiddenMode(
                        mode_type=HiddenModeType.OUTLIERS,
                        severity="medium",
                        description=f"Mean shifts {mean_diff_sigma:.1f}σ when excluding failures",
                        evidence={
                            "mean_all": stability.mean,
                            "mean_wof": stability.mean_wof,
                            "difference_sigma": mean_diff_sigma
                        },
                        recommendation="Failures may be outliers - investigate root cause"
                    ))
        
        # 5. Check stdev difference between wof and all
        if stability.stdev_wof is not None and stability.stdev is not None:
            if stability.stdev > 0:
                stdev_ratio = stability.stdev_wof / stability.stdev
                if stdev_ratio < 0.7:  # wof has much less variation
                    hidden_modes.append(HiddenMode(
                        mode_type=HiddenModeType.BIMODAL,
                        severity="medium",
                        description=f"Variation drops {(1-stdev_ratio)*100:.0f}% when excluding failures",
                        evidence={"stdev_ratio": stdev_ratio},
                        recommendation="Possible bimodal distribution - failures may be distinct population"
                    ))
        
        stability.issues = issues
        stability.hidden_modes = hidden_modes
        
        # Determine overall stability status
        high_severity_count = sum(1 for m in hidden_modes if m.severity == "high")
        medium_severity_count = sum(1 for m in hidden_modes if m.severity == "medium")
        
        if high_severity_count >= 2 or (high_severity_count >= 1 and medium_severity_count >= 2):
            stability.status = StabilityStatus.UNSTABLE
        elif high_severity_count >= 1 or medium_severity_count >= 2:
            stability.status = StabilityStatus.WARNING
        else:
            stability.status = StabilityStatus.STABLE
        
        return stability
    
    def _generate_measurement_recommendations(
        self,
        meas: MeasurementCapabilityResult
    ) -> List[str]:
        """Generate recommendations for a single measurement."""
        
        recommendations = []
        
        # Stability recommendations first
        if meas.stability.status == StabilityStatus.UNSTABLE:
            recommendations.append(
                "⚠️ STABILITY FIRST: Process is not stable. "
                "Address stability before trusting Cpk values."
            )
        
        # Dual Cpk recommendations
        if meas.dual_cpk.failure_impact == "significant":
            recommendations.append(
                f"Failures significantly impact capability "
                f"(Cpk {meas.dual_cpk.cpk_all:.2f} → {meas.dual_cpk.cpk_wof:.2f} without failures). "
                "Address failure root cause first."
            )
        
        # Centering recommendations
        if meas.dual_cpk.centering_issue:
            recommendations.append(
                f"Process is off-center (Cp={meas.dual_cpk.cp_all:.2f} vs Cpk={meas.dual_cpk.cpk_all:.2f}). "
                "Centering adjustment could improve capability significantly."
            )
        
        # Critical limit recommendations
        if meas.dual_cpk.critical_limit == "upper":
            recommendations.append(
                "Upper specification limit is more at risk. "
                "Focus on reducing high-side variation or mean."
            )
        elif meas.dual_cpk.critical_limit == "lower":
            recommendations.append(
                "Lower specification limit is more at risk. "
                "Focus on reducing low-side variation or mean."
            )
        
        # Hidden mode recommendations
        for mode in meas.stability.hidden_modes:
            if mode.severity == "high" and mode.recommendation:
                recommendations.append(mode.recommendation)
        
        # General capability recommendations
        if meas.capability_status == CapabilityStatus.CRITICAL:
            recommendations.append(
                f"CRITICAL: Cpk ({meas.dual_cpk.cpk_all:.2f}) indicates high defect rate. "
                "Immediate process improvement or spec review needed."
            )
        elif meas.capability_status == CapabilityStatus.INCAPABLE:
            recommendations.append(
                "Process improvement required - reduce variation or widen specifications."
            )
        
        return recommendations
    
    def _build_measurement_summary(self, meas: MeasurementCapabilityResult) -> str:
        """Build human-readable summary for a measurement."""
        
        parts = [f"{meas.step_name}"]
        
        if meas.measure_name:
            parts[0] += f" / {meas.measure_name}"
        
        parts.append(f"  Status: {meas.capability_status.value.upper()}")
        
        if meas.dual_cpk.cpk_all is not None:
            cpk_str = f"  Cpk: {meas.dual_cpk.cpk_all:.2f}"
            if meas.dual_cpk.cpk_wof is not None:
                cpk_str += f" (wof: {meas.dual_cpk.cpk_wof:.2f})"
            parts.append(cpk_str)
        
        parts.append(f"  Stability: {meas.stability.status.value}")
        
        if meas.stability.hidden_modes:
            modes = ", ".join(m.mode_type.value for m in meas.stability.hidden_modes[:3])
            parts.append(f"  Issues: {modes}")
        
        return "\n".join(parts)
    
    def _generate_top_recommendations(
        self,
        result: ProcessCapabilityResult
    ) -> List[str]:
        """Generate top-level prioritized recommendations."""
        
        recommendations = []
        
        # 1. Address instability first
        if result.unstable_count > 0:
            recommendations.append(
                f"STABILITY FIRST: {result.unstable_count} measurement(s) show instability. "
                "Stabilize process before focusing on capability improvement."
            )
        
        # 2. Address critical measurements
        if result.critical_count > 0:
            recommendations.append(
                f"CRITICAL: {result.critical_count} measurement(s) have Cpk < 0.67. "
                "These require immediate attention."
            )
        
        # 3. Failure impact
        if result.failure_impacted:
            recommendations.append(
                f"FAILURE IMPACT: {len(result.failure_impacted)} measurement(s) have "
                "capability significantly improved when excluding failures. "
                "Address failure root causes."
            )
        
        # 4. Approaching limits
        if result.approaching_limits:
            recommendations.append(
                f"LIMIT RISK: {len(result.approaching_limits)} measurement(s) are "
                "approaching specification limits."
            )
        
        # 5. Overall capability summary
        if result.avg_cpk_all is not None:
            if result.avg_cpk_all < CPK_MARGINAL:
                recommendations.append(
                    f"OVERALL: Average Cpk is {result.avg_cpk_all:.2f}. "
                    "Process improvement program recommended."
                )
            elif result.avg_cpk_all < CPK_CAPABLE:
                recommendations.append(
                    f"OVERALL: Average Cpk is {result.avg_cpk_all:.2f} (marginal). "
                    "Targeted improvements can reach capable status."
                )
        
        # 6. Positive note if process is good
        if not recommendations:
            recommendations.append(
                "Process capability appears healthy. Continue monitoring for any changes."
            )
        
        return recommendations
    
    def _build_analysis_summary(
        self,
        result: ProcessCapabilityResult,
        filter_input: ProcessCapabilityInput
    ) -> str:
        """Build human-readable analysis summary."""
        
        parts = []
        
        # Header
        parts.append(
            f"Process Capability Analysis: {filter_input.part_number} - "
            f"{filter_input.test_operation} (last {filter_input.days} days)"
        )
        
        # Overall statistics
        parts.append("")
        parts.append("═══ CAPABILITY SUMMARY ═══")
        parts.append(f"• Measurements analyzed: {result.measurements_analyzed}")
        parts.append(
            f"• Capability distribution: "
            f"{result.capable_count} capable, "
            f"{result.marginal_count} marginal, "
            f"{result.incapable_count} incapable, "
            f"{result.critical_count} critical"
        )
        
        if result.avg_cpk_all is not None:
            parts.append(f"• Average Cpk (all): {result.avg_cpk_all:.2f}")
        if result.avg_cpk_wof is not None:
            parts.append(f"• Average Cpk (wof): {result.avg_cpk_wof:.2f}")
        if result.min_cpk_all is not None:
            parts.append(f"• Minimum Cpk: {result.min_cpk_all:.2f}")
        
        # Stability summary
        parts.append("")
        parts.append("═══ STABILITY SUMMARY ═══")
        parts.append(
            f"• {result.stable_count} stable, "
            f"{result.warning_count} warnings, "
            f"{result.unstable_count} unstable"
        )
        
        if result.unstable_count > 0:
            parts.append("⚠️ Unstable processes need stabilization before Cpk is meaningful!")
        
        # Critical measurements
        if result.critical_measurements:
            parts.append("")
            parts.append("═══ CRITICAL MEASUREMENTS ═══")
            for meas in result.critical_measurements[:5]:
                cpk_str = f"Cpk={meas.dual_cpk.cpk_all:.2f}" if meas.dual_cpk.cpk_all else "N/A"
                parts.append(f"  ❌ {meas.step_name}: {cpk_str}")
        
        # Unstable measurements
        if result.unstable_measurements:
            parts.append("")
            parts.append("═══ UNSTABLE MEASUREMENTS ═══")
            for meas in result.unstable_measurements[:5]:
                issues = ", ".join(meas.stability.issues[:2])
                parts.append(f"  ⚠️ {meas.step_name}: {issues}")
        
        # Failure-impacted measurements
        if result.failure_impacted:
            parts.append("")
            parts.append("═══ FAILURE-IMPACTED (Cpk improves without failures) ═══")
            for meas in result.failure_impacted[:5]:
                cpk_all = meas.dual_cpk.cpk_all or 0
                cpk_wof = meas.dual_cpk.cpk_wof or 0
                parts.append(
                    f"  ⚡ {meas.step_name}: "
                    f"{cpk_all:.2f} → {cpk_wof:.2f} (wof)"
                )
        
        # Recommendations
        if result.top_recommendations:
            parts.append("")
            parts.append("═══ TOP RECOMMENDATIONS ═══")
            for i, rec in enumerate(result.top_recommendations, 1):
                parts.append(f"  {i}. {rec}")
        
        return "\n".join(parts)
    
    def _build_no_data_summary(self, filter_input: ProcessCapabilityInput) -> str:
        """Build summary when no data found."""
        
        parts = [
            f"No measurement data found for {filter_input.part_number} - "
            f"{filter_input.test_operation} in the last {filter_input.days} days."
        ]
        
        parts.append("")
        parts.append("Possible reasons:")
        parts.append("• No units tested in the specified time period")
        parts.append("• No measurements with capability data (numeric limits required)")
        
        if filter_input.step_path:
            parts.append(f"• Step path filter '{filter_input.step_path}' may be too restrictive")
        
        return "\n".join(parts)


# =============================================================================
# Tool Definition Export
# =============================================================================

def get_process_capability_tool_definition() -> Dict[str, Any]:
    """Get OpenAI tool definition for process capability analysis."""
    return {
        "name": ProcessCapabilityTool.name,
        "description": ProcessCapabilityTool.description,
        "parameters": ProcessCapabilityTool.get_parameters_schema(),
    }
