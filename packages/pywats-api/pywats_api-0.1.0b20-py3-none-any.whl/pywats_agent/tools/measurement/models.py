"""
Measurement filter model for AI agents.

Defines the input parameters for measurement queries.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


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
