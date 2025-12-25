"""
Yield Trend Analysis Tool.

Analyzes yield changes over time with intelligent insight generation.
Returns token-efficient summaries, not raw data.

Features:
- Automatic granularity selection (day/week/month)
- Trend direction detection (improving/stable/declining/volatile)
- Change point identification
- Session-based caching for drill-downs
- Sticky filter context inheritance

Usage:
    tool = YieldTrendTool(api)
    result = tool.analyze(
        part_number="WIDGET-001",
        test_operation="FCT",
        granularity="day",
        lookback_periods=14
    )
"""

from typing import Any, Dict, List, Optional, TYPE_CHECKING
from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict

from ...result import AgentResult

if TYPE_CHECKING:
    from pywats import pyWATS


class TimeGranularity(str, Enum):
    """Time period granularity for trend analysis."""
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"


# Mapping to WATS date_grouping values
GRANULARITY_TO_DATE_GROUPING = {
    TimeGranularity.HOUR: "HOUR",
    TimeGranularity.DAY: "DAY",
    TimeGranularity.WEEK: "WEEK",
    TimeGranularity.MONTH: "MONTH",
    TimeGranularity.QUARTER: "QUARTER",
}


class TrendInput(BaseModel):
    """Input parameters for trend analysis."""
    model_config = ConfigDict(use_enum_values=True)
    
    # Filter parameters (can inherit from context)
    part_number: Optional[str] = Field(
        default=None,
        description="Product part number to analyze"
    )
    test_operation: Optional[str] = Field(
        default=None,
        description="Test operation/process to analyze (e.g., 'FCT', 'EOL')"
    )
    station_name: Optional[str] = Field(
        default=None,
        description="Filter to specific test station"
    )
    product_group: Optional[str] = Field(
        default=None,
        description="Filter to product group"
    )
    
    # Trend-specific parameters
    granularity: TimeGranularity = Field(
        default=TimeGranularity.DAY,
        description="Time granularity: hour, day, week, month, quarter"
    )
    lookback_periods: int = Field(
        default=14,
        description="Number of periods to analyze (default: 14 days/weeks/etc.)",
        ge=2,
        le=90
    )
    
    # Optional: reuse existing session
    session_id: Optional[str] = Field(
        default=None,
        description="Session ID to reuse cached data (for drill-downs)"
    )
    
    # Metric selection
    metric: str = Field(
        default="fpy",
        description="Yield metric to analyze: 'fpy', 'lpy', 'try'"
    )


