"""
Adaptive time filter for handling varying production volumes.

PROBLEM:
- Default 30-day window can be too large for high-volume customers
- Million+ units per week would overwhelm queries
- Few customers realize this can be changed

SOLUTION:
- Start with a small time window
- Check volume (unit/report counts)
- Expand if necessary to get meaningful data
- All thresholds are configurable

Example:
    >>> from pywats_agent.tools.adaptive_time import AdaptiveTimeFilter
    >>> 
    >>> adaptive = AdaptiveTimeFilter(api)
    >>> optimal_filter = adaptive.get_optimal_filter(
    ...     part_number="WIDGET-001",
    ...     test_operation="FCT"
    ... )
    >>> print(f"Using {optimal_filter['days']} days")
"""

from typing import Any, Dict, List, Optional, TYPE_CHECKING
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

if TYPE_CHECKING:
    from pywats import pyWATS


class VolumeCategory(str, Enum):
    """Production volume categories."""
    VERY_HIGH = "very_high"     # >100k units/day
    HIGH = "high"               # 10k-100k units/day
    MEDIUM = "medium"           # 1k-10k units/day
    LOW = "low"                 # 100-1k units/day
    VERY_LOW = "very_low"       # <100 units/day
    UNKNOWN = "unknown"


@dataclass
class AdaptiveTimeConfig:
    """
    Configuration for adaptive time filtering.
    
    All thresholds can be customized per customer/deployment.
    """
    
    # Initial time window to try (in days)
    initial_days: int = 1
    
    # Maximum time window (in days)
    max_days: int = 90
    
    # Expansion factor when current window is too small
    expansion_factor: float = 3.0
    
    # Minimum records needed for meaningful analysis
    min_records: int = 10
    
    # Target records for good analysis (will expand until this is met)
    target_records: int = 100
    
    # Maximum records to fetch (performance limit)
    max_records: int = 10000
    
    # Volume thresholds (units per day)
    volume_thresholds: Dict[VolumeCategory, int] = field(default_factory=lambda: {
        VolumeCategory.VERY_HIGH: 100000,
        VolumeCategory.HIGH: 10000,
        VolumeCategory.MEDIUM: 1000,
        VolumeCategory.LOW: 100,
        VolumeCategory.VERY_LOW: 0,
    })
    
    # Recommended days by volume category
    recommended_days: Dict[VolumeCategory, int] = field(default_factory=lambda: {
        VolumeCategory.VERY_HIGH: 1,      # High volume: 1 day is plenty
        VolumeCategory.HIGH: 3,           # High: 3 days
        VolumeCategory.MEDIUM: 7,         # Medium: 1 week
        VolumeCategory.LOW: 30,           # Low: 1 month
        VolumeCategory.VERY_LOW: 90,      # Very low: 3 months
        VolumeCategory.UNKNOWN: 7,        # Unknown: start with 1 week
    })


