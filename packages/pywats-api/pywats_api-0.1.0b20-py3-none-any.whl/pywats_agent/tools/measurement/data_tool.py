"""
Individual measurement data tool.

Provides access to raw measurement values with timestamps,
serial numbers, and limit information.
"""

from typing import Any, Dict, List, TYPE_CHECKING
from datetime import datetime, timedelta

from ...result import AgentResult
from .models import MeasurementFilter

if TYPE_CHECKING:
    from pywats import pyWATS


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
