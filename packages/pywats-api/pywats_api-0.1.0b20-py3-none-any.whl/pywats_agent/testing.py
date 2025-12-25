"""
Test harness for agent tool selection and execution.

This module provides utilities for testing agent behavior without
requiring actual LLM calls, enabling:
- Verification of tool routing logic
- Testing parameter extraction
- Dry-run execution with mock data
- Integration testing with real API but controlled inputs

Example:
    >>> from pywats_agent import ToolExecutor, InMemoryDataStore
    >>> from pywats_agent.testing import AgentTestHarness
    >>> 
    >>> harness = AgentTestHarness(executor)
    >>> 
    >>> # Test that a prompt selects the right tool
    >>> harness.assert_tool_selected(
    ...     "What's the yield for WIDGET-001?",
    ...     expected_tool="analyze_yield"
    ... )
    >>> 
    >>> # Test parameter extraction
    >>> harness.assert_parameters_extracted(
    ...     "Show yield for WIDGET-001 by station for last 7 days",
    ...     expected={"part_number": "WIDGET-001", "perspective": "by station", "days": 7}
    ... )
"""

import json
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

from .context import AgentContext
from .agent.envelope import ToolResultEnvelope

if TYPE_CHECKING:
    from .agent.executor import ToolExecutor


@dataclass
class ToolCall:
    """
    Represents a single tool call (actual or expected).
    """
    tool_name: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    def matches(self, other: "ToolCall", strict: bool = False) -> bool:
        """
        Check if this tool call matches another.
        
        Args:
            other: The other tool call to compare
            strict: If True, parameters must match exactly.
                   If False, only checks that expected params are present.
        """
        if self.tool_name != other.tool_name:
            return False
        
        if strict:
            return self.parameters == other.parameters
        
        # Non-strict: check that all expected parameters are present with correct values
        for key, expected_value in self.parameters.items():
            if key not in other.parameters:
                return False
            if other.parameters[key] != expected_value:
                return False
        
        return True


@dataclass
class TestCase:
    """
    A single test case for agent behavior.
    """
    name: str
    prompt: str
    expected_tool: str
    expected_parameters: Dict[str, Any] = field(default_factory=dict)
    context: Optional[AgentContext] = None
    description: str = ""


@dataclass 
class TestResult:
    """
    Result of running a test case.
    """
    test_case: TestCase
    passed: bool
    actual_tool: Optional[str] = None
    actual_parameters: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    agent_result: Optional[ToolResultEnvelope] = None


# ============================================================================
# Tool Selection Patterns
# ============================================================================

# Patterns that suggest specific tools based on keywords
TOOL_SELECTION_PATTERNS: Dict[str, List[str]] = {
    "analyze_yield": [
        r"\byield\b",
        r"\bfpy\b",
        r"\bfirst.?pass\b",
        r"\bpass.?rate\b",
        r"\bfailure.?rate\b",
        r"\bproduction.?quality\b",
        r"\bdaily.?trend\b",
    ],
    "analyze_test_steps": [
        r"\btest.?step\b",
        r"\bstep.?fail\b",
        r"\bwhich.?step\b",
        r"\bwhat.?step\b",
        r"\bfailing.?step\b",
        r"\bstep.?statistic\b",
        r"\bstep.?analysis\b",
        r"\bsteps?.?are.?failing\b",
        r"\bstep.*caus",
        r"\bsteps?\b.*\b(FCT|EOL|ICT|FVT|AOI)\b",
        r"\b(FCT|EOL|ICT|FVT|AOI)\b.*\bsteps?\b",
        r"failing.*\b(FCT|EOL|ICT|FVT|AOI)\b",
        r"step\s+statistic",
    ],
    "get_measurement_statistics": [
        r"\bmeasurement.?(stat|avg|average|cpk|cp\b|mean|std)",
        r"\b(cpk|cp)\b",
        r"\bprocess.?capability\b",
        r"\baggregate.*measurement\b",
        r"\bmeasurement.*aggregate\b",
    ],
    "get_measurement_data": [
        r"\bmeasurement.?data\b",
        r"\braw.?measurements?\b",
        r"\bindividual.?measurements?\b",
        r"\bmeasurement.?point\b",
        r"\blast.?\d+.?measurement\b",
        r"\brecent.?measurement\b",
        r"\blast.?\d+.*measurement\b",
        r"\bget.*(measurement|reading)\b",
        r"\bshow.*(measurement|reading)\b",
        r"\blast\s+\d+\s+\w*\s*measurement",
    ],
}

