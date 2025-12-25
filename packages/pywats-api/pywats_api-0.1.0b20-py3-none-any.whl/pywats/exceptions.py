"""Custom exceptions for pyWATS.

This module defines all exception types used throughout the pyWATS library.
"""
from typing import Optional, Dict, Any


class PyWATSError(Exception):
    """Base exception for all pyWATS errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self):
        if self.details:
            return f"{self.message} - Details: {self.details}"
        return self.message


class AuthenticationError(PyWATSError):
    """Raised when authentication fails."""
    pass


class NotFoundError(PyWATSError):
    """Raised when a requested resource is not found."""
    
    def __init__(self, resource_type: str, identifier: str, message: Optional[str] = None):
        self.resource_type = resource_type
        self.identifier = identifier
        msg = message or f"{resource_type} '{identifier}' not found"
        super().__init__(msg, {"resource_type": resource_type, "identifier": identifier})


class ValidationError(PyWATSError):
    """Raised when data validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Optional[Any] = None):
        self.field = field
        self.value = value
        details: Dict[str, Any] = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)
        super().__init__(message, details)


class ServerError(PyWATSError):
    """Raised when the server returns an error."""
    
    def __init__(self, status_code: int, message: str, response_body: Optional[str] = None):
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(
            f"Server error ({status_code}): {message}",
            {"status_code": status_code, "response_body": response_body}
        )


class ConnectionError(PyWATSError):
    """Raised when connection to the server fails."""
    pass


class TimeoutError(PyWATSError):
    """Raised when a request times out."""
    pass
