"""pyWATS Agent (BETA).

Public API policy (BETA): **no backwards compatibility**.

Use the canonical executor + result envelope (data handles + bounded previews).

Example:
    >>> from pywats import pyWATS
    >>> from pywats_agent import ToolExecutor, InMemoryDataStore
    >>>
    >>> api = pyWATS(base_url="...", token="...")
    >>> executor = ToolExecutor.with_default_tools(api, datastore=InMemoryDataStore())
    >>>
    >>> env = executor.execute("analyze_yield", {"part_number": "WIDGET-001"})
    >>> print(env.summary)
"""
from .visualization import (
    ChartType,
    DataSeries,
    ReferenceLine,
    Annotation,
    ChartPayload,
    TableColumn,
    TablePayload,
    KPIPayload,
    DrillDownOption,
    VisualizationPayload,
    VizBuilder,
    merge_visualizations,
    empty_visualization,
)

# Agent core: registry/profiles + datastore handles + LLM-safe envelopes
from .agent import (
    AgentTool,
    DataStore,
    InMemoryDataStore,
    build_default_registry,
    get_profile,
    ResponsePolicy,
    ToolExecutor,
    ToolProfile,
    ToolRegistry,
    ToolResultEnvelope,
    ToolInput,
)

__version__ = "0.1.0b20"
__all__ = [
    # Agent core
    "AgentTool",
    "DataStore",
    "InMemoryDataStore",
    "build_default_registry",
    "get_profile",
    "ResponsePolicy",
    "ToolExecutor",
    "ToolProfile",
    "ToolRegistry",
    "ToolResultEnvelope",
    "ToolInput",
    # Visualization (sidecar pattern)
    "ChartType",
    "DataSeries",
    "ReferenceLine",
    "Annotation",
    "ChartPayload",
    "TableColumn",
    "TablePayload",
    "KPIPayload",
    "DrillDownOption",
    "VisualizationPayload",
    "VizBuilder",
    "merge_visualizations",
    "empty_visualization",
]
