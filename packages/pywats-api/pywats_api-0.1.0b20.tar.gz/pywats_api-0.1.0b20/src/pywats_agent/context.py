"""
Agent context for passing UI state and pre-loaded data.

This module provides a standardized way to pass context from
a frontend application (browser) to the agent, enabling:
- Context-aware tool selection
- Pre-loaded data to avoid redundant API calls
- User preferences and filters already in view
- Autonomy/rigor configuration

Example:
    >>> from pywats_agent import AgentContext, AgentConfig, AnalyticalRigor
    >>> 
    >>> # Frontend sends context with the query
    >>> context = AgentContext(
    ...     current_product="WIDGET-001",
    ...     current_station="Line1-FCT",
    ...     date_range=("2024-12-01", "2024-12-19"),
    ...     config=AgentConfig(rigor=AnalyticalRigor.THOROUGH),
    ... )
    >>>
    >>> # NOTE: ToolExecutor does not apply AgentContext defaults.
    >>> # Apply context defaults in your orchestration layer before calling the tool.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

from .autonomy import AgentConfig


class VisibleData(BaseModel):
    """
    Data already loaded and visible in the UI.
    
    Use this to avoid redundant API calls when the agent
    needs data that's already on screen.
    """
    
    # Yield data currently displayed
    yield_data: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Yield statistics currently visible in the UI"
    )
    
    # Report data currently displayed
    reports: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Test reports currently visible (summary data)"
    )
    
    # Measurement data currently displayed
    measurements: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Measurement data currently visible"
    )
    
    # Step analysis data currently displayed
    step_analysis: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Test step analysis currently visible"
    )


class AgentContext(BaseModel):
    """
    Context passed from frontend to the agent.
    
    This captures the current state of the user's view, including:
    - What product/station/test they're looking at
    - What date range is selected
    - What data is already loaded (to avoid redundant fetches)
    
    The context is used to:
    1. Provide default values for tool parameters
    2. Include relevant info in the system prompt
    3. Skip API calls when data is already available
    
    Example:
        >>> context = AgentContext(
        ...     current_product="WIDGET-001",
        ...     current_station="Line1-FCT",
        ...     current_page="yield_analysis",
        ... )
        >>> 
        >>> # Get system prompt addition
        >>> print(context.to_system_prompt())
        Current context:
        - Product: WIDGET-001
        - Station: Line1-FCT
        - Page: yield_analysis
    """
    
    # Current selection state
    current_product: Optional[str] = Field(
        default=None,
        description="Currently selected product part number"
    )
    current_revision: Optional[str] = Field(
        default=None,
        description="Currently selected product revision"
    )
    current_station: Optional[str] = Field(
        default=None,
        description="Currently selected test station"
    )
    current_test_operation: Optional[str] = Field(
        default=None,
        description="Currently selected test operation (e.g., 'FCT', 'EOL')"
    )
    current_serial_number: Optional[str] = Field(
        default=None,
        description="Currently selected unit serial number"
    )
    
    # Date range
    date_from: Optional[Union[datetime, str]] = Field(
        default=None,
        description="Start of selected date range"
    )
    date_to: Optional[Union[datetime, str]] = Field(
        default=None,
        description="End of selected date range"
    )
    
    # UI state
    current_page: Optional[str] = Field(
        default=None,
        description="Current page/view name (e.g., 'yield_analysis', 'reports', 'measurements')"
    )
    
    # Pre-loaded data
    visible_data: Optional[VisibleData] = Field(
        default=None,
        description="Data already loaded and visible in the UI"
    )
    
    # Additional custom context
    custom: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional custom context from the frontend"
    )
    
    # Agent configuration (autonomy/rigor)
    config: Optional[AgentConfig] = Field(
        default=None,
        description="Agent behavior configuration (rigor level, write mode)"
    )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentContext":
        """
        Create context from a dictionary (e.g., from JSON request body).
        
        Args:
            data: Dictionary with context fields
            
        Returns:
            AgentContext instance
        """
        # Handle nested visible_data
        if "visible_data" in data and isinstance(data["visible_data"], dict):
            data["visible_data"] = VisibleData(**data["visible_data"])
        
        # Handle nested config
        if "config" in data and isinstance(data["config"], dict):
            data["config"] = AgentConfig(**data["config"])
        
        return cls(**data)
    
    def to_system_prompt(self) -> str:
        """
        Convert context to text for inclusion in agent system prompt.
        
        Returns:
            Human-readable context description
        """
        parts = []
        
        # Include config instructions first (most important)
        if self.config:
            parts.append(self.config.get_system_prompt())
            parts.append("")  # Blank line separator
        
        parts.append("Current context:")
        
        if self.current_product:
            line = f"- Product: {self.current_product}"
            if self.current_revision:
                line += f" (revision {self.current_revision})"
            parts.append(line)
        
        if self.current_station:
            parts.append(f"- Station: {self.current_station}")
        
        if self.current_test_operation:
            parts.append(f"- Test operation: {self.current_test_operation}")
        
        if self.current_serial_number:
            parts.append(f"- Serial number: {self.current_serial_number}")
        
        if self.date_from or self.date_to:
            date_from_str = str(self.date_from)[:10] if self.date_from else "start"
            date_to_str = str(self.date_to)[:10] if self.date_to else "now"
            parts.append(f"- Date range: {date_from_str} to {date_to_str}")
        
        if self.current_page:
            parts.append(f"- Page: {self.current_page}")
        
        if self.visible_data:
            loaded = []
            if self.visible_data.yield_data:
                loaded.append(f"yield ({len(self.visible_data.yield_data)} records)")
            if self.visible_data.reports:
                loaded.append(f"reports ({len(self.visible_data.reports)} records)")
            if self.visible_data.measurements:
                loaded.append(f"measurements ({len(self.visible_data.measurements)} records)")
            if self.visible_data.step_analysis:
                loaded.append(f"step analysis ({len(self.visible_data.step_analysis)} records)")
            if loaded:
                parts.append(f"- Data already loaded: {', '.join(loaded)}")
        
        if len(parts) == 1:
            return "No specific context provided."
        
        return "\n".join(parts)
    
    def get_default_parameters(self) -> Dict[str, Any]:
        """
        Get default tool parameters derived from context.
        
        These can be used to fill in missing parameters when
        the user doesn't explicitly specify them.
        
        Returns:
            Dictionary of parameter defaults
        """
        defaults = {}
        
        if self.current_product:
            defaults["part_number"] = self.current_product
        if self.current_revision:
            defaults["revision"] = self.current_revision
        if self.current_station:
            defaults["station_name"] = self.current_station
        if self.current_test_operation:
            defaults["test_operation"] = self.current_test_operation
        if self.current_serial_number:
            defaults["serial_number"] = self.current_serial_number
        if self.date_from:
            defaults["date_from"] = self.date_from
        if self.date_to:
            defaults["date_to"] = self.date_to
        
        return defaults
    
    def has_visible_yield_data(self) -> bool:
        """Check if yield data is already loaded."""
        return bool(self.visible_data and self.visible_data.yield_data)
    
    def has_visible_measurements(self) -> bool:
        """Check if measurement data is already loaded."""
        return bool(self.visible_data and self.visible_data.measurements)
    
    def has_visible_step_analysis(self) -> bool:
        """Check if step analysis data is already loaded."""
        return bool(self.visible_data and self.visible_data.step_analysis)
    
    def has_visible_reports(self) -> bool:
        """Check if report data is already loaded."""
        return bool(self.visible_data and self.visible_data.reports)
