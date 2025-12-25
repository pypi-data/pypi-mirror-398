"""Base model for all pyWATS models.

Provides consistent Pydantic 2 configuration for serialization/deserialization.

IMPORTANT FOR API CONSUMERS (including LLMs/Agents):
=====================================================

This library uses Pydantic field aliases for backend API compatibility.
The WATS backend REST API uses camelCase naming (e.g., "partNumber", "serialNumber"),
but this Python library exposes snake_case field names for Pythonic usage.

ALWAYS USE PYTHON FIELD NAMES (snake_case) when creating or accessing models:

    ✅ CORRECT:
        report = WATSFilter(part_number="WIDGET-001", serial_number="SN123")
        print(report.part_number)
        
    ❌ WRONG (do NOT use camelCase aliases):
        report = WATSFilter(partNumber="WIDGET-001")  # Will NOT work as expected
        
The aliases (camelCase) exist ONLY for:
    - Deserializing JSON responses from the WATS backend API
    - Serializing to JSON when sending requests to the backend API

They are NOT intended for direct use in Python code.
"""
from pydantic import BaseModel, ConfigDict


class PyWATSModel(BaseModel):
    """
    Base class for all pyWATS models.

    Provides consistent Pydantic 2 configuration for serialization/deserialization.
    
    IMPORTANT - Field Naming Convention:
    ------------------------------------
    All fields use Python snake_case naming. The backend REST API uses camelCase,
    but this is handled automatically via Pydantic aliases.
    
    When creating model instances, ALWAYS use the Python field names:
    
        # Correct usage - use snake_case field names
        filter = WATSFilter(
            part_number="PN23X2",           # NOT "partNumber"
            serial_number="SN-12345",       # NOT "serialNumber"  
            station_name="TestStation",     # NOT "stationName"
        )
        
        # Accessing fields - use snake_case
        print(filter.part_number)           # NOT filter.partNumber
        
    The model_config includes `populate_by_name=True` which allows BOTH
    the Python field name AND the alias to be used during model creation.
    However, for consistency and clarity, always prefer the Python field names.
    
    Backend Alias Reference:
    ------------------------
    Common field mappings (Python name -> Backend alias):
        - part_number -> partNumber
        - serial_number -> serialNumber
        - station_name -> stationName
        - product_group -> productGroup
        - date_from -> dateFrom
        - date_to -> dateTo
        - created_utc -> createdUtc
        - modified_utc -> modifiedUtc
        
    See individual model classes for complete field documentation.
    """
    model_config = ConfigDict(
        populate_by_name=True,          # Allow using field names or aliases
        use_enum_values=True,           # Serialize enums as values
        arbitrary_types_allowed=True,   # Allow custom types
        from_attributes=True,           # Allow creating from ORM objects
        validate_assignment=True,       # Validate on attribute assignment
    )
