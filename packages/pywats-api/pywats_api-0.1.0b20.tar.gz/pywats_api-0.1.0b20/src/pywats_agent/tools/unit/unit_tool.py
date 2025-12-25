"""
Unit Analysis Tool for WATS Agent.

Comprehensive tool for analyzing individual units or small sets of units.

WATS UNIT CONCEPTS:
- A unit is identified by: part_number + serial_number
- Multiple revisions = same unit (upgraded/reworked)
- Sub-units: Components assembled into a parent unit (tracked in UUT reports)
- Production unit: MES-managed unit with phase tracking (optional)
- UUT reports: Test results linked to units

DATA SOURCES:
1. Analytics Domain:
   - Serial number history: All UUT/UUR reports for a serial
   - Sub-unit history tracking
   
2. Production Domain:
   - Production unit info (if MES tracking enabled)
   - Unit verification/grading (requires verification rules)
   - Unit phase tracking
   
3. Report Domain:
   - Full test report details
   - Sub-unit information from reports
"""

from typing import Any, Dict, List, Optional, TYPE_CHECKING, Literal
from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel, Field

from .._base import AgentTool, ToolInput
from ...result import AgentResult

if TYPE_CHECKING:
    from pywats import pyWATS


# =============================================================================
# Data Models
# =============================================================================

class UnitStatus(str, Enum):
    """Overall unit status classification."""
    PASSING = "passing"           # All tests passed
    FAILING = "failing"           # Has failing tests
    IN_PROGRESS = "in_progress"   # Under production/test
    REPAIRED = "repaired"         # Was failing, now repaired
    SCRAPPED = "scrapped"         # Marked as scrapped
    UNKNOWN = "unknown"           # No test data or unclear status


class AnalysisScope(str, Enum):
    """What to include in the analysis."""
    QUICK = "quick"           # Basic status and last test only
    STANDARD = "standard"     # Status, history summary, verification
    FULL = "full"             # Everything including sub-units and all history
    HISTORY_ONLY = "history"  # Just test history (for debugging)
    VERIFICATION = "verify"   # Focus on verification/grading


class TestSummary(BaseModel):
    """Summary of test results for a unit."""
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    error: int = 0
    first_test: Optional[datetime] = None
    last_test: Optional[datetime] = None
    first_pass: Optional[datetime] = None
    processes_tested: List[str] = Field(default_factory=list)
    stations_used: List[str] = Field(default_factory=list)
    
    @property
    def pass_rate(self) -> float:
        """Calculate pass rate."""
        if self.total_tests == 0:
            return 0.0
        return self.passed / self.total_tests * 100


class SubUnitInfo(BaseModel):
    """Information about a sub-unit (component)."""
    part_type: Optional[str] = None
    serial_number: Optional[str] = None
    part_number: Optional[str] = None
    revision: Optional[str] = None
    # From sub-unit's own test history if available
    test_summary: Optional[TestSummary] = None


class ProcessVerification(BaseModel):
    """Verification status for a single process."""
    process_code: Optional[int] = None
    process_name: Optional[str] = None
    status: Optional[str] = None
    last_test: Optional[datetime] = None
    station_name: Optional[str] = None
    total_count: int = 0
    non_passed_count: int = 0
    repair_count: int = 0
    
    @property
    def is_passing(self) -> bool:
        return self.status == "Passed"


class VerificationGrade(BaseModel):
    """Complete verification grade for a unit."""
    status: Optional[str] = None
    grade: Optional[str] = None
    all_processes_in_order: bool = False
    all_passed_first_run: bool = False
    all_passed_any_run: bool = False
    all_passed_last_run: bool = False
    no_repairs: bool = False
    process_results: List[ProcessVerification] = Field(default_factory=list)
    
    # Indicates if verification rules exist
    has_rules: bool = False
    rule_suggestion: Optional[str] = None


