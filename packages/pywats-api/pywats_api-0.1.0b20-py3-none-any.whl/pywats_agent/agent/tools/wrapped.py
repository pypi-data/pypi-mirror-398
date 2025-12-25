from __future__ import annotations

from typing import Any

from ...result import AgentResult
from ..tooling import AgentTool

# Import existing input models + tool implementations (wrapped into the canonical tool interface)
from ...tools.yield_pkg import YieldAnalysisTool, YieldFilter
from ...tools.step import TestStepAnalysisTool, TestStepAnalysisFilter
from ...tools.measurement import (
    AggregatedMeasurementTool,
    MeasurementDataTool,
    MeasurementFilter,
)
from ...tools.unit import UnitAnalysisInput, UnitAnalysisTool
from ...tools.subunit.subunit_tool import SubUnitAnalysisInput, SubUnitAnalysisTool
from ...tools.control_panel import ControlPanelInput, ControlPanelTool
from ...tools.root_cause import (
    FailureModeFilter,
    RootCauseInput,
)
from ...tools.root_cause import DimensionalAnalysisTool as _FailureModesTool
from ...tools.root_cause import RootCauseAnalysisTool as _RootCauseTool
from ...tools.capability import ProcessCapabilityInput, ProcessCapabilityTool


def _convert_agent_result(result: AgentResult) -> tuple[bool, str, Any, dict[str, Any], Any | None]:
    def _is_blank(text: Any) -> bool:
        return not isinstance(text, str) or not text.strip()

    def _kpi_prefix_for(data: Any, metadata: dict[str, Any]) -> str | None:
        # Prefer explicit, machine-parsable prefixes to prevent UI/LLM hallucinations.
        if data is None:
            if metadata.get("no_data") is True:
                return "NO_DATA:"
            return None

        if isinstance(data, list):
            rc = len(data)
            metadata.setdefault("record_count", rc)
            if rc == 0:
                metadata["no_data"] = True
                return "NO_DATA: rows=0"

            # If a tool already computed KPIs, keep summary compact but structured.
            kpis = metadata.get("kpis")
            if isinstance(kpis, dict):
                parts: list[str] = [f"rows={kpis.get('rows', rc)}"]
                if kpis.get("total_units") is not None:
                    parts.append(f"units={kpis.get('total_units')}")
                if kpis.get("total_reports") is not None:
                    parts.append(f"reports={kpis.get('total_reports')}")
                if kpis.get("avg_yield") is not None:
                    try:
                        parts.append(f"avg={float(kpis.get('avg_yield')):.1f}%")
                    except Exception:
                        pass
                return "KPIS: " + "; ".join(parts)

            return f"KPIS: rows={rc}"

        # Mapping / object: leave alone; most of these already have concise summaries.
        return None

    if result.success:
        metadata: dict[str, Any] = dict(result.metadata or {})
        data = result.data
        viz_payload = None
        if getattr(result, "viz_payload", None) is not None:
            try:
                viz_payload = result.viz_payload.model_dump()
            except Exception:
                # Best-effort: still allow sidecar storage of opaque payload.
                viz_payload = result.viz_payload

        # Treat empty list as explicit NO_DATA for UI gating.
        if isinstance(data, list) and len(data) == 0:
            data = None
            metadata["no_data"] = True
            metadata.setdefault("record_count", 0)

        summary = result.summary
        if _is_blank(summary):
            summary = "NO_DATA: tool returned an empty summary."
            metadata.setdefault("no_data", True)

        prefix = _kpi_prefix_for(data, metadata)
        if prefix and not summary.lstrip().startswith(("KPIS:", "NO_DATA:")):
            summary = prefix + "\n" + summary

        return True, summary, data, metadata, viz_payload

    metadata: dict[str, Any] = dict(result.metadata or {})
    if result.error:
        metadata["error"] = result.error
    summary = result.summary
    if _is_blank(summary):
        summary = "NO_DATA: tool failed without an error summary."
    if not summary.lstrip().startswith(("NO_DATA:", "Error:")):
        # Keep failures explicit and machine-readable.
        summary = "Error: " + summary
    return False, summary, None, metadata, None


class AnalyzeYieldTool(AgentTool[YieldFilter]):
    """Analyze yield (canonical tool interface)."""

    name = "analyze_yield"
    description = "Analyze yield (canonical envelope + out-of-band data handles)."
    input_model = YieldFilter

    def __init__(self, api: Any):
        super().__init__(api)
        self._tool = YieldAnalysisTool(api)

    def run(self, input_obj: YieldFilter):
        result = self._tool.analyze(input_obj)
        return _convert_agent_result(result)


