"""Software repository - data access layer.

All API interactions for software distribution packages.
"""
from typing import Optional, List, Union, Dict, Any, TYPE_CHECKING
import logging
from uuid import UUID

if TYPE_CHECKING:
    from ...core import HttpClient
    from ...core.exceptions import ErrorHandler

from .models import Package, PackageFile, VirtualFolder
from .enums import PackageStatus


class SoftwareRepository:
    """
    Software distribution data access layer.

    Handles all WATS API interactions for software packages.
    """

    def __init__(
        self, 
        http_client: "HttpClient",
        error_handler: Optional["ErrorHandler"] = None
    ):
        """
        Initialize with HTTP client.

        Args:
            http_client: HttpClient for making HTTP requests
            error_handler: Optional ErrorHandler for error handling (default: STRICT mode)
        """
        self._http_client = http_client
        # Import here to avoid circular imports
        from ...core.exceptions import ErrorHandler, ErrorMode
        self._error_handler = error_handler or ErrorHandler(ErrorMode.STRICT)

    # =========================================================================
    # Query Packages
    # =========================================================================

    def get_packages(self) -> List[Package]:
        """
        Get all software packages.

        GET /api/Software/Packages

        Returns:
            List of Package objects
        """
        response = self._http_client.get("/api/Software/Packages")
        if response.is_success and response.data:
            if isinstance(response.data, list):
                return [Package.model_validate(item) for item in response.data]
        return []

    def get_package(self, package_id: Union[str, UUID]) -> Optional[Package]:
        """
        Get a specific software package by ID.

        GET /api/Software/Package/{id}

        Args:
            package_id: The package UUID

        Returns:
            Package object or None if not found
        """
        response = self._http_client.get(f"/api/Software/Package/{package_id}")
        if response.is_success and response.data:
            return Package.model_validate(response.data)
        return None

    def get_package_by_name(
        self,
        name: str,
        status: Optional[Union[PackageStatus, str]] = None,
        version: Optional[int] = None,
    ) -> Optional[Package]:
        """
        Get a software package by name.

        GET /api/Software/PackageByName

        Args:
            name: Package name
            status: Optional status filter (PackageStatus enum or string)
            version: Optional specific version number

        Returns:
            Package object or None if not found
        """
        params: Dict[str, Any] = {"name": name}
        if status:
            # Handle both enum and string
            params["status"] = status.value if hasattr(status, 'value') else status
        if version is not None:
            params["version"] = version
        response = self._http_client.get("/api/Software/PackageByName", params=params)
        if response.is_success and response.data:
            return Package.model_validate(response.data)
        return None

    def get_packages_by_tag(
        self,
        tag: str,
        value: str,
        status: Optional[Union[PackageStatus, str]] = None,
    ) -> List[Package]:
        """
        Get packages filtered by tag.

        GET /api/Software/PackagesByTag

        Args:
            tag: Tag name to filter by
            value: Tag value to match
            status: Optional status filter (PackageStatus enum or string)

        Returns:
            List of matching Package objects
        """
        params = {"tag": tag, "value": value}
        if status:
            # Handle both enum and string
            params["status"] = status.value if hasattr(status, 'value') else status
        response = self._http_client.get("/api/Software/PackagesByTag", params=params)
        if response.is_success and response.data:
            if isinstance(response.data, list):
                return [Package.model_validate(item) for item in response.data]
        return []

    # =========================================================================
    # Create, Update, Delete Packages
    # =========================================================================

    def create_package(self, package: Package) -> Optional[Package]:
        """
        Create a new package in Draft status.

        POST /api/Software/Package

        If name exists, version will be previous version + 1.

        Args:
            package: Package object with metadata

        Returns:
            Created Package object or None
        """
        data = package.model_dump(by_alias=True, exclude_none=True)
        response = self._http_client.post("/api/Software/Package", data=data)
        if response.is_success and response.data:
            return Package.model_validate(response.data)
        return None

    def update_package(
        self, package_id: Union[str, UUID], package: Package
    ) -> Optional[Package]:
        """
        Update a software package.

        PUT /api/Software/Package/{id}

        Note: This will overwrite existing configuration.
        - Package in Draft: all details can be edited
        - Package in Pending/Released: only Status and Tags can be edited

        Args:
            package_id: The package UUID
            package: Updated package data

        Returns:
            Updated Package object or None
        """
        # Use mode="json" to properly serialize UUIDs, datetimes, and enums
        data = package.model_dump(mode="json", by_alias=True, exclude_none=True)
        response = self._http_client.put(
            f"/api/Software/Package/{package_id}", data=data
        )
        if response.is_success and response.data:
            return Package.model_validate(response.data)
        return None

    def delete_package(self, package_id: Union[str, UUID]) -> bool:
        """
        Delete a software package by ID.

        DELETE /api/Software/Package/{id}

        Note: Status must be Draft or Revoked before deletion.

        Args:
            package_id: The package UUID to delete

        Returns:
            True if successful
        """
        response = self._http_client.delete(f"/api/Software/Package/{package_id}")
        return response.is_success

    def delete_package_by_name(
        self, name: str, version: Optional[int] = None
    ) -> bool:
        """
        Delete a software package by name.

        DELETE /api/Software/PackageByName

        Note: Status must be Draft or Revoked before deletion.

        Args:
            name: Package name
            version: Optional version number

        Returns:
            True if successful
        """
        params: Dict[str, Any] = {"name": name}
        if version is not None:
            params["version"] = version
        response = self._http_client.delete(
            "/api/Software/PackageByName", params=params
        )
        return response.is_success

    # =========================================================================
    # Package Status
    # =========================================================================

    def update_package_status(
        self, package_id: Union[str, UUID], status: PackageStatus
    ) -> bool:
        """
        Update the status of a software package.

        POST /api/Software/PackageStatus/{id}

        Status transitions:
        - Draft -> Pending
        - Pending -> Draft OR Released
        - Released -> Revoked

        Args:
            package_id: The package UUID
            status: New status

        Returns:
            True if successful
        """
        response = self._http_client.post(
            f"/api/Software/PackageStatus/{package_id}",
            params={"status": status.value},
        )
        return response.is_success

    # =========================================================================
    # Package Files
    # =========================================================================

    def get_package_files(
        self, package_id: Union[str, UUID]
    ) -> List[PackageFile]:
        """
        Get files associated with a package.

        GET /api/Software/PackageFiles/{id}

        Args:
            package_id: The package UUID

        Returns:
            List of PackageFile objects
        """
        response = self._http_client.get(f"/api/Software/PackageFiles/{package_id}")
        if response.is_success and response.data:
            if isinstance(response.data, list):
                return [
                    PackageFile.model_validate(item) for item in response.data
                ]
        return []

    def upload_package_zip(
        self,
        package_id: Union[str, UUID],
        zip_content: bytes,
        clean_install: bool = False,
    ) -> bool:
        """
        Upload a zip file to a software package.

        POST /api/Software/Package/UploadZip/{id}

        Note:
        - Will merge files by default
        - Use clean_install=True to delete existing files first
        - Zip cannot contain files on root level
        - All files must be in a folder

        Args:
            package_id: The package UUID
            zip_content: Zip file content as bytes
            clean_install: If True, delete existing files first

        Returns:
            True if successful
        """
        params = {"cleanInstall": "true"} if clean_install else {}
        headers = {"Content-Type": "application/zip"}
        response = self._http_client.post(
            f"/api/Software/Package/UploadZip/{package_id}",
            data=zip_content,
            params=params,
            headers=headers,
        )
        return response.is_success

    def update_file_attribute(
        self,
        file_id: Union[str, UUID],
        attributes: str,
    ) -> bool:
        """
        Update file attributes for a specific file.

        POST /api/Software/Package/FileAttribute/{id}

        Args:
            file_id: The file ID
            attributes: Attribute data to update

        Returns:
            True if successful
        """
        response = self._http_client.post(
            f"/api/Software/Package/FileAttribute/{file_id}",
            data={"attributes": attributes},
        )
        return response.is_success

    # =========================================================================
    # Virtual Folders
    # =========================================================================

    def get_virtual_folders(self) -> List[VirtualFolder]:
        """
        Get all virtual folders registered in Production Manager.

        GET /api/Software/VirtualFolders

        Returns:
            List of VirtualFolder objects
        """
        response = self._http_client.get("/api/Software/VirtualFolders")
        if response.is_success and response.data:
            if isinstance(response.data, list):
                return [
                    VirtualFolder.model_validate(item) for item in response.data
                ]
        return []
