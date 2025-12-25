"""Exception classes and error handling for pyWATS API.

This module provides consistent error handling across all domains with two modes:
- STRICT: Raises exceptions on empty responses and all errors
- LENIENT: Returns None for 404 and empty responses, only raises on actual errors

Usage:
    api = pyWATS(error_mode=ErrorMode.STRICT)  # Default
    api = pyWATS(error_mode=ErrorMode.LENIENT)

Exception Hierarchy:
    PyWATSError (base)
    ├── NotFoundError (404)
    ├── ValidationError (400)
    ├── AuthenticationError (401)
    ├── AuthorizationError (403)
    ├── ConflictError (409)
    ├── ServerError (5xx)
    ├── EmptyResponseError (200 with no data, STRICT mode only)
    ├── ConnectionError (network failures)
    └── TimeoutError (request timeouts)
"""
from enum import Enum
from typing import Optional, Dict, Any, Type, TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from .client import Response

logger = logging.getLogger(__name__)


class ErrorMode(Enum):
    """Controls how the API handles ambiguous responses."""
    
    STRICT = "strict"
    """
    - 200 with empty/null response raises EmptyResponseError
    - Any non-2xx raises appropriate exception
    - Best for: Production code that needs certainty
    """
    
    LENIENT = "lenient"
    """
    - 200 with empty/null response returns None
    - 404 returns None (for get operations)
    - Only actual errors (5xx, 4xx except 404) raise exceptions
    - Best for: Exploratory code, scripts that handle missing data
    """


class PyWATSError(Exception):
    """
    Base exception for all pyWATS errors.
    
    Attributes:
        message: Human-readable error description
        operation: Name of the operation that failed (e.g., "get_product")
        details: Additional context (without HTTP internals)
        cause: Original exception if this wraps another error
    """

    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        self.message = message
        self.operation = operation
        self.details = details or {}
        self.cause = cause
        super().__init__(message)

    def __str__(self) -> str:
        parts = [self.message]
        if self.operation:
            parts.append(f"Operation: {self.operation}")
        if self.details:
            parts.append(f"Details: {self.details}")
        return " | ".join(parts)
    
    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"operation={self.operation!r}, "
            f"details={self.details!r})"
        )


class AuthenticationError(PyWATSError):
    """Raised when authentication fails (401/403)."""
    pass


class AuthorizationError(PyWATSError):
    """Permission denied (maps from HTTP 403)."""
    pass


