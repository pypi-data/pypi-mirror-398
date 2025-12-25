"""
Yield Deviation Analysis Tool.

Analyzes yield deviations across configurations/dimensions to find failure modes.
Returns token-efficient summaries with pre-ranked findings.

Features:
- Multi-dimensional analysis (station, batch, operator, etc.)
- Significance scoring with confidence levels
- Pre-ranked findings (critical, high, moderate)
- Failure mode hypothesis generation
- Session-based caching for drill-downs
- Sticky filter context inheritance

Usage:
    tool = YieldDeviationTool(api)
    result = tool.analyze(
        part_number="WIDGET-001",
        test_operation="FCT",
        dimensions=["station_name"],
        days=30
    )
"""

from typing import Any, Dict, List, Optional, TYPE_CHECKING
from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict

from ...result import AgentResult

if TYPE_CHECKING:
    from pywats import pyWATS


class StandardDimension(str, Enum):
    """Standard dimensions for deviation analysis."""
    STATION = "station_name"
    FIXTURE = "fixture_id"
    OPERATOR = "operator"
    BATCH = "batch_number"
    LOCATION = "location"
    SOFTWARE = "sw_filename"
    REVISION = "revision"
    PRODUCT_GROUP = "product_group"
    LEVEL = "level"


# Mapping to WATS dimension names
DIMENSION_TO_WATS = {
    StandardDimension.STATION: "stationName",
    StandardDimension.FIXTURE: "fixtureId",
    StandardDimension.OPERATOR: "operator",
    StandardDimension.BATCH: "batchNumber",
    StandardDimension.LOCATION: "location",
    StandardDimension.SOFTWARE: "swFilename",
    StandardDimension.REVISION: "revision",
    StandardDimension.PRODUCT_GROUP: "productGroup",
    StandardDimension.LEVEL: "level",
}

# Natural language to dimension mapping
DIMENSION_ALIASES = {
    # Station
    "station": StandardDimension.STATION,
    "test station": StandardDimension.STATION,
    "tester": StandardDimension.STATION,
    "equipment": StandardDimension.STATION,
    
    # Fixture
    "fixture": StandardDimension.FIXTURE,
    "socket": StandardDimension.FIXTURE,
    "test fixture": StandardDimension.FIXTURE,
    
    # Operator
    "operator": StandardDimension.OPERATOR,
    "technician": StandardDimension.OPERATOR,
    "user": StandardDimension.OPERATOR,
    
    # Batch
    "batch": StandardDimension.BATCH,
    "lot": StandardDimension.BATCH,
    "batch number": StandardDimension.BATCH,
    "lot number": StandardDimension.BATCH,
    
    # Location
    "location": StandardDimension.LOCATION,
    "line": StandardDimension.LOCATION,
    "production line": StandardDimension.LOCATION,
    
    # Software
    "software": StandardDimension.SOFTWARE,
    "test software": StandardDimension.SOFTWARE,
    "sw version": StandardDimension.SOFTWARE,
    
    # Revision
    "revision": StandardDimension.REVISION,
    "version": StandardDimension.REVISION,
    "product revision": StandardDimension.REVISION,
    
    # Product group
    "product group": StandardDimension.PRODUCT_GROUP,
    "group": StandardDimension.PRODUCT_GROUP,
    "category": StandardDimension.PRODUCT_GROUP,
    
    # Level
    "level": StandardDimension.LEVEL,
    "production level": StandardDimension.LEVEL,
}


