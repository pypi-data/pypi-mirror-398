"""Discovery helpers for LLM/Agent-friendly API exploration.

This module provides methods to discover available fields, filters, enums,
and valid values at runtime - essential for LLMs/Agents to understand
what options are available without hardcoding knowledge.

Usage:
    from pywats.shared import discover

    # Get all fields for a model
    fields = discover.get_model_fields(WATSFilter)
    # Returns: {'part_number': {'type': 'str', 'required': False, ...}, ...}

    # Get enum values
    values = discover.get_enum_values(ProductState)
    # Returns: {'ACTIVE': 1, 'INACTIVE': 0}

    # Get filter field suggestions
    suggestions = discover.get_filter_suggestions()
    # Returns field names grouped by purpose
"""
from typing import Dict, Any, List, Type, Optional, get_type_hints, Union
from enum import Enum
import inspect
from pydantic import BaseModel
from pydantic.fields import FieldInfo


def get_model_fields(model_class: Type[BaseModel]) -> Dict[str, Dict[str, Any]]:
    """
    Get all fields of a Pydantic model with their metadata.
    
    Args:
        model_class: A Pydantic model class (not instance)
        
    Returns:
        Dictionary mapping field names to their metadata:
        - type: The field's type as a string
        - required: Whether the field is required
        - default: Default value if any
        - description: Field description from docstring or Field()
        - alias: Backend API alias if different from field name
        
    Example:
        >>> from pywats.domains.report.models import WATSFilter
        >>> fields = get_model_fields(WATSFilter)
        >>> print(fields['part_number'])
        {
            'type': 'Optional[str]',
            'required': False,
            'default': None,
            'description': 'Filter by product part number',
            'alias': 'partNumber'
        }
    """
    result = {}
    
    # Get type hints for proper type annotation strings
    try:
        hints = get_type_hints(model_class)
    except Exception:
        hints = {}
    
    for field_name, field_info in model_class.model_fields.items():
        # Get type string
        type_str = "Any"
        if field_name in hints:
            type_hint = hints[field_name]
            type_str = _format_type(type_hint)
        
        # Determine if required
        is_required = field_info.is_required()
        
        # Get default
        default = field_info.default if field_info.default is not None else None
        
        # Get description
        description = field_info.description or ""
        
        # Get alias (serialization alias is what goes to the API)
        alias = None
        if field_info.serialization_alias:
            alias = field_info.serialization_alias
        elif field_info.alias:
            alias = field_info.alias
            
        result[field_name] = {
            "type": type_str,
            "required": is_required,
            "default": default,
            "description": description,
            "alias": alias,
        }
    
    return result


def get_required_fields(model_class: Type[BaseModel]) -> List[str]:
    """
    Get list of required field names for a model.
    
    Args:
        model_class: A Pydantic model class
        
    Returns:
        List of required field names
        
    Example:
        >>> from pywats.domains.asset.models import Asset
        >>> required = get_required_fields(Asset)
        >>> print(required)
        ['serial_number', 'type_id']
    """
    return [
        name for name, field_info in model_class.model_fields.items()
        if field_info.is_required()
    ]


def get_optional_fields(model_class: Type[BaseModel]) -> List[str]:
    """
    Get list of optional field names for a model.
    
    Args:
        model_class: A Pydantic model class
        
    Returns:
        List of optional field names
        
    Example:
        >>> from pywats.domains.report.models import WATSFilter
        >>> optional = get_optional_fields(WATSFilter)
        >>> print(optional[:5])
        ['serial_number', 'part_number', 'revision', 'batch_number', 'station_name']
    """
    return [
        name for name, field_info in model_class.model_fields.items()
        if not field_info.is_required()
    ]


def get_enum_values(enum_class: Type[Enum]) -> Dict[str, Any]:
    """
    Get all values of an enum as a dictionary.
    
    Args:
        enum_class: An Enum class
        
    Returns:
        Dictionary mapping enum names to their values
        
    Example:
        >>> from pywats.domains.product.enums import ProductState
        >>> values = get_enum_values(ProductState)
        >>> print(values)
        {'INACTIVE': 0, 'ACTIVE': 1}
    """
    return {member.name: member.value for member in enum_class}


def get_enum_names(enum_class: Type[Enum]) -> List[str]:
    """
    Get all member names of an enum.
    
    Args:
        enum_class: An Enum class
        
    Returns:
        List of enum member names
        
    Example:
        >>> from pywats.domains.asset.enums import AssetState
        >>> names = get_enum_names(AssetState)
        >>> print(names)
        ['OK', 'Warning', 'Alarm', 'Disabled', 'NeedsCalibration', ...]
    """
    return [member.name for member in enum_class]


def get_method_signature(method) -> Dict[str, Any]:
    """
    Get the signature of a method with parameter details.
    
    Args:
        method: A method or function
        
    Returns:
        Dictionary with method metadata:
        - parameters: Dict of param names to their info
        - return_type: Return type annotation
        - docstring: Method docstring
        
    Example:
        >>> from pywats.domains.asset.service import AssetService
        >>> sig = get_method_signature(AssetService.create_asset)
        >>> print(sig['parameters']['serial_number'])
        {'type': 'str', 'required': True, 'default': None}
    """
    sig = inspect.signature(method)
    hints = {}
    try:
        hints = get_type_hints(method)
    except Exception:
        pass
    
    parameters = {}
    for name, param in sig.parameters.items():
        if name == 'self':
            continue
            
        param_info = {
            "type": _format_type(hints.get(name, Any)),
            "required": param.default is inspect.Parameter.empty,
            "default": None if param.default is inspect.Parameter.empty else param.default,
            "kind": str(param.kind).split(".")[-1],  # POSITIONAL_OR_KEYWORD, KEYWORD_ONLY, etc.
        }
        parameters[name] = param_info
    
    return {
        "parameters": parameters,
        "return_type": _format_type(hints.get('return', Any)),
        "docstring": inspect.getdoc(method) or "",
    }


