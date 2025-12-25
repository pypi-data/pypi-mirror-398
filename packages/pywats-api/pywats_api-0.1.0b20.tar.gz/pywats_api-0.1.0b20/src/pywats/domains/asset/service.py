"""Asset service - business logic layer.

Provides high-level operations for asset management.
"""
from typing import Optional, List, Dict, Union, Any
from datetime import datetime
from uuid import UUID
from pathlib import Path
import logging

from .models import Asset, AssetType, AssetLog

logger = logging.getLogger(__name__)
from .enums import AssetState, AssetAlarmState
from .repository import AssetRepository


class AssetService:
    """
    Asset business logic.

    Provides high-level operations for managing assets including
    validation, state management, and business rules.
    """

    def __init__(self, repository: AssetRepository, base_url: Optional[str] = None):
        """
        Initialize with repository.

        Args:
            repository: AssetRepository for data access
            base_url: Base URL for internal API file operations
        """
        self._repository = repository
        self._base_url = base_url or ""

    # =========================================================================
    # Asset Operations
    # =========================================================================

    def get_assets(
        self,
        filter_str: Optional[str] = None,
        top: Optional[int] = None
    ) -> List[Asset]:
        """
        Get all assets.

        Args:
            filter_str: Optional OData filter string
            top: Optional max number of results

        Returns:
            List of Asset objects
        """
        return self._repository.get_all(filter_str=filter_str, top=top)

    def get_asset(self, identifier: str) -> Optional[Asset]:
        """
        Get an asset by ID or serial number.

        Args:
            identifier: Asset ID (GUID) or serial number

        Returns:
            Asset if found, None otherwise
        """
        return self._repository.get_by_id(identifier)

    def get_asset_by_serial(self, serial_number: str) -> Optional[Asset]:
        """
        Get an asset by serial number.

        Args:
            serial_number: Asset serial number

        Returns:
            Asset if found, None otherwise
        """
        return self._repository.get_by_serial_number(serial_number)

    def create_asset(
        self,
        serial_number: str,
        type_id: UUID,
        asset_name: Optional[str] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        parent_asset_id: Optional[str] = None,
        parent_serial_number: Optional[str] = None,
        *,
        part_number: Optional[str] = None,
        revision: Optional[str] = None,
        state: AssetState = AssetState.OK,
        client_id: Optional[int] = None,
        first_seen_date: Optional[datetime] = None,
        last_seen_date: Optional[datetime] = None,
        last_maintenance_date: Optional[datetime] = None,
        next_maintenance_date: Optional[datetime] = None,
        last_calibration_date: Optional[datetime] = None,
        next_calibration_date: Optional[datetime] = None,
        total_count: Optional[int] = None,
        running_count: Optional[int] = None,
    ) -> Optional[Asset]:
        """
        Create a new asset.

        Args:
            serial_number: Unique serial number (required)
            type_id: Asset type UUID (required)
            asset_name: Optional display name
            description: Optional description text
            location: Optional physical location
            parent_asset_id: Parent asset ID for hierarchical assets
            parent_serial_number: Parent asset serial number for hierarchy
            part_number: Asset part number
            revision: Asset revision string
            state: Asset state (default: AssetState.OK). Values: OK, Warning, Alarm, etc.
            client_id: Client identifier
            first_seen_date: Date asset was first seen
            last_seen_date: Date asset was last seen
            last_maintenance_date: Date of last maintenance
            next_maintenance_date: Date of next scheduled maintenance
            last_calibration_date: Date of last calibration
            next_calibration_date: Date of next scheduled calibration
            total_count: Total usage count
            running_count: Running count since last calibration

        Returns:
            Created Asset object, or None on failure
            
        Example:
            >>> asset = service.create_asset(
            ...     serial_number="SN-001",
            ...     type_id=my_type_id,
            ...     asset_name="Test Station 1",
            ...     location="Lab A",
            ...     state=AssetState.OK
            ... )
        """
        asset = Asset(
            serial_number=serial_number,
            type_id=type_id,
            asset_name=asset_name,
            description=description,
            location=location,
            parent_asset_id=parent_asset_id,
            parent_serial_number=parent_serial_number,
            part_number=part_number,
            revision=revision,
            state=state,
            client_id=client_id,
            first_seen_date=first_seen_date,
            last_seen_date=last_seen_date,
            last_maintenance_date=last_maintenance_date,
            next_maintenance_date=next_maintenance_date,
            last_calibration_date=last_calibration_date,
            next_calibration_date=next_calibration_date,
            total_count=total_count,
            running_count=running_count,
        )
        result = self._repository.save(asset)
        if result:
            logger.info(f"ASSET_CREATED: {result.serial_number} (type_id={type_id}, name={asset_name})")
        return result

    def update_asset(self, asset: Asset) -> Optional[Asset]:
        """
        Update an existing asset.

        Args:
            asset: Asset object with updated fields

        Returns:
            Updated Asset object
        """
        result = self._repository.save(asset)
        if result:
            logger.info(f"ASSET_UPDATED: {result.serial_number} (id={result.asset_id})")
        return result

    def delete_asset(
        self,
        asset_id: Optional[str] = None,
        serial_number: Optional[str] = None
    ) -> bool:
        """
        Delete an asset by ID or serial number.

        Args:
            asset_id: Asset ID to delete
            serial_number: Asset serial number to delete

        Returns:
            True if successful
        """
        # Repository requires asset_id as first arg, but we handle both
        if asset_id:
            result = self._repository.delete(asset_id=asset_id, serial_number=serial_number)
            if result:
                logger.info(f"ASSET_DELETED: id={asset_id} (sn={serial_number})")
            return result
        elif serial_number:
            # Get asset by serial to get ID
            asset = self._repository.get_by_serial_number(serial_number)
            if asset and asset.asset_id:
                result = self._repository.delete(asset_id=asset.asset_id)
                if result:
                    logger.info(f"ASSET_DELETED: {serial_number} (id={asset.asset_id})")
                return result
        return False

    # =========================================================================
    # Status Operations
    # =========================================================================

    def get_status(
        self,
        asset_id: Optional[str] = None,
        serial_number: Optional[str] = None,
        translate: bool = True,
        culture_code: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get asset status including alarm information.

        This is the primary way to check if an asset is in alarm
        (needs calibration, maintenance, or has exceeded counts).

        Args:
            asset_id: Asset ID
            serial_number: Asset serial number
            translate: Whether to translate status messages
            culture_code: Culture for translations (e.g., 'en-US')

        Returns:
            Status dictionary with alarm info or None
        """
        return self._repository.get_status(
            asset_id=asset_id,
            serial_number=serial_number,
            translate=translate,
            culture_code=culture_code
        )

    # =========================================================================
    # State Management
    # =========================================================================

    def get_asset_state(self, asset_id: str) -> Optional[AssetState]:
        """
        Get the current state of an asset.

        Args:
            asset_id: Asset ID

        Returns:
            Current AssetState or None if not found
        """
        asset = self._repository.get_by_id(asset_id)
        return asset.state if asset else None

    def set_asset_state(
        self,
        state: AssetState,
        asset_id: Optional[str] = None,
        serial_number: Optional[str] = None
    ) -> bool:
        """
        Set the state of an asset.

        Args:
            state: New state
            asset_id: Asset ID
            serial_number: Asset serial number

        Returns:
            True if successful
        """
        result = self._repository.set_state(
            state=state,
            asset_id=asset_id,
            serial_number=serial_number
        )
        if result:
            identifier = serial_number or asset_id
            logger.info(f"ASSET_STATE_CHANGED: {identifier} (state={state.name})")
        return result

    def is_in_alarm(self, asset: Asset) -> bool:
        """
        Check if an asset is in alarm state.

        Uses get_status to determine alarm state.
        Consider using get_status directly for more detail.

        Args:
            asset: Asset to check

        Returns:
            True if asset is in alarm
        """
        status = self.get_status(
            asset_id=asset.asset_id,
            serial_number=asset.serial_number
        )
        if status:
            # Support both snake_case (preferred) and camelCase (backend) keys
            alarm_state = status.get("alarm_state") or status.get("alarmState", 0)
            return bool(alarm_state == AssetAlarmState.ALARM.value)
        return False

    def is_in_warning(self, asset: Asset) -> bool:
        """
        Check if an asset is in warning state.

        Args:
            asset: Asset to check

        Returns:
            True if asset is in warning
        """
        status = self.get_status(
            asset_id=asset.asset_id,
            serial_number=asset.serial_number
        )
        if status:
            # Support both snake_case (preferred) and camelCase (backend) keys
            alarm_state = status.get("alarm_state") or status.get("alarmState", 0)
            return bool(alarm_state == AssetAlarmState.WARNING.value)
        return False

    def get_assets_in_alarm(self) -> List[Asset]:
        """
        Get all assets that are in alarm state.

        Note: This requires checking status for each asset.
        For large datasets, consider using server-side filtering.

        Returns:
            List of assets in alarm
        """
        assets = self._repository.get_all()
        result = []
        for asset in assets:
            status = self.get_status(
                asset_id=asset.asset_id,
                serial_number=asset.serial_number
            )
            # Support both snake_case (preferred) and camelCase (backend) keys
            alarm_state = status.get("alarm_state") or status.get("alarmState") if status else None
            if alarm_state == AssetAlarmState.ALARM.value:
                result.append(asset)
        return result

    def get_assets_in_warning(self) -> List[Asset]:
        """
        Get all assets that are in warning state.

        Returns:
            List of assets in warning
        """
        assets = self._repository.get_all()
        result = []
        for asset in assets:
            status = self.get_status(
                asset_id=asset.asset_id,
                serial_number=asset.serial_number
            )
            # Support both snake_case (preferred) and camelCase (backend) keys
            alarm_state = status.get("alarm_state") or status.get("alarmState") if status else None
            if alarm_state == AssetAlarmState.WARNING.value:
                result.append(asset)
        return result

    # =========================================================================
    # Count Operations
    # =========================================================================

    def increment_count(
        self,
        asset_id: Optional[str] = None,
        serial_number: Optional[str] = None,
        amount: int = 1,
        increment_children: bool = False
    ) -> bool:
        """
        Increment the usage count of an asset.

        Args:
            asset_id: Asset ID
            serial_number: Asset serial number
            amount: Amount to increment by (default 1)
            increment_children: Also increment child asset counts

        Returns:
            True if successful
        """
        return self._repository.update_count(
            asset_id=asset_id,
            serial_number=serial_number,
            increment_by=amount,
            increment_children=increment_children
        )

    def reset_running_count(
        self,
        asset_id: Optional[str] = None,
        serial_number: Optional[str] = None,
        comment: Optional[str] = None
    ) -> bool:
        """
        Reset the running count of an asset.

        Args:
            asset_id: Asset ID
            serial_number: Asset serial number
            comment: Optional comment explaining reset

        Returns:
            True if successful
        """
        result = self._repository.reset_running_count(
            asset_id=asset_id,
            serial_number=serial_number,
            comment=comment
        )
        if result:
            identifier = serial_number or asset_id
            logger.info(f"ASSET_RUNNING_COUNT_RESET: {identifier}")
        return result

    # =========================================================================
    # Calibration & Maintenance
    # =========================================================================

    def record_calibration(
        self,
        asset_id: Optional[str] = None,
        serial_number: Optional[str] = None,
        comment: Optional[str] = None,
        calibration_date: Optional[datetime] = None
    ) -> bool:
        """
        Record a calibration event for an asset.

        This resets the calibration interval timer and logs the event.

        Args:
            asset_id: Asset ID
            serial_number: Asset serial number
            comment: Optional comment
            calibration_date: Date of calibration (default: now)

        Returns:
            True if successful
        """
        result = self._repository.post_calibration(
            asset_id=asset_id,
            serial_number=serial_number,
            date_time=calibration_date,
            comment=comment
        )
        if result:
            identifier = serial_number or asset_id
            logger.info(f"ASSET_CALIBRATED: {identifier}")
        return result

    def record_maintenance(
        self,
        asset_id: Optional[str] = None,
        serial_number: Optional[str] = None,
        comment: Optional[str] = None,
        maintenance_date: Optional[datetime] = None
    ) -> bool:
        """
        Record a maintenance event for an asset.

        This resets the maintenance interval timer and logs the event.

        Args:
            asset_id: Asset ID
            serial_number: Asset serial number
            comment: Optional comment
            maintenance_date: Date of maintenance (default: now)

        Returns:
            True if successful
        """
        result = self._repository.post_maintenance(
            asset_id=asset_id,
            serial_number=serial_number,
            date_time=maintenance_date,
            comment=comment
        )
        if result:
            identifier = serial_number or asset_id
            logger.info(f"ASSET_MAINTENANCE_RECORDED: {identifier}")
        return result

    # =========================================================================
    # Log Operations
    # =========================================================================

    def get_asset_log(
        self,
        filter_str: Optional[str] = None,
        top: Optional[int] = None
    ) -> List[AssetLog]:
        """
        Get asset log entries.

        Args:
            filter_str: Optional OData filter
            top: Max number of entries

        Returns:
            List of AssetLog entries
        """
        return self._repository.get_log(filter_str=filter_str, top=top)

    def add_log_message(
        self,
        asset_id: str,
        message: str,
        user: Optional[str] = None
    ) -> bool:
        """
        Add a message to the asset log.

        Args:
            asset_id: Asset ID
            message: Message text
            user: Optional user name

        Returns:
            True if successful
        """
        result = self._repository.post_message(asset_id, message, user)
        if result:
            logger.info(f"ASSET_LOG_MESSAGE_ADDED: id={asset_id}")
        return result

    # =========================================================================
    # Asset Types
    # =========================================================================

    def get_asset_types(self) -> List[AssetType]:
        """
        Get all asset types.

        Returns:
            List of AssetType objects
        """
        return self._repository.get_types()

    def create_asset_type(
        self,
        type_name: str,
        running_count_limit: Optional[int] = None,
        total_count_limit: Optional[int] = None,
        calibration_interval: Optional[float] = None,
        maintenance_interval: Optional[float] = None,
        warning_threshold: Optional[float] = None,
        alarm_threshold: Optional[float] = None,
        *,
        icon: Optional[str] = None,
    ) -> Optional[AssetType]:
        """
        Create a new asset type.

        Args:
            type_name: Name of the asset type (required)
            running_count_limit: Max running count before alarm triggers
            total_count_limit: Maximum total usage count
            calibration_interval: Days between calibrations (float)
            maintenance_interval: Days between maintenance (float)
            warning_threshold: Warning threshold percentage (0-100)
            alarm_threshold: Alarm threshold percentage (0-100)
            icon: Icon identifier string for UI display

        Returns:
            Created AssetType object, or None on failure
            
        Example:
            >>> asset_type = service.create_asset_type(
            ...     type_name="Test Station",
            ...     calibration_interval=365.0,
            ...     warning_threshold=80.0,
            ...     alarm_threshold=90.0
            ... )
        """
        asset_type = AssetType(
            type_name=type_name,
            running_count_limit=running_count_limit,
            total_count_limit=total_count_limit,
            calibration_interval=calibration_interval,
            maintenance_interval=maintenance_interval,
            warning_threshold=warning_threshold,
            alarm_threshold=alarm_threshold,
            icon=icon,
        )
        result = self._repository.save_type(asset_type)
        if result:
            logger.info(f"ASSET_TYPE_CREATED: {result.type_name} (id={result.type_id})")
        return result

    # =========================================================================
    # Sub-Assets
    # =========================================================================

    def get_child_assets(
        self,
        parent_id: Optional[str] = None,
        parent_serial: Optional[str] = None,
        level: Optional[int] = None
    ) -> List[Asset]:
        """
        Get child assets of a parent.

        Args:
            parent_id: Parent asset ID
            parent_serial: Parent asset serial number
            level: Optional depth level (None = all levels)

        Returns:
            List of child Asset objects
        """
        return self._repository.get_sub_assets(
            parent_id=parent_id,
            parent_serial=parent_serial,
            level=level
        )

    def add_child_asset(
        self,
        parent_serial: str,
        child_serial: str,
        child_type_id: UUID,
        child_name: Optional[str] = None,
        *,
        description: Optional[str] = None,
        location: Optional[str] = None,
        part_number: Optional[str] = None,
        revision: Optional[str] = None,
        state: AssetState = AssetState.OK,
    ) -> Optional[Asset]:
        """
        Create a new child asset under a parent.

        Args:
            parent_serial: Parent asset serial number (required)
            child_serial: New child asset serial number (required)
            child_type_id: Asset type UUID for child (required)
            child_name: Optional display name for child
            description: Optional description text
            location: Optional physical location
            part_number: Child asset part number
            revision: Child asset revision string
            state: Asset state (default: AssetState.OK)

        Returns:
            Created child Asset object, or None on failure
            
        Example:
            >>> child = service.add_child_asset(
            ...     parent_serial="PARENT-001",
            ...     child_serial="CHILD-001",
            ...     child_type_id=probe_type_id,
            ...     child_name="Probe A"
            ... )
        """
        child = Asset(
            serial_number=child_serial,
            type_id=child_type_id,
            asset_name=child_name,
            parent_serial_number=parent_serial,
            description=description,
            location=location,
            part_number=part_number,
            revision=revision,
            state=state,
        )
        result = self._repository.save(child)
        if result:
            logger.info(f"ASSET_CHILD_ADDED: {child_serial} (parent={parent_serial})")
        return result

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
        Upload a file attachment to an asset.

        ⚠️ Uses internal API - requires base_url to be set.

        Args:
            asset_id: Asset ID
            filename: Unique filename
            content: File content as bytes

        Returns:
            True if successful
        """
        result = self._repository.upload_file(
            asset_id=asset_id,
            filename=filename,
            content=content,
            base_url=self._base_url
        )
        if result:
            logger.info(f"ASSET_FILE_UPLOADED: id={asset_id} (filename={filename}, size={len(content)})")
        return result

    def upload_file_from_path(
        self,
        asset_id: str,
        file_path: Union[str, Path],
        filename: Optional[str] = None
    ) -> bool:
        """
        Upload a file from disk to an asset.

        Args:
            asset_id: Asset ID
            file_path: Path to the file to upload
            filename: Optional custom filename (defaults to original)

        Returns:
            True if successful
        """
        path = Path(file_path)
        with open(path, "rb") as f:
            content = f.read()
        return self.upload_file(
            asset_id=asset_id,
            filename=filename or path.name,
            content=content
        )

    def download_file(
        self,
        asset_id: str,
        filename: str
    ) -> Optional[bytes]:
        """
        Download a file attachment from an asset.

        Args:
            asset_id: Asset ID
            filename: Filename to download

        Returns:
            File content as bytes, or None if not found
        """
        return self._repository.download_file(
            asset_id=asset_id,
            filename=filename,
            base_url=self._base_url
        )

    def download_file_to_path(
        self,
        asset_id: str,
        filename: str,
        destination: Union[str, Path]
    ) -> bool:
        """
        Download a file from an asset to disk.

        Args:
            asset_id: Asset ID
            filename: Filename to download
            destination: Path to save the file

        Returns:
            True if successful
        """
        content = self.download_file(asset_id=asset_id, filename=filename)
        if content:
            with open(destination, "wb") as f:
                f.write(content)
            return True
        return False

    def list_files(self, asset_id: str) -> List[str]:
        """
        List all file attachments for an asset.

        Args:
            asset_id: Asset ID

        Returns:
            List of filenames
        """
        return self._repository.list_files(
            asset_id=asset_id,
            base_url=self._base_url
        )

    def delete_files(
        self,
        asset_id: str,
        filenames: List[str]
    ) -> bool:
        """
        Delete file attachments from an asset.

        Args:
            asset_id: Asset ID
            filenames: List of filenames to delete

        Returns:
            True if successful
        """
        return self._repository.delete_files(
            asset_id=asset_id,
            filenames=filenames,
            base_url=self._base_url
        )
