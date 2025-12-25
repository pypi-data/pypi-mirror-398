"""
Base Converter Interface

Defines the interface that all converters must implement.
Converters are Python scripts that run on the client (and potentially server)
to convert various file formats to WATS report structures.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, BinaryIO, List, Union, Tuple
from pathlib import Path
from enum import Enum
import mimetypes

# Optional: python-magic for advanced file type detection
try:
    import magic  # type: ignore
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False


class ConversionStatus(Enum):
    """Status of a conversion operation"""
    SUCCESS = "success"
    FAILED = "failed"
    SUSPENDED = "suspended"  # Conversion suspended, will retry later
    SKIPPED = "skipped"  # File doesn't qualify for this converter


class PostProcessAction(Enum):
    """Post-processing action after successful conversion"""
    DELETE = "delete"  # Delete the source file
    MOVE = "move"      # Move to Done folder
    ZIP = "zip"        # Zip and move to Done folder
    KEEP = "keep"      # Keep file in place (no action)


class FileInfo:
    """
    Information about the file being converted.
    
    Provides access to file metadata, path, name, extension, etc.
    """
    
    def __init__(self, file_path: Path):
        self.path = file_path
        self.name = file_path.name
        self.stem = file_path.stem  # Filename without extension
        self.extension = file_path.suffix
        self.size = file_path.stat().st_size if file_path.exists() else 0
        self.parent = file_path.parent
        
        # Detect MIME type
        self.mime_type, _ = mimetypes.guess_type(str(file_path))
        
        # Try to detect file signature (magic number) if available
        self.file_type = None
        if HAS_MAGIC:
            try:
                if file_path.exists():
                    self.file_type = magic.from_file(str(file_path), mime=True)
            except Exception as e:
                import logging
                logging.getLogger(__name__).debug(f"Could not detect file type for {file_path}: {e}")
    
    def __str__(self) -> str:
        return f"FileInfo({self.name}, {self.size} bytes, {self.mime_type or 'unknown'})"


@dataclass
class ConverterResult:
    """
    Result of a conversion operation.
    
    Attributes:
        status: Conversion status (success, failed, suspended, skipped)
        report: The converted UUT/UUR report data (if successful)
        error: Error message (if failed)
        warnings: List of warning messages
        metadata: Additional metadata about the conversion
        suspend_reason: Reason for suspension (if status=SUSPENDED)
        post_action: Post-processing action (delete, move, zip, keep)
    """
    status: ConversionStatus
    report: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    suspend_reason: Optional[str] = None
    post_action: PostProcessAction = PostProcessAction.MOVE
    
    @property
    def success(self) -> bool:
        """Backward compatibility property"""
        return self.status == ConversionStatus.SUCCESS
    
    @classmethod
    def success_result(
        cls,
        report: Dict[str, Any],
        post_action: PostProcessAction = PostProcessAction.MOVE,
        warnings: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "ConverterResult":
        """Create a successful conversion result"""
        return cls(
            status=ConversionStatus.SUCCESS,
            report=report,
            warnings=warnings or [],
            metadata=metadata or {},
            post_action=post_action
        )
    
    @classmethod
    def failed_result(
        cls,
        error: str,
        post_action: PostProcessAction = PostProcessAction.KEEP,
        warnings: Optional[List[str]] = None
    ) -> "ConverterResult":
        """Create a failed conversion result"""
        return cls(
            status=ConversionStatus.FAILED,
            error=error,
            warnings=warnings or [],
            post_action=post_action
        )
    
    @classmethod
    def suspended_result(
        cls,
        reason: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "ConverterResult":
        """Create a suspended conversion result (will retry later)"""
        return cls(
            status=ConversionStatus.SUSPENDED,
            suspend_reason=reason,
            metadata=metadata or {},
            post_action=PostProcessAction.KEEP
        )
    
    @classmethod
    def skipped_result(cls, reason: str) -> "ConverterResult":
        """Create a skipped conversion result (file doesn't qualify)"""
        return cls(
            status=ConversionStatus.SKIPPED,
            error=reason,
            post_action=PostProcessAction.KEEP
        )


@dataclass
class ConverterArguments:
    """
    Arguments passed to converter from the client/service.
    
    Attributes:
        api_client: Reference to the pyWATS API client
        file_info: Information about the file being converted
        drop_folder: The drop folder being monitored
        done_folder: Folder for successfully processed files
        error_folder: Folder for failed conversions
        user_settings: User-configured settings for this converter
    """
    api_client: Any  # pyWATS client instance
    file_info: FileInfo
    drop_folder: Path
    done_folder: Path
    error_folder: Path
    user_settings: Dict[str, Any] = field(default_factory=dict)


class ConverterBase(ABC):
    """
    Base class for file-to-report converters.
    
    All converters must inherit from this class and implement:
    - convert_file() method for the actual conversion
    
    Optional overrides:
    - validate_file() to qualify files before conversion
    - get_arguments() to define configurable parameters
    - on_success() for custom post-processing
    - on_failure() for custom error handling
    
    Example:
        class MyConverter(ConverterBase):
            def __init__(self, station_name: str = "Default"):
                super().__init__()
                self.station_name = station_name
            
            @property
            def name(self) -> str:
                return "My Custom Converter"
            
            @property
            def supported_extensions(self) -> List[str]:
                return [".csv", ".txt"]
            
            def validate_file(self, file_info: FileInfo) -> tuple[bool, str]:
                # Check file extension
                if file_info.extension.lower() not in [".csv", ".txt"]:
                    return False, "Unsupported file type"
                
                # Check file size
                if file_info.size > 10 * 1024 * 1024:  # 10 MB
                    return False, "File too large"
                
                return True, ""
            
            def convert_file(
                self,
                file_path: Path,
                args: ConverterArguments
            ) -> ConverterResult:
                # Access file information
                print(f"Converting {args.file_info.name}")
                print(f"File size: {args.file_info.size} bytes")
                print(f"Drop folder: {args.drop_folder}")
                
                # Read and parse file
                with open(file_path, 'r') as f:
                    data = f.read()
                
                # Parse and create report
                report = {
                    "type": "UUT",
                    "partNumber": "...",
                    "serialNumber": "...",
                    "result": "Passed",
                }
                
                # Check if we need to suspend (e.g., waiting for dependencies)
                if some_condition:
                    return ConverterResult.suspended_result(
                        reason="Waiting for serial number reservation"
                    )
                
                # Return success
                return ConverterResult.success_result(
                    report=report,
                    post_action=PostProcessAction.ZIP,
                    metadata={"rows": 10}
                )
    """
    
    def __init__(self) -> None:
        # Configuration loaded from settings
        self.user_settings: Dict[str, Any] = {}
        self._api_client: Optional[Any] = None
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Human-readable name of the converter.
        """
        pass
    
    @property
    def version(self) -> str:
        """
        Version string for the converter.
        """
        return "1.0.0"
    
    @property
    def description(self) -> str:
        """
        Description of what the converter does.
        """
        return ""
    
    @property
    def supported_extensions(self) -> List[str]:
        """
        List of file extensions this converter supports.
        
        Example: [".csv", ".txt", ".xml"]
        
        Return ["*"] to accept all file types.
        """
        return ["*"]
    
    @property
    def supported_mime_types(self) -> List[str]:
        """
        List of MIME types this converter supports.
        
        Example: ["text/csv", "text/plain"]
        
        Return [] to skip MIME type checking.
        """
        return []
    
    def validate_file(self, file_info: FileInfo) -> Tuple[bool, str]:
        """
        Validate if a file qualifies for conversion by this converter.
        
        This method is called before convert_file() to quickly filter files.
        Override this method for custom validation logic (file signature,
        size limits, content checks, etc.).
        
        Default implementation checks:
        - File extension against supported_extensions
        - MIME type against supported_mime_types (if specified)
        
        Args:
            file_info: Information about the file
        
        Returns:
            Tuple of (is_valid, reason_if_invalid)
            - (True, "") if file qualifies
            - (False, "reason") if file doesn't qualify
        
        Example:
            def validate_file(self, file_info: FileInfo) -> tuple[bool, str]:
                # Check extension
                if file_info.extension.lower() not in [".csv", ".txt"]:
                    return False, f"Unsupported extension: {file_info.extension}"
                
                # Check file size
                if file_info.size > 10 * 1024 * 1024:  # 10 MB
                    return False, "File exceeds 10 MB limit"
                
                # Check file signature (magic number)
                if file_info.file_type and "text" not in file_info.file_type:
                    return False, "File is not a text file"
                
                return True, ""
        """
        # Check extension
        if self.supported_extensions and "*" not in self.supported_extensions:
            ext = file_info.extension.lower()
            if ext not in [e.lower() for e in self.supported_extensions]:
                return False, f"Unsupported file extension: {ext}"
        
        # Check MIME type if specified
        if self.supported_mime_types and file_info.file_type:
            if file_info.file_type not in self.supported_mime_types:
                return False, f"Unsupported MIME type: {file_info.file_type}"
        
        return True, ""
    
    @abstractmethod
    def convert_file(
        self,
        file_path: Path,
        args: ConverterArguments
    ) -> ConverterResult:
        """
        Convert a file to a UUT/UUR report.
        
        This is the main conversion method that must be implemented.
        
        Args:
            file_path: Path to the file to convert
            args: ConverterArguments with API client, file info, folders, settings
        
        Returns:
            ConverterResult with status and report data
        
        The converter has several options:
        
        1. SUCCESS: Return successful result with report
            return ConverterResult.success_result(
                report=report_dict,
                post_action=PostProcessAction.MOVE  # or ZIP, DELETE, KEEP
            )
        
        2. FAILED: Return failed result
            return ConverterResult.failed_result(
                error="Conversion failed: invalid format"
            )
        
        3. SUSPENDED: Suspend conversion (will retry later)
            return ConverterResult.suspended_result(
                reason="Waiting for serial number reservation"
            )
        
        4. SKIPPED: Skip this file (doesn't qualify)
            return ConverterResult.skipped_result(
                reason="File is not ready for processing"
            )
        
        Example:
            def convert_file(self, file_path: Path, args: ConverterArguments) -> ConverterResult:
                # Access converter arguments
                api = args.api_client
                file_info = args.file_info
                settings = args.user_settings
                
                try:
                    # Read file
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = f.read()
                    
                    # Parse data
                    serial = extract_serial(data)
                    
                    # Check if we should suspend
                    if not serial:
                        return ConverterResult.suspended_result(
                            reason="No serial number found, waiting"
                        )
                    
                    # Create report
                    report = {
                        "type": "UUT",
                        "serialNumber": serial,
                        "partNumber": settings.get("default_part", "UNKNOWN"),
                        "result": "Passed"
                    }
                    
                    return ConverterResult.success_result(
                        report=report,
                        post_action=PostProcessAction.ZIP
                    )
                
                except Exception as e:
                    return ConverterResult.failed_result(
                        error=f"Conversion error: {e}"
                    )
        """
        pass
    
    def on_success(
        self,
        file_path: Path,
        result: ConverterResult,
        args: ConverterArguments
    ) -> None:
        """
        Called after successful conversion and report submission.
        
        Override for custom post-processing logic.
        
        Args:
            file_path: Path to the converted file
            result: The successful conversion result
            args: Converter arguments
        
        Example:
            def on_success(self, file_path: Path, result: ConverterResult, args: ConverterArguments):
                # Log to custom system
                self.log_conversion(file_path, result.report["serialNumber"])
                
                # Send notification
                self.send_notification(f"Converted {file_path.name}")
        """
        pass
    
    def on_failure(
        self,
        file_path: Path,
        result: ConverterResult,
        args: ConverterArguments
    ) -> None:
        """
        Called after failed conversion.
        
        Override for custom error handling logic.
        
        Args:
            file_path: Path to the file that failed
            result: The failed conversion result
            args: Converter arguments
        
        Example:
            def on_failure(self, file_path: Path, result: ConverterResult, args: ConverterArguments):
                # Log error
                self.log_error(file_path, result.error)
                
                # Send alert
                self.send_alert(f"Conversion failed: {result.error}")
        """
        pass
    
    # Backward compatibility method (deprecated)
    def convert(self, file_stream: BinaryIO, filename: str) -> ConverterResult:
        """
        DEPRECATED: Use convert_file() instead.
        
        This method is kept for backward compatibility.
        """
        # Create temp file and call new method
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(filename).suffix) as tmp:
            tmp.write(file_stream.read())
            tmp_path = Path(tmp.name)
        
        try:
            file_info = FileInfo(tmp_path)
            args = ConverterArguments(
                api_client=None,
                file_info=file_info,
                drop_folder=tmp_path.parent,
                done_folder=tmp_path.parent,
                error_folder=tmp_path.parent,
                user_settings=self.user_settings
            )
            
            result = self.convert_file(tmp_path, args)
            return result
        finally:
            tmp_path.unlink(missing_ok=True)
    
    def validate_report(self, report: Dict[str, Any]) -> List[str]:
        """
        Validate a report before submission.
        
        Returns list of validation errors (empty if valid).
        Can be overridden by subclasses for custom validation.
        """
        errors = []
        
        # Basic required fields
        required_fields = ['partNumber', 'serialNumber', 'result']
        for field in required_fields:
            if field not in report or not report[field]:
                errors.append(f"Missing required field: {field}")
        
        return errors
    
    def get_arguments(self) -> Dict[str, Any]:
        """
        Get configurable arguments/parameters for this converter.
        
        Returns a dictionary of argument definitions that can be
        configured by users (shown in GUI or settings file).
        
        Format:
            {
                "param_name": {
                    "type": "string" | "int" | "float" | "bool" | "choice" | "path",
                    "default": <default_value>,
                    "description": "Parameter description",
                    "choices": ["a", "b"],  # Only for type="choice"
                    "required": True/False,
                    "min": <min_value>,  # For int/float
                    "max": <max_value>,  # For int/float
                }
            }
        
        Example:
            def get_arguments(self) -> Dict[str, Any]:
                return {
                    "station_name": {
                        "type": "string",
                        "default": "Station1",
                        "description": "Name of the test station",
                        "required": True
                    },
                    "timeout": {
                        "type": "int",
                        "default": 30,
                        "description": "Conversion timeout in seconds",
                        "min": 1,
                        "max": 300
                    },
                    "default_part": {
                        "type": "string",
                        "default": "UNKNOWN",
                        "description": "Default part number if not found in file"
                    },
                    "encoding": {
                        "type": "choice",
                        "default": "utf-8",
                        "choices": ["utf-8", "latin-1", "ascii"],
                        "description": "File encoding"
                    }
                }
        """
        return {}
    
    # Backward compatibility
    def get_parameters(self) -> Dict[str, Any]:
        """DEPRECATED: Use get_arguments() instead"""
        return self.get_arguments()


class CSVConverter(ConverterBase):
    """
    Example CSV converter implementation using the new architecture.
    
    This is a template showing how to implement a converter with:
    - File validation
    - Configurable arguments
    - Post-processing actions
    - Custom success/failure handlers
    
    Customize for your specific CSV format.
    """
    
    def __init__(
        self,
        delimiter: str = ",",
        encoding: str = "utf-8",
        skip_header: bool = True,
        part_number_column: int = 0,
        serial_number_column: int = 1,
        result_column: int = 2
    ):
        super().__init__()
        self.delimiter = delimiter
        self.encoding = encoding
        self.skip_header = skip_header
        self.part_number_column = part_number_column
        self.serial_number_column = serial_number_column
        self.result_column = result_column
    
    @property
    def name(self) -> str:
        return "CSV Converter"
    
    @property
    def version(self) -> str:
        return "2.0.0"
    
    @property
    def description(self) -> str:
        return "Converts CSV files to UUT reports with configurable columns and validation"
    
    @property
    def supported_extensions(self) -> List[str]:
        return [".csv", ".txt"]
    
    @property
    def supported_mime_types(self) -> List[str]:
        return ["text/csv", "text/plain"]
    
    def validate_file(self, file_info: FileInfo) -> Tuple[bool, str]:
        """Validate CSV file before conversion"""
        # Call base validation
        valid, reason = super().validate_file(file_info)
        if not valid:
            return False, reason
        
        # Check file size (e.g., max 10 MB)
        max_size = 10 * 1024 * 1024
        if file_info.size > max_size:
            return False, f"File too large: {file_info.size} bytes (max {max_size})"
        
        # Check minimum size (at least some content)
        if file_info.size < 10:
            return False, "File too small, likely empty"
        
        return True, ""
    
    def convert_file(
        self,
        file_path: Path,
        args: ConverterArguments
    ) -> ConverterResult:
        """Convert CSV file to UUT report"""
        try:
            # Get settings (merged with user settings)
            encoding = args.user_settings.get("encoding", self.encoding)
            delimiter = args.user_settings.get("delimiter", self.delimiter)
            skip_header = args.user_settings.get("skip_header", self.skip_header)
            
            # Read file
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            
            lines = content.strip().split('\n')
            
            if not lines:
                return ConverterResult.failed_result(
                    error="Empty file"
                )
            
            # Skip header if configured
            data_lines = lines[1:] if skip_header else lines
            
            if not data_lines:
                return ConverterResult.failed_result(
                    error="No data rows found"
                )
            
            # Parse first data row
            row = data_lines[0].split(delimiter)
            
            if len(row) <= max(self.part_number_column, self.serial_number_column, self.result_column):
                return ConverterResult.failed_result(
                    error=f"Insufficient columns in CSV. Expected at least {max(self.part_number_column, self.serial_number_column, self.result_column) + 1}, got {len(row)}"
                )
            
            # Extract fields
            part_number = row[self.part_number_column].strip()
            serial_number = row[self.serial_number_column].strip()
            result = row[self.result_column].strip()
            
            # Check for missing data - suspend if not ready
            if not serial_number:
                return ConverterResult.suspended_result(
                    reason="No serial number found in file, waiting for complete data"
                )
            
            # Parse result
            result_value = "Passed" if result.lower() in ["pass", "passed", "p", "ok"] else "Failed"
            
            # Create report
            report = {
                "type": "UUT",
                "partNumber": part_number,
                "serialNumber": serial_number,
                "result": result_value,
                "processCode": 10,  # Default process code
            }
            
            # Validate report
            errors = self.validate_report(report)
            if errors:
                return ConverterResult.failed_result(
                    error="; ".join(errors)
                )
            
            # Success - determine post-processing action from settings
            post_action_str = args.user_settings.get("post_action", "move")
            post_action = {
                "delete": PostProcessAction.DELETE,
                "move": PostProcessAction.MOVE,
                "zip": PostProcessAction.ZIP,
                "keep": PostProcessAction.KEEP
            }.get(post_action_str.lower(), PostProcessAction.MOVE)
            
            return ConverterResult.success_result(
                report=report,
                post_action=post_action,
                metadata={
                    "source_file": args.file_info.name,
                    "rows_processed": len(data_lines),
                    "file_size": args.file_info.size
                }
            )
            
        except UnicodeDecodeError as e:
            return ConverterResult.failed_result(
                error=f"Encoding error: {e}. Try different encoding."
            )
        
        except Exception as e:
            return ConverterResult.failed_result(
                error=f"Conversion error: {str(e)}"
            )
    
    def on_success(
        self,
        file_path: Path,
        result: ConverterResult,
        args: ConverterArguments
    ) -> None:
        """Called after successful conversion"""
        # Log success
        import logging
        logger = logging.getLogger(__name__)
        logger.info(
            f"Successfully converted {file_path.name}: "
            f"SN={result.report.get('serialNumber') if result.report else 'N/A'}, "
            f"Result={result.report.get('result') if result.report else 'N/A'}"
        )
    
    def on_failure(
        self,
        file_path: Path,
        result: ConverterResult,
        args: ConverterArguments
    ) -> None:
        """Called after failed conversion"""
        # Log failure
        import logging
        logger = logging.getLogger(__name__)
        logger.error(
            f"Failed to convert {file_path.name}: {result.error}"
        )
    
    def get_arguments(self) -> Dict[str, Any]:
        """Define configurable arguments"""
        return {
            "delimiter": {
                "type": "string",
                "default": ",",
                "description": "Field delimiter character",
                "required": False
            },
            "encoding": {
                "type": "choice",
                "default": "utf-8",
                "choices": ["utf-8", "latin-1", "ascii", "utf-16"],
                "description": "File encoding"
            },
            "skip_header": {
                "type": "bool",
                "default": True,
                "description": "Skip first row as header"
            },
            "part_number_column": {
                "type": "int",
                "default": 0,
                "description": "Column index for part number (0-based)",
                "min": 0,
                "max": 100
            },
            "serial_number_column": {
                "type": "int",
                "default": 1,
                "description": "Column index for serial number (0-based)",
                "min": 0,
                "max": 100
            },
            "result_column": {
                "type": "int",
                "default": 2,
                "description": "Column index for result (0-based)",
                "min": 0,
                "max": 100
            },
            "post_action": {
                "type": "choice",
                "default": "move",
                "choices": ["delete", "move", "zip", "keep"],
                "description": "Post-processing action after successful conversion"
            }
        }
