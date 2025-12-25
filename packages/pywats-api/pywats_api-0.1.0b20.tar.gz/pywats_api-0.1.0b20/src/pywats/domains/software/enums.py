"""Software domain enums.

Package status and related enumerations.
"""
from enum import Enum


class PackageStatus(str, Enum):
    """Software package status"""

    DRAFT = "Draft"
    PENDING = "Pending"
    RELEASED = "Released"
    REVOKED = "Revoked"
