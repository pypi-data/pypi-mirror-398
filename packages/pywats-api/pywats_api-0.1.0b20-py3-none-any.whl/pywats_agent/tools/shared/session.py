"""
Analysis session infrastructure for stateful yield analysis.

Sessions enable:
- Fetch data once, analyze multiple ways
- Drill-down without re-fetching
- Pre-computed matrices for quick answers
- Token-efficient responses (insights, not raw data)

Usage:
    manager = SessionManager.get_instance()
    
    # Create session with fetched data
    session = manager.create_session(
        yield_data=[...],
        filter_params={...}
    )
    
    # Get session for drill-down
    session = manager.get_session(session_id)
    period_detail = session.get_period_detail("2024-12-15")
"""

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from enum import Enum
from threading import Lock
from dataclasses import dataclass, field
from pydantic import BaseModel, Field, ConfigDict

if TYPE_CHECKING:
    from pywats.domains.analytics import YieldData


class SessionType(str, Enum):
    """Type of analysis session."""
    TREND = "trend"           # Temporal analysis
    DEVIATION = "deviation"   # Dimensional/configuration analysis
    GENERAL = "general"       # General yield query


@dataclass
class TemporalMatrix:
    """
    Pre-computed temporal analysis data.
    
    Organizes yield data by time periods for efficient trend analysis.
    """
    periods: List[str]                    # Ordered period labels
    yields: Dict[str, float]              # period -> yield
    unit_counts: Dict[str, int]           # period -> unit count
    fp_counts: Dict[str, int]             # period -> first pass count
    
    # Computed metrics
    trend_slope: Optional[float] = None   # Linear trend slope
    volatility: Optional[float] = None    # Standard deviation
    change_points: List[str] = field(default_factory=list)  # Significant changes
    
    def get_period(self, period: str) -> Optional[Dict[str, Any]]:
        """Get data for a specific period."""
        if period not in self.yields:
            return None
        return {
            "period": period,
            "yield": self.yields[period],
            "unit_count": self.unit_counts.get(period, 0),
            "fp_count": self.fp_counts.get(period, 0),
        }
    
    def get_range(self, start: str, end: str) -> List[Dict[str, Any]]:
        """Get data for a period range."""
        result = []
        in_range = False
        for period in self.periods:
            if period == start:
                in_range = True
            if in_range:
                result.append(self.get_period(period))
            if period == end:
                break
        return result


@dataclass  
class DeviationCell:
    """A single cell in the deviation matrix."""
    dimension_values: Dict[str, str]   # e.g., {"station_name": "ST-01"}
    yield_value: float
    unit_count: int
    deviation_from_baseline: float
    significance: str                   # "critical", "high", "moderate", "low", "none"
    confidence: float                   # 0-1 based on sample size
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **self.dimension_values,
            "yield": self.yield_value,
            "unit_count": self.unit_count,
            "deviation": self.deviation_from_baseline,
            "significance": self.significance,
            "confidence": self.confidence,
        }


@dataclass
class DeviationMatrix:
    """
    Pre-computed deviation analysis data.
    
    Organizes yield data by dimensions for efficient failure mode detection.
    """
    dimensions: List[str]               # Dimensions used
    baseline_yield: float               # Overall yield for comparison
    total_units: int                    # Total units in analysis
    
    cells: List[DeviationCell] = field(default_factory=list)
    
    # Pre-ranked findings (sorted by impact)
    critical_cells: List[DeviationCell] = field(default_factory=list)
    high_cells: List[DeviationCell] = field(default_factory=list)
    moderate_cells: List[DeviationCell] = field(default_factory=list)
    
    def get_cell(self, **dimension_values) -> Optional[DeviationCell]:
        """Get a specific cell by dimension values."""
        for cell in self.cells:
            if all(cell.dimension_values.get(k) == v for k, v in dimension_values.items()):
                return cell
        return None
    
    def get_dimension_values(self, dimension: str) -> List[str]:
        """Get all unique values for a dimension."""
        values = set()
        for cell in self.cells:
            if dimension in cell.dimension_values:
                values.add(cell.dimension_values[dimension])
        return sorted(values)