def list_service_methods(service_class: Type) -> Dict[str, str]:
    """
    List all public methods of a service class with their docstrings.
    
    Args:
        service_class: A service class
        
    Returns:
        Dictionary mapping method names to their first line of docstring
        
    Example:
        >>> from pywats.domains.asset.service import AssetService
        >>> methods = list_service_methods(AssetService)
        >>> print(methods['create_asset'])
        'Create a new asset.'
    """
    result = {}
    for name, method in inspect.getmembers(service_class, predicate=inspect.isfunction):
        if name.startswith('_'):
            continue
        doc = inspect.getdoc(method)
        first_line = doc.split('\n')[0] if doc else ""
        result[name] = first_line
    return result


def get_filter_field_categories() -> Dict[str, List[str]]:
    """
    Get WATSFilter fields organized by category.
    
    Returns:
        Dictionary mapping category names to lists of field names.
        
    Example:
        >>> categories = get_filter_field_categories()
        >>> print(categories['identity'])
        ['serial_number', 'part_number', 'revision', 'batch_number']
    """
    return {
        "identity": [
            "serial_number",
            "part_number", 
            "revision",
            "batch_number",
        ],
        "location": [
            "station_name",
            "test_operation",
            "level",
        ],
        "status": [
            "status",  # "Passed", "Failed", "Error"
            "yield_value",
        ],
        "product": [
            "product_group",
        ],
        "software": [
            "sw_filename",
            "sw_version",
        ],
        "misc": [
            "misc_description",
            "misc_value",
            "socket",
        ],
        "date_range": [
            "date_from",
            "date_to",
        ],
        "aggregation": [
            "date_grouping",  # HOUR, DAY, WEEK, MONTH, QUARTER, YEAR
            "period_count",
            "include_current_period",
        ],
        "result_limiting": [
            "max_count",
            "min_count",
            "top_count",
        ],
        "advanced": [
            "dimensions",
            "run",  # 1=first, 2=second, -1=last, -2=all
        ],
    }


def get_valid_status_values() -> List[str]:
    """
    Get valid values for the 'status' filter field.
    
    Returns:
        List of valid status strings
    """
    return ["Passed", "Failed", "Error"]


def get_valid_date_groupings() -> List[str]:
    """
    Get valid values for the 'date_grouping' filter field.
    
    Returns:
        List of valid date grouping strings
    """
    return ["HOUR", "DAY", "WEEK", "MONTH", "QUARTER", "YEAR"]


def get_valid_dimensions() -> List[str]:
    """
    Get valid dimension values for dynamic queries.
    
    These can be used in the 'dimensions' field as a comma-separated string.
    
    Returns:
        List of valid dimension names
    """
    return [
        # Common
        "partNumber",
        "revision",
        "productName",
        "productGroup",
        "unitType",
        "period",
        "level",
        "stationName",
        "location",
        "purpose",
        "operator",
        "batchNumber",
        "testOperation",
        "swFilename",
        "swVersion",
        "processCode",
        "fixtureId",
        "socketIndex",
        "errorCode",
        # Misc info
        "miscInfoDescription",
        "miscInfoString",
        # Yield-specific
        "stepCausedUutFailure",
        "stepPathCausedUutFailure",
        "assetSerialNumber",
        "assetName",
        # Repair-specific
        "repairOperation",
        "repairCode",
        "repairCategory",
        "repairType",
        "componentRef",
        "componentNumber",
        "componentRevision",
        "componentVendor",
        "componentDescription",
        "functionBlock",
        "referencedStep",
        "referencedStepPath",
        # Test-context dimensions (used by repair stats)
        "testPeriod",
        "testLevel",
        "testStationName",
        "testLocation",
        "testPurpose",
        "testOperator",
    ]


def _format_type(type_hint) -> str:
    """Format a type hint as a readable string."""
    if type_hint is None:
        return "None"
    
    # Handle string annotations
    if isinstance(type_hint, str):
        return type_hint
    
    # Get origin for generic types (List, Dict, Optional, etc.)
    origin = getattr(type_hint, '__origin__', None)
    
    if origin is Union:
        args = getattr(type_hint, '__args__', ())
        # Check if it's Optional (Union with None)
        if len(args) == 2 and type(None) in args:
            other = [a for a in args if a is not type(None)][0]
            return f"Optional[{_format_type(other)}]"
        return f"Union[{', '.join(_format_type(a) for a in args)}]"
    
    if origin is list:
        args = getattr(type_hint, '__args__', ())
        if args:
            return f"List[{_format_type(args[0])}]"
        return "List"
    
    if origin is dict:
        args = getattr(type_hint, '__args__', ())
        if len(args) == 2:
            return f"Dict[{_format_type(args[0])}, {_format_type(args[1])}]"
        return "Dict"
    
    # Simple types
    if hasattr(type_hint, '__name__'):
        return type_hint.__name__
    
    return str(type_hint)


# Convenience alias
Any = object  # Placeholder for typing.Any in format function
