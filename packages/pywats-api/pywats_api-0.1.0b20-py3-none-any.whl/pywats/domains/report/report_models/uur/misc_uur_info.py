"""
MiscUURInfo models for UUR reports.

Based on C# MiscUURInfo and MiscUURInfoCollection specifications - handles misc repair
information fields with regex validation and collection indexing.
"""

import re
from typing import List, Dict, Iterator, Optional, Union, Any, TYPE_CHECKING
from uuid import UUID

from pydantic import BaseModel

if TYPE_CHECKING:
    from .uur_report import UURReport


class MiscUURInfo(BaseModel):
    """
    Misc information attached to a UUR.
    
    Based on C# MiscUURInfo class specification.
    """
    
    def __init__(self, guid: UUID, description: str, valid_regex: str = "", 
                 input_mask: str = "", value: str = "", report: Optional['UURReport'] = None):
        """
        Initialize misc UUR info.
        
        Args:
            guid: Unique identifier for this misc info field
            description: Human-readable description (e.g., "SWVer1")
            valid_regex: Regular expression for validation (may contain multiple alternatives separated by ';')
            input_mask: GUI input mask hint
            value: The string value of the info (e.g., "1.15.3")
            report: Reference to parent UUR report
        """
        super().__init__()
        self._guid = guid
        self._description = description
        self._valid_regex = valid_regex
        self._input_mask = input_mask
        self._value = value
        self._report = report
        
        # Precompiled regex and allowed literals
        self._compiled_regex: Optional[re.Pattern] = None
        self._allowed_literals: List[str] = []
        self._is_required = False
        
        self._compile_validation()
    
    def _compile_validation(self):
        """Precompile regex and extract allowed literals"""
        if self._valid_regex:
            # Check if regex contains multiple alternatives separated by ';'
            if ';' in self._valid_regex:
                # Treat as literal list
                self._allowed_literals = [lit.strip() for lit in self._valid_regex.split(';') if lit.strip()]
                self._is_required = "" not in self._allowed_literals
            else:
                # Treat as regex pattern
                try:
                    self._compiled_regex = re.compile(self._valid_regex)
                    # Check if empty string matches (determines if field is required)
                    self._is_required = not bool(self._compiled_regex.match(""))
                except re.error:
                    # If regex is invalid, treat as single literal
                    self._allowed_literals = [self._valid_regex]
                    self._is_required = self._valid_regex != ""
    
    @property
    def id(self) -> UUID:
        """Internal GUID identifier"""
        return self._guid
    
    @property
    def description(self) -> str:
        """The information description, e.g. SWVer1"""
        return self._description
    
    @property
    def valid_regular_expression(self) -> str:
        """A regular expression that will be validated"""
        return self._valid_regex
    
    @property
    def input_mask(self) -> str:
        """GUI input mask hint"""
        return self._input_mask
    
    @property
    def data_string(self) -> str:
        """The string value of the info, e.g. 1.15.3"""
        return self._value
    
    @data_string.setter
    def data_string(self, value: str):
        """Set the string value with validation."""
        # Validate value against regex/literals
        is_valid, error = self.validate_value_string(value)
        if not is_valid:
            raise ValueError(error)
        
        self._value = value
    
    @property
    def value(self) -> str:
        """Alias for data_string"""
        return self.data_string
    
    @value.setter
    def value(self, val: str):
        """Set value (alias for data_string setter)"""
        self.data_string = val
    
    @property
    def is_required(self) -> bool:
        """True if this field cannot be empty"""
        return self._is_required
    
    def validate_value_string(self, value: str) -> tuple[bool, str]:
        """Validate a value string against regex/literals.
        
        Args:
            value: The value to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not value:
            if self._is_required:
                return False, f"Field '{self._description}' cannot be blank"
            return True, ""
        
        # Try regex first
        if self._compiled_regex:
            if self._compiled_regex.match(value):
                return True, ""
            return False, f"Field '{self._description}' does not match required pattern"
        
        # Try literal list
        if self._allowed_literals:
            if value in self._allowed_literals:
                return True, ""
            return False, f"Field '{self._description}' must be one of: {', '.join(self._allowed_literals)}"
        
        # No validation rules - accept anything
        return True, ""
    
    def validate_value(self) -> tuple[bool, str]:
        """
        Validate current value against regex/literals.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        return self.validate_value_string(self._value)
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation"""
        return {
            'guid': str(self._guid),
            'description': self._description,
            'value': self._value,
            'valid_regex': self._valid_regex,
            'input_mask': self._input_mask,
            'is_required': self._is_required
        }
    
    def __str__(self) -> str:
        return f"MiscUURInfo({self._description}={self._value})"


class MiscUURInfoCollection:
    """
    Collection of misc UUR info with indexing by ordinal or description.
    
    Based on C# MiscUURInfoColletion class specification.
    """
    
    def __init__(self, misc_infos: Optional[List[MiscUURInfo]] = None):
        """
        Initialize collection.
        
        Args:
            misc_infos: Initial list of misc info objects
        """
        self._items: List[MiscUURInfo] = []
        self._by_description: Dict[str, MiscUURInfo] = {}
        self._by_guid: Dict[UUID, MiscUURInfo] = {}
        
        if misc_infos:
            for info in misc_infos:
                self.add(info)
    
    def add(self, info: MiscUURInfo):
        """Add misc info to collection"""
        # Check for duplicate description (case-insensitive)
        desc_lower = info.description.lower()
        existing_desc = next((k for k in self._by_description.keys() if k.lower() == desc_lower), None)
        if existing_desc:
            raise ValueError(f"Misc info with description '{info.description}' already exists")
        
        self._items.append(info)
        self._by_description[info.description] = info
        self._by_guid[info.id] = info
    
    def __getitem__(self, key: Union[int, str]) -> Union[MiscUURInfo, str]:
        """
        Collection property accessor for UUR MiscInfo.
        
        Args:
            key: Either ordinal index (int) or description/GUID (str)
            
        Returns:
            MiscUURInfo object for int keys, or data string for str keys
        """
        if isinstance(key, int):
            # Ordinal index - return MiscUURInfo object
            return self._items[key]
        elif isinstance(key, str):
            # Description or GUID - return data string value
            info = self._find_by_string_key(key)
            return info.data_string
        else:
            raise TypeError("Key must be int (ordinal) or str (description/GUID)")
    
    def __setitem__(self, key: Union[int, str], value: str):
        """
        Set value by ordinal index or description.
        
        Args:
            key: Either ordinal index (int) or description/GUID (str)
            value: New data string value
        """
        if isinstance(key, int):
            # Ordinal index
            info = self._items[key]
            info.data_string = value
        elif isinstance(key, str):
            # Description or GUID
            info = self._find_by_string_key(key)
            info.data_string = value
        else:
            raise TypeError("Key must be int (ordinal) or str (description/GUID)")
    
    def _find_by_string_key(self, key: str) -> MiscUURInfo:
        """Find misc info by description or GUID string"""
        # Try description first (case-insensitive)
        for desc, info in self._by_description.items():
            if desc.lower() == key.lower():
                return info
        
        # Try GUID
        try:
            guid = UUID(key)
            if guid in self._by_guid:
                return self._by_guid[guid]
        except ValueError:
            pass
        
        raise KeyError(f"No misc info found with description or GUID '{key}'")
    
    def __len__(self) -> int:
        """Get number of items in collection"""
        return len(self._items)
    
    def __iter__(self) -> Iterator[MiscUURInfo]:
        """Iterate over misc info objects"""
        return iter(self._items)
    
    def get_by_guid(self, guid: UUID) -> Optional[MiscUURInfo]:
        """Get misc info by GUID"""
        return self._by_guid.get(guid)
    
    def get_by_description(self, description: str, case_sensitive: bool = False) -> Optional[MiscUURInfo]:
        """
        Get misc info by description.
        
        Args:
            description: Description to search for
            case_sensitive: Whether to match case-sensitively
            
        Returns:
            MiscUURInfo if found, None otherwise
        """
        if case_sensitive:
            return self._by_description.get(description)
        else:
            desc_lower = description.lower()
            for desc, info in self._by_description.items():
                if desc.lower() == desc_lower:
                    return info
            return None
    
    def validate_all(self) -> List[str]:
        """
        Validate all misc infos and return list of error messages.
        
        Returns:
            List of validation error messages (empty if all valid)
        """
        errors = []
        for info in self._items:
            is_valid, error_msg = info.validate_value()
            if not is_valid:
                errors.append(error_msg)
        return errors
    
    def to_array(self) -> List[MiscUURInfo]:
        """Convert to array (matches C# ToArray() method)"""
        return self._items.copy()
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation"""
        return {
            'items': [info.to_dict() for info in self._items],
            'count': len(self._items)
        }
    
    def __str__(self) -> str:
        return f"MiscUURInfoCollection({len(self._items)} items)"