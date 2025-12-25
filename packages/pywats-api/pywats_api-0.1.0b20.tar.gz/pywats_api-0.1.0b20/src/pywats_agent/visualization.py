"""
Visualization Payload System

Allows tools to pass rich data directly to the UI for visualization
WITHOUT including it in the LLM context (saving tokens and avoiding noise).

Architecture:
    ┌─────────────────────────────────────────────────────────────────┐
    │                    AgentResult                                  │
    │                                                                 │
    │  summary: str ──────────► LLM context (small, token-efficient)  │
    │  viz_payload: {...} ────► UI only (bypasses LLM completely)     │
    │  data: {...} ───────────► Full data (optional, for debugging)   │
    └─────────────────────────────────────────────────────────────────┘

The LLM receives only the summary. The UI receives the full visualization
payload and can render charts, tables, KPIs without bloating the context.

Example:
    >>> from pywats_agent.visualization import VizBuilder
    >>> 
    >>> # In a tool's _execute method:
    >>> result = AgentResult(
    ...     success=True,
    ...     summary="Yield trending down 2.3% over 7 days",
    ...     viz_payload=VizBuilder.line_chart(
    ...         title="Yield Trend",
    ...         labels=["Mon", "Tue", "Wed", "Thu", "Fri"],
    ...         series=[
    ...             {"name": "Yield %", "values": [94.2, 93.1, 92.5, 91.8, 91.9]},
    ...             {"name": "Target", "values": [95, 95, 95, 95, 95]},
    ...         ],
    ...         reference_lines=[{"value": 95, "label": "Target", "color": "green"}]
    ...     )
    ... )
"""

from typing import Any, Dict, List, Optional, Literal, Union
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime, timezone


# =============================================================================
# Chart Types
# =============================================================================

class ChartType(str, Enum):
    """Supported chart types for visualization."""
    LINE = "line"                  # Time series, trends
    AREA = "area"                  # Filled line chart
    BAR = "bar"                    # Comparisons, categories
    HORIZONTAL_BAR = "horizontal_bar"
    STACKED_BAR = "stacked_bar"   # Stacked comparisons
    PIE = "pie"                    # Distribution
    DONUT = "donut"                # Distribution with center
    SCATTER = "scatter"            # Correlation
    BUBBLE = "bubble"              # 3-variable scatter
    HEATMAP = "heatmap"            # Matrix data (e.g., step/station)
    TABLE = "table"                # Tabular data
    GAUGE = "gauge"                # Single KPI
    PARETO = "pareto"              # Pareto analysis (bar + cumulative line)
    HISTOGRAM = "histogram"        # Distribution
    BOX = "box"                    # Statistical distribution
    CONTROL = "control"            # SPC control chart (with UCL/LCL)
    WATERFALL = "waterfall"        # Show contributions to total
    FUNNEL = "funnel"              # Process funnel
    TREEMAP = "treemap"            # Hierarchical data


# =============================================================================
# Data Models
# =============================================================================

class DataSeries(BaseModel):
    """A single data series for charting."""
    name: str = Field(description="Series name for legend")
    values: List[Any] = Field(description="Data values")
    color: Optional[str] = Field(default=None, description="Color override (hex or name)")
    type: Optional[str] = Field(default=None, description="Series type for mixed charts")
    y_axis: Optional[str] = Field(default=None, description="Which y-axis (left/right)")
    
    # For scatter/bubble charts
    x_values: Optional[List[Any]] = Field(default=None, description="X values for scatter")
    sizes: Optional[List[float]] = Field(default=None, description="Bubble sizes")


class ReferenceLine(BaseModel):
    """Reference line on a chart (target, limit, etc.)."""
    value: float
    label: Optional[str] = None
    color: str = "gray"
    style: Literal["solid", "dashed", "dotted"] = "dashed"
    axis: Literal["x", "y"] = "y"


