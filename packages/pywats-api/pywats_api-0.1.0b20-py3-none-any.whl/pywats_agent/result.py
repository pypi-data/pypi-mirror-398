"""
Agent result wrapper for consistent responses.

Provides a standardized format for tool execution results,
including both structured data and human-readable summaries.

Visualization Sidecar:
    The viz_payload field allows tools to pass rich visualization data
    directly to the UI WITHOUT including it in the LLM context:
    
    ┌─────────────────────────────────────────────────────────────┐
    │                    AgentResult                              │
    │                                                             │
    │  summary ─────────► LLM context (small, token-efficient)    │
    │  viz_payload ─────► UI only (bypasses LLM completely)       │
    │  data ────────────► Full data (optional, for debugging)     │
    └─────────────────────────────────────────────────────────────┘
    
    Example:
        >>> from pywats_agent.visualization import VizBuilder
        >>> 
        >>> result = AgentResult.ok(
        ...     summary="Yield trending down 2.3% over 7 days",
        ...     viz_payload=VizBuilder.line_chart(
        ...         title="Yield Trend",
        ...         labels=["Mon", "Tue", "Wed"],
        ...         series=[{"name": "Yield", "values": [94, 93, 92]}]
        ...     )
        ... )
"""

from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from .visualization import VisualizationPayload


class AgentResult(BaseModel):
    """
    Standardized result from agent tool execution.
    
    Provides both structured data and human-readable summary
    for AI agents to consume and relay to users.
    
    Attributes:
        success: Whether the operation succeeded
        data: Structured data result (dict or list of dicts)
        summary: Human-readable summary of the result
        error: Error message if the operation failed
        metadata: Additional context (counts, averages, etc.)
    
    Example:
        >>> result = AgentResult.ok(
        ...     data=[{"station": "A", "fpy": 95.0}],
        ...     summary="Found 1 station with 95% FPY",
        ...     metadata={"total_records": 1}
        ... )
        >>> print(result.summary)
        "Found 1 station with 95% FPY"
    """
    
    success: bool = Field(
        description="Whether the operation succeeded"
    )
    data: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = Field(
        default=None, 
        description="Structured data result"
    )
    summary: str = Field(
        description="Human-readable summary of the result (sent to LLM)"
    )
    error: Optional[str] = Field(
        default=None, 
        description="Error message if failed"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata (counts, averages, etc.)"
    )
    viz_payload: Optional["VisualizationPayload"] = Field(
        default=None,
        description="Visualization payload for UI (NOT sent to LLM context)"
    )
    
    @classmethod
    def ok(
        cls,
        data: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None,
        summary: str = "Operation completed successfully",
        metadata: Optional[Dict[str, Any]] = None,
        viz_payload: Optional["VisualizationPayload"] = None
    ) -> "AgentResult":
        """
        Create a successful result.
        
        Args:
            data: The structured data to return
            summary: Human-readable summary (sent to LLM)
            metadata: Additional context
            viz_payload: Visualization for UI (bypasses LLM)
            
        Returns:
            AgentResult indicating success
        """
        return cls(
            success=True,
            data=data,
            summary=summary,
            metadata=metadata or {},
            viz_payload=viz_payload
        )
    
    @classmethod
    def fail(cls, message: str) -> "AgentResult":
        """
        Create an error result.
        
        Args:
            message: Error description
            
        Returns:
            AgentResult indicating failure
        """
        return cls(
            success=False,
            error=message,
            summary=f"Error: {message}"
        )
    
    def to_openai_response(self) -> str:
        """
        Format result for OpenAI tool response.
        
        NOTE: viz_payload is intentionally excluded - it goes to UI only,
        not to the LLM context. This keeps token usage low.
        
        Returns:
            JSON string suitable for OpenAI tool response
        """
        import json
        
        if self.success:
            return json.dumps({
                "success": True,
                "summary": self.summary,
                "data": self.data,
                "metadata": self.metadata
                # viz_payload intentionally omitted - UI only
            })
        else:
            return json.dumps({
                "success": False,
                "error": self.error
            })
    
    def to_ui_response(self) -> Dict[str, Any]:
        """
        Format result for UI consumption (includes viz_payload).
        
        The UI receives everything including visualization data.
        Use this when sending the response to the frontend.
        
        Returns:
            Dict with all fields including viz_payload
        """
        response = {
            "success": self.success,
            "summary": self.summary,
            "data": self.data,
            "metadata": self.metadata,
            "error": self.error,
        }
        
        if self.viz_payload:
            response["viz_payload"] = self.viz_payload.model_dump()
        
        return response
    
    def has_visualization(self) -> bool:
        """Check if this result has a visualization payload."""
        return self.viz_payload is not None
    
    def __str__(self) -> str:
        """Return the summary as string representation."""
        return self.summary


# Rebuild model to resolve forward reference
def _rebuild_model():
    """Rebuild AgentResult to resolve VisualizationPayload forward reference."""
    from .visualization import VisualizationPayload
    AgentResult.model_rebuild()

# Call at module load time
_rebuild_model()
