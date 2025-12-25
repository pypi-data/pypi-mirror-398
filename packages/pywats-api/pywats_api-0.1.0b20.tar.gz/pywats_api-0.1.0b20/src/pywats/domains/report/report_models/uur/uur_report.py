"""
Complete UURReport implementation.

Based on C# UURReport specification - full API compatibility with all methods:
AddFailure, AddUURPartInfo, fail code navigation, attachments, validation.
"""

from typing import List, Optional, TYPE_CHECKING, Union, Any
from datetime import datetime
from uuid import UUID, uuid4
from pydantic import Field

from .uur_info import UURInfo
from ..report import Report
from ..sub_unit import SubUnit

# Import all the new UUR models
from .fail_code import FailCode, FailCodes
from .misc_uur_info import MiscUURInfo, MiscUURInfoCollection
from .uur_attachment import UURAttachment
from .uur_part_info import UURPartInfo
from .failure import Failure
from .uur_sub_unit import UURSubUnit, UURFailure

if TYPE_CHECKING:
    from ....pywats import pyWATS


class UURReport(Report):
    """
    A unit under repair report (UUR).
    
    Complete implementation based on C# UURReport specification with full API compatibility.
    """
    
    # Overloads
    type: str = Field(default="R", pattern='^[R]$')
    
    # Override sub_units to use UURSubUnit (with idx, parentIdx, failures)
    sub_units: Optional[List[UURSubUnit]] = Field(default_factory=list, validation_alias="subUnits", serialization_alias="subUnits")
    
    # UUR Specific  
    uur_info: UURInfo = Field(default_factory=UURInfo, validation_alias="uur", serialization_alias="uur")
    
    def __init__(self, **data):
        """Initialize UUR report"""
        super().__init__(**data)
        
        # Internal state
        self._repair_type_selected: Optional[object] = None  # RepairType reference
        self._misc_info: Optional[MiscUURInfoCollection] = None
        self._part_infos: List[UURPartInfo] = []
        self._failures: List[Failure] = []
        self._attachments: List[UURAttachment] = []
        self._fail_codes: Optional[FailCodes] = None
        self._failure_index = 0
        self._api: Optional['pyWATS'] = None  # Reference to pyWATS client
        
        # Initialize main unit (index 0) if not exists
        self._ensure_main_unit()
        # Also ensure sub_units has main unit for serialization
        self._ensure_main_sub_unit()
    
    def _ensure_main_unit(self):
        """Ensure main unit (index 0) exists in internal part_infos"""
        if not self._part_infos:
            main_unit = UURPartInfo(
                uur_report=self,
                part_index=0,
                part_number=getattr(self, 'pn', ''),
                serial_number=getattr(self, 'sn', ''),
                part_revision_number=getattr(self, 'rev', ''),
                parent_idx=0
            )
            self._part_infos.append(main_unit)
    
    def _ensure_main_sub_unit(self):
        """Ensure main unit (idx=0) exists in sub_units for serialization"""
        if self.sub_units is None:
            self.sub_units = []
        
        # Check if main unit (idx=0) already exists
        has_main = any(su.idx == 0 for su in self.sub_units)
        if not has_main:
            # Create main unit with report's pn/sn/rev
            main_sub = UURSubUnit.create_main_unit(
                pn=self.pn,
                sn=self.sn,
                rev=self.rev or ""
            )
            # Insert at beginning
            self.sub_units.insert(0, main_sub)
    
    def get_main_sub_unit(self) -> UURSubUnit:
        """Get the main sub unit (idx=0)"""
        self._ensure_main_sub_unit()
        for su in self.sub_units:
            if su.idx == 0:
                return su
        # Should never happen after _ensure_main_sub_unit
        raise ValueError("Main sub unit not found")
    
    def add_uur_sub_unit(
        self,
        pn: str,
        sn: str,
        rev: str = "",
        part_type: str = "SubUnit"
    ) -> UURSubUnit:
        """
        Add a sub unit to the UUR for serialization.
        
        Args:
            pn: Part number
            sn: Serial number
            rev: Revision
            part_type: Type of sub unit
            
        Returns:
            The created UURSubUnit
        """
        if self.sub_units is None:
            self.sub_units = []
        
        # Get next index
        max_idx = max((su.idx for su in self.sub_units), default=-1)
        new_idx = max_idx + 1
        
        sub_unit = UURSubUnit(
            pn=pn,
            sn=sn,
            rev=rev,
            part_type=part_type,
            idx=new_idx,
            parent_idx=0  # Default to main unit as parent
        )
        self.sub_units.append(sub_unit)
        return sub_unit
    
    def add_failure_to_main_unit(
        self,
        category: str,
        code: str,
        comment: Optional[str] = None,
        component_ref: Optional[str] = None,
        ref_step_id: Optional[int] = None
    ) -> UURFailure:
        """
        Add a failure to the main unit (idx=0).
        
        This is the most common case - logging a failure on the main unit.
        
        Args:
            category: Failure category (e.g., "Component Failure")
            code: Failure code
            comment: Optional comment
            component_ref: Component reference (e.g., "C12")
            ref_step_id: Optional step ID from UUT
            
        Returns:
            The created UURFailure
        """
        main_unit = self.get_main_sub_unit()
        return main_unit.add_failure(
            category=category,
            code=code,
            comment=comment,
            component_ref=component_ref,
            ref_step_id=ref_step_id
        )
    
    # === Core Properties (C# API compatibility) ===
    
    @property
    def comment(self) -> Optional[str]:
        """Comment on repair"""
        return self.uur_info.comment
    
    @comment.setter
    def comment(self, value: Optional[str]):
        """Set comment on repair"""
        self.uur_info.comment = value
    
    @property
    def uut_guid(self) -> UUID:
        """Referenced UUT Guid"""
        return self.uur_info.refUUT or UUID('00000000-0000-0000-0000-000000000000')
    
    @uut_guid.setter
    def uut_guid(self, value: UUID):
        """Set referenced UUT GUID"""
        self.uur_info.refUUT = value
    
    @property
    def operation_type(self) -> dict:
        """The test report operation type, e.g. PCBA test, Calibration, Final Function etc."""
        return self.uur_info.get_test_operation_info()
    
    @operation_type.setter  
    def operation_type(self, value: dict):
        """Set operation type from dictionary with code, name, guid"""
        if isinstance(value, dict):
            self.uur_info.test_operation_code = value.get('code')
            self.uur_info.test_operation_name = value.get('name')
            if 'guid' in value and value['guid']:
                self.uur_info.test_operation_guid = UUID(value['guid'])
    
    @property
    def repair_type_selected(self) -> Optional[object]:
        """Repair type"""
        return self._repair_type_selected
    
    @repair_type_selected.setter
    def repair_type_selected(self, value: object):
        """Set repair type"""
        self._repair_type_selected = value
        # Initialize misc info collection from repair type
        # TODO: Initialize from actual repair type when available
    
    @property
    def operator(self) -> Optional[str]:
        """Name of the operator that performed the repair"""
        return self.uur_info.uur_operator
    
    @operator.setter
    def operator(self, value: Optional[str]):
        """Set operator name"""
        self.uur_info.uur_operator = value
    
    @property
    def part_info(self) -> List[UURPartInfo]:
        """Returns array of registered sub-parts"""
        return self._part_infos.copy()
    
    @property
    def confirmed(self) -> Optional[datetime]:
        """UUR was finalize date time (UTC) - not currently displayed in the UUR report"""
        return self.uur_info.confirmDate
    
    @confirmed.setter
    def confirmed(self, value: datetime):
        """Set confirmed date"""
        self.uur_info.confirmDate = value
    
    @property
    def finalized(self) -> Optional[datetime]:
        """UUR was finalize date time (UTC)"""
        return self.uur_info.finalizeDate
    
    @finalized.setter
    def finalized(self, value: datetime):
        """Set finalized date"""
        self.uur_info.finalizeDate = value
    
    @property
    def api(self) -> Optional['pyWATS']:
        """Get reference to pyWATS API client for validation and fail code lookup."""
        return self._api
    
    @api.setter
    def api(self, value: 'pyWATS'):
        """Set reference to pyWATS API client."""
        self._api = value
        # Load fail codes when API is set
        if value and self.process_code:
            try:
                self._load_fail_codes()
            except Exception as e:
                import logging
                logging.getLogger(__name__).debug(f"Could not load fail codes: {e}")
    
    @property
    def execution_time(self) -> float:
        """Time spent on UUR report (seconds)"""
        return self.uur_info.execution_time
    
    @execution_time.setter
    def execution_time(self, value: float):
        """Set execution time"""
        self.uur_info.execution_time = value
    
    @property
    def failures(self) -> List[Failure]:
        """Returns array of failures belonging to main unit"""
        return [f for f in self._failures if f.part_index == 0]
    
    @property
    def misc_info(self) -> Optional[MiscUURInfoCollection]:
        """Collection of valid MiscInfo fields for the selected repair type"""
        return self._misc_info
    
    @misc_info.setter
    def misc_info(self, value: MiscUURInfoCollection):
        """Set misc info collection"""
        self._misc_info = value
    
    @property
    def misc_uur_info(self) -> List[MiscUURInfo]:
        """Misc repair information"""
        return self._misc_info.to_array() if self._misc_info else []
    
    @property
    def attachments(self) -> List[UURAttachment]:
        """Get files attached to this UUR (report-level attachments)"""
        return [a for a in self._attachments if not a.is_failure_attachment]
    
    # === Fail Code Navigation Methods ===
    
    def get_root_failcodes(self) -> List[FailCode]:
        """Get the root list of fail codes for this repair type"""
        if self._fail_codes:
            return self._fail_codes.get_root_fail_codes()
        return []
    
    def get_child_fail_codes(self, fail_code: FailCode) -> List[FailCode]:
        """Get the list of fail codes that belongs to a fail code"""
        if self._fail_codes:
            return self._fail_codes.get_child_fail_codes(fail_code)
        return fail_code.child_fail_codes
    
    def get_fail_code(self, fail_code_id: UUID) -> Optional[FailCode]:
        """Get a Fail code given its id"""
        if self._fail_codes:
            return self._fail_codes.get_fail_code(fail_code_id)
        return None
    
    # === Part Management Methods ===
    
    def add_uur_part_info(self, part_number: str, part_serial_number: str, 
                          part_revision_number: str) -> UURPartInfo:
        """
        Adds a UUR sub-unit.
        
        Args:
            part_number: Part number of the sub-unit
            part_serial_number: Serial number of the sub-unit
            part_revision_number: Revision number of the sub-unit
            
        Returns:
            UURPartInfo object for the new sub-unit
        """
        part_index = len(self._part_infos)
        
        part_info = UURPartInfo(
            uur_report=self,
            part_index=part_index,
            part_number=part_number,
            serial_number=part_serial_number,
            part_revision_number=part_revision_number,
            parent_idx=0  # Single-level hierarchy
        )
        
        self._part_infos.append(part_info)
        return part_info
    
    def get_part_info_by_index(self, index: int) -> Optional[UURPartInfo]:
        """Get part info by index"""
        try:
            return self._part_infos[index] if index < len(self._part_infos) else None
        except IndexError:
            return None
    
    def remove_part_info(self, part_info: UURPartInfo) -> bool:
        """
        Remove a part info (cannot remove main unit at index 0).
        
        Args:
            part_info: Part info to remove
            
        Returns:
            True if removed, False if not found or is main unit
        """
        if part_info.part_index == 0:
            return False  # Cannot remove main unit
        
        try:
            self._part_infos.remove(part_info)
            # Also remove associated failures
            self._failures = [f for f in self._failures if f.part_index != part_info.part_index]
            return True
        except ValueError:
            return False
    
    # === Failure Management Methods ===
    
    def _add_failure_internal(self, fail_code: FailCode, component_reference: str, 
                             part_index: int) -> Failure:
        """
        Internal method to add a failure (used by UURPartInfo).
        
        Args:
            fail_code: Valid fail code
            component_reference: Reference to component
            part_index: Index of part this failure belongs to
            
        Returns:
            Created Failure object
        """
        # Validate fail code is selectable
        is_valid, error = fail_code.validate_for_selection()
        if not is_valid:
            raise ValueError(f"Cannot add failure: {error}")
        
        failure = Failure(
            uur_report=self,
            fail_code_guid=str(fail_code.id),
            part_idx=part_index,
            component_reference=component_reference
        )
        
        # Set fail code metadata
        failure.set_fail_code_metadata(
            category="",  # TODO: Get from fail code tree
            code=fail_code.description,
            description=fail_code.description
        )
        
        self._failures.append(failure)
        self._failure_index += 1
        
        return failure
    
    def add_failure(self, fail_code: FailCode, component_reference: str, 
                   comment: str = "", step_order_number: int = 0) -> Failure:
        """
        Adds a failure to the repaired unit (main unit, index 0).
        
        Args:
            fail_code: Valid fail code
            component_reference: Reference to component
            comment: Comment about the failure
            step_order_number: UUT step order number
            
        Returns:
            Created Failure object
        """
        failure = self._add_failure_internal(fail_code, component_reference, 0)
        failure.component_reference = component_reference
        failure.comment = comment
        failure.failed_step_order_number = step_order_number
        
        return failure
    
    def get_failures_by_part_index(self, part_index: int) -> List[Failure]:
        """Get all failures for a specific part index"""
        return [f for f in self._failures if f.part_index == part_index]
    
    def remove_failure(self, failure: Failure) -> bool:
        """
        Remove a failure.
        
        Args:
            failure: Failure to remove
            
        Returns:
            True if removed, False if not found
        """
        try:
            self._failures.remove(failure)
            return True
        except ValueError:
            return False
    
    # === Attachment Methods ===
    
    def attach_file(self, file_name: str, delete_after_attach: bool = False) -> UURAttachment:
        """
        Attaches a file to the repair report.
        
        Args:
            file_name: Full path and name of file
            delete_after_attach: If true, the file is deleted after being attached
            
        Returns:
            UURAttachment object
        """
        attachment = UURAttachment(
            uur_report=self,
            file_path=file_name,
            delete_after_attach=delete_after_attach
        )
        self._attachments.append(attachment)
        return attachment
    
    def attach_byte_array(self, label: str, content: bytes, mime_type: str = "") -> UURAttachment:
        """
        Attaches a byte array to the repair report.
        
        Args:
            label: Will be shown in WATS as a label to the attachment
            content: Byte array (binary data) to be attached
            mime_type: MIME type for the content
            
        Returns:
            UURAttachment object
        """
        if not mime_type:
            mime_type = "application/octet-stream"
        
        attachment = UURAttachment(
            uur_report=self,
            label=label,
            content=content,
            mime_type=mime_type
        )
        self._attachments.append(attachment)
        return attachment
    
    def remove_attachment(self, attachment: UURAttachment) -> bool:
        """
        Remove an attachment.
        
        Args:
            attachment: Attachment to remove
            
        Returns:
            True if removed, False if not found
        """
        try:
            self._attachments.remove(attachment)
            return True
        except ValueError:
            return False
    
    # === Validation and Utility Methods ===
    
    def validate_uur(self) -> tuple[bool, str]:
        """
        Validate this UUR report.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        errors = []
        
        # Validate dual process codes
        is_valid, error = self.uur_info.validate_dual_process_codes()
        if not is_valid:
            errors.append(f"Process codes: {error}")
        
        # Validate main unit exists
        if not self._part_infos or self._part_infos[0].part_index != 0:
            errors.append("Main unit (index 0) is required")
        
        # Validate part infos
        for part_info in self._part_infos:
            is_valid, error = part_info.validate_part_info()
            if not is_valid:
                errors.append(f"Part {part_info.part_index}: {error}")
        
        # Validate failures
        for i, failure in enumerate(self._failures):
            is_valid, error = failure.validate_failure()
            if not is_valid:
                errors.append(f"Failure {i}: {error}")
        
        # Validate misc info
        if self._misc_info:
            validation_errors = self._misc_info.validate_all()
            errors.extend(validation_errors)
        
        # Validate attachments
        for i, attachment in enumerate(self._attachments):
            is_valid, error = attachment.validate_size()
            if not is_valid:
                errors.append(f"Attachment {i}: {error}")
        
        if errors:
            return False, "; ".join(errors)
        
        return True, ""
    
    def _load_fail_codes(self):
        """Load fail codes from API (internal method)."""
        if not self._api:
            return
        
        try:
            # Use internal API to get fail codes for this repair process
            if hasattr(self._api, 'process_internal'):
                fail_code_list = self._api.process_internal.get_fail_codes(self.process_code)
                # Store as dictionary keyed by GUID for quick lookup
                self._fail_codes = {fc['guid']: fc for fc in fail_code_list}
        except Exception as e:
            import logging
            logging.getLogger(__name__).debug(f"Failed to load fail codes from API: {e}")
    
    def get_fail_code(self, guid: Union[str, UUID]) -> Optional[FailCode]:
        """Get a fail code by GUID.
        
        Args:
            guid: The fail code GUID (string or UUID)
            
        Returns:
            FailCode object if found, None otherwise
        """
        # Ensure fail codes are loaded
        if not self._fail_codes and self._api:
            self._load_fail_codes()
        
        if not self._fail_codes:
            return None
        
        # Convert to string for comparison
        guid_str = str(guid)
        
        # Look up fail code
        fc_data = self._fail_codes.get(guid_str)
        if not fc_data:
            return None
        
        # Create FailCode object
        return FailCode(
            guid=UUID(fc_data['guid']),
            description=fc_data.get('description', ''),
            category=fc_data.get('category', ''),
            category_guid=UUID(fc_data.get('category_guid', '00000000-0000-0000-0000-000000000000')),
            failure_type=fc_data.get('failure_type'),
            selectable=fc_data.get('selectable', True)
        )
    
    def get_summary(self) -> dict:
        """Get summary information about this UUR report"""
        return {
            'type': 'UUR',
            'uut_guid': str(self.uut_guid),
            'operator': self.operator,
            'comment': self.comment,
            'part_count': len(self._part_infos),
            'failure_count': len(self._failures),
            'attachment_count': len(self._attachments),
            'misc_info_count': len(self.misc_uur_info),
            'execution_time': self.execution_time,
            'confirmed': self.confirmed.isoformat() if self.confirmed else None,
            'finalized': self.finalized.isoformat() if self.finalized else None
        }
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation"""
        # Build dictionary manually
        base_dict = {'type': self.type}
        
        uur_dict = {
            'uur_summary': self.get_summary(),
            'part_infos': [part.to_dict() for part in self._part_infos],
            'failures': [failure.to_dict() for failure in self._failures],
            'attachments': [attachment.to_dict() for attachment in self._attachments],
            'misc_info': [info.to_dict() for info in self.misc_uur_info]
        }
        
        return {**base_dict, **uur_dict}


