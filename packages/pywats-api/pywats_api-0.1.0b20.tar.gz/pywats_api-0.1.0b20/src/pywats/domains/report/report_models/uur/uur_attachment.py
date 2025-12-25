"""
UURAttachment model for UUR reports.

Based on C# UURAttachment specification - handles file and byte array attachments
with MIME type detection, size validation, and report/failure level distinction.
"""

import os
import mimetypes
from pathlib import Path
from typing import Optional, TYPE_CHECKING, Any, Dict
from uuid import UUID, uuid4

from pydantic import BaseModel

if TYPE_CHECKING:
    from .uur_report import UURReport


class UURAttachment(BaseModel):
    """
    An attachment (file) to a UUR report or failure.
    
    Based on C# UURAttachment class specification.
    """
    
    def __init__(self, uur_report: 'UURReport', file_path: Optional[str] = None, 
                 label: Optional[str] = None, content: Optional[bytes] = None, 
                 mime_type: Optional[str] = None, failure_idx: Optional[int] = None,
                 delete_after_attach: bool = False):
        """
        Initialize UUR attachment.
        
        Args:
            uur_report: Parent UUR report
            file_path: Path to file to attach (for file attachments)
            label: Label/filename for the attachment
            content: Byte content (for byte array attachments)
            mime_type: MIME type (auto-detected if not provided)
            failure_idx: Index of failure this attachment belongs to (None for report-level)
            delete_after_attach: Whether to delete file after attaching
        """
        super().__init__()
        self._uur_report = uur_report
        self._file_path = file_path
        self._label = label
        self._content = content
        self._mime_type = mime_type
        self._failure_idx = failure_idx
        self._delete_after_attach = delete_after_attach
        self._binary_data_guid = uuid4()
        
        # Validate and load content
        self._validate_and_load()
    
    def _validate_and_load(self):
        """Validate attachment and load content"""
        if self._file_path and self._content:
            raise ValueError("Cannot specify both file_path and content")
        
        if not self._file_path and not self._content:
            raise ValueError("Must specify either file_path or content")
        
        if self._file_path:
            self._load_from_file()
        else:
            self._load_from_bytes()
    
    def _load_from_file(self):
        """Load attachment from file"""
        if not self._file_path:
            raise ValueError("File path not specified")
            
        if not os.path.exists(self._file_path):
            raise FileNotFoundError(f"The specified file {self._file_path} does not exist")
        
        file_info = Path(self._file_path)
        file_size = file_info.stat().st_size
        
        # Check file size limit (if API is available)
        is_valid, error = self._validate_size(file_size)
        if not is_valid:
            raise ValueError(error)
        
        # Load file content
        try:
            with open(self._file_path, 'rb') as f:
                self._content = f.read()
        except Exception as ex:
            raise RuntimeError(f"Error reading attachment {self._file_path}") from ex
        
        # Set label if not provided
        if not self._label:
            self._label = file_info.name
        
        # Auto-detect MIME type if not provided
        if not self._mime_type:
            self._mime_type = self._get_mime_type(file_info)
        
        # Delete file if requested
        if self._delete_after_attach:
            try:
                file_info.unlink()
            except Exception as ex:
                raise RuntimeError(f"Error deleting attachment {self._file_path}") from ex
    
    def _load_from_bytes(self):
        """Load attachment from byte array"""
        if not self._label:
            self._label = "attachment"
        
        if not self._mime_type:
            self._mime_type = "application/octet-stream"
    
    def _get_mime_type(self, file_info: Path) -> str:
        """
        Get MIME type for file.
        
        Args:
            file_info: Path object for the file
            
        Returns:
            MIME type string
        """
        mime_type, _ = mimetypes.guess_type(str(file_info))
        return mime_type or "application/octet-stream"
    
    @property
    def file_name(self) -> str:
        """Original filename (if set)"""
        return self._label or ""
    
    @property
    def data(self) -> bytes:
        """Returns attachment data as byte array"""
        return self._content or b""
    
    @property
    def mime_type(self) -> str:
        """MIME type of the attachment"""
        return self._mime_type or "application/octet-stream"
    
    @mime_type.setter
    def mime_type(self, value: str):
        """Set MIME type"""
        self._mime_type = value
    
    @property
    def content_type(self) -> str:
        """Alias for mime_type (matches C# property name)"""
        return self.mime_type
    
    @content_type.setter
    def content_type(self, value: str):
        """Set content type (alias for mime_type)"""
        self.mime_type = value
    
    @property
    def size(self) -> int:
        """Size of attachment in bytes"""
        return len(self._content) if self._content else 0
    
    @property
    def failure_idx(self) -> Optional[int]:
        """Index of failure this attachment belongs to (None for report-level)"""
        return self._failure_idx
    
    @property
    def is_failure_attachment(self) -> bool:
        """True if attached to a specific failure, False if report-level"""
        return self._failure_idx is not None
    
    @property
    def binary_data_guid(self) -> UUID:
        """Unique identifier for this binary data"""
        return self._binary_data_guid
    
    def _validate_size(self, size: int) -> tuple[bool, str]:
        """Validate attachment size against API limits.
        
        Args:
            size: Size in bytes
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Get max size from API if available
        max_size = self._get_max_attachment_size()
        
        if max_size > 0 and size > max_size:
            return False, f"Attachment size ({size} bytes) exceeds maximum allowed ({max_size} bytes)"
        
        return True, ""
    
    def _get_max_attachment_size(self) -> int:
        """Get maximum attachment size from API.
        
        Returns:
            Maximum size in bytes, or 0 if no limit
        """
        if not self._uur_report or not hasattr(self._uur_report, 'api'):
            # Default to 10 MB if no API available
            return 10 * 1024 * 1024
        
        api = getattr(self._uur_report, 'api', None)
        if not api:
            # Default to 10 MB if no API available
            return 10 * 1024 * 1024
        
        # Default to 10 MB - this matches typical WATS API limits
        # Could be made configurable through API settings in the future
        return 10 * 1024 * 1024
    
    def validate_size(self, max_size: Optional[int] = None) -> tuple[bool, str]:
        """
        Validate attachment size against limit.
        
        Args:
            max_size: Maximum size in bytes (uses API limit if not provided)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self._content:
            return False, f"Attachment has no content"
        
        return self._validate_size(len(self._content))
    
    def to_binary_type_dict(self) -> Dict[str, Any]:
        """
        Convert to WRML Binary_type representation.
        
        Returns:
            Dictionary representing Binary_type structure
        """
        binary_data = {
            'value': self._content,
            'content_type': self.mime_type,
            'file_name': self.file_name,
            'size': self.size,
            'size_specified': True,
            'binary_data_guid': str(self._binary_data_guid)
        }
        
        result: Dict[str, Any] = {
            'data': binary_data
        }
        
        if self._failure_idx is not None:
            result['fail_idx'] = self._failure_idx
            result['fail_idx_specified'] = True
        else:
            result['fail_idx_specified'] = False
        
        return result
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation"""
        return {
            'file_name': self.file_name,
            'mime_type': self.mime_type,
            'size_bytes': self.size,
            'failure_idx': self._failure_idx,
            'is_failure_attachment': self.is_failure_attachment,
            'binary_data_guid': str(self._binary_data_guid)
        }
    
    def __str__(self) -> str:
        level = f"failure[{self._failure_idx}]" if self.is_failure_attachment else "report"
        return f"UURAttachment({self.file_name}, {self.size} bytes, {level})"
    
    def __repr__(self) -> str:
        return (f"UURAttachment(file_name='{self.file_name}', size={self.size}, "
                f"failure_idx={self._failure_idx}, mime_type='{self.mime_type}')")