"""Process repository - public API data access layer.

Uses the public WATS API endpoints for process operations.
"""
from typing import List, Optional, TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from ...core.exceptions import ErrorHandler

from ...core import HttpClient
from .models import ProcessInfo

logger = logging.getLogger(__name__)


class ProcessRepository:
    """
    Process data access layer using public API.
    
    Uses:
    - GET /api/App/Processes (public endpoint)
    """
    
    def __init__(
        self, 
        http_client: HttpClient,
        error_handler: Optional["ErrorHandler"] = None
    ):
        """
        Initialize repository with HTTP client.
        
        Args:
            http_client: The HTTP client for API calls
            error_handler: Optional ErrorHandler for error handling (default: STRICT mode)
        """
        self._http_client = http_client
        # Import here to avoid circular imports
        from ...core.exceptions import ErrorHandler, ErrorMode
        self._error_handler = error_handler or ErrorHandler(ErrorMode.STRICT)
    
    def get_processes(self) -> List[ProcessInfo]:
        """
        Get all processes from the public API.
        
        GET /api/App/Processes
        
        Note: The public API returns processes with limited fields.
        Use ProcessRepositoryInternal for full details.
        
        Returns:
            List of ProcessInfo objects
        """
        response = self._http_client.get("/api/App/Processes")
        if response.is_success and response.data:
            return [ProcessInfo.model_validate(p) for p in response.data]
        return []
