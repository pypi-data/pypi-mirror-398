"""RootCause domain enums.

Ticket status, priority, and other enumerations.
"""
from enum import IntEnum, IntFlag


class TicketStatus(IntFlag):
    """
    Ticket status flags.

    Can be combined for filtering (e.g., OPEN | IN_PROGRESS)
    """

    OPEN = 1
    IN_PROGRESS = 2
    ON_HOLD = 4
    SOLVED = 8
    CLOSED = 16
    ARCHIVED = 32


class TicketPriority(IntEnum):
    """Ticket priority levels"""

    LOW = 0
    MEDIUM = 1
    HIGH = 2


class TicketView(IntEnum):
    """Ticket view filter for listing tickets"""

    ASSIGNED = 0  # Tickets assigned to current user
    FOLLOWING = 1  # Tickets current user is following
    ALL = 2  # All tickets (requires "Manage All Tickets" permission)


class TicketUpdateType(IntEnum):
    """Type of ticket update/history entry"""

    CONTENT = 0  # Ticket content (text)
    PROGRESS = 1  # Progress changed
    PROPERTIES = 2  # Ticket properties (assignee, status, etc.)
    NOTIFICATION = 3  # Notification info (reminder/mail)