class DeviationInput(BaseModel):
    """Input parameters for deviation analysis."""
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
    
    # Deviation-specific parameters
    dimensions: List[str] = Field(
        default=["station_name"],
        description="""
Dimensions to analyze for deviations. Options:
- station_name/station/tester: Compare test stations
- fixture_id/fixture/socket: Compare test fixtures
- operator/technician: Compare operators
- batch_number/batch/lot: Compare production batches
- location/line: Compare production lines
- sw_filename/software: Compare test software versions
- revision: Compare product revisions
- product_group: Compare product groups
- level: Compare production levels

Can analyze multiple dimensions at once for cross-tabulation.
        """
    )
    
    days: int = Field(
        default=30,
        description="Number of days to analyze",
        ge=1,
        le=365
    )
    
    min_sample_size: int = Field(
        default=10,
        description="Minimum units to consider a dimension value significant",
        ge=1
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


def resolve_dimension(dim_input: str) -> Optional[str]:
    """
    Resolve a natural language dimension to WATS dimension name.
    
    Args:
        dim_input: Natural language dimension
        
    Returns:
        WATS dimension name (e.g., "stationName")
    """
    normalized = dim_input.lower().strip()
    
    # Check direct enum value
    try:
        dim = StandardDimension(normalized)
        return DIMENSION_TO_WATS[dim]
    except ValueError:
        pass
    
    # Check aliases
    if normalized in DIMENSION_ALIASES:
        dim = DIMENSION_ALIASES[normalized]
        return DIMENSION_TO_WATS[dim]
    
    # Check if already a WATS dimension name
    wats_dims = list(DIMENSION_TO_WATS.values())
    if normalized in [d.lower() for d in wats_dims]:
        # Find the correctly cased version
        for d in wats_dims:
            if d.lower() == normalized:
                return d
    
    return None


class YieldDeviationTool:
    """
    Intelligent yield deviation analysis tool.
    
    Finds failure modes by analyzing yield across configurations:
    - Compares yield across dimension values (stations, batches, etc.)
    - Calculates statistical significance
    - Pre-ranks findings by impact
    - Generates failure mode hypotheses
    
    Returns token-efficient summaries with actionable insights.
    
    DEVIATION ANALYSIS GUIDE:
    
    DIMENSION SELECTION:
    - station_name: Equipment issues (calibration, wear, environment)
    - fixture_id: Fixture problems (wear, contamination, alignment)
    - operator: Training/skill differences
    - batch_number: Incoming material variation
    - location: Line-specific environmental factors
    - sw_filename: Test software regressions
    
    SIGNIFICANCE LEVELS:
    - CRITICAL: >10% below baseline, high confidence
    - HIGH: 5-10% below baseline
    - MODERATE: 2-5% below baseline
    - LOW: <2% below baseline
    
    Example:
        >>> tool = YieldDeviationTool(api)
        >>> 
        >>> # Find which stations have issues
        >>> result = tool.analyze(DeviationInput(
        ...     part_number="WIDGET-001",
        ...     test_operation="FCT",
        ...     dimensions=["station_name"],
        ...     days=30
        ... ))
        >>> print(result.summary)
        "CRITICAL: ST-07 at 88.2% yield (-6.9% vs baseline 95.1%)"
        >>> 
        >>> # Multi-dimensional analysis
        >>> result = tool.analyze(DeviationInput(
        ...     dimensions=["station_name", "operator"],
        ...     days=14
        ... ))
    """
    
    name = "analyze_yield_deviation"
    description = """
⚠️ SPECIALIZED DRILL-DOWN TOOL - Use after analyze_yield.

This tool finds FAILURE MODES by comparing yield across configurations.
Use AFTER getting overall yield with analyze_yield to understand WHERE problems occur.

💡 TIP: For general yield questions, use analyze_yield FIRST with perspective="by station"
or perspective="by batch" for similar but faster results.

WHEN TO USE THIS TOOL:
✅ "Why is yield low?" - AFTER knowing what the yield actually is
✅ "Find the root cause of failures" - deviation analysis
✅ "Compare stations statistically" - significance scoring
✅ "Is there a bad station/batch/operator?" - multi-dimensional

DO NOT USE FOR:
❌ "What's the yield?" → Use analyze_yield
❌ "Show me top runners" → Use analyze_yield
❌ "Which station is best?" → Use analyze_yield with perspective="by station"
❌ "Production volume?" → Use analyze_yield

Returns:
- Baseline yield for comparison
- Pre-ranked findings (critical, high, moderate)
- Significance and confidence for each finding
- Failure mode hypothesis

DIMENSIONS TO ANALYZE:
- station/tester/equipment: Find problematic test stations
- fixture/socket: Find worn or misaligned fixtures
- operator/technician: Find training needs
- batch/lot: Find incoming material issues
- location/line: Find line-specific problems
- software: Find test software regressions

INHERITS CONTEXT:
This tool inherits filter context from previous queries. If you already
asked about WIDGET-001/FCT, you can ask "analyze by station" without
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
                "dimensions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "default": ["station_name"],
                    "description": "Dimensions to analyze: station, fixture, operator, batch, location, software, revision"
                },
                "days": {
                    "type": "integer",
                    "default": 30,
                    "minimum": 1,
                    "maximum": 365,
                    "description": "Number of days to analyze"
                },
                "min_sample_size": {
                    "type": "integer",
                    "default": 10,
                    "minimum": 1,
                    "description": "Minimum sample size for significance"
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
    
    def analyze(self, input_params: DeviationInput) -> AgentResult:
        """
        Analyze yield deviations across dimensions.
        
        Args:
            input_params: DeviationInput with filters and dimensions
            
        Returns:
            AgentResult with deviation summary and session_id for drill-downs
        """
        try:
            from ..shared.context import get_context
            from ..shared.session import get_session_manager, SessionType
            from ..shared.computations import (
                calculate_deviation_significance,
                DeviationAnalysis,
                SignificanceLevel,
                generate_deviation_insight,
                generate_failure_mode_hypothesis,
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
            
            # Resolve dimensions
            wats_dimensions = []
            for dim in input_params.dimensions:
                resolved = resolve_dimension(dim)
                if resolved:
                    wats_dimensions.append(resolved)
                else:
                    notes.append(f"Unknown dimension '{dim}' - skipped")
            
            if not wats_dimensions:
                return AgentResult.error(
                    error="No valid dimensions specified",
                    metadata={"requested": input_params.dimensions}
                )
            
            # Check for reusable session
            session_manager = get_session_manager()
            existing_session = None
            if input_params.session_id:
                existing_session = session_manager.get_session(input_params.session_id)
            
            # Use existing session or fetch new data
            if existing_session and existing_session.deviation_matrix:
                # Reuse cached data
                matrix = existing_session.deviation_matrix
                session_id = existing_session.session_id
                notes.append(f"Using cached session {session_id[:12]}...")
            else:
                # Build WATS filter and fetch data
                wats_filter = self._build_wats_filter(input_params, effective_filter, wats_dimensions)
                
                # Call WATS API
                yield_data = self._api.analytics.get_dynamic_yield(wats_filter)
                
                if not yield_data:
                    return AgentResult.error(
                        error="No yield data found for the specified filters",
                        metadata={
                            "filter": effective_filter,
                            "dimensions": wats_dimensions,
                            "days": input_params.days,
                        }
                    )
                
                # Create session for caching
                session = session_manager.create_session(
                    session_type=SessionType.DEVIATION,
                    filter_params={
                        **effective_filter,
                        "dimensions": ";".join(wats_dimensions),
                        "days": input_params.days,
                    },
                    yield_data=yield_data,
                )
                matrix = session.deviation_matrix
                session_id = session.session_id
            
            # Process the deviation matrix
            baseline = matrix.baseline_yield
            total_units = matrix.total_units
            
            # Convert to DeviationAnalysis objects for computation helpers
            deviations = []
            for cell in matrix.cells:
                if cell.unit_count >= input_params.min_sample_size:
                    deviation, significance, confidence = calculate_deviation_significance(
                        value=cell.yield_value,
                        baseline=baseline,
                        sample_size=cell.unit_count,
                        min_sample=input_params.min_sample_size,
                    )
                    
                    # Get primary dimension value for display
                    dim_key = list(cell.dimension_values.keys())[0] if cell.dimension_values else "unknown"
                    dim_value = list(cell.dimension_values.values())[0] if cell.dimension_values else "unknown"
                    
                    deviations.append(DeviationAnalysis(
                        dimension=dim_key,
                        value=dim_value,
                        yield_value=cell.yield_value,
                        baseline_yield=baseline,
                        deviation=deviation,
                        significance=significance,
                        confidence=confidence,
                        unit_count=cell.unit_count,
                        impact_score=deviation * cell.unit_count,
                    ))
            
            # Categorize findings
            critical = [d for d in deviations if d.significance == SignificanceLevel.CRITICAL]
            high = [d for d in deviations if d.significance == SignificanceLevel.HIGH]
            moderate = [d for d in deviations if d.significance == SignificanceLevel.MODERATE]
            
            # Sort by impact
            critical.sort(key=lambda d: d.impact_score)
            high.sort(key=lambda d: d.impact_score)
            moderate.sort(key=lambda d: d.impact_score)
            
            # Generate insights
            primary_dim = wats_dimensions[0] if wats_dimensions else "dimension"
            insight = generate_deviation_insight(deviations, baseline, primary_dim)
            hypothesis = generate_failure_mode_hypothesis(critical + high, primary_dim)
            
            # Build response data (token-efficient)
            response_data = {
                "session_id": session_id,
                "baseline_yield": round(baseline, 2),
                "total_units": total_units,
                "dimensions_analyzed": wats_dimensions,
                "critical_count": len(critical),
                "high_count": len(high),
                "moderate_count": len(moderate),
                "critical_findings": [d.to_dict() for d in critical[:3]],
                "high_findings": [d.to_dict() for d in high[:3]],
                "filter_context": effective_filter,
            }
            
            if hypothesis:
                response_data["hypothesis"] = hypothesis
            
            # Build summary
            summary_parts = [insight]
            if hypothesis:
                summary_parts.append(f"Hypothesis: {hypothesis}")
            if notes:
                summary_parts.extend(notes)
            
            # Add suggestions
            suggestions = self._generate_suggestions(critical, high, primary_dim)
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
                error=f"Deviation analysis failed: {str(e)}",
                metadata={"input": input_params.model_dump() if hasattr(input_params, 'model_dump') else str(input_params)}
            )
    
    def _build_wats_filter(
        self,
        input_params: DeviationInput,
        effective_filter: Dict[str, Any],
        wats_dimensions: List[str]
    ) -> Dict[str, Any]:
        """Build WATS API filter from parameters."""
        from pywats.domains.report import WATSFilter
        from datetime import datetime, timedelta
        
        date_to = datetime.now()
        date_from = date_to - timedelta(days=input_params.days)
        
        # Build filter with dimension(s)
        filter_dict = {
            "dimensions": ";".join(wats_dimensions),
            "date_from": date_from,
            "date_to": date_to,
        }
        
        # Add effective filters
        for key in ["part_number", "test_operation", "station_name", "product_group"]:
            if effective_filter.get(key):
                filter_dict[key] = effective_filter[key]
        
        return WATSFilter(**filter_dict)
    
    def _generate_suggestions(
        self,
        critical: List,
        high: List,
        dimension: str
    ) -> List[str]:
        """Generate next step suggestions based on findings."""
        suggestions = []
        
        if critical:
            top = critical[0]
            suggestions.append(f"Investigate {top.value} immediately ({top.deviation:+.1f}% deviation)")
        
        if len(critical) > 1:
            suggestions.append(f"Check for common factors across {len(critical)} critical items")
        
        # Dimension-specific suggestions
        dim_suggestions = {
            "stationName": "Check calibration dates and maintenance records",
            "fixtureId": "Inspect fixture for wear, contamination, or alignment issues",
            "operator": "Review training records and compare procedures",
            "batchNumber": "Check incoming inspection data and supplier quality",
            "location": "Compare environmental conditions between locations",
            "swFilename": "Review test software change log for regressions",
        }
        
        if dimension in dim_suggestions and (critical or high):
            suggestions.append(dim_suggestions[dimension])
        
        if not critical and not high:
            suggestions.append("No significant deviations - consider analyzing different dimensions")
            suggestions.append("Try analyzing by batch or operator for incoming quality issues")
        
        return suggestions[:3]  # Max 3 suggestions
    
    def get_dimension_detail(
        self,
        session_id: str,
        **dimension_values
    ) -> AgentResult:
        """
        Get detailed data for a specific dimension value from cached session.
        
        Args:
            session_id: Session ID from previous analyze() call
            **dimension_values: Dimension value to get detail for
            
        Returns:
            AgentResult with dimension detail
        """
        from ..shared.session import get_session_manager
        
        session = get_session_manager().get_session(session_id)
        if not session:
            return AgentResult.error(error=f"Session {session_id} not found or expired")
        
        detail = session.get_dimension_detail(**dimension_values)
        if not detail:
            return AgentResult.error(error=f"Dimension combination not found in session")
        
        return AgentResult.ok(
            data=detail,
            summary=(
                f"{list(dimension_values.values())[0]}: {detail['yield']:.1f}% yield "
                f"({detail['unit_count']} units, {detail['deviation']:+.1f}% vs baseline)"
            )
        )


# Factory function for tool registration
def create_yield_deviation_tool(api: "pyWATS") -> YieldDeviationTool:
    """Create a YieldDeviationTool instance."""
    return YieldDeviationTool(api)
