"""Software domain models.

Software package and file models.
"""
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import Field, AliasChoices

from ...shared.base_model import PyWATSModel
from .enums import PackageStatus


class PackageTag(PyWATSModel):
    """
    Represents a tag/metadata on a software package.

    Attributes:
        key: Tag name/key
        value: Tag value
    """

    key: Optional[str] = Field(default=None)
    value: Optional[str] = Field(default=None)


class PackageFile(PyWATSModel):
    """
    Represents a file within a software package.

    Attributes:
        file_id: Unique identifier for the file
        filename: Name of the file
        path: Full path to the file within the package
        size: File size in bytes
        checksum: File checksum/hash
        created_utc: Creation timestamp
        modified_utc: Last modification timestamp
        attributes: Additional file attributes
    """

    file_id: Optional[UUID] = Field(
        default=None,
        validation_alias=AliasChoices("fileId", "file_id", "id"),
        serialization_alias="fileId",
    )
    filename: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("filename", "fileName", "name"),
    )
    path: Optional[str] = Field(default=None)
    size: Optional[int] = Field(default=None)
    checksum: Optional[str] = Field(default=None)
    created_utc: Optional[datetime] = Field(
        default=None,
        validation_alias=AliasChoices("createdUtc", "created_utc", "created"),
        serialization_alias="createdUtc",
    )
    modified_utc: Optional[datetime] = Field(
        default=None,
        validation_alias=AliasChoices("modifiedUtc", "modified_utc", "modified"),
        serialization_alias="modifiedUtc",
    )
    attributes: Optional[str] = Field(default=None)


class VirtualFolder(PyWATSModel):
    """
    Represents a virtual folder in Production Manager.

    Attributes:
        folder_id: Unique identifier for the folder
        name: Folder name
        path: Folder path
        description: Folder description
    """

    folder_id: Optional[UUID] = Field(
        default=None,
        validation_alias=AliasChoices("folderId", "folder_id", "id"),
        serialization_alias="folderId",
    )
    name: Optional[str] = Field(default=None)
    path: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)


class Package(PyWATSModel):
    """
    Represents a software distribution package.

    Attributes:
        package_id: Unique identifier for the package
        name: Package name
        description: Package description
        version: Package version number
        status: Package status (Draft, Pending, Released, Revoked)
        install_on_root: Whether to install on root
        root_directory: Root directory path
        priority: Installation priority
        tags: List of package tags/metadata
        created_utc: Creation timestamp
        modified_utc: Last modification timestamp
        created_by: User who created the package
        modified_by: User who last modified the package
        files: List of files in the package (when populated)
    """

    package_id: Optional[UUID] = Field(
        default=None,
        validation_alias=AliasChoices("packageId", "package_id", "id"),
        serialization_alias="packageId",
    )
    name: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    version: Optional[int] = Field(default=None)
    status: Optional[PackageStatus] = Field(default=None)
    install_on_root: Optional[bool] = Field(
        default=None,
        validation_alias=AliasChoices("installOnRoot", "install_on_root"),
        serialization_alias="installOnRoot",
    )
    root_directory: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("rootDirectory", "root_directory"),
        serialization_alias="rootDirectory",
    )
    priority: Optional[int] = Field(default=None)
    tags: Optional[List[PackageTag]] = Field(default=None)
    created_utc: Optional[datetime] = Field(
        default=None,
        validation_alias=AliasChoices("createdUtc", "created_utc", "created"),
        serialization_alias="createdUtc",
    )
    modified_utc: Optional[datetime] = Field(
        default=None,
        validation_alias=AliasChoices("modifiedUtc", "modified_utc", "modified"),
        serialization_alias="modifiedUtc",
    )
    created_by: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("createdBy", "created_by"),
        serialization_alias="createdBy",
    )
    modified_by: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("modifiedBy", "modified_by"),
        serialization_alias="modifiedBy",
    )
    files: Optional[List[PackageFile]] = Field(default=None)
