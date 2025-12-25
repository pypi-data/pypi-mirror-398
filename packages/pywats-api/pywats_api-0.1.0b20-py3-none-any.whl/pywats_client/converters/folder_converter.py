"""
Folder Converter Base Class

Base class for converters that work on entire folders rather than
individual files. Triggered when a folder is considered "ready".

Use this for multi-file packages where all files must arrive before
conversion can proceed.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, List, Optional, TYPE_CHECKING
import fnmatch
import logging

from .models import (
    ConverterType,
    ConverterSource,
    ValidationResult,
    ConverterResult,
    ArgumentDefinition,
    PostProcessAction,
)

if TYPE_CHECKING:
    from .context import ConverterContext

logger = logging.getLogger(__name__)


class FolderConverter(ABC):
    """
    Base class for folder-based converters.
    
    Triggered when a folder is deemed "ready" for processing.
    Use this for data packages with multiple files that must be
    processed together.
    
    Folder Readiness Strategies:
        1. MARKER FILE (default): Folder is ready when a marker file appears
        2. FILE COUNT: Folder is ready when it contains N files
        3. TIMEOUT: Folder is ready after N seconds of no new files
        4. CUSTOM: Override is_folder_ready() for custom logic
    
    Implementation Requirements:
        - Override `name` property (required)
        - Override `convert()` method (required)
        - Optionally override `readiness_marker` for marker file name
        - Optionally override `is_folder_ready()` for custom readiness logic
    
    Example:
        class MultiFileTestConverter(FolderConverter):
            @property
            def name(self) -> str:
                return "Multi-File Test Converter"
            
            @property
            def folder_patterns(self) -> List[str]:
                return ["TEST_*", "RESULT_*"]  # Match folder names
            
            @property
            def readiness_marker(self) -> Optional[str]:
                return "COMPLETE.marker"  # Ready when this file appears
            
            def validate(
                self,
                source: ConverterSource,
                context: ConverterContext
            ) -> ValidationResult:
                folder = source.folder_path
                
                # Check for required files
                has_data = (folder / "data.csv").exists()
                has_config = (folder / "config.xml").exists()
                
                if has_data and has_config:
                    return ValidationResult.perfect_match()
                elif has_data:
                    return ValidationResult.partial_match(
                        "Found data.csv but missing config.xml"
                    )
                else:
                    return ValidationResult.no_match("Required files not found")
            
            def convert(
                self,
                source: ConverterSource,
                context: ConverterContext
            ) -> ConverterResult:
                folder = source.folder_path
                
                # Read all files in the folder
                data_file = folder / "data.csv"
                config_file = folder / "config.xml"
                
                # Process...
                
                return ConverterResult.success_result(
                    report=report,
                    post_action=PostProcessAction.MOVE
                )
    """
    
    def __init__(self) -> None:
        """Initialize the converter"""
        self._arguments: Dict[str, Any] = {}
    
    # =========================================================================
    # Required Properties (must override)
    # =========================================================================
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Human-readable name of the converter.
        
        This is displayed in the GUI and used for logging.
        """
        pass
    
    # =========================================================================
    # Optional Properties (can override)
    # =========================================================================
    
    @property
    def converter_type(self) -> ConverterType:
        """Converter type - always FOLDER for this class"""
        return ConverterType.FOLDER
    
    @property
    def version(self) -> str:
        """Version string for the converter"""
        return "1.0.0"
    
    @property
    def description(self) -> str:
        """Description of what this converter does"""
        return ""
    
    @property
    def author(self) -> str:
        """Author/maintainer of this converter"""
        return ""
    
    @property
    def folder_patterns(self) -> List[str]:
        """
        Glob patterns for folder names this converter handles.
        
        Used for initial filtering before readiness check.
        
        Examples:
            ["TEST_*"]          - Folders starting with "TEST_"
            ["*_results"]       - Folders ending with "_results"
            ["*"]               - All folders (use validate() to filter)
        
        Default: ["*"] (all folders)
        """
        return ["*"]
    
    @property
    def readiness_marker(self) -> Optional[str]:
        """
        Marker file that indicates folder is ready for processing.
        
        When this file appears in the folder, conversion begins.
        This is the simplest and most reliable readiness strategy.
        
        Examples:
            "COMPLETE.marker"     - Generic marker
            "_READY"              - Hidden marker
            "process.trigger"     - Custom trigger file
            None                  - Use is_folder_ready() instead
        
        Default: "COMPLETE.marker"
        """
        return "COMPLETE.marker"
    
    @property
    def min_file_count(self) -> Optional[int]:
        """
        Minimum number of files required before checking readiness.
        
        If set, folder is only checked for readiness once it contains
        at least this many files. Used as a pre-filter before
        readiness_marker or is_folder_ready() is checked.
        
        Default: None (no minimum)
        """
        return None
    
    @property
    def expected_files(self) -> Optional[List[str]]:
        """
        List of expected file patterns that must exist.
        
        If set, all patterns must match at least one file before
        the folder is considered for readiness.
        
        Example:
            ["data.csv", "config.xml", "*.log"]
        
        Default: None (no specific files required)
        """
        return None
    
    @property
    def arguments_schema(self) -> Dict[str, ArgumentDefinition]:
        """
        Define configurable arguments for this converter.
        
        These are exposed in the GUI for user configuration.
        Values are accessible via context.get_argument() during conversion.
        
        Returns:
            Dictionary of argument_name -> ArgumentDefinition
        """
        return {}
    
    @property
    def default_post_action(self) -> PostProcessAction:
        """Default post-processing action for successful conversions"""
        return PostProcessAction.MOVE
    
    @property
    def preserve_folder_structure(self) -> bool:
        """
        Whether to preserve folder structure when moving/archiving.
        
        If True, the entire folder is moved as-is.
        If False, files are flattened into the target directory.
        
        Default: True
        """
        return True
    
    # =========================================================================
    # Readiness Check (optional override)
    # =========================================================================
    
    def is_folder_ready(
        self, 
        folder_path: Path, 
        context: "ConverterContext"
    ) -> bool:
        """
        Check if a folder is ready for conversion.
        
        The default implementation checks:
        1. Folder matches folder_patterns
        2. Contains at least min_file_count files (if set)
        3. All expected_files exist (if set)
        4. Readiness marker file exists (if set)
        
        Override this method for custom readiness logic.
        
        Args:
            folder_path: Path to the folder
            context: Converter context
        
        Returns:
            True if folder is ready for conversion
        
        Example (timeout-based readiness):
            def is_folder_ready(self, folder_path, context) -> bool:
                # Check if any file has been modified in the last 30 seconds
                import time
                now = time.time()
                for file in folder_path.iterdir():
                    if file.is_file():
                        mtime = file.stat().st_mtime
                        if now - mtime < 30:  # Modified within 30 seconds
                            return False  # Still receiving files
                return True  # Folder is stable
        """
        # Check folder pattern match
        if not self._matches_folder_patterns(folder_path):
            return False
        
        # Check minimum file count
        if self.min_file_count is not None:
            file_count = sum(1 for f in folder_path.iterdir() if f.is_file())
            if file_count < self.min_file_count:
                return False
        
        # Check expected files exist
        if self.expected_files:
            for pattern in self.expected_files:
                if not any(
                    fnmatch.fnmatch(f.name, pattern) 
                    for f in folder_path.iterdir() 
                    if f.is_file()
                ):
                    return False
        
        # Check marker file
        if self.readiness_marker:
            marker_path = folder_path / self.readiness_marker
            if not marker_path.exists():
                return False
        
        return True
    
    def _matches_folder_patterns(self, folder_path: Path) -> bool:
        """Check if folder name matches any of the folder patterns"""
        if "*" in self.folder_patterns:
            return True
        
        folder_name = folder_path.name.lower()
        return any(
            fnmatch.fnmatch(folder_name, pattern.lower())
            for pattern in self.folder_patterns
        )
    
    # =========================================================================
    # Validation (optional override)
    # =========================================================================
    
    def validate(
        self, 
        source: ConverterSource, 
        context: "ConverterContext"
    ) -> ValidationResult:
        """
        Validate folder contents and rate how well this converter fits.
        
        Called AFTER is_folder_ready() returns True, BEFORE convert().
        
        Use this to:
        1. Verify folder contents are valid
        2. Rate confidence for potential auto-selection
        3. Preview detected fields (part number, serial, etc.)
        4. Check for missing or invalid files
        
        Args:
            source: The folder to convert
            context: Converter context
        
        Returns:
            ValidationResult with confidence score
        
        Example:
            def validate(self, source, context) -> ValidationResult:
                folder = source.folder_path
                
                # Check for signature file
                sig_file = folder / "manifest.json"
                if sig_file.exists():
                    import json
                    with open(sig_file) as f:
                        manifest = json.load(f)
                    
                    if manifest.get("format") == "our_format":
                        return ValidationResult.perfect_match(
                            detected_part_number=manifest.get("partNumber")
                        )
                
                # No manifest - check for expected file structure
                if (folder / "data.csv").exists():
                    return ValidationResult.partial_match()
                
                return ValidationResult.no_match("Invalid folder structure")
        """
        # Default: Pattern match only
        return ValidationResult.pattern_match(
            message=f"Folder matched pattern for {self.name}"
        )
    
    # =========================================================================
    # Conversion (must override)
    # =========================================================================
    
    @abstractmethod
    def convert(
        self, 
        source: ConverterSource, 
        context: "ConverterContext"
    ) -> ConverterResult:
        """
        Convert the folder contents to a WATS report.
        
        This is the main conversion method. Process all files in the
        folder and return a report dictionary.
        
        Args:
            source: Folder to convert
                - source.folder_path: Path to the folder
                - source.files: List of FileInfo for all files in folder
                - source.get_files_by_pattern("*.csv"): Filter files
            context: Converter context with API client, settings, etc.
        
        Returns:
            ConverterResult with status and report data
        
        Example:
            def convert(self, source, context) -> ConverterResult:
                folder = source.folder_path
                
                try:
                    # Read main data file
                    data_file = folder / "data.csv"
                    config_file = folder / "config.xml"
                    
                    with open(data_file) as f:
                        data = parse_csv(f)
                    
                    with open(config_file) as f:
                        config = parse_xml(f)
                    
                    # Build report
                    report = {
                        "type": "UUT",
                        "partNumber": config["partNumber"],
                        "serialNumber": data["serial"],
                        "result": "Passed",
                        # ...
                    }
                    
                    # Process all log files
                    for log_file in source.get_files_by_pattern("*.log"):
                        report["additionalData"] = {
                            "logs": log_file.path.read_text()
                        }
                    
                    return ConverterResult.success_result(report=report)
                    
                except Exception as e:
                    return ConverterResult.failed_result(str(e))
        """
        pass
    
    # =========================================================================
    # Lifecycle Callbacks (optional override)
    # =========================================================================
    
    def on_load(self, context: "ConverterContext") -> None:
        """Called when the converter is loaded"""
        pass
    
    def on_unload(self) -> None:
        """Called when the converter is unloaded"""
        pass
    
    def on_success(
        self, 
        source: ConverterSource, 
        result: ConverterResult,
        context: "ConverterContext"
    ) -> None:
        """Called after successful conversion"""
        pass
    
    def on_failure(
        self, 
        source: ConverterSource, 
        result: ConverterResult,
        context: "ConverterContext"
    ) -> None:
        """Called after failed conversion"""
        pass
    
    # =========================================================================
    # Helper Methods (for subclasses)
    # =========================================================================
    
    def list_files(
        self, 
        folder: Path, 
        pattern: str = "*",
        recursive: bool = False
    ) -> List[Path]:
        """
        List files in folder matching pattern.
        
        Args:
            folder: Folder path
            pattern: Glob pattern (default: "*")
            recursive: Include subdirectories
        
        Returns:
            List of matching file paths
        """
        if recursive:
            return list(folder.rglob(pattern))
        return list(folder.glob(pattern))
    
    def read_marker_data(self, folder: Path) -> Optional[str]:
        """
        Read contents of the readiness marker file.
        
        Some workflows put metadata in the marker file.
        
        Returns:
            Marker file contents or None if not found
        """
        if not self.readiness_marker:
            return None
        
        marker_path = folder / self.readiness_marker
        if marker_path.exists():
            return marker_path.read_text()
        return None
    
    def delete_marker(self, folder: Path) -> bool:
        """
        Delete the readiness marker file.
        
        Call this during conversion if you want to clean up
        the marker file as part of processing.
        
        Returns:
            True if deleted, False if not found
        """
        if not self.readiness_marker:
            return False
        
        marker_path = folder / self.readiness_marker
        if marker_path.exists():
            marker_path.unlink()
            return True
        return False