class AnalysisSession:
    """
    Stateful analysis session.
    
    Holds fetched data and pre-computed analysis for efficient follow-ups.
    Sessions auto-expire after TTL to prevent memory bloat.
    """
    
    DEFAULT_TTL_MINUTES = 5
    
    def __init__(
        self,
        session_id: str,
        session_type: SessionType,
        filter_params: Dict[str, Any],
        yield_data: List["YieldData"],
        ttl_minutes: int = DEFAULT_TTL_MINUTES
    ):
        self.session_id = session_id
        self.session_type = session_type
        self.filter_params = filter_params
        self.yield_data = yield_data
        
        self.created_at = datetime.now()
        self.expires_at = self.created_at + timedelta(minutes=ttl_minutes)
        self.last_accessed = self.created_at
        
        # Pre-computed matrices (populated on demand)
        self._temporal_matrix: Optional[TemporalMatrix] = None
        self._deviation_matrix: Optional[DeviationMatrix] = None
        
        # Metadata
        self.total_records = len(yield_data)
        self.dimensions_used = filter_params.get("dimensions", "")
    
    @property
    def is_expired(self) -> bool:
        """Check if session has expired."""
        return datetime.now() > self.expires_at
    
    def touch(self) -> None:
        """Update last accessed time."""
        self.last_accessed = datetime.now()
    
    @property
    def temporal_matrix(self) -> Optional[TemporalMatrix]:
        """Get pre-computed temporal matrix (lazy-loaded)."""
        if self._temporal_matrix is None and self.yield_data:
            self._temporal_matrix = self._build_temporal_matrix()
        return self._temporal_matrix
    
    @property
    def deviation_matrix(self) -> Optional[DeviationMatrix]:
        """Get pre-computed deviation matrix (lazy-loaded)."""
        if self._deviation_matrix is None and self.yield_data:
            self._deviation_matrix = self._build_deviation_matrix()
        return self._deviation_matrix
    
    def _build_temporal_matrix(self) -> TemporalMatrix:
        """Build temporal analysis matrix from yield data."""
        periods = []
        yields = {}
        unit_counts = {}
        fp_counts = {}
        
        for row in self.yield_data:
            period = getattr(row, 'period', None)
            if period:
                if period not in yields:
                    periods.append(period)
                    yields[period] = getattr(row, 'fpy', 0.0) or 0.0
                    unit_counts[period] = getattr(row, 'unit_count', 0) or 0
                    fp_counts[period] = getattr(row, 'fp_count', 0) or 0
        
        # Sort periods (assuming ISO date format)
        periods.sort()
        
        # Compute trend metrics
        trend_slope = None
        volatility = None
        change_points = []
        
        if len(periods) >= 2:
            yield_values = [yields[p] for p in periods]
            
            # Simple linear regression for slope
            n = len(yield_values)
            x_mean = (n - 1) / 2
            y_mean = sum(yield_values) / n
            
            numerator = sum((i - x_mean) * (y - y_mean) for i, y in enumerate(yield_values))
            denominator = sum((i - x_mean) ** 2 for i in range(n))
            
            if denominator > 0:
                trend_slope = numerator / denominator
            
            # Volatility (standard deviation)
            if n > 1:
                variance = sum((y - y_mean) ** 2 for y in yield_values) / (n - 1)
                volatility = variance ** 0.5
            
            # Change point detection (simple: >5% change between periods)
            for i in range(1, len(periods)):
                prev_yield = yields[periods[i-1]]
                curr_yield = yields[periods[i]]
                if prev_yield > 0:
                    change_pct = abs(curr_yield - prev_yield)
                    if change_pct > 5:  # 5% threshold
                        change_points.append(periods[i])
        
        return TemporalMatrix(
            periods=periods,
            yields=yields,
            unit_counts=unit_counts,
            fp_counts=fp_counts,
            trend_slope=trend_slope,
            volatility=volatility,
            change_points=change_points,
        )
    
    def _build_deviation_matrix(self) -> DeviationMatrix:
        """Build deviation analysis matrix from yield data."""
        # Parse dimensions from filter
        dimensions_str = self.filter_params.get("dimensions", "")
        dimensions = [d.strip() for d in dimensions_str.split(";") if d.strip()]
        
        # Map WATS dimension names to attribute names
        dim_attr_map = {
            "stationName": "station_name",
            "partNumber": "part_number",
            "testOperation": "test_operation",
            "productGroup": "product_group",
            "operator": "operator",
            "location": "location",
            "batchNumber": "batch_number",
            "fixtureId": "fixture_id",
            "revision": "revision",
            "level": "level",
            "period": "period",
        }
        
        # Calculate baseline
        total_units = 0
        total_passed = 0
        cells = []
        
        for row in self.yield_data:
            unit_count = getattr(row, 'unit_count', 0) or 0
            fp_count = getattr(row, 'fp_count', 0) or 0
            fpy = getattr(row, 'fpy', None)
            
            total_units += unit_count
            total_passed += fp_count
            
            # Build dimension values for this row
            dim_values = {}
            for dim in dimensions:
                attr_name = dim_attr_map.get(dim, dim)
                value = getattr(row, attr_name, None)
                if value is not None:
                    dim_values[dim] = str(value)
            
            if dim_values and fpy is not None:
                cells.append(DeviationCell(
                    dimension_values=dim_values,
                    yield_value=fpy,
                    unit_count=unit_count,
                    deviation_from_baseline=0.0,  # Calculated below
                    significance="none",
                    confidence=0.0,
                ))
        
        # Calculate baseline yield
        baseline_yield = (total_passed / total_units * 100) if total_units > 0 else 0.0
        
        # Calculate deviations and significance
        critical = []
        high = []
        moderate = []
        
        for cell in cells:
            cell.deviation_from_baseline = cell.yield_value - baseline_yield
            
            # Confidence based on sample size
            if cell.unit_count >= 100:
                cell.confidence = 1.0
            elif cell.unit_count >= 30:
                cell.confidence = 0.8
            elif cell.unit_count >= 10:
                cell.confidence = 0.5
            else:
                cell.confidence = 0.2
            
            # Significance based on deviation magnitude and confidence
            abs_dev = abs(cell.deviation_from_baseline)
            if cell.deviation_from_baseline < 0:  # Only care about underperformance
                if abs_dev >= 10 and cell.confidence >= 0.5:
                    cell.significance = "critical"
                    critical.append(cell)
                elif abs_dev >= 5 and cell.confidence >= 0.5:
                    cell.significance = "high"
                    high.append(cell)
                elif abs_dev >= 2 and cell.confidence >= 0.3:
                    cell.significance = "moderate"
                    moderate.append(cell)
                else:
                    cell.significance = "low"
        
        # Sort by impact (deviation * unit_count)
        critical.sort(key=lambda c: c.deviation_from_baseline * c.unit_count)
        high.sort(key=lambda c: c.deviation_from_baseline * c.unit_count)
        moderate.sort(key=lambda c: c.deviation_from_baseline * c.unit_count)
        
        return DeviationMatrix(
            dimensions=dimensions,
            baseline_yield=baseline_yield,
            total_units=total_units,
            cells=cells,
            critical_cells=critical[:5],
            high_cells=high[:5],
            moderate_cells=moderate[:5],
        )
    
    def get_period_detail(self, period: str) -> Optional[Dict[str, Any]]:
        """Get detailed data for a specific period."""
        self.touch()
        if self.temporal_matrix:
            return self.temporal_matrix.get_period(period)
        return None
    
    def get_dimension_detail(self, **dimension_values) -> Optional[Dict[str, Any]]:
        """Get detailed data for a specific dimension combination."""
        self.touch()
        if self.deviation_matrix:
            cell = self.deviation_matrix.get_cell(**dimension_values)
            if cell:
                return cell.to_dict()
        return None
    
    def compare_periods(self, period1: str, period2: str) -> Dict[str, Any]:
        """Compare two periods from cached data."""
        self.touch()
        p1 = self.get_period_detail(period1)
        p2 = self.get_period_detail(period2)
        
        if not p1 or not p2:
            return {"error": "Period not found"}
        
        return {
            "period1": p1,
            "period2": p2,
            "yield_change": p2["yield"] - p1["yield"],
            "unit_change": p2["unit_count"] - p1["unit_count"],
        }
    
    def to_summary(self) -> Dict[str, Any]:
        """Convert to a token-efficient summary for the agent."""
        return {
            "session_id": self.session_id,
            "session_type": self.session_type.value,
            "total_records": self.total_records,
            "filter_context": {
                k: v for k, v in self.filter_params.items()
                if k in ["part_number", "test_operation", "station_name", "days"]
            },
            "expires_in_minutes": max(0, int((self.expires_at - datetime.now()).seconds / 60)),
        }


