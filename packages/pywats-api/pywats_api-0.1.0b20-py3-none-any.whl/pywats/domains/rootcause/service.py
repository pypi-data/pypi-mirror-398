"""RootCause service - business logic layer.

All business operations for the RootCause ticketing system.
"""
from typing import Optional, List, Union
from uuid import UUID
import logging

from .repository import RootCauseRepository

logger = logging.getLogger(__name__)
from .models import Ticket, TicketUpdate
from .enums import TicketStatus, TicketPriority, TicketView
from ...core import HttpClient


class RootCauseService:
    """
    RootCause (Ticketing) business logic layer.

    Provides high-level operations for issue tracking and resolution.
    """

    def __init__(self, repository_or_client: Union[RootCauseRepository, HttpClient]):
        """
        Initialize with RootCauseRepository or HttpClient.

        Args:
            repository_or_client: RootCauseRepository instance or HttpClient (for backward compatibility)
        """
        if isinstance(repository_or_client, RootCauseRepository):
            self._repository = repository_or_client
        else:
            # Backward compatibility: create repository from HttpClient
            self._repository = RootCauseRepository(repository_or_client)

    # =========================================================================
    # Ticket Operations
    # =========================================================================

    def get_ticket(self, ticket_id: Union[str, UUID]) -> Optional[Ticket]:
        """
        Get a ticket by ID.

        Args:
            ticket_id: The ticket ID (GUID)

        Returns:
            Ticket object or None if not found
        """
        return self._repository.get_ticket(ticket_id)

    def get_tickets(
        self,
        status: TicketStatus = TicketStatus.OPEN,
        view: TicketView = TicketView.ASSIGNED,
        search_string: Optional[str] = None,
    ) -> List[Ticket]:
        """
        Get tickets with given status.

        Args:
            status: Ticket status flags (can be combined with |)
            view: View filter (ASSIGNED, FOLLOWING, ALL)
            search_string: Optional search for subject, tags, or tag value

        Returns:
            List of Ticket objects
        """
        return self._repository.get_tickets(status, view, search_string)

    def get_open_tickets(
        self, view: TicketView = TicketView.ASSIGNED
    ) -> List[Ticket]:
        """
        Get all open tickets.

        Args:
            view: View filter

        Returns:
            List of open Ticket objects
        """
        return self._repository.get_tickets(TicketStatus.OPEN, view)

    def get_active_tickets(
        self, view: TicketView = TicketView.ASSIGNED
    ) -> List[Ticket]:
        """
        Get all active tickets (Open or In Progress).

        Args:
            view: View filter

        Returns:
            List of active Ticket objects
        """
        status = TicketStatus.OPEN | TicketStatus.IN_PROGRESS
        return self._repository.get_tickets(status, view)

    def create_ticket(
        self,
        subject: str,
        priority: TicketPriority = TicketPriority.MEDIUM,
        assignee: Optional[str] = None,
        team: Optional[str] = None,
        report_uuid: Optional[Union[str, UUID]] = None,
        initial_comment: Optional[str] = None,
    ) -> Optional[Ticket]:
        """
        Create a new ticket.

        Args:
            subject: Ticket subject/title
            priority: Priority level (default: MEDIUM)
            assignee: Username to assign ticket to
            team: Team to assign ticket to
            report_uuid: UUID of associated report
            initial_comment: Initial comment/description

        Returns:
            Created Ticket object or None
        """
        ticket = Ticket(
            subject=subject,
            priority=priority,
            assignee=assignee,
            team=team,
        )
        if report_uuid:
            ticket.report_uuid = (
                UUID(report_uuid)
                if isinstance(report_uuid, str)
                else report_uuid
            )
        if initial_comment:
            ticket.update = TicketUpdate(content=initial_comment)

        result = self._repository.create_ticket(ticket)
        if result:
            logger.info(f"TICKET_CREATED: {result.ticket_id} (subject={subject}, priority={priority.name})")
        return result

    def update_ticket(self, ticket: Ticket) -> Optional[Ticket]:
        """
        Update an existing ticket.

        Args:
            ticket: Ticket object with updated data

        Returns:
            Updated Ticket object or None
        """
        result = self._repository.update_ticket(ticket)
        if result:
            logger.info(f"TICKET_UPDATED: {result.ticket_id}")
        return result

    def add_comment(
        self, ticket_id: Union[str, UUID], comment: str
    ) -> Optional[Ticket]:
        """
        Add a comment to a ticket.

        Args:
            ticket_id: Ticket ID
            comment: Comment text

        Returns:
            Updated Ticket object or None
        """
        ticket = Ticket(
            ticket_id=(
                UUID(ticket_id) if isinstance(ticket_id, str) else ticket_id
            ),
            update=TicketUpdate(content=comment),
        )
        result = self._repository.update_ticket(ticket)
        if result:
            logger.info(f"TICKET_COMMENT_ADDED: {ticket_id}")
        return result

    def change_status(
        self, ticket_id: Union[str, UUID], status: TicketStatus
    ) -> Optional[Ticket]:
        """
        Change the status of a ticket.

        Args:
            ticket_id: Ticket ID
            status: New status

        Returns:
            Updated Ticket object or None
        """
        ticket = Ticket(
            ticket_id=(
                UUID(ticket_id) if isinstance(ticket_id, str) else ticket_id
            ),
            status=status,
        )
        result = self._repository.update_ticket(ticket)
        if result:
            logger.info(f"TICKET_STATUS_CHANGED: {ticket_id} (status={status.name})")
        return result

    def assign_ticket(
        self, ticket_id: Union[str, UUID], assignee: str
    ) -> Optional[Ticket]:
        """
        Assign a ticket to a user.

        Args:
            ticket_id: Ticket ID
            assignee: Username to assign to

        Returns:
            Updated Ticket object or None
        """
        ticket = Ticket(
            ticket_id=(
                UUID(ticket_id) if isinstance(ticket_id, str) else ticket_id
            ),
            assignee=assignee,
        )
        result = self._repository.update_ticket(ticket)
        if result:
            logger.info(f"TICKET_ASSIGNED: {ticket_id} (assignee={assignee})")
        return result

    def archive_tickets(
        self, ticket_ids: List[Union[str, UUID]]
    ) -> Optional[Ticket]:
        """
        Archive solved tickets.

        Only Solved tickets can be archived.

        Args:
            ticket_ids: List of ticket IDs to archive

        Returns:
            Ticket object or None
        """
        result = self._repository.archive_tickets(ticket_ids)
        if result:
            logger.info(f"TICKETS_ARCHIVED: count={len(ticket_ids)}")
        return result

    # =========================================================================
    # Attachment Operations
    # =========================================================================

    def get_attachment(
        self, attachment_id: Union[str, UUID], filename: Optional[str] = None
    ) -> Optional[bytes]:
        """
        Get attachment content.

        Args:
            attachment_id: The attachment ID (GUID)
            filename: Optional filename for download

        Returns:
            Attachment content as bytes, or None
        """
        return self._repository.get_attachment(attachment_id, filename)

    def upload_attachment(
        self, file_content: bytes, filename: str
    ) -> Optional[UUID]:
        """
        Upload an attachment.

        Args:
            file_content: The file content as bytes
            filename: The filename for the attachment

        Returns:
            UUID of the created attachment, or None
        """
        return self._repository.upload_attachment(file_content, filename)
