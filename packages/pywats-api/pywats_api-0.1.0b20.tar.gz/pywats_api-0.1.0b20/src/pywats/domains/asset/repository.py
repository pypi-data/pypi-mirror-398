"""Asset repository - data access layer.

Handles all API calls for asset management.
"""
from typing import Optional, List, Dict, Any, Union, TYPE_CHECKING, cast
from datetime import datetime
import logging

if TYPE_CHECKING:
    from ...core.client import HttpClient
    from ...core.exceptions import ErrorHandler

from .models import Asset, AssetType, AssetLog
from .enums import AssetState

logger = logging.getLogger(__name__)


class AssetRepository:
    """
    Asset data access layer.

    Handles all HTTP API calls for asset CRUD operations.
    """

    def __init__(
        self, 
        http_client: "HttpClient",
        error_handler: Optional["ErrorHandler"] = None
    ):
        """
        Initialize with HTTP client.

        Args:`n            http_client: HttpClient instance for making requests
            error_handler: Optional ErrorHandler for error handling (default: STRICT mode)
        """
        self._http_client = http_client
        # Import here to avoid circular imports
        from ...core.exceptions import ErrorHandler, ErrorMode
        self._error_handler = error_handler or ErrorHandler(ErrorMode.STRICT)

    # =========================================================================
    # Asset CRUD
    # =========================================================================

    def get_all(
        self,
        filter_str: Optional[str] = None,
        orderby: Optional[str] = None,
        top: Optional[int] = None,
        skip: Optional[int] = None
    ) -> List[Asset]:
        """
        Get all assets with optional OData filtering.

        GET /api/Asset

        Args:
            filter_str: OData filter string (e.g., "assetType eq 'Station'")
            orderby: OData order by string (e.g., "name asc")
            top: Maximum number of assets to return
            skip: Number of assets to skip (for pagination)

        Returns:
            List of Asset objects, empty list if none found
        """
        logger.debug(f"Fetching assets (filter={filter_str}, top={top})")
        params: Dict[str, Any] = {}
        if filter_str:
            params["$filter"] = filter_str
        if orderby:
            params["$orderby"] = orderby
        if top:
            params["$top"] = top
        if skip:
            params["$skip"] = skip

        response = self._http_client.get(
            "/api/Asset",
            params=params if params else None
        )
        if response.is_success and response.data:
            assets = [Asset.model_validate(item) for item in response.data]
            logger.info(f"Retrieved {len(assets)} assets")
            return assets
        logger.warning("No assets found or empty response")
        return []

    def get_by_id(self, asset_id: str) -> Optional[Asset]:
        """
        Get an asset by its ID.

        GET /api/Asset/{assetId}

        Args:
            asset_id: Asset UUID

        Returns:
            Asset object or None if not found
        """
        logger.debug(f"Fetching asset: {asset_id}")
        response = self._http_client.get(f"/api/Asset/{asset_id}")
        if response.is_success and response.data:
            asset = Asset.model_validate(response.data)
            logger.info(f"Retrieved asset: {asset_id}")
            return asset
        logger.info(f"Asset not found: {asset_id}")
        return None

    def get_by_serial_number(self, serial_number: str) -> Optional[Asset]:
        """
        Get an asset by its serial number.

        GET /api/Asset/{serialNumber}

        Args:
            serial_number: Asset serial number

        Returns:
            Asset object or None if not found
        """
        response = self._http_client.get(f"/api/Asset/{serial_number}")
        if response.is_success and response.data:
            return Asset.model_validate(response.data)
        return None

    def save(self, asset: Union[Asset, Dict[str, Any]]) -> Optional[Asset]:
        """
        Create a new asset or update an existing one.

        PUT /api/Asset

        Args:
            asset: Asset object or dict with asset data

        Returns:
            Created/updated Asset object, or None on failure
        """
        if isinstance(asset, Asset):
            data = asset.model_dump(mode="json", by_alias=True, exclude_none=True)
        else:
            data = asset
        response = self._http_client.put("/api/Asset", data=data)
        if response.is_success and response.data:
            return Asset.model_validate(response.data)
        return None

    def delete(self, asset_id: str, serial_number: Optional[str] = None) -> bool:
        """
        Delete an asset by ID or serial number.

        DELETE /api/Asset
        
        Args:
            asset_id: Asset ID (GUID)
            serial_number: Asset serial number (alternative to asset_id)

        Returns:
            True if deleted successfully, False otherwise
        """
        params: Dict[str, Any] = {}
        if asset_id:
            params["id"] = asset_id
        if serial_number:
            params["serialNumber"] = serial_number
        response = self._http_client.delete("/api/Asset", params=params)
        return response.is_success

    # =========================================================================
    # Asset Status and State
    # =========================================================================

    def get_status(
        self,
        asset_id: Optional[str] = None,
        serial_number: Optional[str] = None,
        translate: bool = True,
        culture_code: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get the current status of an asset including alarm state.

        GET /api/Asset/Status
        
        The status includes:
        - state: Current asset state (AssetState)
        - alarmState: 0=OK, 1=Warning, 2=Alarm
        - message: Human-readable status message
        - runningCount, totalCount, etc.
        
        Args:
            asset_id: Asset ID
            serial_number: Asset serial number (alternative)
            translate: Whether to translate messages
            culture_code: Culture for translations (e.g., 'zh-CN')

        Returns:
            Dict with status information, or None if not found
        """
        params: Dict[str, Any] = {}
        if asset_id:
            params["id"] = asset_id
        if serial_number:
            params["serialNumber"] = serial_number
        if not translate:
            params["translate"] = "false"
        if culture_code:
            params["cultureCode"] = culture_code
            
        response = self._http_client.get("/api/Asset/Status", params=params)
        if response.is_success and response.data:
            return cast(Dict[str, Any], response.data)
        return None

    def set_state(
        self,
        state: Union[AssetState, int],
        asset_id: Optional[str] = None,
        serial_number: Optional[str] = None
    ) -> bool:
        """
        Set the state of an asset.

        PUT /api/Asset/State
        
        Args:
            state: New state (0-6)
            asset_id: Asset ID
            serial_number: Asset serial number (alternative)

        Returns:
            True if state was set successfully, False otherwise
        """
        state_value = state.value if isinstance(state, AssetState) else state
        params: Dict[str, Any] = {"state": state_value}
        if asset_id:
            params["id"] = asset_id
        if serial_number:
            params["serialNumber"] = serial_number
        response = self._http_client.put("/api/Asset/State", params=params)
        return response.is_success

    # =========================================================================
    # Asset Count
    # =========================================================================

    def update_count(
        self,
        asset_id: Optional[str] = None,
        serial_number: Optional[str] = None,
        total_count: Optional[int] = None,
        increment_by: Optional[int] = None,
        increment_children: bool = False
    ) -> bool:
        """
        Increment the running and total count on an asset.

        PUT /api/Asset/Count
        
        Args:
            asset_id: Asset ID
            serial_number: Asset serial number (alternative)
            total_count: New total count (calculates increment)
            increment_by: Direct increment value
            increment_children: Also increment child assets

        Returns:
            True if count was updated successfully, False otherwise
        """
        params: Dict[str, Any] = {}
        if asset_id:
            params["id"] = asset_id
        if serial_number:
            params["serialNumber"] = serial_number
        if total_count is not None:
            params["totalCount"] = total_count
        if increment_by is not None:
            params["incrementBy"] = increment_by
        if increment_children:
            params["incrementChildren"] = "true"
        response = self._http_client.put("/api/Asset/Count", params=params)
        return response.is_success

    def reset_running_count(
        self,
        asset_id: Optional[str] = None,
        serial_number: Optional[str] = None,
        comment: Optional[str] = None
    ) -> bool:
        """
        Reset the running count to 0.

        POST /api/Asset/ResetRunningCount
        
        Args:
            asset_id: Asset ID
            serial_number: Asset serial number (alternative)
            comment: Log message

        Returns:
            True if running count was reset successfully, False otherwise
        """
        params: Dict[str, Any] = {}
        if asset_id:
            params["id"] = asset_id
        if serial_number:
            params["serialNumber"] = serial_number
        if comment:
            params["comment"] = comment
        response = self._http_client.post(
            "/api/Asset/ResetRunningCount",
            params=params
        )
        return response.is_success

    # =========================================================================
    # Calibration
    # =========================================================================

    def post_calibration(
        self,
        asset_id: Optional[str] = None,
        serial_number: Optional[str] = None,
        date_time: Optional[datetime] = None,
        comment: Optional[str] = None
    ) -> bool:
        """
        Inform that an asset has been calibrated.

        POST /api/Asset/Calibration
        
        This resets the running count and updates the calibration dates.
        
        Args:
            asset_id: Asset ID
            serial_number: Asset serial number (alternative)
            date_time: Calibration date (default: now)
            comment: Log message

        Returns:
            True if calibration was recorded successfully, False otherwise
        """
        params: Dict[str, Any] = {}
        if asset_id:
            params["id"] = asset_id
        if serial_number:
            params["serialNumber"] = serial_number
        if date_time:
            params["dateTime"] = date_time.isoformat()
        if comment:
            params["comment"] = comment
        response = self._http_client.post("/api/Asset/Calibration", params=params)
        return response.is_success

    # =========================================================================
    # Maintenance
    # =========================================================================

    def post_maintenance(
        self,
        asset_id: Optional[str] = None,
        serial_number: Optional[str] = None,
        date_time: Optional[datetime] = None,
        comment: Optional[str] = None
    ) -> bool:
        """
        Inform that an asset has had maintenance.

        POST /api/Asset/Maintenance
        
        Args:
            asset_id: Asset ID
            serial_number: Asset serial number (alternative)
            date_time: Maintenance date (default: now)
            comment: Log message

        Returns:
            True if maintenance was recorded successfully, False otherwise
        """
        params: Dict[str, Any] = {}
        if asset_id:
            params["id"] = asset_id
        if serial_number:
            params["serialNumber"] = serial_number
        if date_time:
            params["dateTime"] = date_time.isoformat()
        if comment:
            params["comment"] = comment
        response = self._http_client.post("/api/Asset/Maintenance", params=params)
        return response.is_success

    # =========================================================================
    # Asset Log
    # =========================================================================

    def get_log(
        self,
        filter_str: Optional[str] = None,
        orderby: Optional[str] = None,
        top: Optional[int] = None,
        skip: Optional[int] = None
    ) -> List[AssetLog]:
        """
        Get asset log records.

        GET /api/Asset/Log

        Args:
            filter_str: OData filter string
            orderby: OData order by string
            top: Maximum number of log entries to return
            skip: Number of entries to skip (for pagination)

        Returns:
            List of AssetLog objects, empty list if none found
        """
        params: Dict[str, Any] = {}
        if filter_str:
            params["$filter"] = filter_str
        if orderby:
            params["$orderby"] = orderby
        if top:
            params["$top"] = top
        if skip:
            params["$skip"] = skip
        response = self._http_client.get(
            "/api/Asset/Log",
            params=params if params else None
        )
        if response.is_success and response.data:
            return [AssetLog.model_validate(item) for item in response.data]
        return []

    def post_message(
        self,
        asset_id: str,
        message: str,
        user: Optional[str] = None
    ) -> bool:
        """
        Post a message to the asset log.

        POST /api/Asset/Message

        Args:
            asset_id: Asset ID
            message: Log message to post
            user: User who posted the message (optional)

        Returns:
            True if message was posted successfully, False otherwise
        """
        data: Dict[str, Any] = {"assetId": asset_id, "comment": message}
        if user:
            data["user"] = user
        response = self._http_client.post("/api/Asset/Message", data=data)
        return response.is_success

    # =========================================================================
    # Asset Types
    # =========================================================================

    def get_types(
        self,
        filter_str: Optional[str] = None,
        top: Optional[int] = None
    ) -> List[AssetType]:
        """
        Get all asset types.

        GET /api/Asset/Types

        Args:
            filter_str: OData filter string
            top: Maximum number of types to return

        Returns:
            List of AssetType objects, empty list if none found
        """
        params: Dict[str, Any] = {}
        if filter_str:
            params["$filter"] = filter_str
        if top:
            params["$top"] = top
        response = self._http_client.get(
            "/api/Asset/Types",
            params=params if params else None
        )
        if response.is_success and response.data:
            return [AssetType.model_validate(item) for item in response.data]
        return []

    def save_type(
        self,
        asset_type: Union[AssetType, Dict[str, Any]]
    ) -> Optional[AssetType]:
        """
        Create or update an asset type.

        PUT /api/Asset/Types

        Args:
            asset_type: AssetType object or dict with type data

        Returns:
            Created/updated AssetType object, or None on failure
        """
        if isinstance(asset_type, AssetType):
            data = asset_type.model_dump(by_alias=True, exclude_none=True)
        else:
            data = asset_type
        response = self._http_client.put("/api/Asset/Types", data=data)
        if response.is_success and response.data:
            return AssetType.model_validate(response.data)
        return None

    # =========================================================================
    # Sub-Assets
    # =========================================================================

    def get_sub_assets(
        self,
        parent_id: Optional[str] = None,
        parent_serial: Optional[str] = None,
        level: Optional[int] = None
    ) -> List[Asset]:
        """
        Get child assets of a parent asset.

        GET /api/Asset/SubAssets
        
        Args:
            parent_id: Parent asset ID
            parent_serial: Parent asset serial number (alternative)
            level: How many levels deep (0=all, 1=direct children)

        Returns:
            List of child Asset objects, empty list if none found
        """
        params: Dict[str, Any] = {}
        if parent_id:
            params["id"] = parent_id
        if parent_serial:
            params["serialNumber"] = parent_serial
        if level is not None:
            params["level"] = level
        response = self._http_client.get("/api/Asset/SubAssets", params=params)
        if response.is_success and response.data:
            return [Asset.model_validate(item) for item in response.data]
        return []

    # =========================================================================
    # File Operations - Delegated to Internal Repository
    # =========================================================================

    def upload_file(
        self,
        asset_id: str,
        filename: str,
        content: bytes,
        base_url: str
    ) -> bool:
        """
        Upload a file to an asset.

        ⚠️ INTERNAL API - Delegated to AssetRepositoryInternal.
        
        Note: This method is deprecated. Use AssetServiceInternal instead.
        
        Args:
            asset_id: Asset ID
            filename: Unique filename
            content: File content as bytes
            base_url: Base URL for Referer header

        Returns:
            True if file was uploaded successfully, False otherwise
        """
        from .repository_internal import AssetRepositoryInternal
        internal_repo = AssetRepositoryInternal(self._http_client, base_url)
        return internal_repo.upload_file(asset_id, filename, content)

    def download_file(
        self,
        asset_id: str,
        filename: str,
        base_url: str
    ) -> Optional[bytes]:
        """
        Download a file from an asset.

        ⚠️ INTERNAL API - Delegated to AssetRepositoryInternal.
        
        Note: This method is deprecated. Use AssetServiceInternal instead.
        
        Args:
            asset_id: Asset ID
            filename: Filename to download
            base_url: Base URL for Referer header
            
        Returns:
            File content as bytes, or None if not found
        """
        from .repository_internal import AssetRepositoryInternal
        internal_repo = AssetRepositoryInternal(self._http_client, base_url)
        return internal_repo.download_file(asset_id, filename)

    def list_files(self, asset_id: str, base_url: str) -> List[str]:
        """
        List all files attached to an asset.

        ⚠️ INTERNAL API - Delegated to AssetRepositoryInternal.
        
        Note: This method is deprecated. Use AssetServiceInternal instead.
        
        Args:
            asset_id: Asset ID
            base_url: Base URL for Referer header
            
        Returns:
            List of filenames
        """
        from .repository_internal import AssetRepositoryInternal
        internal_repo = AssetRepositoryInternal(self._http_client, base_url)
        return internal_repo.list_files(asset_id)

    def delete_files(
        self,
        asset_id: str,
        filenames: List[str],
        base_url: str
    ) -> bool:
        """
        Delete files from an asset.

        ⚠️ INTERNAL API - Delegated to AssetRepositoryInternal.
        
        Note: This method is deprecated. Use AssetServiceInternal instead.
        
        Args:
            asset_id: Asset ID
            filenames: List of filenames to delete
            base_url: Base URL for Referer header

        Returns:
            True if files were deleted successfully, False otherwise
        """
        from .repository_internal import AssetRepositoryInternal
        internal_repo = AssetRepositoryInternal(self._http_client, base_url)
        return internal_repo.delete_files(asset_id, filenames)