class Annotation(BaseModel):
    """Annotation on a chart (point out specific events)."""
    x: Any  # X position (label index or value)
    y: Optional[float] = None
    text: str
    color: Optional[str] = None


class ChartPayload(BaseModel):
    """Payload for chart visualization."""
    chart_type: ChartType
    title: Optional[str] = None
    subtitle: Optional[str] = None
    
    # Data
    labels: List[str] = Field(default_factory=list, description="X-axis labels or categories")
    series: List[DataSeries] = Field(default_factory=list)
    
    # Reference lines (targets, limits)
    reference_lines: List[ReferenceLine] = Field(default_factory=list)
    
    # Annotations (call out specific points)
    annotations: List[Annotation] = Field(default_factory=list)
    
    # Axis configuration
    x_axis_label: Optional[str] = None
    y_axis_label: Optional[str] = None
    y_axis_min: Optional[float] = None
    y_axis_max: Optional[float] = None
    
    # For dual-axis charts
    y2_axis_label: Optional[str] = None
    y2_axis_min: Optional[float] = None
    y2_axis_max: Optional[float] = None
    
    # Control chart specifics
    ucl: Optional[float] = Field(default=None, description="Upper control limit")
    lcl: Optional[float] = Field(default=None, description="Lower control limit")
    target: Optional[float] = Field(default=None, description="Target/center line")
    
    # Formatting
    value_format: str = Field(default=".1f", description="Python format string for values")
    percent_mode: bool = Field(default=False, description="Display as percentages")
    
    # Interactivity hints
    show_legend: bool = True
    show_tooltips: bool = True
    enable_zoom: bool = False
    enable_drill_down: bool = False
    
    # Chart-specific options (flexible)
    options: Dict[str, Any] = Field(default_factory=dict)


class TableColumn(BaseModel):
    """Column definition for table visualization."""
    key: str = Field(description="Data key in row dict")
    label: str = Field(description="Display header")
    type: Literal["string", "number", "percent", "date", "status", "link"] = "string"
    sortable: bool = True
    width: Optional[str] = None
    format: Optional[str] = None  # Format string for numbers
    align: Literal["left", "center", "right"] = "left"
    
    # Conditional formatting
    highlight_positive: bool = False
    highlight_negative: bool = False
    status_colors: Optional[Dict[str, str]] = None  # {"Passed": "green", "Failed": "red"}


class TablePayload(BaseModel):
    """Payload for table visualization."""
    title: Optional[str] = None
    columns: List[TableColumn]
    rows: List[Dict[str, Any]]
    
    # Pagination
    total_rows: Optional[int] = None
    page: int = 1
    page_size: int = 50
    
    # Sorting
    default_sort_key: Optional[str] = None
    default_sort_desc: bool = False
    
    # Row highlighting
    highlight_rules: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Rules like {'condition': 'status == Failed', 'color': 'red'}"
    )
    
    # Export options
    exportable: bool = True
    export_filename: Optional[str] = None


class KPIPayload(BaseModel):
    """Payload for KPI/gauge visualization."""
    title: str
    value: float
    unit: Optional[str] = None
    format: str = ".1f"
    
    # Thresholds for coloring (red/yellow/green)
    thresholds: Optional[Dict[str, float]] = Field(
        default=None,
        description="{'good': 95, 'warn': 90} - above good=green, above warn=yellow, else red"
    )
    invert_thresholds: bool = Field(
        default=False,
        description="If True, lower is better (e.g., defect rate)"
    )
    
    # Trend indicator
    trend: Optional[Literal["up", "down", "flat"]] = None
    trend_value: Optional[float] = None
    trend_period: Optional[str] = None  # "vs last week", "vs yesterday"
    trend_is_good: Optional[bool] = None
    
    # Comparison
    comparison_value: Optional[float] = None
    comparison_label: Optional[str] = None
    
    # Sparkline (mini chart)
    sparkline_values: Optional[List[float]] = None
    sparkline_labels: Optional[List[str]] = None
    
    # Gauge specifics
    min_value: float = 0
    max_value: float = 100
    show_gauge: bool = False


