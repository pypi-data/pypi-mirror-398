"""
Asset Degradation Analysis Tool for AI agents.

Analyzes how asset quality degrades over calibration cycles. Correlates
yield, Cpk, and failure rate with asset lifecycle (time since calibration,
usage count). Helps fine-tune calibration intervals.

PURPOSE:
An asset that is "healthy" (not overdue for calibration) may still be
degrading in quality. This tool detects if:
- Yield drops as calibration approaches
- Cpk degrades over time
- Failure rates increase with usage

CALIBRATION INTERVAL OPTIMIZATION:
┌─────────────────────────────────────────────────────────────────────────────┐
│ If quality degrades significantly BEFORE calibration is due:                │
│   → Calibration interval is TOO LONG                                        │
│   → Recommendation: Shorten interval                                        │
│                                                                             │
│ If quality remains stable throughout calibration cycle:                     │
│   → Calibration interval may be appropriate or could be extended           │
│   → Recommendation: Maintain or cautiously extend                          │
│                                                                             │
│ If quality degrades early but stabilizes:                                   │
│   → Initial wear, then stable operation                                     │
│   → Recommendation: Investigate break-in period                            │
└─────────────────────────────────────────────────────────────────────────────┘

METHODOLOGY:
1. Get calibration history for the asset
2. For each calibration cycle, divide into time bins (early, mid, late)
3. Calculate quality metrics (yield, Cpk, failure rate) per bin
4. Compare early vs late to measure degradation
5. Average across cycles for statistical validity
6. Generate calibration interval recommendations
"""

from typing import Any, Dict, List, Optional, TYPE_CHECKING
from datetime import datetime, timedelta
from dataclasses import dataclass
import statistics

from ...result import AgentResult
from .models import (
    AssetDegradationFilter,
    AssetDegradationAnalysis,
    CalibrationCycleMetrics,
    DegradationTrend,
)

if TYPE_CHECKING:
    from pywats import pyWATS
    from pywats.domains.asset.models import Asset, AssetLog
    from pywats.domains.analytics.models import YieldData, StepAnalysisRow


# =============================================================================
# Configuration
# =============================================================================

# Cycle time bins
EARLY_CYCLE_PCT = 0.20    # First 20% of cycle = "early"
LATE_CYCLE_PCT = 0.20     # Last 20% of cycle = "late"
# Middle = remaining 60%

# Degradation thresholds
SIGNIFICANT_YIELD_DEGRADATION = 2.0       # 2% yield drop = significant
SIGNIFICANT_CPK_DEGRADATION = 0.10        # 0.10 Cpk drop = significant
SIGNIFICANT_FAILURE_RATE_INCREASE = 0.02  # 2% failure rate increase = significant

# Interval adjustment thresholds
SHORTEN_INTERVAL_THRESHOLD = 3.0   # >3% degradation → shorten
EXTEND_INTERVAL_THRESHOLD = 0.5    # <0.5% degradation → could extend


# =============================================================================
# Asset Degradation Analysis Tool
# =============================================================================

