"""RootCause repository - data access layer.

All API interactions for the RootCause ticketing system.
"""
from typing import Optional, List, Union, Dict, Any, TYPE_CHECKING
import logging
from uuid import UUID

if TYPE_CHECKING:
    from ...core import HttpClient
    from ...core.exceptions import ErrorHandler

from .models import Ticket, TicketAttachment
from .enums import TicketStatus, TicketView


class RootCauseRepository:
    """
    RootCause (Ticketing) data access layer.

    Handles all WATS API interactions for the ticketing system.
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
    # Ticket Operations
    # =========================================================================

    def get_ticket(self, ticket_id: Union[str, UUID]) -> Optional[Ticket]:
        """
        Get a root cause ticket by ID.

        GET /api/RootCause/Ticket

        Args:
            ticket_id: The ticket ID (GUID)

        Returns:
            Ticket object or None if not found
        """
        response = self._http_client.get(
            "/api/RootCause/Ticket", params={"ticketId": str(ticket_id)}
        )
        if response.is_success and response.data:
            return Ticket.model_validate(response.data)
        return None

    def get_tickets(
        self,
        status: TicketStatus,
        view: TicketView,
        search_string: Optional[str] = None,
    ) -> List[Ticket]:
        """
        Get root cause tickets with a given status.

        GET /api/RootCause/Tickets

        Args:
            status: Ticket status flags (can be combined with |)
            view: View filter (ASSIGNED, FOLLOWING, ALL)
            search_string: Optional search for subject, tags, or tag value

        Returns:
            List of Ticket objects matching the criteria
        """
        params: Dict[str, Any] = {"status": int(status), "view": int(view)}
        if search_string:
            params["searchString"] = search_string

        response = self._http_client.get("/api/RootCause/Tickets", params=params)
        if response.is_success and response.data:
            return [Ticket.model_validate(item) for item in response.data]
        return []

    def create_ticket(self, ticket: Ticket) -> Optional[Ticket]:
        """
        Create a new root cause ticket.

        POST /api/RootCause/Ticket

        Args:
            ticket: Ticket object with the new ticket data

        Returns:
            Created Ticket object with assigned ID and ticket number
        """
        response = self._http_client.post(
            "/api/RootCause/Ticket",
            data=ticket.model_dump(mode="json", by_alias=True, exclude_none=True),
        )
        if response.is_success and response.data:
            return Ticket.model_validate(response.data)
        return None

    def update_ticket(self, ticket: Ticket) -> Optional[Ticket]:
        """
        Update a root cause ticket.

        PUT /api/RootCause/Ticket

        Args:
            ticket: Ticket object with updated data

        Returns:
            Updated Ticket object
        """
        response = self._http_client.put(
            "/api/RootCause/Ticket",
            data=ticket.model_dump(mode="json", by_alias=True, exclude_none=True),
        )
        if response.is_success and response.data:
            return Ticket.model_validate(response.data)
        return None

    def archive_tickets(
        self, ticket_ids: List[Union[str, UUID]]
    ) -> Optional[Ticket]:
        """
        Archive tickets.

        POST /api/RootCause/ArchiveTickets

        Only Solved tickets can be archived.

        Args:
            ticket_ids: List of ticket IDs to archive

        Returns:
            Ticket object or None
        """
        ids = [str(tid) for tid in ticket_ids]
        response = self._http_client.post("/api/RootCause/ArchiveTickets", data=ids)
        if response.is_success and response.data:
            return Ticket.model_validate(response.data)
        return None

    # =========================================================================
    # Attachment Operations
    # =========================================================================

    def get_attachment(
        self,
        attachment_id: Union[str, UUID],
        filename: Optional[str] = None,
    ) -> Optional[bytes]:
        """
        Get root cause attachment content.

        GET /api/RootCause/Attachment

        Args:
            attachment_id: The attachment ID (GUID)
            filename: Optional filename for download

        Returns:
            Attachment content as bytes, or None if not found
        """
        params: Dict[str, str] = {"attachmentId": str(attachment_id)}
        if filename:
            params["fileName"] = filename

        response = self._http_client.get("/api/RootCause/Attachment", params=params)
        if response.is_success:
            return response.raw
        return None

    def upload_attachment(
        self, file_content: bytes, filename: str
    ) -> Optional[UUID]:
        """
        Upload root cause attachment and return attachment ID.

        POST /api/RootCause/Attachment

        Args:
            file_content: The file content as bytes
            filename: The filename for the attachment

        Returns:
            UUID of the created attachment, or None if failed
        """
        files = {"file": (filename, file_content)}
        response = self._http_client.post("/api/RootCause/Attachment", files=files)
        if response.is_success and response.data:
            return (
                UUID(response.data) if isinstance(response.data, str) else None
            )
        return None
