"""
UURSubUnit model for UUR reports.

Extended SubUnit with repair-specific fields: idx, parentIdx, failures.
Based on WSJF SubUnit schema for repairs.
"""

from typing import List, Optional
from pydantic import Field, ConfigDict

from ..wats_base import WATSBase


class UURFailure(WATSBase):
    """
    Serializable failure for UUR subUnits.
    
    Based on WSJF Failure schema - simpler than the full Failure class
    for serialization purposes.
    """
    category: str = Field(default="Unknown")
    """Failure category."""
    
    code: str = Field(default="Unknown")
    """Failure code."""
    
    comment: Optional[str] = Field(default=None)
    """Failure comment."""
    
    com_ref: Optional[str] = Field(default=None, validation_alias="comRef", serialization_alias="comRef")
    """Component reference."""
    
    func_block: Optional[str] = Field(default=None, validation_alias="funcBlock", serialization_alias="funcBlock")
    """Function block reference."""
    
    ref_step_id: Optional[int] = Field(default=None, validation_alias="refStepId", serialization_alias="refStepId")
    """Id of step from referenced UUT that uncovered failure."""
    
    ref_step_name: Optional[str] = Field(default=None, validation_alias="refStepName", serialization_alias="refStepName")
    """Name of step from referenced UUT that uncovered failure."""
    
    art_number: Optional[str] = Field(default=None, validation_alias="artNumber", serialization_alias="artNumber")
    """Article number of failed component."""
    
    art_rev: Optional[str] = Field(default=None, validation_alias="artRev", serialization_alias="artRev")
    """Failed component revision."""
    
    art_vendor: Optional[str] = Field(default=None, validation_alias="artVendor", serialization_alias="artVendor")
    """Vendor of failed component."""
    
    art_description: Optional[str] = Field(default=None, validation_alias="artDescription", serialization_alias="artDescription")
    """Description of failed component."""
    
    model_config = ConfigDict(populate_by_name=True)


class UURSubUnit(WATSBase):
    """
    Extended SubUnit for UUR reports with repair-specific fields.
    
    Based on WSJF SubUnit schema - includes idx, parentIdx, failures
    which are only used in repairs.
    """
    pn: str = Field(default="", max_length=100)
    """Unit part number."""
    
    rev: Optional[str] = Field(default=None, max_length=100)
    """Unit revision number."""
    
    sn: Optional[str] = Field(default=None, max_length=100)
    """Unit serial number. Can be None/null for main unit failures."""
    
    part_type: Optional[str] = Field(default="Unknown", max_length=50, validation_alias="partType", serialization_alias="partType")
    """Type of unit."""
    
    idx: int = Field(default=0)
    """Unit index (only used in repair). Index 0 is the main unit."""
    
    parent_idx: Optional[int] = Field(default=None, validation_alias="parentIdx", serialization_alias="parentIdx")
    """Index of parent unit (only used in repair)."""
    
    position: Optional[int] = Field(default=None)
    """Position of unit."""
    
    replaced_idx: Optional[int] = Field(default=None, validation_alias="replacedIdx", serialization_alias="replacedIdx")
    """Index of unit this unit was replaced by (only valid for repair)."""
    
    failures: Optional[List[UURFailure]] = Field(default=None)
    """Failures in this unit."""
    
    model_config = ConfigDict(populate_by_name=True)
    
    def add_failure(
        self,
        category: str,
        code: str,
        comment: Optional[str] = None,
        component_ref: Optional[str] = None,
        ref_step_id: Optional[int] = None
    ) -> UURFailure:
        """
        Add a failure to this subunit.
        
        Args:
            category: Failure category (e.g., "Component Failure")
            code: Failure code
            comment: Optional comment about the failure
            component_ref: Component reference (e.g., "C12")
            ref_step_id: Optional step ID from UUT that revealed failure
            
        Returns:
            The created UURFailure
        """
        if self.failures is None:
            self.failures = []
            
        failure = UURFailure(
            category=category,
            code=code,
            comment=comment,
            com_ref=component_ref,
            ref_step_id=ref_step_id
        )
        self.failures.append(failure)
        return failure
    
    @classmethod
    def from_sub_unit(cls, sub_unit, idx: int = 0, parent_idx: Optional[int] = None) -> "UURSubUnit":
        """
        Create UURSubUnit from a basic SubUnit.
        
        Args:
            sub_unit: SubUnit from UUT report
            idx: Index to assign (0 for main unit)
            parent_idx: Parent index
            
        Returns:
            UURSubUnit with copied data and repair fields
        """
        return cls(
            pn=sub_unit.pn,
            rev=sub_unit.rev,
            sn=sub_unit.sn,
            part_type=getattr(sub_unit, 'part_type', 'Unknown'),
            idx=idx,
            parent_idx=parent_idx
        )
    
    @classmethod
    def create_main_unit(cls, pn: str, sn: str, rev: str = "") -> "UURSubUnit":
        """
        Create the main unit (idx=0) for a UUR report.
        
        Args:
            pn: Part number
            sn: Serial number  
            rev: Revision
            
        Returns:
            UURSubUnit configured as main unit (no parentIdx for main unit)
        """
        return cls(
            pn=pn,
            sn=sn,
            rev=rev,
            idx=0,
            parent_idx=None,  # Main unit has no parent
            part_type="Main"
        )
