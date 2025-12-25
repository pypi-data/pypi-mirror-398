"""Process repository - internal API data access layer.

⚠️ INTERNAL API - SUBJECT TO CHANGE ⚠️

Uses internal WATS API endpoints that are not publicly documented.
These endpoints may change without notice. This module should be
replaced with public API endpoints as soon as they become available.

The internal API requires the Referer header to be set to the base URL.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID

from ...core import HttpClient
from .models import ProcessInfo, RepairOperationConfig


class ProcessRepositoryInternal:
    """
    Process data access layer using internal API.
    
    ⚠️ INTERNAL API - SUBJECT TO CHANGE ⚠️
    
    Uses:
    - GET /api/internal/Process/GetProcesses
    - GET /api/internal/Process/GetProcess/{id}
    - GET /api/internal/Process/GetRepairOperations
    - GET /api/internal/Process/GetRepairOperation/{id}
    
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
    
    def _internal_get(self, endpoint: str) -> Any:
        """
        Make an internal API GET request with Referer header.
        
        ⚠️ INTERNAL: Adds Referer header required by internal API.
        """
        response = self._http.get(
            endpoint,
            headers={"Referer": self._base_url}
        )
        if response.is_success:
            return response.data
        return None
    
    # =========================================================================
    # Process Operations
    # =========================================================================
    
    def get_processes(self) -> List[ProcessInfo]:
        """
        Get all processes with full details.
        
        ⚠️ INTERNAL API - uses /api/internal/Process/GetProcesses
        
        Returns:
            List of ProcessInfo objects with full details
        """
        data = self._internal_get("/api/internal/Process/GetProcesses")
        if data and isinstance(data, list):
            # Internal API uses PascalCase - need to map fields
            result = []
            for p in data:
                # Map PascalCase to our model
                mapped = {
                    "code": p.get("Code"),
                    "name": p.get("Name"),
                    "description": p.get("Description"),
                    "ProcessID": p.get("ProcessID"),
                    "processIndex": p.get("ProcessIndex"),
                    "state": p.get("State"),
                    "Properties": p.get("Properties"),
                    "isTestOperation": p.get("IsTestOperation", False),
                    "isRepairOperation": p.get("IsRepairOperation", False),
                    "isWipOperation": p.get("IsWIPOperation", False),
                }
                result.append(ProcessInfo.model_validate(mapped))
            return result
        return []
    
    def get_process(self, process_id: UUID) -> Optional[ProcessInfo]:
        """
        Get a specific process by ID.
        
        ⚠️ INTERNAL API - uses /api/internal/Process/GetProcess/{id}
        
        Args:
            process_id: The process GUID
            
        Returns:
            ProcessInfo or None if not found
        """
        data = self._internal_get(f"/api/internal/Process/GetProcess/{process_id}")
        if data:
            mapped = {
                "code": data.get("Code"),
                "name": data.get("Name"),
                "description": data.get("Description"),
                "ProcessID": data.get("ProcessID"),
                "processIndex": data.get("ProcessIndex"),
                "state": data.get("State"),
                "Properties": data.get("Properties"),
                "isTestOperation": data.get("IsTestOperation", False),
                "isRepairOperation": data.get("IsRepairOperation", False),
                "isWipOperation": data.get("IsWIPOperation", False),
            }
            return ProcessInfo.model_validate(mapped)
        return None
    
    # =========================================================================
    # Repair Operations
    # =========================================================================
    
    def get_repair_operations(self) -> Dict[int, RepairOperationConfig]:
        """
        Get all repair operation configurations.
        
        ⚠️ INTERNAL API - uses /api/internal/Process/GetRepairOperations
        
        Returns a dictionary keyed by process code (e.g., 500, 510).
        
        Returns:
            Dict mapping process code to RepairOperationConfig
        """
        data = self._internal_get("/api/internal/Process/GetRepairOperations")
        if data and isinstance(data, dict):
            result = {}
            for code_str, config in data.items():
                try:
                    code = int(code_str)
                    result[code] = RepairOperationConfig.model_validate(config)
                except (ValueError, Exception):
                    continue
            return result
        return {}
    
    def get_repair_operation(
        self, 
        process_id: UUID, 
        process_code: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific repair operation configuration.
        
        ⚠️ INTERNAL API - uses /api/internal/Process/GetRepairOperation/{id}
        
        Args:
            process_id: The process GUID
            process_code: Optional process code filter
            
        Returns:
            Repair operation config dict or None
        """
        endpoint = f"/api/internal/Process/GetRepairOperation/{process_id}"
        if process_code is not None:
            endpoint += f"?processCode={process_code}"
        return self._internal_get(endpoint)
