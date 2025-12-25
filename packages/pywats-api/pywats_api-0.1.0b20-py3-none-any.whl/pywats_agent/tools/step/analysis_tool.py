"""
Test Step Analysis (TSA) for root cause analysis and process capability.

This module provides comprehensive step-level analysis tools that bridge yield
analysis with detailed root cause investigation. TSA is typically the next step
after yield analysis when investigating quality issues.

TSA WORKFLOW:
1. Yield analysis identifies a problem (low FPY, yield drop)
2. Dimensional analysis may narrow down to specific configurations
3. TSA provides step-by-step visibility into the test sequence
4. Individual step/measurement drill-down for root cause

KEY CONCEPTS:

Test Sequence Consistency:
- TSA typically analyzes ONE product in ONE process at a time
- When multiple SW filenames or revisions are included, sequences may differ
- Different sequences are merged: identical step paths merge, different paths stay separate
- Each step may have different sample counts (not necessarily a problem)
- Data integrity check: Alert user when multiple SW versions or revisions detected

Process Capability (Cp/Cpk):
- Cpk ≥ 1.33: Process is capable (3-sigma coverage)
- Cpk 1.0-1.33: Process is marginally capable, improvement needed
- Cpk < 1.0: Process is NOT capable, immediate action required
- Cp shows potential if centered, Cpk shows actual capability

Statistical Summary Fields:
- cpk: Process capability index (considers both limits and centering)
- cp: Process capability (potential, assumes centered)
- cp_upper/cp_lower: Capability against individual limits
- avg, min, max: Basic measurement statistics
- stdev: Standard deviation (process variation)
- sigma_high_3/sigma_low_3: ±3σ limits for control charts

Step Failure Analysis:
- step_failed_count: Step reported failure
- step_error_count: Step had an error (equipment, system issue)
- step_terminated_count: Test terminated at this step
- step_caused_uut_failed: This step was the CAUSE of unit failure (critical!)
- step_caused_uut_error: This step caused unit error
- step_caused_uut_terminated: This step caused termination

ANALYSIS PRIORITIES:
1. Steps that CAUSE unit failures (step_caused_uut_failed) - highest priority
2. Low Cpk measurements (capability issues)
3. High failure rate steps
4. Timing anomalies (step_time_avg vs expected)

Example:
    >>> from pywats_agent.tools.step_analysis import StepAnalysisTool
    >>> 
    >>> tool = StepAnalysisTool(api)
    >>> result = tool.analyze_with_summary(StepAnalysisInput(
    ...     part_number="PCBA-001",
    ...     test_operation="FCT",
    ...     days=30
    ... ))
    >>> 
    >>> # Result includes:
    >>> # - Data integrity check (SW versions, revisions)
    >>> # - Overall process capability summary
    >>> # - Most problematic steps (by failure impact)
    >>> # - Cpk concerns (measurements needing attention)
    >>> # - Best performing steps
"""

from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

from pydantic import BaseModel, Field

from ...result import AgentResult

if TYPE_CHECKING:
    from pywats import pyWATS
    from pywats.domains.analytics.models import StepAnalysisRow


# =============================================================================
# Process Capability Thresholds
# =============================================================================

class CpkStatus(Enum):
    """Process capability status levels."""
    CAPABLE = "capable"           # Cpk ≥ 1.33
    MARGINAL = "marginal"         # 1.0 ≤ Cpk < 1.33
    INCAPABLE = "incapable"       # Cpk < 1.0
    NO_DATA = "no_data"           # No Cpk available


# Cpk thresholds for classification
CPK_CAPABLE_THRESHOLD = 1.33    # Industry standard for 3-sigma
CPK_MARGINAL_THRESHOLD = 1.0    # Minimum acceptable
CPK_CRITICAL_THRESHOLD = 0.67   # Requires immediate action


# =============================================================================
# Data Integrity Check Result
# =============================================================================

