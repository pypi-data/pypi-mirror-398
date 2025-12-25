"""
Asset analysis models for AI agents.

Provides data structures for asset-related failure mode analysis,
health monitoring, and degradation tracking.
"""

from typing import Optional, List
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field

from pydantic import BaseModel, Field, ConfigDict


# =============================================================================
# Enums
# =============================================================================

class AssetHealthStatus(str, Enum):
    """Overall asset health status."""
    HEALTHY = "healthy"           # All metrics within normal range
    WARNING = "warning"           # Approaching limits (calibration/maintenance due soon)
    CRITICAL = "critical"         # Exceeded limits or overdue
    UNKNOWN = "unknown"           # Cannot determine (missing data)


class CalibrationStatus(str, Enum):
    """Asset calibration status."""
    CURRENT = "current"           # Calibration is up to date
    DUE_SOON = "due_soon"         # Within warning threshold
    OVERDUE = "overdue"           # Past due date
    UNKNOWN = "unknown"           # Never calibrated or no data


class AssetImpactLevel(str, Enum):
    """How much an asset impacts yield."""
    CRITICAL = "critical"         # Strong correlation with failures (>10% impact)
    HIGH = "high"                 # Significant correlation (5-10% impact)
    MODERATE = "moderate"         # Noticeable correlation (2-5% impact)
    LOW = "low"                   # Minor correlation (<2% impact)
    NONE = "none"                 # No measurable impact


class DegradationTrend(str, Enum):
    """Asset quality degradation trend."""
    DEGRADING = "degrading"       # Quality getting worse over time
    STABLE = "stable"             # No significant change
    IMPROVING = "improving"       # Quality improving (after maintenance)
    UNKNOWN = "unknown"           # Insufficient data


# =============================================================================
# Filter Models (Input)
# =============================================================================

