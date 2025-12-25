"""
Asset Health Tool for AI agents.

Checks calibration and maintenance status of assets identified as
potential root causes. Use after AssetDimensionTool identifies
suspect assets.

WORKFLOW:
1. Look up asset by serial number
2. Check calibration status (current, due soon, overdue)
3. Check maintenance status
4. Check usage counters vs limits
5. Return prioritized health assessment

INTEGRATION:
┌─────────────────────────────────────────────────────────────────────────────┐
│ AssetDimensionTool → identifies suspect assets                              │
│                   ↓                                                         │
│ AssetHealthTool → checks calibration/maintenance status                     │
│                   ↓                                                         │
│ AssetDegradationTool → analyzes quality trends over calibration cycles     │
└─────────────────────────────────────────────────────────────────────────────┘

KEY METRICS:
- Calibration status: days since/until calibration, overdue amount
- Maintenance status: days since/until maintenance
- Usage counters: running count vs limit, total count vs limit
- Alarm state: OK, WARNING, ALARM (based on configured thresholds)
"""

from typing import Any, Dict, List, Optional, TYPE_CHECKING
from datetime import datetime

from ...result import AgentResult
from .models import (
    AssetHealthFilter,
    AssetHealthResult,
    AssetHealthInfo,
    AssetHealthStatus,
    CalibrationStatus,
)

if TYPE_CHECKING:
    from pywats import pyWATS
    from pywats.domains.asset.models import Asset


# =============================================================================
# Configuration
# =============================================================================

# Warning thresholds (if not configured on asset type)
DEFAULT_CALIBRATION_WARNING_DAYS = 7    # Warn if calibration due within 7 days
DEFAULT_MAINTENANCE_WARNING_DAYS = 7    # Warn if maintenance due within 7 days
DEFAULT_COUNTER_WARNING_PCT = 0.80      # Warn if counter at 80% of limit


# =============================================================================
# Asset Health Tool
# =============================================================================

