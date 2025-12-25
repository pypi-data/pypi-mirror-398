"""
Client Configuration Management

Handles configuration for pyWATS Client instances including:
- Server connection settings
- Station configuration (single and multi-station modes)
- Converter configurations
- Sync intervals
- Instance identification
"""

import json
import os
import socket
import uuid
from pathlib import Path
from dataclasses import dataclass, field, asdict, fields
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class ConverterConfig:
    """
    Configuration for a single converter instance.
    
    This represents a converter assigned to a watch folder.
    Each folder has exactly one converter.
    
    Converter Types:
        - "file": Triggered when files are created/modified (FileConverter)
        - "folder": Triggered when folder is ready (FolderConverter)
        - "scheduled": Runs on timer/cron (ScheduledConverter)
    """
    # Required fields
    name: str                    # Human-readable name
    module_path: str             # Python module path (e.g., "my_converter.CSVConverter")
    
    # Watch folder (for file/folder converters)
    watch_folder: str = ""       # Folder to watch for files/folders
    done_folder: str = ""        # Folder for successfully converted files
    error_folder: str = ""       # Folder for failed files
    pending_folder: str = ""     # Folder for suspended files (retry)
    
    # Converter type
    converter_type: str = "file"  # "file", "folder", or "scheduled"
    
    # State
    enabled: bool = True
    
    # Configuration arguments (passed to converter)
    arguments: Dict[str, Any] = field(default_factory=dict)
    
    # File/folder patterns (for pre-filtering)
    file_patterns: List[str] = field(default_factory=lambda: ["*.*"])
    folder_patterns: List[str] = field(default_factory=lambda: ["*"])
    
    # Validation thresholds
    alarm_threshold: float = 0.5    # Warn below this (but allow)
    reject_threshold: float = 0.2   # Reject below this
    
    # Retry settings
    max_retries: int = 3
    retry_delay_seconds: int = 60
    
    # Scheduled converter settings
    schedule_interval_seconds: Optional[int] = None  # For scheduled converters
    cron_expression: Optional[str] = None            # For scheduled converters
    run_on_startup: bool = False                     # Run immediately on load
    
    # Folder converter settings
    readiness_marker: str = "COMPLETE.marker"  # Marker file for folder readiness
    min_file_count: Optional[int] = None       # Min files before checking readiness
    
    # Post-processing
    post_action: str = "move"  # "move", "delete", "archive", "keep"
    archive_folder: str = ""   # For "archive" post action
    
    # Metadata
    description: str = ""
    author: str = ""
    version: str = "1.0.0"
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConverterConfig":
        # Filter to only known fields for forward compatibility
        known_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in known_fields}
        return cls(**filtered_data)
    
    @property
    def is_file_converter(self) -> bool:
        """True if this is a file-based converter"""
        return self.converter_type == "file"
    
    @property
    def is_folder_converter(self) -> bool:
        """True if this is a folder-based converter"""
        return self.converter_type == "folder"
    
    @property
    def is_scheduled_converter(self) -> bool:
        """True if this is a scheduled converter"""
        return self.converter_type == "scheduled"
    
    def validate(self) -> List[str]:
        """
        Validate the configuration.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        if not self.name:
            errors.append("name is required")
        
        if not self.module_path:
            errors.append("module_path is required")
        
        if self.converter_type not in ("file", "folder", "scheduled"):
            errors.append(f"Invalid converter_type: {self.converter_type}")
        
        # File/folder converters need a watch folder
        if self.converter_type in ("file", "folder") and not self.watch_folder:
            errors.append("watch_folder is required for file/folder converters")
        
        # Scheduled converters need a schedule
        if self.converter_type == "scheduled":
            if not self.schedule_interval_seconds and not self.cron_expression:
                errors.append("Scheduled converters need schedule_interval_seconds or cron_expression")
        
        # Threshold validation
        if not (0.0 <= self.alarm_threshold <= 1.0):
            errors.append(f"alarm_threshold must be between 0.0 and 1.0")
        
        if not (0.0 <= self.reject_threshold <= 1.0):
            errors.append(f"reject_threshold must be between 0.0 and 1.0")
        
        if self.reject_threshold > self.alarm_threshold:
            errors.append("reject_threshold must be <= alarm_threshold")
        
        return errors


@dataclass
class ProxyConfig:
    """Proxy configuration"""
    enabled: bool = False
    host: str = ""
    port: int = 8080
    username: str = ""
    password: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProxyConfig":
        return cls(**data)


@dataclass
class StationPreset:
    """
    Configuration for a saved station preset.
    
    Used in multi-station mode to manage multiple stations from a single client.
    """
    key: str                      # Unique identifier within registry
    name: str                     # Station name (machineName in reports)
    location: str = ""            # Location string
    purpose: str = "Production"   # Purpose string
    description: str = ""         # Optional description
    is_default: bool = False      # Is this the default station?
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StationPreset":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ClientConfig:
    """
    Main configuration for pyWATS Client instance.
    
    Each instance has its own configuration file allowing
    multiple instances to run on the same machine.
    
    Station vs Client Identity:
    - instance_name: The name of this client installation
    - station_name: The station identity used in reports (machineName)
    
    By default, these can be the same. However, a single client can
    represent multiple stations (hub mode) by using station_presets.
    """
    # Instance identification (the client installation)
    instance_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    instance_name: str = "WATS Client"
    
    # Server connection
    service_address: str = ""
    api_token: str = ""
    username: str = ""
    
    # Station identification (the test station identity in reports)
    station_name: str = ""               # Default station name for reports
    location: str = ""                   # Default location
    purpose: str = ""                    # Default purpose
    station_description: str = ""        # Optional description
    auto_detect_location: bool = False   # Use GPS/network location
    include_station_in_reports: bool = True  # Apply station info to reports
    
    # Station name source: "hostname", "config", "manual"
    # - hostname: Use computer hostname as station name
    # - config: Use station_name from config
    # - manual: User must specify for each report
    station_name_source: str = "hostname"
    
    # Multi-station mode (hub)
    multi_station_enabled: bool = False      # Enable multi-station support
    station_presets: List[StationPreset] = field(default_factory=list)
    active_station_key: str = ""             # Key of currently active preset
    
    # Serial Number Handler settings
    sn_mode: str = "Manual Entry"  # "Manual Entry", "Auto-increment", "Barcode Scanner", "External Source"
    sn_prefix: str = ""
    sn_start: int = 1
    sn_padding: int = 6
    sn_com_port: str = "Auto-detect"
    sn_terminator: str = "Enter (CR)"
    sn_validate_format: bool = False
    sn_pattern: str = ""
    sn_check_duplicates: bool = True
    
    # Proxy settings (simplified fields for GUI binding)
    proxy_mode: str = "system"  # "none", "system", "manual"
    proxy_host: str = ""
    proxy_port: int = 8080
    proxy_auth: bool = False
    proxy_username: str = ""
    proxy_password: str = ""
    proxy_bypass: str = ""
    
    # Legacy proxy config (for backward compatibility)
    proxy: ProxyConfig = field(default_factory=ProxyConfig)
    
    # Sync settings
    sync_interval_seconds: int = 300  # 5 minutes
    process_sync_enabled: bool = True
    
    # Offline storage
    reports_folder: str = "reports"
    offline_queue_enabled: bool = True
    max_retry_attempts: int = 5
    retry_interval_seconds: int = 60
    
    # Converter settings
    converters_folder: str = "converters"
    converters: List[ConverterConfig] = field(default_factory=list)
    converters_enabled: bool = True
    
    # Yield monitor settings
    yield_monitor_enabled: bool = False
    yield_threshold: float = 95.0
    
    # Location services
    location_services_enabled: bool = False
    
    # Software Distribution settings
    software_auto_update: bool = False
    
    # GUI tab visibility settings - control which tabs are shown
    show_software_tab: bool = True
    show_sn_handler_tab: bool = True
    show_converters_tab: bool = True
    show_location_tab: bool = True
    show_proxy_tab: bool = True
    show_asset_tab: bool = True
    show_rootcause_tab: bool = True
    show_production_tab: bool = True
    show_product_tab: bool = True
    
    # Connection state - persist connected state
    auto_connect: bool = True  # Always try to connect on startup
    was_connected: bool = False  # Remember last connection state
    
    # Service settings
    service_auto_start: bool = True  # Start service on system startup
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "client.log"
    
    # GUI settings
    start_minimized: bool = False
    minimize_to_tray: bool = True
    
    # Internal state (not saved)
    _config_path: Optional[Path] = field(default=None, repr=False)
    
    def __post_init__(self):
        """Ensure nested objects are properly initialized"""
        if isinstance(self.proxy, dict):
            self.proxy = ProxyConfig.from_dict(self.proxy)
        if self.converters:
            converted = []
            for c in self.converters:
                if isinstance(c, dict):
                    converted.append(ConverterConfig.from_dict(c))
                else:
                    converted.append(c)
            self.converters = converted
        # Convert station presets
        if self.station_presets:
            converted_presets = []
            for sp in self.station_presets:
                if isinstance(sp, dict):
                    converted_presets.append(StationPreset.from_dict(sp))
                else:
                    converted_presets.append(sp)
            self.station_presets = converted_presets
    
    # =========================================================================
    # Station Properties and Methods
    # =========================================================================
    
    def get_effective_station_name(self) -> str:
        """
        Get the effective station name to use for reports.
        
        Priority:
        1. Active station preset (if multi-station enabled)
        2. Configured station_name
        3. Computer hostname (if station_name_source is "hostname")
        
        Returns:
            Station name to use for reports
        """
        # Check multi-station mode first
        if self.multi_station_enabled and self.active_station_key:
            preset = self.get_active_station_preset()
            if preset:
                return preset.name
        
        # Use configured station name
        if self.station_name:
            return self.station_name
        
        # Fall back to hostname if configured
        if self.station_name_source == "hostname":
            return socket.gethostname().upper()
        
        return ""
    
    def get_effective_location(self) -> str:
        """Get the effective location for reports."""
        if self.multi_station_enabled and self.active_station_key:
            preset = self.get_active_station_preset()
            if preset:
                return preset.location
        return self.location
    
    def get_effective_purpose(self) -> str:
        """Get the effective purpose for reports."""
        if self.multi_station_enabled and self.active_station_key:
            preset = self.get_active_station_preset()
            if preset:
                return preset.purpose
        return self.purpose
    
    def get_active_station_preset(self) -> Optional[StationPreset]:
        """Get the currently active station preset."""
        if not self.active_station_key:
            return None
        for preset in self.station_presets:
            if preset.key == self.active_station_key:
                return preset
        return None
    
    def set_active_station(self, key: str) -> bool:
        """
        Set the active station by key.
        
        Args:
            key: Key of the station preset to activate
            
        Returns:
            True if successful, False if key not found
        """
        for preset in self.station_presets:
            if preset.key == key:
                self.active_station_key = key
                return True
        return False
    
    def add_station_preset(self, preset: StationPreset) -> None:
        """Add a station preset to the list."""
        # Remove existing preset with same key
        self.station_presets = [p for p in self.station_presets if p.key != preset.key]
        self.station_presets.append(preset)
        
        # If this is the first preset, make it active
        if len(self.station_presets) == 1:
            self.active_station_key = preset.key
    
    def remove_station_preset(self, key: str) -> bool:
        """
        Remove a station preset by key.
        
        Args:
            key: Key of the preset to remove
            
        Returns:
            True if removed, False if not found
        """
        original_count = len(self.station_presets)
        self.station_presets = [p for p in self.station_presets if p.key != key]
        
        if len(self.station_presets) < original_count:
            # Update active key if needed
            if self.active_station_key == key:
                self.active_station_key = (
                    self.station_presets[0].key if self.station_presets else ""
                )
            return True
        return False
    
    @property
    def identifier(self) -> str:
        """Get unique identifier for this instance"""
        # Similar to the MAC-based identifier shown in the WATS Client
        import hashlib
        return hashlib.md5(self.instance_id.encode()).hexdigest()[:16].upper()
    
    @property
    def formatted_identifier(self) -> str:
        """Get formatted identifier like 4C:5F:70:D6:2F:F4"""
        ident = self.identifier
        return ":".join(ident[i:i+2] for i in range(0, min(len(ident), 12), 2))
    
    @property
    def data_path(self) -> Path:
        """Get the base data path for this instance.
        
        This is the directory containing config, reports, logs, etc.
        """
        if self._config_path:
            return self._config_path.parent
        # Fallback to default location
        if os.name == 'nt':
            return Path(os.environ.get('APPDATA', '')) / 'pyWATS_Client'
        return Path.home() / '.config' / 'pywats_client'
    
    def get_reports_path(self) -> Path:
        """Get absolute path to reports folder"""
        if os.path.isabs(self.reports_folder):
            return Path(self.reports_folder)
        if self._config_path:
            return self._config_path.parent / self.reports_folder
        return Path(self.reports_folder)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = {
            "instance_id": self.instance_id,
            "instance_name": self.instance_name,
            "service_address": self.service_address,
            "api_token": self.api_token,
            # Station identification
            "station_name": self.station_name,
            "location": self.location,
            "purpose": self.purpose,
            "station_description": self.station_description,
            "auto_detect_location": self.auto_detect_location,
            "include_station_in_reports": self.include_station_in_reports,
            "station_name_source": self.station_name_source,
            # Multi-station mode
            "multi_station_enabled": self.multi_station_enabled,
            "station_presets": [sp.to_dict() for sp in self.station_presets],
            "active_station_key": self.active_station_key,
            # Serial Number Handler
            "sn_mode": self.sn_mode,
            "sn_prefix": self.sn_prefix,
            "sn_start": self.sn_start,
            "sn_padding": self.sn_padding,
            "sn_com_port": self.sn_com_port,
            "sn_terminator": self.sn_terminator,
            "sn_validate_format": self.sn_validate_format,
            "sn_pattern": self.sn_pattern,
            "sn_check_duplicates": self.sn_check_duplicates,
            # Proxy settings
            "proxy_mode": self.proxy_mode,
            "proxy_host": self.proxy_host,
            "proxy_port": self.proxy_port,
            "proxy_auth": self.proxy_auth,
            "proxy_username": self.proxy_username,
            "proxy_password": self.proxy_password,
            "proxy_bypass": self.proxy_bypass,
            "proxy": self.proxy.to_dict(),
            "sync_interval_seconds": self.sync_interval_seconds,
            "process_sync_enabled": self.process_sync_enabled,
            "reports_folder": self.reports_folder,
            "offline_queue_enabled": self.offline_queue_enabled,
            "max_retry_attempts": self.max_retry_attempts,
            "retry_interval_seconds": self.retry_interval_seconds,
            "converters_folder": self.converters_folder,
            "converters": [c.to_dict() for c in self.converters],
            "converters_enabled": self.converters_enabled,
            "yield_monitor_enabled": self.yield_monitor_enabled,
            "yield_threshold": self.yield_threshold,
            "location_services_enabled": self.location_services_enabled,
            "software_auto_update": self.software_auto_update,
            # GUI tab visibility
            "show_software_tab": self.show_software_tab,
            "show_sn_handler_tab": self.show_sn_handler_tab,
            "show_converters_tab": self.show_converters_tab,
            "show_location_tab": self.show_location_tab,
            "show_proxy_tab": self.show_proxy_tab,
            "show_asset_tab": self.show_asset_tab,
            "show_rootcause_tab": self.show_rootcause_tab,
            "show_production_tab": self.show_production_tab,
            "show_product_tab": self.show_product_tab,
            "auto_connect": self.auto_connect,
            "was_connected": self.was_connected,
            "service_auto_start": self.service_auto_start,
            "log_level": self.log_level,
            "log_file": self.log_file,
            "start_minimized": self.start_minimized,
            "minimize_to_tray": self.minimize_to_tray,
        }
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ClientConfig":
        """Create from dictionary, filtering out unknown fields"""
        # Get valid field names from the class
        valid_fields = {f.name for f in fields(cls)}
        # Filter data to only include valid fields
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)
    
    def save(self, path: Optional[Path] = None) -> None:
        """Save configuration to file"""
        save_path = path or self._config_path
        if not save_path:
            raise ValueError("No configuration path specified")
        
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2)
        
        self._config_path = save_path
    
    @classmethod
    def load(cls, path: Path) -> "ClientConfig":
        """Load configuration from file"""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        config = cls.from_dict(data)
        config._config_path = path
        return config
    
    @classmethod
    def load_or_create(cls, path: Path) -> "ClientConfig":
        """Load existing configuration or create new one"""
        path = Path(path)
        if path.exists():
            return cls.load(path)
        
        config = cls()
        config._config_path = path
        config.save()
        return config


def get_default_config_path(instance_id: Optional[str] = None) -> Path:
    """
    Get default configuration path for an instance.
    
    On Windows: %APPDATA%/pyWATS_Client/
    On Linux/Mac: ~/.config/pywats_client/
    """
    if os.name == 'nt':
        base = Path(os.environ.get('APPDATA', '')) / 'pyWATS_Client'
    else:
        base = Path.home() / '.config' / 'pywats_client'
    
    if instance_id:
        return base / f"config_{instance_id}.json"
    return base / "config.json"


def get_all_instance_configs() -> List[Path]:
    """Get all configuration files for all instances"""
    if os.name == 'nt':
        base = Path(os.environ.get('APPDATA', '')) / 'pyWATS_Client'
    else:
        base = Path.home() / '.config' / 'pywats_client'
    
    if not base.exists():
        return []
    
    return list(base.glob("config*.json"))
