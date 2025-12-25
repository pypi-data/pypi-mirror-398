"""Production repository - internal API data access layer.

⚠️ INTERNAL API - SUBJECT TO CHANGE ⚠️

Uses internal WATS API endpoints that are not publicly documented.
These endpoints may change without notice. This module should be
replaced with public API endpoints as soon as they become available.

The internal API requires the Referer header to be set to the base URL.
"""
from typing import List, Optional, Dict, Any

from ...core import HttpClient
from .models import UnitPhase


class ProductionRepositoryInternal:
    """
    Production data access layer using internal API.
    
    ⚠️ INTERNAL API - SUBJECT TO CHANGE ⚠️
    
    Uses:
    - GET /api/internal/Mes/GetUnitPhases
    
    The internal API requires the Referer header.
    """
    
    def __init__(self, http_client: HttpClient, base_url: str):
        """
        Initialize repository with HTTP client and base URL.
        
        Args:
            http_client: The HTTP client for API calls
            base_url: The base URL (needed for Referer header)
        """
        self._http = http_client
        self._base_url = base_url.rstrip('/')
    
    def _internal_get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Make an internal API GET request with Referer header.
        
        ⚠️ INTERNAL: Adds Referer header required by internal API.
        """
        response = self._http.get(
            endpoint,
            params=params,
            headers={"Referer": self._base_url}
        )
        if response.is_success:
            return response.data
        return None
    
    # =========================================================================
    # Unit Phases (MES)
    # =========================================================================
    
    def get_unit_phases(self) -> List[UnitPhase]:
        """
        Get all available unit phases.

        GET /api/internal/Mes/GetUnitPhases

        ⚠️ INTERNAL API - Uses internal endpoint with Referer header.
        
        Unit phases define production workflow states (e.g., "In Test", 
        "Passed", "Failed", "In Repair").

        Returns:
            List of UnitPhase objects
        """
        data = self._internal_get("/api/internal/Mes/GetUnitPhases")
        if data:
            return [UnitPhase.model_validate(item) for item in data]
        return []
