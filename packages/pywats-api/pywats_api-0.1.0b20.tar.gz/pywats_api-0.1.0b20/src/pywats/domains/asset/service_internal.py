"""Asset service - internal API business logic layer.

⚠️ INTERNAL API - SUBJECT TO CHANGE ⚠️

Provides service-level operations using internal WATS API endpoints
for file operations on assets (stations, fixtures, etc.).

These endpoints may change without notice.

Usage:
    # Via main API
    api = pyWATS(url, username, password)
    
    # Upload file
    api.asset_internal.upload_file(asset_id, "config.json", content)
    
    # List files
    files = api.asset_internal.list_files(asset_id)
    
    # Download file
    content = api.asset_internal.download_file(asset_id, "config.json")
    
    # Delete files
    api.asset_internal.delete_files(asset_id, ["old.txt"])
"""
from typing import List, Optional
import logging

from .repository_internal import AssetRepositoryInternal


logger = logging.getLogger(__name__)


class AssetServiceInternal:
    """
    Asset service using internal API for file operations.
    
    ⚠️ INTERNAL API - SUBJECT TO CHANGE ⚠️
    
    Provides file operations on assets:
    - upload_file() - Upload file to asset
    - download_file() - Download file from asset
    - list_files() - List files attached to asset
    - delete_files() - Delete files from asset
    """
    
    def __init__(self, repository: AssetRepositoryInternal):
        """
        Initialize service with repository.
        
        Args:
            repository: AssetRepositoryInternal instance
        """
        self._repository = repository
    
    # =========================================================================
    # File Operations
    # =========================================================================
    
    def upload_file(
        self,
        asset_id: str,
        filename: str,
        content: bytes
    ) -> bool:
        """
        Upload a file to an asset.

        ⚠️ INTERNAL API - Uses internal Blob endpoint.
        
        Files are stored in blob storage and associated with the asset ID.
        Use this to attach configuration files, documentation, images, etc.
        
        Args:
            asset_id: Asset ID (GUID)
            filename: Unique filename for the file
            content: File content as bytes

        Returns:
            True if file was uploaded successfully, False otherwise
            
        Example:
            content = b'{"setting": "value"}'
            success = api.asset_internal.upload_file(
                asset_id="abc-123",
                filename="config.json",
                content=content
            )
        """
        logger.debug(f"Uploading file '{filename}' to asset {asset_id}")
        return self._repository.upload_file(asset_id, filename, content)
    
    def download_file(
        self,
        asset_id: str,
        filename: str
    ) -> Optional[bytes]:
        """
        Download a file from an asset.

        ⚠️ INTERNAL API - Uses internal Blob endpoint.
        
        Args:
            asset_id: Asset ID (GUID)
            filename: Filename to download
            
        Returns:
            File content as bytes, or None if not found
            
        Example:
            content = api.asset_internal.download_file(
                asset_id="abc-123",
                filename="config.json"
            )
            if content:
                data = json.loads(content.decode('utf-8'))
        """
        logger.debug(f"Downloading file '{filename}' from asset {asset_id}")
        return self._repository.download_file(asset_id, filename)
    
    def list_files(self, asset_id: str) -> List[str]:
        """
        List all files attached to an asset.

        ⚠️ INTERNAL API - Uses internal Blob endpoint.
        
        Args:
            asset_id: Asset ID (GUID)
            
        Returns:
            List of filenames
            
        Example:
            files = api.asset_internal.list_files("abc-123")
            for filename in files:
                print(f"  - {filename}")
        """
        logger.debug(f"Listing files for asset {asset_id}")
        return self._repository.list_files(asset_id)
    
    def delete_files(
        self,
        asset_id: str,
        filenames: List[str]
    ) -> bool:
        """
        Delete files from an asset.

        ⚠️ INTERNAL API - Uses internal Blob endpoint.
        
        Args:
            asset_id: Asset ID (GUID)
            filenames: List of filenames to delete

        Returns:
            True if files were deleted successfully, False otherwise
            
        Example:
            success = api.asset_internal.delete_files(
                asset_id="abc-123",
                filenames=["old_config.json", "temp.txt"]
            )
        """
        logger.debug(f"Deleting {len(filenames)} files from asset {asset_id}")
        return self._repository.delete_files(asset_id, filenames)
    
    def file_exists(self, asset_id: str, filename: str) -> bool:
        """
        Check if a file exists on an asset.
        
        ⚠️ INTERNAL API

        Args:
            asset_id: Asset ID (GUID)
            filename: Filename to check
            
        Returns:
            True if file exists, False otherwise
        """
        files = self.list_files(asset_id)
        return filename in files