# Parameter extraction patterns
PARAMETER_PATTERNS: Dict[str, List[tuple]] = {
    "part_number": [
        (r"(?:for|product|part|pn)\s+['\"]?([A-Z0-9]+-[A-Z0-9]+)['\"]?", 1),
        (r"['\"]([A-Z0-9]+-[A-Z0-9]+)['\"]", 1),
    ],
    "days": [
        (r"(?:last|past)\s+(\d+)\s+days?", 1),
        (r"(\d+)\s+days?", 1),
    ],
    "perspective": [
        (r"\bby\s+(station|product|day|daily|operator)\b", 1),
        (r"\b(overall|total)\s+yield\b", "overall"),
        (r"\b(daily|day)\s+(yield|trend)\b", "daily"),
        (r"\byield\s+(trend|daily)\b", "daily"),
    ],
    "test_operation": [
        (r"for\s+(FCT|EOL|ICT|FVT|AOI)\b", 1),  # "for FCT" - must check first
        (r"in\s+(FCT|EOL|ICT|FVT|AOI)\b", 1),   # "in FCT"
        (r"\b(FCT|EOL|ICT|FVT|AOI)\b", 1),      # standalone FCT etc
    ],
    "measurement_path": [
        (r"measurement\s+['\"]([^'\"]+)['\"]", 1),
        (r"['\"]([^'\"]+/[^'\"]+)['\"]", 1),  # Path with slashes
    ],
}


def _pattern_based_tool_selection(prompt: str) -> Optional[str]:
    """
    Select a tool based on keyword patterns in the prompt.
    
    This is a simple heuristic for testing - real agents use LLMs.
    """
    prompt_lower = prompt.lower()
    
    scores: Dict[str, int] = {}
    for tool_name, patterns in TOOL_SELECTION_PATTERNS.items():
        score = 0
        for pattern in patterns:
            if re.search(pattern, prompt_lower):
                score += 1
        if score > 0:
            scores[tool_name] = score
    
    if not scores:
        return None
    
    # Return tool with highest score
    return max(scores, key=scores.get)


def _pattern_based_parameter_extraction(prompt: str) -> Dict[str, Any]:
    """
    Extract parameters from prompt using regex patterns.
    
    This is a simple heuristic for testing - real agents use LLMs.
    """
    params = {}
    
    for param_name, patterns in PARAMETER_PATTERNS.items():
        for pattern_tuple in patterns:
            pattern = pattern_tuple[0]
            group_or_value = pattern_tuple[1]
            
            match = re.search(pattern, prompt, re.IGNORECASE)
            if match:
                if isinstance(group_or_value, int):
                    params[param_name] = match.group(group_or_value)
                else:
                    params[param_name] = group_or_value
                break
    
    # Normalize perspective values
    if "perspective" in params:
        perspective_map = {
            "station": "by station",
            "product": "by product", 
            "day": "daily",
            "daily": "daily",
            "operator": "by operator",
            "overall": "overall",
            "total": "overall",
        }
        params["perspective"] = perspective_map.get(
            params["perspective"].lower(), 
            params["perspective"]
        )
    
    # Convert days to int
    if "days" in params:
        params["days"] = int(params["days"])
    
    return params


