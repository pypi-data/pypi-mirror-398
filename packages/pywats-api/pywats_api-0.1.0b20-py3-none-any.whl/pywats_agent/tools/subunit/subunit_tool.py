"""
Sub-Unit Analysis Tool for WATS Agent.

Deep analysis of sub-unit relationships using the query_header endpoint.
This is the primary tool for sub-unit analysis on large datasets where
expanding sub-units is only available through query headers.

WATS SUB-UNIT CONCEPTS:
- Sub-units are components assembled into a parent unit
- Tracked in UUT/UUR reports with: partNumber, serialNumber, revision, partType
- Sub-units can be filtered to find parents containing specific components
- Sub-unit statistics help understand assembly composition

USE CASES:
1. Filter by sub-unit: Find all parents containing a specific component
2. Get sub-units for parents: Expand sub-unit data for filtered parent reports
3. Sub-unit statistics: Count sub-units by type, part number, revision
4. Deviation detection: Find parents with unexpected sub-unit configurations
"""

from typing import Any, Dict, List, Optional, TYPE_CHECKING
from datetime import datetime
from enum import Enum
from collections import defaultdict
from pydantic import BaseModel, Field

from .._base import AgentTool, ToolInput
from ...result import AgentResult

if TYPE_CHECKING:
    from pywats import pyWATS


# =============================================================================
# Data Models
# =============================================================================

class SubUnitSummary(BaseModel):
    """Summary of a sub-unit type."""
    part_number: str
    revision: Optional[str] = None
    part_type: Optional[str] = None
    count: int = 0
    unique_serials: int = 0
    sample_serials: List[str] = Field(default_factory=list)


class ParentWithSubUnits(BaseModel):
    """Parent report with its sub-units."""
    uuid: str
    serial_number: str
    part_number: str
    revision: Optional[str] = None
    status: Optional[str] = None
    test_date: Optional[datetime] = None
    sub_unit_count: int = 0
    sub_units: List[Dict[str, Any]] = Field(default_factory=list)


class DeviationResult(BaseModel):
    """Result of deviation analysis."""
    parent_serial: str
    parent_uuid: str
    deviation_type: str  # missing_subunit, extra_subunit, unexpected_type
    expected: Optional[str] = None
    actual: Optional[str] = None
    details: Optional[str] = None


class SubUnitAnalysisResult(BaseModel):
    """Complete sub-unit analysis result."""
    query_type: str  # filter_by_subunit, get_subunits, statistics, deviation
    total_parents: int = 0
    total_subunits: int = 0
    
    # For filter_by_subunit
    parents: List[ParentWithSubUnits] = Field(default_factory=list)
    
    # For statistics
    subunit_types: List[SubUnitSummary] = Field(default_factory=list)
    
    # For deviation detection
    deviations: List[DeviationResult] = Field(default_factory=list)
    
    # Warnings or notes
    warnings: List[str] = Field(default_factory=list)


class QueryType(str, Enum):
    """Type of sub-unit query to perform."""
    FILTER_BY_SUBUNIT = "filter_by_subunit"      # Find parents with specific sub-unit
    GET_SUBUNITS = "get_subunits"                # Get sub-units for a parent filter
    STATISTICS = "statistics"                     # Sub-unit type statistics
    DEVIATION = "deviation"                       # Detect configuration deviations


# =============================================================================
# Tool Input
# =============================================================================