@dataclass
class AdaptiveTimeResult:
    """Result from adaptive time filter calculation."""
    
    # Recommended time window
    days: int
    date_from: datetime
    date_to: datetime
    
    # Volume information
    estimated_units: int
    estimated_daily_volume: float
    volume_category: VolumeCategory
    
    # How we arrived at this recommendation
    iterations: int
    initial_days: int
    
    # Additional context
    message: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API use."""
        return {
            "days": self.days,
            "date_from": self.date_from,
            "date_to": self.date_to,
            "estimated_units": self.estimated_units,
            "estimated_daily_volume": self.estimated_daily_volume,
            "volume_category": self.volume_category.value,
            "message": self.message,
        }


class AdaptiveTimeFilter:
    """
    Dynamically determines optimal time window based on production volume.
    
    PROBLEM ADDRESSED:
    - Default 30 days is too large for high-volume customers
    - Some customers have millions of units per week
    - Queries become slow and overwhelming
    
    SOLUTION:
    - Start with small window (configurable, default 1 day)
    - Check volume
    - Expand if needed to get meaningful data
    - Never exceed max_days or max_records
    
    Example:
        >>> adaptive = AdaptiveTimeFilter(api)
        >>> 
        >>> # Get optimal filter for a product
        >>> result = adaptive.calculate_optimal_window(
        ...     part_number="WIDGET-001",
        ...     test_operation="FCT"
        ... )
        >>> 
        >>> print(f"Recommended: {result.days} days")
        >>> print(f"Volume: {result.volume_category.value}")
        >>> print(f"~{result.estimated_daily_volume:.0f} units/day")
    """
    
    def __init__(
        self, 
        api: "pyWATS", 
        config: Optional[AdaptiveTimeConfig] = None
    ):
        """
        Initialize adaptive time filter.
        
        Args:
            api: Configured pyWATS instance
            config: Optional custom configuration
        """
        self._api = api
        self._config = config or AdaptiveTimeConfig()
        
        # Cache for volume estimates
        self._volume_cache: Dict[str, tuple] = {}  # key -> (volume, timestamp)
        self._cache_ttl = 300  # 5 minutes
    
    def calculate_optimal_window(
        self,
        part_number: Optional[str] = None,
        test_operation: Optional[str] = None,
        station_name: Optional[str] = None,
        product_group: Optional[str] = None,
    ) -> AdaptiveTimeResult:
        """
        Calculate the optimal time window for a query.
        
        Starts small and expands until we have enough data or hit limits.
        
        Args:
            part_number: Optional product filter
            test_operation: Optional process filter
            station_name: Optional station filter
            product_group: Optional product group filter
            
        Returns:
            AdaptiveTimeResult with recommended time window
        """
        import time
        
        # Generate cache key
        cache_key = f"{part_number}|{test_operation}|{station_name}|{product_group}"
        
        # Check cache
        if cache_key in self._volume_cache:
            cached_volume, cached_time = self._volume_cache[cache_key]
            if time.time() - cached_time < self._cache_ttl:
                return self._build_result_from_volume(cached_volume)
        
        # Start with initial window
        current_days = self._config.initial_days
        iterations = 0
        date_to = datetime.now()
        
        while current_days <= self._config.max_days and iterations < 5:
            iterations += 1
            
            # Calculate date range
            date_from = date_to - timedelta(days=current_days)
            
            # Get count for this window
            count = self._get_volume_count(
                date_from=date_from,
                date_to=date_to,
                part_number=part_number,
                test_operation=test_operation,
                station_name=station_name,
                product_group=product_group,
            )
            
            # Calculate daily rate
            daily_volume = count / current_days if current_days > 0 else 0
            
            # If we have enough data, we're done
            if count >= self._config.target_records:
                volume_category = self._categorize_volume(daily_volume)
                
                # Cache the result
                self._volume_cache[cache_key] = (daily_volume, time.time())
                
                return AdaptiveTimeResult(
                    days=current_days,
                    date_from=date_from,
                    date_to=date_to,
                    estimated_units=count,
                    estimated_daily_volume=daily_volume,
                    volume_category=volume_category,
                    iterations=iterations,
                    initial_days=self._config.initial_days,
                    message=f"Found {count} records in {current_days} days (~{daily_volume:.0f}/day). Volume: {volume_category.value}.",
                )
            
            # If we have some data but not enough, check if expanding would exceed limits
            if count > 0:
                # Estimate what we'd get with more days
                estimated_total = daily_volume * self._config.max_days
                if estimated_total > self._config.max_records:
                    # We'd get too much data - stop here and recommend limiting
                    volume_category = self._categorize_volume(daily_volume)
                    self._volume_cache[cache_key] = (daily_volume, time.time())
                    
                    # Find optimal days to stay under max_records
                    optimal_days = int(self._config.max_records / daily_volume) if daily_volume > 0 else current_days
                    optimal_days = max(current_days, min(optimal_days, self._config.max_days))
                    
                    return AdaptiveTimeResult(
                        days=optimal_days,
                        date_from=date_to - timedelta(days=optimal_days),
                        date_to=date_to,
                        estimated_units=int(daily_volume * optimal_days),
                        estimated_daily_volume=daily_volume,
                        volume_category=volume_category,
                        iterations=iterations,
                        initial_days=self._config.initial_days,
                        message=f"High volume detected (~{daily_volume:.0f}/day). Using {optimal_days} days to stay performant.",
                    )
            
            # Expand window
            current_days = min(
                int(current_days * self._config.expansion_factor),
                self._config.max_days
            )
        
        # We've exhausted expansions - return what we have
        date_from = date_to - timedelta(days=current_days)
        count = self._get_volume_count(
            date_from=date_from,
            date_to=date_to,
            part_number=part_number,
            test_operation=test_operation,
            station_name=station_name,
            product_group=product_group,
        )
        daily_volume = count / current_days if current_days > 0 else 0
        volume_category = self._categorize_volume(daily_volume)
        
        self._volume_cache[cache_key] = (daily_volume, time.time())
        
        message = f"Using {current_days} days ({count} records, ~{daily_volume:.0f}/day)."
        if count < self._config.min_records:
            message += " Limited data available."
        
        return AdaptiveTimeResult(
            days=current_days,
            date_from=date_from,
            date_to=date_to,
            estimated_units=count,
            estimated_daily_volume=daily_volume,
            volume_category=volume_category,
            iterations=iterations,
            initial_days=self._config.initial_days,
            message=message,
        )
    
    def _get_volume_count(
        self,
        date_from: datetime,
        date_to: datetime,
        part_number: Optional[str] = None,
        test_operation: Optional[str] = None,
        station_name: Optional[str] = None,
        product_group: Optional[str] = None,
    ) -> int:
        """
        Get unit count for a time window.
        
        Uses a lightweight query to just get counts.
        """
        from pywats.domains.report.models import WATSFilter
        
        filter_params: Dict[str, Any] = {
            "date_from": date_from,
            "date_to": date_to,
        }
        
        if part_number:
            filter_params["part_number"] = part_number
        if test_operation:
            filter_params["test_operation"] = test_operation
        if station_name:
            filter_params["station_name"] = station_name
        if product_group:
            filter_params["product_group"] = product_group
        
        try:
            wats_filter = WATSFilter(**filter_params)
            # Use get_dynamic_yield without dimensions to get aggregate count
            data = self._api.analytics.get_dynamic_yield(wats_filter)
            
            if data:
                # Sum up unit counts
                total_units = sum(
                    getattr(d, 'unit_count', 0) or 0
                    for d in data
                )
                return total_units
            
            return 0
            
        except Exception:
            return 0
    
    def _categorize_volume(self, daily_volume: float) -> VolumeCategory:
        """Categorize daily volume."""
        thresholds = self._config.volume_thresholds
        
        if daily_volume >= thresholds[VolumeCategory.VERY_HIGH]:
            return VolumeCategory.VERY_HIGH
        elif daily_volume >= thresholds[VolumeCategory.HIGH]:
            return VolumeCategory.HIGH
        elif daily_volume >= thresholds[VolumeCategory.MEDIUM]:
            return VolumeCategory.MEDIUM
        elif daily_volume >= thresholds[VolumeCategory.LOW]:
            return VolumeCategory.LOW
        elif daily_volume > 0:
            return VolumeCategory.VERY_LOW
        else:
            return VolumeCategory.UNKNOWN
    
    def _build_result_from_volume(self, daily_volume: float) -> AdaptiveTimeResult:
        """Build result from cached daily volume."""
        volume_category = self._categorize_volume(daily_volume)
        recommended_days = self._config.recommended_days[volume_category]
        
        date_to = datetime.now()
        date_from = date_to - timedelta(days=recommended_days)
        
        return AdaptiveTimeResult(
            days=recommended_days,
            date_from=date_from,
            date_to=date_to,
            estimated_units=int(daily_volume * recommended_days),
            estimated_daily_volume=daily_volume,
            volume_category=volume_category,
            iterations=0,  # From cache
            initial_days=self._config.initial_days,
            message=f"Based on volume ({daily_volume:.0f}/day), using {recommended_days} days.",
        )
    
    def get_volume_estimate(
        self,
        part_number: Optional[str] = None,
        test_operation: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get a quick volume estimate for agent context.
        
        Returns:
            Dict with daily_volume, category, and recommended_days
        """
        result = self.calculate_optimal_window(
            part_number=part_number,
            test_operation=test_operation,
        )
        
        return {
            "daily_volume": result.estimated_daily_volume,
            "volume_category": result.volume_category.value,
            "recommended_days": result.days,
            "message": result.message,
        }


# Export for use in other modules
__all__ = [
    "AdaptiveTimeFilter",
    "AdaptiveTimeConfig",
    "AdaptiveTimeResult",
    "VolumeCategory",
]
