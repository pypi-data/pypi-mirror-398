"""
Dimensional yield analysis for failure mode detection.

This module bridges the gap between high-level yield analysis and detailed
root cause analysis by systematically comparing yields across dimensions.

WORKFLOW:
1. Start with top-level yield (product/process)
2. Use dimensional analysis to find which factors correlate with yield
3. Identify specific configurations that have significantly lower yield
4. Feed those insights into root cause analysis

SUPPORTED DIMENSIONS:
- UUT Header properties: station_name, location, operator, fixture_id, batch_number, etc.
- Software: sw_filename, sw_version
- Product: part_number, revision, product_group, level
- Process: test_operation, process_code
- Time: period (with date_grouping)
- Custom: misc_info properties (if supported by server)

COMMON FAILURE MODE PATTERNS:
- Station-specific: One station has significantly lower yield
- Batch-specific: Certain batches have defect issues (component lot, supplier)
- Operator-specific: Training or technique differences
- Fixture-specific: Fixture wear or calibration issues
- Time-specific: Yield degradation over time (equipment drift)
- Software-specific: Test version differences

Example:
    >>> from pywats_agent.tools.dimensional_analysis import DimensionalAnalysisTool
    >>> 
    >>> tool = DimensionalAnalysisTool(api)
    >>> 
    >>> # Analyze which dimensions affect yield for a product
    >>> result = tool.analyze_failure_modes(
    ...     part_number="WIDGET-001",
    ...     test_operation="FCT",
    ...     days=30
    ... )
    >>> 
    >>> print(result.significant_dimensions)
    >>> # Output: [('station_name', 'Station-3', 0.82, 0.95, -13.7%)]
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
# Configuration
# =============================================================================

# Standard dimensions to analyze for failure modes
# These are the most common factors that affect yield
STANDARD_DIMENSIONS = [
    "stationName",       # Test station - equipment issues
    "operator",          # Operator - training/technique issues
    "fixtureId",         # Fixture - wear/calibration issues
    "batchNumber",       # Batch - component lot issues
    "location",          # Location/line - environment issues
    "swFilename",        # Software - test version issues
    "swVersion",         # Software version
    "period",            # Time - drift over time
]

# Dimension-friendly names for reporting
DIMENSION_DISPLAY_NAMES = {
    "stationName": "Station",
    "operator": "Operator", 
    "fixtureId": "Fixture",
    "batchNumber": "Batch",
    "location": "Location/Line",
    "swFilename": "Test Software",
    "swVersion": "Software Version",
    "period": "Time Period",
    "partNumber": "Product",
    "revision": "Revision",
    "testOperation": "Test Operation",
    "processCode": "Process Code",
    "productGroup": "Product Group",
    "level": "Production Level",
}

# Dimension to YieldData field mapping
DIMENSION_TO_FIELD = {
    "stationName": "station_name",
    "operator": "operator",
    "fixtureId": "fixture_id",
    "batchNumber": "batch_number",
    "location": "location",
    "swFilename": "sw_filename",
    "swVersion": "sw_version",
    "period": "period",
    "partNumber": "part_number",
    "revision": "revision",
    "testOperation": "test_operation",
    "processCode": "process_code",
    "productGroup": "product_group",
    "level": "level",
}


class SignificanceLevel(str, Enum):
    """Statistical significance of yield difference."""
    CRITICAL = "critical"     # >10% below baseline, high confidence
    HIGH = "high"             # 5-10% below baseline
    MODERATE = "moderate"     # 2-5% below baseline
    LOW = "low"               # <2% below baseline
    NOT_SIGNIFICANT = "not_significant"


@dataclass
class DimensionYieldResult:
    """Yield result for a specific dimension value."""
    dimension: str           # e.g., "stationName"
    value: str              # e.g., "Station-3"
    display_name: str       # e.g., "Station"
    
    # Yield metrics
    fpy: float              # First pass yield (%)
    lpy: float              # Last pass yield (%)
    unit_count: int         # Number of units
    
    # Comparison to baseline
    baseline_fpy: float     # Overall FPY for comparison
    fpy_delta: float        # Difference from baseline (%)
    fpy_delta_pct: float    # Relative difference (%)
    
    # Statistical significance
    significance: SignificanceLevel
    confidence: float       # Confidence level (0-1)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "dimension": self.dimension,
            "value": self.value,
            "display_name": self.display_name,
            "fpy": self.fpy,
            "lpy": self.lpy,
            "unit_count": self.unit_count,
            "baseline_fpy": self.baseline_fpy,
            "fpy_delta": self.fpy_delta,
            "fpy_delta_pct": self.fpy_delta_pct,
            "significance": self.significance.value,
            "confidence": self.confidence,
        }


@dataclass
class FailureModeResult:
    """Result from failure mode analysis."""
    
    # Context
    part_number: Optional[str]
    test_operation: Optional[str]
    days: int
    date_from: datetime
    date_to: datetime
    
    # Baseline yield
    baseline_fpy: float
    baseline_lpy: float
    total_units: int
    
    # Significant findings
    significant_dimensions: List[DimensionYieldResult]
    
    # All dimension results (for reference)
    all_results: Dict[str, List[DimensionYieldResult]]
    
    # Analysis summary
    analysis_summary: str
    recommendations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "part_number": self.part_number,
            "test_operation": self.test_operation,
            "days": self.days,
            "date_from": self.date_from.isoformat() if self.date_from else None,
            "date_to": self.date_to.isoformat() if self.date_to else None,
            "baseline_fpy": self.baseline_fpy,
            "baseline_lpy": self.baseline_lpy,
            "total_units": self.total_units,
            "significant_dimensions": [d.to_dict() for d in self.significant_dimensions],
            "analysis_summary": self.analysis_summary,
            "recommendations": self.recommendations,
        }


class FailureModeFilter(BaseModel):
    """Filter for failure mode analysis."""
    
    # Product/Process context
    part_number: Optional[str] = Field(
        default=None,
        description="Product to analyze (recommended)"
    )
    test_operation: Optional[str] = Field(
        default=None,
        description="Test operation/process to analyze (recommended)"
    )
    
    # Time range
    days: int = Field(
        default=30,
        description="Number of days to analyze"
    )
    date_from: Optional[datetime] = Field(
        default=None,
        description="Start date (overrides days)"
    )
    date_to: Optional[datetime] = Field(
        default=None,
        description="End date"
    )
    
    # Analysis configuration
    dimensions: Optional[List[str]] = Field(
        default=None,
        description="""
