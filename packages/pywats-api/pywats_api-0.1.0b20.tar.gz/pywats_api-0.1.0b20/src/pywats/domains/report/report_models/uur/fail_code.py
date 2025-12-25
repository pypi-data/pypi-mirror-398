"""
FailCode model for UUR reports.

Based on C# FailCode specification - represents repair fail codes with tree navigation.
"""

from typing import List, Optional
from uuid import UUID
from enum import IntEnum

from pydantic import BaseModel


class FailureTypeEnum(IntEnum):
    """Failure type enumeration for WATS reporting purposes"""
    UNKNOWN = 0
    COMPONENT = 1
    MANUFACTURING = 2
    DESIGN = 3
    TEST_EQUIPMENT = 4


class FailCode(BaseModel):
    """
    Repair fail code - can be either a category (non-selectable) or a selectable fail code.
    
    Based on C# FailCode class specification.
    """
    
    def __init__(self, guid: UUID, description: str, selectable: bool = True, 
                 sort_order: int = 0, failure_type: FailureTypeEnum = FailureTypeEnum.UNKNOWN,
                 child_fail_codes: Optional[List['FailCode']] = None):
        """
        Initialize a fail code.
        
        Args:
            guid: Unique fail code identifier
            description: Human-readable description
            selectable: True if this is a selectable fail code, False if category
            sort_order: Sorting order for display
            failure_type: Type of failure for reporting
            child_fail_codes: Child fail codes (for categories)
        """
        super().__init__()
        self._guid = guid
        self._description = description
        self._selectable = selectable
        self._sort_order = sort_order
        self._failure_type = failure_type
        self._child_fail_codes = child_fail_codes or []
    
    @property
    def id(self) -> UUID:
        """Unique fail code ID"""
        return self._guid
    
    @property
    def guid(self) -> UUID:
        """Unique fail code GUID (alias for id)"""
        return self._guid
    
    @property
    def selectable(self) -> bool:
        """True if this is a selectable fail code, False if it is a fail code category"""
        return self._selectable
    
    @property
    def description(self) -> str:
        """Fail code description"""
        return self._description
    
    @property
    def sort_order(self) -> int:
        """Sorting order"""
        return self._sort_order
    
    @property
    def failure_type(self) -> FailureTypeEnum:
        """For WATS reporting purposes, use this enum"""
        return self._failure_type
    
    @property
    def is_category(self) -> bool:
        """True if this is a category (has children), False if leaf fail code"""
        return not self._selectable and len(self._child_fail_codes) > 0
    
    @property
    def child_fail_codes(self) -> List['FailCode']:
        """Get child fail codes (for categories)"""
        return self._child_fail_codes.copy()
    
    def add_child_fail_code(self, child: 'FailCode'):
        """Add a child fail code (for categories)"""
        if self._selectable:
            raise ValueError("Cannot add children to selectable fail codes")
        self._child_fail_codes.append(child)
    
    def find_fail_code(self, guid: UUID) -> Optional['FailCode']:
        """
        Recursively search for a fail code by GUID in this tree.
        
        Args:
            guid: GUID to search for
            
        Returns:
            FailCode if found, None otherwise
        """
        if self._guid == guid:
            return self
        
        # Search in children
        for child in self._child_fail_codes:
            result = child.find_fail_code(guid)
            if result:
                return result
        
        return None
    
    def get_all_selectable_fail_codes(self) -> List['FailCode']:
        """Get all selectable fail codes in this tree"""
        result = []
        
        if self._selectable:
            result.append(self)
        
        for child in self._child_fail_codes:
            result.extend(child.get_all_selectable_fail_codes())
        
        return result
    
    def validate_for_selection(self) -> tuple[bool, str]:
        """
        Validate that this fail code can be selected for a failure.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self._selectable:
            return False, f"Fail code '{self._description}' is a category and cannot be selected"
        
        return True, ""
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation"""
        return {
            'guid': str(self._guid),
            'description': self._description,
            'selectable': self._selectable,
            'sort_order': self._sort_order,
            'failure_type': self._failure_type.value,
            'is_category': self.is_category,
            'child_count': len(self._child_fail_codes)
        }
    
    def __str__(self) -> str:
        return f"FailCode({self._description}, selectable={self._selectable})"
    
    def __repr__(self) -> str:
        return f"FailCode(guid={self._guid}, description='{self._description}', selectable={self._selectable})"


class FailCodes:
    """
    Collection class for managing fail code trees for repair types.
    
    Based on C# FailCodes class specification.
    """
    
    def __init__(self, root_fail_codes: List[FailCode]):
        """
        Initialize with root fail codes.
        
        Args:
            root_fail_codes: List of top-level fail codes/categories
        """
        self._root_fail_codes = root_fail_codes
    
    def get_root_fail_codes(self) -> List[FailCode]:
        """Returns list of fail codes on the root level"""
        return self._root_fail_codes.copy()
    
    def get_child_fail_codes(self, fail_code: FailCode) -> List[FailCode]:
        """
        Get child fail codes of a fail code.
        
        Args:
            fail_code: Parent fail code
            
        Returns:
            List of child fail codes
        """
        return fail_code.child_fail_codes
    
    def get_fail_code(self, fail_code_id: UUID) -> Optional[FailCode]:
        """
        Get a fail code by its GUID.
        
        Args:
            fail_code_id: GUID of the fail code to find
            
        Returns:
            FailCode if found, None otherwise
        """
        for root in self._root_fail_codes:
            result = root.find_fail_code(fail_code_id)
            if result:
                return result
        
        return None
    
    def get_all_selectable_fail_codes(self) -> List[FailCode]:
        """Get all selectable fail codes from all trees"""
        result = []
        for root in self._root_fail_codes:
            result.extend(root.get_all_selectable_fail_codes())
        return result
    
    def validate_fail_code_for_selection(self, fail_code_id: UUID) -> tuple[bool, str]:
        """
        Validate that a fail code exists and can be selected.
        
        Args:
            fail_code_id: GUID of fail code to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        fail_code = self.get_fail_code(fail_code_id)
        if not fail_code:
            return False, f"Fail code with GUID {fail_code_id} not found"
        
        return fail_code.validate_for_selection()