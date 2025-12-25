"""Process domain module.

Provides process/operation management for test operations and repair operations.

This module handles the process list which defines:
- Test operations (e.g., End of line test, PCBA test, etc.)
- Repair operations (e.g., Repair, RMA repair)
- WIP operations
"""
from .models import ProcessInfo, RepairOperationConfig, RepairCategory
from .repository import ProcessRepository
from .service import ProcessService

# Internal API (⚠️ subject to change - will be replaced with public API)
from .repository_internal import ProcessRepositoryInternal
from .service_internal import ProcessServiceInternal

__all__ = [
    # Models
    "ProcessInfo",
    "RepairOperationConfig",
    "RepairCategory",
    # Public API
    "ProcessRepository",
    "ProcessService",
    # Internal API (⚠️ subject to change)
    "ProcessRepositoryInternal",
    "ProcessServiceInternal",
]
