"""
Computation helpers for yield analysis.

Provides statistical calculations and insight generation:
- Trend detection (direction, rate, volatility)
- Change point detection
- Deviation significance scoring
- Natural language insight generation
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
import math


class TrendDirection(str, Enum):
    """Direction of yield trend."""
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    VOLATILE = "volatile"
    INSUFFICIENT_DATA = "insufficient_data"


class Volatility(str, Enum):
    """Volatility level."""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class SignificanceLevel(str, Enum):
    """Significance of a deviation."""
    CRITICAL = "critical"    # >10% deviation, high confidence
    HIGH = "high"            # 5-10% deviation
    MODERATE = "moderate"    # 2-5% deviation
    LOW = "low"              # <2% deviation
    NONE = "none"            # No significant deviation


@dataclass
class TrendAnalysis:
    """Results of trend analysis."""
    direction: TrendDirection
    slope_per_period: float              # Change per period (e.g., per day)
    rate_description: str                # e.g., "-2.3% per week"
    current_value: float
    start_value: float
    periods_analyzed: int
    volatility: Volatility
    volatility_value: float              # Standard deviation
    change_points: List[str]             # Periods with significant changes
    confidence: float                    # 0-1 based on data quality
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "direction": self.direction.value,
            "slope_per_period": round(self.slope_per_period, 3),
            "rate_description": self.rate_description,
            "current_value": round(self.current_value, 2),
            "start_value": round(self.start_value, 2),
            "periods_analyzed": self.periods_analyzed,
            "volatility": self.volatility.value,
            "volatility_value": round(self.volatility_value, 2),
            "change_points": self.change_points,
            "confidence": round(self.confidence, 2),
        }


@dataclass
class DeviationAnalysis:
    """Results of deviation analysis for a single dimension value."""
    dimension: str
    value: str
    yield_value: float
    baseline_yield: float
    deviation: float
    significance: SignificanceLevel
    confidence: float
    unit_count: int
    impact_score: float                  # deviation * unit_count
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "dimension": self.dimension,
            "value": self.value,
            "yield": round(self.yield_value, 2),
            "baseline": round(self.baseline_yield, 2),
            "deviation": round(self.deviation, 2),
            "significance": self.significance.value,
            "confidence": round(self.confidence, 2),
            "unit_count": self.unit_count,
            "impact_score": round(self.impact_score, 1),
        }


def calculate_trend(
    values: List[float],
    periods: Optional[List[str]] = None,
    period_type: str = "day"
) -> TrendAnalysis:
    """
    Analyze trend from a sequence of values.
    
    Args:
        values: Yield values in chronological order
        periods: Optional period labels (for change point reporting)
        period_type: Type of period (day, week, month) for rate description
        
    Returns:
        TrendAnalysis with direction, rate, volatility, etc.
    """
    n = len(values)
    
    # Handle insufficient data
    if n < 2:
        return TrendAnalysis(
            direction=TrendDirection.INSUFFICIENT_DATA,
            slope_per_period=0.0,
            rate_description="Insufficient data",
            current_value=values[0] if values else 0.0,
            start_value=values[0] if values else 0.0,
            periods_analyzed=n,
            volatility=Volatility.LOW,
            volatility_value=0.0,
            change_points=[],
            confidence=0.0,
        )
    
    # Calculate linear regression
    x_mean = (n - 1) / 2
    y_mean = sum(values) / n
    
    numerator = sum((i - x_mean) * (y - y_mean) for i, y in enumerate(values))
    denominator = sum((i - x_mean) ** 2 for i in range(n))
    
    slope = numerator / denominator if denominator > 0 else 0.0
    
    # Calculate variance and standard deviation
    variance = sum((y - y_mean) ** 2 for y in values) / (n - 1) if n > 1 else 0.0
    std_dev = math.sqrt(variance)
    
    # Determine volatility
    if std_dev > 5:
        volatility = Volatility.HIGH
    elif std_dev > 2:
        volatility = Volatility.MODERATE
    else:
        volatility = Volatility.LOW
    
    # Detect change points (>5% change between consecutive periods)
    change_points = []
    if periods:
        for i in range(1, n):
            if values[i-1] > 0:
                change_pct = abs(values[i] - values[i-1])
                if change_pct > 5:
                    change_points.append(periods[i])
    
    # Determine direction
    # Consider both slope magnitude and volatility
    slope_threshold = 0.5  # Half a percentage point per period
    
    if volatility == Volatility.HIGH and abs(slope) < 2:
        direction = TrendDirection.VOLATILE
    elif slope > slope_threshold:
        direction = TrendDirection.IMPROVING
    elif slope < -slope_threshold:
        direction = TrendDirection.DECLINING
    else:
        direction = TrendDirection.STABLE
    
    # Build rate description
    period_multipliers = {"day": 1, "week": 7, "month": 30}
    multiplier = period_multipliers.get(period_type, 1)
    
    rate_per_week = slope * 7 / multiplier
    if abs(rate_per_week) < 0.1:
        rate_description = "stable"
    else:
        sign = "+" if rate_per_week > 0 else ""
        rate_description = f"{sign}{rate_per_week:.1f}% per week"
    
    # Calculate confidence based on data points and R-squared
    # More points = higher confidence
    confidence = min(1.0, n / 14)  # Max confidence at 2 weeks of daily data
    
    # Adjust confidence down for high volatility (noisy data)
    if volatility == Volatility.HIGH:
        confidence *= 0.7
    elif volatility == Volatility.MODERATE:
        confidence *= 0.85
    
    return TrendAnalysis(
        direction=direction,
        slope_per_period=slope,
        rate_description=rate_description,
        current_value=values[-1],
        start_value=values[0],
        periods_analyzed=n,
        volatility=volatility,
        volatility_value=std_dev,
        change_points=change_points,
        confidence=confidence,
    )


def calculate_deviation_significance(
    value: float,
    baseline: float,
    sample_size: int,
    min_sample: int = 10
) -> Tuple[float, SignificanceLevel, float]:
    """
    Calculate deviation significance.
    
    Args:
        value: The observed yield value
        baseline: The baseline yield to compare against
        sample_size: Number of units in this segment
        min_sample: Minimum sample size for any significance
        
    Returns:
        Tuple of (deviation, significance, confidence)
    """
    deviation = value - baseline
    
    # Confidence based on sample size
    if sample_size >= 100:
        confidence = 1.0
    elif sample_size >= 50:
        confidence = 0.9
    elif sample_size >= 30:
        confidence = 0.8
    elif sample_size >= min_sample:
        confidence = 0.5
    else:
        confidence = 0.2
    
    # Significance based on deviation magnitude and direction
    abs_dev = abs(deviation)
    
    # Only underperformance is significant (negative deviation)
    if deviation >= 0:
        significance = SignificanceLevel.NONE
    elif abs_dev >= 10 and confidence >= 0.5:
        significance = SignificanceLevel.CRITICAL
    elif abs_dev >= 5 and confidence >= 0.5:
        significance = SignificanceLevel.HIGH
    elif abs_dev >= 2 and confidence >= 0.3:
        significance = SignificanceLevel.MODERATE
    elif abs_dev >= 1:
        significance = SignificanceLevel.LOW
    else:
        significance = SignificanceLevel.NONE
    
    return deviation, significance, confidence


def rank_deviations(
    deviations: List[DeviationAnalysis],
    top_n: int = 5
) -> List[DeviationAnalysis]:
    """
    Rank deviations by impact (deviation * sample size).
    
    Returns top N most impactful deviations (underperformers).
    """
    # Filter to underperformers only
    underperformers = [d for d in deviations if d.deviation < 0]
    
    # Sort by impact score (most negative first)
    underperformers.sort(key=lambda d: d.impact_score)
    
    return underperformers[:top_n]


def generate_trend_insight(trend: TrendAnalysis) -> str:
    """
    Generate a natural language insight for trend analysis.
    
    Returns a concise, actionable summary.
    """
    if trend.direction == TrendDirection.INSUFFICIENT_DATA:
        return "Insufficient data for trend analysis."
    
    change = trend.current_value - trend.start_value
    change_sign = "+" if change > 0 else ""
    
    base = f"Yield is {trend.direction.value}"
    
    if trend.direction == TrendDirection.VOLATILE:
        return (
            f"{base} ({trend.volatility_value:.1f}% std dev). "
            f"Current: {trend.current_value:.1f}%, started at {trend.start_value:.1f}%. "
            f"High variability makes trends unreliable."
        )
    
    if trend.direction == TrendDirection.STABLE:
        return (
            f"{base} around {trend.current_value:.1f}% "
            f"(±{trend.volatility_value:.1f}%) over {trend.periods_analyzed} periods."
        )
    
    # Improving or declining
    insight = (
        f"{base} at {trend.rate_description}. "
        f"Current: {trend.current_value:.1f}% (from {trend.start_value:.1f}%, "
        f"{change_sign}{change:.1f}% change)."
    )
    
    if trend.change_points:
        insight += f" Significant shifts on: {', '.join(trend.change_points[:3])}."
    
    return insight


def generate_deviation_insight(
    deviations: List[DeviationAnalysis],
    baseline: float,
    dimension_name: str
) -> str:
    """
    Generate a natural language insight for deviation analysis.
    
    Returns a concise summary of findings.
    """
    critical = [d for d in deviations if d.significance == SignificanceLevel.CRITICAL]
    high = [d for d in deviations if d.significance == SignificanceLevel.HIGH]
    
    if not critical and not high:
        return f"No significant {dimension_name} deviations found. All within ±5% of baseline ({baseline:.1f}%)."
    
    findings = []
    
    if critical:
        top = critical[0]
        findings.append(
            f"CRITICAL: {top.value} at {top.yield_value:.1f}% yield "
            f"({top.deviation:+.1f}% vs baseline {baseline:.1f}%)"
        )
    
    if high and len(findings) < 2:
        top = high[0]
        findings.append(
            f"HIGH: {top.value} at {top.yield_value:.1f}% yield "
            f"({top.deviation:+.1f}%)"
        )
    
    count = len(critical) + len(high)
    insight = "; ".join(findings)
    
    if count > 2:
        insight += f" (+{count - 2} more issues)"
    
    return insight


def generate_failure_mode_hypothesis(
    findings: List[DeviationAnalysis],
    dimension: str
) -> Optional[str]:
    """
    Generate a hypothesis for the failure mode based on findings.
    
    Uses patterns in the data to suggest likely causes.
    """
    if not findings:
        return None
    
    # Common patterns
    dimension_hints = {
        "stationName": "equipment-related issue (calibration, fixture wear, environment)",
        "station_name": "equipment-related issue (calibration, fixture wear, environment)",
        "fixtureId": "fixture-specific problem (wear, contamination, alignment)",
        "fixture_id": "fixture-specific problem (wear, contamination, alignment)",
        "operator": "operator skill/training difference",
        "batchNumber": "incoming material batch quality variation",
        "batch_number": "incoming material batch quality variation",
        "location": "line/cell-specific environmental or process difference",
        "testOperation": "process routing or test coverage issue",
        "test_operation": "process routing or test coverage issue",
        "swFilename": "test software version regression",
        "sw_filename": "test software version regression",
        "revision": "design change impact on testability",
    }
    
    hint = dimension_hints.get(dimension, "configuration-specific issue")
    
    top = findings[0]
    if len(findings) == 1:
        return f"Single {dimension} ({top.value}) showing issues suggests {hint}."
    else:
        return f"Multiple {dimension} values affected - investigate common factors: {hint}."


def summarize_for_agent(
    trend: Optional[TrendAnalysis] = None,
    deviations: Optional[List[DeviationAnalysis]] = None,
    dimension: Optional[str] = None,
    baseline: Optional[float] = None,
    max_tokens: int = 300
) -> Dict[str, Any]:
    """
    Create a token-efficient summary for the LLM agent.
    
    Prioritizes actionable insights over raw data.
    """
    summary = {"insights": []}
    
    if trend:
        summary["trend"] = {
            "direction": trend.direction.value,
            "rate": trend.rate_description,
            "current": trend.current_value,
            "confidence": trend.confidence,
        }
        summary["insights"].append(generate_trend_insight(trend))
    
    if deviations and dimension and baseline is not None:
        critical = [d for d in deviations if d.significance == SignificanceLevel.CRITICAL]
        high = [d for d in deviations if d.significance == SignificanceLevel.HIGH]
        
        # Include only top findings (not all data)
        summary["findings"] = {
            "critical_count": len(critical),
            "high_count": len(high),
            "top_issues": [
                {"value": d.value, "yield": d.yield_value, "deviation": d.deviation}
                for d in (critical + high)[:3]
            ],
            "baseline": baseline,
        }
        summary["insights"].append(generate_deviation_insight(deviations, baseline, dimension))
        
        hypothesis = generate_failure_mode_hypothesis(critical + high, dimension)
        if hypothesis:
            summary["hypothesis"] = hypothesis
    
    return summary
