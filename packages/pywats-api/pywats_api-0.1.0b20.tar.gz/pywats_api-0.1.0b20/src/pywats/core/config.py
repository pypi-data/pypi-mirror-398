"""
pyWATS API Configuration

Provides configuration management for the pyWATS API library.
Settings are stored in a JSON config file and can be modified programmatically
or through the GUI client.

Configuration Hierarchy:
- API Settings: Core API behavior (timeouts, error modes, caching)
- Domain Settings: Per-domain configuration (product, report, etc.)
"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, TypeVar, Type
from pydantic import BaseModel, Field, ConfigDict

# Import ErrorMode from exceptions to avoid duplication
from .exceptions import ErrorMode

logger = logging.getLogger(__name__)

# Type variable for domain settings subclasses
T = TypeVar('T', bound='DomainSettings')


class DomainSettings(BaseModel):
    """Settings for a specific API domain.
    
    Attributes:
        enabled: Whether the domain is enabled
        cache_enabled: Whether caching is enabled for this domain
        cache_ttl_seconds: Cache time-to-live in seconds
    """
    model_config = ConfigDict(extra='ignore')
    
    enabled: bool = Field(default=True, description="Whether the domain is enabled")
    cache_enabled: bool = Field(default=True, description="Whether caching is enabled")
    cache_ttl_seconds: int = Field(default=300, description="Cache TTL in seconds (default 5 minutes)")
    
    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()
    
    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        return cls.model_validate(data)


class ProductDomainSettings(DomainSettings):
    """Product domain specific settings.
    
    Attributes:
        auto_create_products: Automatically create products if not found
        default_revision: Default revision for new products
    """
    auto_create_products: bool = Field(default=False, description="Auto-create products if not found")
    default_revision: str = Field(default="A", description="Default revision for new products")


class ReportDomainSettings(DomainSettings):
    """Report domain specific settings.
    
    Attributes:
        auto_submit: Automatically submit reports after creation
        validate_before_submit: Validate reports before submission
        include_attachments: Include attachments in reports
        max_attachment_size_mb: Maximum attachment size in MB
    """
    auto_submit: bool = Field(default=True, description="Auto-submit reports after creation")
    validate_before_submit: bool = Field(default=True, description="Validate before submission")
    include_attachments: bool = Field(default=True, description="Include attachments in reports")
    max_attachment_size_mb: int = Field(default=10, description="Max attachment size in MB")


class ProductionDomainSettings(DomainSettings):
    """Production domain specific settings.
    
    Attributes:
        auto_reserve_serials: Automatically reserve serial numbers
        serial_reserve_count: Number of serials to reserve at once
        validate_serial_format: Validate serial number format
    """
    auto_reserve_serials: bool = Field(default=True, description="Auto-reserve serial numbers")
    serial_reserve_count: int = Field(default=10, description="Number of serials to reserve")
    validate_serial_format: bool = Field(default=False, description="Validate serial format")


class ProcessDomainSettings(DomainSettings):
    """Process domain specific settings.
    
    Attributes:
        refresh_interval_seconds: Interval for refreshing process data
        auto_refresh: Enable automatic refresh
    """
    refresh_interval_seconds: int = Field(default=300, description="Refresh interval in seconds")
    auto_refresh: bool = Field(default=True, description="Enable automatic refresh")


class SoftwareDomainSettings(DomainSettings):
    """Software domain specific settings.
    
    Attributes:
        auto_download: Automatically download software updates
        download_path: Path for downloaded files
    """
    auto_download: bool = Field(default=False, description="Auto-download software updates")
    download_path: str = Field(default="./downloads", description="Download path")


class AssetDomainSettings(DomainSettings):
    """Asset domain specific settings."""
    pass  # Uses base settings only


class RootCauseDomainSettings(DomainSettings):
    """RootCause domain specific settings."""
    pass  # Uses base settings only


class AppDomainSettings(DomainSettings):
    """App/Statistics domain specific settings."""
    pass  # Uses base settings only


class APISettings(BaseModel):
    """
    Main API configuration settings.
    
    Controls global API behavior and per-domain settings.
    
    Attributes:
        timeout_seconds: HTTP request timeout
        max_retries: Maximum number of retry attempts
        retry_delay_seconds: Delay between retries
        error_mode: Error handling mode ("strict" or "lenient")
        log_requests: Log HTTP requests
        log_responses: Log HTTP responses
        verify_ssl: Verify SSL certificates
        product: Product domain settings
        report: Report domain settings
        production: Production domain settings
        process: Process domain settings
        software: Software domain settings
        asset: Asset domain settings
        rootcause: RootCause domain settings
        app: App/Statistics domain settings
    """
    model_config = ConfigDict(extra='ignore')
    
    # Connection settings
    timeout_seconds: int = Field(default=30, description="HTTP request timeout")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    retry_delay_seconds: int = Field(default=1, description="Delay between retries")
    
    # Error handling
    error_mode: str = Field(default="strict", description="Error mode: 'strict' or 'lenient'")
    
    # Logging
    log_requests: bool = Field(default=False, description="Log HTTP requests")
    log_responses: bool = Field(default=False, description="Log HTTP responses")
    
    # SSL/TLS
    verify_ssl: bool = Field(default=True, description="Verify SSL certificates")
    
    # Domain settings
    product: ProductDomainSettings = Field(default_factory=ProductDomainSettings)
    report: ReportDomainSettings = Field(default_factory=ReportDomainSettings)
    production: ProductionDomainSettings = Field(default_factory=ProductionDomainSettings)
    process: ProcessDomainSettings = Field(default_factory=ProcessDomainSettings)
    software: SoftwareDomainSettings = Field(default_factory=SoftwareDomainSettings)
    asset: AssetDomainSettings = Field(default_factory=AssetDomainSettings)
    rootcause: RootCauseDomainSettings = Field(default_factory=RootCauseDomainSettings)
    app: AppDomainSettings = Field(default_factory=AppDomainSettings)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = {
            "timeout_seconds": self.timeout_seconds,
            "max_retries": self.max_retries,
            "retry_delay_seconds": self.retry_delay_seconds,
            "error_mode": self.error_mode,
            "log_requests": self.log_requests,
            "log_responses": self.log_responses,
            "verify_ssl": self.verify_ssl,
            "domains": {
                "product": self.product.to_dict(),
                "report": self.report.to_dict(),
                "production": self.production.to_dict(),
                "process": self.process.to_dict(),
                "software": self.software.to_dict(),
                "asset": self.asset.to_dict(),
                "rootcause": self.rootcause.to_dict(),
                "app": self.app.to_dict(),
            }
        }
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "APISettings":
        """Create from dictionary."""
        domains = data.pop("domains", {})
        
        settings = cls(
            timeout_seconds=data.get("timeout_seconds", 30),
            max_retries=data.get("max_retries", 3),
            retry_delay_seconds=data.get("retry_delay_seconds", 1),
            error_mode=data.get("error_mode", "strict"),
            log_requests=data.get("log_requests", False),
            log_responses=data.get("log_responses", False),
            verify_ssl=data.get("verify_ssl", True),
        )
        
        # Load domain settings
        if "product" in domains:
            settings.product = ProductDomainSettings.from_dict(domains["product"])
        if "report" in domains:
            settings.report = ReportDomainSettings.from_dict(domains["report"])
        if "production" in domains:
            settings.production = ProductionDomainSettings.from_dict(domains["production"])
        if "process" in domains:
            settings.process = ProcessDomainSettings.from_dict(domains["process"])
        if "software" in domains:
            settings.software = SoftwareDomainSettings.from_dict(domains["software"])
        if "asset" in domains:
            settings.asset = AssetDomainSettings.from_dict(domains["asset"])
        if "rootcause" in domains:
            settings.rootcause = RootCauseDomainSettings.from_dict(domains["rootcause"])
        if "app" in domains:
            settings.app = AppDomainSettings.from_dict(domains["app"])
        
        return settings


class APIConfigManager:
    """
    Manages API configuration file operations.
    
    Handles loading, saving, and watching for changes to the API config file.
    """
    
    DEFAULT_CONFIG_FILENAME = "pywats_api.json"
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the config manager.
        
        Args:
            config_path: Path to config file. If None, uses default location.
        """
        if config_path is None:
            # Default to user's config directory
            import os
            if os.name == 'nt':
                base = Path(os.environ.get('APPDATA', '')) / 'pyWATS'
            else:
                base = Path.home() / '.config' / 'pywats'
            config_path = base / self.DEFAULT_CONFIG_FILENAME
        
        self.config_path = Path(config_path)
        self._settings: Optional[APISettings] = None
    
    def load(self) -> APISettings:
        """Load settings from file, creating defaults if not found."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self._settings = APISettings.from_dict(data)
                logger.debug(f"Loaded API settings from {self.config_path}")
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load API config, using defaults: {e}")
                self._settings = APISettings()
        else:
            logger.debug("No API config file found, using defaults")
            self._settings = APISettings()
        
        return self._settings
    
    def save(self, settings: Optional[APISettings] = None) -> None:
        """Save settings to file."""
        if settings:
            self._settings = settings
        
        if self._settings is None:
            self._settings = APISettings()
        
        # Ensure directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._settings.to_dict(), f, indent=2)
            logger.debug(f"Saved API settings to {self.config_path}")
        except IOError as e:
            logger.error(f"Failed to save API config: {e}")
            raise
    
    @property
    def settings(self) -> APISettings:
        """Get current settings, loading if needed."""
        if self._settings is None:
            self.load()
        return self._settings  # type: ignore
    
    def reset_to_defaults(self) -> APISettings:
        """Reset all settings to defaults."""
        self._settings = APISettings()
        self.save()
        return self._settings


# Global config manager instance
_config_manager: Optional[APIConfigManager] = None


def get_api_config_manager() -> APIConfigManager:
    """Get the global API config manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = APIConfigManager()
    return _config_manager


def get_api_settings() -> APISettings:
    """Get the current API settings."""
    return get_api_config_manager().settings