@dataclass
class DataIntegrityResult:
    """Results from checking data integrity before analysis.
    
    When analyzing TSA data, it's important to verify that the data represents
    a consistent test configuration. Multiple SW versions or revisions may
    indicate different test sequences being merged.
    """
    
    is_consistent: bool
    """True if data appears consistent (single SW version, single revision)."""
    
    sw_versions: List[str] = field(default_factory=list)
    """List of unique SW filenames found in the data."""
    
    revisions: List[str] = field(default_factory=list)
    """List of unique product revisions found in the data."""
    
    warning_message: Optional[str] = None
    """Warning message if data inconsistency detected."""
    
    recommendation: Optional[str] = None
    """Suggested action if data is inconsistent."""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_consistent": self.is_consistent,
            "sw_versions": self.sw_versions,
            "revisions": self.revisions,
            "warning_message": self.warning_message,
            "recommendation": self.recommendation,
        }


# =============================================================================
# Step Analysis Summary
# =============================================================================

@dataclass
class StepSummary:
    """Summary of a single step for reporting."""
    
    step_name: str
    step_path: str
    step_type: Optional[str] = None
    step_group: Optional[str] = None
    
    # Execution stats
    total_count: int = 0
    passed_count: int = 0
    failed_count: int = 0
    error_count: int = 0
    
    # Failure impact (CRITICAL)
    caused_unit_fail: int = 0
    caused_unit_error: int = 0
    
    # Pass rate
    pass_rate: float = 0.0
    
    # Capability metrics (for measurements)
    cpk: Optional[float] = None
    cp: Optional[float] = None
    cpk_status: CpkStatus = CpkStatus.NO_DATA
    
    # Measurement stats
    avg: Optional[float] = None
    stdev: Optional[float] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    limit_low: Optional[float] = None
    limit_high: Optional[float] = None
    
    # Timing
    avg_time: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_name": self.step_name,
            "step_path": self.step_path,
            "step_type": self.step_type,
            "step_group": self.step_group,
            "total_count": self.total_count,
            "passed_count": self.passed_count,
            "failed_count": self.failed_count,
            "error_count": self.error_count,
            "caused_unit_fail": self.caused_unit_fail,
            "caused_unit_error": self.caused_unit_error,
            "pass_rate": self.pass_rate,
            "cpk": self.cpk,
            "cp": self.cp,
            "cpk_status": self.cpk_status.value,
            "avg": self.avg,
            "stdev": self.stdev,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "limit_low": self.limit_low,
            "limit_high": self.limit_high,
            "avg_time": self.avg_time,
        }


@dataclass
class OverallProcessSummary:
    """Overall process capability and quality summary."""
    
    total_steps: int = 0
    total_measurements: int = 0
    
    # Capability summary
    capable_count: int = 0          # Cpk ≥ 1.33
    marginal_count: int = 0         # 1.0 ≤ Cpk < 1.33
    incapable_count: int = 0        # Cpk < 1.0
    
    # Averages
    avg_cpk: Optional[float] = None
    min_cpk: Optional[float] = None
    max_cpk: Optional[float] = None
    
    # Failure summary
    total_failures: int = 0
    steps_with_failures: int = 0
    total_caused_unit_fail: int = 0
    
    # Overall pass rate
    overall_pass_rate: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_steps": self.total_steps,
            "total_measurements": self.total_measurements,
            "capable_count": self.capable_count,
            "marginal_count": self.marginal_count,
            "incapable_count": self.incapable_count,
            "avg_cpk": self.avg_cpk,
            "min_cpk": self.min_cpk,
            "max_cpk": self.max_cpk,
            "total_failures": self.total_failures,
            "steps_with_failures": self.steps_with_failures,
            "total_caused_unit_fail": self.total_caused_unit_fail,
            "overall_pass_rate": self.overall_pass_rate,
        }


