"""Shared components for pyWATS.

Contains base models, common types, validators, and discovery helpers used across domains.

For LLM/Agent Integration:
--------------------------
- Use `discover` module to explore available fields, methods, and valid values
- Use `Result`, `Success`, `Failure` for structured error handling
- All models use snake_case field names (not camelCase aliases)
"""
from .base_model import PyWATSModel
from .common_types import Setting, ChangeType
from .result import Result, Success, Failure, ErrorCode, failure_from_exception
from . import discovery as discover

__all__ = [
    # Base model
    "PyWATSModel",
    # Common types
    "Setting",
    "ChangeType",
    # Result types for structured error handling
    "Result",
    "Success",
    "Failure",
    "ErrorCode",
    "failure_from_exception",
    # Discovery module for API exploration
    "discover",
]