class SubUnitAnalysisInput(ToolInput):
    """Input parameters for sub-unit analysis."""
    
    query_type: QueryType = Field(
        default=QueryType.GET_SUBUNITS,
        description="""Type of analysis:
- filter_by_subunit: Find parent units containing a specific sub-unit (by PN or SN)
- get_subunits: Get all sub-units for filtered parent reports  
- statistics: Count sub-units by type/part number/revision
- deviation: Detect parents with unexpected sub-unit configurations"""
    )
    
    # Sub-unit filtering (for filter_by_subunit)
    subunit_part_number: Optional[str] = Field(
        default=None,
        description="Filter parents by this sub-unit part number"
    )
    
    subunit_serial_number: Optional[str] = Field(
        default=None,
        description="Filter parents by this sub-unit serial number"
    )
    
    # Parent filtering
    parent_part_number: Optional[str] = Field(
        default=None,
        description="Filter to parent reports with this part number (product)"
    )
    
    parent_serial_number: Optional[str] = Field(
        default=None,
        description="Filter to parent reports with this serial number"
    )
    
    process_name: Optional[str] = Field(
        default=None,
        description="Filter to reports from this process/operation"
    )
    
    station_name: Optional[str] = Field(
        default=None,
        description="Filter to reports from this station"
    )
    
    start_date: Optional[datetime] = Field(
        default=None,
        description="Filter reports from this date onward"
    )
    
    end_date: Optional[datetime] = Field(
        default=None,
        description="Filter reports up to this date"
    )
    
    # Report type
    report_type: str = Field(
        default="uut",
        description="Report type: 'uut' (default) or 'uur'"
    )
    
    # Deviation detection options
    expected_subunit_pns: Optional[List[str]] = Field(
        default=None,
        description="For deviation detection: list of expected sub-unit part numbers"
    )
    
    expected_subunit_count: Optional[int] = Field(
        default=None,
        description="For deviation detection: expected number of sub-units"
    )
    
    # Pagination
    max_results: int = Field(
        default=1000,
        description="Maximum number of parent reports to query (max 10000)"
    )


# =============================================================================
# Sub-Unit Analysis Tool
# =============================================================================

