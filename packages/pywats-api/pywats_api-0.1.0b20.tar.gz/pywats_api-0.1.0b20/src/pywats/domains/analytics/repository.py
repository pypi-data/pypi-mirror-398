"""Analytics repository - data access layer.

All API interactions for statistics, KPIs, yield analysis, and dashboard data.
Note: Maps to the WATS /api/App/* endpoints (backend naming).
"""
from typing import Optional, List, Dict, Any, Union, TYPE_CHECKING, cast
import logging

if TYPE_CHECKING:
    from ...core import HttpClient
    from ...core.exceptions import ErrorHandler

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


class AnalyticsRepository:
    """
    Analytics/Statistics data access layer.

    Handles all WATS API interactions for statistics, KPIs, and yield analysis.
    Maps to /api/App/* endpoints on the backend.
    """

    def __init__(
        self, 
        http_client: "HttpClient",
        error_handler: Optional["ErrorHandler"] = None
    ):
        """
        Initialize with HTTP client.

        Args:
            http_client: HttpClient for making HTTP requests
            error_handler: ErrorHandler for response handling (optional for backward compat)
        """
        self._http_client = http_client
        self._error_handler = error_handler

    # =========================================================================
    # System Info
    # =========================================================================

    def get_version(self) -> Optional[str]:
        """
        Get server/api version.

        GET /api/App/Version

        Returns:
            Version string (e.g., "24.1.0") or None
        """
        response = self._http_client.get("/api/App/Version")
        
        if self._error_handler:
            data = self._error_handler.handle_response(
                response, operation="get_version", allow_empty=True
            )
            return str(data) if data else None
        
        # Backward compatibility: original behavior
        if response.is_success and response.data:
            return str(response.data)
        return None

    def get_processes(self) -> List[ProcessInfo]:
        """
        Get processes.

        GET /api/App/Processes

        Returns:
            List of ProcessInfo objects
        """
        response = self._http_client.get("/api/App/Processes")
        
        if self._error_handler:
            data = self._error_handler.handle_response(
                response, operation="get_processes", allow_empty=True
            )
            if data:
                return [ProcessInfo.model_validate(item) for item in data]
            return []
        
        # Backward compatibility
        if response.is_success and response.data:
            return [ProcessInfo.model_validate(item) for item in response.data]
        return []

    def get_levels(self) -> List[LevelInfo]:
        """
        Retrieves all ClientGroups (levels).

        GET /api/App/Levels

        Returns:
            List of LevelInfo objects
        """
        response = self._http_client.get("/api/App/Levels")
        
        if self._error_handler:
            data = self._error_handler.handle_response(
                response, operation="get_levels", allow_empty=True
            )
            if data:
                return [LevelInfo.model_validate(item) for item in data]
            return []
        
        # Backward compatibility
        if response.is_success and response.data:
            return [LevelInfo.model_validate(item) for item in response.data]
        return []

    def get_product_groups(self) -> List[ProductGroup]:
        """
        Retrieves all ProductGroups.

        GET /api/App/ProductGroups

        Returns:
            List of ProductGroup objects
        """
        response = self._http_client.get("/api/App/ProductGroups")
        
        if self._error_handler:
            data = self._error_handler.handle_response(
                response, operation="get_product_groups", allow_empty=True
            )
            if data:
                return [ProductGroup.model_validate(item) for item in data]
            return []
        
        # Backward compatibility
        if response.is_success and response.data:
            return [
                ProductGroup.model_validate(item) for item in response.data
            ]
        return []

    # =========================================================================
    # Yield Statistics
    # =========================================================================

    def get_dynamic_yield(
        self, filter_data: Union[WATSFilter, Dict[str, Any]]
    ) -> List[YieldData]:
        """
        Calculate yield by custom dimensions (PREVIEW).

        POST /api/App/DynamicYield

        Args:
            filter_data: WATSFilter object or dict

        Returns:
            List of YieldData objects
        """
        if isinstance(filter_data, WATSFilter):
            data = filter_data.model_dump(by_alias=True, exclude_none=True)
        else:
            data = filter_data

        # Some WATS servers require `dimensions` in the query string.
        # To be robust across server versions:
        # - If the payload is only `dimensions`, send it as query param + empty JSON body.
        # - If there are other filters, keep `dimensions` in the body and also send it
        #   as a query param.
        params: Optional[Dict[str, Any]] = None
        if isinstance(data, dict) and data.get("dimensions"):
            dimensions = data.get("dimensions")
            params = {"dimensions": dimensions}
            if len(data.keys()) == 1:
                data = {}

        # Always send an object body (not null) for these preview endpoints.
        if not data:
            data = {}

        response = self._http_client.post(
            "/api/App/DynamicYield", data=data, params=params
        )
        if response.is_success and response.data:
            return [YieldData.model_validate(item) for item in response.data]
        return []

    def get_volume_yield(
        self,
        filter_data: Optional[Union[WATSFilter, Dict[str, Any]]] = None,
        product_group: Optional[str] = None,
        level: Optional[str] = None,
    ) -> List[YieldData]:
        """
        Volume/Yield list.

        GET/POST /api/App/VolumeYield

        Args:
            filter_data: WATSFilter object or dict (for POST)
            product_group: Product group filter (for GET)
            level: Level filter (for GET)

        Returns:
            List of YieldData objects
        """
        if filter_data:
            if isinstance(filter_data, WATSFilter):
                data = filter_data.model_dump(by_alias=True, exclude_none=True)
            else:
                data = filter_data
            response = self._http_client.post("/api/App/VolumeYield", data=data)
        else:
            params: Dict[str, Any] = {}
            if product_group:
                params["productGroup"] = product_group
            if level:
                params["level"] = level
            response = self._http_client.get(
                "/api/App/VolumeYield", params=params if params else None
            )
        if response.is_success and response.data:
            return [YieldData.model_validate(item) for item in response.data]
        return []

    def get_high_volume(
        self,
        filter_data: Optional[Union[WATSFilter, Dict[str, Any]]] = None,
        product_group: Optional[str] = None,
        level: Optional[str] = None,
    ) -> List[YieldData]:
        """
        High Volume list.

        GET/POST /api/App/HighVolume

        Args:
            filter_data: WATSFilter object or dict (for POST)
            product_group: Product group filter (for GET)
            level: Level filter (for GET)

        Returns:
            List of YieldData objects
        """
        if filter_data:
            if isinstance(filter_data, WATSFilter):
                data = filter_data.model_dump(by_alias=True, exclude_none=True)
            else:
                data = filter_data
            response = self._http_client.post("/api/App/HighVolume", data=data)
        else:
            params: Dict[str, Any] = {}
            if product_group:
                params["productGroup"] = product_group
            if level:
                params["level"] = level
            response = self._http_client.get(
                "/api/App/HighVolume", params=params if params else None
            )
        if response.is_success and response.data:
            return [YieldData.model_validate(item) for item in response.data]
        return []

    def get_high_volume_by_product_group(
        self, filter_data: Union[WATSFilter, Dict[str, Any]]
    ) -> List[YieldData]:
        """
        Yield by product group sorted by volume.

        POST /api/App/HighVolumeByProductGroup

        Args:
            filter_data: WATSFilter object or dict

        Returns:
            List of YieldData objects
        """
        if isinstance(filter_data, WATSFilter):
            data = filter_data.model_dump(by_alias=True, exclude_none=True)
        else:
            data = filter_data
        response = self._http_client.post(
            "/api/App/HighVolumeByProductGroup", data=data
        )
        if response.is_success and response.data:
            return [YieldData.model_validate(item) for item in response.data]
        return []

    def get_worst_yield(
        self,
        filter_data: Optional[Union[WATSFilter, Dict[str, Any]]] = None,
        product_group: Optional[str] = None,
        level: Optional[str] = None,
    ) -> List[YieldData]:
        """
        Worst Yield list.

        GET/POST /api/App/WorstYield

        Args:
            filter_data: WATSFilter object or dict (for POST)
            product_group: Product group filter (for GET)
            level: Level filter (for GET)

        Returns:
            List of YieldData objects
        """
        if filter_data:
            if isinstance(filter_data, WATSFilter):
                data = filter_data.model_dump(by_alias=True, exclude_none=True)
            else:
                data = filter_data
            response = self._http_client.post("/api/App/WorstYield", data=data)
        else:
            params: Dict[str, Any] = {}
            if product_group:
                params["productGroup"] = product_group
            if level:
                params["level"] = level
            response = self._http_client.get(
                "/api/App/WorstYield", params=params if params else None
            )
        if response.is_success and response.data:
            return [YieldData.model_validate(item) for item in response.data]
        return []

    def get_worst_yield_by_product_group(
        self, filter_data: Union[WATSFilter, Dict[str, Any]]
    ) -> List[YieldData]:
        """
        Yield by product group sorted by lowest yield.

        POST /api/App/WorstYieldByProductGroup

        Args:
            filter_data: WATSFilter object or dict

        Returns:
            List of YieldData objects
        """
        if isinstance(filter_data, WATSFilter):
            data = filter_data.model_dump(by_alias=True, exclude_none=True)
        else:
            data = filter_data
        response = self._http_client.post(
            "/api/App/WorstYieldByProductGroup", data=data
        )
        if response.is_success and response.data:
            return [YieldData.model_validate(item) for item in response.data]
        return []

    # =========================================================================
    # Repair Statistics
    # =========================================================================

    def get_dynamic_repair(
        self, filter_data: Union[WATSFilter, Dict[str, Any]]
    ) -> List[RepairStatistics]:
        """
        Calculate repair statistics by custom dimensions (PREVIEW).

        POST /api/App/DynamicRepair

        Args:
            filter_data: WATSFilter object or dict with filters like:
                - part_number: Filter by product
                - product_group: Filter by product group
                - period_count: Number of periods
                - grouping: Grouping dimension

        Returns:
            List of RepairStatistics objects with repair counts and rates
        """
        if isinstance(filter_data, WATSFilter):
            data = filter_data.model_dump(by_alias=True, exclude_none=True)
        else:
            data = filter_data

        # Some WATS servers require `dimensions` in the query string.
        # To be robust across server versions:
        # - If the payload is only `dimensions`, send it as query param + empty JSON body.
        # - If there are other filters, keep `dimensions` in the body and also send it
        #   as a query param.
        params: Optional[Dict[str, Any]] = None
        if isinstance(data, dict) and data.get("dimensions"):
            dimensions = data.get("dimensions")
            params = {"dimensions": dimensions}
            if len(data.keys()) == 1:
                data = {}

        # Always send an object body (not null) for these preview endpoints.
        if not data:
            data = {}

        response = self._http_client.post(
            "/api/App/DynamicRepair", data=data, params=params
        )
        if response.is_success and response.data:
            items = response.data if isinstance(response.data, list) else [response.data]
            return [RepairStatistics.model_validate(item) for item in items]
        return []

    def get_related_repair_history(
        self, part_number: str, revision: str
    ) -> List[RepairHistoryRecord]:
        """
        Get list of repaired failures related to the part number and revision.

        GET /api/App/RelatedRepairHistory

        Args:
            part_number: Product part number
            revision: Product revision

        Returns:
            List of RepairHistoryRecord objects with repair details
        """
        params: Dict[str, Any] = {
            "partNumber": part_number,
            "revision": revision,
        }
        response = self._http_client.get(
            "/api/App/RelatedRepairHistory", params=params
        )
        if response.is_success and response.data:
            items = response.data if isinstance(response.data, list) else [response.data]
            return [RepairHistoryRecord.model_validate(item) for item in items]
        return []

    # =========================================================================
    # Failure Analysis
    # =========================================================================

    def get_top_failed(
        self,
        filter_data: Optional[Union[WATSFilter, Dict[str, Any]]] = None,
        *,
        product_group: Optional[str] = None,
        level: Optional[str] = None,
        part_number: Optional[str] = None,
        revision: Optional[str] = None,
        top_count: Optional[int] = None,
    ) -> List[TopFailedStep]:
        """
        Get the top failed steps.

        GET/POST /api/App/TopFailed

        Args:
            filter_data: WATSFilter object or dict (for POST)
            product_group: Filter by product group (GET only)
            level: Filter by production level (GET only)
            part_number: Filter by part number (GET only)
            revision: Filter by revision (GET only)
            top_count: Maximum number of results (GET only)

        Returns:
            List of TopFailedStep objects with failure statistics
        """
        if filter_data:
            if isinstance(filter_data, WATSFilter):
                data = filter_data.model_dump(by_alias=True, exclude_none=True)
            else:
                data = filter_data
            response = self._http_client.post("/api/App/TopFailed", data=data)
        else:
            params: Dict[str, Any] = {}
            if product_group:
                params["productGroup"] = product_group
            if level:
                params["level"] = level
            if part_number:
                params["partNumber"] = part_number
            if revision:
                params["revision"] = revision
            if top_count is not None:
                params["topCount"] = top_count
            response = self._http_client.get(
                "/api/App/TopFailed", params=params if params else None
            )
        if response.is_success and response.data:
            items = response.data if isinstance(response.data, list) else [response.data]
            return [TopFailedStep.model_validate(item) for item in items]
        return []

    def get_test_step_analysis(
        self, filter_data: Union[WATSFilter, Dict[str, Any]]
    ) -> List[StepAnalysisRow]:
        """
        Get step and measurement statistics (PREVIEW).

        POST /api/App/TestStepAnalysis

        Args:
            filter_data: WATSFilter object or dict

        Returns:
            List of StepAnalysisRow rows
        """
        if isinstance(filter_data, WATSFilter):
            data = filter_data.model_dump(by_alias=True, exclude_none=True)
        else:
            data = filter_data
        response = self._http_client.post("/api/App/TestStepAnalysis", data=data)
        if response.is_success and response.data:
            raw_items: List[Any]
            if isinstance(response.data, list):
                raw_items = response.data
            else:
                raw_items = [response.data]
            return [StepAnalysisRow.model_validate(item) for item in raw_items]
        return []

    # =========================================================================
    # Measurements
    # =========================================================================

    @staticmethod
    def _normalize_measurement_path(path: str) -> str:
        """
        Convert user-friendly path format to API format.
        
        The API expects paths using paragraph mark (¶) as separator:
        - "MainSequence¶Step Group¶Step Name" for steps
        - "MainSequence¶Step Group¶Step Name¶¶MeasurementName" for multi-numeric
        
        This method converts common formats:
        - "/" separator -> "¶"
        - "::" for measurement name -> "¶¶"
        
        Args:
            path: User-provided path (e.g., "Main/Step/Test" or "Main/Step/Test::Meas1")
            
        Returns:
            API-formatted path with ¶ separators
        """
        if not path:
            return path
        
        # Already in API format
        if "¶" in path:
            return path
        
        # Handle measurement name separator (:: -> ¶¶)
        if "::" in path:
            step_path, measurement_name = path.rsplit("::", 1)
            step_path = step_path.replace("/", "¶")
            return f"{step_path}¶¶{measurement_name}"
        
        # Simple path conversion
        return path.replace("/", "¶")

    def get_measurements(
        self, 
        filter_data: Union[WATSFilter, Dict[str, Any]],
        *,
        measurement_paths: Optional[str] = None,
    ) -> List[MeasurementData]:
        """
        Get numeric measurements by measurement path (PREVIEW).

        POST /api/App/Measurements

        IMPORTANT: This API requires partNumber and testOperation filters.
        Without them, it returns measurements from the last 7 days of most 
        failed steps, which can cause timeouts.

        Args:
            filter_data: WATSFilter object or dict with filters. 
                REQUIRED: part_number and test_operation to avoid timeout.
            measurement_paths: Measurement path(s) as query parameter.
                Format: "Step Group¶Step Name¶¶MeasurementName"
                Multiple paths separated by semicolon (;)
                Can use "/" which will be converted to "¶"

        Returns:
            List of MeasurementData objects with individual measurement values
            
        Example:
            >>> # Get specific measurement with proper filters
            >>> data = analytics.get_measurements(
            ...     WATSFilter(part_number="PROD-001", test_operation="EOL Test"),
            ...     measurement_paths="Main¶Voltage Test¶¶Output"
            ... )
        """
        if isinstance(filter_data, WATSFilter):
            data = filter_data.model_dump(by_alias=True, exclude_none=True)
        else:
            data = dict(filter_data)
        
        # Build query params for measurementPaths
        params: Dict[str, str] = {}
        
        # Check for measurement_path in data (legacy support) and move to query param
        if "measurement_path" in data:
            measurement_paths = measurement_paths or data.pop("measurement_path")
        if "measurementPath" in data:
            measurement_paths = measurement_paths or data.pop("measurementPath")
            
        if measurement_paths:
            params["measurementPaths"] = self._normalize_measurement_path(measurement_paths)
        
        response = self._http_client.post(
            "/api/App/Measurements", 
            data=data,
            params=params if params else None
        )
        if response.is_success and response.data:
            items = response.data if isinstance(response.data, list) else [response.data]
            return [MeasurementData.model_validate(item) for item in items]
        return []

    def get_aggregated_measurements(
        self, 
        filter_data: Union[WATSFilter, Dict[str, Any]],
        *,
        measurement_paths: Optional[str] = None,
    ) -> List[AggregatedMeasurement]:
        """
        Get aggregated numeric measurements by measurement path.

        POST /api/App/AggregatedMeasurements

        IMPORTANT: This API requires partNumber and testOperation filters.
        Without them, it returns measurements from the last 7 days of most 
        failed steps, which can cause timeouts.

        Args:
            filter_data: WATSFilter object or dict with filters.
                REQUIRED: part_number and test_operation to avoid timeout.
            measurement_paths: Measurement path(s) as query parameter.
                Format: "Step Group¶Step Name¶¶MeasurementName"
                Multiple paths separated by semicolon (;)
                Can use "/" which will be converted to "¶"

        Returns:
            List of AggregatedMeasurement objects with statistics (min, max, avg, cpk, etc.)
            
        Example:
            >>> # Get aggregated stats with proper filters
            >>> data = analytics.get_aggregated_measurements(
            ...     WATSFilter(part_number="PROD-001", test_operation="EOL Test"),
            ...     measurement_paths="Main¶Voltage Test¶¶Output"
            ... )
        """
        if isinstance(filter_data, WATSFilter):
            data = filter_data.model_dump(by_alias=True, exclude_none=True)
        else:
            data = dict(filter_data)
        
        # Build query params for measurementPaths
        params: Dict[str, str] = {}
        
        # Check for measurement_path in data (legacy support) and move to query param
        if "measurement_path" in data:
            measurement_paths = measurement_paths or data.pop("measurement_path")
        if "measurementPath" in data:
            measurement_paths = measurement_paths or data.pop("measurementPath")
            
        if measurement_paths:
            params["measurementPaths"] = self._normalize_measurement_path(measurement_paths)
            
        response = self._http_client.post(
            "/api/App/AggregatedMeasurements", 
            data=data,
            params=params if params else None
        )
        if response.is_success and response.data:
            items = response.data if isinstance(response.data, list) else [response.data]
            return [AggregatedMeasurement.model_validate(item) for item in items]
        return []

    # =========================================================================
    # OEE (Overall Equipment Effectiveness)
    # =========================================================================

    def get_oee_analysis(
        self, filter_data: Union[WATSFilter, Dict[str, Any]]
    ) -> Optional[OeeAnalysisResult]:
        """
        Overall Equipment Effectiveness - analysis.

        POST /api/App/OeeAnalysis

        Args:
            filter_data: WATSFilter object or dict with filters like:
                - part_number: Filter by product
                - station_name: Filter by station
                - date_from/date_to: Time range

        Returns:
            OeeAnalysisResult object with OEE metrics (availability, performance, quality)
        """
        if isinstance(filter_data, WATSFilter):
            data = filter_data.model_dump(by_alias=True, exclude_none=True)
        else:
            data = filter_data
        response = self._http_client.post("/api/App/OeeAnalysis", data=data)
        if response.is_success and response.data:
            return OeeAnalysisResult.model_validate(response.data)
        return None

    # =========================================================================
    # Serial Number and Unit History
    # =========================================================================

    def get_serial_number_history(
        self, filter_data: Union[WATSFilter, Dict[str, Any]]
    ) -> List[ReportHeader]:
        """
        Serial Number History.

        POST /api/App/SerialNumberHistory

        Args:
            filter_data: WATSFilter object or dict

        Returns:
            List of ReportHeader objects
        """
        if isinstance(filter_data, WATSFilter):
            data = filter_data.model_dump(by_alias=True, exclude_none=True)
        else:
            data = filter_data
        response = self._http_client.post("/api/App/SerialNumberHistory", data=data)
        if response.is_success and response.data:
            return [
                ReportHeader.model_validate(item) for item in response.data
            ]
        return []

    def get_uut_reports(
        self,
        filter_data: Optional[Union[WATSFilter, Dict[str, Any]]] = None,
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
        Returns UUT report header info.

        GET/POST /api/App/UutReport

        Args:
            filter_data: WATSFilter object or dict (for POST)
            product_group: Filter by product group (GET only)
            level: Filter by production level (GET only)
            part_number: Filter by part number (GET only)
            revision: Filter by revision (GET only)
            serial_number: Filter by serial number (GET only)
            status: Filter by status (GET only)
            top_count: Maximum results, default 1000 (GET only)

        Returns:
            List of ReportHeader objects
        """
        if filter_data:
            if isinstance(filter_data, WATSFilter):
                data = filter_data.model_dump(by_alias=True, exclude_none=True)
            else:
                data = filter_data
            response = self._http_client.post("/api/App/UutReport", data=data)
        else:
            params: Dict[str, Any] = {}
            if product_group:
                params["productGroup"] = product_group
            if level:
                params["level"] = level
            if part_number:
                params["partNumber"] = part_number
            if revision:
                params["revision"] = revision
            if serial_number:
                params["serialNumber"] = serial_number
            if status:
                params["status"] = status
            if top_count is not None:
                params["topCount"] = top_count
            response = self._http_client.get(
                "/api/App/UutReport", params=params if params else None
            )
        if response.is_success and response.data:
            return [
                ReportHeader.model_validate(item) for item in response.data
            ]
        return []

    def get_uur_reports(
        self, filter_data: Union[WATSFilter, Dict[str, Any]]
    ) -> List[ReportHeader]:
        """
        Returns UUR report header info.

        POST /api/App/UurReport

        Args:
            filter_data: WATSFilter object or dict

        Returns:
            List of ReportHeader objects
        """
        if isinstance(filter_data, WATSFilter):
            data = filter_data.model_dump(by_alias=True, exclude_none=True)
        else:
            data = filter_data
        response = self._http_client.post("/api/App/UurReport", data=data)
        if response.is_success and response.data:
            return [
                ReportHeader.model_validate(item) for item in response.data
            ]
        return []
