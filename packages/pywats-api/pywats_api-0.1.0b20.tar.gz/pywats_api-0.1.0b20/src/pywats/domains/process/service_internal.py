"""Process service - internal API business logic layer.

⚠️ INTERNAL API - SUBJECT TO CHANGE ⚠️

Uses internal WATS API endpoints that are not publicly documented.
These methods may change or be removed without notice.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID

from .repository_internal import ProcessRepositoryInternal
from .models import ProcessInfo, RepairOperationConfig, RepairCategory


class ProcessServiceInternal:
    """
    Process business logic layer using internal API.
    
    ⚠️ INTERNAL API - SUBJECT TO CHANGE ⚠️
    
    Provides extended operations including:
    - Full process details (ProcessID, state, etc.)
    - Repair operation configurations
    - Fail code categories
    """
    
    def __init__(self, repository: ProcessRepositoryInternal):
        """
        Initialize service with internal repository.
        
        Args:
            repository: ProcessRepositoryInternal instance
        """
        self._repository = repository
    
    # =========================================================================
    # Process Operations
    # =========================================================================
    
    def get_processes(self) -> List[ProcessInfo]:
        """
        Get all processes with full details.
        
        ⚠️ INTERNAL API
        
        Returns:
            List of ProcessInfo objects with full details
        """
        return self._repository.get_processes()
    
    def get_process(self, process_id: UUID) -> Optional[ProcessInfo]:
        """
        Get a specific process by ID.
        
        ⚠️ INTERNAL API
        
        Args:
            process_id: The process GUID
            
        Returns:
            ProcessInfo or None if not found
        """
        return self._repository.get_process(process_id)
    
    def get_test_operations(self) -> List[ProcessInfo]:
        """
        Get all test operations (isTestOperation=true).
        
        ⚠️ INTERNAL API
        
        Returns:
            List of test operation ProcessInfo objects
        """
        return [p for p in self.get_processes() if p.is_test_operation]
    
    def get_repair_processes(self) -> List[ProcessInfo]:
        """
        Get all repair processes (isRepairOperation=true).
        
        ⚠️ INTERNAL API
        
        Returns:
            List of repair ProcessInfo objects
        """
        return [p for p in self.get_processes() if p.is_repair_operation]
    
    def get_process_by_code(self, code: int) -> Optional[ProcessInfo]:
        """
        Get a process by its code.
        
        ⚠️ INTERNAL API
        
        Args:
            code: The process code (e.g., 100, 500)
            
        Returns:
            ProcessInfo or None if not found
        """
        for p in self.get_processes():
            if p.code == code:
                return p
        return None
    
    # =========================================================================
    # Repair Operations
    # =========================================================================
    
    def get_repair_operation_configs(self) -> Dict[int, RepairOperationConfig]:
        """
        Get all repair operation configurations.
        
        ⚠️ INTERNAL API
        
        Returns a dictionary keyed by process code (e.g., 500, 510)
        containing repair categories and fail codes.
        
        Returns:
            Dict mapping process code to RepairOperationConfig
        """
        return self._repository.get_repair_operations()
    
    def get_repair_categories(self, repair_code: int = 500) -> List[RepairCategory]:
        """
        Get repair categories (fail code categories) for a repair process.
        
        ⚠️ INTERNAL API
        
        Args:
            repair_code: The repair process code (default 500)
            
        Returns:
            List of RepairCategory objects
        """
        configs = self.get_repair_operation_configs()
        if repair_code in configs:
            return configs[repair_code].categories
        return []
    
    def get_fail_codes(self, repair_code: int = 500) -> List[Dict[str, Any]]:
        """
        Get flattened fail codes for a repair process.
        
        ⚠️ INTERNAL API
        
        Args:
            repair_code: The repair process code (default 500)
            
        Returns:
            List of fail code dicts with category info
        """
        result = []
        for category in self.get_repair_categories(repair_code):
            for fc in category.fail_codes:
                result.append({
                    "guid": str(fc.guid),
                    "description": fc.description,
                    "category": category.description,
                    "category_guid": str(category.guid),
                    "failure_type": fc.failure_type,
                    "selectable": fc.selectable
                })
        return result
    
    # =========================================================================
    # Validation Helpers
    # =========================================================================
    
    def is_valid_test_operation(self, code: int) -> bool:
        """
        Check if a process code is a valid test operation.
        
        ⚠️ INTERNAL API
        
        Args:
            code: The process code to validate
            
        Returns:
            True if the code is a valid test operation
        """
        process = self.get_process_by_code(code)
        return process is not None and process.is_test_operation
    
    def is_valid_repair_operation(self, code: int) -> bool:
        """
        Check if a process code is a valid repair operation.
        
        ⚠️ INTERNAL API
        
        Args:
            code: The process code to validate
            
        Returns:
            True if the code is a valid repair operation
        """
        process = self.get_process_by_code(code)
        return process is not None and process.is_repair_operation
    
    def get_default_repair_code(self) -> int:
        """
        Get the default repair process code.
        
        ⚠️ INTERNAL API
        
        Returns:
            The first available repair process code, or 500 as fallback
        """
        repair_procs = self.get_repair_processes()
        if repair_procs:
            return repair_procs[0].code or 500
        return 500
