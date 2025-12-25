"""RootCause domain models.

Ticket and related data models.
"""
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import Field, AliasChoices

from ...shared.base_model import PyWATSModel
from ...shared.common_types import Setting
from .enums import TicketStatus, TicketPriority, TicketUpdateType


class TicketAttachment(PyWATSModel):
    """
    Represents an attachment in a RootCause ticket.

    Attributes:
        attachment_id: Unique identifier for the attachment
        filename: Name of the attached file
    """

    attachment_id: Optional[UUID] = Field(
        default=None,
        validation_alias=AliasChoices("attachmentId", "attachment_id"),
        serialization_alias="attachmentId",
    )
    filename: Optional[str] = Field(default=None)


class TicketUpdate(PyWATSModel):
    """
    Represents an update/history entry in a RootCause ticket.

    Attributes:
        update_id: Unique identifier for the update
        update_utc: Timestamp of the update (UTC)
        update_user: User who made the update
        content: Content/comment of the update
        update_type: Type of update
        attachments: List of attachments added in this update
    """

    update_id: Optional[UUID] = Field(
        default=None,
        validation_alias=AliasChoices("updateId", "update_id"),
        serialization_alias="updateId",
    )
    update_utc: Optional[datetime] = Field(
        default=None,
        validation_alias=AliasChoices("updateUtc", "update_utc"),
        serialization_alias="updateUtc",
    )
    update_user: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("updateUser", "update_user"),
        serialization_alias="updateUser",
    )
    content: Optional[str] = Field(default=None)
    update_type: Optional[TicketUpdateType] = Field(
        default=None,
        validation_alias=AliasChoices("updateType", "update_type"),
        serialization_alias="updateType",
    )
    attachments: Optional[List[TicketAttachment]] = Field(default=None)


class Ticket(PyWATSModel):
    """
    Represents a RootCause ticket in WATS.

    Used for tracking issues, collaborating on solutions, and managing
    the resolution workflow.

    Attributes:
        ticket_id: Unique identifier for the ticket
        ticket_number: Human-readable ticket number
        progress: Progress information/notes
        owner: Username of the ticket owner
        assignee: Username of the assigned user
        subject: Ticket subject/title
        status: Current status (Open, In Progress, etc.)
        priority: Priority level (Low, Medium, High)
        report_uuid: UUID of the associated report (if any)
        created_utc: Ticket creation timestamp (UTC)
        updated_utc: Last update timestamp (UTC)
        team: Team assigned to the ticket
        origin: Origin/source of the ticket
        tags: List of tags/metadata
        history: List of historical updates
        update: Current/pending update
    """

    ticket_id: Optional[UUID] = Field(
        default=None,
        validation_alias=AliasChoices("ticketId", "ticket_id"),
        serialization_alias="ticketId",
    )
    ticket_number: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("ticketNumber", "ticket_number"),
        serialization_alias="ticketNumber",
    )
    progress: Optional[str] = Field(default=None)
    owner: Optional[str] = Field(default=None)
    assignee: Optional[str] = Field(default=None)
    subject: Optional[str] = Field(default=None)
    status: Optional[TicketStatus] = Field(default=None)
    priority: Optional[TicketPriority] = Field(default=None)
    report_uuid: Optional[UUID] = Field(
        default=None,
        validation_alias=AliasChoices("reportUuid", "report_uuid"),
        serialization_alias="reportUuid",
    )
    created_utc: Optional[datetime] = Field(
        default=None,
        validation_alias=AliasChoices("createdUtc", "created_utc"),
        serialization_alias="createdUtc",
    )
    updated_utc: Optional[datetime] = Field(
        default=None,
        validation_alias=AliasChoices("updatedUtc", "updated_utc"),
        serialization_alias="updatedUtc",
    )
    team: Optional[str] = Field(default=None)
    origin: Optional[str] = Field(default=None)
    tags: Optional[List[Setting]] = Field(default=None)
    history: Optional[List[TicketUpdate]] = Field(default=None)
    update: Optional[TicketUpdate] = Field(default=None)
