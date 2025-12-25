from __future__ import annotations

from .registry import ToolProfile, ToolRegistry
from .tools import (
    AnalyzeYieldTool,
    AnalyzeTestStepsTool,
    AnalyzeFailureModesTool,
    AnalyzeProcessCapabilityTool,
    AnalyzeRootCauseTool,
    AnalyzeSubUnitsTool,
    AnalyzeUnitTool,
    ControlPanelTool,
    GetMeasurementDataTool,
    GetMeasurementStatisticsTool,
)


DEFAULT_TOOL_CLASSES = (
    AnalyzeYieldTool,
    AnalyzeTestStepsTool,
    AnalyzeRootCauseTool,
    AnalyzeFailureModesTool,
    AnalyzeProcessCapabilityTool,
    GetMeasurementStatisticsTool,
    GetMeasurementDataTool,
    AnalyzeUnitTool,
    AnalyzeSubUnitsTool,
    ControlPanelTool,
)


def build_default_registry() -> ToolRegistry:
    reg = ToolRegistry()
    reg.register_many(DEFAULT_TOOL_CLASSES)
    return reg


PROFILES: dict[str, ToolProfile] = {
    "minimal": ToolProfile(name="minimal", enabled_tools=("analyze_yield",)),
    "analysis": ToolProfile(
        name="analysis",
        enabled_tools=(
            "analyze_yield",
            "analyze_test_steps",
            "analyze_root_cause",
            "analyze_failure_modes",
        ),
    ),
    "measurement": ToolProfile(
        name="measurement",
        enabled_tools=(
            "get_measurement_statistics",
            "get_measurement_data",
            "analyze_process_capability",
        ),
    ),
    "full": ToolProfile(
        name="full",
        enabled_tools=(
            "analyze_yield",
            "analyze_test_steps",
            "analyze_root_cause",
            "analyze_failure_modes",
            "analyze_process_capability",
            "get_measurement_statistics",
            "get_measurement_data",
            "analyze_unit",
            "analyze_subunits",
            "control_panel",
        ),
    ),
}


def get_profile(name: str) -> ToolProfile:
    return PROFILES[name]