class DrillDownOption(BaseModel):
    """Option for drilling down into data."""
    label: str
    action: str  # Tool to call
    params: Dict[str, Any] = Field(default_factory=dict)
    description: Optional[str] = None


class VisualizationPayload(BaseModel):
    """
    Complete visualization payload that bypasses LLM context.
    
    This is sent to the UI alongside the agent response but is NOT
    included in the conversation context sent to the LLM.
    
    The UI application should:
    1. Check viz_type to determine what to render
    2. Extract the appropriate payload (chart, table, kpis, etc.)
    3. Render using a charting library (Chart.js, Recharts, etc.)
    4. Optionally show drill-down options for further exploration
    """
    
    # What type of visualization
    viz_type: Literal["chart", "table", "kpi", "multi", "dashboard"] = Field(
        description="Primary visualization type"
    )
    
    # Single visualizations
    chart: Optional[ChartPayload] = None
    table: Optional[TablePayload] = None
    kpi: Optional[KPIPayload] = None
    
    # Multiple visualizations (for dashboards/multi-view)
    charts: List[ChartPayload] = Field(default_factory=list)
    tables: List[TablePayload] = Field(default_factory=list)
    kpis: List[KPIPayload] = Field(default_factory=list)
    
    # Layout hints for multi-visualization
    layout: Optional[str] = Field(
        default=None,
        description="Layout hint: 'grid', 'vertical', 'horizontal', 'dashboard'"
    )
    
    # Drill-down support
    drill_down_options: List[DrillDownOption] = Field(default_factory=list)
    
    # Context for UI (not for LLM)
    context_id: Optional[str] = Field(
        default=None,
        description="ID to correlate with cached data for drill-down"
    )
    
    # Raw data info (for export without including full data)
    raw_data_available: bool = False
    raw_data_row_count: Optional[int] = None
    raw_data_endpoint: Optional[str] = None  # API endpoint to fetch full data
    
    # Metadata
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source_tool: Optional[str] = None


# =============================================================================
# Builder Helpers
# =============================================================================