class NotFoundError(PyWATSError):
    """Resource not found (maps from HTTP 404)."""

    def __init__(
        self,
        message: Optional[str] = None,
        resource_type: Optional[str] = None,
        identifier: Optional[str] = None,
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.resource_type = resource_type
        self.identifier = identifier
        
        if message is None:
            if resource_type and identifier:
                message = f"{resource_type} '{identifier}' not found"
            else:
                message = "Resource not found"
        
        final_details = details or {}
        if resource_type:
            final_details["resource_type"] = resource_type
        if identifier:
            final_details["identifier"] = identifier
            
        super().__init__(message, operation=operation, details=final_details)


class ValidationError(PyWATSError):
    """Request validation failed (maps from HTTP 400)."""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.field = field
        self.value = value
        final_details = details or {}
        if field:
            final_details["field"] = field
        if value is not None:
            final_details["value"] = str(value)
        super().__init__(message, operation=operation, details=final_details)


class ServerError(PyWATSError):
    """Server-side error (maps from HTTP 5xx)."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.status_code = status_code
        self.response_body = response_body
        final_details = details or {}
        if status_code:
            final_details["status_code"] = status_code
        if response_body:
            final_details["response_body"] = response_body
        super().__init__(message, operation=operation, details=final_details)


class ConflictError(PyWATSError):
    """Resource conflict (maps from HTTP 409)."""
    pass


class EmptyResponseError(PyWATSError):
    """
    Received empty response when data was expected.
    
    Only raised in STRICT mode when:
    - HTTP 200 received but response body is empty/null
    - The operation expected data to be returned
    """
    pass


class ConnectionError(PyWATSError):
    """
    Network/connection failure.
    
    Raised when:
    - Cannot connect to server
    - DNS resolution failure
    """
    pass


class TimeoutError(PyWATSError):
    """Raised when a request times out."""
    pass


# Status code to exception mapping
_STATUS_TO_EXCEPTION: Dict[int, Type[PyWATSError]] = {
    400: ValidationError,
    401: AuthenticationError,
    403: AuthorizationError,
    404: NotFoundError,
    409: ConflictError,
}


class ErrorHandler:
    """
    Translates HTTP responses to domain results based on error mode.
    
    This class is the central point for converting HTTP responses into
    either domain objects or appropriate exceptions, based on the
    configured error mode.
    
    Usage:
        handler = ErrorHandler(mode=ErrorMode.STRICT)
        
        # In repository:
        response = client.get("/api/Product", params={"partNumber": "X"})
        data = handler.handle_response(response, operation="get_product")
        if data is None:
            return None
        return Product.model_validate(data)
    """
    
    def __init__(self, mode: ErrorMode = ErrorMode.STRICT):
        self.mode = mode
        logger.debug(f"ErrorHandler initialized with mode: {mode.value}")
    
    def handle_response(
        self,
        response: "Response",
        operation: str,
        allow_empty: bool = False
    ) -> Any:
        """
        Process HTTP response according to error mode.
        
        Args:
            response: Raw HTTP response from HttpClient
            operation: Name of the operation (for error context)
            allow_empty: Whether empty response is valid for this operation
                        (e.g., DELETE operations that return no content)
            
        Returns:
            Response data (dict, list, or primitive) or None
            
        Raises:
            NotFoundError: Resource not found (404, STRICT mode only)
            ValidationError: Request validation failed (400)
            AuthenticationError: Authentication failed (401)
            AuthorizationError: Permission denied (403)
            ConflictError: Resource conflict (409)
            ServerError: Server error (5xx)
            EmptyResponseError: Empty response when data expected (STRICT mode only)
            ConnectionError: Network failure
        """
        # Handle HTTP errors
        if not response.is_success:
            logger.debug(f"Handling error response: {response.status_code} for {operation}")
            return self._handle_error_response(response, operation)
        
        # Handle empty responses
        if self._is_empty(response.data):
            logger.debug(f"Empty response for {operation} (allow_empty={allow_empty})")
            return self._handle_empty_response(operation, allow_empty)
        
        logger.debug(f"Successful response for {operation}")
        return response.data
    
    def _is_empty(self, data: Any) -> bool:
        """Check if response data is considered empty."""
        if data is None:
            return True
        if isinstance(data, (list, dict)) and len(data) == 0:
            return True
        if isinstance(data, str) and data.strip() == "":
            return True
        return False
    
    def _handle_error_response(
        self, 
        response: "Response", 
        operation: str
    ) -> None:
        """
        Map HTTP error to domain exception or None.
        
        Args:
            response: HTTP response with error status
            operation: Name of the operation
            
        Returns:
            None (in LENIENT mode for 404)
            
        Raises:
            Appropriate PyWATSError subclass
        """
        details = self._extract_error_details(response)
        status_code = response.status_code
        
        # Handle 404 specially in LENIENT mode
        if status_code == 404 and self.mode == ErrorMode.LENIENT:
            logger.info(f"404 for {operation}, returning None (LENIENT mode)")
            return None
        
        # Get appropriate exception class
        exception_class = _STATUS_TO_EXCEPTION.get(status_code)
        
        if exception_class is None:
            if 500 <= status_code < 600:
                exception_class = ServerError
            else:
                exception_class = PyWATSError
        
        # Build error message
        message = details.get("message") or details.get("error") or f"HTTP {status_code}"
        
        logger.error(
            f"{exception_class.__name__} in {operation}: {message}",
            extra={"status_code": status_code, "details": details}
        )
        
        raise exception_class(
            message=message,
            operation=operation,
            details=details
        )
    
    def _handle_empty_response(
        self,
        operation: str,
        allow_empty: bool
    ) -> None:
        """
        Handle 200 with empty body.
        
        Args:
            operation: Name of the operation
            allow_empty: Whether empty is allowed
            
        Returns:
            None
            
        Raises:
            EmptyResponseError (STRICT mode, when not allowed)
        """
        if allow_empty:
            logger.debug(f"Empty response allowed for {operation}")
            return None
        
        if self.mode == ErrorMode.STRICT:
            logger.warning(f"Empty response for {operation}, raising EmptyResponseError (STRICT mode)")
            raise EmptyResponseError(
                message="Received empty response when data was expected",
                operation=operation
            )
        
        logger.info(f"Empty response for {operation}, returning None (LENIENT mode)")
        return None  # LENIENT mode
    
    def _extract_error_details(self, response: "Response") -> Dict[str, Any]:
        """
        Extract error details from response.
        
        Attempts to get structured error info from the response body
        without exposing raw HTTP details.
        """
        details: Dict[str, Any] = {
            "status_code": response.status_code
        }
        
        data = response.data
        
        if isinstance(data, dict):
            # Common error response patterns
            if "message" in data:
                details["message"] = data["message"]
            if "Message" in data:
                details["message"] = data["Message"]
            if "error" in data:
                details["error"] = data["error"]
            if "errors" in data:
                details["errors"] = data["errors"]
            if "detail" in data:
                details["detail"] = data["detail"]
            if "title" in data:
                details["title"] = data["title"]
        elif isinstance(data, str) and data:
            details["message"] = data
        
        return details