Dimensions to analyze. If not specified, uses standard dimensions:
stationName, operator, fixtureId, batchNumber, location, swFilename, period
        """
    )
    
    min_units: int = Field(
        default=10,
        description="Minimum units per dimension value to include in analysis"
    )
    
    significance_threshold: float = Field(
        default=2.0,
        description="Minimum FPY delta (%) to consider significant"
    )
    
    include_time_analysis: bool = Field(
        default=True,
        description="Include time-based trend analysis"
    )


class DimensionalAnalysisTool:
    """
    Analyzes yield across dimensions to detect failure modes.
    
    WORKFLOW:
    1. Get baseline yield for the filter (product + process)
    2. Query yield with each dimension individually
    3. Compare each dimension value to baseline
    4. Identify statistically significant deviations
    5. Generate recommendations for root cause investigation
    
    This is the bridge between high-level yield analysis and detailed
    root cause analysis. It answers: "WHAT is causing yield loss?"
    
    Example:
        >>> tool = DimensionalAnalysisTool(api)
        >>> 
        >>> # Find what's affecting yield for WIDGET-001 at FCT
        >>> result = tool.analyze(FailureModeFilter(
        ...     part_number="WIDGET-001",
        ...     test_operation="FCT",
        ...     days=30
        ... ))
        >>> 
        >>> # Check findings
        >>> for dim in result.significant_dimensions:
        ...     print(f"{dim.display_name} '{dim.value}': "
        ...           f"FPY={dim.fpy}% vs baseline {dim.baseline_fpy}% "
        ...           f"({dim.fpy_delta_pct:+.1f}%)")
        >>> 
        >>> # Output:
        >>> # Station 'Station-3': FPY=82% vs baseline 95% (-13.7%)
        >>> # Batch 'BATCH-2024-042': FPY=88% vs baseline 95% (-7.4%)
    """
    
    name = "analyze_failure_modes"
    description = """
