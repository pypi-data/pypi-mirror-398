"""
File Converter Base Class

Base class for file-based converters that are triggered when
files are created or modified in a watch folder.

This is the most common converter type.
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


class FileConverter(ABC):
    """
    Base class for file-based converters.
    
    Triggered when a file is created or modified in the watch folder.
    This is the most common converter type.
    
    Implementation Requirements:
        - Override `name` property (required)
        - Override `convert()` method (required)
        - Optionally override `validate()` for content-based confidence scoring
        - Optionally override `file_patterns` for file filtering
        - Optionally override `arguments_schema` for configurable parameters
    
    Example:
        class CSVConverter(FileConverter):
            @property
            def name(self) -> str:
                return "CSV Converter"
            
            @property
            def file_patterns(self) -> List[str]:
                return ["*.csv", "*.txt"]
            
            @property
            def arguments_schema(self) -> Dict[str, ArgumentDefinition]:
                return {
                    "delimiter": ArgumentDefinition(
                        arg_type=ArgumentType.STRING,
                        default=",",
                        description="CSV field delimiter"
                    ),
                }
            
            def validate(
                self, 
                source: ConverterSource, 
                context: ConverterContext
            ) -> ValidationResult:
                # Read first line and check for expected columns
                try:
                    with open(source.path, 'r') as f:
                        header = f.readline()
                    
                    if "PartNumber" in header and "SerialNumber" in header:
                        # Found expected columns - high confidence
                        return ValidationResult.perfect_match(
                            detected_part_number=self._extract_part_number(header)
                        )
                    elif "," in header:
                        # It's a CSV, but not our expected format
                        return ValidationResult.pattern_match()
                    else:
                        return ValidationResult.no_match("Not a CSV file")
                except Exception as e:
                    return ValidationResult.no_match(str(e))
            
            def convert(
                self, 
                source: ConverterSource, 
                context: ConverterContext
            ) -> ConverterResult:
                delimiter = context.get_argument("delimiter", ",")
                
                # Read and parse CSV
                with open(source.path, 'r') as f:
                    # ... parsing logic ...
                    pass
                
                report = {
                    "type": "UUT",
                    "partNumber": "...",
                    "serialNumber": "...",
                    "result": "Passed",
                }
                
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
        """Converter type - always FILE for this class"""
        return ConverterType.FILE
    
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
    def file_patterns(self) -> List[str]:
        """
        Glob patterns for files this converter handles.
        
        Used for initial file filtering before validate() is called.
        
        Examples:
            ["*.csv"]           - Only CSV files
            ["*.csv", "*.txt"]  - CSV and TXT files
            ["test_*.log"]      - Log files starting with "test_"
            ["*"]               - All files (use validate() to filter)
        
        Default: ["*"] (all files)
        """
        return ["*"]
    
    @property
    def arguments_schema(self) -> Dict[str, ArgumentDefinition]:
        """
        Define configurable arguments for this converter.
        
        These are exposed in the GUI for user configuration.
        Values are accessible via context.get_argument() during conversion.
        
        Returns:
            Dictionary of argument_name -> ArgumentDefinition
        
        Example:
            from .models import ArgumentDefinition, ArgumentType
            
            @property
            def arguments_schema(self) -> Dict[str, ArgumentDefinition]:
                return {
                    "delimiter": ArgumentDefinition(
                        arg_type=ArgumentType.STRING,
                        default=",",
                        description="CSV field delimiter"
                    ),
                    "skip_header": ArgumentDefinition(
                        arg_type=ArgumentType.BOOLEAN,
                        default=True,
                        description="Skip first row as header"
                    ),
                    "encoding": ArgumentDefinition(
                        arg_type=ArgumentType.CHOICE,
                        default="utf-8",
                        choices=["utf-8", "utf-16", "latin-1", "ascii"],
                        description="File encoding"
                    ),
                }
        """
        return {}
    
    @property
    def default_post_action(self) -> PostProcessAction:
        """Default post-processing action for successful conversions"""
        return PostProcessAction.MOVE
    
    # =========================================================================
    # Validation (optional override)
    # =========================================================================
    
    def validate(
        self, 
        source: ConverterSource, 
        context: "ConverterContext"
    ) -> ValidationResult:
        """
        Validate source and rate how well this converter fits.
        
        This method is called BEFORE convert() to:
        1. Filter files that don't qualify for this converter
        2. Rate confidence (for potential auto-selection in future)
        3. Preview detected fields (part number, serial, etc.)
        4. Check if dependencies are ready (for suspend/retry)
        
        The default implementation checks file patterns only (low confidence).
        Override this method for content-based validation (high confidence).
        
        Confidence Levels:
            1.0     - Perfect match (signature/header verified, fields detected)
            0.7-0.9 - Good match (content structure recognized)
            0.3-0.6 - Pattern match only (extension matched)
            0.0     - No match
        
        Args:
            source: The file to potentially convert
            context: Converter context with API client, settings, etc.
        
        Returns:
            ValidationResult with confidence score and detected fields
        
        Example:
            def validate(self, source, context) -> ValidationResult:
                try:
                    with open(source.path, 'rb') as f:
                        header = f.read(4)
                    
                    # Check file signature (magic bytes)
                    if header == b'STDF':
                        # Perfect match - STDF file format
                        return ValidationResult.perfect_match(
                            detected_part_number=self._read_part_number(source.path)
                        )
                    
                    return ValidationResult.no_match("Not an STDF file")
                except Exception as e:
                    return ValidationResult.no_match(str(e))
        """
        # Default: Check file pattern match
        if not self._matches_file_patterns(source):
            return ValidationResult.no_match(
                f"File '{source.primary_name}' doesn't match patterns: {self.file_patterns}"
            )
        
        # Pattern matched - low confidence (override for content-based validation)
        return ValidationResult.pattern_match(
            message=f"Matched pattern for {self.name}"
        )
    
    def _matches_file_patterns(self, source: ConverterSource) -> bool:
        """Check if source matches any of the file patterns"""
        if "*" in self.file_patterns:
            return True
        
        filename = source.primary_name.lower()
        return any(
            fnmatch.fnmatch(filename, pattern.lower())
            for pattern in self.file_patterns
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
        Convert the source file to a WATS report.
        
        This is the main conversion method. Read the file, parse it,
        and return a report dictionary.
        
        Args:
            source: File to convert (access via source.path)
            context: Converter context with:
                - context.api_client: WATS API client
                - context.get_argument(name): Get configured argument value
                - context.station_name: Station name for reports
                - context.drop_folder, done_folder, error_folder: Paths
        
        Returns:
            ConverterResult with status and report data
        
        Return Options:
            1. SUCCESS - Conversion completed successfully
                return ConverterResult.success_result(
                    report=report_dict,
                    post_action=PostProcessAction.MOVE
                )
            
            2. FAILED - Conversion failed (will move to error folder)
                return ConverterResult.failed_result(
                    error="Could not parse file: missing required field"
                )
            
            3. SUSPENDED - Conversion paused (will retry later)
                return ConverterResult.suspended_result(
                    reason="Waiting for companion file",
                    retry_after=timedelta(seconds=60)
                )
            
            4. SKIPPED - File should be ignored
                return ConverterResult.skipped_result(
                    reason="File is a template, not real data"
                )
        
        Example:
            def convert(self, source, context) -> ConverterResult:
                try:
                    # Get configured arguments
                    delimiter = context.get_argument("delimiter", ",")
                    encoding = context.get_argument("encoding", "utf-8")
                    
                    # Read and parse file
                    with open(source.path, 'r', encoding=encoding) as f:
                        reader = csv.DictReader(f, delimiter=delimiter)
                        rows = list(reader)
                    
                    if not rows:
                        return ConverterResult.failed_result("File is empty")
                    
                    # Build WATS report
                    report = {
                        "type": "UUT",
                        "partNumber": rows[0].get("PartNumber", "UNKNOWN"),
                        "serialNumber": rows[0].get("SerialNumber", "UNKNOWN"),
                        "operationTypeCode": "10",
                        "result": "Passed",
                        "startDateTime": datetime.now().isoformat(),
                        "root": {
                            "stepType": "SEQ_GROUP",
                            "group": "Main",
                            "status": "Passed",
                        }
                    }
                    
                    return ConverterResult.success_result(
                        report=report,
                        metadata={"rows_processed": len(rows)}
                    )
                    
                except Exception as e:
                    logger.exception(f"Conversion failed: {e}")
                    return ConverterResult.failed_result(str(e))
        """
        pass
    
    # =========================================================================
    # Lifecycle Callbacks (optional override)
    # =========================================================================
    
    def on_load(self, context: "ConverterContext") -> None:
        """
        Called when the converter is loaded.
        
        Use for one-time initialization (e.g., loading lookup tables).
        """
        pass
    
    def on_unload(self) -> None:
        """
        Called when the converter is unloaded.
        
        Use for cleanup.
        """
        pass
    
    def on_success(
        self, 
        source: ConverterSource, 
        result: ConverterResult,
        context: "ConverterContext"
    ) -> None:
        """
        Called after successful conversion and post-processing.
        
        Use for custom logging, notifications, or cleanup.
        """
        pass
    
    def on_failure(
        self, 
        source: ConverterSource, 
        result: ConverterResult,
        context: "ConverterContext"
    ) -> None:
        """
        Called after failed conversion.
        
        Use for custom error handling, notifications, or cleanup.
        """
        pass
    
    # =========================================================================
    # Helper Methods (for subclasses)
    # =========================================================================
    
    def read_file_text(
        self, 
        path: Path, 
        encoding: str = "utf-8",
        errors: str = "replace"
    ) -> str:
        """
        Helper to read file contents as text.
        
        Args:
            path: File path
            encoding: Text encoding (default: utf-8)
            errors: How to handle encoding errors (default: replace)
        
        Returns:
            File contents as string
        """
        with open(path, 'r', encoding=encoding, errors=errors) as f:
            return f.read()
    
    def read_file_lines(
        self, 
        path: Path, 
        encoding: str = "utf-8",
        strip: bool = True
    ) -> List[str]:
        """
        Helper to read file as list of lines.
        
        Args:
            path: File path
            encoding: Text encoding
            strip: Whether to strip whitespace from lines
        
        Returns:
            List of lines
        """
        with open(path, 'r', encoding=encoding) as f:
            if strip:
                return [line.strip() for line in f]
            return f.readlines()
    
    def read_file_bytes(self, path: Path) -> bytes:
        """
        Helper to read file contents as bytes.
        
        Args:
            path: File path
        
        Returns:
            File contents as bytes
        """
        with open(path, 'rb') as f:
            return f.read()