@dataclass
class TSAResult:
    """Complete Test Step Analysis result."""
    
    # Data integrity
    data_integrity: DataIntegrityResult
    
    # Overall summary
    overall_summary: OverallProcessSummary
    
    # Prioritized findings
    critical_steps: List[StepSummary] = field(default_factory=list)
    """Steps causing unit failures - highest priority."""
    
    cpk_concerns: List[StepSummary] = field(default_factory=list)
    """Measurements with Cpk below threshold."""
    
    high_fail_rate_steps: List[StepSummary] = field(default_factory=list)
    """Steps with high failure rates."""
    
    best_performers: List[StepSummary] = field(default_factory=list)
    """Steps with best Cpk or pass rates."""
    
    # All steps
    all_steps: List[StepSummary] = field(default_factory=list)
    
    # Human-readable summary
    analysis_summary: str = ""
    
    # Recommendations
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "data_integrity": self.data_integrity.to_dict(),
            "overall_summary": self.overall_summary.to_dict(),
            "critical_steps": [s.to_dict() for s in self.critical_steps],
            "cpk_concerns": [s.to_dict() for s in self.cpk_concerns],
            "high_fail_rate_steps": [s.to_dict() for s in self.high_fail_rate_steps],
            "best_performers": [s.to_dict() for s in self.best_performers],
            "all_steps_count": len(self.all_steps),
            "analysis_summary": self.analysis_summary,
            "recommendations": self.recommendations,
        }


# =============================================================================
# Filter Models
# =============================================================================

class StepAnalysisInput(BaseModel):
    """Input filter for step analysis.
    
    TSA is typically used for ONE product in ONE process at a time to ensure
    consistent test sequence analysis. Mixing different sequences can lead
    to confusing results.
    """
    
    part_number: str = Field(
        description="Product part number (REQUIRED). TSA works best with a single product."
    )
    test_operation: str = Field(
        description="Test operation/process name (REQUIRED, e.g., 'FCT', 'EOL', 'ICT')."
    )
    
    # Optional filters
    revision: Optional[str] = Field(
        default=None,
        description=(
            "Product revision to analyze. If not specified, all revisions are included "
            "which may cause sequence merging. Recommended to specify for clean analysis."
        )
    )
    sw_filename: Optional[str] = Field(
        default=None,
        description=(
            "Filter by specific test software. If not specified, all SW versions included "
            "which may merge different test sequences."
        )
    )
    
    # Time range
    days: int = Field(
        default=30,
        description="Number of days to analyze (default: 30)"
    )
    date_from: Optional[datetime] = Field(
        default=None,
        description="Start date (overrides 'days' if specified)"
    )
    date_to: Optional[datetime] = Field(
        default=None,
        description="End date (default: now)"
    )
    
    # Analysis options
    run: int = Field(
        default=1,
        description=(
            "Run number to analyze (default: 1 for first run). "
            "Use run=1 for initial test, run=2+ for retest."
        )
    )
    max_count: int = Field(
        default=10000,
        description="Maximum number of test reports to analyze (default: 10000)"
    )
    
    # Output control
    include_passing: bool = Field(
        default=True,
        description="Include steps that are all passing (useful for completeness)"
    )
    cpk_threshold: float = Field(
        default=CPK_CAPABLE_THRESHOLD,
        description=f"Cpk threshold for flagging concerns (default: {CPK_CAPABLE_THRESHOLD})"
    )
    fail_rate_threshold: float = Field(
        default=5.0,
        description="Failure rate percentage threshold for flagging (default: 5%)"
    )


# =============================================================================
# Step Analysis Tool
# =============================================================================

