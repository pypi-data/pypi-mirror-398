"""
Dimension Discovery Tool.

Discovers available dimensions in yield data and validates
dimension combinations for statistical analysis.

This tool helps agents:
1. Know what dimensions exist in the dataset
2. Understand cardinality and sample distribution
3. Check if a dimension combination is viable
4. Get recommendations for analysis approaches

Usage:
    tool = DimensionDiscoveryTool(api)
    result = tool.discover(
        part_number="WIDGET-001",
        test_operation="FCT",
        days=30
    )
    # Returns available dimensions, cardinalities, and recommendations
"""

from typing import Any, Dict, List, Optional, TYPE_CHECKING
from datetime import datetime, timedelta
from pydantic import BaseModel, Field, ConfigDict

from ...result import AgentResult

if TYPE_CHECKING:
    from pywats import pyWATS


class DiscoveryInput(BaseModel):
    """Input parameters for dimension discovery."""
    model_config = ConfigDict(use_enum_values=True)
    
    # Filter parameters
    part_number: Optional[str] = Field(
        default=None,
        description="Product part number to analyze"
    )
    test_operation: Optional[str] = Field(
        default=None,
        description="Test operation/process (e.g., 'FCT', 'EOL')"
    )
    station_name: Optional[str] = Field(
        default=None,
        description="Filter to specific test station"
    )
    product_group: Optional[str] = Field(
        default=None,
        description="Filter to product group"
    )
    
    days: int = Field(
        default=30,
        description="Number of days to analyze",
        ge=1,
        le=365
    )
    
    # Discovery options
    suggest_combinations: bool = Field(
        default=True,
        description="Whether to suggest viable dimension combinations"
    )
    max_combination_size: int = Field(
        default=2,
        description="Maximum dimensions to combine in suggestions",
        ge=1,
        le=4
    )
    
    # Optional: use existing session
    session_id: Optional[str] = Field(
        default=None,
        description="Reuse data from existing session"
    )


