"""Production service - internal API business logic layer.

⚠️ INTERNAL API - SUBJECT TO CHANGE ⚠️

Provides service-level operations using internal WATS API endpoints.
These endpoints may change without notice.

Usage:
    # Via main API
    api = pyWATS(url, username, password)
    phases = api.production_internal.get_unit_phases()
"""
from typing import List, Optional
import logging

from .repository_internal import ProductionRepositoryInternal
from .models import UnitPhase


logger = logging.getLogger(__name__)


class ProductionServiceInternal:
    """
    Production service using internal API.
    
    ⚠️ INTERNAL API - SUBJECT TO CHANGE ⚠️
    
    Provides:
    - get_unit_phases() - Get all available MES unit phases
    """
    
    def __init__(self, repository: ProductionRepositoryInternal):
        """
        Initialize service with repository.
        
        Args:
            repository: ProductionRepositoryInternal instance
        """
        self._repository = repository
    
    # =========================================================================
    # Unit Phases
    # =========================================================================
    
    def get_unit_phases(self) -> List[UnitPhase]:
        """
        Get all available unit phases.

        ⚠️ INTERNAL API - Uses internal Mes endpoint.
        
        Unit phases define production workflow states:
        - "In Test" - Unit is being tested
        - "Passed" - Unit passed testing
        - "Failed" - Unit failed testing
        - "In Repair" - Unit is being repaired
        - "Scrapped" - Unit has been scrapped
        - etc.

        Returns:
            List of UnitPhase objects containing phase configuration
            
        Example:
            phases = api.production_internal.get_unit_phases()
            for phase in phases:
                print(f"{phase.name}: {phase.description}")
        """
        logger.debug("Fetching unit phases from internal API")
        return self._repository.get_unit_phases()
    
    def get_phase_by_name(self, name: str) -> UnitPhase | None:
        """
        Get a specific unit phase by name.
        
        ⚠️ INTERNAL API

        Args:
            name: The name of the phase to find
            
        Returns:
            UnitPhase if found, None otherwise
        """
        phases = self.get_unit_phases()
        for phase in phases:
            if phase.name == name:
                return phase
        return None
