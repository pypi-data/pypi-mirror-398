"""
Asset Dimension Analysis Tool for AI agents.

Analyzes assets (fixtures, stations, probe cards) as failure mode dimensions.
When an asset shows statistically lower yield than peers, it becomes a
root cause suspect that may need calibration or maintenance.

WORKFLOW:
1. Query yield grouped by fixtureId/stationName dimension
2. Calculate baseline yield (overall or peer average)
3. Flag assets that deviate significantly from baseline
4. Rank suspects by impact level and confidence
5. Correlate with failing test steps for context

INTEGRATION WITH ROOT CAUSE ANALYSIS:
┌─────────────────────────────────────────────────────────────────────────────┐
│ Asset analysis is ONE DIMENSION of multi-dimensional root cause analysis.  │
│                                                                             │
│ When DimensionalAnalysisTool shows fixtureId/stationName as significant:   │
│   → Use AssetDimensionTool for deeper asset-specific analysis              │
│   → Use AssetHealthTool to check calibration/maintenance status            │
│   → Use AssetDegradationTool to analyze quality trends over time           │
└─────────────────────────────────────────────────────────────────────────────┘
"""

from typing import Any, Dict, List, Optional, TYPE_CHECKING
from datetime import datetime, timedelta
from dataclasses import dataclass
import statistics

from ...result import AgentResult
from .models import (
    AssetDimensionFilter,
    AssetDimensionResult,
    AssetYieldImpact,
    AssetImpactLevel,
)

if TYPE_CHECKING:
    from pywats import pyWATS
    from pywats.domains.analytics.models import YieldData


# =============================================================================
# Configuration
# =============================================================================

# Impact level thresholds (yield delta percentage)
IMPACT_CRITICAL_THRESHOLD = 0.10    # >10% below baseline
IMPACT_HIGH_THRESHOLD = 0.05        # 5-10% below baseline
IMPACT_MODERATE_THRESHOLD = 0.02    # 2-5% below baseline

# Statistical significance
MIN_CONFIDENCE = 0.80               # Minimum confidence to flag as suspect


# =============================================================================
# Asset Dimension Analysis Tool
# =============================================================================

