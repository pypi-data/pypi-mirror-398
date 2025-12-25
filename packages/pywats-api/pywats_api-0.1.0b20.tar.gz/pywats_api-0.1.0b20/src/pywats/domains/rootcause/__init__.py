"""RootCause domain module.

Provides ticketing system services and models.
"""
from .enums import (
    TicketStatus,
    TicketPriority,
    TicketView,
    TicketUpdateType,
)
from .models import Ticket, TicketUpdate, TicketAttachment
from .repository import RootCauseRepository
from .service import RootCauseService

__all__ = [
    # Enums
    "TicketStatus",
    "TicketPriority",
    "TicketView",
    "TicketUpdateType",
    # Models
    "Ticket",
    "TicketUpdate",
    "TicketAttachment",
    # Repository & Service
    "RootCauseRepository",
    "RootCauseService",
]