class AssetHealthTool:
    """
    Checks calibration and maintenance status of assets.
    
    Use this tool after AssetDimensionTool identifies assets with
    yield problems. Determines if the asset is:
    - Currently calibrated
    - Due for calibration soon
    - Overdue for calibration
    - In need of maintenance
    
    WHEN TO USE:
    - AssetDimensionTool identified suspect assets
    - Need to verify calibration status before blaming an asset
    - Planning calibration/maintenance schedules
    - Checking why a specific asset has degraded performance
    
    OUTPUT:
    - Health status: HEALTHY, WARNING, CRITICAL, UNKNOWN
    - Calibration status with dates and metrics
    - Maintenance status
    - Usage counter percentages
    - Prioritized list of issues
    
    NEXT STEPS:
    - If overdue → Schedule immediate calibration/maintenance
    - If due soon → Plan calibration, investigate if quality is degrading
    - If healthy but still suspect → Use AssetDegradationTool for trend analysis
    """
    
    def __init__(self, api: "pyWATS"):
        """
        Initialize with pyWATS API.
        
        Args:
            api: Authenticated pyWATS API instance
        """
        self._api = api
    
    # =========================================================================
    # Main Entry Point
    # =========================================================================
    
    def check_health(self, filter_input: AssetHealthFilter) -> AgentResult:
        """
        Check health status of specified assets.
        
        Args:
            filter_input: Filter specifying which assets to check
            
        Returns:
            AgentResult with AssetHealthResult data
        """
        try:
            # Collect asset serial numbers to check
            serials_to_check = self._collect_serials(filter_input)
            
            if not serials_to_check:
                return AgentResult(
                    success=False,
                    error="No assets specified. Provide asset_serial, asset_serials, or asset_type.",
                    summary="No assets to check."
                )
            
            # Check each asset
            asset_infos: List[AssetHealthInfo] = []
            for serial in serials_to_check:
                info = self._check_single_asset(serial, filter_input.include_history)
                if info:
                    asset_infos.append(info)
            
            if not asset_infos:
                return AgentResult(
                    success=True,
                    data=AssetHealthResult(
                        assets_checked=len(serials_to_check),
                        healthy_count=0,
                        warning_count=0,
                        critical_count=0
                    ),
                    summary=f"No asset data found for {len(serials_to_check)} serial number(s)."
                )
            
            # Filter if requested
            if filter_input.only_problematic:
                asset_infos = [
                    a for a in asset_infos 
                    if a.health_status in (AssetHealthStatus.WARNING, AssetHealthStatus.CRITICAL)
                ]
            
            # Categorize by status
            healthy = [a for a in asset_infos if a.health_status == AssetHealthStatus.HEALTHY]
            warning = [a for a in asset_infos if a.health_status == AssetHealthStatus.WARNING]
            critical = [a for a in asset_infos if a.health_status == AssetHealthStatus.CRITICAL]
            
            result = AssetHealthResult(
                assets_checked=len(serials_to_check),
                healthy_count=len(healthy),
                warning_count=len(warning),
                critical_count=len(critical),
                assets=asset_infos,
                critical_assets=critical,
                warning_assets=warning
            )
            
            return AgentResult(
                success=True,
                data=result,
                summary=self._build_summary(result),
                recommendations=self._build_recommendations(result)
            )
            
        except Exception as e:
            return AgentResult(
                success=False,
                error=f"Asset health check failed: {str(e)}",
                summary=f"Failed to check asset health: {str(e)}"
            )
    
    # =========================================================================
    # Data Collection
    # =========================================================================
    
    def _collect_serials(self, filter_input: AssetHealthFilter) -> List[str]:
        """Collect asset serial numbers to check."""
        serials = []
        
        # Single serial
        if filter_input.asset_serial:
            serials.append(filter_input.asset_serial)
        
        # List of serials
        if filter_input.asset_serials:
            serials.extend(filter_input.asset_serials)
        
        # By asset type - get all assets of that type
        if filter_input.asset_type:
            try:
                assets = self._api.asset.get_assets(
                    filter_str=f"assetType/typeName eq '{filter_input.asset_type}'"
                )
                serials.extend([a.serial_number for a in assets if a.serial_number])
            except Exception:
                pass  # Continue with what we have
        
        # Remove duplicates while preserving order
        seen = set()
        unique_serials = []
        for s in serials:
            if s not in seen:
                seen.add(s)
                unique_serials.append(s)
        
        return unique_serials
    
    def _check_single_asset(
        self,
        serial: str,
        include_history: bool
    ) -> Optional[AssetHealthInfo]:
        """Check health of a single asset."""
        
        # Get asset details
        asset = self._api.asset.get_asset_by_serial(serial)
        if not asset:
            return None
        
        # Get status (includes alarm info)
        status = self._api.asset.get_status(serial_number=serial)
        
        # Build health info
        return self._build_health_info(asset, status)
    
    def _build_health_info(
        self,
        asset: "Asset",
        status: Optional[Dict[str, Any]]
    ) -> AssetHealthInfo:
        """Build AssetHealthInfo from asset data and status."""
        
        warnings: List[str] = []
        now = datetime.utcnow()
        
        # =================================================================
        # Calibration Status
        # =================================================================
        cal_status = CalibrationStatus.UNKNOWN
        days_since_cal = None
        cal_overdue = None
        cal_interval = None
        
        if asset.last_calibration_date:
            days_since_cal = (now - asset.last_calibration_date).days
        
        if asset.asset_type and asset.asset_type.calibration_interval:
            cal_interval = asset.asset_type.calibration_interval
        
        if asset.next_calibration_date:
            days_until = (asset.next_calibration_date - now).days
            
            if days_until < 0:
                cal_status = CalibrationStatus.OVERDUE
                cal_overdue = abs(days_until)
                warnings.append(f"Calibration OVERDUE by {cal_overdue} days")
            elif days_until <= DEFAULT_CALIBRATION_WARNING_DAYS:
                cal_status = CalibrationStatus.DUE_SOON
                warnings.append(f"Calibration due in {days_until} days")
            else:
                cal_status = CalibrationStatus.CURRENT
        elif asset.last_calibration_date is None:
            cal_status = CalibrationStatus.UNKNOWN
            warnings.append("Asset has never been calibrated")
        else:
            cal_status = CalibrationStatus.CURRENT
        
        # =================================================================
        # Usage Counters
        # =================================================================
        running_count = asset.running_count
        running_limit = None
        running_pct = None
        total_count = asset.total_count
        total_limit = None
        
        if asset.asset_type:
            running_limit = asset.asset_type.running_count_limit
            total_limit = asset.asset_type.total_count_limit
        
        if running_count is not None and running_limit:
            running_pct = running_count / running_limit
            if running_pct >= 1.0:
                warnings.append(f"Running count EXCEEDED: {running_count}/{running_limit}")
            elif running_pct >= DEFAULT_COUNTER_WARNING_PCT:
                warnings.append(f"Running count at {running_pct*100:.0f}% of limit")
        
        # =================================================================
        # Maintenance Status
        # =================================================================
        days_since_maint = None
        maint_overdue = None
        
        if asset.last_maintenance_date:
            days_since_maint = (now - asset.last_maintenance_date).days
        
        if asset.next_maintenance_date:
            days_until = (asset.next_maintenance_date - now).days
            if days_until < 0:
                maint_overdue = abs(days_until)
                warnings.append(f"Maintenance OVERDUE by {maint_overdue} days")
            elif days_until <= DEFAULT_MAINTENANCE_WARNING_DAYS:
                warnings.append(f"Maintenance due in {days_until} days")
        
        # =================================================================
        # Overall Health Status
        # =================================================================
        health_status = AssetHealthStatus.HEALTHY
        
        if cal_status == CalibrationStatus.OVERDUE or maint_overdue:
            health_status = AssetHealthStatus.CRITICAL
        elif cal_status == CalibrationStatus.DUE_SOON:
            health_status = AssetHealthStatus.WARNING
        elif running_pct and running_pct >= DEFAULT_COUNTER_WARNING_PCT:
            health_status = AssetHealthStatus.WARNING
        elif cal_status == CalibrationStatus.UNKNOWN:
            health_status = AssetHealthStatus.UNKNOWN
        
        return AssetHealthInfo(
            asset_serial=asset.serial_number,
            asset_name=asset.asset_name,
            asset_type=asset.asset_type.type_name if asset.asset_type else None,
            health_status=health_status,
            calibration_status=cal_status,
            last_calibration_date=asset.last_calibration_date,
            next_calibration_date=asset.next_calibration_date,
            days_since_calibration=days_since_cal,
            calibration_days_overdue=cal_overdue,
            calibration_interval_days=cal_interval,
            running_count=running_count,
            running_count_limit=running_limit,
            running_count_pct=running_pct,
            total_count=total_count,
            total_count_limit=total_limit,
            last_maintenance_date=asset.last_maintenance_date,
            next_maintenance_date=asset.next_maintenance_date,
            days_since_maintenance=days_since_maint,
            maintenance_days_overdue=maint_overdue,
            warnings=warnings
        )
    
    # =========================================================================
    # Reporting
    # =========================================================================
    
    def _build_summary(self, result: AssetHealthResult) -> str:
        """Build human-readable summary."""
        parts = [f"Checked {result.assets_checked} asset(s):"]
        
        if result.critical_count:
            parts.append(f"{result.critical_count} CRITICAL")
        if result.warning_count:
            parts.append(f"{result.warning_count} WARNING")
        if result.healthy_count:
            parts.append(f"{result.healthy_count} healthy")
        
        return " ".join(parts)
    
    def _build_recommendations(self, result: AssetHealthResult) -> List[str]:
        """Build actionable recommendations."""
        recommendations = []
        
        if result.critical_assets:
            recommendations.append(
                f"CRITICAL: {result.critical_count} asset(s) need immediate attention:"
            )
            for asset in result.critical_assets[:5]:
                issues = ", ".join(asset.warnings) if asset.warnings else "Critical status"
                recommendations.append(f"  → {asset.asset_serial}: {issues}")
        
        if result.warning_assets:
            recommendations.append(
                f"WARNING: {result.warning_count} asset(s) need attention soon:"
            )
            for asset in result.warning_assets[:5]:
                issues = ", ".join(asset.warnings) if asset.warnings else "Warning status"
                recommendations.append(f"  → {asset.asset_serial}: {issues}")
        
        if result.critical_count == 0 and result.warning_count == 0:
            if result.healthy_count:
                recommendations.append(
                    "All assets are healthy. If yield issues persist, "
                    "use AssetDegradationTool to check for quality drift."
                )
            else:
                recommendations.append(
                    "No health data available. Assets may not have calibration tracking configured."
                )
        
        return recommendations


# =============================================================================
# Tool Definition for Agent Integration
# =============================================================================

def get_asset_health_tool_definition() -> Dict[str, Any]:
    """Get the tool definition for agent registration."""
    return {
        "name": "asset_health_check",
        "description": (
            "Check calibration and maintenance status of assets (fixtures, stations). "
            "Use after AssetDimensionTool identifies suspect assets, to verify if "
            "calibration or maintenance issues could be causing yield problems."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "asset_serial": {
                    "type": "string",
                    "description": "Single asset serial number to check"
                },
                "asset_serials": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of asset serial numbers to check"
                },
                "asset_type": {
                    "type": "string",
                    "description": "Check all assets of this type (e.g., 'Fixture')"
                },
                "only_problematic": {
                    "type": "boolean",
                    "description": "Only return assets with warning/critical status"
                },
                "include_history": {
                    "type": "boolean",
                    "description": "Include calibration/maintenance history logs"
                }
            },
            "required": []
        }
    }
