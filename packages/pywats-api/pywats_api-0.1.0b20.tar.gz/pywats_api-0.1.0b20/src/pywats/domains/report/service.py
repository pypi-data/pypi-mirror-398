"""Report service - business logic layer.

All business operations for test reports (UUT/UUR).
"""
from typing import Optional, List, Dict, Any, overload, Callable, Union, TYPE_CHECKING
from datetime import datetime, timedelta
from uuid import uuid4, UUID
import logging

from .repository import ReportRepository

logger = logging.getLogger(__name__)
from .models import WATSFilter, ReportHeader
from .enums import DateGrouping
from .report_models import UUTReport, UURReport
from .report_models.uut.uut_info import UUTInfo
from .report_models.uur.uur_info import UURInfo

if TYPE_CHECKING:
    from pywats.core.station import Station


class ReportService:
    """
    Report business logic layer.

    Provides high-level operations for working with WATS test reports.
    
    Supports station configuration through:
    - Explicit Station parameter on report creation methods
    - Legacy station_name/location/purpose parameters
    - Default station from pyWATS API instance
    """

    def __init__(
        self, 
        repository: ReportRepository,
        station_provider: Optional[Callable[[], Optional["Station"]]] = None
    ):
        """
        Initialize with ReportRepository.

        Args:
            repository: ReportRepository instance for data access
            station_provider: Optional callable that returns the current Station
        """
        self._repository = repository
        self._station_provider = station_provider
    
    def _resolve_station(
        self,
        station: Optional["Station"] = None,
        station_name: Optional[str] = None,
        location: Optional[str] = None,
        purpose: Optional[str] = None
    ) -> tuple:
        """
        Resolve station information from various sources.

        Priority:
        1. Explicit Station object
        2. Legacy station_name/location/purpose parameters
        3. Default station from API (via station_provider)
        4. Fallback to "Unknown" values

        Args:
            station: Explicit Station object
            station_name: Legacy station name parameter
            location: Legacy location parameter
            purpose: Legacy purpose parameter
            
        Returns:
            Tuple of (station_name, location, purpose)

        The resolved values populate WATS' `stationName`, `location`, and `purpose` dimensions so
        analytics, root cause searches, and station-specific quotas remain consistent regardless of
        whether the caller passes a Station object or legacy strings.
        """
        # Priority 1: Explicit Station object
        if station is not None:
            return (station.name, station.location, station.purpose)
        
        # Priority 2: Legacy parameters (if station_name is provided)
        if station_name:
            return (
                station_name,
                location or "",
                purpose or "Development"
            )
        
        # Priority 3: Default station from API
        if self._station_provider:
            default_station = self._station_provider()
            if default_station:
                return (
                    default_station.name,
                    location or default_station.location,
                    purpose or default_station.purpose
                )
        
        # Priority 4: Fallback
        return (
            "Unknown",
            location or "Unknown",
            purpose or "Development"
        )

    # =========================================================================
    # Report Factory Methods
    # =========================================================================

    def create_uut_report(
        self,
        operator: str,
        part_number: str,
        revision: str,
        serial_number: str,
        operation_type: int,
        station: Optional["Station"] = None,
        station_name: Optional[str] = None,
        location: Optional[str] = None,
        purpose: Optional[str] = None
    ) -> UUTReport:
        """
        Create a new UUT (Unit Under Test) report.

        Args:
            operator: Name of the test operator
            part_number: Part number of the unit being tested
            revision: Revision of the unit
            serial_number: Serial number of the unit
            operation_type: Process code/operation type
            station: Station object with name, location, and purpose
            station_name: Optional station name (legacy, use station instead)
            location: Optional location (legacy, use station instead)
            purpose: Optional purpose (legacy, use station instead)

        Returns:
            A new UUTReport object ready for adding steps and submission
        
        Note:
            Station information priority:
            1. Explicit station parameter
            2. Legacy station_name/location/purpose parameters
            3. API's default station (from pyWATS instance)
            4. Fallback to "Unknown" values

            The `operation_type` argument maps directly to WATS' processCode lookup (e.g. 100 = end-of-line test, 200 = calibration).
            The same code flows into the penultimate event so dashboards and failure tracking can join the test log with the correct operation context.
        
        See Also:
            For a fluent interface with comprehensive factory methods:
                from pywats.tools.test_uut import TestUUT
                report = TestUUT(pn, sn, rev, operator, process_code).get_root()
        """
        # Resolve station information
        resolved_station_name, resolved_location, resolved_purpose = self._resolve_station(
            station, station_name, location, purpose
        )
        
        uut_info = UUTInfo(
            operator=operator
        )

        report = UUTReport(
            id=uuid4(),
            type="T",
            pn=part_number,
            sn=serial_number,
            rev=revision,
            process_code=operation_type,
            station_name=resolved_station_name,
            location=resolved_location,
            purpose=resolved_purpose,
            start=datetime.now().astimezone(),
            info=uut_info
        )

        return report

    # =========================================================================
    # UUR Factory Methods - Multiple creation patterns
    # =========================================================================

    @overload
    def create_uur_report(
        self,
        uut_or_guid_or_pn: UUTReport,
        test_operation_code_pos: None = None,
        *,
        repair_process_code: int = 500,
        operator: Optional[str] = None,
        station: Optional["Station"] = None,
        station_name: Optional[str] = None,
        location: Optional[str] = None,
        comment: Optional[str] = None
    ) -> UURReport: ...

    @overload
    def create_uur_report(
        self,
        uut_or_guid_or_pn: UUID,
        test_operation_code_pos: None = None,
        *,
        part_number: str,
        serial_number: str,
        test_operation_code: int,
        repair_process_code: int = 500,
        revision: str = "A",
        operator: Optional[str] = None,
        station: Optional["Station"] = None,
        station_name: Optional[str] = None,
        location: Optional[str] = None,
        comment: Optional[str] = None
    ) -> UURReport: ...

    @overload
    def create_uur_report(
        self,
        uut_or_guid_or_pn: str,
        test_operation_code_pos: int,
        *,
        serial_number: str,
        repair_process_code: int = 500,
        revision: str = "A",
        operator: Optional[str] = None,
        station: Optional["Station"] = None,
        station_name: Optional[str] = None,
        location: Optional[str] = None,
        comment: Optional[str] = None
    ) -> UURReport: ...

    def create_uur_report(
        self,
        uut_or_guid_or_pn: Union[UUTReport, UUID, str, None] = None,
        test_operation_code_pos: Optional[int] = None,
        *,
        # Common optional parameters
        operator: Optional[str] = None,
        part_number: Optional[str] = None,
        serial_number: Optional[str] = None,
        revision: str = "A",
        # Dual process codes (key UUR architectural feature)
        repair_process_code: int = 500,
        test_operation_code: Optional[int] = None,
        station: Optional["Station"] = None,
        station_name: Optional[str] = None,
        location: Optional[str] = None,
        purpose: Optional[str] = None,
        comment: Optional[str] = None,
        # Legacy parameters (for backward compatibility)
        process_code: Optional[int] = None,
        operation_type: Optional[int] = None,
    ) -> UURReport:
        """
        Create a new UUR (Unit Under Repair) report.

        UUR reports require TWO process codes:
        
        1. **repair_process_code**: The type of repair operation (default: 500)
           - Must be a valid repair operation (isRepairOperation=true)
           - Common values: 500 (Repair), 510 (RMA Repair)
           - This becomes the top-level report process_code
        
        2. **test_operation_code**: The original test operation that failed
           - Must be a valid test operation (isTestOperation=true)  
           - Common values: 100 (End of line test), 50 (PCBA test), etc.
           - Automatically extracted from UUTReport if provided
           - Stored in uur_info.test_operation_code

        Supports multiple calling patterns:

        1. From UUTReport object (recommended):
           ```python
           uur = api.report.create_uur_report(
               failed_uut,
               repair_process_code=500,
               operator="RepairTech"
           )
           ```

        2. From UUT GUID (when you have the ID but not the full report):
           ```python
           uur = api.report.create_uur_report(
               uut_guid,
               part_number="PN-123",
               serial_number="SN-001",
               test_operation_code=100,
               repair_process_code=500
           )
           ```

        3. From part number and test operation code:
           ```python
           uur = api.report.create_uur_report(
               "PN-123", 100,  # part_number, test_operation_code
               serial_number="SN-001",
               repair_process_code=500
           )
           ```

        Args:
            uut_or_guid_or_pn: UUTReport object, UUID of referenced UUT, or part number
            test_operation_code_pos: Test operation code (positional, for pattern 3)
            operator: Name of the repair operator
            part_number: Part number (when not using UUTReport)
            serial_number: Serial number (when not using UUTReport)
            revision: Revision of the unit (default "A")
            repair_process_code: Repair operation type (default 500=Repair)
            test_operation_code: Original test operation that failed
            station_name: Optional station name
            location: Optional location  
            purpose: Optional purpose (default "Repair")
            comment: Optional comment for the repair
            process_code: Legacy - use test_operation_code instead
            operation_type: Legacy - use test_operation_code instead

        Returns:
            A new UURReport object ready for adding repair info and submission
        
        Domain Notes:
            - WATS requires the top-level `processCode` to describe the repair operation (500, 510, etc.). This is exposed here through `repair_process_code`.
            - The original test operation that failed is tracked separately via `test_operation_code` (and later stored in `uurInfo.test_operation_code`) so fail code navigation remains tied to the correct test step.
        """
        # Resolve parameters based on calling pattern
        ref_uut_guid: Optional[UUID] = None
        pn: str = ""
        sn: str = ""
        rev: str = revision
        test_op_code: Optional[int] = None

        # Pattern 1: UUTReport object
        if isinstance(uut_or_guid_or_pn, UUTReport):
            uut = uut_or_guid_or_pn
            ref_uut_guid = uut.id
            pn = uut.pn
            sn = uut.sn
            rev = uut.rev or revision
            # Extract test operation code from the UUT
            test_op_code = test_operation_code or uut.process_code
            # Use UUT's station/location as defaults if not specified
            station_name = station_name or uut.station_name
            location = location or uut.location

        # Pattern 2: UUID
        elif isinstance(uut_or_guid_or_pn, UUID):
            ref_uut_guid = uut_or_guid_or_pn
            if not part_number:
                raise ValueError("part_number is required when creating UUR from UUID")
            if not serial_number:
                raise ValueError("serial_number is required when creating UUR from UUID")
            pn = part_number
            sn = serial_number
            rev = revision
            # Resolve test operation code from various sources (use 'is not None' to allow 0)
            test_op_code = (
                test_operation_code if test_operation_code is not None else
                test_operation_code_pos if test_operation_code_pos is not None else
                process_code if process_code is not None else
                operation_type
            )
            if test_op_code is None:
                raise ValueError("test_operation_code is required when creating UUR from UUID")

        # Pattern 3: part_number string with test_operation_code
        elif isinstance(uut_or_guid_or_pn, str):
            pn = uut_or_guid_or_pn
            # Resolve test operation code (use 'is not None' to allow 0)
            test_op_code = (
                test_operation_code_pos if test_operation_code_pos is not None else
                test_operation_code if test_operation_code is not None else
                process_code if process_code is not None else
                operation_type
            )
            if test_op_code is None:
                raise ValueError("test_operation_code is required when creating UUR from part_number")
            if not serial_number:
                raise ValueError("serial_number is required when creating UUR from part_number")
            sn = serial_number
            rev = revision

        # Legacy fallback: use keyword arguments
        else:
            if part_number:
                pn = part_number
            if serial_number:
                sn = serial_number
            test_op_code = test_operation_code or process_code or operation_type

        if not pn:
            raise ValueError("part_number is required")
        if not sn:
            raise ValueError("serial_number is required")

        # Resolve station information
        resolved_station_name, resolved_location, resolved_purpose = self._resolve_station(
            station, station_name, location, purpose
        )
        # Default purpose for UUR is "Repair"
        if resolved_purpose == "Development":
            resolved_purpose = "Repair"

        # Get current timestamp for timing fields
        now = datetime.now().astimezone()

        # Create UURInfo with dual process code architecture
        # Note: API requires processCode, confirmDate, finalizeDate, execTime in uur object
        # refUUT can be null (for standalone repairs without a failed UUT reference)
        uur_info = UURInfo(
            operator=operator or "Unknown",  # Required field from ReportInfo
            ref_uut=ref_uut_guid,  # Can be None for standalone repairs
            comment=comment,
            # Set the test operation code (what failed)
            test_operation_code=test_op_code,
            process_code=test_op_code,  # API requires this in uur object
            # Required timing fields
            confirm_date=now,
            finalize_date=now,
            exec_time=0.0,  # Time spent on repair (seconds)
        )

        # Create report with repair process code at top level
        report = UURReport(
            id=uuid4(),
            type="R",
            pn=pn,
            sn=sn,
            rev=rev,
            process_code=repair_process_code,  # Repair operation (500, 510, etc.)
            station_name=resolved_station_name,
            location=resolved_location,
            purpose=resolved_purpose,
            start=datetime.now().astimezone(),
            uur_info=uur_info
        )
        
        # Copy sub_units from UUT if creating from UUTReport
        if isinstance(uut_or_guid_or_pn, UUTReport):
            uut = uut_or_guid_or_pn
            self._copy_sub_units_to_uur(uut, report)

        return report
    
    def _copy_sub_units_to_uur(self, uut: UUTReport, uur: UURReport) -> None:
        """
        Copy sub_units from UUT to UUR report.
        
        UUR uses extended SubUnits with idx, parentIdx, and failures fields.
        The main unit (idx=0) is already created by UURReport.
        
        Args:
            uut: Source UUT report
            uur: Target UUR report
        
        WATS requires each serialized sub_unit to contain `idx` and `parentIdx` so that
        failure propagation and repair analytics can resolve the correct hierarchy.
        """
        from .report_models.uur.uur_sub_unit import UURSubUnit
        
        if not uut.sub_units:
            return
            
        # Copy each sub_unit from UUT, starting from idx=1 (main is idx=0)
        for i, sub_unit in enumerate(uut.sub_units):
            uur_sub = UURSubUnit.from_sub_unit(
                sub_unit,
                idx=i + 1,  # Start from 1 since 0 is main unit
                parent_idx=0  # Default parent is main unit
            )
            if uur.sub_units is None:
                uur.sub_units = []
            uur.sub_units.append(uur_sub)

    def create_uur_from_uut(
        self,
        uut_report: UUTReport,
        operator: Optional[str] = None,
        comment: Optional[str] = None
    ) -> UURReport:
        """
        Create a UUR report linked to a UUT report.

        This is a convenience method that creates a repair report referencing
        the given UUT report, copying relevant metadata.

        Args:
            uut_report: The UUT report to create repair for
            operator: Operator performing the repair
            comment: Initial comment for the repair

        Returns:
            UURReport linked to the UUT
        """
        return self.create_uur_report(
            uut_report,
            operator=operator,
            comment=comment
        )

    # =========================================================================
    # Query Methods
    # =========================================================================

    def query_uut_headers(
        self,
        filter_data: Optional[Union[WATSFilter, Dict[str, Any]]] = None,
        expand: Optional[List[str]] = None,
        odata_filter: Optional[str] = None,
        top: Optional[int] = None,
        orderby: Optional[str] = None,
    ) -> List[ReportHeader]:
        """
        Query UUT report headers.

        Args:
            filter_data: WATSFilter or filter dict
            expand: Fields to expand (subunits, miscinfo, assets, attachments)
            odata_filter: Raw OData filter string
            top: Maximum results
            orderby: Sort order (e.g., "start desc")

        Returns:
            List of ReportHeader objects
        """
        return self._repository.query_headers(
            "uut", filter_data, expand=expand, 
            odata_filter=odata_filter, top=top, orderby=orderby
        )

    def query_uur_headers(
        self,
        filter_data: Optional[Union[WATSFilter, Dict[str, Any]]] = None,
        expand: Optional[List[str]] = None,
        odata_filter: Optional[str] = None,
        top: Optional[int] = None,
        orderby: Optional[str] = None,
    ) -> List[ReportHeader]:
        """
        Query UUR report headers.

        Args:
            filter_data: WATSFilter or filter dict
            expand: Fields to expand (uurSubUnits, uurMiscInfo, uurAttachments)
            odata_filter: Raw OData filter string
            top: Maximum results
            orderby: Sort order (e.g., "start desc")

        Returns:
            List of ReportHeader objects
        """
        return self._repository.query_headers(
            "uur", filter_data, expand=expand,
            odata_filter=odata_filter, top=top, orderby=orderby
        )

    def query_headers_with_subunits(
        self,
        filter_data: Optional[Union[WATSFilter, Dict[str, Any]]] = None,
        report_type: str = "uut",
        top: Optional[int] = None,
        orderby: Optional[str] = None,
        include_misc_info: bool = False,
        include_assets: bool = False,
    ) -> List[ReportHeader]:
        """
        Query report headers with expanded sub-unit data.

        This is the primary method for sub-unit analysis, automatically
        expanding the subunits (for UUT) or uurSubUnits (for UUR) fields.

        Args:
            filter_data: WATSFilter or filter dict
            report_type: "uut" or "uur"
            top: Maximum results (default 1000, max 10000)
            orderby: Sort order (e.g., "start desc")
            include_misc_info: Also expand misc info
            include_assets: Also expand assets

        Returns:
            List of ReportHeader objects with populated sub_units/uur_sub_units
        """
        # Build expand list based on report type
        if report_type == "uut":
            expand_fields = ["subunits"]
            if include_misc_info:
                expand_fields.append("miscinfo")
            if include_assets:
                expand_fields.append("assets")
        else:
            expand_fields = ["uurSubUnits"]
            if include_misc_info:
                expand_fields.append("uurMiscInfo")

        return self._repository.query_headers(
            report_type, filter_data, expand=expand_fields,
            top=top, orderby=orderby
        )

    def query_headers_by_subunit_part_number(
        self,
        subunit_part_number: str,
        filter_data: Optional[Union[WATSFilter, Dict[str, Any]]] = None,
        report_type: str = "uut",
        top: Optional[int] = None,
    ) -> List[ReportHeader]:
        """
        Query report headers filtering by sub-unit part number.

        Uses OData filter to find parent units containing specific sub-units.

        Args:
            subunit_part_number: Part number of sub-unit to filter by
            filter_data: Additional WATSFilter or filter dict for parent
            report_type: "uut" or "uur"
            top: Maximum results

        Returns:
            List of ReportHeader objects with sub-units expanded
        """
        if report_type == "uut":
            odata_filter = f"subunits/any(s: s/partNumber eq '{subunit_part_number}')"
            expand_fields = ["subunits"]
        else:
            odata_filter = f"uurSubUnits/any(s: s/partNumber eq '{subunit_part_number}')"
            expand_fields = ["uurSubUnits"]

        return self._repository.query_headers(
            report_type, filter_data, expand=expand_fields,
            odata_filter=odata_filter, top=top
        )

    def query_headers_by_subunit_serial(
        self,
        subunit_serial_number: str,
        filter_data: Optional[Union[WATSFilter, Dict[str, Any]]] = None,
        report_type: str = "uut",
        top: Optional[int] = None,
    ) -> List[ReportHeader]:
        """
        Query report headers filtering by sub-unit serial number.

        Args:
            subunit_serial_number: Serial number of sub-unit to filter by
            filter_data: Additional WATSFilter or filter dict for parent
            report_type: "uut" or "uur"
            top: Maximum results

        Returns:
            List of ReportHeader objects with sub-units expanded
        """
        if report_type == "uut":
            odata_filter = f"subunits/any(s: s/serialNumber eq '{subunit_serial_number}')"
            expand_fields = ["subunits"]
        else:
            odata_filter = f"uurSubUnits/any(s: s/serialNumber eq '{subunit_serial_number}')"
            expand_fields = ["uurSubUnits"]

        return self._repository.query_headers(
            report_type, filter_data, expand=expand_fields,
            odata_filter=odata_filter, top=top
        )

    def query_headers_by_misc_info(
        self,
        description: str,
        string_value: str,
        top: Optional[int] = None
    ) -> List[ReportHeader]:
        """
        Query report headers by misc info.

        Args:
            description: Misc info description
            string_value: Misc info string value
            top: Number of records to return

        Returns:
            List of ReportHeader objects
        """
        return self._repository.query_headers_by_misc_info(
            description, string_value, top
        )

    # =========================================================================
    # Query Helpers
    # =========================================================================

    def get_headers_by_serial(
        self,
        serial_number: str,
        report_type: str = "uut",
        top: Optional[int] = None
    ) -> List[ReportHeader]:
        """
        Get report headers by serial number.

        Args:
            serial_number: Serial number to search
            report_type: "uut" or "uur"
            top: Number of records to return

        Returns:
            List of ReportHeader
        """
        filter_data = WATSFilter(serial_number=serial_number, top_count=top)
        return self._repository.query_headers(report_type, filter_data)

    def get_headers_by_part_number(
        self,
        part_number: str,
        report_type: str = "uut",
        top: Optional[int] = None
    ) -> List[ReportHeader]:
        """
        Get report headers by part number.

        Args:
            part_number: Part number to search
            report_type: "uut" or "uur"
            top: Number of records to return

        Returns:
            List of ReportHeader
        """
        filter_data = WATSFilter(part_number=part_number, top_count=top)
        return self._repository.query_headers(report_type, filter_data)

    def get_headers_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        report_type: str = "uut"
    ) -> List[ReportHeader]:
        """
        Get report headers by date range.

        Args:
            start_date: Start date
            end_date: End date
            report_type: "uut" or "uur"

        Returns:
            List of ReportHeader
        """
        filter_data = WATSFilter(date_from=start_date, date_to=end_date)
        return self._repository.query_headers(report_type, filter_data)

    def get_recent_headers(
        self,
        days: int = 7,
        report_type: str = "uut",
        top: Optional[int] = None
    ) -> List[ReportHeader]:
        """
        Get headers from the last N days.

        Args:
            days: Number of days back
            report_type: "uut" or "uur"
            top: Number of records to return

        Returns:
            List of ReportHeader
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        filter_data = WATSFilter(date_from=start_date, date_to=end_date, top_count=top)
        return self._repository.query_headers(report_type, filter_data)

    def get_todays_headers(
        self,
        report_type: str = "uut",
        top: Optional[int] = None
    ) -> List[ReportHeader]:
        """
        Get today's report headers.

        Args:
            report_type: "uut" or "uur"
            top: Number of records to return

        Returns:
            List of ReportHeader
        """
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)
        filter_data = WATSFilter(date_from=today, date_to=tomorrow, top_count=top)
        return self._repository.query_headers(report_type, filter_data)

    # =========================================================================
    # WSJF (JSON Format) Operations
    # =========================================================================

    def get_report(
        self, report_id: str
    ) -> Optional[Union[UUTReport, UURReport]]:
        """
        Get a report in WSJF format.

        Args:
            report_id: Report ID (GUID)

        Returns:
            UUTReport or UURReport, or None
        """
        return self._repository.get_wsjf(report_id)

    def submit_report(
        self, report: Union[UUTReport, UURReport, Dict[str, Any]]
    ) -> Optional[str]:
        """
        Submit a new report.

        Args:
            report: Report to submit (UUTReport, UURReport or dict)

        Returns:
            Report ID if successful, None otherwise
        """
        result = self._repository.post_wsjf(report)
        if result:
            # Extract identifying info for logging
            # Prefer snake_case (part_number, serial_number), fallback to aliases (pn, sn, partNumber, serialNumber)
            if isinstance(report, dict):
                pn = report.get('part_number') or report.get('pn') or report.get('partNumber', 'unknown')
                sn = report.get('serial_number') or report.get('sn') or report.get('serialNumber', 'unknown')
            else:
                pn = getattr(report, 'part_number', None) or getattr(report, 'pn', None) or 'unknown'
                sn = getattr(report, 'serial_number', None) or getattr(report, 'sn', None) or 'unknown'
            logger.info(f"REPORT_SUBMITTED: id={result} (pn={pn}, sn={sn})")
        return result

    def submit(
        self, report: Union[UUTReport, UURReport, Dict[str, Any]]
    ) -> Optional[str]:
        """
        Submit a new report (alias for submit_report).

        Args:
            report: Report to submit (UUTReport, UURReport or dict)

        Returns:
            Report ID if successful, None otherwise
        """
        return self.submit_report(report)

    # =========================================================================
    # WSXF (XML Format) Operations
    # =========================================================================

    def get_report_xml(self, report_id: str) -> Optional[bytes]:
        """
        Get a report as XML (WSXF format).

        Args:
            report_id: Report ID (GUID)

        Returns:
            XML content as bytes or None
        """
        return self._repository.get_wsxf(report_id)

    def submit_report_xml(self, xml_content: str) -> Optional[str]:
        """
        Submit a report in XML format.

        Args:
            xml_content: Report as XML string

        Returns:
            Report ID if successful, None otherwise
        """
        result = self._repository.post_wsxf(xml_content)
        if result:
            logger.info(f"REPORT_SUBMITTED_XML: id={result}")
        return result

    # =========================================================================
    # Attachments
    # =========================================================================

    def get_attachment(
        self,
        attachment_id: Optional[str] = None,
        step_id: Optional[str] = None
    ) -> Optional[bytes]:
        """
        Get attachment content.

        Args:
            attachment_id: Attachment ID
            step_id: Step ID

        Returns:
            Attachment content as bytes or None
        """
        return self._repository.get_attachment(attachment_id, step_id)

    def get_all_attachments(self, report_id: str) -> Optional[bytes]:
        """
        Get all attachments for a report as zip file.

        Args:
            report_id: Report ID

        Returns:
            Zip file content as bytes or None
        """
        return self._repository.get_attachments_as_zip(report_id)

    # =========================================================================
    # Certificate
    # =========================================================================

    def get_certificate(self, report_id: str) -> Optional[bytes]:
        """
        Get certificate for a report.

        Args:
            report_id: Report ID

        Returns:
            Certificate content as bytes or None
        """
        return self._repository.get_certificate(report_id)