class VizBuilder:
    """
    Fluent builder for creating visualization payloads.
    
    Makes it easy for tools to create properly structured visualizations
    without manually constructing all the nested objects.
    
    Example:
        >>> payload = VizBuilder.line_chart(
        ...     title="Yield Trend",
        ...     labels=dates,
        ...     series=[{"name": "Yield", "values": yields}],
        ... )
    """
    
    @staticmethod
    def line_chart(
        title: str,
        labels: List[str],
        series: List[Union[DataSeries, Dict[str, Any]]],
        *,
        subtitle: Optional[str] = None,
        reference_lines: Optional[List[Union[ReferenceLine, Dict[str, Any]]]] = None,
        y_axis_label: Optional[str] = None,
        y_axis_min: Optional[float] = None,
        y_axis_max: Optional[float] = None,
        percent_mode: bool = False,
        source_tool: Optional[str] = None,
    ) -> VisualizationPayload:
        """Create a line chart visualization."""
        return VisualizationPayload(
            viz_type="chart",
            chart=ChartPayload(
                chart_type=ChartType.LINE,
                title=title,
                subtitle=subtitle,
                labels=labels,
                series=[DataSeries(**s) if isinstance(s, dict) else s for s in series],
                reference_lines=[
                    ReferenceLine(**r) if isinstance(r, dict) else r 
                    for r in (reference_lines or [])
                ],
                y_axis_label=y_axis_label,
                y_axis_min=y_axis_min,
                y_axis_max=y_axis_max,
                percent_mode=percent_mode,
            ),
            source_tool=source_tool,
        )
    
    @staticmethod
    def area_chart(
        title: str,
        labels: List[str],
        series: List[Union[DataSeries, Dict[str, Any]]],
        *,
        stacked: bool = False,
        **kwargs
    ) -> VisualizationPayload:
        """Create an area chart visualization."""
        payload = VizBuilder.line_chart(title, labels, series, **kwargs)
        payload.chart.chart_type = ChartType.AREA
        payload.chart.options["stacked"] = stacked
        return payload
    
    @staticmethod
    def bar_chart(
        title: str,
        labels: List[str],
        series: List[Union[DataSeries, Dict[str, Any]]],
        *,
        subtitle: Optional[str] = None,
        horizontal: bool = False,
        stacked: bool = False,
        y_axis_label: Optional[str] = None,
        percent_mode: bool = False,
        source_tool: Optional[str] = None,
    ) -> VisualizationPayload:
        """Create a bar chart visualization."""
        chart_type = ChartType.HORIZONTAL_BAR if horizontal else ChartType.BAR
        if stacked:
            chart_type = ChartType.STACKED_BAR
            
        return VisualizationPayload(
            viz_type="chart",
            chart=ChartPayload(
                chart_type=chart_type,
                title=title,
                subtitle=subtitle,
                labels=labels,
                series=[DataSeries(**s) if isinstance(s, dict) else s for s in series],
                y_axis_label=y_axis_label,
                percent_mode=percent_mode,
            ),
            source_tool=source_tool,
        )
    
    @staticmethod
    def pie_chart(
        title: str,
        labels: List[str],
        values: List[float],
        *,
        donut: bool = False,
        subtitle: Optional[str] = None,
        source_tool: Optional[str] = None,
    ) -> VisualizationPayload:
        """Create a pie/donut chart visualization."""
        return VisualizationPayload(
            viz_type="chart",
            chart=ChartPayload(
                chart_type=ChartType.DONUT if donut else ChartType.PIE,
                title=title,
                subtitle=subtitle,
                labels=labels,
                series=[DataSeries(name="Values", values=values)],
            ),
            source_tool=source_tool,
        )
    
    @staticmethod
    def pareto_chart(
        title: str,
        labels: List[str],
        values: List[float],
        *,
        subtitle: Optional[str] = None,
        cumulative_label: str = "Cumulative %",
        source_tool: Optional[str] = None,
    ) -> VisualizationPayload:
        """Create a Pareto chart (bar + cumulative line)."""
        # Sort by value descending
        sorted_pairs = sorted(zip(labels, values), key=lambda x: x[1], reverse=True)
        sorted_labels = [p[0] for p in sorted_pairs]
        sorted_values = [p[1] for p in sorted_pairs]
        
        # Calculate cumulative percentage
        total = sum(sorted_values)
        cumulative = []
        running = 0
        for v in sorted_values:
            running += v
            cumulative.append((running / total * 100) if total > 0 else 0)
        
        return VisualizationPayload(
            viz_type="chart",
            chart=ChartPayload(
                chart_type=ChartType.PARETO,
                title=title,
                subtitle=subtitle,
                labels=sorted_labels,
                series=[
                    DataSeries(name="Count", values=sorted_values, type="bar"),
                    DataSeries(name=cumulative_label, values=cumulative, type="line", y_axis="right"),
                ],
                y2_axis_label=cumulative_label,
                y2_axis_min=0,
                y2_axis_max=100,
            ),
            source_tool=source_tool,
        )
    
    @staticmethod
    def control_chart(
        title: str,
        labels: List[str],
        values: List[float],
        *,
        ucl: Optional[float] = None,
        lcl: Optional[float] = None,
        target: Optional[float] = None,
        subtitle: Optional[str] = None,
        y_axis_label: Optional[str] = None,
        source_tool: Optional[str] = None,
    ) -> VisualizationPayload:
        """Create an SPC control chart with control limits."""
        ref_lines = []
        if ucl is not None:
            ref_lines.append(ReferenceLine(value=ucl, label="UCL", color="red", style="dashed"))
        if lcl is not None:
            ref_lines.append(ReferenceLine(value=lcl, label="LCL", color="red", style="dashed"))
        if target is not None:
            ref_lines.append(ReferenceLine(value=target, label="Target", color="green", style="solid"))
        
        return VisualizationPayload(
            viz_type="chart",
            chart=ChartPayload(
                chart_type=ChartType.CONTROL,
                title=title,
                subtitle=subtitle,
                labels=labels,
                series=[DataSeries(name="Value", values=values)],
                reference_lines=ref_lines,
                ucl=ucl,
                lcl=lcl,
                target=target,
                y_axis_label=y_axis_label,
            ),
            source_tool=source_tool,
        )
    
    @staticmethod
    def heatmap(
        title: str,
        x_labels: List[str],
        y_labels: List[str],
        values: List[List[float]],
        *,
        subtitle: Optional[str] = None,
        value_format: str = ".1f",
        color_scale: Optional[str] = None,  # "green-red", "blue-red", etc.
        source_tool: Optional[str] = None,
    ) -> VisualizationPayload:
        """Create a heatmap visualization."""
        # Flatten for series format
        series = []
        for i, row_label in enumerate(y_labels):
            series.append(DataSeries(name=row_label, values=values[i]))
        
        return VisualizationPayload(
            viz_type="chart",
            chart=ChartPayload(
                chart_type=ChartType.HEATMAP,
                title=title,
                subtitle=subtitle,
                labels=x_labels,
                series=series,
                value_format=value_format,
                options={"y_labels": y_labels, "color_scale": color_scale},
            ),
            source_tool=source_tool,
        )
    
    @staticmethod
    def histogram(
        title: str,
        values: List[float],
        *,
        bins: int = 20,
        subtitle: Optional[str] = None,
        x_axis_label: Optional[str] = None,
        source_tool: Optional[str] = None,
    ) -> VisualizationPayload:
        """Create a histogram visualization."""
        return VisualizationPayload(
            viz_type="chart",
            chart=ChartPayload(
                chart_type=ChartType.HISTOGRAM,
                title=title,
                subtitle=subtitle,
                series=[DataSeries(name="Distribution", values=values)],
                x_axis_label=x_axis_label,
                y_axis_label="Frequency",
                options={"bins": bins},
            ),
            source_tool=source_tool,
        )
    
    @staticmethod
    def scatter(
        title: str,
        x_values: List[float],
        y_values: List[float],
        *,
        series_name: str = "Data",
        x_axis_label: Optional[str] = None,
        y_axis_label: Optional[str] = None,
        subtitle: Optional[str] = None,
        source_tool: Optional[str] = None,
    ) -> VisualizationPayload:
        """Create a scatter plot visualization."""
        return VisualizationPayload(
            viz_type="chart",
            chart=ChartPayload(
                chart_type=ChartType.SCATTER,
                title=title,
                subtitle=subtitle,
                series=[DataSeries(name=series_name, values=y_values, x_values=x_values)],
                x_axis_label=x_axis_label,
                y_axis_label=y_axis_label,
            ),
            source_tool=source_tool,
        )
    
    @staticmethod
    def table(
        columns: List[Union[TableColumn, Dict[str, Any]]],
        rows: List[Dict[str, Any]],
        *,
        title: Optional[str] = None,
        total_rows: Optional[int] = None,
        default_sort_key: Optional[str] = None,
        default_sort_desc: bool = False,
        exportable: bool = True,
        source_tool: Optional[str] = None,
    ) -> VisualizationPayload:
        """Create a table visualization."""
        return VisualizationPayload(
            viz_type="table",
            table=TablePayload(
                title=title,
                columns=[TableColumn(**c) if isinstance(c, dict) else c for c in columns],
                rows=rows,
                total_rows=total_rows or len(rows),
                default_sort_key=default_sort_key,
                default_sort_desc=default_sort_desc,
                exportable=exportable,
            ),
            source_tool=source_tool,
        )
    
    @staticmethod
    def kpi(
        title: str,
        value: float,
        *,
        unit: Optional[str] = None,
        format: str = ".1f",
        thresholds: Optional[Dict[str, float]] = None,
        trend: Optional[Literal["up", "down", "flat"]] = None,
        trend_value: Optional[float] = None,
        trend_period: Optional[str] = None,
        trend_is_good: Optional[bool] = None,
        sparkline_values: Optional[List[float]] = None,
        show_gauge: bool = False,
        source_tool: Optional[str] = None,
    ) -> VisualizationPayload:
        """Create a single KPI visualization."""
        return VisualizationPayload(
            viz_type="kpi",
            kpi=KPIPayload(
                title=title,
                value=value,
                unit=unit,
                format=format,
                thresholds=thresholds,
                trend=trend,
                trend_value=trend_value,
                trend_period=trend_period,
                trend_is_good=trend_is_good,
                sparkline_values=sparkline_values,
                show_gauge=show_gauge,
            ),
            source_tool=source_tool,
        )
    
    @staticmethod
    def kpi_row(
        kpis: List[Union[KPIPayload, Dict[str, Any]]],
        *,
        source_tool: Optional[str] = None,
    ) -> VisualizationPayload:
        """Create a row of multiple KPIs."""
        return VisualizationPayload(
            viz_type="multi",
            kpis=[KPIPayload(**k) if isinstance(k, dict) else k for k in kpis],
            layout="horizontal",
            source_tool=source_tool,
        )
    
    @staticmethod
    def dashboard(
        *,
        kpis: Optional[List[Union[KPIPayload, Dict[str, Any]]]] = None,
        charts: Optional[List[Union[ChartPayload, Dict[str, Any]]]] = None,
        tables: Optional[List[Union[TablePayload, Dict[str, Any]]]] = None,
        layout: str = "dashboard",
        source_tool: Optional[str] = None,
    ) -> VisualizationPayload:
        """Create a multi-component dashboard visualization."""
        return VisualizationPayload(
            viz_type="dashboard",
            kpis=[KPIPayload(**k) if isinstance(k, dict) else k for k in (kpis or [])],
            charts=[ChartPayload(**c) if isinstance(c, dict) else c for c in (charts or [])],
            tables=[TablePayload(**t) if isinstance(t, dict) else t for t in (tables or [])],
            layout=layout,
            source_tool=source_tool,
        )
    
    @staticmethod
    def with_drill_down(
        payload: VisualizationPayload,
        options: List[Union[DrillDownOption, Dict[str, Any]]],
    ) -> VisualizationPayload:
        """Add drill-down options to an existing visualization."""
        payload.drill_down_options = [
            DrillDownOption(**o) if isinstance(o, dict) else o for o in options
        ]
        if payload.chart:
            payload.chart.enable_drill_down = True
        return payload


# =============================================================================
# Utility Functions
# =============================================================================

def merge_visualizations(
    *payloads: VisualizationPayload,
    layout: str = "vertical"
) -> VisualizationPayload:
    """
    Merge multiple visualization payloads into a single dashboard.
    
    Useful when a tool wants to return multiple charts/tables.
    """
    all_charts = []
    all_tables = []
    all_kpis = []
    all_drill_downs = []
    
    for p in payloads:
        if p.chart:
            all_charts.append(p.chart)
        if p.table:
            all_tables.append(p.table)
        if p.kpi:
            all_kpis.append(p.kpi)
        all_charts.extend(p.charts)
        all_tables.extend(p.tables)
        all_kpis.extend(p.kpis)
        all_drill_downs.extend(p.drill_down_options)
    
    return VisualizationPayload(
        viz_type="dashboard",
        charts=all_charts,
        tables=all_tables,
        kpis=all_kpis,
        drill_down_options=all_drill_downs,
        layout=layout,
    )


def empty_visualization() -> VisualizationPayload:
    """Create an empty visualization (no data to show)."""
    return VisualizationPayload(viz_type="chart")