class ProductionInfo(BaseModel):
    """Production/MES tracking information."""
    has_production_unit: bool = False
    phase: Optional[str] = None
    phase_id: Optional[int] = None
    batch_number: Optional[str] = None
    location: Optional[str] = None
    created: Optional[datetime] = None
    parent_serial_number: Optional[str] = None


class UnitInfo(BaseModel):
    """Complete unit information."""
    # Identity
    serial_number: str
    part_number: str
    revision: Optional[str] = None
    
    # Overall status
    status: UnitStatus = UnitStatus.UNKNOWN
    status_reason: Optional[str] = None
    
    # Test summary
    test_summary: TestSummary = Field(default_factory=TestSummary)
    
    # Production info (if MES enabled)
    production: ProductionInfo = Field(default_factory=ProductionInfo)
    
    # Verification/grading (if rules exist)
    verification: Optional[VerificationGrade] = None
    
    # Sub-units (components)
    sub_units: List[SubUnitInfo] = Field(default_factory=list)
    
    # Recent test history (last N reports)
    recent_tests: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Any warnings or notes
    warnings: List[str] = Field(default_factory=list)


# =============================================================================
# Tool Input
# =============================================================================

class UnitAnalysisInput(ToolInput):
    """Input parameters for unit analysis."""
    
    serial_number: str = Field(
        description="The unit serial number to analyze"
    )
    
    part_number: Optional[str] = Field(
        default=None,
        description="The product part number. If not provided, will attempt to find from history."
    )
    
    scope: AnalysisScope = Field(
        default=AnalysisScope.STANDARD,
        description="Analysis depth: quick (last test only), standard (summary + verification), "
                    "full (include sub-units and all history), history (test history only), "
                    "verify (focus on verification grading)"
    )
    
    include_sub_units: bool = Field(
        default=False,
        description="Include sub-unit (component) history. Auto-enabled for 'full' scope."
    )
    
    max_history: int = Field(
        default=50,
        description="Maximum number of historical test records to retrieve"
    )


# =============================================================================
# Unit Analysis Tool
# =============================================================================

