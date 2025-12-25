"""Analytics service - business logic layer.

All business operations for statistics, KPIs, yield analysis, and dashboard data.
Note: Maps to the WATS /api/App/* endpoints (backend naming).
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Union

from .repository import AnalyticsRepository
from .models import (
    YieldData,
    ProcessInfo,
    LevelInfo,
    ProductGroup,
    StepAnalysisRow,
    TopFailedStep,
    RepairStatistics,
    RepairHistoryRecord,
    MeasurementData,
    AggregatedMeasurement,
    OeeAnalysisResult,
)
from ..report.models import WATSFilter, ReportHeader


class AnalyticsService:
    """
    Analytics/Statistics business logic layer.

    Provides high-level operations for yield statistics, KPIs, failure analysis,
    and production analytics. This module wraps the WATS /api/App/* endpoints.
    
    Example:
        >>> api = pyWATS(base_url="...", token="...")
        >>> # Get yield statistics
        >>> yield_data = api.analytics.get_dynamic_yield(
        ...     WATSFilter(part_number="WIDGET-001", period_count=30)
        ... )
        >>> # Get top failures
        >>> failures = api.analytics.get_top_failed(part_number="WIDGET-001")
    """

    def __init__(self, repository: AnalyticsRepository):
        """
        Initialize with AnalyticsRepository.

        Args:
            repository: AnalyticsRepository instance for data access
        """
        self._repository = repository

    # =========================================================================
    # System Info
    # =========================================================================

    def get_version(self) -> Optional[str]:
        """
        Get WATS API version information.

        Returns:
            Version string (e.g., "24.1.0") or None if not available
            
        Example:
            >>> version = api.analytics.get_version()
            >>> print(f"WATS Server: {version}")
            WATS Server: 24.1.0
        """
        return self._repository.get_version()

    def get_processes(self) -> List[ProcessInfo]:
        """
        Get all defined test processes/operations.

        Returns:
            List of ProcessInfo objects
            
        Example:
            >>> processes = api.analytics.get_processes()
            >>> for p in processes:
            ...     print(f"{p.code}: {p.name} (test={p.is_test_operation})")
            100: End of line test (test=True)
            500: Repair (test=False)
        """
        return self._repository.get_processes()

    def get_levels(self) -> List[LevelInfo]:
        """
        Get all production levels.

        Returns:
            List of LevelInfo objects
            
        Example:
            >>> levels = api.analytics.get_levels()
            >>> for lvl in levels:
            ...     print(f"{lvl.level_id}: {lvl.level_name}")
            1: PCBA
            2: Box Build
        """
        return self._repository.get_levels()

    def get_product_groups(self) -> List[ProductGroup]:
        """
        Get all product groups.

        Returns:
            List of ProductGroup objects
            
        Example:
            >>> groups = api.analytics.get_product_groups()
            >>> for g in groups:
            ...     print(f"{g.product_group_id}: {g.product_group_name}")
            1: Electronics
            2: Sensors
        """
        return self._repository.get_product_groups()

    # =========================================================================
    # Yield Statistics
    # =========================================================================

    def get_dynamic_yield(
        self, filter_data: Union[WATSFilter, Dict[str, Any]]
    ) -> List[YieldData]:
        """
        Get dynamic yield statistics by custom dimensions (PREVIEW).

        Supported dimensions: part_number, product_name, station_name, location,
        purpose, revision, test_operation, process_code, sw_filename, sw_version,
        product_group, level, period, batch_number, operator, fixture_id, etc.

        Args:
            filter_data: WATSFilter with dimensions and filters

        Returns:
            List of YieldData objects
            
        Example:
            >>> from pywats import WATSFilter
            >>> filter_obj = WATSFilter(
            ...     part_number="WIDGET-001",
            ...     period_count=30,
            ...     dimensions="partNumber;period"
            ... )
            >>> yield_data = api.analytics.get_dynamic_yield(filter_obj)
            >>> for y in yield_data:
            ...     print(f"{y.part_number} ({y.period}): FPY={y.fpy}%")
        """
        return self._repository.get_dynamic_yield(filter_data)

    def get_dynamic_repair(
        self, filter_data: Union[WATSFilter, Dict[str, Any]]
    ) -> List[RepairStatistics]:
        """
        Get dynamic repair statistics by custom dimensions (PREVIEW).

        Args:
            filter_data: WATSFilter with dimensions and filters

        Returns:
            List of RepairStatistics objects with repair counts and rates
            
        Example:
            >>> from pywats import WATSFilter
            >>> filter_obj = WATSFilter(
            ...     part_number="WIDGET-001",
            ...     period_count=30,
            ...     dimensions="partNumber;period"
            ... )
            >>> repairs = api.analytics.get_dynamic_repair(filter_obj)
            >>> for r in repairs:
            ...     print(f"{r.part_number}: {r.repair_count} repairs ({r.repair_rate}%)")
        """
        return self._repository.get_dynamic_repair(filter_data)

    def get_volume_yield(
        self,
        filter_data: Optional[WATSFilter] = None,
        product_group: Optional[str] = None,
        level: Optional[str] = None,
    ) -> List[YieldData]:
        """
        Get volume/yield statistics.

        Args:
            filter_data: Optional WATSFilter for POST request
            product_group: Optional product group filter (for GET)
            level: Optional level filter (for GET)

        Returns:
            List of YieldData objects
            
        Example:
            >>> # Simple GET request with filters
            >>> yield_data = api.analytics.get_volume_yield(
            ...     product_group="Electronics",
            ...     level="PCBA"
            ... )
            >>> for y in yield_data:
            ...     print(f"{y.part_number}: {y.unit_count} units, FPY={y.fpy}%")
        """
        return self._repository.get_volume_yield(
            filter_data=filter_data, product_group=product_group, level=level
        )

    def get_worst_yield(
        self,
        filter_data: Optional[WATSFilter] = None,
        product_group: Optional[str] = None,
        level: Optional[str] = None,
    ) -> List[YieldData]:
        """
        Get worst yield statistics (products with lowest yield).

        Args:
            filter_data: Optional WATSFilter for POST request
            product_group: Optional product group filter (for GET)
            level: Optional level filter (for GET)

        Returns:
            List of YieldData objects sorted by worst yield first
            
        Example:
            >>> # Find products with worst yield in PCBA level
            >>> worst = api.analytics.get_worst_yield(level="PCBA")
            >>> for y in worst[:5]:  # Top 5 worst
            ...     print(f"{y.part_number}: FPY={y.fpy}%")
        """
        return self._repository.get_worst_yield(
            filter_data=filter_data, product_group=product_group, level=level
        )

    def get_worst_yield_by_product_group(
        self, filter_data: WATSFilter
    ) -> List[YieldData]:
        """
        Get worst yield statistics grouped by product group.

        Args:
            filter_data: WATSFilter with parameters

        Returns:
            List of YieldData objects grouped by product group, sorted by worst yield
            
        Example:
            >>> from pywats import WATSFilter
            >>> filter_obj = WATSFilter(period_count=30)
            >>> worst = api.analytics.get_worst_yield_by_product_group(filter_obj)
            >>> for y in worst:
            ...     print(f"{y.product_group}: FPY={y.fpy}%")
        """
        return self._repository.get_worst_yield_by_product_group(filter_data)

    # =========================================================================
    # High Volume Analysis
    # =========================================================================

    def get_high_volume(
        self,
        filter_data: Optional[WATSFilter] = None,
        product_group: Optional[str] = None,
        level: Optional[str] = None,
    ) -> List[YieldData]:
        """
        Get high volume product list (products with most units tested).

        Args:
            filter_data: Optional WATSFilter for POST request
            product_group: Optional product group filter (for GET)
            level: Optional level filter (for GET)

        Returns:
            List of YieldData objects sorted by highest volume first
            
        Example:
            >>> # Get highest volume products in Electronics group
            >>> high_vol = api.analytics.get_high_volume(product_group="Electronics")
            >>> for y in high_vol[:5]:  # Top 5 by volume
            ...     print(f"{y.part_number}: {y.unit_count} units")
        """
        return self._repository.get_high_volume(
            filter_data=filter_data, product_group=product_group, level=level
        )

    def get_high_volume_by_product_group(
        self, filter_data: WATSFilter
    ) -> List[YieldData]:
        """
        Get yield statistics grouped by product group, sorted by volume.

        Args:
            filter_data: WATSFilter with parameters

        Returns:
            List of YieldData objects grouped by product group, sorted by volume
            
        Example:
            >>> from pywats import WATSFilter
            >>> filter_obj = WATSFilter(period_count=30)
            >>> by_group = api.analytics.get_high_volume_by_product_group(filter_obj)
            >>> for y in by_group:
            ...     print(f"{y.product_group}: {y.unit_count} units, FPY={y.fpy}%")
        """
        return self._repository.get_high_volume_by_product_group(filter_data)

    # =========================================================================
    # Failure Analysis
    # =========================================================================

    def get_top_failed(
        self,
        filter_data: Optional[WATSFilter] = None,
        *,
        product_group: Optional[str] = None,
        level: Optional[str] = None,
        part_number: Optional[str] = None,
        revision: Optional[str] = None,
        top_count: Optional[int] = None,
    ) -> List[TopFailedStep]:
        """
        Get top failed test steps.

        Can be called with a WATSFilter (uses POST) or with explicit parameters (uses GET).

        Args:
            filter_data: Optional WATSFilter for POST request (takes precedence)
            product_group: Filter by product group (GET only)
            level: Filter by production level (GET only)
            part_number: Filter by part number (GET only)
            revision: Filter by revision (GET only)
            top_count: Maximum number of results (GET only)

        Returns:
            List of TopFailedStep objects with failure counts and rates
            
        Example:
            >>> # Simple GET request
            >>> failures = api.analytics.get_top_failed(
            ...     part_number="WIDGET-001",
            ...     top_count=10
            ... )
            >>> for f in failures:
            ...     print(f"{f.step_name}: {f.fail_count} failures ({f.fail_rate}%)")
            
            >>> # Or with WATSFilter for more control
            >>> from pywats import WATSFilter
            >>> filter_obj = WATSFilter(part_number="WIDGET-001", top_count=10)
            >>> failures = api.analytics.get_top_failed(filter_obj)
        """
        return self._repository.get_top_failed(
            filter_data,
            product_group=product_group,
            level=level,
            part_number=part_number,
            revision=revision,
            top_count=top_count,
        )

    def get_test_step_analysis(
        self, filter_data: Union[WATSFilter, Dict[str, Any]]
    ) -> List[StepAnalysisRow]:
        """
        Get test step analysis data (PREVIEW).

        Args:
            filter_data: WATSFilter with analysis parameters including:
                - part_number: Product part number (required)
                - test_operation: Test operation (required)
                - max_count: Maximum number of results
                - date_from: Start date

        Returns:
            List of StepAnalysisRow rows with step statistics
            
        Example:
            >>> from pywats import WATSFilter
            >>> filter_obj = WATSFilter(
            ...     part_number="WIDGET-001",
            ...     test_operation="100",
            ...     max_count=1000
            ... )
            >>> analysis = api.analytics.get_test_step_analysis(filter_obj)
            >>> for row in analysis:
            ...     print(f"{row.step_name}: {row.step_count} runs, {row.step_failed_count} failures")
        """
        return self._repository.get_test_step_analysis(filter_data)

    def get_test_step_analysis_for_operation(
        self,
        part_number: str,
        test_operation: str,
        *,
        revision: Optional[str] = None,
        days: int = 30,
        run: int = 1,
        max_count: int = 10000,
    ) -> List[StepAnalysisRow]:
        """Convenience wrapper for TestStepAnalysis.

        A simplified interface that automatically creates the filter object
        with sensible defaults for common use cases.

        Args:
            part_number: Product part number (required).
            test_operation: Test operation name (required).
            revision: Product revision (optional).
            days: Number of days to look back from now (default: 30).
            run: Run number to analyze (default: 1 for first run).
            max_count: Maximum number of results (default: 10000).

        Returns:
            List[StepAnalysisRow]: Typed step analysis results.

        Raises:
            ValueError: If part_number or test_operation is empty.

        Example:
            >>> # Simple call with just required parameters
            >>> analysis = api.analytics.get_test_step_analysis_for_operation(
            ...     part_number="PCBA-001",
            ...     test_operation="FCT"
            ... )
            >>> for row in analysis:
            ...     print(f"{row.step_name}: {row.step_count} tests")

            >>> # With optional parameters
            >>> analysis = api.analytics.get_test_step_analysis_for_operation(
            ...     part_number="PCBA-001",
            ...     test_operation="FCT",
            ...     revision="A",
            ...     days=7,
            ...     max_count=500
            ... )
        """
        if not part_number:
            raise ValueError("part_number is required")
        if not test_operation:
            raise ValueError("test_operation is required")

        filter_data = WATSFilter(
            part_number=part_number,
            test_operation=test_operation,
            revision=revision,
            max_count=max_count,
            date_from=datetime.now() - timedelta(days=days),
            run=run,
        )
        return self.get_test_step_analysis(filter_data)

    # =========================================================================
    # Repair History
    # =========================================================================

    def get_related_repair_history(
        self, part_number: str, revision: str
    ) -> List[RepairHistoryRecord]:
        """
        Get list of repaired failures related to the part number and revision.

        Args:
            part_number: Product part number
            revision: Product revision

        Returns:
            List of RepairHistoryRecord objects with repair details
            
        Example:
            >>> repairs = api.analytics.get_related_repair_history(
            ...     part_number="WIDGET-001",
            ...     revision="A"
            ... )
            >>> for r in repairs:
            ...     print(f"SN {r.serial_number}: {r.fail_step_name} -> {r.repair_code}")
        """
        return self._repository.get_related_repair_history(
            part_number, revision
        )

    # =========================================================================
    # Measurement Analysis
    # =========================================================================

    def get_aggregated_measurements(
        self, 
        filter_data: WATSFilter,
        *,
        measurement_paths: Optional[str] = None,
    ) -> List[AggregatedMeasurement]:
        """
        Get aggregated measurement statistics.

        IMPORTANT: This API requires partNumber and testOperation filters.
        Without them, it returns measurements from the last 7 days of most 
        failed steps, which can cause timeouts.

        Args:
            filter_data: WATSFilter with measurement filters.
                REQUIRED: part_number to avoid timeout.
            measurement_paths: Measurement path(s) as query parameter.
                Format: "Step Group¶Step Name¶¶MeasurementName"
                Can use "/" which will be converted to "¶"
                Multiple paths separated by semicolon (;)

        Returns:
            List of AggregatedMeasurement objects with statistics (min, max, avg, cpk, etc.)
            
        Example:
            >>> from pywats import WATSFilter
            >>> filter_obj = WATSFilter(part_number="WIDGET-001")
            >>> measurements = api.analytics.get_aggregated_measurements(
            ...     filter_obj,
            ...     measurement_paths="Main/Voltage Test/Output Voltage"
            ... )
            >>> for m in measurements:
            ...     print(f"{m.step_name}: avg={m.avg}, cpk={m.cpk}")
        """
        return self._repository.get_aggregated_measurements(
            filter_data, 
            measurement_paths=measurement_paths
        )

    def get_measurements(
        self, 
        filter_data: WATSFilter,
        *,
        measurement_paths: Optional[str] = None,
    ) -> List[MeasurementData]:
        """
        Get individual measurement data points (PREVIEW).

        IMPORTANT: This API requires partNumber and testOperation filters.
        Without them, it returns measurements from the last 7 days of most 
        failed steps, which can cause timeouts.

        Args:
            filter_data: WATSFilter with measurement filters.
                REQUIRED: part_number to avoid timeout.
            measurement_paths: Measurement path(s) as query parameter.
                Format: "Step Group¶Step Name¶¶MeasurementName"
                Can use "/" which will be converted to "¶"
                Multiple paths separated by semicolon (;)

        Returns:
            List of MeasurementData objects with individual measurement values
            
        Example:
            >>> from pywats import WATSFilter
            >>> filter_obj = WATSFilter(part_number="WIDGET-001", top_count=100)
            >>> data = api.analytics.get_measurements(
            ...     filter_obj,
            ...     measurement_paths="Main/Voltage Test/Output Voltage"
            ... )
            >>> for m in data:
            ...     print(f"SN {m.serial_number}: {m.value}")
        """
        return self._repository.get_measurements(
            filter_data,
            measurement_paths=measurement_paths
        )

    # =========================================================================
    # OEE Analysis
    # =========================================================================

    def get_oee_analysis(self, filter_data: WATSFilter) -> Optional[OeeAnalysisResult]:
        """
        Get Overall Equipment Effectiveness analysis.

        OEE = Availability × Performance × Quality

        Supported filters: product_group, level, part_number, revision,
        station_name, test_operation, status, sw_filename, sw_version,
        socket, date_from, date_to

        Args:
            filter_data: WATSFilter with OEE parameters

        Returns:
            OeeAnalysisResult object with OEE metrics, or None if no data
            
        Example:
            >>> from pywats import WATSFilter
            >>> from datetime import datetime, timedelta
            >>> filter_obj = WATSFilter(
            ...     station_name="Line1-EOL",
            ...     date_from=datetime.now() - timedelta(days=7),
            ...     date_to=datetime.now()
            ... )
            >>> oee = api.analytics.get_oee_analysis(filter_obj)
            >>> if oee:
            ...     print(f"OEE: {oee.oee}%")
            ...     print(f"  Availability: {oee.availability}%")
            ...     print(f"  Performance: {oee.performance}%")
            ...     print(f"  Quality: {oee.quality}%")
        """
        return self._repository.get_oee_analysis(filter_data)

    # =========================================================================
    # Serial Number History
    # =========================================================================

    def get_serial_number_history(
        self, filter_data: WATSFilter
    ) -> List[ReportHeader]:
        """
        Get test history for a serial number.

        Supported filters: product_group, level, serial_number, part_number,
        batch_number, misc_value

        Args:
            filter_data: WATSFilter with serial number and other filters

        Returns:
            List of ReportHeader objects
            
        Example:
            >>> from pywats import WATSFilter
            >>> filter_obj = WATSFilter(serial_number="SN12345")
            >>> history = api.analytics.get_serial_number_history(filter_obj)
            >>> for report in history:
            ...     print(f"{report.start}: {report.status} - {report.part_number}")
        """
        return self._repository.get_serial_number_history(filter_data)

    # =========================================================================
    # UUT/UUR Reports
    # =========================================================================

    def get_uut_reports(
        self,
        filter_data: Optional[WATSFilter] = None,
        *,
        product_group: Optional[str] = None,
        level: Optional[str] = None,
        part_number: Optional[str] = None,
        revision: Optional[str] = None,
        serial_number: Optional[str] = None,
        status: Optional[str] = None,
        top_count: Optional[int] = None,
    ) -> List[ReportHeader]:
        """
        Get UUT report headers (like Test Reports in Reporting).

        Can be called with a WATSFilter (uses POST) or with explicit parameters (uses GET).
        By default the 1000 newest reports that match the filter are returned.

        Note: This API is not suitable for workflow or production management,
        use the Production module instead.

        Args:
            filter_data: Optional WATSFilter for POST request (takes precedence)
            product_group: Filter by product group (GET only)
            level: Filter by production level (GET only)
            part_number: Filter by part number (GET only)
            revision: Filter by revision (GET only)
            serial_number: Filter by serial number (GET only)
            status: Filter by status: 'Passed', 'Failed', 'Error' (GET only)
            top_count: Maximum number of results, default 1000 (GET only)

        Returns:
            List of ReportHeader objects
            
        Example:
            >>> # Simple query for recent reports
            >>> reports = api.analytics.get_uut_reports(
            ...     part_number="WIDGET-001",
            ...     status="Failed",
            ...     top_count=100
            ... )
            >>> for r in reports:
            ...     print(f"{r.serial_number}: {r.status} at {r.start}")
        """
        return self._repository.get_uut_reports(
            filter_data,
            product_group=product_group,
            level=level,
            part_number=part_number,
            revision=revision,
            serial_number=serial_number,
            status=status,
            top_count=top_count,
        )

    def get_uur_reports(self, filter_data: WATSFilter) -> List[ReportHeader]:
        """
        Get UUR report headers (like Repair Reports in Reporting).

        By default the 1000 newest reports that match the filter are returned.
        Use top_count filter to change this.

        Note: This API is not suitable for workflow or production management,
        use the Production module instead.

        Args:
            filter_data: WATSFilter with filter parameters

        Returns:
            List of ReportHeader objects
            
        Example:
            >>> from pywats import WATSFilter
            >>> filter_obj = WATSFilter(
            ...     part_number="WIDGET-001",
            ...     top_count=50
            ... )
            >>> repairs = api.analytics.get_uur_reports(filter_obj)
            >>> for r in repairs:
            ...     print(f"{r.serial_number}: repaired at {r.start}")
        """
        return self._repository.get_uur_reports(filter_data)

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def get_yield_summary(
        self,
        part_number: str,
        revision: Optional[str] = None,
        days: int = 30,
    ) -> List[YieldData]:
        """
        Get yield summary for a product over a time period.
        
        Convenience wrapper that creates a WATSFilter internally.

        Args:
            part_number: Product part number
            revision: Optional product revision
            days: Number of days to include (default: 30)

        Returns:
            List of YieldData objects
            
        Example:
            >>> # Get 30-day yield summary for a product
            >>> summary = api.analytics.get_yield_summary(
            ...     part_number="WIDGET-001",
            ...     days=30
            ... )
            >>> for y in summary:
            ...     print(f"{y.period}: FPY={y.fpy}%")
        """
        filter_data = WATSFilter(
            part_number=part_number,
            revision=revision,
            period_count=days,
            dimensions="partNumber;period",
        )
        return self.get_dynamic_yield(filter_data)

    def get_station_yield(
        self, station_name: str, days: int = 7
    ) -> List[YieldData]:
        """
        Get yield statistics for a specific test station.
        
        Convenience wrapper that creates a WATSFilter internally.

        Args:
            station_name: Test station name
            days: Number of days to include (default: 7)

        Returns:
            List of YieldData objects
            
        Example:
            >>> # Get 7-day yield for a station
            >>> station_yield = api.analytics.get_station_yield(
            ...     station_name="Line1-EOL",
            ...     days=7
            ... )
            >>> for y in station_yield:
            ...     print(f"{y.period}: {y.unit_count} units, FPY={y.fpy}%")
        """
        filter_data = WATSFilter(
            station_name=station_name,
            period_count=days,
            dimensions="stationName;period",
        )
        return self.get_dynamic_yield(filter_data)