Dimensional yield analysis to detect failure modes.

WHEN TO USE THIS TOOL:
- After top-level yield analysis shows a problem
- Before deep root cause analysis
- To answer: "WHAT is causing yield loss?"

WHAT IT DOES:
1. Compares yield across dimensions (station, operator, fixture, batch, etc.)
2. Identifies dimensions that correlate with low yield
3. Highlights specific configurations with significantly lower yield
4. Generates recommendations for root cause investigation

COMMON FINDINGS:
- Station-specific: Equipment issues (calibration, wear)
- Batch-specific: Component issues (lot variation, supplier)
- Operator-specific: Training or technique differences
- Fixture-specific: Fixture wear or contamination
- Time-based: Drift over time (equipment degradation)
- Software-specific: Test version differences

Example questions this tool answers:
- "Why is FCT yield dropping?"
- "Is there a specific station causing failures?"
- "Are certain batches having more problems?"
- "What's different about the failing units?"

WORKFLOW:
1. Use yield_tool to identify overall yield problem
2. Use THIS TOOL to find which factors affect yield
3. Use root_cause_tool to dig into specific failures
"""
    
    def __init__(self, api: "pyWATS"):
        """Initialize with pyWATS instance."""
        self._api = api
    
    def analyze(self, filter_input: FailureModeFilter) -> AgentResult:
        """
        Analyze yield across dimensions to find failure modes.
        
        Args:
            filter_input: Analysis filter with product/process and config
            
        Returns:
            AgentResult with significant findings and recommendations
        """
        try:
            # Set up time range
            date_to = filter_input.date_to or datetime.now()
            if filter_input.date_from:
                date_from = filter_input.date_from
            else:
                date_from = date_to - timedelta(days=filter_input.days)
            
            # Step 1: Get baseline yield
            baseline = self._get_baseline_yield(
                part_number=filter_input.part_number,
                test_operation=filter_input.test_operation,
                date_from=date_from,
                date_to=date_to,
            )
            
            if not baseline:
                return AgentResult.fail(
                    "No data found for the specified filter. "
                    "Check part_number, test_operation, and date range."
                )
            
            baseline_fpy = baseline.get("fpy", 0) or 0
            baseline_lpy = baseline.get("lpy", 0) or 0
            total_units = baseline.get("unit_count", 0) or 0
            
            if total_units < filter_input.min_units:
                return AgentResult.fail(
                    f"Insufficient data: only {total_units} units found. "
                    f"Need at least {filter_input.min_units} for meaningful analysis."
                )
            
            # Step 2: Analyze each dimension
            dimensions = filter_input.dimensions or STANDARD_DIMENSIONS
            all_results: Dict[str, List[DimensionYieldResult]] = {}
            significant_findings: List[DimensionYieldResult] = []
            
            for dimension in dimensions:
                dim_results = self._analyze_dimension(
                    dimension=dimension,
                    part_number=filter_input.part_number,
                    test_operation=filter_input.test_operation,
                    date_from=date_from,
                    date_to=date_to,
                    baseline_fpy=baseline_fpy,
                    min_units=filter_input.min_units,
                    significance_threshold=filter_input.significance_threshold,
                )
                
                if dim_results:
                    all_results[dimension] = dim_results
                    
                    # Collect significant findings
                    for result in dim_results:
                        if result.significance != SignificanceLevel.NOT_SIGNIFICANT:
                            significant_findings.append(result)
            
            # Sort findings by significance and delta
            significant_findings.sort(
                key=lambda x: (
                    0 if x.significance == SignificanceLevel.CRITICAL else
                    1 if x.significance == SignificanceLevel.HIGH else
                    2 if x.significance == SignificanceLevel.MODERATE else 3,
                    x.fpy_delta  # More negative = worse
                )
            )
            
            # Step 3: Generate analysis summary and recommendations
            summary, recommendations = self._generate_analysis(
                significant_findings=significant_findings,
                baseline_fpy=baseline_fpy,
                total_units=total_units,
                part_number=filter_input.part_number,
                test_operation=filter_input.test_operation,
            )
            
            # Build result
            result = FailureModeResult(
                part_number=filter_input.part_number,
                test_operation=filter_input.test_operation,
                days=filter_input.days,
                date_from=date_from,
                date_to=date_to,
                baseline_fpy=baseline_fpy,
                baseline_lpy=baseline_lpy,
                total_units=total_units,
                significant_dimensions=significant_findings,
                all_results=all_results,
                analysis_summary=summary,
                recommendations=recommendations,
            )
            
            return AgentResult.ok(
                data=result.to_dict(),
                summary=summary,
                metadata={
                    "baseline_fpy": baseline_fpy,
                    "total_units": total_units,
                    "dimensions_analyzed": len(all_results),
                    "significant_findings": len(significant_findings),
                }
            )
            
        except Exception as e:
            return AgentResult.fail(f"Dimensional analysis failed: {str(e)}")
    
    def _get_baseline_yield(
        self,
        part_number: Optional[str],
        test_operation: Optional[str],
        date_from: datetime,
        date_to: datetime,
    ) -> Optional[Dict[str, Any]]:
        """Get overall baseline yield for the filter."""
        from pywats.domains.report.models import WATSFilter
        
        filter_params: Dict[str, Any] = {
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
            
            if data:
                # Aggregate if multiple records
                total_units = sum(d.unit_count or 0 for d in data)
                total_fp = sum(d.fp_count or 0 for d in data)
                total_lp = sum(d.lp_count or 0 for d in data)
                
                fpy = (total_fp / total_units * 100) if total_units > 0 else 0
                lpy = (total_lp / total_units * 100) if total_units > 0 else 0
                
                return {
                    "unit_count": total_units,
                    "fpy": fpy,
                    "lpy": lpy,
                    "fp_count": total_fp,
                    "lp_count": total_lp,
                }
            return None
        except Exception:
            return None
    
    def _analyze_dimension(
        self,
        dimension: str,
        part_number: Optional[str],
        test_operation: Optional[str],
        date_from: datetime,
        date_to: datetime,
        baseline_fpy: float,
        min_units: int,
        significance_threshold: float,
    ) -> List[DimensionYieldResult]:
        """Analyze yield for a specific dimension."""
        from pywats.domains.report.models import WATSFilter
        
        filter_params: Dict[str, Any] = {
            "date_from": date_from,
            "date_to": date_to,
            "dimensions": dimension,
        }
        if part_number:
            filter_params["part_number"] = part_number
        if test_operation:
            filter_params["test_operation"] = test_operation
        
        try:
            wats_filter = WATSFilter(**filter_params)
            data = self._api.analytics.get_dynamic_yield(wats_filter)
            
            if not data:
                return []
            
            results = []
            field_name = DIMENSION_TO_FIELD.get(dimension, dimension)
            display_name = DIMENSION_DISPLAY_NAMES.get(dimension, dimension)
            
            for record in data:
                # Get the dimension value
                value = getattr(record, field_name, None)
                if value is None:
                    # Try camelCase version
                    value = getattr(record, dimension, None)
                if value is None:
                    continue
                
                unit_count = record.unit_count or 0
                if unit_count < min_units:
                    continue
                
                # Calculate FPY from counts if available
                fp_count = record.fp_count or 0
                lp_count = record.lp_count or 0
                fpy = (fp_count / unit_count * 100) if unit_count > 0 else (record.fpy or 0)
                lpy = (lp_count / unit_count * 100) if unit_count > 0 else (record.lpy or 0)
                
                # Calculate delta from baseline
                fpy_delta = fpy - baseline_fpy
                fpy_delta_pct = (fpy_delta / baseline_fpy * 100) if baseline_fpy > 0 else 0
                
                # Determine significance
                significance, confidence = self._calculate_significance(
                    fpy_delta=fpy_delta,
                    unit_count=unit_count,
                    significance_threshold=significance_threshold,
                )
                
                results.append(DimensionYieldResult(
                    dimension=dimension,
                    value=str(value),
                    display_name=display_name,
                    fpy=round(fpy, 2),
                    lpy=round(lpy, 2),
                    unit_count=unit_count,
                    baseline_fpy=round(baseline_fpy, 2),
                    fpy_delta=round(fpy_delta, 2),
                    fpy_delta_pct=round(fpy_delta_pct, 2),
                    significance=significance,
                    confidence=round(confidence, 2),
                ))
            
            # Sort by FPY delta (worst first)
            results.sort(key=lambda x: x.fpy_delta)
            
            return results
            
        except Exception:
            return []
    
    def _calculate_significance(
        self,
        fpy_delta: float,
        unit_count: int,
        significance_threshold: float,
    ) -> Tuple[SignificanceLevel, float]:
        """
        Calculate statistical significance of yield difference.
        
        Simple approach based on:
        1. Magnitude of delta (how much worse than baseline)
        2. Sample size (more units = more confidence)
        """
        # Only consider negative deltas (worse than baseline)
        if fpy_delta >= -significance_threshold:
            return SignificanceLevel.NOT_SIGNIFICANT, 0.0
        
        # Confidence based on sample size (simplified)
        # More units = higher confidence
        if unit_count >= 100:
            confidence = 0.95
        elif unit_count >= 50:
            confidence = 0.85
        elif unit_count >= 20:
            confidence = 0.70
        else:
            confidence = 0.50
        
        # Significance level based on delta magnitude
        abs_delta = abs(fpy_delta)
        if abs_delta >= 10.0 and confidence >= 0.70:
            return SignificanceLevel.CRITICAL, confidence
        elif abs_delta >= 5.0 and confidence >= 0.50:
            return SignificanceLevel.HIGH, confidence
        elif abs_delta >= 2.0:
            return SignificanceLevel.MODERATE, confidence
        else:
            return SignificanceLevel.LOW, confidence
    
    def _generate_analysis(
        self,
        significant_findings: List[DimensionYieldResult],
        baseline_fpy: float,
        total_units: int,
        part_number: Optional[str],
        test_operation: Optional[str],
    ) -> Tuple[str, List[str]]:
        """Generate analysis summary and recommendations."""
        
        # Build context string
        context_parts = []
        if part_number:
            context_parts.append(f"Product: {part_number}")
        if test_operation:
            context_parts.append(f"Process: {test_operation}")
        context = ", ".join(context_parts) if context_parts else "All products/processes"
        
        # Summary header
        lines = [
            f"**Dimensional Yield Analysis**",
            f"Context: {context}",
            f"Baseline FPY: {baseline_fpy:.1f}% ({total_units:,} units)",
            "",
        ]
        
        # Significant findings
        if not significant_findings:
            lines.append("No significant yield variations detected across dimensions.")
            lines.append("Yield appears stable across stations, operators, batches, and other factors.")
            return "\n".join(lines), []
        
        lines.append(f"**{len(significant_findings)} Significant Finding(s):**")
        lines.append("")
        
        recommendations = []
        
        # Group findings by significance
        critical = [f for f in significant_findings if f.significance == SignificanceLevel.CRITICAL]
        high = [f for f in significant_findings if f.significance == SignificanceLevel.HIGH]
        moderate = [f for f in significant_findings if f.significance == SignificanceLevel.MODERATE]
        
        if critical:
            lines.append("🔴 **CRITICAL** (>10% below baseline):")
            for f in critical:
                lines.append(f"  - {f.display_name} '{f.value}': FPY={f.fpy}% "
                           f"({f.fpy_delta:+.1f}%, {f.unit_count:,} units)")
                recommendations.append(
                    f"URGENT: Investigate {f.display_name} '{f.value}' - "
                    f"FPY is {abs(f.fpy_delta):.1f}% below baseline"
                )
            lines.append("")
        
        if high:
            lines.append("🟠 **HIGH** (5-10% below baseline):")
            for f in high:
                lines.append(f"  - {f.display_name} '{f.value}': FPY={f.fpy}% "
                           f"({f.fpy_delta:+.1f}%, {f.unit_count:,} units)")
                recommendations.append(
                    f"Review {f.display_name} '{f.value}' for potential issues"
                )
            lines.append("")
        
        if moderate:
            lines.append("🟡 **MODERATE** (2-5% below baseline):")
            for f in moderate[:5]:  # Limit to top 5
                lines.append(f"  - {f.display_name} '{f.value}': FPY={f.fpy}% "
                           f"({f.fpy_delta:+.1f}%, {f.unit_count:,} units)")
            if len(moderate) > 5:
                lines.append(f"  - ... and {len(moderate) - 5} more")
            lines.append("")
        
        # Add dimension-specific recommendations
        dimension_types = set(f.dimension for f in significant_findings[:5])
        
        if "stationName" in dimension_types:
            recommendations.append(
                "Station-specific issue detected: Check equipment calibration, "
                "test fixtures, and environmental conditions"
            )
        if "operator" in dimension_types:
            recommendations.append(
                "Operator-specific issue detected: Review training procedures "
                "and standardize test techniques"
            )
        if "batchNumber" in dimension_types:
            recommendations.append(
                "Batch-specific issue detected: Investigate component lots, "
                "supplier quality, and incoming inspection"
            )
        if "fixtureId" in dimension_types:
            recommendations.append(
                "Fixture-specific issue detected: Check fixture condition, "
                "contact wear, and maintenance schedule"
            )
        if "period" in dimension_types:
            recommendations.append(
                "Time-based trend detected: Monitor for equipment drift, "
                "check preventive maintenance schedule"
            )
        if "swFilename" in dimension_types or "swVersion" in dimension_types:
            recommendations.append(
                "Software-specific issue detected: Compare test versions, "
                "review recent test program changes"
            )
        
        lines.append("**Recommended Actions:**")
        for i, rec in enumerate(recommendations[:5], 1):
            lines.append(f"{i}. {rec}")
        
        return "\n".join(lines), recommendations


def get_dimensional_analysis_tool_definition() -> Dict[str, Any]:
    """Get tool definition for agent registration."""
    return {
        "name": "analyze_failure_modes",
        "description": DimensionalAnalysisTool.description,
        "parameters": {
            "type": "object",
            "properties": {
                "part_number": {
                    "type": "string",
                    "description": "Product part number to analyze"
                },
                "test_operation": {
                    "type": "string",
                    "description": "Test operation/process to analyze"
                },
                "days": {
                    "type": "integer",
                    "description": "Number of days to analyze (default: 30)",
                    "default": 30
                },
                "dimensions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Specific dimensions to analyze (optional)"
                },
                "min_units": {
                    "type": "integer",
                    "description": "Minimum units per dimension value",
                    "default": 10
                },
                "significance_threshold": {
                    "type": "number",
                    "description": "Minimum FPY delta (%) to consider significant",
                    "default": 2.0
                }
            }
        }
    }


# Export
__all__ = [
    "DimensionalAnalysisTool",
    "DimensionYieldResult",
    "FailureModeResult", 
    "FailureModeFilter",
    "SignificanceLevel",
    "STANDARD_DIMENSIONS",
    "get_dimensional_analysis_tool_definition",
]