class AssetDimensionFilter(BaseModel):
    """
    Filter for asset-based dimensional analysis.
    
    Use this to analyze yield by asset (fixture, station) as a failure mode
    dimension. When an asset shows statistically lower yield than peers,
    it becomes a root cause suspect.
    """
    
    # Required
    part_number: str = Field(
        description="Product part number to analyze (required)"
    )
    test_operation: str = Field(
        description="Test operation/process to analyze (required, e.g., 'FCT', 'EOL')"
    )
    
    # Asset filtering
    asset_type: Optional[str] = Field(
        default=None,
        description="Filter by asset type name (e.g., 'Fixture', 'Station', 'Probe Card')"
    )
    asset_serial: Optional[str] = Field(
        default=None,
        description="Specific asset serial number to analyze"
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
    min_unit_count: int = Field(
        default=30,
        description="Minimum units per asset for statistical validity"
    )
    significance_threshold: float = Field(
        default=0.02,
        description="Yield difference threshold to flag (default: 2%)"
    )
    
    model_config = ConfigDict(extra="forbid")


class AssetHealthFilter(BaseModel):
    """
    Filter for asset health check.
    
    Use this to check calibration and maintenance status of assets
    identified as potential root causes.
    """
    
    # Asset identification (at least one required)
    asset_serial: Optional[str] = Field(
        default=None,
        description="Asset serial number to check"
    )
    asset_serials: Optional[List[str]] = Field(
        default=None,
        description="List of asset serial numbers to check"
    )
    asset_type: Optional[str] = Field(
        default=None,
        description="Check all assets of this type"
    )
    
    # Filter options
    only_problematic: bool = Field(
        default=False,
        description="Only return assets with warning/critical status"
    )
    include_history: bool = Field(
        default=False,
        description="Include calibration/maintenance history logs"
    )
    
    model_config = ConfigDict(extra="forbid")


class AssetDegradationFilter(BaseModel):
    """
    Filter for asset quality degradation analysis.
    
    Use this to analyze how asset quality degrades over time and
    correlate with calibration cycles. Helps fine-tune calibration intervals.
    """
    
    # Asset identification
    asset_serial: str = Field(
        description="Asset serial number to analyze (required)"
    )
    
    # Analysis scope
    calibration_cycles: int = Field(
        default=3,
        description="Number of calibration cycles to analyze (default: 3)"
    )
    
    # Metrics to track
    track_cpk: bool = Field(
        default=True,
        description="Track Cpk trend over calibration cycle"
    )
    track_failure_rate: bool = Field(
        default=True,
        description="Track failure rate trend over calibration cycle"
    )
    
    # Context
    part_number: Optional[str] = Field(
        default=None,
        description="Limit analysis to specific product"
    )
    test_operation: Optional[str] = Field(
        default=None,
        description="Limit analysis to specific test operation"
    )
    
    model_config = ConfigDict(extra="forbid")


# =============================================================================
# Result Models (Output)
# =============================================================================

@dataclass
class AssetYieldImpact:
    """
    Yield impact of a specific asset.
    
    Represents how much an asset (fixture, station) differs from
    the baseline yield, indicating potential root cause.
    """
    asset_serial: str
    asset_name: Optional[str]
    asset_type: Optional[str]
    
    # Yield metrics
    unit_count: int
    yield_pct: float           # Asset's yield
    baseline_yield_pct: float  # Overall/peer yield
    yield_delta: float         # Difference (negative = worse)
    
    # Impact assessment
    impact_level: AssetImpactLevel
    is_suspect: bool           # True if statistically significant
    confidence: float          # Statistical confidence (0-1)
    
    # Failure details
    failure_count: int
    top_failing_steps: List[str] = field(default_factory=list)
    
    def __str__(self) -> str:
        sign = "-" if self.yield_delta < 0 else "+"
        return (
            f"{self.asset_serial}: {self.yield_pct:.1f}% "
            f"({sign}{abs(self.yield_delta):.1f}% vs baseline) "
            f"[{self.impact_level.value}]"
        )


@dataclass
class AssetHealthInfo:
    """
    Health status of an asset.
    
    Includes calibration and maintenance status with detailed metrics.
    """
    asset_serial: str
    asset_name: Optional[str]
    asset_type: Optional[str]
    
    # Overall status
    health_status: AssetHealthStatus
    
    # Calibration
    calibration_status: CalibrationStatus
    last_calibration_date: Optional[datetime]
    next_calibration_date: Optional[datetime]
    days_since_calibration: Optional[float]
    calibration_days_overdue: Optional[float]
    calibration_interval_days: Optional[float]
    
    # Usage counters
    running_count: Optional[int]        # Since last calibration
    running_count_limit: Optional[int]
    running_count_pct: Optional[float]  # % of limit used
    total_count: Optional[int]
    total_count_limit: Optional[int]
    
    # Maintenance
    last_maintenance_date: Optional[datetime]
    next_maintenance_date: Optional[datetime]
    days_since_maintenance: Optional[float]
    maintenance_days_overdue: Optional[float]
    
    # Warnings
    warnings: List[str] = field(default_factory=list)
    
    def __str__(self) -> str:
        return (
            f"{self.asset_serial}: {self.health_status.value.upper()} "
            f"(cal: {self.calibration_status.value})"
        )


@dataclass
class CalibrationCycleMetrics:
    """
    Quality metrics for one calibration cycle.
    
    Tracks how asset quality changes from post-calibration to
    pre-next-calibration.
    """
    cycle_number: int
    calibration_date: datetime
    next_calibration_date: Optional[datetime]
    
    # Time bins within cycle (early, mid, late)
    early_yield_pct: Optional[float]    # First 20% of cycle
    mid_yield_pct: Optional[float]      # Middle 60%
    late_yield_pct: Optional[float]     # Last 20% of cycle
    
    early_cpk: Optional[float]
    mid_cpk: Optional[float]
    late_cpk: Optional[float]
    
    early_failure_rate: Optional[float]
    mid_failure_rate: Optional[float]
    late_failure_rate: Optional[float]
    
    # Degradation assessment
    yield_degradation: Optional[float]  # Early - Late
    cpk_degradation: Optional[float]
    failure_rate_increase: Optional[float]
    
    unit_count: int


@dataclass
class AssetDegradationAnalysis:
    """
    Analysis of asset quality degradation over calibration cycles.
    
    Helps determine if calibration intervals are appropriate.
    """
    asset_serial: str
    asset_name: Optional[str]
    asset_type: Optional[str]
    
    # Overall assessment
    degradation_trend: DegradationTrend
    avg_yield_degradation_per_cycle: Optional[float]
    avg_cpk_degradation_per_cycle: Optional[float]
    
    # Calibration interval recommendation
    current_interval_days: Optional[float]
    recommended_interval_days: Optional[float]
    interval_adjustment: Optional[str]  # "shorten", "extend", "maintain"
    
    # Per-cycle data
    cycles: List[CalibrationCycleMetrics] = field(default_factory=list)
    
    # Insights
    insights: List[str] = field(default_factory=list)
    
    def __str__(self) -> str:
        return (
            f"{self.asset_serial}: {self.degradation_trend.value} "
            f"(recommendation: {self.interval_adjustment or 'N/A'})"
        )


# =============================================================================
# Aggregated Results
# =============================================================================

@dataclass
class AssetDimensionResult:
    """
    Result of asset-based dimensional analysis.
    
    Shows which assets are impacting yield and could be root causes.
    """
    # Query context
    part_number: str
    test_operation: str
    date_from: datetime
    date_to: datetime
    
    # Overall metrics
    total_units: int
    overall_yield_pct: float
    assets_analyzed: int
    
    # Suspect assets (statistically worse than baseline)
    suspect_assets: List[AssetYieldImpact] = field(default_factory=list)
    
    # All assets (for completeness)
    all_assets: List[AssetYieldImpact] = field(default_factory=list)
    
    # Summary
    summary: str = ""
    
    def __str__(self) -> str:
        suspects = len(self.suspect_assets)
        return (
            f"Asset Analysis: {self.assets_analyzed} assets, "
            f"{suspects} suspects identified"
        )


@dataclass
class AssetHealthResult:
    """
    Result of asset health check.
    
    Shows calibration and maintenance status for requested assets.
    """
    assets_checked: int
    healthy_count: int
    warning_count: int
    critical_count: int
    
    # Asset details
    assets: List[AssetHealthInfo] = field(default_factory=list)
    
    # Prioritized issues
    critical_assets: List[AssetHealthInfo] = field(default_factory=list)
    warning_assets: List[AssetHealthInfo] = field(default_factory=list)
    
    def __str__(self) -> str:
        return (
            f"Asset Health: {self.healthy_count} healthy, "
            f"{self.warning_count} warning, {self.critical_count} critical"
        )
