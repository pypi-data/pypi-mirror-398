"""
Statistical Thresholds Configuration.

Configures minimum sample sizes, significance thresholds, and confidence
levels for yield analysis tools. Research-backed defaults with flexibility
for different analysis types.

SAMPLE SIZE CONSIDERATIONS (Research Summary):
- Central Limit Theorem: n≥30 for approximate normality
- Proportion estimates: n≥30 for ±5% margin at 95% CI
- Process capability (Cpk): n≥100 for reliable estimates
- Six Sigma quality: n≥50 recommended minimum

RECOMMENDED DEFAULTS:
- Screening: n≥10 (quick check, lower confidence)
- Analysis: n≥30 (standard statistical validity)
- Reporting: n≥50 (higher confidence for decisions)
- Capability: n≥100 (process improvement decisions)

The system uses a weighted scoring approach to combine:
1. Sample size confidence
2. Deviation magnitude
3. Historical context weight
4. Dimension cardinality penalty

This allows for smart filtering of negligible findings.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum


class AnalysisType(str, Enum):
    """Types of analysis with different statistical requirements."""
    
    SCREENING = "screening"     # Quick check, accept higher uncertainty
    EXPLORATORY = "exploratory" # Finding patterns, moderate thresholds
    DIAGNOSTIC = "diagnostic"   # Root cause, need confidence
    REPORTING = "reporting"     # Executive summary, high confidence
    CAPABILITY = "capability"   # Process capability, highest confidence


class MetricType(str, Enum):
    """Yield metrics with different sensitivity requirements."""
    
    FPY = "fpy"   # First Pass Yield - most sensitive to variations
    LPY = "lpy"   # Last Pass Yield - less sensitive (includes repairs)
    TRY = "try"   # True Yield (rolled throughput) - most stable
    RTY = "rty"   # Rolled Throughput Yield - process chain


@dataclass
class SampleSizeThresholds:
    """
    Sample size thresholds for statistical validity.
    
    These determine the minimum samples needed before findings
    are considered reliable at different confidence levels.
    
    Research basis:
    - absolute_minimum: Below this, findings are speculative
    - low_confidence: CLT approximation starts working (n≥10)
    - medium_confidence: Standard validity threshold (n≥30)
    - high_confidence: Suitable for reporting (n≥50)
    - publication_grade: High precision required (n≥100)
    """
    absolute_minimum: int = 5      # Below this, always flag as insufficient
    low_confidence: int = 10       # 50-60% confidence
    medium_confidence: int = 30    # 70-80% confidence
    high_confidence: int = 50      # 85-90% confidence
    publication_grade: int = 100   # 95%+ confidence
    
    def get_confidence_level(self, n: int) -> Tuple[float, str]:
        """
        Get confidence level and description for a sample size.
        
        Returns:
            Tuple of (confidence 0-1, description)
        """
        if n < self.absolute_minimum:
            return 0.1, "insufficient"
        elif n < self.low_confidence:
            return 0.3, "very_low"
        elif n < self.medium_confidence:
            return 0.6, "low"
        elif n < self.high_confidence:
            return 0.8, "medium"
        elif n < self.publication_grade:
            return 0.9, "high"
        else:
            return 0.95, "very_high"


@dataclass
class DeviationThresholds:
    """
    Thresholds for deviation significance.
    
    These determine when a yield deviation is considered
    actionable vs noise.
    
    Manufacturing context:
    - critical: Immediate action needed (production stop consideration)
    - high: Investigation required within 24-48 hours
    - moderate: Should investigate if pattern persists
    - low: Monitor, no immediate action
    """
    critical: float = 10.0    # >10% below baseline
    high: float = 5.0         # 5-10% below baseline
    moderate: float = 2.0     # 2-5% below baseline
    low: float = 1.0          # 1-2% below baseline
    
    def classify(self, deviation: float) -> str:
        """Classify a deviation magnitude."""
        abs_dev = abs(deviation)
        if abs_dev >= self.critical:
            return "critical"
        elif abs_dev >= self.high:
            return "high"
        elif abs_dev >= self.moderate:
            return "moderate"
        elif abs_dev >= self.low:
            return "low"
        else:
            return "none"


@dataclass
class DimensionCardinalityLimits:
    """
    Limits for dimension cardinality.
    
    High-cardinality dimensions dilute sample sizes.
    When dimension has 100 unique values and 1000 samples,
    average cell has only 10 samples - often insufficient.
    
    These limits help warn about sparsity.
    """
    warn_threshold: int = 20          # Warn if dimension has >20 values
    max_recommended: int = 50         # Above this, suggest filtering
    sparsity_threshold: float = 10.0  # Min samples per cell on average
    
    def check_sparsity(
        self, 
        total_samples: int, 
        cardinality: int,
        extra_dimensions: int = 0
    ) -> Tuple[bool, float, str]:
        """
        Check if dimension combination will be sparse.
        
        Args:
            total_samples: Total samples in dataset
            cardinality: Number of unique values in dimension(s)
            extra_dimensions: Additional dimensions being cross-tabulated
            
        Returns:
            Tuple of (is_acceptable, samples_per_cell, warning)
        """
        # Account for combinatorial explosion with extra dimensions
        effective_cardinality = cardinality * (2 ** extra_dimensions)
        samples_per_cell = total_samples / max(1, effective_cardinality)
        
        if samples_per_cell < self.sparsity_threshold:
            return (
                False,
                samples_per_cell,
                f"Sparse data: ~{samples_per_cell:.1f} samples per cell "
                f"(need ≥{self.sparsity_threshold}). Consider filtering or fewer dimensions."
            )
        
        if cardinality > self.max_recommended:
            return (
                True,
                samples_per_cell,
                f"High cardinality ({cardinality} values). Results may be noisy."
            )
        
        if cardinality > self.warn_threshold:
            return (
                True,
                samples_per_cell,
                f"Moderate cardinality ({cardinality} values)."
            )
        
        return True, samples_per_cell, ""


@dataclass
class StatisticalConfig:
    """
    Master statistical configuration for yield analysis.
    
    Combines all threshold configurations with smart defaults
    based on analysis type.
    """
    sample_size: SampleSizeThresholds = field(default_factory=SampleSizeThresholds)
    deviation: DeviationThresholds = field(default_factory=DeviationThresholds)
    cardinality: DimensionCardinalityLimits = field(default_factory=DimensionCardinalityLimits)
    
    # Analysis-specific overrides
    analysis_type: AnalysisType = AnalysisType.EXPLORATORY
    metric_type: MetricType = MetricType.FPY
    
    # Weighting for combined scoring
    sample_weight: float = 0.4      # Importance of sample size
    deviation_weight: float = 0.4   # Importance of deviation magnitude
    confidence_weight: float = 0.2  # Importance of historical confidence
    
    # Filtering thresholds
    min_combined_score: float = 0.3  # Below this, finding is filtered out
    
    @classmethod
    def for_analysis_type(cls, analysis_type: AnalysisType) -> "StatisticalConfig":
        """
        Create a config optimized for a specific analysis type.
        
        Args:
            analysis_type: Type of analysis being performed
            
        Returns:
            Configured StatisticalConfig
        """
        config = cls(analysis_type=analysis_type)
        
        if analysis_type == AnalysisType.SCREENING:
            # Relaxed thresholds for quick checks
            config.sample_size = SampleSizeThresholds(
                absolute_minimum=3,
                low_confidence=5,
                medium_confidence=15,
                high_confidence=30,
                publication_grade=50
            )
            config.min_combined_score = 0.2
            
        elif analysis_type == AnalysisType.DIAGNOSTIC:
            # Stricter for root cause
            config.sample_size = SampleSizeThresholds(
                absolute_minimum=10,
                low_confidence=20,
                medium_confidence=40,
                high_confidence=70,
                publication_grade=100
            )
            config.deviation = DeviationThresholds(
                critical=8.0,
                high=4.0,
                moderate=2.0,
                low=1.0
            )
            config.min_combined_score = 0.4
            
        elif analysis_type == AnalysisType.REPORTING:
            # Highest confidence for executives
            config.sample_size = SampleSizeThresholds(
                absolute_minimum=20,
                low_confidence=30,
                medium_confidence=50,
                high_confidence=100,
                publication_grade=200
            )
            config.min_combined_score = 0.5
            
        elif analysis_type == AnalysisType.CAPABILITY:
            # Process capability studies
            config.sample_size = SampleSizeThresholds(
                absolute_minimum=30,
                low_confidence=50,
                medium_confidence=100,
                high_confidence=150,
                publication_grade=300
            )
            config.min_combined_score = 0.6
            
        return config
    
    def calculate_finding_score(
        self,
        sample_size: int,
        deviation: float,
        historical_confidence: float = 1.0
    ) -> Tuple[float, bool, Dict[str, Any]]:
        """
        Calculate a combined score for a finding.
        
        Uses weighted combination of factors to determine
        if a finding should be reported.
        
        Args:
            sample_size: Number of samples for this finding
            deviation: Magnitude of yield deviation
            historical_confidence: Optional confidence from prior analysis
            
        Returns:
            Tuple of (score 0-1, should_report, breakdown)
        """
        # Sample size component (0-1)
        sample_conf, sample_desc = self.sample_size.get_confidence_level(sample_size)
        
        # Deviation component (0-1 based on thresholds)
        abs_dev = abs(deviation)
        if abs_dev >= self.deviation.critical:
            dev_score = 1.0
        elif abs_dev >= self.deviation.high:
            dev_score = 0.8
        elif abs_dev >= self.deviation.moderate:
            dev_score = 0.5
        elif abs_dev >= self.deviation.low:
            dev_score = 0.3
        else:
            dev_score = 0.1
        
        # Combined score
        combined = (
            self.sample_weight * sample_conf +
            self.deviation_weight * dev_score +
            self.confidence_weight * historical_confidence
        )
        
        should_report = combined >= self.min_combined_score
        
        breakdown = {
            "sample_size": sample_size,
            "sample_confidence": sample_conf,
            "sample_description": sample_desc,
            "deviation": deviation,
            "deviation_score": dev_score,
            "deviation_class": self.deviation.classify(deviation),
            "historical_confidence": historical_confidence,
            "combined_score": round(combined, 3),
            "threshold": self.min_combined_score,
            "should_report": should_report,
        }
        
        return combined, should_report, breakdown


# Singleton instance with defaults
_default_config: Optional[StatisticalConfig] = None


def get_statistical_config() -> StatisticalConfig:
    """Get the default statistical configuration."""
    global _default_config
    if _default_config is None:
        _default_config = StatisticalConfig()
    return _default_config


def set_statistical_config(config: StatisticalConfig) -> None:
    """Set the default statistical configuration."""
    global _default_config
    _default_config = config


def reset_statistical_config() -> None:
    """Reset to default configuration."""
    global _default_config
    _default_config = None


# =============================================================================
# DIMENSION DISCOVERY
# =============================================================================

@dataclass
class DimensionInfo:
    """Information about a dimension in a dataset."""
    name: str                          # Internal name
    display_name: str                  # Human-readable name
    wats_field: str                    # WATS API field name
    cardinality: int                   # Number of unique values
    sample_counts: Dict[str, int]      # Value -> count mapping
    total_samples: int                 # Total samples for this dimension
    coverage: float                    # % of total data this dimension covers
    sparsity_warning: Optional[str]    # Warning if sparse
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "wats_field": self.wats_field,
            "cardinality": self.cardinality,
            "total_samples": self.total_samples,
            "coverage": round(self.coverage * 100, 1),
            "top_values": dict(sorted(
                self.sample_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]),
            "sparsity_warning": self.sparsity_warning,
        }


@dataclass
class DimensionCombinationStats:
    """Statistics for a dimension combination."""
    dimensions: List[str]                      # Dimension names
    total_cells: int                           # Number of unique combinations
    populated_cells: int                       # Cells with data
    min_samples: int                           # Minimum samples in any cell
    max_samples: int                           # Maximum samples in any cell
    avg_samples: float                         # Average samples per cell
    median_samples: float                      # Median samples per cell
    cells_below_threshold: int                 # Cells below min sample size
    coverage: float                            # % of total data covered
    is_viable: bool                            # Whether analysis is statistically sound
    warning: Optional[str]                     # Any warnings
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "dimensions": self.dimensions,
            "total_cells": self.total_cells,
            "populated_cells": self.populated_cells,
            "min_samples": self.min_samples,
            "max_samples": self.max_samples,
            "avg_samples": round(self.avg_samples, 1),
            "median_samples": round(self.median_samples, 1),
            "cells_below_threshold": self.cells_below_threshold,
            "coverage_pct": round(self.coverage * 100, 1),
            "is_viable": self.is_viable,
            "warning": self.warning,
        }


class DimensionDiscovery:
    """
    Discovers available dimensions and their statistics in a dataset.
    
    Used to:
    - List which dimensions are present in the data
    - Check cardinality of each dimension
    - Validate dimension combinations before analysis
    - Warn about sparse combinations
    """
    
    # All supported WATS dimensions with metadata
    SUPPORTED_DIMENSIONS = {
        "partNumber": ("part_number", "Part Number"),
        "productName": ("product_name", "Product Name"),
        "stationName": ("station_name", "Station"),
        "location": ("location", "Location/Line"),
        "purpose": ("purpose", "Purpose"),
        "revision": ("revision", "Revision"),
        "testOperation": ("test_operation", "Test Operation"),
        "processCode": ("process_code", "Process Code"),
        "swFilename": ("sw_filename", "Software File"),
        "swVersion": ("sw_version", "Software Version"),
        "productGroup": ("product_group", "Product Group"),
        "level": ("level", "Level"),
        "batchNumber": ("batch_number", "Batch Number"),
        "operator": ("operator", "Operator"),
        "fixtureId": ("fixture_id", "Fixture ID"),
        "period": ("period", "Time Period"),
    }
    
    def __init__(self, config: Optional[StatisticalConfig] = None):
        """Initialize with optional statistical config."""
        self.config = config or get_statistical_config()
    
    def analyze_dimension(
        self,
        yield_data: List[Any],
        dimension: str
    ) -> Optional[DimensionInfo]:
        """
        Analyze a single dimension in the yield data.
        
        Args:
            yield_data: List of YieldData objects
            dimension: WATS dimension name to analyze
            
        Returns:
            DimensionInfo or None if dimension not present
        """
        if dimension not in self.SUPPORTED_DIMENSIONS:
            return None
        
        snake_name, display_name = self.SUPPORTED_DIMENSIONS[dimension]
        
        # Extract values from data
        sample_counts: Dict[str, int] = {}
        total_samples = 0
        
        for item in yield_data:
            # Try snake_case first, then camelCase
            value = getattr(item, snake_name, None)
            if value is None:
                value = getattr(item, dimension, None)
            if value is None:
                continue
                
            # Get unit count
            unit_count = getattr(item, "unit_count", None)
            if unit_count is None:
                unit_count = getattr(item, "unitCount", 1)
            
            value_str = str(value) if value is not None else "(null)"
            sample_counts[value_str] = sample_counts.get(value_str, 0) + unit_count
            total_samples += unit_count
        
        if not sample_counts:
            return None
        
        cardinality = len(sample_counts)
        
        # Check sparsity
        is_ok, samples_per_cell, warning = self.config.cardinality.check_sparsity(
            total_samples, cardinality
        )
        
        return DimensionInfo(
            name=snake_name,
            display_name=display_name,
            wats_field=dimension,
            cardinality=cardinality,
            sample_counts=sample_counts,
            total_samples=total_samples,
            coverage=1.0 if yield_data else 0.0,
            sparsity_warning=warning if warning else None,
        )
    
    def discover_all_dimensions(
        self,
        yield_data: List[Any]
    ) -> Dict[str, DimensionInfo]:
        """
        Discover all available dimensions in the dataset.
        
        Args:
            yield_data: List of YieldData objects
            
        Returns:
            Dictionary of dimension name -> DimensionInfo
        """
        discovered = {}
        
        for wats_dim in self.SUPPORTED_DIMENSIONS:
            info = self.analyze_dimension(yield_data, wats_dim)
            if info and info.cardinality > 0:
                discovered[info.name] = info
        
        return discovered
    
    def analyze_dimension_combination(
        self,
        yield_data: List[Any],
        dimensions: List[str],
        min_sample_size: Optional[int] = None
    ) -> DimensionCombinationStats:
        """
        Analyze a combination of dimensions.
        
        Args:
            yield_data: List of YieldData objects
            dimensions: List of dimension names
            min_sample_size: Override for minimum sample threshold
            
        Returns:
            Statistics about the dimension combination
        """
        min_samples = min_sample_size or self.config.sample_size.low_confidence
        
        # Build composite keys and counts
        cell_counts: Dict[str, int] = {}
        total_samples = 0
        
        for item in yield_data:
            key_parts = []
            for dim in dimensions:
                # Get the snake_case attribute name
                snake_name = None
                for wats_dim, (snake, _) in self.SUPPORTED_DIMENSIONS.items():
                    if snake == dim or wats_dim == dim:
                        snake_name = snake
                        break
                
                if snake_name:
                    value = getattr(item, snake_name, None)
                    if value is None:
                        value = getattr(item, dim, None)
                else:
                    value = getattr(item, dim, None)
                    
                key_parts.append(str(value) if value is not None else "(null)")
            
            key = "|".join(key_parts)
            
            unit_count = getattr(item, "unit_count", None)
            if unit_count is None:
                unit_count = getattr(item, "unitCount", 1)
            
            cell_counts[key] = cell_counts.get(key, 0) + unit_count
            total_samples += unit_count
        
        if not cell_counts:
            return DimensionCombinationStats(
                dimensions=dimensions,
                total_cells=0,
                populated_cells=0,
                min_samples=0,
                max_samples=0,
                avg_samples=0.0,
                median_samples=0.0,
                cells_below_threshold=0,
                coverage=0.0,
                is_viable=False,
                warning="No data found for dimension combination",
            )
        
        counts = list(cell_counts.values())
        sorted_counts = sorted(counts)
        
        populated = len(counts)
        min_count = min(counts)
        max_count = max(counts)
        avg_count = sum(counts) / len(counts)
        median_idx = len(sorted_counts) // 2
        median_count = sorted_counts[median_idx]
        
        cells_below = sum(1 for c in counts if c < min_samples)
        
        # Determine viability
        is_viable = True
        warning = None
        
        if cells_below > populated * 0.5:
            is_viable = False
            warning = f"{cells_below}/{populated} cells below minimum ({min_samples}). Too sparse for reliable analysis."
        elif cells_below > populated * 0.3:
            warning = f"{cells_below}/{populated} cells below minimum. Results may be unreliable."
        elif avg_count < min_samples:
            warning = f"Average cell size ({avg_count:.1f}) below threshold ({min_samples})."
        
        return DimensionCombinationStats(
            dimensions=dimensions,
            total_cells=populated,  # Only count populated cells
            populated_cells=populated,
            min_samples=min_count,
            max_samples=max_count,
            avg_samples=avg_count,
            median_samples=float(median_count),
            cells_below_threshold=cells_below,
            coverage=1.0,
            is_viable=is_viable,
            warning=warning,
        )
    
    def suggest_viable_combinations(
        self,
        yield_data: List[Any],
        max_dimensions: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Suggest viable dimension combinations for analysis.
        
        Args:
            yield_data: List of YieldData objects
            max_dimensions: Maximum dimensions to combine
            
        Returns:
            List of viable combinations with statistics
        """
        from itertools import combinations
        
        # First discover all dimensions
        available = self.discover_all_dimensions(yield_data)
        
        if not available:
            return []
        
        # Get dimension names that are viable alone
        viable_single = [
            name for name, info in available.items()
            if info.cardinality > 1 and info.sparsity_warning is None
        ]
        
        suggestions = []
        
        # Single dimensions
        for dim in viable_single:
            stats = self.analyze_dimension_combination(yield_data, [dim])
            if stats.is_viable:
                suggestions.append({
                    "dimensions": [dim],
                    "stats": stats.to_dict(),
                    "recommendation": "good"
                })
        
        # Two-dimension combinations
        if max_dimensions >= 2:
            for combo in combinations(viable_single, 2):
                stats = self.analyze_dimension_combination(yield_data, list(combo))
                if stats.is_viable:
                    suggestions.append({
                        "dimensions": list(combo),
                        "stats": stats.to_dict(),
                        "recommendation": "good" if not stats.warning else "caution"
                    })
        
        # Three-dimension combinations
        if max_dimensions >= 3 and len(viable_single) >= 3:
            for combo in combinations(viable_single, 3):
                stats = self.analyze_dimension_combination(yield_data, list(combo))
                if stats.is_viable:
                    suggestions.append({
                        "dimensions": list(combo),
                        "stats": stats.to_dict(),
                        "recommendation": "caution"  # 3D always needs caution
                    })
        
        # Sort by avg samples (higher is better)
        suggestions.sort(key=lambda x: x["stats"]["avg_samples"], reverse=True)
        
        return suggestions


# Export utility function
def discover_dimensions(yield_data: List[Any]) -> Dict[str, DimensionInfo]:
    """
    Convenience function to discover all dimensions in yield data.
    
    Args:
        yield_data: List of YieldData objects
        
    Returns:
        Dictionary of dimension name -> DimensionInfo
    """
    discovery = DimensionDiscovery()
    return discovery.discover_all_dimensions(yield_data)