class AnalyzeTestStepsTool(AgentTool[TestStepAnalysisFilter]):
    """Analyze step-level statistics (canonical tool interface)."""

    name = "analyze_test_steps"
    description = "Analyze step-level statistics (canonical envelope + out-of-band data handles)."
    input_model = TestStepAnalysisFilter

    def __init__(self, api: Any):
        super().__init__(api)
        self._tool = TestStepAnalysisTool(api)

    def run(self, input_obj: TestStepAnalysisFilter):
        result = self._tool.analyze(input_obj)
        return _convert_agent_result(result)


class GetMeasurementStatisticsTool(AgentTool[MeasurementFilter]):
    """Get aggregated measurement statistics (canonical tool interface)."""

    name = "get_measurement_statistics"
    description = "Get aggregated measurement statistics (canonical envelope + out-of-band data handles)."
    input_model = MeasurementFilter

    def __init__(self, api: Any):
        super().__init__(api)
        self._tool = AggregatedMeasurementTool(api)

    def run(self, input_obj: MeasurementFilter):
        result = self._tool.analyze(input_obj)
        return _convert_agent_result(result)


class GetMeasurementDataTool(AgentTool[MeasurementFilter]):
    """Get individual measurement datapoints (canonical tool interface)."""

    name = "get_measurement_data"
    description = "Get individual measurement datapoints (canonical envelope + out-of-band data handles)."
    input_model = MeasurementFilter

    def __init__(self, api: Any):
        super().__init__(api)
        self._tool = MeasurementDataTool(api)

    def run(self, input_obj: MeasurementFilter):
        result = self._tool.analyze(input_obj)
        return _convert_agent_result(result)


class AnalyzeUnitTool(AgentTool[UnitAnalysisInput]):
    """Analyze a single unit (canonical tool interface)."""

    name = "analyze_unit"
    description = "Analyze a single unit (canonical envelope + out-of-band data handles)."
    input_model = UnitAnalysisInput

    def __init__(self, api: Any):
        super().__init__(api)
        self._tool = UnitAnalysisTool(api)

    def run(self, input_obj: UnitAnalysisInput):
        result = self._tool.analyze(input_obj)
        return _convert_agent_result(result)


class AnalyzeSubUnitsTool(AgentTool[SubUnitAnalysisInput]):
    """Analyze sub-unit (component) relationships (canonical tool interface)."""

    name = "analyze_subunits"
    description = "Analyze sub-unit (component) relationships (canonical envelope + out-of-band data handles)."
    input_model = SubUnitAnalysisInput

    def __init__(self, api: Any):
        super().__init__(api)
        self._tool = SubUnitAnalysisTool(api)

    def run(self, input_obj: SubUnitAnalysisInput):
        result = self._tool.analyze(input_obj)
        return _convert_agent_result(result)


class ControlPanelTool(AgentTool[ControlPanelInput]):
    """Administrative WATS management operations (canonical tool interface)."""

    name = "control_panel"
    description = "Administrative WATS management operations (canonical envelope + out-of-band data handles)."
    input_model = ControlPanelInput

    def __init__(self, api: Any):
        super().__init__(api)
        self._tool = ControlPanelTool(api)

    def run(self, input_obj: ControlPanelInput):
        result = self._tool.analyze(input_obj)
        return _convert_agent_result(result)


class AnalyzeProcessCapabilityTool(AgentTool[ProcessCapabilityInput]):
    """Advanced capability analysis (canonical tool interface)."""

    name = "analyze_process_capability"
    description = "Advanced capability analysis (canonical envelope + out-of-band data handles)."
    input_model = ProcessCapabilityInput

    def __init__(self, api: Any):
        super().__init__(api)
        self._tool = ProcessCapabilityTool(api)

    def run(self, input_obj: ProcessCapabilityInput):
        result = self._tool.analyze(input_obj)
        return _convert_agent_result(result)


class AnalyzeRootCauseTool(AgentTool[RootCauseInput]):
    """Top-down root cause investigation (canonical tool interface)."""

    name = "analyze_root_cause"
    description = "Top-down root cause investigation (canonical envelope + out-of-band data handles)."
    input_model = RootCauseInput

    def __init__(self, api: Any):
        super().__init__(api)
        self._tool = _RootCauseTool(api)

    def run(self, input_obj: RootCauseInput):
        result = self._tool.analyze(input_obj)
        return _convert_agent_result(result)


class AnalyzeFailureModesTool(AgentTool[FailureModeFilter]):
    """Dimensional yield splitting to detect failure modes (canonical tool interface)."""

    name = "analyze_failure_modes"
    description = "Dimensional yield splitting to detect failure modes (canonical envelope + out-of-band data handles)."
    input_model = FailureModeFilter

    def __init__(self, api: Any):
        super().__init__(api)
        self._tool = _FailureModesTool(api)

    def run(self, input_obj: FailureModeFilter):
        result = self._tool.analyze(input_obj)
        return _convert_agent_result(result)
