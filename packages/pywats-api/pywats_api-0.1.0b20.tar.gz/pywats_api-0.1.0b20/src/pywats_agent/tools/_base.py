"""
Base classes for all agent tools.

Provides common interfaces and patterns for building agent tools.
All tools should inherit from AgentTool and use ToolInput for parameters.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type, TYPE_CHECKING
from pydantic import BaseModel, ConfigDict

from ..result import AgentResult

if TYPE_CHECKING:
    from pywats import pyWATS


class ToolInput(BaseModel):
    """
    Base class for tool input parameters.
    
    All tool inputs should inherit from this class to ensure
    consistent validation and serialization behavior.
    """
    
    model_config = ConfigDict(extra="forbid")  # Reject unknown fields - catches API mismatches


class AgentTool(ABC):
    """
    Base class for all agent tools.
    
    Provides common interface for:
    - Tool metadata (name, description)
    - Parameter schema generation
    - Execution with consistent error handling
    - OpenAI/LLM-compatible tool definitions
    
    Example:
        >>> class MyTool(AgentTool):
        ...     name = "my_tool"
        ...     description = "Does something useful"
        ...     input_model = MyToolInput
        ...     
        ...     def _execute(self, input: MyToolInput) -> AgentResult:
        ...         # Implementation
        ...         return AgentResult.ok(data={}, summary="Done")
    """
    
    # Override these in subclasses
    name: str = ""
    description: str = ""
    input_model: Type[ToolInput] = ToolInput
    
    def __init__(self, api: "pyWATS"):
        """
        Initialize tool with pyWATS API instance.
        
        Args:
            api: pyWATS instance for API calls
        """
        self._api = api
    
    @classmethod
    def get_parameters_schema(cls) -> Dict[str, Any]:
        """
        Get OpenAI-compatible JSON schema for parameters.
        
        Returns:
            Dictionary with JSON schema for the input model
        """
        schema = cls.input_model.model_json_schema()
        
        # Convert to OpenAI function format
        return {
            "type": "object",
            "properties": schema.get("properties", {}),
            "required": schema.get("required", []),
        }
    
    @classmethod
    def get_definition(cls) -> Dict[str, Any]:
        """
        Get complete tool definition for LLM function calling.
        
        Returns:
            Dictionary with name, description, and parameters
        """
        return {
            "name": cls.name,
            "description": cls.description,
            "parameters": cls.get_parameters_schema(),
        }
    
    def execute(self, params: Dict[str, Any]) -> AgentResult:
        """
        Execute the tool with given parameters.
        
        Validates input, calls implementation, handles errors.
        
        Args:
            params: Dictionary of parameters from LLM
            
        Returns:
            AgentResult with data and summary
        """
        try:
            # Validate and parse input
            input_obj = self.input_model.model_validate(params)
            
            # Call implementation
            return self._execute(input_obj)
            
        except Exception as e:
            return AgentResult.error(
                error=str(e),
                error_type=type(e).__name__,
            )
    
    @abstractmethod
    def _execute(self, input: ToolInput) -> AgentResult:
        """
        Implement the tool's core logic.
        
        Override this method in subclasses.
        
        Args:
            input: Validated input object
            
        Returns:
            AgentResult with data and summary
        """
        pass


class AnalysisTool(AgentTool):
    """
    Base class for analysis tools that query data and provide insights.
    
    Adds common patterns for:
    - Date range handling
    - Filter building
    - Summary generation
    """
    
    def _build_date_range(
        self, 
        days: int,
        date_from: Optional[Any] = None,
        date_to: Optional[Any] = None,
    ) -> tuple:
        """
        Build date range from parameters.
        
        Args:
            days: Default number of days if no explicit dates
            date_from: Optional start date
            date_to: Optional end date
            
        Returns:
            Tuple of (date_from, date_to)
        """
        from datetime import datetime, timedelta
        
        if date_to is None:
            date_to = datetime.now()
        if date_from is None:
            date_from = date_to - timedelta(days=days)
            
        return date_from, date_to