class AssetDegradationTool:
    """
    Analyzes asset quality degradation over calibration cycles.
    
    Correlates quality metrics (yield, Cpk, failure rate) with
    calibration lifecycle to determine if calibration intervals
    are appropriate.
    
    WHEN TO USE:
    - AssetDimensionTool identified an asset as suspect
    - AssetHealthTool shows asset is "healthy" but yield is still low
    - Optimizing calibration intervals based on actual quality data
    - Investigating whether an asset type needs different calibration schedule
    
    OUTPUT:
    - Per-cycle quality metrics (early, mid, late)
    - Degradation trend assessment
    - Calibration interval recommendation
    - Actionable insights
    
    KEY INSIGHT:
    If an asset's quality degrades significantly before its next calibration
    is due, the calibration interval should be shortened. This tool provides
    the data to make that decision objectively.
    """
    
    def __init__(self, api: "pyWATS"):
        """
        Initialize with pyWATS API.
        
        Args:
            api: Authenticated pyWATS API instance
        """
        self._api = api
    
    # =========================================================================
    # Main Entry Point
    # =========================================================================
    
    def analyze(self, filter_input: AssetDegradationFilter) -> AgentResult:
        """
        Analyze asset quality degradation over calibration cycles.
        
        Args:
            filter_input: Analysis parameters
            
        Returns:
            AgentResult with AssetDegradationAnalysis data
        """
        try:
            # Get asset details
            asset = self._api.asset.get_asset_by_serial(filter_input.asset_serial)
            if not asset:
                return AgentResult(
                    success=False,
                    error=f"Asset not found: {filter_input.asset_serial}",
                    summary=f"Could not find asset with serial: {filter_input.asset_serial}"
                )
            
            # Get calibration history from asset logs
            calibration_dates = self._get_calibration_history(asset)
            
            if len(calibration_dates) < 2:
                return AgentResult(
                    success=True,
                    data=AssetDegradationAnalysis(
                        asset_serial=filter_input.asset_serial,
                        asset_name=asset.asset_name,
                        asset_type=asset.asset_type.type_name if asset.asset_type else None,
                        degradation_trend=DegradationTrend.UNKNOWN,
                        cycles=[],
                        insights=["Insufficient calibration history (need at least 2 calibrations)."]
                    ),
                    summary="Insufficient calibration history for degradation analysis.",
                    recommendations=[
                        "Asset needs at least 2 calibration events to analyze degradation.",
                        "Consider monitoring this asset over future calibration cycles."
                    ]
                )
            
            # Analyze each calibration cycle
            cycles = []
            for i in range(min(filter_input.calibration_cycles, len(calibration_dates) - 1)):
                cycle_start = calibration_dates[i]
                cycle_end = calibration_dates[i + 1] if i + 1 < len(calibration_dates) else datetime.utcnow()
                
                cycle_metrics = self._analyze_cycle(
                    asset_serial=filter_input.asset_serial,
                    cycle_number=i + 1,
                    start_date=cycle_start,
                    end_date=cycle_end,
                    part_number=filter_input.part_number,
                    test_operation=filter_input.test_operation,
                    track_cpk=filter_input.track_cpk,
                    track_failure_rate=filter_input.track_failure_rate
                )
                
                if cycle_metrics.unit_count > 0:
                    cycles.append(cycle_metrics)
            
            if not cycles:
                return AgentResult(
                    success=True,
                    data=AssetDegradationAnalysis(
                        asset_serial=filter_input.asset_serial,
                        asset_name=asset.asset_name,
                        asset_type=asset.asset_type.type_name if asset.asset_type else None,
                        degradation_trend=DegradationTrend.UNKNOWN,
                        cycles=[],
                        insights=["No test data found during calibration cycles."]
                    ),
                    summary="No test data found for degradation analysis.",
                    recommendations=[
                        "Verify that test reports reference this asset.",
                        "Check if the asset serial number is correctly recorded in reports."
                    ]
                )
            
            # Calculate overall degradation metrics
            avg_yield_degradation = self._average_degradation(
                [c.yield_degradation for c in cycles if c.yield_degradation is not None]
            )
            avg_cpk_degradation = self._average_degradation(
                [c.cpk_degradation for c in cycles if c.cpk_degradation is not None]
            )
            
            # Determine degradation trend
            trend = self._assess_trend(avg_yield_degradation, avg_cpk_degradation)
            
            # Get calibration interval
            cal_interval = None
            if asset.asset_type and asset.asset_type.calibration_interval:
                cal_interval = asset.asset_type.calibration_interval
            
            # Generate interval recommendation
            recommended_interval, adjustment = self._recommend_interval(
                current_interval=cal_interval,
                avg_degradation=avg_yield_degradation,
                trend=trend
            )
            
            # Build result
            result = AssetDegradationAnalysis(
                asset_serial=filter_input.asset_serial,
                asset_name=asset.asset_name,
                asset_type=asset.asset_type.type_name if asset.asset_type else None,
                degradation_trend=trend,
                avg_yield_degradation_per_cycle=avg_yield_degradation,
                avg_cpk_degradation_per_cycle=avg_cpk_degradation,
                current_interval_days=cal_interval,
                recommended_interval_days=recommended_interval,
                interval_adjustment=adjustment,
                cycles=cycles,
                insights=self._generate_insights(cycles, trend, avg_yield_degradation)
            )
            
            return AgentResult(
                success=True,
                data=result,
                summary=self._build_summary(result),
                recommendations=self._build_recommendations(result)
            )
            
        except Exception as e:
            return AgentResult(
                success=False,
                error=f"Degradation analysis failed: {str(e)}",
                summary=f"Failed to analyze asset degradation: {str(e)}"
            )
    
    # =========================================================================
    # Data Retrieval
    # =========================================================================
    
    def _get_calibration_history(self, asset: "Asset") -> List[datetime]:
        """
        Get calibration dates from asset history.
        
        Returns dates in chronological order (oldest first).
        """
        from pywats.domains.asset.enums import AssetLogType
        
        dates = []
        
        # From asset logs
        if asset.asset_log:
            for log in asset.asset_log:
                # Look for calibration log entries
                if log.log_type == AssetLogType.RESET_COUNT or \
                   (log.comment and 'calibrat' in log.comment.lower()):
                    if log.date:
                        dates.append(log.date)
        
        # Add last calibration date if not in logs
        if asset.last_calibration_date and asset.last_calibration_date not in dates:
            dates.append(asset.last_calibration_date)
        
        # Sort chronologically
        dates.sort()
        
        return dates
    
    def _analyze_cycle(
        self,
        asset_serial: str,
        cycle_number: int,
        start_date: datetime,
        end_date: datetime,
        part_number: Optional[str],
        test_operation: Optional[str],
        track_cpk: bool,
        track_failure_rate: bool
    ) -> CalibrationCycleMetrics:
        """Analyze quality metrics for one calibration cycle."""
        
        # Calculate time bins
        cycle_duration = (end_date - start_date).total_seconds()
        early_end = start_date + timedelta(seconds=cycle_duration * EARLY_CYCLE_PCT)
        late_start = end_date - timedelta(seconds=cycle_duration * LATE_CYCLE_PCT)
        
        # Get yield for each bin
        early_yield = self._get_period_yield(
            asset_serial, start_date, early_end, part_number, test_operation
        )
        mid_yield = self._get_period_yield(
            asset_serial, early_end, late_start, part_number, test_operation
        )
        late_yield = self._get_period_yield(
            asset_serial, late_start, end_date, part_number, test_operation
        )
        
        # Calculate unit count
        unit_count = (
            (early_yield[1] if early_yield else 0) +
            (mid_yield[1] if mid_yield else 0) +
            (late_yield[1] if late_yield else 0)
        )
        
        # Get Cpk if requested
        early_cpk = mid_cpk = late_cpk = None
        if track_cpk:
            early_cpk = self._get_period_cpk(
                asset_serial, start_date, early_end, part_number, test_operation
            )
            mid_cpk = self._get_period_cpk(
                asset_serial, early_end, late_start, part_number, test_operation
            )
            late_cpk = self._get_period_cpk(
                asset_serial, late_start, end_date, part_number, test_operation
            )
        
        # Calculate degradation
        yield_degradation = None
        if early_yield and late_yield and early_yield[0] is not None and late_yield[0] is not None:
            yield_degradation = early_yield[0] - late_yield[0]
        
        cpk_degradation = None
        if early_cpk is not None and late_cpk is not None:
            cpk_degradation = early_cpk - late_cpk
        
        # Failure rate calculation
        early_fr = mid_fr = late_fr = failure_rate_increase = None
        if track_failure_rate:
            if early_yield and early_yield[0] is not None:
                early_fr = (100 - early_yield[0]) / 100
            if mid_yield and mid_yield[0] is not None:
                mid_fr = (100 - mid_yield[0]) / 100
            if late_yield and late_yield[0] is not None:
                late_fr = (100 - late_yield[0]) / 100
            if early_fr is not None and late_fr is not None:
                failure_rate_increase = late_fr - early_fr
        
        return CalibrationCycleMetrics(
            cycle_number=cycle_number,
            calibration_date=start_date,
            next_calibration_date=end_date,
            early_yield_pct=early_yield[0] if early_yield else None,
            mid_yield_pct=mid_yield[0] if mid_yield else None,
            late_yield_pct=late_yield[0] if late_yield else None,
            early_cpk=early_cpk,
            mid_cpk=mid_cpk,
            late_cpk=late_cpk,
            early_failure_rate=early_fr,
            mid_failure_rate=mid_fr,
            late_failure_rate=late_fr,
            yield_degradation=yield_degradation,
            cpk_degradation=cpk_degradation,
            failure_rate_increase=failure_rate_increase,
            unit_count=unit_count
        )
    
    def _get_period_yield(
        self,
        asset_serial: str,
        date_from: datetime,
        date_to: datetime,
        part_number: Optional[str],
        test_operation: Optional[str]
    ) -> Optional[tuple]:
        """
        Get yield for a specific time period.
        
        Returns (yield_pct, unit_count) or None.
        """
        from pywats.domains.report.models import WATSFilter
        
        try:
            # Build filter - include fixture filter
            wats_filter = WATSFilter(
                date_from=date_from,
                date_to=date_to,
                socket=asset_serial  # fixtureId in WATS
            )
            if part_number:
                wats_filter.part_number = part_number
            if test_operation:
                wats_filter.test_operation = test_operation
            
            # Get yield data
            yields = self._api.analytics.get_dynamic_yield(wats_filter)
            
            if not yields:
                return None
            
            # Aggregate
            total_units = sum(y.unit_count or 0 for y in yields)
            if total_units == 0:
                return None
            
            # Weighted average yield
            weighted_sum = sum(
                (y.fpy or 0) * (y.unit_count or 0)
                for y in yields
            )
            avg_yield = weighted_sum / total_units
            
            return (avg_yield, total_units)
            
        except Exception:
            return None
    
    def _get_period_cpk(
        self,
        asset_serial: str,
        date_from: datetime,
        date_to: datetime,
        part_number: Optional[str],
        test_operation: Optional[str]
    ) -> Optional[float]:
        """
        Get average Cpk for a specific time period.
        
        Returns average Cpk or None.
        """
        from pywats.domains.report.models import WATSFilter
        
        try:
            wats_filter = WATSFilter(
                date_from=date_from,
                date_to=date_to,
                socket=asset_serial
            )
            if part_number:
                wats_filter.part_number = part_number
            if test_operation:
                wats_filter.test_operation = test_operation
            
            # Get step analysis for Cpk
            steps = self._api.analytics.get_test_step_analysis(wats_filter)
            
            if not steps:
                return None
            
            # Average Cpk across steps with valid Cpk
            cpks = [s.cpk for s in steps if s.cpk is not None and s.cpk > 0]
            if not cpks:
                return None
            
            return statistics.mean(cpks)
            
        except Exception:
            return None
    
    # =========================================================================
    # Analysis
    # =========================================================================
    
    def _average_degradation(self, values: List[float]) -> Optional[float]:
        """Calculate average degradation across cycles."""
        if not values:
            return None
        return statistics.mean(values)
    
    def _assess_trend(
        self,
        avg_yield_degradation: Optional[float],
        avg_cpk_degradation: Optional[float]
    ) -> DegradationTrend:
        """Assess overall degradation trend."""
        
        if avg_yield_degradation is None and avg_cpk_degradation is None:
            return DegradationTrend.UNKNOWN
        
        # Use yield degradation as primary indicator
        if avg_yield_degradation is not None:
            if avg_yield_degradation > SIGNIFICANT_YIELD_DEGRADATION:
                return DegradationTrend.DEGRADING
            elif avg_yield_degradation < -SIGNIFICANT_YIELD_DEGRADATION:
                return DegradationTrend.IMPROVING  # Negative = improving
            else:
                return DegradationTrend.STABLE
        
        # Fall back to Cpk
        if avg_cpk_degradation is not None:
            if avg_cpk_degradation > SIGNIFICANT_CPK_DEGRADATION:
                return DegradationTrend.DEGRADING
            elif avg_cpk_degradation < -SIGNIFICANT_CPK_DEGRADATION:
                return DegradationTrend.IMPROVING
            else:
                return DegradationTrend.STABLE
        
        return DegradationTrend.UNKNOWN
    
    def _recommend_interval(
        self,
        current_interval: Optional[float],
        avg_degradation: Optional[float],
        trend: DegradationTrend
    ) -> tuple:
        """
        Generate calibration interval recommendation.
        
        Returns (recommended_interval, adjustment_type)
        """
        if current_interval is None or avg_degradation is None:
            return (None, None)
        
        if trend == DegradationTrend.DEGRADING:
            if avg_degradation > SHORTEN_INTERVAL_THRESHOLD:
                # Significant degradation - reduce interval by ~20%
                recommended = current_interval * 0.80
                return (round(recommended), "shorten")
            else:
                # Moderate degradation - reduce by ~10%
                recommended = current_interval * 0.90
                return (round(recommended), "shorten_slightly")
        
        elif trend == DegradationTrend.STABLE:
            if avg_degradation < EXTEND_INTERVAL_THRESHOLD:
                # Very stable - could extend by ~10%
                recommended = current_interval * 1.10
                return (round(recommended), "extend")
            else:
                return (current_interval, "maintain")
        
        elif trend == DegradationTrend.IMPROVING:
            # Unusual - quality improves over time (maybe burn-in effect)
            return (current_interval, "maintain")
        
        return (current_interval, "maintain")
    
    def _generate_insights(
        self,
        cycles: List[CalibrationCycleMetrics],
        trend: DegradationTrend,
        avg_degradation: Optional[float]
    ) -> List[str]:
        """Generate human-readable insights."""
        insights = []
        
        # Trend insight
        if trend == DegradationTrend.DEGRADING:
            insights.append(
                f"Quality DEGRADES over calibration cycles. "
                f"Average yield drop: {avg_degradation:.1f}% per cycle."
            )
        elif trend == DegradationTrend.STABLE:
            insights.append(
                "Quality remains STABLE throughout calibration cycles. "
                "Current calibration interval appears appropriate."
            )
        elif trend == DegradationTrend.IMPROVING:
            insights.append(
                "Quality IMPROVES over calibration cycles. "
                "This may indicate a burn-in effect or data anomaly."
            )
        
        # Per-cycle insights
        for cycle in cycles:
            if cycle.yield_degradation is not None and cycle.yield_degradation > 3:
                insights.append(
                    f"Cycle {cycle.cycle_number}: Significant yield drop from "
                    f"{cycle.early_yield_pct:.1f}% to {cycle.late_yield_pct:.1f}% "
                    f"({cycle.yield_degradation:.1f}% degradation)"
                )
        
        return insights
    
    # =========================================================================
    # Reporting
    # =========================================================================
    
    def _build_summary(self, result: AssetDegradationAnalysis) -> str:
        """Build human-readable summary."""
        parts = [f"Asset {result.asset_serial}:"]
        
        parts.append(f"{result.degradation_trend.value} trend")
        
        if result.avg_yield_degradation_per_cycle is not None:
            parts.append(f"({result.avg_yield_degradation_per_cycle:.1f}% avg yield drop/cycle)")
        
        if result.interval_adjustment:
            parts.append(f"Recommendation: {result.interval_adjustment} calibration interval")
        
        return " ".join(parts)
    
    def _build_recommendations(self, result: AssetDegradationAnalysis) -> List[str]:
        """Build actionable recommendations."""
        recommendations = []
        
        if result.interval_adjustment == "shorten":
            recommendations.append(
                f"SHORTEN calibration interval. Current: {result.current_interval_days} days → "
                f"Recommended: {result.recommended_interval_days} days"
            )
            recommendations.append(
                "Quality is degrading significantly before calibration is due."
            )
        
        elif result.interval_adjustment == "shorten_slightly":
            recommendations.append(
                f"Consider shortening calibration interval slightly. "
                f"Current: {result.current_interval_days} days → "
                f"Recommended: {result.recommended_interval_days} days"
            )
        
        elif result.interval_adjustment == "extend":
            recommendations.append(
                f"Calibration interval could potentially be extended. "
                f"Current: {result.current_interval_days} days → "
                f"Recommended: {result.recommended_interval_days} days"
            )
            recommendations.append(
                "Quality remains stable throughout calibration cycle. "
                "Extend cautiously and monitor."
            )
        
        elif result.interval_adjustment == "maintain":
            recommendations.append(
                f"Maintain current calibration interval ({result.current_interval_days} days)."
            )
        
        if result.degradation_trend == DegradationTrend.UNKNOWN:
            recommendations.append(
                "Insufficient data for reliable degradation analysis. "
                "Continue monitoring over more calibration cycles."
            )
        
        return recommendations


# =============================================================================
# Tool Definition for Agent Integration
# =============================================================================

def get_asset_degradation_tool_definition() -> Dict[str, Any]:
    """Get the tool definition for agent registration."""
    return {
        "name": "asset_degradation_analysis",
        "description": (
            "Analyze how asset quality degrades over calibration cycles. "
            "Correlates yield and Cpk with calibration lifecycle to determine "
            "if calibration intervals are appropriate. Use when optimizing "
            "calibration schedules or investigating why a 'healthy' asset has "
            "yield problems."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "asset_serial": {
                    "type": "string",
                    "description": "Asset serial number to analyze (required)"
                },
                "calibration_cycles": {
                    "type": "integer",
                    "description": "Number of calibration cycles to analyze (default: 3)"
                },
                "track_cpk": {
                    "type": "boolean",
                    "description": "Track Cpk trend over calibration cycle (default: true)"
                },
                "track_failure_rate": {
                    "type": "boolean",
                    "description": "Track failure rate trend (default: true)"
                },
                "part_number": {
                    "type": "string",
                    "description": "Limit analysis to specific product"
                },
                "test_operation": {
                    "type": "string",
                    "description": "Limit analysis to specific test operation"
                }
            },
            "required": ["asset_serial"]
        }
    }
