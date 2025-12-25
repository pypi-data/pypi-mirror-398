"""Common types shared across domains.

Contains settings, change types, and other shared structures.
"""
from typing import Optional
from enum import IntEnum
from pydantic import Field

from .base_model import PyWATSModel


class ChangeType(IntEnum):
    """Change type for settings."""
    NONE = 0
    ADD = 1
    UPDATE = 2
    DELETE = 3
    UNKNOWN_4 = 4
    UNKNOWN_5 = 5
    UNKNOWN_6 = 6


class Setting(PyWATSModel):
    """
    Key-value setting used for tags/custom data.

    Used in Products, ProductRevisions, Assets, and Units.
    """
    key: str = Field(..., alias="key")
    value: Optional[str] = Field(default=None, alias="value")  # Allow None values
    change: Optional[ChangeType] = Field(default=None, alias="change")
