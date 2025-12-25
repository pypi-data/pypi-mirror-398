"""
Measurement analysis tools for AI agents.

Provides intelligent measurement data access for both aggregated statistics
and individual measurement data points.
"""

from typing import Any, Dict, List, Optional, TYPE_CHECKING
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

from ..result import AgentResult

if TYPE_CHECKING:
    from pywats import pyWATS


class MeasurementFilter(BaseModel):
    """
    Measurement filter for AI agents.
    
    This is the LLM-friendly interface for querying measurement data,
    both aggregated statistics and individual data points.
    
    IMPORTANT: The WATS API requires part_number and test_operation filters
    for measurement queries. Without them, the API returns measurements from
    the last 7 days of most failed steps, which can cause timeouts.
    
    Best practice: Always provide part_number when querying measurements.
    """
    
    # Required measurement identifier
    measurement_path: str = Field(
        description="""
        Path to the measurement step (required).
        
        Format options:
        - Using "/" as separator: "Step Group/Step Name/Measurement"
        - Using "¶" (paragraph mark): "Step Group¶Step Name¶Measurement"  
        - For multi-numeric: Use "::" for measurement name: "Step Group/Step/Test::MeasName"
        
        Examples:
        - "Main/Voltage Test/Output Voltage"
        - "Main/Voltage Test::Measurement0" (multi-numeric)
        - "MainSequence Callback¶NI steps¶Voltage Test"
        
        Note: "/" is automatically converted to "¶" for the API.
        """
    )
    
    # Recommended filters (quasi-required for performance)
    part_number: Optional[str] = Field(
        default=None,
        description="Filter by product part number (e.g., 'WIDGET-001'). STRONGLY RECOMMENDED to avoid timeouts."
    )
    test_operation: Optional[str] = Field(
        default=None,
        description="Filter by test operation name. STRONGLY RECOMMENDED to avoid timeouts."
    )
    revision: Optional[str] = Field(
        default=None,
        description="Filter by product revision"
    )
    station_name: Optional[str] = Field(
        default=None,
        description="Filter by test station name"
    )
    serial_number: Optional[str] = Field(
        default=None,
        description="Filter by specific unit serial number"
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
    
    # Result options
    top_count: Optional[int] = Field(
        default=None,
        description="Limit number of individual data points returned (for get_measurements)"
    )
    grouping: Optional[str] = Field(
        default=None,
        description="Grouping for aggregated measurements (e.g., 'partNumber', 'stationName')"
    )


class AggregatedMeasurementTool:
    """
    Tool for analyzing aggregated measurement statistics.
    
    Provides statistical analysis of measurement data including:
    - Min, max, average values
    - Standard deviation and variance
    - Process capability metrics (Cp, Cpk)
    - Limit violations
    
    Example:
        >>> tool = AggregatedMeasurementTool(api)
        >>> 
        >>> result = tool.analyze(MeasurementFilter(
        ...     part_number="WIDGET-001",
        ...     measurement_path="Main/Voltage Test/Output Voltage",
        ...     days=7
        ... ))
        >>> 
        >>> # Returns aggregate statistics:
        >>> # - Count, min, max, avg, stdev
        >>> # - Cpk and Cp values
        >>> # - Limit information
    """
    
    name = "get_measurement_statistics"
    description = """
Get aggregated measurement statistics and process capability metrics.

Use this tool to answer questions like:
- "What's the average output voltage for WIDGET-001?"
- "Show me Cpk for all voltage measurements"
- "What are the min/max values for temperature measurements?"
- "Get measurement statistics for product X"
- "Is the process capable for this measurement?"
- "What's the standard deviation of this measurement?"

Provides aggregate statistics including:
- Count, min, max, average
- Standard deviation and variance
- Process capability (Cp, Cpk)
- Limit values (low and high)
- Part number and revision info
"""
    
    def __init__(self, api: "pyWATS"):
        """Initialize with a pyWATS instance."""
        self._api = api
    
    @staticmethod
    def get_parameters_schema() -> Dict[str, Any]:
        """Get OpenAI-compatible parameter schema."""
        return {
            "type": "object",
            "properties": {
                "measurement_path": {
                    "type": "string",
                    "description": "Path to the measurement (required). Format: 'Group/Step/Measurement' or use wildcards"
                },
                "part_number": {
                    "type": "string",
                    "description": "Filter by product part number (optional)"
                },
                "revision": {
                    "type": "string",
                    "description": "Filter by product revision (optional)"
                },
                "station_name": {
                    "type": "string",
                    "description": "Filter by test station (optional)"
                },
                "days": {
                    "type": "integer",
                    "description": "Number of days to analyze (default: 30)",
                    "default": 30
                },
                "grouping": {
                    "type": "string",
                    "description": "Group results by dimension (e.g., 'partNumber', 'stationName')"
                },
            },
            "required": ["measurement_path"]
        }
    
    def analyze(self, filter_input: MeasurementFilter) -> AgentResult:
        """
        Get aggregated measurement statistics.
        
        Args:
            filter_input: MeasurementFilter with parameters
            
        Returns:
            AgentResult with aggregated measurement data and summary
        """
        try:
            # Build filter for API
            from pywats.domains.report.models import WATSFilter
            
            date_to = filter_input.date_to or datetime.now()
            date_from = filter_input.date_from or (date_to - timedelta(days=filter_input.days))
            
            # NOTE: measurement_path is passed separately as a query parameter
            # Do NOT include it in the WATSFilter body
            filter_params = {
                "date_from": date_from,
                "date_to": date_to,
            }
            
            if filter_input.part_number:
                filter_params["part_number"] = filter_input.part_number
            if filter_input.revision:
                filter_params["revision"] = filter_input.revision
            if filter_input.station_name:
                filter_params["station_name"] = filter_input.station_name
            if filter_input.grouping:
                filter_params["grouping"] = filter_input.grouping
            
            wats_filter = WATSFilter(**filter_params)
            
            # Call the API with measurement_paths as query parameter
            data = self._api.analytics.get_aggregated_measurements(
                wats_filter,
                measurement_paths=filter_input.measurement_path
            )
            
            if not data:
                return AgentResult.ok(
                    data=[],
                    summary=self._build_no_data_summary(filter_input)
                )
            
            # Build rich summary
            summary = self._build_summary(data, filter_input)
            
            return AgentResult.ok(
                data=[d.model_dump() for d in data],
                summary=summary,
                metadata={
                    "measurement_count": len(data),
                    "measurement_path": filter_input.measurement_path,
                    "part_number": filter_input.part_number,
                    "days": filter_input.days,
                }
            )
            
        except Exception as e:
            return AgentResult.fail(f"Aggregated measurement analysis failed: {str(e)}")
    
    def analyze_from_dict(self, params: Dict[str, Any]) -> AgentResult:
        """
        Analyze measurements from a dictionary of parameters.
        
        Args:
            params: Dictionary of parameters from LLM tool call
            
        Returns:
            AgentResult with measurement data and summary
        """
        filter_input = MeasurementFilter(**params)
        return self.analyze(filter_input)
    
    def _build_summary(
        self, 
        data: List[Any], 
        filter_input: MeasurementFilter
    ) -> str:
        """Build a human-readable summary of the measurement statistics."""
        
        parts = [
            f"Aggregated measurement statistics for '{filter_input.measurement_path}'"
        ]
        
        if filter_input.part_number:
            parts[0] += f" on {filter_input.part_number}"
        
        parts[0] += f" (last {filter_input.days} days):"
        
        parts.append(f"\n• Found {len(data)} measurement group(s)")
        
        # Add details for each measurement group
        for i, meas in enumerate(data[:10], 1):  # Limit to 10 for readability
            step_name = meas.step_name or "Unknown"
            count = meas.count or 0
            avg = meas.avg
            min_val = meas.min
            max_val = meas.max
            cpk = meas.cpk
            
            line_parts = [f"\n{i}. {step_name}:"]
            line_parts.append(f"   Count: {count:,}")
            
            if avg is not None:
                line_parts.append(f"   Avg: {avg:.4f}")
            if min_val is not None and max_val is not None:
                line_parts.append(f"   Range: {min_val:.4f} - {max_val:.4f}")
            if cpk is not None:
                line_parts.append(f"   Cpk: {cpk:.2f}")
                
            parts.extend(line_parts)
        
        if len(data) > 10:
            parts.append(f"\n... and {len(data) - 10} more measurement groups")
        
        return "\n".join(parts)
    
    def _build_no_data_summary(self, filter_input: MeasurementFilter) -> str:
        """Build summary when no data is found."""
        parts = [
            f"No aggregated measurement data found for '{filter_input.measurement_path}'"
        ]
        
        if filter_input.part_number:
            parts[0] += f" on {filter_input.part_number}"
        
        parts[0] += f" in the last {filter_input.days} days."
        
        return "\n".join(parts)


class MeasurementDataTool:
    """
    Tool for retrieving individual measurement data points.
    
    Provides access to raw measurement values with timestamps,
    serial numbers, and limit information.
    
    Example:
        >>> tool = MeasurementDataTool(api)
        >>> 
        >>> result = tool.analyze(MeasurementFilter(
        ...     part_number="WIDGET-001",
        ...     measurement_path="Main/Voltage Test/Output Voltage",
        ...     top_count=100,
        ...     days=7
        ... ))
        >>> 
        >>> # Returns individual measurements:
        >>> # - Serial number, value, timestamp
        >>> # - Pass/fail status
        >>> # - Limit values
    """
    
    name = "get_measurement_data"
    description = """
Get individual measurement data points with timestamps and serial numbers.

Use this tool to answer questions like:
- "Show me the last 100 voltage measurements for WIDGET-001"
- "What were the actual measurement values for serial number X?"
- "Get raw measurement data for temperature sensor"
- "Show me measurements that failed limits"
- "What was measured for this specific unit?"

Provides individual data points including:
- Serial number and part number
- Measured value
- Pass/fail status
- Limit values (low and high)
- Timestamp
- Step name and path
"""
    
    def __init__(self, api: "pyWATS"):
        """Initialize with a pyWATS instance."""
        self._api = api
    
    @staticmethod
    def get_parameters_schema() -> Dict[str, Any]:
        """Get OpenAI-compatible parameter schema."""
        return {
            "type": "object",
            "properties": {
                "measurement_path": {
                    "type": "string",
                    "description": "Path to the measurement (required). Format: 'Group/Step/Measurement'"
                },
                "part_number": {
                    "type": "string",
                    "description": "Filter by product part number (optional)"
                },
                "revision": {
                    "type": "string",
                    "description": "Filter by product revision (optional)"
                },
                "serial_number": {
                    "type": "string",
                    "description": "Filter by specific unit serial number (optional)"
                },
                "station_name": {
                    "type": "string",
                    "description": "Filter by test station (optional)"
                },
                "days": {
                    "type": "integer",
                    "description": "Number of days to retrieve (default: 30)",
                    "default": 30
                },
                "top_count": {
                    "type": "integer",
                    "description": "Limit number of data points returned (default: 1000)",
                    "default": 1000
                },
            },
            "required": ["measurement_path"]
        }
    
    def analyze(self, filter_input: MeasurementFilter) -> AgentResult:
        """
        Get individual measurement data points.
        
        Args:
            filter_input: MeasurementFilter with parameters
            
        Returns:
            AgentResult with measurement data points and summary
        """
        try:
            # Build filter for API
            from pywats.domains.report.models import WATSFilter
            
            date_to = filter_input.date_to or datetime.now()
            date_from = filter_input.date_from or (date_to - timedelta(days=filter_input.days))
            
            # NOTE: measurement_path is passed separately as a query parameter
            # Do NOT include it in the WATSFilter body
            filter_params = {
                "date_from": date_from,
                "date_to": date_to,
            }
            
            if filter_input.part_number:
                filter_params["part_number"] = filter_input.part_number
            if filter_input.revision:
                filter_params["revision"] = filter_input.revision
            if filter_input.station_name:
                filter_params["station_name"] = filter_input.station_name
            if filter_input.serial_number:
                filter_params["serial_number"] = filter_input.serial_number
            if filter_input.top_count:
                filter_params["top_count"] = filter_input.top_count
            
            wats_filter = WATSFilter(**filter_params)
            
            # Call the API with measurement_paths as query parameter
            data = self._api.analytics.get_measurements(
                wats_filter,
                measurement_paths=filter_input.measurement_path
            )
            
            if not data:
                return AgentResult.ok(
                    data=[],
                    summary=self._build_no_data_summary(filter_input)
                )
            
            # Build rich summary
            summary = self._build_summary(data, filter_input)
            
            return AgentResult.ok(
                data=[d.model_dump() for d in data],
                summary=summary,
                metadata={
                    "data_point_count": len(data),
                    "measurement_path": filter_input.measurement_path,
                    "part_number": filter_input.part_number,
                    "serial_number": filter_input.serial_number,
                    "days": filter_input.days,
                }
            )
            
        except Exception as e:
            return AgentResult.fail(f"Measurement data retrieval failed: {str(e)}")
    
    def analyze_from_dict(self, params: Dict[str, Any]) -> AgentResult:
        """
        Get measurement data from a dictionary of parameters.
        
        Args:
            params: Dictionary of parameters from LLM tool call
            
        Returns:
            AgentResult with measurement data and summary
        """
        filter_input = MeasurementFilter(**params)
        return self.analyze(filter_input)
    
    def _build_summary(
        self, 
        data: List[Any], 
        filter_input: MeasurementFilter
    ) -> str:
        """Build a human-readable summary of the measurement data."""
        
        parts = [
            f"Individual measurement data for '{filter_input.measurement_path}'"
        ]
        
        if filter_input.part_number:
            parts[0] += f" on {filter_input.part_number}"
        if filter_input.serial_number:
            parts[0] += f" (SN: {filter_input.serial_number})"
        
        parts[0] += f" (last {filter_input.days} days):"
        
        # Calculate statistics from the data
        values = [d.value for d in data if d.value is not None]
        failed_count = sum(1 for d in data if d.status and 'fail' in d.status.lower())
        
        parts.append(f"\n• Retrieved {len(data)} data point(s)")
        
        if values:
            avg = sum(values) / len(values)
            min_val = min(values)
            max_val = max(values)
            parts.append(f"• Value range: {min_val:.4f} - {max_val:.4f}")
            parts.append(f"• Average: {avg:.4f}")
        
        if failed_count > 0:
            fail_rate = (failed_count / len(data)) * 100
            parts.append(f"• Failed measurements: {failed_count} ({fail_rate:.1f}%)")
        
        # Show sample of data points
        if data and len(data) <= 10:
            parts.append("\nMeasurement data:")
            for d in data:
                sn = d.serial_number or "Unknown"
                val = d.value if d.value is not None else "N/A"
                status = d.status or "Unknown"
                parts.append(f"  • SN {sn}: {val} ({status})")
        elif data:
            parts.append(f"\nShowing first 5 of {len(data)} measurements:")
            for d in data[:5]:
                sn = d.serial_number or "Unknown"
                val = d.value if d.value is not None else "N/A"
                status = d.status or "Unknown"
                parts.append(f"  • SN {sn}: {val} ({status})")
        
        return "\n".join(parts)
    
    def _build_no_data_summary(self, filter_input: MeasurementFilter) -> str:
        """Build summary when no data is found."""
        parts = [
            f"No measurement data found for '{filter_input.measurement_path}'"
        ]
        
        if filter_input.part_number:
            parts[0] += f" on {filter_input.part_number}"
        if filter_input.serial_number:
            parts[0] += f" (SN: {filter_input.serial_number})"
        
        parts[0] += f" in the last {filter_input.days} days."
        
        return "\n".join(parts)


def get_aggregated_measurement_tool_definition() -> Dict[str, Any]:
    """
    Get the OpenAI tool definition for aggregated measurements.
    
    Returns:
        Dictionary with tool name, description, and parameters schema
    """
    return {
        "name": AggregatedMeasurementTool.name,
        "description": AggregatedMeasurementTool.description,
        "parameters": AggregatedMeasurementTool.get_parameters_schema(),
    }


def get_measurement_data_tool_definition() -> Dict[str, Any]:
    """
    Get the OpenAI tool definition for measurement data.
    
    Returns:
        Dictionary with tool name, description, and parameters schema
    """
    return {
        "name": MeasurementDataTool.name,
        "description": MeasurementDataTool.description,
        "parameters": MeasurementDataTool.get_parameters_schema(),
    }