class AgentTestHarness:
    """
    Test harness for verifying agent tool selection and execution.
    
    Provides methods for testing without LLM calls:
    - Pattern-based tool selection simulation
    - Parameter extraction testing
    - Dry-run execution with validation
    - Real API integration tests
    
    Example:
        >>> harness = AgentTestHarness(executor)
        >>> 
        >>> # Quick tool selection test
        >>> tool = harness.predict_tool("What's the yield for WIDGET-001?")
        >>> assert tool == "analyze_yield"
        >>> 
        >>> # Full test case
        >>> result = harness.run_test(TestCase(
        ...     name="yield_by_station",
        ...     prompt="Show yield by station for WIDGET-001",
        ...     expected_tool="analyze_yield",
        ...     expected_parameters={"part_number": "WIDGET-001", "perspective": "by station"}
        ... ))
        >>> assert result.passed
    """
    
    def __init__(
        self, 
        executor: "ToolExecutor",
        context: Optional[AgentContext] = None
    ):
        """
        Initialize the test harness.
        
        Args:
            executor: ToolExecutor instance to test
            context: Optional default context for tests
        """
        self._executor = executor
        self._default_context = context
    
    def predict_tool(self, prompt: str) -> Optional[str]:
        """
        Predict which tool would be selected for a prompt.
        
        Uses pattern matching - not as accurate as an LLM but useful
        for basic verification.
        
        Args:
            prompt: The user's natural language query
            
        Returns:
            Predicted tool name or None if no match
        """
        return _pattern_based_tool_selection(prompt)
    
    def extract_parameters(self, prompt: str) -> Dict[str, Any]:
        """
        Extract parameters from a natural language prompt.
        
        Uses pattern matching - not as accurate as an LLM but useful
        for basic verification.
        
        Args:
            prompt: The user's natural language query
            
        Returns:
            Dictionary of extracted parameters
        """
        return _pattern_based_parameter_extraction(prompt)
    
    def simulate_tool_call(self, prompt: str) -> ToolCall:
        """
        Simulate what tool call would be generated from a prompt.
        
        Args:
            prompt: The user's natural language query
            
        Returns:
            ToolCall with predicted tool and parameters
        """
        tool = self.predict_tool(prompt)
        params = self.extract_parameters(prompt)
        return ToolCall(tool_name=tool or "unknown", parameters=params)
    
    def run_test(
        self, 
        test_case: TestCase,
        execute_real: bool = False
    ) -> TestResult:
        """
        Run a single test case.
        
        Args:
            test_case: The test case to run
            execute_real: If True, actually execute the tool against the API.
                         If False, only verify tool selection and parameters.
        
        Returns:
            TestResult with pass/fail status and details
        """
        # Simulate the tool call
        simulated = self.simulate_tool_call(test_case.prompt)
        
        # Check tool selection
        if simulated.tool_name != test_case.expected_tool:
            return TestResult(
                test_case=test_case,
                passed=False,
                actual_tool=simulated.tool_name,
                actual_parameters=simulated.parameters,
                error=f"Tool mismatch: expected '{test_case.expected_tool}', got '{simulated.tool_name}'"
            )
        
        # Check parameters (non-strict - only verify expected ones are present)
        for key, expected_value in test_case.expected_parameters.items():
            if key not in simulated.parameters:
                return TestResult(
                    test_case=test_case,
                    passed=False,
                    actual_tool=simulated.tool_name,
                    actual_parameters=simulated.parameters,
                    error=f"Missing parameter: '{key}'"
                )
            if simulated.parameters[key] != expected_value:
                return TestResult(
                    test_case=test_case,
                    passed=False,
                    actual_tool=simulated.tool_name,
                    actual_parameters=simulated.parameters,
                    error=f"Parameter mismatch for '{key}': expected '{expected_value}', got '{simulated.parameters[key]}'"
                )
        
        # Optionally execute for real
        agent_result = None
        if execute_real:
            try:
                # Merge context defaults with extracted parameters
                context = test_case.context or self._default_context
                params = simulated.parameters.copy()
                if context:
                    defaults = context.get_default_parameters()
                    for key, value in defaults.items():
                        if key not in params:
                            params[key] = value
                
                agent_result = self._executor.execute(
                    test_case.expected_tool, 
                    params
                )
            except Exception as e:
                return TestResult(
                    test_case=test_case,
                    passed=False,
                    actual_tool=simulated.tool_name,
                    actual_parameters=simulated.parameters,
                    error=f"Execution failed: {str(e)}",
                    agent_result=None
                )
        
        return TestResult(
            test_case=test_case,
            passed=True,
            actual_tool=simulated.tool_name,
            actual_parameters=simulated.parameters,
            agent_result=agent_result
        )
    
    def run_tests(
        self, 
        test_cases: List[TestCase],
        execute_real: bool = False
    ) -> List[TestResult]:
        """
        Run multiple test cases.
        
        Args:
            test_cases: List of test cases to run
            execute_real: If True, actually execute tools against API
            
        Returns:
            List of TestResult objects
        """
        return [self.run_test(tc, execute_real) for tc in test_cases]
    
    def assert_tool_selected(
        self, 
        prompt: str, 
        expected_tool: str,
        msg: Optional[str] = None
    ) -> None:
        """
        Assert that a prompt would select a specific tool.
        
        Raises AssertionError if the wrong tool is predicted.
        
        Args:
            prompt: The user's natural language query
            expected_tool: The tool name that should be selected
            msg: Optional custom error message
        """
        actual = self.predict_tool(prompt)
        if actual != expected_tool:
            error_msg = msg or f"Expected tool '{expected_tool}' but got '{actual}' for prompt: {prompt}"
            raise AssertionError(error_msg)
    
    def assert_parameters_extracted(
        self,
        prompt: str,
        expected: Dict[str, Any],
        strict: bool = False,
        msg: Optional[str] = None
    ) -> None:
        """
        Assert that specific parameters are extracted from a prompt.
        
        Args:
            prompt: The user's natural language query
            expected: Expected parameters (keys and values)
            strict: If True, actual must match exactly.
                   If False, only checks expected params are present.
            msg: Optional custom error message
        """
        actual = self.extract_parameters(prompt)
        
        if strict and actual != expected:
            error_msg = msg or f"Parameters don't match exactly. Expected: {expected}, Got: {actual}"
            raise AssertionError(error_msg)
        
        for key, value in expected.items():
            if key not in actual:
                error_msg = msg or f"Missing parameter '{key}'. Expected: {expected}, Got: {actual}"
                raise AssertionError(error_msg)
            if actual[key] != value:
                error_msg = msg or f"Parameter '{key}' mismatch. Expected: {value}, Got: {actual[key]}"
                raise AssertionError(error_msg)
    
    def get_tool_definitions_summary(self) -> str:
        """
        Get a human-readable summary of available tools.
        
        Useful for understanding what tools are available.
        """
        definitions = self._executor.get_tool_definitions()
        
        lines = ["Available Tools:", "=" * 50]
        for defn in definitions:
            lines.append(f"\n{defn['name']}")
            lines.append("-" * len(defn['name']))
            
            # Truncate description
            desc = defn.get('description', 'No description')
            if len(desc) > 200:
                desc = desc[:200] + "..."
            lines.append(desc)
            
            # List parameters
            params = defn.get('parameters', {}).get('properties', {})
            required = defn.get('parameters', {}).get('required', [])
            
            if params:
                lines.append("\nParameters:")
                for name, schema in params.items():
                    req = " (required)" if name in required else ""
                    ptype = schema.get('type', 'any')
                    lines.append(f"  - {name}: {ptype}{req}")
        
        return "\n".join(lines)
    
    def dry_run(
        self,
        prompt: str,
        context: Optional[AgentContext] = None
    ) -> Dict[str, Any]:
        """
        Perform a dry run showing what would happen for a prompt.
        
        Returns a dictionary with predicted tool, parameters, and context.
        Does NOT execute against the API.
        
        Args:
            prompt: The user's natural language query
            context: Optional context to apply
            
        Returns:
            Dictionary with prediction details
        """
        context = context or self._default_context
        
        predicted_tool = self.predict_tool(prompt)
        extracted_params = self.extract_parameters(prompt)
        
        # Apply context defaults
        final_params = extracted_params.copy()
        if context:
            defaults = context.get_default_parameters()
            for key, value in defaults.items():
                if key not in final_params:
                    final_params[key] = value
        
        return {
            "prompt": prompt,
            "predicted_tool": predicted_tool,
            "extracted_parameters": extracted_params,
            "context_defaults": context.get_default_parameters() if context else {},
            "final_parameters": final_params,
            "context_summary": context.to_system_prompt() if context else None,
            "would_execute": predicted_tool in self._executor.list_tools(),
        }