class AssetDimensionTool:
    """
    Analyzes assets as failure mode dimensions.
    
    Use this tool to identify which fixtures, stations, or other assets
    are correlated with yield problems. Assets with statistically lower
    yield than peers become root cause suspects.
    
    WHEN TO USE:
    - DimensionalAnalysisTool flagged fixtureId or stationName as significant
    - Investigating fixture/station-specific quality problems
    - Correlating yield issues with specific test equipment
    - Prioritizing calibration/maintenance based on quality impact
    
    OUTPUT:
    - Ranked list of suspect assets with yield impact
    - Confidence scores for statistical significance
    - Top failing steps per asset for context
    
    NEXT STEPS:
    - For suspect assets → AssetHealthTool to check calibration status
    - For assets with degradation → AssetDegradationTool for trend analysis
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
    
    def analyze(self, filter_input: AssetDimensionFilter) -> AgentResult:
        """
        Analyze assets as a failure mode dimension.
        
        Identifies which assets (fixtures, stations) have lower yield
        than their peers, indicating potential root causes.
        
        Args:
            filter_input: Analysis parameters
            
        Returns:
            AgentResult with AssetDimensionResult data
        """
        try:
            # Resolve date range
            date_to = filter_input.date_to or datetime.utcnow()
            if filter_input.date_from:
                date_from = filter_input.date_from
            else:
                date_from = date_to - timedelta(days=filter_input.days)
            
            # Get yield by fixture dimension
            yield_by_fixture = self._get_yield_by_asset(
                part_number=filter_input.part_number,
                test_operation=filter_input.test_operation,
                date_from=date_from,
                date_to=date_to,
                dimension="fixtureId"
            )
            
            # Also get yield by station if fixture data is sparse
            yield_by_station = self._get_yield_by_asset(
                part_number=filter_input.part_number,
                test_operation=filter_input.test_operation,
                date_from=date_from,
                date_to=date_to,
                dimension="stationName"
            )
            
            # Combine results (prefer fixture if available)
            asset_yields = self._merge_asset_yields(
                yield_by_fixture, 
                yield_by_station,
                filter_input.min_unit_count
            )
            
            if not asset_yields:
                return AgentResult(
                    success=True,
                    data=AssetDimensionResult(
                        part_number=filter_input.part_number,
                        test_operation=filter_input.test_operation,
                        date_from=date_from,
                        date_to=date_to,
                        total_units=0,
                        overall_yield_pct=0.0,
                        assets_analyzed=0,
                        summary="No asset data found for this product/process."
                    ),
                    summary="No asset data found for analysis.",
                    recommendations=["Verify that test reports include asset (fixture/station) information."]
                )
            
            # Calculate baseline yield
            total_units, overall_yield = self._calculate_baseline(asset_yields)
            
            # Analyze each asset
            all_assets: List[AssetYieldImpact] = []
            for asset_id, (units, yield_pct, asset_type) in asset_yields.items():
                impact = self._assess_asset_impact(
                    asset_id=asset_id,
                    asset_type=asset_type,
                    units=units,
                    yield_pct=yield_pct,
                    baseline_yield=overall_yield,
                    threshold=filter_input.significance_threshold
                )
                all_assets.append(impact)
            
            # Sort by impact (worst first)
            all_assets.sort(key=lambda x: x.yield_delta)
            
            # Identify suspects
            suspects = [a for a in all_assets if a.is_suspect]
            
            # Build result
            result = AssetDimensionResult(
                part_number=filter_input.part_number,
                test_operation=filter_input.test_operation,
                date_from=date_from,
                date_to=date_to,
                total_units=total_units,
                overall_yield_pct=overall_yield,
                assets_analyzed=len(all_assets),
                suspect_assets=suspects,
                all_assets=all_assets,
                summary=self._build_summary(suspects, all_assets, overall_yield)
            )
            
            return AgentResult(
                success=True,
                data=result,
                summary=result.summary,
                recommendations=self._build_recommendations(suspects)
            )
            
        except Exception as e:
            return AgentResult(
                success=False,
                error=f"Asset dimension analysis failed: {str(e)}",
                summary=f"Failed to analyze assets: {str(e)}"
            )
    
    # =========================================================================
    # Data Retrieval
    # =========================================================================
    
    def _get_yield_by_asset(
        self,
        part_number: str,
        test_operation: str,
        date_from: datetime,
        date_to: datetime,
        dimension: str  # "fixtureId" or "stationName"
    ) -> List["YieldData"]:
        """Get yield data grouped by asset dimension."""
        from pywats.domains.report.models import WATSFilter
        
        wats_filter = WATSFilter(
            part_number=part_number,
            test_operation=test_operation,
            date_from=date_from,
            date_to=date_to,
            dimensions=dimension
        )
        
        return self._api.analytics.get_dynamic_yield(wats_filter)
    
    def _merge_asset_yields(
        self,
        fixture_yields: List["YieldData"],
        station_yields: List["YieldData"],
        min_units: int
    ) -> Dict[str, tuple]:
        """
        Merge fixture and station yield data.
        
        Returns dict: asset_id -> (unit_count, yield_pct, asset_type)
        """
        result = {}
        
        # Process fixture data
        for yd in fixture_yields:
            fixture_id = getattr(yd, 'fixture_id', None)
            if fixture_id and yd.unit_count and yd.unit_count >= min_units:
                fpy = yd.fpy if yd.fpy is not None else 0.0
                result[f"fixture:{fixture_id}"] = (yd.unit_count, fpy, "fixture")
        
        # Process station data (only if no fixture data or supplementary)
        for yd in station_yields:
            station_name = getattr(yd, 'station_name', None)
            if station_name and yd.unit_count and yd.unit_count >= min_units:
                fpy = yd.fpy if yd.fpy is not None else 0.0
                key = f"station:{station_name}"
                if key not in result:  # Don't overwrite fixture data
                    result[key] = (yd.unit_count, fpy, "station")
        
        return result
    
    def _calculate_baseline(
        self,
        asset_yields: Dict[str, tuple]
    ) -> tuple:
        """
        Calculate baseline yield.
        
        Returns (total_units, weighted_average_yield)
        """
        total_units = sum(units for units, _, _ in asset_yields.values())
        
        if total_units == 0:
            return 0, 0.0
        
        # Weighted average yield
        weighted_sum = sum(
            units * yield_pct 
            for units, yield_pct, _ in asset_yields.values()
        )
        avg_yield = weighted_sum / total_units
        
        return total_units, avg_yield
    
    # =========================================================================
    # Analysis
    # =========================================================================
    
    def _assess_asset_impact(
        self,
        asset_id: str,
        asset_type: str,
        units: int,
        yield_pct: float,
        baseline_yield: float,
        threshold: float
    ) -> AssetYieldImpact:
        """Assess the yield impact of a single asset."""
        
        # Calculate yield delta
        yield_delta = yield_pct - baseline_yield
        yield_delta_pct = yield_delta / 100.0 if baseline_yield else 0
        
        # Determine impact level
        abs_delta = abs(yield_delta_pct)
        if abs_delta >= IMPACT_CRITICAL_THRESHOLD:
            impact_level = AssetImpactLevel.CRITICAL
        elif abs_delta >= IMPACT_HIGH_THRESHOLD:
            impact_level = AssetImpactLevel.HIGH
        elif abs_delta >= IMPACT_MODERATE_THRESHOLD:
            impact_level = AssetImpactLevel.MODERATE
        elif abs_delta > 0.01:
            impact_level = AssetImpactLevel.LOW
        else:
            impact_level = AssetImpactLevel.NONE
        
        # Calculate confidence based on sample size
        # Using a simple heuristic: more units = higher confidence
        confidence = min(1.0, units / 100.0)  # 100 units = 100% confidence
        
        # Is this a suspect? (worse than baseline by threshold amount, with confidence)
        is_suspect = (
            yield_delta < 0 and 
            abs_delta >= threshold and 
            confidence >= MIN_CONFIDENCE
        )
        
        # Parse asset ID
        parts = asset_id.split(":", 1)
        serial = parts[1] if len(parts) > 1 else asset_id
        
        # Estimate failure count
        failure_count = int(units * (100 - yield_pct) / 100)
        
        return AssetYieldImpact(
            asset_serial=serial,
            asset_name=None,  # Could be enriched from asset service
            asset_type=asset_type,
            unit_count=units,
            yield_pct=yield_pct,
            baseline_yield_pct=baseline_yield,
            yield_delta=yield_delta,
            impact_level=impact_level,
            is_suspect=is_suspect,
            confidence=confidence,
            failure_count=failure_count,
            top_failing_steps=[]  # Could be enriched with step analysis
        )
    
    # =========================================================================
    # Reporting
    # =========================================================================
    
    def _build_summary(
        self,
        suspects: List[AssetYieldImpact],
        all_assets: List[AssetYieldImpact],
        baseline_yield: float
    ) -> str:
        """Build human-readable summary."""
        if not suspects:
            return (
                f"Analyzed {len(all_assets)} assets. "
                f"No significant asset-related yield deviations found. "
                f"Baseline yield: {baseline_yield:.1f}%"
            )
        
        worst = suspects[0]
        return (
            f"Analyzed {len(all_assets)} assets. "
            f"Found {len(suspects)} suspect(s) with lower-than-baseline yield. "
            f"Worst: {worst.asset_serial} ({worst.asset_type}) at {worst.yield_pct:.1f}% "
            f"({worst.yield_delta:+.1f}% vs {baseline_yield:.1f}% baseline)"
        )
    
    def _build_recommendations(
        self,
        suspects: List[AssetYieldImpact]
    ) -> List[str]:
        """Build actionable recommendations."""
        recommendations = []
        
        if not suspects:
            recommendations.append(
                "Asset dimension shows no significant suspects. "
                "Consider analyzing other dimensions (operator, batch, time period)."
            )
            return recommendations
        
        # Group by impact level
        critical = [s for s in suspects if s.impact_level == AssetImpactLevel.CRITICAL]
        high = [s for s in suspects if s.impact_level == AssetImpactLevel.HIGH]
        
        if critical:
            recommendations.append(
                f"CRITICAL: {len(critical)} asset(s) with >10% yield impact. "
                f"Check calibration and maintenance status immediately."
            )
            for asset in critical[:3]:  # Top 3
                recommendations.append(
                    f"  → {asset.asset_serial}: {asset.yield_pct:.1f}% yield "
                    f"({asset.failure_count} failures). Use AssetHealthTool to check status."
                )
        
        if high:
            recommendations.append(
                f"HIGH: {len(high)} asset(s) with 5-10% yield impact. "
                f"Schedule for inspection."
            )
        
        if suspects:
            recommendations.append(
                "Use AssetHealthTool to check calibration/maintenance status of suspect assets."
            )
            recommendations.append(
                "Use AssetDegradationTool to analyze if quality is degrading over time."
            )
        
        return recommendations


# =============================================================================
# Tool Definition for Agent Integration
# =============================================================================

def get_asset_dimension_tool_definition() -> Dict[str, Any]:
    """Get the tool definition for agent registration."""
    return {
        "name": "asset_dimension_analysis",
        "description": (
            "Analyze assets (fixtures, stations) as failure mode dimensions. "
            "Identifies which test equipment correlates with yield problems. "
            "Use when investigating equipment-related quality issues or when "
            "DimensionalAnalysisTool flagged fixtureId/stationName as significant."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "part_number": {
                    "type": "string",
                    "description": "Product part number to analyze (required)"
                },
                "test_operation": {
                    "type": "string",
                    "description": "Test operation/process (required, e.g., 'FCT', 'EOL')"
                },
                "days": {
                    "type": "integer",
                    "description": "Number of days to analyze (default: 30)"
                },
                "min_unit_count": {
                    "type": "integer",
                    "description": "Minimum units per asset for validity (default: 30)"
                },
                "significance_threshold": {
                    "type": "number",
                    "description": "Yield difference threshold to flag (default: 0.02 = 2%)"
                }
            },
            "required": ["part_number", "test_operation"]
        }
    }