class SessionManager:
    """
    Manages analysis sessions with TTL-based cleanup.
    
    Thread-safe singleton for session storage.
    """
    
    _instance: Optional["SessionManager"] = None
    _lock = Lock()
    
    def __init__(self):
        self._sessions: Dict[str, AnalysisSession] = {}
        self._cleanup_lock = Lock()
    
    @classmethod
    def get_instance(cls) -> "SessionManager":
        """Get the singleton session manager."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance
    
    @classmethod
    def reset_instance(cls) -> None:
        """Reset the manager (for testing)."""
        with cls._lock:
            cls._instance = None
    
    def create_session(
        self,
        session_type: SessionType,
        filter_params: Dict[str, Any],
        yield_data: List["YieldData"],
        ttl_minutes: int = AnalysisSession.DEFAULT_TTL_MINUTES
    ) -> AnalysisSession:
        """Create a new analysis session."""
        self._cleanup_expired()
        
        session_id = f"{session_type.value}_{uuid.uuid4().hex[:8]}"
        session = AnalysisSession(
            session_id=session_id,
            session_type=session_type,
            filter_params=filter_params,
            yield_data=yield_data,
            ttl_minutes=ttl_minutes,
        )
        
        self._sessions[session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[AnalysisSession]:
        """Get a session by ID."""
        session = self._sessions.get(session_id)
        if session and not session.is_expired:
            session.touch()
            return session
        return None
    
    def _cleanup_expired(self) -> None:
        """Remove expired sessions."""
        with self._cleanup_lock:
            expired = [
                sid for sid, session in self._sessions.items()
                if session.is_expired
            ]
            for sid in expired:
                del self._sessions[sid]
    
    def get_active_session_count(self) -> int:
        """Get count of active (non-expired) sessions."""
        self._cleanup_expired()
        return len(self._sessions)


# Convenience functions
def get_session_manager() -> SessionManager:
    """Get the shared session manager."""
    return SessionManager.get_instance()


def create_trend_session(
    filter_params: Dict[str, Any],
    yield_data: List["YieldData"]
) -> AnalysisSession:
    """Create a temporal analysis session."""
    return get_session_manager().create_session(
        SessionType.TREND, filter_params, yield_data
    )


def create_deviation_session(
    filter_params: Dict[str, Any],
    yield_data: List["YieldData"]
) -> AnalysisSession:
    """Create a deviation analysis session."""
    return get_session_manager().create_session(
        SessionType.DEVIATION, filter_params, yield_data
    )
