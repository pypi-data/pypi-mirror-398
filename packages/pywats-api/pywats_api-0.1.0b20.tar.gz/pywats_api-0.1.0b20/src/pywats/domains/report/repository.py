"""Report repository - data access layer.

All API interactions for test reports (UUT/UUR).
"""
from typing import Optional, List, Dict, Any, Union, TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from ...core import HttpClient
    from ...core.exceptions import ErrorHandler

from .models import WATSFilter, ReportHeader
from .report_models import UUTReport, UURReport


class ReportRepository:
    """
    Report data access layer.

    Handles all WATS API interactions for test reports.

    This repository exposes the WATS Report endpoints (`/api/Report/Query/...`, `/api/Report/WSJF`,
    `/api/Report/WSXF`, attachments, and certificates) and keeps the service layer agnostic to HTTP details.
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
            error_handler: Optional ErrorHandler for error handling (default: STRICT mode)
        """
        self._http_client = http_client
        # Import here to avoid circular imports
        from ...core.exceptions import ErrorHandler, ErrorMode
        self._error_handler = error_handler or ErrorHandler(ErrorMode.STRICT)

    # =========================================================================
    # Query Operations
    # =========================================================================

    def query_headers(
        self,
        report_type: str = "uut",
        filter_data: Optional[Union[WATSFilter, Dict[str, Any]]] = None,
        expand: Optional[List[str]] = None,
        odata_filter: Optional[str] = None,
        top: Optional[int] = None,
        orderby: Optional[str] = None,
        skip: Optional[int] = None,
    ) -> List[ReportHeader]:
        """
        Query report headers matching the filter.

        GET /api/Report/Query/Header

        This endpoint supports OData query options for filtering and expanding data.
        
        Args:
            report_type: Report type ("uut" or "uur")
            filter_data: WATSFilter object or dict for basic filtering
            expand: List of fields to expand. Valid values:
                    - "subunits" - UUT sub-units
                    - "miscinfo" - UUT misc info
                    - "assets" - UUT assets
                    - "attachments" - UUT attachments
                    - "uurSubUnits" - UUR sub-units
                    - "uurMiscInfo" - UUR misc info
                    - "uurAttachments" - UUR attachments
            odata_filter: Raw OData $filter string (e.g., "partNumber eq 'XYZ' and status eq 'Failed'")
            top: Maximum number of results ($top)
            orderby: Sort order ($orderby), e.g., "start desc"
            skip: Number of results to skip ($skip)

        Returns:
            List of ReportHeader objects (with expanded data if requested)
            
        Example:
            >>> # Get headers with sub-unit info
            >>> headers = repo.query_headers(
            ...     filter_data=WATSFilter(part_number="ASSY-001"),
            ...     expand=["subunits", "miscinfo"],
            ...     top=100
            ... )
            >>> for h in headers:
            ...     if h.sub_units:
            ...         for su in h.sub_units:
            ...             print(f"  Sub-unit: {su.part_number}/{su.serial_number}")
        """
        params: Dict[str, Any] = {"reportType": report_type}
        if filter_data:
            if isinstance(filter_data, WATSFilter):
                params.update(
                    filter_data.model_dump(by_alias=True, exclude_none=True)
                )
            else:
                params.update(filter_data)
        
        # Build OData query parameters
        if expand:
            params["$expand"] = ",".join(expand)
        if odata_filter:
            params["$filter"] = odata_filter
        if top is not None:
            params["$top"] = top
        if orderby:
            params["$orderby"] = orderby
        if skip is not None:
            params["$skip"] = skip
            
        response = self._http_client.get("/api/Report/Query/Header", params=params)
        if response.is_success and response.data:
            return [
                ReportHeader.model_validate(item)
                for item in response.data
            ]
        return []

    def query_headers_by_misc_info(
        self,
        description: str,
        string_value: str,
        top: Optional[int] = None
    ) -> List[ReportHeader]:
        """
        Get report headers by misc info search.

        GET /api/Report/Query/HeaderByMiscInfo

        Args:
            description: Misc info description
            string_value: Misc info string value
            top: Number of records to return

        Returns:
            List of ReportHeader objects
        """
        params: Dict[str, Any] = {
            "description": description,
            "stringValue": string_value
        }
        if top:
            params["$top"] = top
        response = self._http_client.get(
            "/api/Report/Query/HeaderByMiscInfo", params=params
        )
        if response.is_success and response.data:
            return [
                ReportHeader.model_validate(item)
                for item in response.data
            ]
        return []

    # =========================================================================
    # Report WSJF (JSON Format)
    # =========================================================================

    def post_wsjf(
        self, report: Union[UUTReport, UURReport, Dict[str, Any]]
    ) -> Optional[str]:
        """
        Post a new WSJF report.

        POST /api/Report/WSJF

        Args:
            report: UUTReport, UURReport or report data dict

        Returns:
            Report ID if successful, None otherwise
        
        Notes:
            WSJF (WATS Smart JSON Format) accepts both UUT and UUR payloads. When posting repairs,
            the `uurInfo` block must include `processCode`, `refUUT`, `confirmDate`, `finalizeDate`,
            and `execTime` even if some values are null; this method enforces those fields before shipping.

        Raises:
            ValueError: If the API returns an error with details
        """
        if isinstance(report, (UUTReport, UURReport)):
            data = report.model_dump(
                mode="json", by_alias=True, exclude_none=True
            )
            
            # Special handling for UUR reports: API requires certain fields to be present even if null
            if isinstance(report, UURReport) and 'uurInfo' in data:
                uur_info = data['uurInfo']
                # Ensure these required fields are always present (can be null)
                if 'processCode' not in uur_info:
                    uur_info['processCode'] = report.uur_info.process_code
                if 'refUUT' not in uur_info:
                    uur_info['refUUT'] = report.uur_info.ref_uut
                if 'confirmDate' not in uur_info:
                    uur_info['confirmDate'] = report.uur_info.confirm_date
                if 'finalizeDate' not in uur_info:
                    uur_info['finalizeDate'] = report.uur_info.finalize_date
                if 'execTime' not in uur_info:
                    uur_info['execTime'] = report.uur_info.exec_time
        else:
            data = report
        response = self._http_client.post("/api/Report/WSJF", data=data)
        
        # Check for error responses
        if not response.is_success:
            # Try to get error details from response
            error_msg = "Report submission failed"
            if response.data:
                if isinstance(response.data, dict):
                    # Check for various error message formats
                    error_msg = (
                        response.data.get("message") or
                        response.data.get("Message") or
                        response.data.get("error") or
                        response.data.get("Error") or
                        str(response.data)
                    )
                elif isinstance(response.data, str):
                    error_msg = response.data
                elif isinstance(response.data, list):
                    # Sometimes errors come as a list
                    error_msg = "; ".join(str(e) for e in response.data)
            raise ValueError(f"Report submission failed ({response.status_code}): {error_msg}")
        
        if response.data:
            # Response can be a list with a single result or a dict
            result_data = response.data
            if isinstance(result_data, list) and len(result_data) > 0:
                result_data = result_data[0]
            if isinstance(result_data, dict):
                # Try different key names the API might return
                return (
                    result_data.get("ID") or
                    result_data.get("id") or
                    result_data.get("uuid")
                )
            return str(result_data)
        return None

    def get_wsjf(
        self, report_id: str
    ) -> Optional[Union[UUTReport, UURReport]]:
        """
        Get a report in WSJF format.

        GET /api/Report/Wsjf/{id}

        Args:
            report_id: The report ID (GUID)

        Returns:
            UUTReport or UURReport, or None

        Notes:
            The WATS response includes an `uur` key for repair reports, which signals casting to `UURReport`.
        """
        response = self._http_client.get(f"/api/Report/Wsjf/{report_id}")
        if response.is_success and response.data:
            if response.data.get("uur"):
                return UURReport.model_validate(response.data)
            return UUTReport.model_validate(response.data)
        return None

    # =========================================================================
    # Report WSXF (XML Format)
    # =========================================================================

    def post_wsxf(self, xml_content: str) -> Optional[str]:
        """
        Post a new WSXF (XML) report.

        POST /api/Report/WSXF

        Args:
            xml_content: Report as XML string

        Returns:
            Report ID if successful, None otherwise
        """
        headers = {"Content-Type": "application/xml"}
        response = self._http_client.post(
            "/api/Report/WSXF",
            data=xml_content,
            headers=headers
        )
        if response.is_success and response.data:
            if isinstance(response.data, dict):
                return response.data.get("id")
            return str(response.data)
        return None

    def get_wsxf(self, report_id: str) -> Optional[bytes]:
        """
        Get a report in WSXF (XML) format.

        GET /api/Report/Wsxf/{id}

        Args:
            report_id: The report ID (GUID)

        Returns:
            XML as bytes or None
        """
        response = self._http_client.get(f"/api/Report/Wsxf/{report_id}")
        if response.is_success:
            return response.raw
        return None

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

        GET /api/Report/Attachment

        Args:
            attachment_id: Attachment ID
            step_id: Step ID

        Returns:
            Attachment content as bytes or None
        """
        params: Dict[str, Any] = {}
        if attachment_id:
            params["attachmentId"] = attachment_id
        if step_id:
            params["stepId"] = step_id
        response = self._http_client.get("/api/Report/Attachment", params=params)
        if response.is_success:
            return response.raw
        return None

    def get_attachments_as_zip(self, report_id: str) -> Optional[bytes]:
        """
        Get all attachments for a report as zip.

        GET /api/Report/Attachments/{id}

        Args:
            report_id: Report ID

        Returns:
            Zip file content as bytes or None
        """
        response = self._http_client.get(f"/api/Report/Attachments/{report_id}")
        if response.is_success:
            return response.raw
        return None

    # =========================================================================
    # Certificate
    # =========================================================================

    def get_certificate(self, report_id: str) -> Optional[bytes]:
        """
        Get certificate for a report.

        GET /api/Report/Certificate/{id}

        Args:
            report_id: Report ID

        Returns:
            Certificate content as bytes or None
        """
        response = self._http_client.get(f"/api/Report/Certificate/{report_id}")
        if response.is_success:
            return response.raw
        return None
