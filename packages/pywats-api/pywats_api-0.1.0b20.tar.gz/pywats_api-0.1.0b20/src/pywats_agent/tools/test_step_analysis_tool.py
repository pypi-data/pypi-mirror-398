"""
Test step analysis tool for AI agents.

Provides intelligent test step failure analysis with semantic filtering.
"""

from typing import Any, Dict, List, Optional, TYPE_CHECKING
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

from ..result import AgentResult

if TYPE_CHECKING:
    from pywats import pyWATS


class TestStepAnalysisFilter(BaseModel):
    """
    Test step analysis filter for AI agents.
    
    This is the LLM-friendly interface that provides step-level failure
    analysis and statistics for manufacturing test data.
    """
    
    # Required filters
    part_number: str = Field(
        description="Product part number to analyze (required, e.g., 'WIDGET-001')"
    )
    test_operation: str = Field(
        description="Test operation to analyze (required, e.g., 'FCT', 'EOL', '100')"
    )
    
    # Optional filters
    revision: Optional[str] = Field(
        default=None,
        description="Filter by product revision (e.g., 'A', '1.0')"
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
    
    # Analysis options
    run: int = Field(
        default=1,
        description="Run number to analyze (default: 1 for first run)"
    )
    max_count: int = Field(
        default=10000,
        description="Maximum number of test results to analyze (default: 10000)"
    )


class TestStepAnalysisTool:
    """
    Intelligent test step analysis tool for AI agents.
    
    Provides detailed step-level statistics including pass rates,
    failure counts, and measurement data for manufacturing tests.
    
    Example:
        >>> tool = TestStepAnalysisTool(api)
        >>> 
        >>> result = tool.analyze(TestStepAnalysisFilter(
        ...     part_number="WIDGET-001",
        ...     test_operation="FCT",
        ...     days=7
        ... ))
        >>> 
        >>> # Returns detailed step statistics including:
        >>> # - Step execution counts
        >>> # - Pass/fail/error statistics
        >>> # - Measurement data (if available)
        >>> # - Failure rates per step
    """
    
    name = "analyze_test_steps"
    description = """
Analyze test step execution statistics and failure patterns.

⚠️ SECONDARY TOOL - Use analyze_yield FIRST for overall metrics!
Only use this tool when you need STEP-LEVEL details after understanding
overall yield from analyze_yield, or when user specifically asks about
individual test steps, measurements, or step-level failures.

Use this tool to answer questions like:
- "Which test steps are failing for WIDGET-001?" 
- "What are the failure rates for each step in FCT?"
- "Show me step-level statistics for product X"
- "Which test step causes the most failures?"
- "Get measurement statistics for each test step"

DO NOT use this tool for:
- Overall yield, FPY, pass rate -> use analyze_yield
- Top runners, volume, unit counts -> use analyze_yield
- Trends, comparisons by station/product -> use analyze_yield
- Best/worst performers -> use analyze_yield

Provides detailed execution statistics for each test step including:
- Total executions, passes, failures, errors
- Pass rate and failure rate
- Step timing information (if available)
- Measurement data (min, max, avg, limits)
- Step type and grouping information
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
                "part_number": {
                    "type": "string",
                    "description": "Product part number to analyze (required)"
                },
                "test_operation": {
                    "type": "string",
                    "description": "Test operation to analyze (required, e.g., 'FCT', 'EOL')"
                },
                "revision": {
                    "type": "string",
                    "description": "Filter by product revision (optional)"
                },
                "days": {
                    "type": "integer",
                    "description": "Number of days to analyze (default: 30)",
                    "default": 30
                },
                "run": {
                    "type": "integer",
                    "description": "Run number to analyze (default: 1)",
                    "default": 1
                },
                "max_count": {
                    "type": "integer",
                    "description": "Maximum number of results to analyze (default: 10000)",
                    "default": 10000
                },
            },
            "required": ["part_number", "test_operation"]
        }
    
    def analyze(self, filter_input: TestStepAnalysisFilter) -> AgentResult:
        """
        Analyze test steps with the given filter.
        
        Args:
            filter_input: TestStepAnalysisFilter with parameters
            
        Returns:
            AgentResult with step analysis data and summary
        """
        try:
            # Call the API using the convenience method
            data = self._api.analytics.get_test_step_analysis_for_operation(
                part_number=filter_input.part_number,
                test_operation=filter_input.test_operation,
                revision=filter_input.revision,
                days=filter_input.days,
                run=filter_input.run,
                max_count=filter_input.max_count,
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
                    "step_count": len(data),
                    "part_number": filter_input.part_number,
                    "test_operation": filter_input.test_operation,
                    "revision": filter_input.revision,
                    "days": filter_input.days,
                    "run": filter_input.run,
                }
            )
            
        except Exception as e:
            return AgentResult.fail(f"Test step analysis failed: {str(e)}")
    
    def analyze_from_dict(self, params: Dict[str, Any]) -> AgentResult:
        """
        Analyze test steps from a dictionary of parameters.
        
        This is the main entry point for agent tool calls.
        
        Args:
            params: Dictionary of parameters from LLM tool call
            
        Returns:
            AgentResult with step analysis data and summary
        """
        filter_input = TestStepAnalysisFilter(**params)
        return self.analyze(filter_input)
    
    def _build_summary(
        self, 
        data: List[Any], 
        filter_input: TestStepAnalysisFilter
    ) -> str:
        """Build a human-readable summary of the step analysis."""
        
        # Calculate aggregate statistics
        total_steps = len(data)
        steps_with_failures = sum(1 for d in data if (d.step_failed_count or 0) > 0)
        total_executions = sum(d.step_count or 0 for d in data)
        total_failures = sum(d.step_failed_count or 0 for d in data)
        
        # Find worst performing steps (by failure count)
        sorted_by_failures = sorted(
            [d for d in data if (d.step_failed_count or 0) > 0],
            key=lambda x: x.step_failed_count or 0,
            reverse=True
        )
        
        # Build summary text
        parts = [
            f"Test step analysis for {filter_input.part_number}"
        ]
        
        if filter_input.revision:
            parts[0] += f" (revision {filter_input.revision})"
        
        parts[0] += f" - {filter_input.test_operation} operation (last {filter_input.days} days):"
        
        parts.append(f"• Total steps analyzed: {total_steps}")
        parts.append(f"• Total step executions: {total_executions:,}")
        parts.append(f"• Steps with failures: {steps_with_failures}")
        parts.append(f"• Total failures: {total_failures:,}")
        
        if total_executions > 0:
            failure_rate = (total_failures / total_executions) * 100
            parts.append(f"• Overall step failure rate: {failure_rate:.2f}%")
        
        # Add top failing steps
        if sorted_by_failures:
            parts.append("\nTop failing steps:")
            for i, step in enumerate(sorted_by_failures[:5], 1):
                step_name = step.step_name or "Unknown"
                fail_count = step.step_failed_count or 0
                total_count = step.step_count or 1
                fail_rate = (fail_count / total_count) * 100 if total_count > 0 else 0
                parts.append(f"  {i}. {step_name}: {fail_count:,} failures ({fail_rate:.1f}% of {total_count:,} runs)")
        
        return "\n".join(parts)
    
    def _build_no_data_summary(self, filter_input: TestStepAnalysisFilter) -> str:
        """Build summary when no data is found."""
        parts = [
            f"No test step data found for {filter_input.part_number}"
        ]
        
        if filter_input.revision:
            parts[0] += f" (revision {filter_input.revision})"
        
        parts[0] += f" with {filter_input.test_operation} operation in the last {filter_input.days} days."
        
        parts.append("\nPossible reasons:")
        parts.append("• No units tested in the specified time period")
        parts.append("• Part number or test operation name may be incorrect")
        parts.append("• Revision filter may be too restrictive")
        
        return "\n".join(parts)


def get_test_step_analysis_tool_definition() -> Dict[str, Any]:
    """
    Get the OpenAI tool definition for test step analysis.
    
    Returns:
        Dictionary with tool name, description, and parameters schema
    """
    return {
        "name": TestStepAnalysisTool.name,
        "description": TestStepAnalysisTool.description,
        "parameters": TestStepAnalysisTool.get_parameters_schema(),
    }
