"""Asset repository - internal API data access layer.

⚠️ INTERNAL API - SUBJECT TO CHANGE ⚠️

Uses internal WATS API endpoints that are not publicly documented.
These endpoints may change without notice. This module should be
replaced with public API endpoints as soon as they become available.

The internal API requires the Referer header to be set to the base URL.
"""
from typing import List, Optional, Dict, Any
import base64

from ...core import HttpClient


class AssetRepositoryInternal:
    """
    Asset data access layer using internal API for file operations.
    
    ⚠️ INTERNAL API - SUBJECT TO CHANGE ⚠️
    
    Uses:
    - POST /api/internal/Blob/Asset (upload file)
    - GET /api/internal/Blob/Asset (download file)
    - GET /api/internal/Blob/Asset/List/{assetId} (list files)
    - DELETE /api/internal/Blob/Assets (delete files)
    
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
    
    def _internal_post(
        self,
        endpoint: str,
        data: Any = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Any:
        """
        Make an internal API POST request with Referer header.
        
        ⚠️ INTERNAL: Adds Referer header required by internal API.
        """
        all_headers = {"Referer": self._base_url}
        if headers:
            all_headers.update(headers)
        response = self._http.post(
            endpoint,
            data=data,
            params=params,
            headers=all_headers
        )
        return response
    
    def _internal_delete(
        self,
        endpoint: str,
        data: Any = None,
        params: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Make an internal API DELETE request with Referer header.
        
        ⚠️ INTERNAL: Adds Referer header required by internal API.
        """
        response = self._http.delete(
            endpoint,
            data=data,
            params=params,
            headers={"Referer": self._base_url}
        )
        return response.is_success
    
    # =========================================================================
    # File Operations (Blob)
    # =========================================================================
    
    def upload_file(
        self,
        asset_id: str,
        filename: str,
        content: bytes
    ) -> bool:
        """
        Upload a file to an asset.

        POST /api/internal/Blob/Asset
        
        ⚠️ INTERNAL API - Uses internal endpoint with Referer header.
        
        Args:
            asset_id: Asset ID (GUID)
            filename: Unique filename for the file
            content: File content as bytes

        Returns:
            True if file was uploaded successfully, False otherwise
        """
        params = {"assetId": asset_id, "filename": filename}
        response = self._internal_post(
            "/api/internal/Blob/Asset",
            params=params,
            data=content,
            headers={"Content-Type": "application/octet-stream"}
        )
        return response.is_success if response else False
    
    def download_file(
        self,
        asset_id: str,
        filename: str
    ) -> Optional[bytes]:
        """
        Download a file from an asset.

        GET /api/internal/Blob/Asset
        
        ⚠️ INTERNAL API - Uses internal endpoint with Referer header.
        
        Args:
            asset_id: Asset ID (GUID)
            filename: Filename to download
            
        Returns:
            File content as bytes, or None if not found
        """
        params = {"assetId": asset_id, "filename": filename}
        response = self._http.get(
            "/api/internal/Blob/Asset",
            params=params,
            headers={"Referer": self._base_url}
        )
        if response.is_success:
            # Response might be raw bytes or JSON with base64 content
            if isinstance(response.data, bytes):
                return response.data
            # If it's a dict, it might contain base64 encoded content
            if isinstance(response.data, dict):
                content = response.data.get("content") or response.data.get("Content")
                if content:
                    return base64.b64decode(content)
        return None
    
    def list_files(self, asset_id: str) -> List[str]:
        """
        List all files attached to an asset.

        GET /api/internal/Blob/Asset/List/{assetId}
        
        ⚠️ INTERNAL API - Uses internal endpoint with Referer header.
        
        Args:
            asset_id: Asset ID (GUID)
            
        Returns:
            List of filenames
        """
        data = self._internal_get(f"/api/internal/Blob/Asset/List/{asset_id}")
        if data:
            return list(data) if isinstance(data, list) else []
        return []
    
    def delete_files(
        self,
        asset_id: str,
        filenames: List[str]
    ) -> bool:
        """
        Delete files from an asset.

        DELETE /api/internal/Blob/Assets
        
        ⚠️ INTERNAL API - Uses internal endpoint with Referer header.
        
        Args:
            asset_id: Asset ID (GUID)
            filenames: List of filenames to delete

        Returns:
            True if files were deleted successfully, False otherwise
        """
        return self._internal_delete(
            "/api/internal/Blob/Assets",
            params={"assetId": asset_id},
            data=filenames
        )
