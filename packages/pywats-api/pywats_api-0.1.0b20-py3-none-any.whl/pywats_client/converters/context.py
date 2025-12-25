"""
Converter Context

Context object passed to converters containing configuration,
API client, and helper methods.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class ConverterContext:
    """
    Context passed to converters during validation and conversion.
    
    Provides access to:
    - Configuration values (thresholds, folders, etc.)
    - Configured argument values (from GUI or config)
    - API client for submitting reports
    - Helper methods for common tasks
    
    Example usage in converter:
        def convert(self, source: ConverterSource, context: ConverterContext):
            # Access configured arguments
            delimiter = context.get_argument("delimiter", ",")
            encoding = context.get_argument("encoding", "utf-8")
            
            # Access thresholds
            if confidence < context.reject_threshold:
                return ConverterResult.skipped_result("Below threshold")
            
            # Access API client
            await context.api_client.submit_report(report)
            
            # Access folders
            archive_path = context.done_folder / source.primary_name
            
            return ConverterResult.success_result(report=report)
    """
    
    # =========================================================================
    # Core Dependencies
    # =========================================================================
    
    api_client: Optional[Any] = None
    """WATS API client for submitting reports (pywats.Client or similar)"""
    
    # =========================================================================
    # Folder Configuration
    # =========================================================================
    
    drop_folder: Optional[Path] = None
    """Folder where source files/folders are dropped for conversion"""
    
    done_folder: Optional[Path] = None
    """Folder where successfully converted files are moved"""
    
    error_folder: Optional[Path] = None
    """Folder where failed files are moved"""
    
    pending_folder: Optional[Path] = None
    """Folder where suspended files wait for retry"""
    
    # =========================================================================
    # Station/Environment
    # =========================================================================
    
    station_name: str = ""
    """Station name for reports (from client config)"""
    
    station_id: str = ""
    """Station ID (if different from name)"""
    
    operator: str = ""
    """Current operator (if known)"""
    
    # =========================================================================
    # Validation Thresholds
    # =========================================================================
    
    alarm_threshold: float = 0.5
    """
    Confidence below this triggers a warning but allows conversion.
    
    Use for "low confidence" situations where you want to log a
    warning but still proceed with conversion.
    
    Default: 0.5 (50%)
    """
    
    reject_threshold: float = 0.2
    """
    Confidence below this rejects the conversion entirely.
    
    Files with confidence below this threshold will be skipped
    even if the converter accepts them.
    
    Default: 0.2 (20%)
    """
    
    # =========================================================================
    # Retry Configuration
    # =========================================================================
    
    max_retries: int = 3
    """Maximum number of retry attempts for suspended files"""
    
    retry_delay_seconds: int = 60
    """Delay between retry attempts (in seconds)"""
    
    # =========================================================================
    # Converter Arguments
    # =========================================================================
    
    arguments: Dict[str, Any] = field(default_factory=dict)
    """
    Configured argument values for this converter instance.
    
    These are set in the GUI or config file based on the
    converter's arguments_schema property.
    
    Access via get_argument() method for type-safe retrieval.
    """
    
    # =========================================================================
    # Runtime State
    # =========================================================================
    
    dry_run: bool = False
    """If True, don't actually submit reports (for testing)"""
    
    verbose: bool = False
    """If True, enable verbose logging"""
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    """Additional metadata (can be used by converters for state)"""
    
    # =========================================================================
    # Argument Access
    # =========================================================================
    
    def get_argument(self, name: str, default: Any = None) -> Any:
        """
        Get a configured argument value.
        
        Type-safe retrieval of argument values set in the GUI
        or config file.
        
        Args:
            name: Argument name (as defined in arguments_schema)
            default: Default value if not set
        
        Returns:
            The argument value, or default if not set
        
        Example:
            delimiter = context.get_argument("delimiter", ",")
            batch_size = context.get_argument("batch_size", 100)
        """
        return self.arguments.get(name, default)
    
    def set_argument(self, name: str, value: Any) -> None:
        """
        Set an argument value.
        
        Typically called by the converter manager when loading
        a converter configuration.
        
        Args:
            name: Argument name
            value: Argument value
        """
        self.arguments[name] = value
    
    def has_argument(self, name: str) -> bool:
        """
        Check if an argument is set.
        
        Args:
            name: Argument name
        
        Returns:
            True if the argument has a value
        """
        return name in self.arguments
    
    # =========================================================================
    # Threshold Checking
    # =========================================================================
    
    def check_confidence(self, confidence: float) -> str:
        """
        Check a confidence score against thresholds.
        
        Args:
            confidence: Confidence score (0.0 - 1.0)
        
        Returns:
            "accept" - Above alarm threshold, proceed normally
            "alarm" - Below alarm but above reject, proceed with warning
            "reject" - Below reject threshold, do not convert
        """
        if confidence < self.reject_threshold:
            return "reject"
        elif confidence < self.alarm_threshold:
            return "alarm"
        return "accept"
    
    # =========================================================================
    # Folder Helpers
    # =========================================================================
    
    def ensure_folders_exist(self) -> None:
        """Create all configured folders if they don't exist."""
        for folder in [self.drop_folder, self.done_folder, 
                      self.error_folder, self.pending_folder]:
            if folder:
                folder.mkdir(parents=True, exist_ok=True)
    
    def get_done_path(self, filename: str) -> Path:
        """
        Get path for a file in the done folder.
        
        Args:
            filename: Source filename
        
        Returns:
            Path in done folder
        """
        if not self.done_folder:
            raise ValueError("done_folder not configured")
        return self.done_folder / filename
    
    def get_error_path(self, filename: str) -> Path:
        """
        Get path for a file in the error folder.
        
        Args:
            filename: Source filename
        
        Returns:
            Path in error folder
        """
        if not self.error_folder:
            raise ValueError("error_folder not configured")
        return self.error_folder / filename
    
    def get_pending_path(self, filename: str) -> Path:
        """
        Get path for a file in the pending folder.
        
        Args:
            filename: Source filename
        
        Returns:
            Path in pending folder
        """
        if not self.pending_folder:
            raise ValueError("pending_folder not configured")
        return self.pending_folder / filename
    
    # =========================================================================
    # Logging Helpers
    # =========================================================================
    
    def log_debug(self, message: str) -> None:
        """Log a debug message (only if verbose)."""
        if self.verbose:
            logger.debug(message)
    
    def log_info(self, message: str) -> None:
        """Log an info message."""
        logger.info(message)
    
    def log_warning(self, message: str) -> None:
        """Log a warning message."""
        logger.warning(message)
    
    def log_error(self, message: str) -> None:
        """Log an error message."""
        logger.error(message)
    
    # =========================================================================
    # Factory Methods
    # =========================================================================
    
    @classmethod
    def from_config(
        cls,
        config: Dict[str, Any],
        api_client: Optional[Any] = None
    ) -> "ConverterContext":
        """
        Create a context from a configuration dictionary.
        
        Args:
            config: Configuration dictionary
            api_client: Optional API client
        
        Returns:
            New ConverterContext instance
        """
        return cls(
            api_client=api_client,
            drop_folder=Path(config["drop_folder"]) if config.get("drop_folder") else None,
            done_folder=Path(config["done_folder"]) if config.get("done_folder") else None,
            error_folder=Path(config["error_folder"]) if config.get("error_folder") else None,
            pending_folder=Path(config["pending_folder"]) if config.get("pending_folder") else None,
            station_name=config.get("station_name", ""),
            station_id=config.get("station_id", ""),
            operator=config.get("operator", ""),
            alarm_threshold=config.get("alarm_threshold", 0.5),
            reject_threshold=config.get("reject_threshold", 0.2),
            max_retries=config.get("max_retries", 3),
            retry_delay_seconds=config.get("retry_delay_seconds", 60),
            arguments=config.get("arguments", {}),
            dry_run=config.get("dry_run", False),
            verbose=config.get("verbose", False),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert context to a dictionary.
        
        Returns:
            Dictionary representation (excluding api_client)
        """
        return {
            "drop_folder": str(self.drop_folder) if self.drop_folder else None,
            "done_folder": str(self.done_folder) if self.done_folder else None,
            "error_folder": str(self.error_folder) if self.error_folder else None,
            "pending_folder": str(self.pending_folder) if self.pending_folder else None,
            "station_name": self.station_name,
            "station_id": self.station_id,
            "operator": self.operator,
            "alarm_threshold": self.alarm_threshold,
            "reject_threshold": self.reject_threshold,
            "max_retries": self.max_retries,
            "retry_delay_seconds": self.retry_delay_seconds,
            "arguments": self.arguments,
            "dry_run": self.dry_run,
            "verbose": self.verbose,
        }
    
    def copy_with(self, **overrides: Any) -> "ConverterContext":
        """
        Create a copy of this context with overrides.
        
        Args:
            **overrides: Values to override
        
        Returns:
            New ConverterContext with overrides applied
        
        Example:
            dry_context = context.copy_with(dry_run=True)
        """
        data = self.to_dict()
        data.update(overrides)
        
        # Handle Path conversion
        for key in ["drop_folder", "done_folder", "error_folder", "pending_folder"]:
            if key in data and data[key]:
                data[key] = Path(data[key]) if isinstance(data[key], str) else data[key]
        
        return ConverterContext(
            api_client=self.api_client,
            **data
        )
