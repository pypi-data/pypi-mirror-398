"""
Converter Models

Core data models for the converter architecture.
These models are used by all converter types (File, Folder, Scheduled).
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any, List, Union, Tuple, TYPE_CHECKING
import fnmatch
import mimetypes
import logging

# Type hints for UUTReport/UURReport (avoids circular import)
if TYPE_CHECKING:
    from pywats.domains.report.report_models import UUTReport, UURReport

# Optional: python-magic for advanced file type detection
try:
    import magic  # type: ignore
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False

logger = logging.getLogger(__name__)


# =============================================================================
# Enums
# =============================================================================

class SourceType(Enum):
    """Type of source being converted"""
    FILE = "file"
    FOLDER = "folder"
    DATABASE = "database"
    API = "api"


class ConverterType(Enum):
    """Type of converter"""
    FILE = "file"
    FOLDER = "folder"
    SCHEDULED = "scheduled"


class ConversionStatus(Enum):
    """Status of a conversion operation"""
    SUCCESS = "success"
    FAILED = "failed"
    SUSPENDED = "suspended"  # Conversion suspended, will retry later
    SKIPPED = "skipped"      # File doesn't qualify for this converter
    REJECTED = "rejected"    # Validation confidence below threshold


class PostProcessAction(Enum):
    """Post-processing action after successful conversion"""
    DELETE = "delete"  # Delete the source file/folder
    MOVE = "move"      # Move to Done folder
    ZIP = "zip"        # Zip and move to Done folder
    KEEP = "keep"      # Keep file in place (no action)


class ArgumentType(Enum):
    """Types for converter arguments"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    PATH = "path"
    CHOICE = "choice"     # Dropdown with options
    PASSWORD = "password"  # Masked string


# =============================================================================
# File/Source Information
# =============================================================================

@dataclass
class FileInfo:
    """
    Information about a single file.
    
    Provides access to file metadata, path, name, extension, etc.
    """
    path: Path
    
    def __post_init__(self) -> None:
        self.name = self.path.name
        self.stem = self.path.stem  # Filename without extension
        self.extension = self.path.suffix.lower()
        self.parent = self.path.parent
        
        # Size (only if file exists)
        try:
            self.size = self.path.stat().st_size if self.path.exists() else 0
            self.modified_time = datetime.fromtimestamp(
                self.path.stat().st_mtime
            ) if self.path.exists() else None
        except OSError:
            self.size = 0
            self.modified_time = None
        
        # Detect MIME type
        self.mime_type, _ = mimetypes.guess_type(str(self.path))
        
        # Detect file signature (magic number) if available
        self.file_type: Optional[str] = None
        if HAS_MAGIC and self.path.exists():
            try:
                self.file_type = magic.from_file(str(self.path), mime=True)
            except Exception as e:
                logger.debug(f"Could not detect file type for {self.path}: {e}")
    
    def __str__(self) -> str:
        return f"FileInfo({self.name}, {self.size} bytes, {self.mime_type or 'unknown'})"
    
    def matches_pattern(self, pattern: str) -> bool:
        """Check if filename matches a glob pattern"""
        return fnmatch.fnmatch(self.name.lower(), pattern.lower())
    
    def matches_any_pattern(self, patterns: List[str]) -> bool:
        """Check if filename matches any of the glob patterns"""
        return any(self.matches_pattern(p) for p in patterns)