class DimensionDiscoveryTool:
    """
    Tool for discovering available dimensions in yield data.
    
    Before running deviation analysis, use this tool to:
    - See what dimensions are available
    - Understand data distribution per dimension
    - Check if dimension combinations are viable
    - Get recommendations for analysis
    
    Example:
        >>> tool = DimensionDiscoveryTool(api)
        >>> result = tool.discover(DiscoveryInput(
        ...     part_number="WIDGET-001",
        ...     days=30
        ... ))
        >>> print(result.data["dimensions"])
        {
            "station_name": {"cardinality": 5, "total_samples": 1234, ...},
            "operator": {"cardinality": 12, "total_samples": 1234, ...},
            ...
        }
    """
    
    name = "discover_yield_dimensions"
    description = """
Discover available dimensions and their statistics in yield data.

Use BEFORE deviation analysis to:
- See what dimensions are available (station, operator, batch, etc.)
- Check how many unique values each dimension has
- Understand sample distribution
- Get recommendations for viable analysis approaches

Returns:
- Available dimensions with cardinality and sample counts
- Top values for each dimension
- Viability assessment for dimension combinations
- Recommendations for analysis

WHEN TO USE:
- "What can I analyze by?" → discover dimensions first
- "Is there enough data to compare stations?" → check viability
- "What dimensions have data?" → discover all dimensions
- Before multi-dimensional analysis → check combinations

INHERITS CONTEXT:
This tool inherits filter context from previous queries.
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
                    "description": "Test operation (e.g., 'FCT', 'EOL', 'PCBA')"
                },
                "station_name": {
                    "type": "string",
                    "description": "Filter to specific station"
                },
                "product_group": {
                    "type": "string",
                    "description": "Filter to product group"
                },
                "days": {
                    "type": "integer",
                    "default": 30,
                    "minimum": 1,
                    "maximum": 365,
                    "description": "Number of days to analyze"
                },
                "suggest_combinations": {
                    "type": "boolean",
                    "default": True,
                    "description": "Whether to suggest viable combinations"
                },
                "max_combination_size": {
                    "type": "integer",
                    "default": 2,
                    "minimum": 1,
                    "maximum": 4,
                    "description": "Maximum dimensions to combine"
                },
                "session_id": {
                    "type": "string",
                    "description": "Reuse data from existing session"
                },
            },
            "required": []
        }
    
    def discover(self, input_params: DiscoveryInput) -> AgentResult:
        """
        Discover available dimensions in yield data.
        
        Args:
            input_params: DiscoveryInput with filters
            
        Returns:
            AgentResult with dimensions and recommendations
        """
        try:
            from ..shared.context import get_context
            from ..shared.session import get_session_manager
            from ..shared.statistics import (
                DimensionDiscovery,
                get_statistical_config,
            )
            from pywats import WATSFilter
            
            # Get context and merge
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
            
            # Update context
            context.update_filter(**{k: v for k, v in explicit_params.items() if v})
            
            notes = []
            
            # Resolve process name
            if effective_filter.get("test_operation"):
                try:
                    resolver = self._get_process_resolver()
                    match = resolver.resolve(effective_filter["test_operation"])
                    if match and match.name.lower() != effective_filter["test_operation"].lower():
                        notes.append(f"Process: {effective_filter['test_operation']} → {match.name}")
                        effective_filter["test_operation"] = match.name
                except Exception:
                    pass
            
            # Check for reusable session
            session_manager = get_session_manager()
            yield_data = None
            
            if input_params.session_id:
                existing = session_manager.get_session(input_params.session_id)
                if existing and existing.raw_data:
                    yield_data = existing.raw_data
                    notes.append(f"Using cached session {input_params.session_id[:12]}...")
            
            # Fetch data if needed
            if yield_data is None:
                date_from = datetime.now() - timedelta(days=input_params.days)
                
                # Build minimal filter to get diverse data
                wats_filter = WATSFilter(
                    part_number=effective_filter.get("part_number"),
                    test_operation=effective_filter.get("test_operation"),
                    station_name=effective_filter.get("station_name"),
                    product_group=effective_filter.get("product_group"),
                    date_from=date_from,
                    # Get data with all dimensions
                    dimensions="partNumber;stationName;operator;batchNumber;location;fixtureId;swFilename;revision;productGroup;level;testOperation",
                )
                
                yield_data = self._api.analytics.get_dynamic_yield(wats_filter)
            
            if not yield_data:
                return AgentResult.error(
                    error="No data found for the specified filters",
                    metadata={
                        "filters": effective_filter,
                        "days": input_params.days,
                    }
                )
            
            # Discover dimensions
            discovery = DimensionDiscovery(get_statistical_config())
            dimensions = discovery.discover_all_dimensions(yield_data)
            
            if not dimensions:
                return AgentResult.error(
                    error="No dimensions could be discovered from the data",
                )
            
            # Build response
            total_samples = sum(
                getattr(item, "unit_count", 0) or getattr(item, "unitCount", 1)
                for item in yield_data
            )
            
            dimension_summary = {
                name: {
                    "display_name": info.display_name,
                    "cardinality": info.cardinality,
                    "total_samples": info.total_samples,
                    "top_values": dict(sorted(
                        info.sample_counts.items(),
                        key=lambda x: x[1],
                        reverse=True
                    )[:5]),
                    "sparsity_warning": info.sparsity_warning,
                }
                for name, info in dimensions.items()
            }
            
            # Get suggestions if requested
            suggestions = []
            if input_params.suggest_combinations:
                raw_suggestions = discovery.suggest_viable_combinations(
                    yield_data,
                    max_dimensions=input_params.max_combination_size
                )
                # Simplify for agent
                suggestions = [
                    {
                        "dimensions": s["dimensions"],
                        "avg_samples": s["stats"]["avg_samples"],
                        "cells": s["stats"]["populated_cells"],
                        "recommendation": s["recommendation"],
                    }
                    for s in raw_suggestions[:10]
                ]
            
            # Build insight
            dim_list = ", ".join(sorted(dimensions.keys()))
            insight = f"Found {len(dimensions)} dimensions in data ({total_samples:,} total samples): {dim_list}. "
            
            if suggestions:
                good = [s for s in suggestions if s["recommendation"] == "good"]
                if good:
                    best = good[0]
                    insight += f"Recommended: {' + '.join(best['dimensions'])} ({best['cells']} groups, ~{best['avg_samples']:.0f} samples each)."
            
            return AgentResult.success(
                summary=insight,
                data={
                    "total_samples": total_samples,
                    "dimensions": dimension_summary,
                    "viable_combinations": suggestions,
                    "filters_applied": effective_filter,
                },
                metadata={
                    "days": input_params.days,
                    "notes": notes,
                }
            )
            
        except Exception as e:
            return AgentResult.error(
                error=f"Dimension discovery failed: {str(e)}",
                metadata={"exception_type": type(e).__name__}
            )
    
    # Tool definition for framework integration
    @classmethod
    def get_tool_definition(cls) -> Dict[str, Any]:
        """Get tool definition for registration."""
        return {
            "name": cls.name,
            "description": cls.description,
            "parameters": cls.get_parameters_schema(),
        }
