from __future__ import annotations

from typing import Any, Dict, Iterable, Optional
import json
from collections.abc import Sequence

from .datastore import DataStore
from .envelope import ToolResultEnvelope
from .policy import ResponsePolicy, build_preview, normalize_summary
from .registry import ToolProfile, ToolRegistry


class ToolExecutor:
    """Canonical tool executor.

    - Controls tool availability via ToolProfile / enabled_tools.
    - Stores full data in DataStore and returns only a bounded envelope to the LLM.
    """

    def __init__(
        self,
        api: Any,
        *,
        registry: ToolRegistry,
        datastore: DataStore,
        profile: Optional[ToolProfile] = None,
        enabled_tools: Optional[Iterable[str]] = None,
        policy: Optional[ResponsePolicy] = None,
    ) -> None:
        self._api = api
        self._registry = registry
        self._datastore = datastore
        self._policy = policy or ResponsePolicy()

        if profile and enabled_tools:
            raise ValueError("Pass either profile or enabled_tools, not both")

        if profile:
            self._enabled_tools = list(profile.enabled_tools)
        elif enabled_tools is not None:
            self._enabled_tools = list(enabled_tools)
        else:
            self._enabled_tools = self._registry.list_names()

        self._instances: dict[str, Any] = {}

    @classmethod
    def with_default_tools(
        cls,
        api: Any,
        *,
        datastore: DataStore,
        profile_name: str | None = None,
        enabled_tools: Optional[Iterable[str]] = None,
        policy: Optional[ResponsePolicy] = None,
    ) -> "ToolExecutor":
        from .defaults import build_default_registry, get_profile

        profile = get_profile(profile_name) if profile_name else None
        return cls(
            api,
            registry=build_default_registry(),
            datastore=datastore,
            profile=profile,
            enabled_tools=enabled_tools,
            policy=policy,
        )

    def list_tools(self) -> list[str]:
        return list(self._enabled_tools)

    def get_openai_tools(self) -> list[dict[str, Any]]:
        return [
            {"type": "function", "function": d}
            for d in self._registry.definitions(enabled_tools=self._enabled_tools)
        ]

    def get_tool_definitions(self) -> list[dict[str, Any]]:
        """Return tool definitions in the same shape as OpenAI function schemas."""
        return self._registry.definitions(enabled_tools=self._enabled_tools)

    def execute(self, tool_name: str, parameters: Dict[str, Any]) -> ToolResultEnvelope:
        if tool_name not in self._enabled_tools:
            return ToolResultEnvelope(
                ok=False,
                summary=f"Tool '{tool_name}' is not enabled",
                error="tool_not_enabled",
            )

        try:
            tool = self._get_instance(tool_name)

            # Optional HTTP trace capture (UI/debug only): if the API exposes a
            # WATS HttpClient with capture_traces(), we collect all calls made
            # during tool execution and store them out-of-band.
            http_traces: list[dict[str, Any]] | None = None
            http_client = getattr(self._api, "_http_client", None)
            capture = getattr(http_client, "capture_traces", None) if http_client is not None else None

            def _unpack_tool_result(result: Any) -> tuple[bool, str, Any, dict[str, Any], Any | None]:
                # Tools historically return (ok, summary, data, metadata). We also support
                # an optional visualization sidecar as a 5th element: viz_payload.
                if not isinstance(result, tuple):
                    raise TypeError(f"Tool '{tool_name}' returned non-tuple result: {type(result).__name__}")
                if len(result) == 4:
                    ok, summary, data, metadata = result
                    return bool(ok), str(summary), data, (metadata or {}), None
                if len(result) == 5:
                    ok, summary, data, metadata, viz_payload = result
                    return bool(ok), str(summary), data, (metadata or {}), viz_payload
                raise TypeError(
                    f"Tool '{tool_name}' returned tuple of length {len(result)}; expected 4 or 5"
                )

            if callable(capture):
                with capture() as traces:
                    ok, summary, data, metadata, viz_payload = _unpack_tool_result(tool.execute(parameters))
                    http_traces = list(traces)
            else:
                ok, summary, data, metadata, viz_payload = _unpack_tool_result(tool.execute(parameters))

            summary, summary_truncated = normalize_summary(summary, policy=self._policy)

            data_key: str | None = None
            viz_key: str | None = None
            preview: dict[str, Any] | None = None
            metrics: dict[str, Any] = {"tool": tool_name, **(metadata or {})}
            warnings: list[str] = []

            # Guardrail: treat empty list data as explicit NO_DATA. This prevents
            # confusing "blank" previews / empty dataset handles in UIs.
            if isinstance(data, list) and len(data) == 0:
                data = None
                metrics["no_data"] = True
                metrics.setdefault("record_count", 0)

            # Guardrail: never allow a blank summary.
            if not isinstance(summary, str) or not summary.strip():
                if ok:
                    summary = "NO_DATA: tool returned an empty summary."
                    metrics.setdefault("no_data", True)
                else:
                    summary = "Error: tool failed without an error summary."

            if http_traces:
                trace_key = self._datastore.put(http_traces)
                metrics["http_trace_key"] = trace_key
                metrics["http_trace_count"] = len(http_traces)
                warnings.append("HTTP trace stored out-of-band; use http_trace_key to retrieve")

            if viz_payload is not None:
                viz_key = self._datastore.put(viz_payload)
                metrics["viz_key"] = viz_key
                warnings.append("Visualization stored out-of-band; use viz_key to retrieve")

            if data is not None:
                data_key = self._datastore.put(data)
                preview, preview_metrics = build_preview(data, policy=self._policy)
                metrics.update(preview_metrics)
                metrics["data_key"] = data_key
                warnings.append("Full data stored out-of-band; use data_key to retrieve")

            if summary_truncated:
                warnings.append("Summary truncated")
                metrics["summary_truncated"] = True

            return ToolResultEnvelope(
                ok=bool(ok),
                summary=summary,
                data_key=data_key,
                viz_key=viz_key,
                preview=preview,
                metrics=metrics,
                warnings=warnings,
            )
        except Exception as e:
            return ToolResultEnvelope(
                ok=False,
                summary=f"Error executing '{tool_name}': {e}",
                error=type(e).__name__,
            )

    def execute_openai_tool_call(self, tool_call: Any) -> ToolResultEnvelope:
        tool_name = tool_call.function.name
        parameters = json.loads(tool_call.function.arguments)
        return self.execute(tool_name, parameters)

    def _get_instance(self, tool_name: str) -> Any:
        existing = self._instances.get(tool_name)
        if existing is not None:
            return existing
        cls = self._registry.get(tool_name)
        inst = cls(self._api)
        self._instances[tool_name] = inst
        return inst
