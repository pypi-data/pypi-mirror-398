"""Structured result types for LLM/Agent-friendly error handling.

This module provides standardized result types that give clear, actionable
feedback instead of returning None or raising opaque exceptions.

Usage:
    from pywats.shared import Result, Success, Failure

    # Returning results from service methods
    def create_product(self, part_number: str) -> Result[Product]:
        if not part_number:
            return Failure(
                error_code="INVALID_INPUT",
                message="part_number is required",
                details={"field": "part_number"}
            )
        product = self._repository.save(Product(part_number=part_number))
        if product:
            return Success(product)
        return Failure(
            error_code="SAVE_FAILED",
            message="Failed to save product to repository"
        )

    # Consuming results
    result = service.create_product("WIDGET-001")
    if result.is_success:
        product = result.value
        print(f"Created: {product.part_number}")
    else:
        print(f"Error [{result.error_code}]: {result.message}")
"""
from typing import TypeVar, Generic, Optional, Dict, Any, Union, List
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict

T = TypeVar("T")


class ErrorCode(str, Enum):
    """Standard error codes for pyWATS operations.
    
    These codes help LLMs/Agents understand what went wrong and how to fix it.
    """
    # Validation errors
    INVALID_INPUT = "INVALID_INPUT"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_FORMAT = "INVALID_FORMAT"
    VALUE_OUT_OF_RANGE = "VALUE_OUT_OF_RANGE"
    
    # Resource errors
    NOT_FOUND = "NOT_FOUND"
    ALREADY_EXISTS = "ALREADY_EXISTS"
    CONFLICT = "CONFLICT"
    
    # Operation errors
    OPERATION_FAILED = "OPERATION_FAILED"
    SAVE_FAILED = "SAVE_FAILED"
    DELETE_FAILED = "DELETE_FAILED"
    
    # Authentication/Authorization
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    
    # Network/API errors
    CONNECTION_ERROR = "CONNECTION_ERROR"
    TIMEOUT = "TIMEOUT"
    API_ERROR = "API_ERROR"
    
    # Unknown
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


class Failure(BaseModel):
    """Represents a failed operation with structured error information.
    
    Attributes:
        error_code: Machine-readable error code (use ErrorCode enum values)
        message: Human-readable error description
        details: Additional context (field names, values, suggestions)
        suggestions: List of suggested fixes or next steps
        
    Example:
        >>> failure = Failure(
        ...     error_code="MISSING_REQUIRED_FIELD",
        ...     message="part_number is required to create a product",
        ...     details={"field": "part_number", "received": None},
        ...     suggestions=["Provide a unique part_number string"]
        ... )
    """
    model_config = ConfigDict(
        use_enum_values=True,
        arbitrary_types_allowed=True,
    )
    
    error_code: str = Field(
        ...,
        description="Machine-readable error code (use ErrorCode enum values)"
    )
    message: str = Field(
        ...,
        description="Human-readable error description"
    )
    details: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context (field names, values, etc.)"
    )
    suggestions: List[str] = Field(
        default_factory=list,
        description="List of suggested fixes or next steps"
    )
    
    @property
    def is_success(self) -> bool:
        """Always False for Failure."""
        return False
    
    @property
    def is_failure(self) -> bool:
        """Always True for Failure."""
        return True
    
    @property
    def value(self) -> None:
        """Failures have no value."""
        return None
    
    def __str__(self) -> str:
        result = f"[{self.error_code}] {self.message}"
        if self.suggestions:
            result += f" Suggestions: {', '.join(self.suggestions)}"
        return result


class Success(BaseModel, Generic[T]):
    """Represents a successful operation with a value.
    
    Attributes:
        value: The result value of the operation
        message: Optional success message
        
    Example:
        >>> product = Product(part_number="WIDGET-001")
        >>> success = Success(value=product, message="Product created")
        >>> print(success.value.part_number)
        WIDGET-001
    """
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )
    
    value: Any = Field(
        ...,
        description="The result value of the operation"
    )
    message: str = Field(
        default="",
        description="Optional success message"
    )
    
    @property
    def is_success(self) -> bool:
        """Always True for Success."""
        return True
    
    @property
    def is_failure(self) -> bool:
        """Always False for Success."""
        return False
    
    @property
    def error_code(self) -> None:
        """Success has no error code."""
        return None
    
    def __str__(self) -> str:
        if self.message:
            return f"Success: {self.message}"
        return f"Success: {type(self.value).__name__}"


# Type alias for Result - either Success or Failure
Result = Union[Success[T], Failure]


def failure_from_exception(exc: Exception, error_code: str = "UNKNOWN_ERROR") -> Failure:
    """Create a Failure from an exception.
    
    Args:
        exc: The exception to convert
        error_code: Error code to use (default: UNKNOWN_ERROR)
        
    Returns:
        Failure with exception details
        
    Example:
        >>> try:
        ...     risky_operation()
        ... except ValueError as e:
        ...     return failure_from_exception(e, "INVALID_INPUT")
    """
    return Failure(
        error_code=error_code,
        message=str(exc),
        details={
            "exception_type": type(exc).__name__,
        }
    )
