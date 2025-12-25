"""
Measurement analysis tools for AI agents.

This package provides tools for querying and analyzing measurement data:
- AggregatedMeasurementTool: Statistical analysis (min, max, avg, Cpk)
- MeasurementDataTool: Individual data points with timestamps

IMPORTANT: The WATS API requires part_number and test_operation filters
for measurement queries. Without them, the API returns measurements from
the last 7 days of most failed steps, which can cause timeouts.
"""

from .models import MeasurementFilter
from .aggregated_tool import (
    AggregatedMeasurementTool,
    get_aggregated_measurement_tool_definition,
)
from .data_tool import (
    MeasurementDataTool,
    get_measurement_data_tool_definition,
)

__all__ = [
    # Models
    "MeasurementFilter",
    # Aggregated tool
    "AggregatedMeasurementTool",
    "get_aggregated_measurement_tool_definition",
    # Data tool
    "MeasurementDataTool",
    "get_measurement_data_tool_definition",
]