class SubUnitAnalysisTool(AgentTool):
    """
    Deep analysis of sub-unit relationships using query_header endpoint.
    
    This tool uses the OData $expand capabilities of the query_header API
    to efficiently retrieve sub-unit data for large datasets. It's the 
    primary tool for sub-unit analysis when dealing with many reports.
    
    Capabilities:
    - Filter parents by sub-unit: Find all parent units containing a specific component
    - Get sub-units for parents: Expand sub-unit data for filtered parent reports
    - Sub-unit statistics: Count by part number, revision, type
    - Deviation detection: Find parents with missing/extra/unexpected sub-units
    
    NOTE: This endpoint is designed for bulk queries. For single-unit 
    sub-unit analysis, use analyze_unit with include_sub_units=True.
    """
    
    name = "analyze_subunits"
    description = """Deep analysis of sub-unit (component) relationships in test reports.

Use this tool when you need to:
- Find all parent units that contain a specific sub-unit (component)
- Get the sub-units assembled into parent units matching certain criteria
- Calculate statistics on sub-unit types (count by part number, revision)
- Detect deviations: parents with missing, extra, or unexpected sub-units
- Trace a component serial number back to its parent assemblies

Query types:
- filter_by_subunit: Find parents containing a specific component (by PN or SN)
- get_subunits: Get all sub-units for parent reports matching a filter
- statistics: Aggregate sub-unit counts by type/part number/revision  
- deviation: Find parents with unexpected sub-unit configurations

This tool uses the query_header endpoint with OData expansion, which is the 
only efficient way to query sub-unit data for large datasets. For single-unit
analysis, use analyze_unit instead.

Examples:
- "Which units contain sub-unit PN ABC123?" → filter_by_subunit with subunit_part_number
- "What components are in product XYZ?" → get_subunits with parent_part_number
- "How many of each sub-unit type are used?" → statistics
- "Find units missing required components" → deviation with expected_subunit_pns"""

    input_model = SubUnitAnalysisInput
    
    def _execute(self, input: SubUnitAnalysisInput) -> AgentResult:
        """Execute sub-unit analysis."""
        try:
            if input.query_type == QueryType.FILTER_BY_SUBUNIT:
                return self._filter_by_subunit(input)
            elif input.query_type == QueryType.GET_SUBUNITS:
                return self._get_subunits(input)
            elif input.query_type == QueryType.STATISTICS:
                return self._calculate_statistics(input)
            elif input.query_type == QueryType.DEVIATION:
                return self._detect_deviations(input)
            else:
                return AgentResult.fail(f"Unknown query type: {input.query_type}")
                
        except Exception as e:
            return AgentResult.fail(f"{type(e).__name__}: {str(e)}")
    
    # =========================================================================
    # Query Methods
    # =========================================================================
    
    def _filter_by_subunit(self, input: SubUnitAnalysisInput) -> AgentResult:
        """Find parent units containing a specific sub-unit."""
        if not input.subunit_part_number and not input.subunit_serial_number:
            return AgentResult.fail(
                "filter_by_subunit requires either subunit_part_number or subunit_serial_number"
            )
        
        # Build parent filter
        filter_data = self._build_filter(input)
        
        # Query using sub-unit filter
        if input.subunit_part_number:
            headers = self._api.reports.query_headers_by_subunit_part_number(
                subunit_part_number=input.subunit_part_number,
                filter_data=filter_data,
                report_type=input.report_type,
                top=input.max_results
            )
        else:
            headers = self._api.reports.query_headers_by_subunit_serial(
                subunit_serial_number=input.subunit_serial_number,
                filter_data=filter_data,
                report_type=input.report_type,
                top=input.max_results
            )
        
        # Build result
        result = SubUnitAnalysisResult(
            query_type="filter_by_subunit",
            total_parents=len(headers),
        )
        
        for header in headers:
            sub_units_data = self._extract_subunits(header, input.report_type)
            result.total_subunits += len(sub_units_data)
            
            result.parents.append(ParentWithSubUnits(
                uuid=str(header.uuid),
                serial_number=header.serial_number or "",
                part_number=header.part_number or "",
                revision=header.revision,
                status=header.status,
                test_date=header.start,
                sub_unit_count=len(sub_units_data),
                sub_units=sub_units_data,
            ))
        
        # Build summary
        search_term = input.subunit_part_number or input.subunit_serial_number
        summary = f"Found {len(headers)} parent units containing sub-unit '{search_term}'"
        
        if headers:
            unique_parents = len(set(h.serial_number for h in headers))
            summary += f" ({unique_parents} unique parent serials)"
        
        return AgentResult.ok(
            data=result.model_dump(mode="json"),
            summary=summary
        )
    
    def _get_subunits(self, input: SubUnitAnalysisInput) -> AgentResult:
        """Get sub-units for filtered parent reports."""
        filter_data = self._build_filter(input)
        
        # Query headers with sub-unit expansion
        headers = self._api.reports.query_headers_with_subunits(
            filter_data=filter_data,
            report_type=input.report_type,
            top=input.max_results,
            orderby="start desc"
        )
        
        if not headers:
            return AgentResult.ok(
                data=SubUnitAnalysisResult(
                    query_type="get_subunits",
                    total_parents=0,
                ).model_dump(mode="json"),
                summary="No reports found matching the filter criteria"
            )
        
        result = SubUnitAnalysisResult(
            query_type="get_subunits",
            total_parents=len(headers),
        )
        
        for header in headers:
            sub_units_data = self._extract_subunits(header, input.report_type)
            result.total_subunits += len(sub_units_data)
            
            result.parents.append(ParentWithSubUnits(
                uuid=str(header.uuid),
                serial_number=header.serial_number or "",
                part_number=header.part_number or "",
                revision=header.revision,
                status=header.status,
                test_date=header.start,
                sub_unit_count=len(sub_units_data),
                sub_units=sub_units_data,
            ))
        
        # Calculate average sub-units per parent
        avg_subunits = result.total_subunits / len(headers) if headers else 0
        
        summary = (
            f"Retrieved sub-units for {len(headers)} parent reports. "
            f"Total: {result.total_subunits} sub-units (avg {avg_subunits:.1f} per parent)"
        )
        
        return AgentResult.ok(
            data=result.model_dump(mode="json"),
            summary=summary
        )
    
    def _calculate_statistics(self, input: SubUnitAnalysisInput) -> AgentResult:
        """Calculate sub-unit statistics (count by type/PN/revision)."""
        filter_data = self._build_filter(input)
        
        # Query headers with sub-unit expansion
        headers = self._api.reports.query_headers_with_subunits(
            filter_data=filter_data,
            report_type=input.report_type,
            top=input.max_results,
            orderby="start desc"
        )
        
        if not headers:
            return AgentResult.ok(
                data=SubUnitAnalysisResult(
                    query_type="statistics",
                    total_parents=0,
                ).model_dump(mode="json"),
                summary="No reports found matching the filter criteria"
            )
        
        # Aggregate by part_number + revision
        stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "count": 0,
            "serials": set(),
            "part_type": None,
            "revision": None,
        })
        
        total_subunits = 0
        for header in headers:
            sub_units_data = self._extract_subunits(header, input.report_type)
            total_subunits += len(sub_units_data)
            
            for su in sub_units_data:
                pn = su.get("part_number", "Unknown")
                rev = su.get("revision", "")
                key = f"{pn}|{rev}" if rev else pn
                
                stats[key]["count"] += 1
                if su.get("serial_number"):
                    stats[key]["serials"].add(su["serial_number"])
                stats[key]["part_type"] = su.get("part_type")
                stats[key]["revision"] = rev
                stats[key]["part_number"] = pn
        
        # Build result
        result = SubUnitAnalysisResult(
            query_type="statistics",
            total_parents=len(headers),
            total_subunits=total_subunits,
        )
        
        for key, data in sorted(stats.items(), key=lambda x: x[1]["count"], reverse=True):
            serials = list(data["serials"])
            result.subunit_types.append(SubUnitSummary(
                part_number=data["part_number"],
                revision=data["revision"],
                part_type=data["part_type"],
                count=data["count"],
                unique_serials=len(serials),
                sample_serials=serials[:5],  # First 5 as samples
            ))
        
        summary = (
            f"Sub-unit statistics for {len(headers)} parent reports: "
            f"{len(result.subunit_types)} unique sub-unit types, "
            f"{total_subunits} total instances"
        )
        
        if result.subunit_types:
            top = result.subunit_types[0]
            summary += f". Most common: {top.part_number} ({top.count} instances)"
        
        return AgentResult.ok(
            data=result.model_dump(mode="json"),
            summary=summary
        )
    
    def _detect_deviations(self, input: SubUnitAnalysisInput) -> AgentResult:
        """Detect parents with unexpected sub-unit configurations."""
        filter_data = self._build_filter(input)
        
        # Query headers with sub-unit expansion
        headers = self._api.reports.query_headers_with_subunits(
            filter_data=filter_data,
            report_type=input.report_type,
            top=input.max_results,
            orderby="start desc"
        )
        
        if not headers:
            return AgentResult.ok(
                data=SubUnitAnalysisResult(
                    query_type="deviation",
                    total_parents=0,
                ).model_dump(mode="json"),
                summary="No reports found matching the filter criteria"
            )
        
        result = SubUnitAnalysisResult(
            query_type="deviation",
            total_parents=len(headers),
        )
        
        expected_pns = set(input.expected_subunit_pns or [])
        expected_count = input.expected_subunit_count
        
        # If no expected values, infer from most common configuration
        if not expected_pns and not expected_count:
            # Build baseline from data
            pn_counts: Dict[str, int] = defaultdict(int)
            count_distribution: Dict[int, int] = defaultdict(int)
            
            for header in headers:
                sub_units_data = self._extract_subunits(header, input.report_type)
                count_distribution[len(sub_units_data)] += 1
                for su in sub_units_data:
                    pn = su.get("part_number")
                    if pn:
                        pn_counts[pn] += 1
            
            # Use most common count as expected
            if count_distribution:
                expected_count = max(count_distribution, key=count_distribution.get)
            
            # Use part numbers that appear in >50% of reports as expected
            threshold = len(headers) * 0.5
            expected_pns = {pn for pn, count in pn_counts.items() if count >= threshold}
            
            result.warnings.append(
                f"No expected values provided. Inferred from data: "
                f"expected_count={expected_count}, expected_pns={sorted(expected_pns)}"
            )
        
        # Find deviations
        for header in headers:
            sub_units_data = self._extract_subunits(header, input.report_type)
            actual_pns = {su.get("part_number") for su in sub_units_data if su.get("part_number")}
            
            # Check count deviation
            if expected_count is not None and len(sub_units_data) != expected_count:
                result.deviations.append(DeviationResult(
                    parent_serial=header.serial_number or "",
                    parent_uuid=str(header.uuid),
                    deviation_type="count_mismatch",
                    expected=str(expected_count),
                    actual=str(len(sub_units_data)),
                    details=f"Expected {expected_count} sub-units, found {len(sub_units_data)}"
                ))
            
            # Check for missing sub-units
            if expected_pns:
                missing = expected_pns - actual_pns
                for pn in missing:
                    result.deviations.append(DeviationResult(
                        parent_serial=header.serial_number or "",
                        parent_uuid=str(header.uuid),
                        deviation_type="missing_subunit",
                        expected=pn,
                        actual=None,
                        details=f"Expected sub-unit PN '{pn}' not found"
                    ))
                
                # Check for unexpected sub-units
                unexpected = actual_pns - expected_pns
                for pn in unexpected:
                    result.deviations.append(DeviationResult(
                        parent_serial=header.serial_number or "",
                        parent_uuid=str(header.uuid),
                        deviation_type="unexpected_subunit",
                        expected=None,
                        actual=pn,
                        details=f"Unexpected sub-unit PN '{pn}' found"
                    ))
        
        result.total_subunits = sum(
            len(self._extract_subunits(h, input.report_type)) for h in headers
        )
        
        # Group deviations by type for summary
        deviation_types = defaultdict(int)
        for d in result.deviations:
            deviation_types[d.deviation_type] += 1
        
        if result.deviations:
            type_summary = ", ".join(f"{k}: {v}" for k, v in sorted(deviation_types.items()))
            summary = (
                f"Found {len(result.deviations)} deviations in {len(headers)} parents. "
                f"Types: {type_summary}"
            )
        else:
            summary = f"No deviations found in {len(headers)} parent reports"
        
        return AgentResult.ok(
            data=result.model_dump(mode="json"),
            summary=summary
        )
    
    # =========================================================================
    # Helper Methods
    # =========================================================================
    
    def _build_filter(self, input: SubUnitAnalysisInput) -> Optional[Dict[str, Any]]:
        """Build WATSFilter from input parameters."""
        from pywats import WATSFilter
        
        filter_dict = {}
        
        if input.parent_part_number:
            filter_dict["part_number"] = input.parent_part_number
        if input.parent_serial_number:
            filter_dict["serial_number"] = input.parent_serial_number
        if input.process_name:
            filter_dict["process_name"] = input.process_name
        if input.station_name:
            filter_dict["station_name"] = input.station_name
        if input.start_date:
            filter_dict["date_from"] = input.start_date
        if input.end_date:
            filter_dict["date_to"] = input.end_date
        
        if filter_dict:
            return WATSFilter(**filter_dict)
        return None
    
    def _extract_subunits(self, header: Any, report_type: str) -> List[Dict[str, Any]]:
        """Extract sub-unit data from a header object."""
        if report_type == "uut":
            raw_subunits = getattr(header, "sub_units", None) or []
        else:
            raw_subunits = getattr(header, "uur_sub_units", None) or []
        
        result = []
        for su in raw_subunits:
            if isinstance(su, dict):
                result.append(su)
            elif hasattr(su, "model_dump") and callable(su.model_dump):
                # Pydantic model - call model_dump
                try:
                    result.append(su.model_dump(mode="json"))
                except Exception:
                    # Fallback to manual extraction
                    result.append({
                        "serial_number": getattr(su, "serial_number", None),
                        "part_number": getattr(su, "part_number", None),
                        "revision": getattr(su, "revision", None),
                        "part_type": getattr(su, "part_type", None),
                    })
            else:
                # Plain object or unknown - extract fields manually
                result.append({
                    "serial_number": getattr(su, "serial_number", None),
                    "part_number": getattr(su, "part_number", None),
                    "revision": getattr(su, "revision", None),
                    "part_type": getattr(su, "part_type", None),
                })
        
        return result
