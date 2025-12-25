"""
Settings Manager for pyWATS Client Application

Handles persistent storage and retrieval of application settings
such as folder paths, monitoring rules, converter configurations, etc.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, List, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class MonitorFolder:
    """Configuration for a folder to monitor"""
    path: str
    enabled: bool = True
    converter_type: str = ""
    recursive: bool = False
    delete_after_convert: bool = False
    auto_upload: bool = True
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MonitorFolder":
        """Create from dictionary"""
        return cls(**data)


@dataclass
class ConverterConfig:
    """Configuration for a converter"""
    name: str
    type: str
    enabled: bool = True
    options: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConverterConfig":
        """Create from dictionary"""
        return cls(**data)


@dataclass
class ApplicationSettings:
    """Application-wide settings"""
    # Server and API
    server_url: str = ""  # User must configure - e.g., https://yourcompany.wats.com
    api_token: str = ""
    check_ssl: bool = True
    
    # Connection
    connection_check_interval: int = 30  # seconds
    reconnect_delay: int = 5  # seconds
    max_reconnect_attempts: int = 5
    
    # Paths
    data_folder: str = "./data"
    queue_folder: str = "./queue"
    reports_folder: str = "./reports"
    converters_folder: str = "./converters"
    
    # Monitoring
    monitor_folders: List[Dict[str, Any]] = field(default_factory=list)
    
    # Converters
    enabled_converters: List[Dict[str, Any]] = field(default_factory=list)
    
    # Auto-upload settings
    auto_upload_reports: bool = True
    auto_upload_interval: int = 60  # seconds
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "pywats.log"
    
    # Serial number reservation
    auto_reserve_serials: bool = True
    reserve_count: int = 10
    
    # UI preferences
    start_minimized: bool = False
    show_notifications: bool = True
    
    # Advanced
    proxy_url: Optional[str] = None
    proxy_username: Optional[str] = None
    proxy_password: Optional[str] = None
    
    last_modified: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        # Convert monitor_folders objects to dicts if needed
        if self.monitor_folders and isinstance(self.monitor_folders[0], MonitorFolder):
            data['monitor_folders'] = [m.to_dict() for m in self.monitor_folders]
        if self.enabled_converters and isinstance(self.enabled_converters[0], ConverterConfig):
            data['enabled_converters'] = [c.to_dict() for c in self.enabled_converters]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ApplicationSettings":
        """Create from dictionary"""
        # Convert monitor_folders
        if 'monitor_folders' in data and data['monitor_folders']:
            data['monitor_folders'] = [
                MonitorFolder.from_dict(f) if isinstance(f, dict) else f
                for f in data['monitor_folders']
            ]
        
        # Convert enabled_converters
        if 'enabled_converters' in data and data['enabled_converters']:
            data['enabled_converters'] = [
                ConverterConfig.from_dict(c) if isinstance(c, dict) else c
                for c in data['enabled_converters']
            ]
        
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class SettingsManager:
    """
    Manages persistent application settings.
    
    Handles loading, saving, and validating application configuration.
    Supports both JSON file storage and in-memory caching.
    
    Usage:
        settings_mgr = SettingsManager(Path("./config"))
        
        settings = settings_mgr.load()
        settings.server_url = "https://new-server.com"
        settings_mgr.save(settings)
        
        # Watch for external changes
        settings_mgr.on_settings_changed(lambda s: print(f"Updated: {s}"))
    """
    
    def __init__(self, config_dir: Path = None):
        """
        Initialize settings manager.
        
        Args:
            config_dir: Directory to store settings file (default: current directory)
        """
        self.config_dir = config_dir or Path.cwd()
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.settings_file = self.config_dir / "settings.json"
        self.backup_file = self.config_dir / "settings.backup.json"
        
        self._settings: Optional[ApplicationSettings] = None
        self._callbacks: List[Callable[[ApplicationSettings], None]] = []
        self._last_modified: Optional[datetime] = None
    
    def load(self) -> ApplicationSettings:
        """
        Load settings from file or create defaults.
        
        Returns:
            ApplicationSettings instance
        """
        try:
            if self.settings_file.exists():
                logger.info(f"Loading settings from {self.settings_file}")
                with open(self.settings_file, 'r') as f:
                    data = json.load(f)
                
                self._settings = ApplicationSettings.from_dict(data)
                self._last_modified = datetime.fromisoformat(self._settings.last_modified)
                logger.info(f"Settings loaded successfully")
            
            else:
                logger.info("Settings file not found, using defaults")
                self._settings = ApplicationSettings()
                self.save(self._settings)
        
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
            
            # Try to restore from backup
            if self.backup_file.exists():
                try:
                    logger.info("Attempting to restore from backup...")
                    with open(self.backup_file, 'r') as f:
                        data = json.load(f)
                    self._settings = ApplicationSettings.from_dict(data)
                    logger.info("Settings restored from backup")
                except Exception as backup_error:
                    logger.error(f"Backup restore failed: {backup_error}")
                    self._settings = ApplicationSettings()
            
            else:
                self._settings = ApplicationSettings()
        
        return self._settings
    
    def save(self, settings: ApplicationSettings) -> bool:
        """
        Save settings to file.
        
        Args:
            settings: ApplicationSettings instance
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Update last modified timestamp
            settings.last_modified = datetime.now().isoformat()
            
            # Create backup of existing file
            if self.settings_file.exists():
                try:
                    import shutil
                    shutil.copy(self.settings_file, self.backup_file)
                except Exception as e:
                    logger.warning(f"Failed to create backup: {e}")
            
            # Write new settings
            with open(self.settings_file, 'w') as f:
                json.dump(settings.to_dict(), f, indent=2)
            
            self._settings = settings
            self._last_modified = datetime.fromisoformat(settings.last_modified)
            
            logger.info(f"Settings saved to {self.settings_file}")
            
            # Notify callbacks
            for callback in self._callbacks:
                try:
                    callback(settings)
                except Exception as e:
                    logger.error(f"Error in settings callback: {e}")
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            return False
    
    def get(self) -> ApplicationSettings:
        """Get current settings (loaded or defaults)"""
        if self._settings is None:
            self.load()
        return self._settings
    
    def reset_to_defaults(self) -> ApplicationSettings:
        """Reset settings to defaults"""
        logger.info("Resetting settings to defaults")
        settings = ApplicationSettings()
        self.save(settings)
        return settings
    
    def on_settings_changed(self, callback: Callable[[ApplicationSettings], None]) -> None:
        """
        Register callback for settings changes.
        
        Args:
            callback: Function to call with updated settings
        """
        self._callbacks.append(callback)
    
    def add_monitor_folder(self, folder: MonitorFolder) -> bool:
        """
        Add a folder to monitor.
        
        Args:
            folder: MonitorFolder configuration
            
        Returns:
            True if successful
        """
        settings = self.get()
        
        # Check if already exists
        for existing in settings.monitor_folders:
            if isinstance(existing, MonitorFolder):
                if existing.path == folder.path:
                    logger.warning(f"Folder already monitored: {folder.path}")
                    return False
            elif isinstance(existing, dict) and existing.get('path') == folder.path:
                logger.warning(f"Folder already monitored: {folder.path}")
                return False
        
        settings.monitor_folders.append(folder)
        return self.save(settings)
    
    def remove_monitor_folder(self, path: str) -> bool:
        """
        Remove a monitored folder.
        
        Args:
            path: Folder path to remove
            
        Returns:
            True if successful
        """
        settings = self.get()
        
        initial_count = len(settings.monitor_folders)
        settings.monitor_folders = [
            f for f in settings.monitor_folders
            if (f.path != path if isinstance(f, MonitorFolder) else f.get('path') != path)
        ]
        
        if len(settings.monitor_folders) < initial_count:
            return self.save(settings)
        
        logger.warning(f"Folder not found in monitoring list: {path}")
        return False
    
    def add_converter(self, converter: ConverterConfig) -> bool:
        """
        Add a converter configuration.
        
        Args:
            converter: ConverterConfig instance
            
        Returns:
            True if successful
        """
        settings = self.get()
        
        # Check if already exists
        for existing in settings.enabled_converters:
            if isinstance(existing, ConverterConfig):
                if existing.name == converter.name:
                    logger.warning(f"Converter already configured: {converter.name}")
                    return False
            elif isinstance(existing, dict) and existing.get('name') == converter.name:
                logger.warning(f"Converter already configured: {converter.name}")
                return False
        
        settings.enabled_converters.append(converter)
        return self.save(settings)
    
    def check_external_changes(self) -> bool:
        """
        Check if settings file was modified externally.
        
        Returns:
            True if file was modified
        """
        if not self.settings_file.exists():
            return False
        
        file_mtime = datetime.fromtimestamp(self.settings_file.stat().st_mtime)
        
        if self._last_modified is None:
            return True
        
        return file_mtime > self._last_modified
    
    def validate(self, settings: ApplicationSettings) -> tuple[bool, List[str]]:
        """
        Validate settings.
        
        Args:
            settings: ApplicationSettings to validate
            
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors: List[str] = []
        
        if not settings.server_url:
            errors.append("Server URL is required")
        
        if settings.connection_check_interval < 5:
            errors.append("Connection check interval must be at least 5 seconds")
        
        if settings.auto_upload_interval < 10:
            errors.append("Auto-upload interval must be at least 10 seconds")
        
        # Validate paths exist or can be created
        for attr in ['data_folder', 'queue_folder', 'reports_folder', 'converters_folder']:
            path = getattr(settings, attr)
            try:
                Path(path).mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(f"Invalid path for {attr}: {e}")
        
        return len(errors) == 0, errors
