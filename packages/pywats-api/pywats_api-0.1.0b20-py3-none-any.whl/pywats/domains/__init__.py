"""Domain modules for pyWATS.

Each domain contains:
- models.py: Pure data models (Pydantic)
- enums.py: Domain-specific enumerations
- service.py: Business logic
- repository.py: Data access (API calls)

Some domains also have internal API implementations:
- service_internal.py: Business logic using internal API
- repository_internal.py: Data access using internal API

NOTE: Module naming vs Backend API naming
-----------------------------------------
The 'analytics' module maps to the WATS backend '/api/App/*' endpoints.
We chose 'analytics' as the Python module name because it better describes
the functionality (yield analysis, KPIs, statistics) while 'App' is the
legacy backend controller name. This is purely a naming choice for better
developer experience - all API calls go to /api/App/*.
"""
from . import analytics
from . import asset
from . import process
from . import product
from . import production
from . import report
from . import rootcause
from . import software

__all__ = [
    "analytics",  # Maps to backend /api/App/* endpoints
    "asset",
    "process",
    "product",
    "production",
    "report",
    "rootcause",
    "software",
]
