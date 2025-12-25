# Unknown Step - Fallback for unsupported step types

from pydantic import Field

# Imports
from ..step import Step


class UnknownStep(Step):
    """
    Fallback step type for unrecognized or unsupported step types.
    
    This class handles step types that are not explicitly supported by pyWATS,
    preventing parsing failures when encountering unknown stepType values.
    It stores all unrecognized fields in extra_data for inspection.
    """
    # Accept any step_type string value for unknown types
    step_type: str = Field(..., validation_alias="stepType", serialization_alias="stepType")
    
    model_config = {
        "extra": "allow",  # Allow and preserve extra fields for forward compatibility
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "use_enum_values": True,
    }
    
    def validate_step(self, trigger_children=False, errors=None) -> bool:
        """Validation always passes for unknown steps"""
        if not super().validate_step(trigger_children=trigger_children, errors=errors):
            return False
        return True
