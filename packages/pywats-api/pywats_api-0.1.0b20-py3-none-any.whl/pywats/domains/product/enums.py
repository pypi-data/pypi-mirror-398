"""Product domain enums."""
from enum import IntEnum


class ProductState(IntEnum):
    """Product/Revision state."""
    INACTIVE = 0
    ACTIVE = 1
