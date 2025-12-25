"""Asset data models.

Pure data models with no business logic.
"""
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import Field, AliasChoices

from ...shared import PyWATSModel, Setting
from .enums import AssetState, AssetLogType


class AssetType(PyWATSModel):
    """
    Represents an asset type in WATS.

    Attributes:
        type_id: Unique identifier
        type_name: Name of the asset type
        running_count_limit: Max count until next calibration
        total_count_limit: Asset total count limit
        maintenance_interval: Interval for maintenance (in days)
        calibration_interval: Interval for calibration (in days)
        warning_threshold: Warning threshold percent
        alarm_threshold: Alarm threshold percent
        is_readonly: Whether the type is read-only
        icon: Icon identifier
    """
    type_name: str = Field(
        ...,
        validation_alias=AliasChoices("typeName", "type_name"),
        serialization_alias="typeName"
    )
    type_id: Optional[UUID] = Field(
        default=None,
        validation_alias=AliasChoices("typeId", "type_id"),
        serialization_alias="typeId"
    )
    running_count_limit: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("runningCountLimit", "running_count_limit"),
        serialization_alias="runningCountLimit"
    )
    total_count_limit: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("totalCountLimit", "total_count_limit"),
        serialization_alias="totalCountLimit"
    )
    maintenance_interval: Optional[float] = Field(
        default=None,
        validation_alias=AliasChoices("maintenanceInterval", "maintenance_interval"),
        serialization_alias="maintenanceInterval"
    )
    calibration_interval: Optional[float] = Field(
        default=None,
        validation_alias=AliasChoices("calibrationInterval", "calibration_interval"),
        serialization_alias="calibrationInterval"
    )
    warning_threshold: Optional[float] = Field(
        default=None,
        validation_alias=AliasChoices("warningThreshold", "warning_threshold"),
        serialization_alias="warningThreshold"
    )
    alarm_threshold: Optional[float] = Field(
        default=None,
        validation_alias=AliasChoices("alarmThreshold", "alarm_threshold"),
        serialization_alias="alarmThreshold"
    )
    is_readonly: bool = Field(
        default=False,
        validation_alias=AliasChoices("isReadonly", "is_readonly"),
        serialization_alias="isReadonly"
    )
    icon: Optional[str] = Field(default=None)


class AssetLog(PyWATSModel):
    """
    Represents an asset log entry.

    Attributes:
        log_id: Log entry ID
        asset_id: ID of the asset
        serial_number: Asset serial number
        date: Log entry date
        user: User who made the entry
        log_type: Type of log entry
        comment: Log entry comment
    """
    log_id: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("logId", "log_id"),
        serialization_alias="logId"
    )
    asset_id: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("assetId", "asset_id"),
        serialization_alias="assetId"
    )
    serial_number: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("serialNumber", "serial_number"),
        serialization_alias="serialNumber"
    )
    date: Optional[datetime] = Field(default=None)
    user: Optional[str] = Field(default=None)
    log_type: Optional[AssetLogType] = Field(
        default=None,
        validation_alias=AliasChoices("type", "log_type"),
        serialization_alias="type"
    )
    comment: Optional[str] = Field(default=None)


class Asset(PyWATSModel):
    """
    Represents an asset in WATS.

    Attributes:
        serial_number: Asset serial number (required)
        type_id: Asset type ID (required)
        asset_id: Unique identifier
        parent_asset_id: Parent asset ID (for hierarchical assets)
        parent_serial_number: Parent asset serial number
        asset_name: Asset name
        part_number: Part number
        revision: Revision
        client_id: Client ID
        state: Asset state
        description: Description
        location: Location
        first_seen_date: First seen date
        last_seen_date: Last seen date
        last_maintenance_date: Last maintenance date
        next_maintenance_date: Next maintenance date
        last_calibration_date: Last calibration date
        next_calibration_date: Next calibration date
        total_count: Total usage count
        running_count: Running count since last calibration
        tags: Custom key-value tags
        asset_children: Child assets
        asset_type: Asset type details
        asset_log: Log entries
    """
    serial_number: str = Field(
        ...,
        validation_alias=AliasChoices("serialNumber", "serial_number"),
        serialization_alias="serialNumber"
    )
    type_id: Optional[UUID] = Field(
        default=None,
        validation_alias=AliasChoices("typeId", "type_id"),
        serialization_alias="typeId"
    )
    asset_id: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("assetId", "asset_id"),
        serialization_alias="assetId"
    )
    parent_asset_id: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("parentAssetId", "parent_asset_id"),
        serialization_alias="parentAssetId"
    )
    parent_serial_number: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("parentSerialNumber", "parent_serial_number"),
        serialization_alias="parentSerialNumber"
    )
    asset_name: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("assetName", "asset_name"),
        serialization_alias="assetName"
    )
    part_number: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("partNumber", "part_number"),
        serialization_alias="partNumber"
    )
    revision: Optional[str] = Field(default=None)
    client_id: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("ClientId", "client_id"),
        serialization_alias="ClientId"
    )
    state: AssetState = Field(default=AssetState.OK)
    description: Optional[str] = Field(default=None)
    location: Optional[str] = Field(default=None)
    first_seen_date: Optional[datetime] = Field(
        default=None,
        validation_alias=AliasChoices("firstSeenDate", "first_seen_date"),
        serialization_alias="firstSeenDate"
    )
    last_seen_date: Optional[datetime] = Field(
        default=None,
        validation_alias=AliasChoices("lastSeenDate", "last_seen_date"),
        serialization_alias="lastSeenDate"
    )
    last_maintenance_date: Optional[datetime] = Field(
        default=None,
        validation_alias=AliasChoices("lastMaintenanceDate", "last_maintenance_date"),
        serialization_alias="lastMaintenanceDate"
    )
    next_maintenance_date: Optional[datetime] = Field(
        default=None,
        validation_alias=AliasChoices("nextMaintenanceDate", "next_maintenance_date"),
        serialization_alias="nextMaintenanceDate"
    )
    last_calibration_date: Optional[datetime] = Field(
        default=None,
        validation_alias=AliasChoices("lastCalibrationDate", "last_calibration_date"),
        serialization_alias="lastCalibrationDate"
    )
    next_calibration_date: Optional[datetime] = Field(
        default=None,
        validation_alias=AliasChoices("nextCalibrationDate", "next_calibration_date"),
        serialization_alias="nextCalibrationDate"
    )
    total_count: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("totalCount", "total_count"),
        serialization_alias="totalCount"
    )
    running_count: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("runningCount", "running_count"),
        serialization_alias="runningCount"
    )
    tags: List[Setting] = Field(default_factory=list)
    asset_children: List["Asset"] = Field(
        default_factory=list,
        validation_alias=AliasChoices("assetChildren", "asset_children"),
        serialization_alias="assetChildren"
    )
    asset_type: Optional[AssetType] = Field(
        default=None,
        validation_alias=AliasChoices("assetType", "asset_type"),
        serialization_alias="assetType"
    )
    asset_log: List[AssetLog] = Field(
        default_factory=list,
        validation_alias=AliasChoices("assetLog", "asset_log"),
        serialization_alias="assetLog"
    )