class YieldTrendTool:
    """
    Intelligent yield trend analysis tool.
    
    Analyzes how yield is changing over time:
    - Detects trend direction (improving, stable, declining, volatile)
    - Calculates rate of change
    - Identifies change points (sudden shifts)
    - Caches data for efficient drill-downs
    
    Returns token-efficient summaries with actionable insights.
    
    TEMPORAL ANALYSIS GUIDE:
    
    GRANULARITY SELECTION:
    - HOUR: For real-time monitoring of high-volume lines
    - DAY: Standard analysis, good for 2-4 week lookbacks
    - WEEK: For longer-term trends, good for 2-3 month lookbacks
    - MONTH: For strategic analysis, quarterly/yearly views
    
    INTERPRETATION:
    - IMPROVING: Yield increasing over time (positive slope)
    - DECLINING: Yield decreasing over time (negative slope)
    - STABLE: No significant change (slope near zero)
    - VOLATILE: High variability makes trend unreliable
    
    Example:
        >>> tool = YieldTrendTool(api)
        >>> 
        >>> # Basic trend analysis
        >>> result = tool.analyze(TrendInput(
        ...     part_number="WIDGET-001",
        ...     test_operation="FCT",
        ...     granularity="day",
        ...     lookback_periods=14
        ... ))
        >>> print(result.summary)
        "Yield is declining at -1.8% per week. Current: 94.2% (from 97.5%)"
        >>> 
        >>> # Drill into specific period
        >>> detail = tool.get_period_detail(
        ...     session_id=result.data["session_id"],
        ...     period="2024-12-15"
        ... )
    """
    
    name = "analyze_yield_trend"
    description = """
Analyze yield changes over time with intelligent insights.

⚠️ SPECIALIZED TOOL - Consider using analyze_yield with perspective="trend" first!
Use this tool when you need DETAILED trend analysis with:
- Change point detection (when did shifts occur?)
- Trend classification (improving/declining/volatile)
- Rate of change calculations
- Session-based drill-downs

For simple "show me yield over time", use analyze_yield with perspective="daily/weekly".

Returns:
- Trend direction (improving/stable/declining/volatile)
- Rate of change (e.g., "-1.8% per week")
- Change points (dates where significant shifts occurred)
- Actionable insights

GRANULARITY OPTIONS:
- hour: Real-time, for today's data
- day: Standard, for 1-4 week analysis
- week: Medium-term, for 1-3 month analysis
- month: Long-term, for quarterly/yearly analysis

WHEN TO USE:
- "Is yield improving or getting worse?"
- "Show me the yield trend for the past 2 weeks"
- "When did yield start dropping?"
- "Is the yield stable or fluctuating?"

INHERITS CONTEXT:
This tool inherits filter context from previous queries. If you already
asked about WIDGET-001/FCT, you can ask "show me the trend" without
repeating the filters.
"""
    
    def __init__(self, api: "pyWATS"):
        """Initialize with a pyWATS instance."""
        self._api = api
        self._process_resolver = None
    
    def _get_process_resolver(self):
        """Get process resolver (lazy-loaded)."""
        if self._process_resolver is None:
            from ..shared.process_resolver import ProcessResolver
            self._process_resolver = ProcessResolver(self._api)
        return self._process_resolver
    
    @staticmethod
    def get_parameters_schema() -> Dict[str, Any]:
        """Get OpenAI-compatible parameter schema."""
        return {
            "type": "object",
            "properties": {
                "part_number": {
                    "type": "string",
                    "description": "Product part number to analyze"
                },
                "test_operation": {
                    "type": "string",
                    "description": "Test operation to analyze (e.g., 'FCT', 'EOL', 'PCBA')"
                },
                "station_name": {
                    "type": "string",
                    "description": "Filter to specific test station"
                },
                "product_group": {
                    "type": "string",
                    "description": "Filter to product group"
                },
                "granularity": {
                    "type": "string",
                    "enum": ["hour", "day", "week", "month", "quarter"],
                    "default": "day",
                    "description": "Time period granularity"
                },
                "lookback_periods": {
                    "type": "integer",
                    "default": 14,
                    "minimum": 2,
                    "maximum": 90,
                    "description": "Number of periods to analyze"
                },
                "session_id": {
                    "type": "string",
                    "description": "Session ID to reuse cached data"
                },
                "metric": {
                    "type": "string",
                    "enum": ["fpy", "lpy", "try"],
                    "default": "fpy",
                    "description": "Which yield metric to analyze"
                },
            },
            "required": []  # All optional - uses context
        }
    
    def analyze(self, input_params: TrendInput) -> AgentResult:
        """
        Analyze yield trend.
        
        Args:
            input_params: TrendInput with filters and granularity
            
        Returns:
            AgentResult with trend summary and session_id for drill-downs
        """
        try:
            from ..shared.context import get_context
            from ..shared.session import get_session_manager, SessionType
            from ..shared.computations import (
                calculate_trend, generate_trend_insight, TrendDirection
            )
            
            # Get context and merge with explicit params
            context = get_context()
            explicit_params = {
                "part_number": input_params.part_number,
                "test_operation": input_params.test_operation,
                "station_name": input_params.station_name,
                "product_group": input_params.product_group,
            }
            effective_filter, confirmation = context.get_effective_filter(
                explicit_params=explicit_params
            )
            
            # Update context with any new values
            context.update_filter(**{k: v for k, v in explicit_params.items() if v})
            
            notes = []
            
            # Resolve process name if provided
            if effective_filter.get("test_operation"):
                try:
                    resolver = self._get_process_resolver()
                    match = resolver.resolve(effective_filter["test_operation"])
                    if match and match.name.lower() != effective_filter["test_operation"].lower():
                        notes.append(f"Process resolved: {effective_filter['test_operation']} → {match.name}")
                        effective_filter["test_operation"] = match.name
                except Exception:
                    pass
            
            # Check for reusable session
            session_manager = get_session_manager()
            existing_session = None
            if input_params.session_id:
                existing_session = session_manager.get_session(input_params.session_id)
            
            # Use existing session or fetch new data
            if existing_session and existing_session.temporal_matrix:
                # Reuse cached data
                matrix = existing_session.temporal_matrix
                session_id = existing_session.session_id
                notes.append(f"Using cached session {session_id[:12]}...")
            else:
                # Build WATS filter and fetch data
                wats_filter = self._build_wats_filter(input_params, effective_filter)
                
                # Call WATS API
                yield_data = self._api.analytics.get_dynamic_yield(wats_filter)
                
                if not yield_data:
                    return AgentResult.error(
                        error="No yield data found for the specified filters",
                        metadata={
                            "filter": effective_filter,
                            "granularity": input_params.granularity,
                            "lookback": input_params.lookback_periods,
                        }
                    )
                
                # Create session for caching
                session = session_manager.create_session(
                    session_type=SessionType.TREND,
                    filter_params={**effective_filter, **wats_filter},
                    yield_data=yield_data,
                )
                matrix = session.temporal_matrix
                session_id = session.session_id
            
            # Extract values for trend calculation
            periods = matrix.periods
            yields = [matrix.yields[p] for p in periods]
            
            # Calculate trend
            trend = calculate_trend(
                values=yields,
                periods=periods,
                period_type=input_params.granularity
            )
            
            # Generate insight
            insight = generate_trend_insight(trend)
            
            # Build response
            response_data = {
                "session_id": session_id,
                "trend_direction": trend.direction.value,
                "trend_rate": trend.rate_description,
                "current_yield": round(trend.current_value, 2),
                "start_yield": round(trend.start_value, 2),
                "change_points": trend.change_points[:5],
                "volatility": trend.volatility.value,
                "periods_analyzed": trend.periods_analyzed,
                "confidence": round(trend.confidence, 2),
                "filter_context": effective_filter,
            }
            
            # Build summary
            summary_parts = [insight]
            if notes:
                summary_parts.extend(notes)
            
            # Add suggestions based on findings
            suggestions = self._generate_suggestions(trend)
            if suggestions:
                response_data["suggested_next_steps"] = suggestions
            
            return AgentResult.ok(
                data=response_data,
                summary="\n".join(summary_parts),
                metadata={
                    "session_id": session_id,
                    "context": context.describe_context(),
                }
            )
            
        except Exception as e:
            return AgentResult.error(
                error=f"Trend analysis failed: {str(e)}",
                metadata={"input": input_params.model_dump() if hasattr(input_params, 'model_dump') else str(input_params)}
            )
    
    def _build_wats_filter(
        self,
        input_params: TrendInput,
        effective_filter: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build WATS API filter from parameters."""
        from pywats.domains.report import WATSFilter
        
        # Get date grouping from granularity
        granularity = TimeGranularity(input_params.granularity) if isinstance(input_params.granularity, str) else input_params.granularity
        date_grouping = GRANULARITY_TO_DATE_GROUPING.get(granularity, "DAY")
        
        # Build filter with period dimension for time-series
        filter_dict = {
            "dimensions": "period",
            "date_grouping": date_grouping,
            "period_count": input_params.lookback_periods,
        }
        
        # Add effective filters
        for key in ["part_number", "test_operation", "station_name", "product_group"]:
            if effective_filter.get(key):
                filter_dict[key] = effective_filter[key]
        
        return WATSFilter(**filter_dict)
    
    def _generate_suggestions(self, trend) -> List[str]:
        """Generate next step suggestions based on trend analysis."""
        from ..shared.computations import TrendDirection, Volatility
        
        suggestions = []
        
        if trend.direction == TrendDirection.DECLINING:
            suggestions.append("Investigate by station to find equipment issues")
            suggestions.append("Check if specific batches correlate with decline")
            if trend.change_points:
                suggestions.append(f"Focus on what changed around {trend.change_points[0]}")
        
        elif trend.direction == TrendDirection.VOLATILE:
            suggestions.append("Analyze by batch to check incoming material variation")
            suggestions.append("Check operator-by-operator performance")
            suggestions.append("Review test parameter stability")
        
        elif trend.direction == TrendDirection.IMPROVING:
            suggestions.append("Document what changes drove improvement")
            suggestions.append("Monitor to ensure improvement is sustained")
        
        return suggestions[:3]  # Max 3 suggestions
    
    def get_period_detail(
        self,
        session_id: str,
        period: str
    ) -> AgentResult:
        """
        Get detailed data for a specific period from cached session.
        
        Args:
            session_id: Session ID from previous analyze() call
            period: Period label to get detail for
            
        Returns:
            AgentResult with period detail
        """
        from ..shared.session import get_session_manager
        
        session = get_session_manager().get_session(session_id)
        if not session:
            return AgentResult.error(error=f"Session {session_id} not found or expired")
        
        detail = session.get_period_detail(period)
        if not detail:
            return AgentResult.error(error=f"Period {period} not found in session")
        
        return AgentResult.ok(
            data=detail,
            summary=f"Period {period}: {detail['yield']:.1f}% yield ({detail['unit_count']} units)"
        )
    
    def compare_periods(
        self,
        session_id: str,
        period1: str,
        period2: str
    ) -> AgentResult:
        """
        Compare two periods from cached session.
        
        Args:
            session_id: Session ID from previous analyze() call
            period1: First period to compare
            period2: Second period to compare
            
        Returns:
            AgentResult with comparison
        """
        from ..shared.session import get_session_manager
        
        session = get_session_manager().get_session(session_id)
        if not session:
            return AgentResult.error(error=f"Session {session_id} not found or expired")
        
        comparison = session.compare_periods(period1, period2)
        if "error" in comparison:
            return AgentResult.error(error=comparison["error"])
        
        yield_change = comparison["yield_change"]
        direction = "improved" if yield_change > 0 else "declined"
        
        return AgentResult.ok(
            data=comparison,
            summary=(
                f"{period1} → {period2}: Yield {direction} by {abs(yield_change):.1f}% "
                f"({comparison['period1']['yield']:.1f}% → {comparison['period2']['yield']:.1f}%)"
            )
        )


# Factory function for tool registration
def create_yield_trend_tool(api: "pyWATS") -> YieldTrendTool:
    """Create a YieldTrendTool instance."""
    return YieldTrendTool(api)