class StepAnalysisTool:
    """
    Test Step Analysis (TSA) tool for root cause analysis and process capability.
    
    TSA provides step-by-step visibility into the test sequence, enabling:
    - Root cause identification (which steps cause failures)
    - Process capability assessment (Cpk for measurements)
    - Test sequence optimization (timing, failure patterns)
    
    WORKFLOW POSITION:
    ┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌─────────────┐
    │ Yield       │ --> │ Dimensional  │ --> │ TSA /       │ --> │ Measurement │
    │ Analysis    │     │ Analysis     │     │ Step        │     │ Deep Dive   │
    │             │     │ (optional)   │     │ Analysis    │     │             │
    └─────────────┘     └──────────────┘     └─────────────┘     └─────────────┘
         |                    |                    |                    |
    "What's failing?"   "Where/when?"      "Which step?"        "Why exactly?"
    
    IMPORTANT DATA CONSIDERATIONS:
    
    1. Single Product/Process: TSA is designed for ONE product in ONE process.
       Mixing different products or processes results in incompatible sequences.
    
    2. SW Version Consistency: Different SW filenames often mean different test
       sequences. When detected, the tool alerts the user to confirm intent.
    
    3. Revision Consistency: Different revisions may have different test sequences.
       Recommendation: Filter to a specific revision for clean analysis.
    
    4. Sequence Merging: When multiple sequences are included:
       - Identical step paths are merged (statistics combined)
       - Different step paths are kept separate
       - Each step may have different sample counts (OK if understood)
    
    PRIORITY OF FINDINGS:
    
    1. CRITICAL: Steps that cause unit failures (step_caused_uut_failed > 0)
       - These are the root cause of test failures
       - Highest priority for investigation
    
    2. CAPABILITY: Low Cpk measurements (< 1.33 or < 1.0)
       - Process not capable, likely to cause future failures
       - May need process improvement or spec review
    
    3. HIGH FAILURE: Steps with high failure rates (> threshold)
       - Frequently failing but may not be root cause
       - Could be early terminators or verification checks
    
    PROCESS CAPABILITY GUIDE:
    
    | Cpk Value  | Status      | Action                              |
    |------------|-------------|-------------------------------------|
    | ≥ 1.33     | Capable     | Process is good, monitor            |
    | 1.0-1.33   | Marginal    | Improvement needed, prioritize      |
    | 0.67-1.0   | Incapable   | Action required, risk of failures   |
    | < 0.67     | Critical    | URGENT - high defect rate expected  |
    
    Example:
        >>> tool = StepAnalysisTool(api)
        >>> 
        >>> # Basic analysis
        >>> result = tool.analyze(StepAnalysisInput(
        ...     part_number="PCBA-001",
        ...     test_operation="FCT"
        ... ))
        >>> 
        >>> # The result includes:
        >>> # - Data integrity check (multiple SW versions? revisions?)
        >>> # - Overall capability summary (Cpk distribution)
        >>> # - Critical steps (causing failures)
        >>> # - Cpk concerns (measurements needing attention)
        >>> # - Recommendations for next steps
    """
    
    name = "analyze_test_steps_detailed"
    description = """
Perform detailed Test Step Analysis (TSA) for root cause analysis and process capability.

Use this tool when:
- Yield analysis shows problems and you need to find WHICH step is causing them
- You need process capability (Cp/Cpk) analysis for measurements
- Investigating test failures at the step level
- Evaluating test sequence health and optimization opportunities

KEY INFORMATION PROVIDED:

1. DATA INTEGRITY CHECK:
   - Alerts if multiple SW versions or revisions are in the data
   - Different test programs may have different step sequences
   - Recommend filtering to specific version for clean analysis

2. OVERALL CAPABILITY SUMMARY:
   - Distribution of Cpk values across all measurements
   - Average, min, max Cpk for quick assessment
   - Capable/Marginal/Incapable counts

3. CRITICAL STEPS (PRIORITY):
   - Steps that CAUSED unit failures (root cause)
   - These are the most important for investigation
   - Not just "failing steps" but steps that TERMINATE the test

4. CpK CONCERNS:
   - Measurements with Cpk below threshold
   - Process capability issues that may cause future failures
   - Sorted by Cpk (worst first)

5. HIGH FAILURE RATE STEPS:
   - Steps failing frequently
   - May not be root cause but indicate issues
   - Could be verification checks or early terminators

PROCESS CAPABILITY THRESHOLDS:
- Cpk ≥ 1.33: CAPABLE - Process is good
- Cpk 1.0-1.33: MARGINAL - Improvement needed
- Cpk < 1.0: INCAPABLE - Action required

TYPICAL QUESTIONS THIS ANSWERS:
- "Which test steps are causing failures?"
- "What's the Cpk for our measurements?"
- "Is our process capable?"
- "Where should we focus improvement efforts?"
- "Which step is the root cause of failures?"
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
                    "description": "Test operation name (REQUIRED, e.g., 'FCT', 'EOL')"
                },
                "revision": {
                    "type": "string",
                    "description": "Product revision (recommended to specify for clean analysis)"
                },
                "sw_filename": {
                    "type": "string",
                    "description": "Filter to specific test software (prevents sequence merging)"
                },
                "days": {
                    "type": "integer",
                    "description": "Days to analyze (default: 30)",
                    "default": 30
                },
                "run": {
                    "type": "integer",
                    "description": "Run number (default: 1 for first run)",
                    "default": 1
                },
                "cpk_threshold": {
                    "type": "number",
                    "description": "Cpk threshold for concerns (default: 1.33)",
                    "default": 1.33
                },
                "fail_rate_threshold": {
                    "type": "number",
                    "description": "Failure rate % threshold (default: 5)",
                    "default": 5.0
                },
            },
            "required": ["part_number", "test_operation"]
        }
    
    def analyze(self, filter_input: StepAnalysisInput) -> AgentResult:
        """
        Perform comprehensive step analysis.
        
        Args:
            filter_input: Analysis parameters
            
        Returns:
            AgentResult with TSAResult data and summary
        """
        try:
            # Step 1: Check data integrity (SW versions, revisions)
            integrity = self._check_data_integrity(filter_input)
            
            # Step 2: Get step analysis data
            from pywats.domains.report.models import WATSFilter
            
            filter_params = {
                "part_number": filter_input.part_number,
                "test_operation": filter_input.test_operation,
                "run": filter_input.run,
                "max_count": filter_input.max_count,
            }
            
            if filter_input.revision:
                filter_params["revision"] = filter_input.revision
            if filter_input.sw_filename:
                filter_params["sw_filename"] = filter_input.sw_filename
            
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
                    data={"all_steps_count": 0},
                    summary=self._build_no_data_summary(filter_input, integrity),
                    metadata={"data_integrity": integrity.to_dict()}
                )
            
            # Step 3: Process and summarize data
            result = self._analyze_steps(data, filter_input, integrity)
            
            # Step 4: Build summary
            summary = self._build_analysis_summary(result, filter_input)
            
            return AgentResult.ok(
                data=result.to_dict(),
                summary=summary,
                metadata={
                    "total_steps": result.overall_summary.total_steps,
                    "total_measurements": result.overall_summary.total_measurements,
                    "critical_count": len(result.critical_steps),
                    "cpk_concerns_count": len(result.cpk_concerns),
                    "data_integrity_ok": integrity.is_consistent,
                }
            )
            
        except Exception as e:
            return AgentResult.fail(f"Step analysis failed: {str(e)}")
    
    def analyze_from_dict(self, params: Dict[str, Any]) -> AgentResult:
        """Analyze from dictionary parameters (for LLM tool calls)."""
        filter_input = StepAnalysisInput(**params)
        return self.analyze(filter_input)
    
    def _check_data_integrity(
        self,
        filter_input: StepAnalysisInput
    ) -> DataIntegrityResult:
        """
        Check data integrity by looking at SW versions and revisions in the dataset.
        
        This uses dynamic yield with dimensions to quickly get unique values.
        """
        try:
            from pywats.domains.report.models import WATSFilter
            
            # Build filter for integrity check
            filter_params = {
                "part_number": filter_input.part_number,
                "test_operation": filter_input.test_operation,
                "dimensions": "swFilename;revision",
            }
            
            if filter_input.date_from:
                filter_params["date_from"] = filter_input.date_from
            else:
                filter_params["date_from"] = datetime.now() - timedelta(days=filter_input.days)
            
            wats_filter = WATSFilter(**filter_params)
            
            # Get yield data with dimensions
            yield_data = self._api.analytics.get_dynamic_yield(wats_filter)
            
            if not yield_data:
                return DataIntegrityResult(
                    is_consistent=True,
                    warning_message="No data found for integrity check"
                )
            
            # Extract unique values
            sw_versions = set()
            revisions = set()
            
            for record in yield_data:
                sw = getattr(record, 'sw_filename', None) or getattr(record, 'swFilename', None)
                rev = getattr(record, 'revision', None)
                
                if sw:
                    sw_versions.add(sw)
                if rev:
                    revisions.add(str(rev))
            
            sw_list = sorted(sw_versions)
            rev_list = sorted(revisions)
            
            # Determine if consistent
            is_consistent = len(sw_list) <= 1 and len(rev_list) <= 1
            
            warning = None
            recommendation = None
            
            if len(sw_list) > 1:
                warning = (
                    f"⚠️ MULTIPLE TEST PROGRAMS DETECTED: {len(sw_list)} different SW versions found.\n"
                    f"   Software: {', '.join(sw_list)}\n"
                    "   Different programs may have different test sequences."
                )
                recommendation = (
                    "RECOMMENDATION: Filter to a specific sw_filename for accurate step analysis. "
                    "Merging different test sequences may cause confusing results."
                )
            
            if len(rev_list) > 1:
                rev_warning = (
                    f"⚠️ MULTIPLE REVISIONS: {len(rev_list)} product revisions in data.\n"
                    f"   Revisions: {', '.join(rev_list)}"
                )
                if warning:
                    warning += "\n\n" + rev_warning
                else:
                    warning = rev_warning
                
                if not recommendation:
                    recommendation = (
                        "RECOMMENDATION: Filter to a specific revision for consistent analysis."
                    )
            
            return DataIntegrityResult(
                is_consistent=is_consistent,
                sw_versions=sw_list,
                revisions=rev_list,
                warning_message=warning,
                recommendation=recommendation,
            )
            
        except Exception:
            # If integrity check fails, continue without it
            return DataIntegrityResult(
                is_consistent=True,
                warning_message="Could not perform data integrity check"
            )
    
    def _analyze_steps(
        self,
        data: List["StepAnalysisRow"],
        filter_input: StepAnalysisInput,
        integrity: DataIntegrityResult
    ) -> TSAResult:
        """Process step data and create comprehensive analysis result."""
        
        # Initialize result
        result = TSAResult(
            data_integrity=integrity,
            overall_summary=OverallProcessSummary(),
        )
        
        # Track Cpk values for summary
        cpk_values = []
        total_executions = 0
        total_passed = 0
        
        # Process each step
        for row in data:
            summary = self._create_step_summary(row)
            result.all_steps.append(summary)
            
            # Update overall stats
            total_executions += summary.total_count
            total_passed += summary.passed_count
            
            # Track Cpk
            if summary.cpk is not None:
                cpk_values.append(summary.cpk)
                
                if summary.cpk >= CPK_CAPABLE_THRESHOLD:
                    result.overall_summary.capable_count += 1
                elif summary.cpk >= CPK_MARGINAL_THRESHOLD:
                    result.overall_summary.marginal_count += 1
                else:
                    result.overall_summary.incapable_count += 1
            
            # Track failures
            if summary.failed_count > 0:
                result.overall_summary.steps_with_failures += 1
                result.overall_summary.total_failures += summary.failed_count
            
            # Track caused failures
            result.overall_summary.total_caused_unit_fail += summary.caused_unit_fail
        
        # Calculate overall summary
        result.overall_summary.total_steps = len(data)
        result.overall_summary.total_measurements = len(cpk_values)
        
        if total_executions > 0:
            result.overall_summary.overall_pass_rate = (total_passed / total_executions) * 100
        
        if cpk_values:
            result.overall_summary.avg_cpk = sum(cpk_values) / len(cpk_values)
            result.overall_summary.min_cpk = min(cpk_values)
            result.overall_summary.max_cpk = max(cpk_values)
        
        # Categorize steps
        
        # 1. Critical: Steps causing unit failures
        result.critical_steps = sorted(
            [s for s in result.all_steps if s.caused_unit_fail > 0],
            key=lambda x: x.caused_unit_fail,
            reverse=True
        )[:10]  # Top 10
        
        # 2. Cpk concerns: Below threshold
        result.cpk_concerns = sorted(
            [s for s in result.all_steps 
             if s.cpk is not None and s.cpk < filter_input.cpk_threshold],
            key=lambda x: x.cpk or 0
        )[:10]  # Worst 10
        
        # 3. High failure rate
        result.high_fail_rate_steps = sorted(
            [s for s in result.all_steps 
             if s.pass_rate < (100 - filter_input.fail_rate_threshold) and s.total_count >= 10],
            key=lambda x: x.pass_rate
        )[:10]  # Worst 10
        
        # 4. Best performers: High Cpk
        result.best_performers = sorted(
            [s for s in result.all_steps 
             if s.cpk is not None and s.cpk >= CPK_CAPABLE_THRESHOLD],
            key=lambda x: x.cpk or 0,
            reverse=True
        )[:5]  # Top 5
        
        # Generate recommendations
        result.recommendations = self._generate_recommendations(result, filter_input)
        
        return result
    
    def _create_step_summary(self, row: "StepAnalysisRow") -> StepSummary:
        """Create StepSummary from StepAnalysisRow."""
        
        total = row.step_count or 0
        passed = row.step_passed_count or 0
        failed = row.step_failed_count or 0
        errors = row.step_error_count or 0
        
        # Calculate pass rate
        pass_rate = (passed / total * 100) if total > 0 else 0.0
        
        # Determine Cpk status
        cpk = row.cpk
        cpk_status = CpkStatus.NO_DATA
        if cpk is not None:
            if cpk >= CPK_CAPABLE_THRESHOLD:
                cpk_status = CpkStatus.CAPABLE
            elif cpk >= CPK_MARGINAL_THRESHOLD:
                cpk_status = CpkStatus.MARGINAL
            else:
                cpk_status = CpkStatus.INCAPABLE
        
        return StepSummary(
            step_name=row.step_name or "Unknown",
            step_path=row.step_path or "",
            step_type=row.step_type,
            step_group=row.step_group,
            total_count=total,
            passed_count=passed,
            failed_count=failed,
            error_count=errors,
            caused_unit_fail=row.step_caused_uut_failed or 0,
            caused_unit_error=row.step_caused_uut_error or 0,
            pass_rate=pass_rate,
            cpk=cpk,
            cp=row.cp,
            cpk_status=cpk_status,
            avg=row.avg,
            stdev=row.stdev,
            min_value=row.min,
            max_value=row.max,
            limit_low=row.limit1,
            limit_high=row.limit2,
            avg_time=row.step_time_avg,
        )
    
    def _generate_recommendations(
        self,
        result: TSAResult,
        filter_input: StepAnalysisInput
    ) -> List[str]:
        """Generate actionable recommendations based on analysis."""
        
        recommendations = []
        
        # Data integrity recommendations
        if not result.data_integrity.is_consistent:
            if result.data_integrity.recommendation:
                recommendations.append(result.data_integrity.recommendation)
        
        # Critical step recommendations
        if result.critical_steps:
            top_step = result.critical_steps[0]
            recommendations.append(
                f"PRIORITY: Investigate step '{top_step.step_name}' which caused "
                f"{top_step.caused_unit_fail} unit failures. This is the primary root cause."
            )
        
        # Cpk recommendations
        if result.cpk_concerns:
            incapable = [s for s in result.cpk_concerns if s.cpk_status == CpkStatus.INCAPABLE]
            if incapable:
                recommendations.append(
                    f"CAPABILITY: {len(incapable)} measurements have Cpk < 1.0 (incapable). "
                    "These require immediate attention - review test limits or process parameters."
                )
            
            marginal = [s for s in result.cpk_concerns if s.cpk_status == CpkStatus.MARGINAL]
            if marginal:
                recommendations.append(
                    f"IMPROVEMENT: {len(marginal)} measurements have marginal Cpk (1.0-1.33). "
                    "Consider process optimization or tighter control."
                )
        
        # Overall capability
        if result.overall_summary.avg_cpk is not None:
            avg_cpk = result.overall_summary.avg_cpk
            if avg_cpk < CPK_MARGINAL_THRESHOLD:
                recommendations.append(
                    f"OVERALL: Average Cpk is {avg_cpk:.2f} (below 1.0). "
                    "Process needs significant improvement."
                )
            elif avg_cpk < CPK_CAPABLE_THRESHOLD:
                recommendations.append(
                    f"OVERALL: Average Cpk is {avg_cpk:.2f} (marginal). "
                    "Process improvement recommended."
                )
        
        # No issues found
        if not recommendations:
            recommendations.append(
                "Process appears healthy. Monitor for any trending changes."
            )
        
        return recommendations
    
    def _build_analysis_summary(
        self,
        result: TSAResult,
        filter_input: StepAnalysisInput
    ) -> str:
        """Build human-readable summary."""
        
        parts = []
        
        # Header
        parts.append(
            f"Test Step Analysis for {filter_input.part_number} - "
            f"{filter_input.test_operation} (last {filter_input.days} days)"
        )
        
        # Data integrity warning
        if result.data_integrity.warning_message:
            parts.append("")
            parts.append(result.data_integrity.warning_message)
        
        # Overall summary
        summary = result.overall_summary
        parts.append("")
        parts.append("═══ OVERALL SUMMARY ═══")
        parts.append(f"• Total steps: {summary.total_steps}")
        parts.append(f"• Measurements with Cpk: {summary.total_measurements}")
        parts.append(f"• Overall pass rate: {summary.overall_pass_rate:.1f}%")
        
        if summary.avg_cpk is not None:
            parts.append(f"• Average Cpk: {summary.avg_cpk:.2f} (min: {summary.min_cpk:.2f}, max: {summary.max_cpk:.2f})")
            parts.append(
                f"• Capability: {summary.capable_count} capable, "
                f"{summary.marginal_count} marginal, "
                f"{summary.incapable_count} incapable"
            )
        
        if summary.total_caused_unit_fail > 0:
            parts.append(f"• Steps causing unit failures: {summary.total_caused_unit_fail} occurrences")
        
        # Critical steps
        if result.critical_steps:
            parts.append("")
            parts.append("═══ CRITICAL STEPS (Causing Failures) ═══")
            for step in result.critical_steps[:5]:
                parts.append(
                    f"  ❌ {step.step_name}: {step.caused_unit_fail} unit failures "
                    f"({step.pass_rate:.1f}% pass rate)"
                )
        
        # Cpk concerns
        if result.cpk_concerns:
            parts.append("")
            parts.append("═══ CpK CONCERNS ═══")
            for step in result.cpk_concerns[:5]:
                status = "⚠️" if step.cpk_status == CpkStatus.MARGINAL else "❌"
                parts.append(
                    f"  {status} {step.step_name}: Cpk={step.cpk:.2f} "
                    f"(avg={step.avg:.3f}, σ={step.stdev:.3f})"
                )
        
        # Recommendations
        if result.recommendations:
            parts.append("")
            parts.append("═══ RECOMMENDATIONS ═══")
            for i, rec in enumerate(result.recommendations, 1):
                parts.append(f"  {i}. {rec}")
        
        return "\n".join(parts)
    
    def _build_no_data_summary(
        self,
        filter_input: StepAnalysisInput,
        integrity: DataIntegrityResult
    ) -> str:
        """Build summary when no data found."""
        
        parts = [
            f"No step data found for {filter_input.part_number} - "
            f"{filter_input.test_operation} in the last {filter_input.days} days."
        ]
        
        parts.append("")
        parts.append("Possible reasons:")
        parts.append("• No units tested in the specified time period")
        parts.append("• Part number or test operation name may be incorrect")
        
        if filter_input.revision:
            parts.append(f"• Revision filter '{filter_input.revision}' may be too restrictive")
        
        if filter_input.sw_filename:
            parts.append(f"• SW filename filter '{filter_input.sw_filename}' may not match")
        
        if integrity.warning_message:
            parts.append("")
            parts.append(integrity.warning_message)
        
        return "\n".join(parts)


# =============================================================================
# Tool Definition Export
# =============================================================================

def get_step_analysis_tool_definition() -> Dict[str, Any]:
    """Get OpenAI tool definition for step analysis."""
    return {
        "name": StepAnalysisTool.name,
        "description": StepAnalysisTool.description,
        "parameters": StepAnalysisTool.get_parameters_schema(),
    }