@dataclass
class ConverterSource:
    """
    Abstraction over what's being converted.
    
    Works for files, folders, and virtual sources (database records, API responses).
    This is the primary input to all converter types.
    """
    source_type: SourceType
    path: Optional[Path] = None          # Primary file or folder path
    files: List[Path] = field(default_factory=list)  # All related files
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # For database/API sources
    record_id: Optional[str] = None
    connection_info: Optional[str] = None
    
    # Computed properties
    _file_info: Optional[FileInfo] = field(default=None, repr=False)
    
    @property
    def primary_name(self) -> str:
        """Name of the primary file/folder/record"""
        if self.path:
            return self.path.name
        return self.record_id or "unknown"
    
    @property
    def is_file(self) -> bool:
        return self.source_type == SourceType.FILE
    
    @property
    def is_folder(self) -> bool:
        return self.source_type == SourceType.FOLDER
    
    @property
    def file_info(self) -> Optional[FileInfo]:
        """Get FileInfo for the primary file (cached)"""
        if self._file_info is None and self.path and self.path.is_file():
            object.__setattr__(self, '_file_info', FileInfo(self.path))
        return self._file_info
    
    def get_files_matching(self, pattern: str) -> List[Path]:
        """Get all files matching a glob pattern"""
        return [f for f in self.files if fnmatch.fnmatch(f.name, pattern)]
    
    @classmethod
    def from_file(cls, file_path: Path) -> "ConverterSource":
        """Create source from a single file"""
        return cls(
            source_type=SourceType.FILE,
            path=file_path,
            files=[file_path]
        )
    
    @classmethod
    def from_folder(
        cls, 
        folder_path: Path, 
        include_pattern: str = "*",
        recursive: bool = True
    ) -> "ConverterSource":
        """Create source from a folder with all matching files"""
        if recursive:
            files = [f for f in folder_path.rglob("*") 
                     if f.is_file() and fnmatch.fnmatch(f.name, include_pattern)]
        else:
            files = [f for f in folder_path.glob("*") 
                     if f.is_file() and fnmatch.fnmatch(f.name, include_pattern)]
        
        return cls(
            source_type=SourceType.FOLDER,
            path=folder_path,
            files=sorted(files)
        )
    
    @classmethod
    def from_database_record(
        cls,
        record_id: str,
        connection_info: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "ConverterSource":
        """Create source from a database record"""
        return cls(
            source_type=SourceType.DATABASE,
            record_id=record_id,
            connection_info=connection_info,
            metadata=metadata or {}
        )


# =============================================================================
# Validation Result (Confidence Scoring)
# =============================================================================

@dataclass
class ValidationResult:
    """
    Result of converter validation/preview.
    
    Converters rate how well they match the input and can
    preview what they detected (serial number, part number, etc.)
    
    Confidence Levels:
        1.0     - Perfect match (content verified, all fields detected)
        0.7-0.9 - Good match (content looks correct)
        0.3-0.6 - Extension/pattern match only
        0.0     - No match
    
    Thresholds (configurable):
        alarm_threshold     - Below this, warn user but allow (default: 0.5)
        reject_threshold    - Below this, reject conversion (default: 0.2)
    """
    can_convert: bool           # Whether conversion is possible
    confidence: float           # 0.0 to 1.0 - how well this converter fits
    
    # Detected/preview information (helps user verify correct converter)
    detected_part_number: Optional[str] = None
    detected_serial_number: Optional[str] = None
    detected_process: Optional[str] = None
    detected_start_time: Optional[datetime] = None
    detected_result: Optional[str] = None  # "Passed" / "Failed"
    detected_station: Optional[str] = None
    
    # Validation details
    message: str = ""           # Human-readable explanation
    warnings: List[str] = field(default_factory=list)
    
    # For suspend/retry scenarios
    ready: bool = True          # False if dependencies are missing
    missing_dependencies: List[str] = field(default_factory=list)
    retry_after: Optional[timedelta] = None  # Suggested wait time
    
    def __post_init__(self) -> None:
        # Clamp confidence to valid range
        self.confidence = max(0.0, min(1.0, self.confidence))
    
    @property
    def is_below_alarm_threshold(self) -> bool:
        """Check if below alarm threshold (default 0.5)"""
        return self.confidence < 0.5
    
    def check_thresholds(
        self,
        alarm_threshold: float = 0.5, 
        reject_threshold: float = 0.2
    ) -> Tuple[bool, bool]:
        """
        Check against thresholds.
        
        Returns:
            (should_alarm, should_reject)
        """
        should_alarm = self.confidence < alarm_threshold
        should_reject = self.confidence < reject_threshold
        return should_alarm, should_reject
    
    @classmethod
    def perfect_match(cls, message: str = "Perfect match", **detected: Any) -> "ValidationResult":
        """Perfect confidence match (1.0) - content verified"""
        return cls(can_convert=True, confidence=1.0, message=message, **detected)
    
    @classmethod
    def good_match(
        cls, 
        confidence: float = 0.8, 
        message: str = "Good match",
        **detected: Any
    ) -> "ValidationResult":
        """Good confidence match (0.7-0.9)"""
        return cls(can_convert=True, confidence=confidence, message=message, **detected)
    
    @classmethod
    def pattern_match(
        cls, 
        message: str = "Matched by file pattern only",
        **detected: Any
    ) -> "ValidationResult":
        """Low confidence - only pattern/extension matched (0.3)"""
        return cls(can_convert=True, confidence=0.3, message=message, **detected)
    
    @classmethod
    def no_match(cls, reason: str) -> "ValidationResult":
        """Cannot convert this source"""
        return cls(can_convert=False, confidence=0.0, message=reason)
    
    @classmethod
    def not_ready(
        cls, 
        missing: List[str], 
        retry_after: Optional[timedelta] = None,
        confidence: float = 0.7
    ) -> "ValidationResult":
        """Can convert but dependencies missing - suspend and retry"""
        return cls(
            can_convert=True,
            confidence=confidence,
            ready=False,
            missing_dependencies=missing,
            retry_after=retry_after or timedelta(seconds=60),
            message=f"Waiting for: {', '.join(missing)}"
        )


# =============================================================================
# Converter Result
# =============================================================================

# Type alias for report data - supports both raw dicts and pydantic models
# Note: Using Any at runtime to avoid circular imports, but type checkers see UUTReport/UURReport
ReportType = Union[Dict[str, Any], Any]  # Any covers UUTReport/UURReport at runtime


@dataclass
class ConverterResult:
    """
    Result of a conversion operation.
    
    Contains the converted report(s), status, and metadata.
    
    The report can be either:
    - A dict (raw WSJF format)
    - A UUTReport model (preferred - uses factory methods)
    - A UURReport model
    
    Example with UUTReport (RECOMMENDED):
        from pywats.domains.report.report_models import UUTReport
        from pywats.domains.report.report_models.uut.steps.comp_operator import CompOp
        
        report = UUTReport(
            pn="PART-001", sn="SN-001", rev="A",
            process_code=10, station_name="Station1",
            location="Lab", purpose="Test",
            result="P", start=datetime.now().astimezone()
        )
        root = report.get_root_sequence_call()
        root.add_numeric_step(
            name="Voltage Test", value=5.0, unit="V",
            comp_op=CompOp.GELE, low_limit=4.5, high_limit=5.5,
            status="P"
        )
        return ConverterResult.success_result(report=report)
    """
    status: ConversionStatus
    
    # Report data (one or multiple) - supports Dict, UUTReport, or UURReport
    report: Optional[ReportType] = None
    reports: List[ReportType] = field(default_factory=list)
    
    # Error/status information
    error: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Suspend/retry information
    suspend_reason: Optional[str] = None
    retry_after: Optional[timedelta] = None
    retry_count: int = 0
    
    # Post-processing
    post_action: PostProcessAction = PostProcessAction.MOVE
    
    # Statistics
    processing_time_ms: Optional[int] = None
    records_processed: int = 0
    
    # Validation info (if validation was performed)
    validation: Optional[ValidationResult] = None
    
    @property
    def success(self) -> bool:
        """Backward compatibility property"""
        return self.status == ConversionStatus.SUCCESS
    
    @property
    def has_multiple_reports(self) -> bool:
        return len(self.reports) > 1 or (self.report is not None and len(self.reports) > 0)
    
    def get_all_reports(self) -> List[ReportType]:
        """Get all reports (single or multiple)"""
        if self.reports:
            return self.reports
        elif self.report:
            return [self.report]
        return []
    
    @classmethod
    def success_result(
        cls,
        report: Optional[ReportType] = None,
        reports: Optional[List[ReportType]] = None,
        post_action: PostProcessAction = PostProcessAction.MOVE,
        warnings: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        processing_time_ms: Optional[int] = None
    ) -> "ConverterResult":
        """Create a successful conversion result"""
        return cls(
            status=ConversionStatus.SUCCESS,
            report=report,
            reports=reports or [],
            warnings=warnings or [],
            metadata=metadata or {},
            post_action=post_action,
            processing_time_ms=processing_time_ms,
            records_processed=len(reports) if reports else (1 if report else 0)
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
        retry_after: Optional[timedelta] = None,
        retry_count: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "ConverterResult":
        """Create a suspended conversion result (will retry later)"""
        return cls(
            status=ConversionStatus.SUSPENDED,
            suspend_reason=reason,
            retry_after=retry_after or timedelta(seconds=60),
            retry_count=retry_count,
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
    
    @classmethod
    def rejected_result(
        cls, 
        reason: str, 
        confidence: float,
        threshold: float
    ) -> "ConverterResult":
        """Create a rejected result (confidence below threshold)"""
        return cls(
            status=ConversionStatus.REJECTED,
            error=f"{reason} (confidence {confidence:.2f} below threshold {threshold:.2f})",
            post_action=PostProcessAction.KEEP
        )


# =============================================================================
# Argument Definition (for configurable converter parameters)
# =============================================================================

@dataclass
class ArgumentDefinition:
    """
    Definition of a configurable converter argument.
    
    Used by the GUI to render appropriate input controls.
    """
    arg_type: ArgumentType
    default: Any = None
    description: str = ""
    required: bool = False
    
    # For CHOICE type
    choices: Optional[List[str]] = None
    
    # Validation
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    pattern: Optional[str] = None  # Regex pattern for STRING
    
    def validate(self, value: Any) -> Tuple[bool, str]:
        """Validate a value against this definition"""
        if value is None:
            if self.required:
                return False, "Value is required"
            return True, ""
        
        # Type checking
        if self.arg_type == ArgumentType.INTEGER:
            if not isinstance(value, int):
                return False, "Value must be an integer"
            if self.min_value is not None and value < self.min_value:
                return False, f"Value must be >= {self.min_value}"
            if self.max_value is not None and value > self.max_value:
                return False, f"Value must be <= {self.max_value}"
        
        elif self.arg_type == ArgumentType.FLOAT:
            if not isinstance(value, (int, float)):
                return False, "Value must be a number"
            if self.min_value is not None and value < self.min_value:
                return False, f"Value must be >= {self.min_value}"
            if self.max_value is not None and value > self.max_value:
                return False, f"Value must be <= {self.max_value}"
        
        elif self.arg_type == ArgumentType.BOOLEAN:
            if not isinstance(value, bool):
                return False, "Value must be a boolean"
        
        elif self.arg_type == ArgumentType.CHOICE:
            if self.choices and value not in self.choices:
                return False, f"Value must be one of: {self.choices}"
        
        elif self.arg_type == ArgumentType.STRING:
            if self.pattern:
                import re
                if not re.match(self.pattern, str(value)):
                    return False, f"Value must match pattern: {self.pattern}"
        
        return True, ""


# =============================================================================
# Conversion Record (for tracking and retry logic)
# =============================================================================

@dataclass
class ConversionRecord:
    """
    Record of a conversion attempt.
    
    Tracks conversion history for retry logic and reporting.
    """
    source_path: Path
    converter_name: str
    created_at: datetime = field(default_factory=datetime.now)
    
    # Attempt tracking
    attempts: int = 0
    last_attempt: Optional[datetime] = None
    last_status: Optional[ConversionStatus] = None
    last_error: Optional[str] = None
    
    # Suspend info
    suspend_reason: Optional[str] = None
    next_retry_at: Optional[datetime] = None
    
    # Validation info
    last_confidence: float = 0.0
    
    def record_attempt(
        self,
        status: ConversionStatus,
        error: Optional[str] = None,
        suspend_reason: Optional[str] = None,
        retry_after: Optional[timedelta] = None,
        confidence: float = 0.0
    ) -> None:
        """Record a conversion attempt"""
        self.attempts += 1
        self.last_attempt = datetime.now()
        self.last_status = status
        self.last_error = error
        self.suspend_reason = suspend_reason
        self.last_confidence = confidence
        
        if retry_after:
            self.next_retry_at = datetime.now() + retry_after
    
    def should_retry(self, max_attempts: int = 3) -> bool:
        """Check if this conversion should be retried"""
        if self.last_status not in (ConversionStatus.SUSPENDED, ConversionStatus.FAILED):
            return False
        return self.attempts < max_attempts
    
    def is_due_for_retry(self) -> bool:
        """Check if retry time has passed"""
        if self.next_retry_at is None:
            return True
        return datetime.now() >= self.next_retry_at


@dataclass
class FailureRecord:
    """
    Record of a failed conversion for logging/reporting.
    """
    source_path: Path
    converter_name: str
    error: str
    timestamp: datetime = field(default_factory=datetime.now)
    attempts: int = 1
    final_status: ConversionStatus = ConversionStatus.FAILED
    moved_to: Optional[Path] = None  # Error folder path