class UnitAnalysisTool(AgentTool):
    """
    Comprehensive unit analysis tool.
    
    Analyzes individual units to provide:
    - Complete test history and status
    - Production/MES tracking information
    - Unit verification and grading
    - Sub-unit (component) tracking
    - Status classification and recommendations
    
    A unit in WATS is identified by the combination of part_number + serial_number.
    Multiple revisions are considered the same unit (upgraded/reworked).
    """
    
    name = "analyze_unit"
    description = """Analyze a single unit's complete status, test history, and verification.

Use this tool when you need to:
- Check the current status of a specific unit (pass/fail/in-progress)
- Get the complete test history for a serial number
- Verify if a unit is passing all required tests
- See what sub-units (components) are assembled into a unit
- Understand why a unit is failing or has issues
- Check production phase and MES tracking status

A unit is identified by serial_number + part_number. If part_number is unknown, 
the tool will attempt to find it from the test history.

Scope options:
- quick: Just last test status (fast)
- standard: Status + history summary + verification (default)
- full: Everything including sub-units and full history
- history: Focus on test history timeline
- verify: Focus on verification rules and grading

Returns comprehensive unit information including status, test summary, 
production tracking, verification grade, and any warnings or issues."""

    input_model = UnitAnalysisInput
    
    def _execute(self, input: UnitAnalysisInput) -> AgentResult:
        """Execute unit analysis."""
        try:
            # Initialize unit info
            unit_info = UnitInfo(
                serial_number=input.serial_number,
                part_number=input.part_number or "",
            )
            
            # Step 1: Get test history to find part number if not provided
            history = self._get_test_history(
                input.serial_number, 
                input.part_number,
                input.max_history
            )
            
            if not history and not input.part_number:
                return AgentResult.fail(
                    f"No test history found for serial number '{input.serial_number}'. "
                    f"Try providing a part_number to search the production database."
                )
            
            # Extract part number from history if not provided
            if history and not input.part_number:
                unit_info.part_number = self._extract_part_number(history)
                unit_info.warnings.append(
                    f"Part number inferred from test history: {unit_info.part_number}"
                )
            
            # Extract revision from history
            if history:
                unit_info.revision = self._extract_revision(history)
            
            # Step 2: Build test summary
            unit_info.test_summary = self._build_test_summary(history)
            unit_info.recent_tests = self._format_recent_tests(
                history[:10] if input.scope == AnalysisScope.QUICK else history[:20]
            )
            
            # Step 3: Get production unit info (if available)
            if input.scope in [AnalysisScope.STANDARD, AnalysisScope.FULL, AnalysisScope.VERIFICATION]:
                unit_info.production = self._get_production_info(
                    input.serial_number, 
                    unit_info.part_number
                )
            
            # Step 4: Get verification/grading (if rules exist)
            if input.scope in [AnalysisScope.STANDARD, AnalysisScope.FULL, AnalysisScope.VERIFICATION]:
                unit_info.verification = self._get_verification(
                    input.serial_number,
                    unit_info.part_number,
                    unit_info.revision
                )
            
            # Step 5: Get sub-unit info (for full scope or explicit request)
            if input.scope == AnalysisScope.FULL or input.include_sub_units:
                unit_info.sub_units = self._get_sub_units(
                    input.serial_number,
                    unit_info.part_number,
                    history
                )
            
            # Step 6: Determine overall status
            unit_info.status, unit_info.status_reason = self._determine_status(unit_info)
            
            # Build summary
            summary = self._build_summary(unit_info, input.scope)
            
            return AgentResult.ok(
                data=unit_info.model_dump(mode="json"),
                summary=summary
            )
            
        except Exception as e:
            return AgentResult.fail(f"{type(e).__name__}: {str(e)}")
    
    # =========================================================================
    # Private Methods
    # =========================================================================
    
    def _get_test_history(
        self, 
        serial_number: str, 
        part_number: Optional[str],
        max_records: int
    ) -> List[Any]:
        """Get test history for a serial number."""
        from pywats import WATSFilter
        
        # Try serial number history first (includes all reports)
        filter_data = WATSFilter(
            serial_number=serial_number,
            top_count=max_records
        )
        
        if part_number:
            filter_data.part_number = part_number
        
        try:
            history = self._api.analytics.get_serial_number_history(filter_data)
            if history:
                return history
        except Exception:
            pass
        
        # Fallback to UUT report query
        try:
            reports = self._api.analytics.get_uut_reports(
                serial_number=serial_number,
                part_number=part_number,
                top_count=max_records
            )
            return reports or []
        except Exception:
            return []
    
    def _extract_part_number(self, history: List[Any]) -> str:
        """Extract part number from history records."""
        for record in history:
            pn = getattr(record, 'part_number', None)
            if pn:
                return pn
        return ""
    
    def _extract_revision(self, history: List[Any]) -> Optional[str]:
        """Extract latest revision from history."""
        for record in history:
            rev = getattr(record, 'revision', None)
            if rev:
                return rev
        return None
    
    def _build_test_summary(self, history: List[Any]) -> TestSummary:
        """Build test summary from history records."""
        summary = TestSummary()
        
        if not history:
            return summary
        
        processes = set()
        stations = set()
        
        for record in history:
            summary.total_tests += 1
            
            status = getattr(record, 'status', 'U')
            if status in ['P', 'Passed', 'passed', 'PASSED']:
                summary.passed += 1
            elif status in ['F', 'Failed', 'failed', 'FAILED']:
                summary.failed += 1
            elif status in ['E', 'Error', 'error', 'ERROR']:
                summary.error += 1
            
            # Track dates
            start = getattr(record, 'start', None) or getattr(record, 'start_utc', None)
            if start:
                if summary.first_test is None or start < summary.first_test:
                    summary.first_test = start
                if summary.last_test is None or start > summary.last_test:
                    summary.last_test = start
                
                # Track first pass
                if status in ['P', 'Passed', 'passed', 'PASSED']:
                    if summary.first_pass is None or start < summary.first_pass:
                        summary.first_pass = start
            
            # Track processes and stations
            process = getattr(record, 'process_name', None) or getattr(record, 'process_code', None)
            if process:
                processes.add(str(process))
            
            station = getattr(record, 'station_name', None)
            if station:
                stations.add(station)
        
        summary.processes_tested = sorted(processes)
        summary.stations_used = sorted(stations)
        
        return summary
    
    def _format_recent_tests(self, history: List[Any]) -> List[Dict[str, Any]]:
        """Format recent tests for output."""
        result = []
        for record in history:
            status = getattr(record, 'status', 'U')
            status_icon = "✅" if status in ['P', 'Passed'] else "❌" if status in ['F', 'Failed'] else "⚠️"
            
            result.append({
                "date": str(getattr(record, 'start', '') or getattr(record, 'start_utc', '')),
                "status": status,
                "status_icon": status_icon,
                "process": getattr(record, 'process_name', None) or getattr(record, 'process_code', None),
                "station": getattr(record, 'station_name', None),
                "revision": getattr(record, 'revision', None),
            })
        return result
    
    def _get_production_info(self, serial_number: str, part_number: str) -> ProductionInfo:
        """Get production/MES tracking information."""
        info = ProductionInfo()
        
        if not part_number:
            return info
        
        try:
            unit = self._api.production.get_unit(serial_number, part_number)
            if unit:
                info.has_production_unit = True
                info.phase = getattr(unit, 'unit_phase', None)
                info.phase_id = getattr(unit, 'unit_phase_id', None)
                info.batch_number = getattr(unit, 'batch_number', None)
                info.location = getattr(unit, 'current_location', None)
                info.created = getattr(unit, 'serial_date', None)
                info.parent_serial_number = getattr(unit, 'parent_serial_number', None)
        except Exception:
            pass
        
        return info
    
    def _get_verification(
        self, 
        serial_number: str, 
        part_number: str,
        revision: Optional[str]
    ) -> Optional[VerificationGrade]:
        """Get unit verification/grading."""
        if not part_number:
            return None
        
        try:
            grade = self._api.production.get_unit_grade(
                serial_number, part_number, revision
            )
            
            if not grade:
                # No verification rules exist
                return VerificationGrade(
                    has_rules=False,
                    rule_suggestion="No unit verification rules defined for this product. "
                                    "Verification rules can be created in WATS Control Panel "
                                    "to automatically grade units based on test completion."
                )
            
            # Build verification result
            result = VerificationGrade(
                has_rules=True,
                status=grade.status,
                grade=grade.grade,
                all_processes_in_order=grade.all_processes_executed_in_correct_order,
                all_passed_first_run=grade.all_processes_passed_first_run,
                all_passed_any_run=grade.all_processes_passed_any_run,
                all_passed_last_run=grade.all_processes_passed_last_run,
                no_repairs=grade.no_repairs,
            )
            
            # Add process results
            for proc_result in (grade.results or []):
                result.process_results.append(ProcessVerification(
                    process_code=proc_result.process_code,
                    process_name=proc_result.process_name,
                    status=proc_result.status,
                    last_test=proc_result.start_utc,
                    station_name=proc_result.station_name,
                    total_count=proc_result.total_count or 0,
                    non_passed_count=proc_result.non_passed_count or 0,
                    repair_count=proc_result.repair_count or 0,
                ))
            
            return result
            
        except Exception:
            return None
    
    def _get_sub_units(
        self, 
        serial_number: str, 
        part_number: str,
        history: List[Any]
    ) -> List[SubUnitInfo]:
        """Get sub-unit (component) information."""
        sub_units: Dict[str, SubUnitInfo] = {}
        
        # Try to get sub-units from production unit first
        try:
            unit = self._api.production.get_unit(serial_number, part_number)
            if unit and hasattr(unit, 'sub_units') and unit.sub_units:
                for sub in unit.sub_units:
                    key = f"{getattr(sub, 'serial_number', '')}_{getattr(sub, 'part_number', '')}"
                    if key not in sub_units:
                        sub_units[key] = SubUnitInfo(
                            serial_number=getattr(sub, 'serial_number', None),
                            part_number=getattr(sub, 'part_number', None),
                            revision=getattr(sub, 'revision', None),
                        )
        except Exception:
            pass
        
        # Also extract from test reports (more common source)
        if history:
            # Get the latest report with sub-units
            for record in history:
                report_id = getattr(record, 'id', None)
                if report_id:
                    try:
                        report = self._api.report.get_uut(report_id)
                        if report and hasattr(report, 'sub_units') and report.sub_units:
                            for sub in report.sub_units:
                                sn = getattr(sub, 'sn', None) or getattr(sub, 'serial_number', None)
                                pn = getattr(sub, 'pn', None) or getattr(sub, 'part_number', None)
                                key = f"{sn}_{pn}"
                                if key not in sub_units and sn:
                                    sub_units[key] = SubUnitInfo(
                                        part_type=getattr(sub, 'part_type', None),
                                        serial_number=sn,
                                        part_number=pn,
                                        revision=getattr(sub, 'rev', None) or getattr(sub, 'revision', None),
                                    )
                            break  # Only need sub-units from one report
                    except Exception:
                        continue
        
        return list(sub_units.values())
    
    def _determine_status(self, unit: UnitInfo) -> tuple[UnitStatus, str]:
        """Determine overall unit status."""
        # Check production phase first
        if unit.production.phase:
            phase_lower = unit.production.phase.lower()
            if 'scrapped' in phase_lower:
                return UnitStatus.SCRAPPED, f"Unit phase: {unit.production.phase}"
            if 'production' in phase_lower or 'test' in phase_lower:
                return UnitStatus.IN_PROGRESS, f"Unit phase: {unit.production.phase}"
        
        # Check verification if available
        if unit.verification and unit.verification.has_rules:
            if unit.verification.all_passed_last_run:
                if unit.verification.all_passed_first_run:
                    return UnitStatus.PASSING, "All processes passed first run"
                elif not unit.verification.no_repairs:
                    return UnitStatus.REPAIRED, "Passed after repairs"
                else:
                    return UnitStatus.PASSING, "All processes passed (with retests)"
            else:
                # Find failing processes
                failing = [p.process_name for p in unit.verification.process_results 
                          if not p.is_passing and p.process_name]
                if failing:
                    return UnitStatus.FAILING, f"Failed processes: {', '.join(failing)}"
                return UnitStatus.FAILING, "Not all processes passed"
        
        # Fall back to test summary
        if unit.test_summary.total_tests == 0:
            return UnitStatus.UNKNOWN, "No test records found"
        
        if unit.test_summary.failed == 0 and unit.test_summary.error == 0:
            return UnitStatus.PASSING, f"All {unit.test_summary.total_tests} tests passed"
        
        # Check if last test passed
        if unit.recent_tests:
            last_status = unit.recent_tests[0].get('status', '')
            if last_status in ['P', 'Passed']:
                if unit.test_summary.failed > 0:
                    return UnitStatus.REPAIRED, f"Last test passed (had {unit.test_summary.failed} failures)"
                return UnitStatus.PASSING, "Last test passed"
            else:
                return UnitStatus.FAILING, f"Last test: {last_status}"
        
        return UnitStatus.UNKNOWN, "Unable to determine status"
    
    def _build_summary(self, unit: UnitInfo, scope: AnalysisScope) -> str:
        """Build human-readable summary."""
        lines = []
        
        # Header
        status_icons = {
            UnitStatus.PASSING: "✅",
            UnitStatus.FAILING: "❌",
            UnitStatus.IN_PROGRESS: "🔄",
            UnitStatus.REPAIRED: "🔧",
            UnitStatus.SCRAPPED: "🗑️",
            UnitStatus.UNKNOWN: "❓",
        }
        
        icon = status_icons.get(unit.status, "❓")
        lines.append(f"{icon} Unit Analysis: {unit.serial_number}")
        lines.append(f"   Part Number: {unit.part_number}" + (f" Rev {unit.revision}" if unit.revision else ""))
        lines.append(f"   Status: {unit.status.value.upper()} - {unit.status_reason}")
        lines.append("")
        
        # Test Summary
        ts = unit.test_summary
        if ts.total_tests > 0:
            lines.append(f"📊 Test Summary:")
            lines.append(f"   Total: {ts.total_tests} | Passed: {ts.passed} | Failed: {ts.failed} | Error: {ts.error}")
            lines.append(f"   Pass Rate: {ts.pass_rate:.1f}%")
            if ts.first_test:
                lines.append(f"   First Test: {ts.first_test}")
            if ts.last_test:
                lines.append(f"   Last Test: {ts.last_test}")
            if ts.processes_tested:
                lines.append(f"   Processes: {', '.join(ts.processes_tested[:5])}")
            lines.append("")
        
        # Production Info
        if unit.production.has_production_unit:
            lines.append(f"🏭 Production Tracking:")
            lines.append(f"   Phase: {unit.production.phase or 'N/A'}")
            if unit.production.batch_number:
                lines.append(f"   Batch: {unit.production.batch_number}")
            if unit.production.parent_serial_number:
                lines.append(f"   Parent: {unit.production.parent_serial_number}")
            lines.append("")
        
        # Verification
        if unit.verification:
            if unit.verification.has_rules:
                lines.append(f"📋 Verification Grade: {unit.verification.grade or 'N/A'}")
                lines.append(f"   All Passed Last Run: {'✅' if unit.verification.all_passed_last_run else '❌'}")
                lines.append(f"   First Pass: {'✅' if unit.verification.all_passed_first_run else '❌'}")
                lines.append(f"   No Repairs: {'✅' if unit.verification.no_repairs else '❌'}")
                
                if unit.verification.process_results and scope != AnalysisScope.QUICK:
                    lines.append("   Process Status:")
                    for proc in unit.verification.process_results[:5]:
                        p_icon = "✅" if proc.is_passing else "❌"
                        lines.append(f"      {p_icon} {proc.process_name}: {proc.status}")
                lines.append("")
            else:
                lines.append(f"⚠️ No verification rules configured")
                if unit.verification.rule_suggestion:
                    lines.append(f"   {unit.verification.rule_suggestion}")
                lines.append("")
        
        # Sub-units
        if unit.sub_units:
            lines.append(f"📦 Sub-Units ({len(unit.sub_units)}):")
            for sub in unit.sub_units[:5]:
                lines.append(f"   • {sub.part_type or 'Component'}: {sub.serial_number} ({sub.part_number})")
            if len(unit.sub_units) > 5:
                lines.append(f"   ... and {len(unit.sub_units) - 5} more")
            lines.append("")
        
        # Recent Tests (for standard/full scope)
        if scope != AnalysisScope.QUICK and unit.recent_tests:
            lines.append(f"📝 Recent Tests:")
            for test in unit.recent_tests[:5]:
                lines.append(f"   {test['status_icon']} {test['date']} | {test['process']} @ {test['station']}")
            if len(unit.recent_tests) > 5:
                lines.append(f"   ... and {len(unit.recent_tests) - 5} more in history")
        
        # Warnings
        if unit.warnings:
            lines.append("")
            lines.append("⚠️ Notes:")
            for warn in unit.warnings:
                lines.append(f"   • {warn}")
        
        return "\n".join(lines)


# =============================================================================
# Tool Definition Helper
# =============================================================================

def get_definition() -> Dict[str, Any]:
    """Get tool definition for registration."""
    return UnitAnalysisTool.get_definition()
