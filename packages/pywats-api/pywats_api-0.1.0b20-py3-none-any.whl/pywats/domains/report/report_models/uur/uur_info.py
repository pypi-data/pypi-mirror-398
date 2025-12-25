"""
Enhanced UURInfo model for UUR reports.

Based on C# UURReport specification - handles dual process code architecture
(repair process vs test operation) and all missing properties.
"""

from typing import Optional
from datetime import datetime
from uuid import UUID
from pydantic import Field

from ..report_info import ReportInfo


class UURInfo(ReportInfo):
    """
    UUR-specific information with dual process code architecture.
    
    Based on C# UUR_type specification with full API compatibility.
    """
    
    # Dual process codes (key architectural feature)
    repair_process_code: Optional[int] = Field(default=None, validation_alias="repairProcessCode", serialization_alias="repairProcessCode")
    """The repair process code (top-level WATSReport.Process) - what kind of repair operation this is"""
    
    repair_process_name: Optional[str] = Field(default=None, validation_alias="repairProcessName", serialization_alias="repairProcessName")
    """The repair process name"""
    
    test_operation_code: Optional[int] = Field(default=None, validation_alias="testOperationCode", serialization_alias="testOperationCode")
    """The test operation code (UUR_type.Process) - original test operation that was being performed"""
    
    test_operation_name: Optional[str] = Field(default=None, validation_alias="testOperationName", serialization_alias="testOperationName")
    """The test operation name"""
    
    test_operation_guid: Optional[UUID] = Field(default=None, validation_alias="testOperationGuid", serialization_alias="testOperationGuid")
    """The test operation GUID"""
    
    # Legacy fields (API requires processCode in uur object)
    # Note: exclude=False ensures these fields are ALWAYS serialized (even if None)
    process_code: Optional[int] = Field(
        default=None, 
        validation_alias="processCode", 
        serialization_alias="processCode",
        exclude=False  # Always include in serialization
    )
    """Process code - required by API in uur object"""
    
    process_code_format: Optional[str] = Field(default=None, validation_alias="processCodeFormat", serialization_alias="processCodeFormat")
    """Process code format"""
    
    process_name: Optional[str] = Field(default=None, validation_alias="processName", serialization_alias="processName")
    """Process name"""
    
    # UUR-specific properties
    ref_uut: Optional[UUID] = Field(
        default=None, 
        validation_alias="refUUT", 
        serialization_alias="refUUT",
        exclude=False  # Always include in serialization
    )
    """Referenced UUT GUID - the GUID of the UUT report being repaired"""
    
    comment: Optional[str] = Field(default=None)
    """Comment on repair"""
    
    uur_operator: Optional[str] = Field(default=None, validation_alias="userLoginName", serialization_alias="userLoginName")
    """Name of the operator that performed the repair"""
    
    # Timing information
    confirm_date: Optional[datetime] = Field(
        default=None, 
        validation_alias="confirmDate", 
        serialization_alias="confirmDate",
        exclude=False  # Always include in serialization
    )
    """UUR was confirmed date time (UTC)"""
    
    finalize_date: Optional[datetime] = Field(
        default=None, 
        validation_alias="finalizeDate", 
        serialization_alias="finalizeDate",
        exclude=False  # Always include in serialization
    )
    """UUR was finalized date time (UTC)"""
    
    exec_time: Optional[float] = Field(
        default=0.0, 
        validation_alias="execTime", 
        serialization_alias="execTime",
        exclude=False  # Always include in serialization
    )
    """Time spent on UUR report (seconds) - REQUIRED by API"""
    
    # Status flags
    active: bool = Field(default=True)
    """Whether this UUR is active"""
    
    # Hierarchy information (if needed)
    parent: Optional[UUID] = Field(default=None)
    """Parent UUR GUID (for hierarchical repairs)"""
    
    children: Optional[list[UUID]] = Field(default=None)
    """Child UUR GUIDs (for hierarchical repairs)"""
    
    def __init__(self, **data):
        """Initialize UURInfo with dual process code mapping"""
        super().__init__(**data)
        
        # Map process_code to test_operation_code if needed
        if self.process_code is not None and self.test_operation_code is None:
            self.test_operation_code = self.process_code
        
        if self.process_name and not self.test_operation_name:
            self.test_operation_name = self.process_name
    
    @property
    def referenced_uut_guid(self) -> Optional[UUID]:
        """Alias for ref_uut"""
        return self.ref_uut
    
    @referenced_uut_guid.setter
    def referenced_uut_guid(self, value: Optional[UUID]):
        """Set referenced UUT GUID"""
        self.ref_uut = value
    
    @property
    def user_login_name(self) -> Optional[str]:
        """Alias for uur_operator"""
        return self.uur_operator
    
    @user_login_name.setter
    def user_login_name(self, value: Optional[str]):
        """Set operator login name"""
        self.uur_operator = value
    

    @property
    def execution_time(self) -> float:
        """Alias for exec_time"""
        return self.exec_time if self.exec_time is not None else 0.0
    
    @execution_time.setter
    def execution_time(self, value: float):
        """Set execution time"""
        self.exec_time = value
    
    def get_repair_process_info(self) -> dict:
        """
        Get repair process information.
        
        Returns:
            Dictionary with repair process details
        """
        return {
            'code': self.repair_process_code,
            'name': self.repair_process_name,
            'type': 'repair'
        }
    
    def get_test_operation_info(self) -> dict:
        """
        Get test operation information.
        
        Returns:
            Dictionary with test operation details
        """
        return {
            'code': self.test_operation_code,
            'name': self.test_operation_name,
            'guid': str(self.test_operation_guid) if self.test_operation_guid else None,
            'type': 'test'
        }
    
    def set_dual_process_codes(self, repair_code: int, repair_name: str,
                              test_code: int, test_name: str, test_guid: Optional[UUID] = None):
        """
        Set both repair and test process codes.
        
        Args:
            repair_code: Code for the repair operation
            repair_name: Name for the repair operation
            test_code: Code for the original test operation
            test_name: Name for the original test operation
            test_guid: GUID for the original test operation
        """
        # Set repair process
        self.repair_process_code = repair_code
        self.repair_process_name = repair_name
        
        # Set test operation
        self.test_operation_code = test_code
        self.test_operation_name = test_name
        self.test_operation_guid = test_guid
        
        # Update process_code for API compatibility
        self.process_code = test_code
        self.process_name = test_name
    
    def validate_dual_process_codes(self) -> tuple[bool, str]:
        """
        Validate that both process codes are properly set.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        errors = []
        
        if self.repair_process_code is None:
            errors.append("Repair process code is required")
        
        if self.test_operation_code is None:
            errors.append("Test operation code is required")
        
        if not self.repair_process_name:
            errors.append("Repair process name is required")
        
        if not self.test_operation_name:
            errors.append("Test operation name is required")
        
        if errors:
            return False, "; ".join(errors)
        
        return True, ""
    
    def to_uur_type_dict(self) -> dict:
        """
        Convert to WRML UUR_type representation.
        
        Returns:
            Dictionary representing UUR_type structure
        """
        result = {
            'process': {
                'code': self.test_operation_code,
                'code_specified': self.test_operation_code is not None,
                'name': self.test_operation_name
            },
            'user_login_name': self.uur_operator,
            'active': self.active,
            'active_specified': True,
            'comment': self.comment,
            'referenced_uut': str(self.ref_uut) if self.ref_uut else None
        }
        
        if self.test_operation_guid:
            result['process']['guid'] = str(self.test_operation_guid)
        
        if self.confirm_date:
            result['confirm_date'] = self.confirm_date.isoformat()
            result['confirm_date_specified'] = True
        
        if self.finalize_date:
            result['finalize_date'] = self.finalize_date.isoformat()
            result['finalize_date_specified'] = True
        
        if self.exec_time is not None:
            result['execution_time'] = self.exec_time
            result['execution_time_specified'] = True
        
        return result
    
    def to_dict(self) -> dict:
        """Enhanced dictionary representation with dual process codes"""
        # Build dictionary manually instead of calling super()
        base_dict = {}
        
        uur_dict = {
            # Dual process architecture
            'repair_process_code': self.repair_process_code,
            'repair_process_name': self.repair_process_name,
            'test_operation_code': self.test_operation_code,
            'test_operation_name': self.test_operation_name,
            'test_operation_guid': str(self.test_operation_guid) if self.test_operation_guid else None,
            
            # UUR-specific properties
            'referenced_uut_guid': str(self.ref_uut) if self.ref_uut else None,
            'comment': self.comment,
            'operator': self.uur_operator,
            'confirm_date': self.confirm_date.isoformat() if self.confirm_date else None,
            'finalize_date': self.finalize_date.isoformat() if self.finalize_date else None,
            'execution_time': self.exec_time,
            'active': self.active,
            
            # Legacy compatibility
            'process_code': self.process_code,
            'process_name': self.process_name,
            'process_code_format': self.process_code_format
        }
        
        return {**base_dict, **uur_dict}