# ============================================================================
# Pre-built Test Suites
# ============================================================================

def get_yield_tool_test_cases() -> List[TestCase]:
    """Get standard test cases for the yield analysis tool."""
    return [
        TestCase(
            name="basic_yield",
            prompt="What's the yield for WIDGET-001?",
            expected_tool="analyze_yield",
            expected_parameters={"part_number": "WIDGET-001"},
            description="Basic yield query with product"
        ),
        TestCase(
            name="yield_by_station",
            prompt="Show yield by station for WIDGET-001",
            expected_tool="analyze_yield",
            expected_parameters={"part_number": "WIDGET-001", "perspective": "by station"},
            description="Yield grouped by station"
        ),
        TestCase(
            name="yield_last_7_days",
            prompt="What's the yield for WIDGET-001 for the last 7 days?",
            expected_tool="analyze_yield",
            expected_parameters={"part_number": "WIDGET-001", "days": 7},
            description="Yield with time range"
        ),
        TestCase(
            name="daily_yield",
            prompt="Show daily yield trend for WIDGET-001",
            expected_tool="analyze_yield",
            expected_parameters={"part_number": "WIDGET-001", "perspective": "daily"},
            description="Daily yield trend"
        ),
    ]


def get_step_analysis_test_cases() -> List[TestCase]:
    """Get standard test cases for the test step analysis tool."""
    return [
        TestCase(
            name="failing_steps",
            prompt="Which test steps are failing for WIDGET-001 in FCT?",
            expected_tool="analyze_test_steps",
            expected_parameters={"part_number": "WIDGET-001", "test_operation": "FCT"},
            description="Basic step failure query"
        ),
        TestCase(
            name="step_statistics",
            prompt="Show step statistics for WIDGET-001 in EOL",
            expected_tool="analyze_test_steps",
            expected_parameters={"part_number": "WIDGET-001", "test_operation": "EOL"},
            description="Step statistics query"
        ),
    ]


def get_measurement_test_cases() -> List[TestCase]:
    """Get standard test cases for measurement tools."""
    return [
        TestCase(
            name="measurement_stats",
            prompt="What's the Cpk for 'Main/Voltage Test/Output' measurement?",
            expected_tool="get_measurement_statistics",
            expected_parameters={},  # Path extraction is complex
            description="Measurement statistics with Cpk"
        ),
        TestCase(
            name="recent_measurements",
            prompt="Show the last 100 measurements for WIDGET-001",
            expected_tool="get_measurement_data",
            expected_parameters={"part_number": "WIDGET-001"},
            description="Recent measurement data"
        ),
    ]


def get_all_test_cases() -> List[TestCase]:
    """Get all standard test cases."""
    return (
        get_yield_tool_test_cases() + 
        get_step_analysis_test_cases() + 
        get_measurement_test_cases()
    )
