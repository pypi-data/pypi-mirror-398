from __future__ import annotations  # Enable forward references
from abc import ABC
import base64
from enum import Enum
import os
from typing import Any, Optional, Union, Literal, Annotated

try:
    # Python 3.11+
    from typing import Self
except ImportError:  # pragma: no cover
    # Python 3.10
    from typing_extensions import Self
from pydantic import Field, ModelWrapValidatorHandler, model_validator, Discriminator, Tag
from abc import ABC, abstractmethod

from ..wats_base import WATSBase

from ..chart import Chart, ChartType
from ..additional_data import AdditionalData
from ..attachment import Attachment
# -----------------------------------------------------------------------
# LoopInfo for looping steps
class LoopInfo(WATSBase):
    idx: Optional[int] = Field(default=None)
    num: Optional[int] = Field(default=None)
    ending_index: Optional[int] = Field(default=None, validation_alias="endingIndex",serialization_alias="endingIndex")
    passed: Optional[int] = Field(default=None)
    failed: Optional[int] = Field(default=None)

class StepStatus(Enum):
    Passed = 'P'
    Failed = 'F'
    Skipped = 'S'
    Terminated = 'T'
    Done = 'D'

# -----------------------------------------------------------------------
# Step: Abstract base step for all steps
class Step(WATSBase, ABC):  
    # Parent Step - For internal use only - does not seriallize
    parent: Optional['Step'] = Field(default=None, exclude=True)

    # Required - Base step_type is str to allow subclasses to override with specific Literals
    # This enables Pydantic's discriminated union to work properly
    step_type: str = Field(default="NONE", validation_alias="stepType", serialization_alias="stepType")
    
    name: str = Field(default="StepName", max_length=100, min_length=1)
    group: str = Field(default="M", max_length=1, min_length=1, pattern='^[SMC]$')
    #status: str = Field(default="P", max_length=1, min_length=1, pattern='^[PFSDET]$')
    status: StepStatus = Field(default=StepStatus.Passed)

    id: Optional[Union[int, str]] = Field(default=None)

    # Error code and report text
    error_code: Optional[Union[int, str]] = Field(default=None, validation_alias="errorCode",serialization_alias="errorCode")
    error_code_format: Optional[str] = Field(default=None, validation_alias="errorCodeFormat", serialization_alias="errorCodeFormat")
    error_message: Optional[str] = Field(default=None, validation_alias="errorMessage",serialization_alias="errorMessage")
    report_text: Optional[str] = Field(default=None, validation_alias="reportText",serialization_alias="reportText")
    
    start: Optional[str] = Field(default=None, validation_alias="start",serialization_alias="start")
    tot_time: Optional[Union[float, str]] = Field(default=None, validation_alias="totTime",serialization_alias="totTime")
    tot_time_format: Optional[str] = Field(default=None, validation_alias="totTimeFormat",serialization_alias="totTimeFormat")
    ts_guid: Optional[str] = Field(default=None, validation_alias="tsGuid",serialization_alias="tsGuid")
    
    # Step Caused Failure (ReadOnly)
    caused_seq_failure: Optional[bool] = Field(default=None, validation_alias="causedSeqFailure", serialization_alias="causedSeqFailure")
    caused_uut_failure: Optional[bool] = Field(default=None, validation_alias="causedUUTFailure", serialization_alias="causedUUTFailure")
    
    # LoopInfo
    loop: Optional[LoopInfo] = Field(default=None)
   
    # Additional Results, Charts and Attachments
    additional_results: Optional[list[AdditionalData]] = Field(default=None, validation_alias="additionalResults", serialization_alias="additionalResults")
    
    chart: Optional[Chart] = Field(default=None)
    attachment: Optional[Attachment] = Field(default=None)  



    # validate - all step types
    @abstractmethod
    def validate_step(self, trigger_children=False, errors=None) -> bool:
        # Implement generic step validation here

        # Validate Step
            # Validate LoopInfo
            # Validate Additional Results
            # Validate Chart
            # Validate Attachment

        return True
        # validate_step template:
        # @abstractmethod
        # def validate_step(self, trigger_children=False, errors=None) -> bool:
        #     if errors is None:
        #         errors = []
        #     if not super().validate_step(trigger_children=trigger_children, errors=errors):
        #         return False
        #     # Current Class Validation:
        #       # For every validation failure        
        #           errors.append(f"{self.get_step_path()} ErrorMessage.")
        #     return True

    # return the steps path
    def get_step_path(self) -> str:
        path = []
        current_step = self
        while current_step is not None:
            path.append(current_step.name)
            current_step = current_step.parent
        return '/'.join(reversed(path))

    # Add chart to any step
    def add_chart(self, chart_type:ChartType, chart_label: str, x_label:str, x_unit:str, y_label: str, y_unit: str) -> Chart:
        self.chart = Chart(chart_type=chart_type, label=chart_label, xLabel=x_label, yLabel=y_label, xUnit=x_unit, yUnit=y_unit)
        return self.chart
    
    # Attach a file to the step        
    def attach_file(self, file_name: str, delete_after_upload: bool = False) -> None:
        """
        Reads a file, encodes its contents in base64, and stores it in the data property.
        Optionally deletes the file after reading it.
        
        :param file_name: The name or path of the file to attach
        :param delete_after_upload: Whether to delete the file after attaching it (default is True)
        """
        if self.attachment is None:
            self.attachment = Attachment(name="New attachment")
        try:
            with open(file_name, 'rb') as file:
                # Read the file and encode it in base64
                binary_content = file.read()
                self.attachment.data = base64.b64encode(binary_content).decode('utf-8')
                # Optionally delete the file
                if delete_after_upload:
                    os.remove(file_name)
        except (OSError, IOError) as e:
            raise ValueError(f"Failed to attach file '{file_name}': {e}") from e
        
        # Set the name of the attachment as the filename
        self.attachment.name = os.path.basename(file_name)
        import mimetypes
        self.attachment.content_type, _ = mimetypes.guess_type(file_name, strict=False)


        

# Discriminator function for StepType Union
# Maps stepType values to the appropriate Step class tag
def _discriminate_step_type(v: Any) -> str:
    """
    Discriminator function for step types.
    Returns a tag identifying which Step class should handle this data.
    Falls back to 'unknown' for unrecognized step types.
    """
    if isinstance(v, dict):
        step_type = v.get('stepType', v.get('step_type', ''))
    else:
        step_type = getattr(v, 'step_type', getattr(v, 'stepType', ''))
    
    # Map stepType values to class tags
    # Order matters: Check more specific types first
    if step_type in ['SequenceCall', 'WATS_SeqCall']:
        return 'SequenceCall'
    elif step_type in ['ET_CHAR']:
        return 'ChartStep'
    elif step_type in ['ET_MNLT']:
        return 'MultiNumericStep'
    elif step_type in ['ET_NLT', 'NumericLimitStep']:
        return 'NumericStep'
    elif step_type in ['ET_MPFT']:
        return 'MultiBooleanStep'
    elif step_type in ['ET_PFT', 'PassFailStep']:
        return 'BooleanStep'
    elif step_type in ['ET_MSVT']:
        return 'MultiStringStep'
    elif step_type in ['ET_SVT', 'StringValueStep']:
        return 'StringStep'
    elif step_type in ['CallExe']:
        return 'CallExeStep'
    elif step_type in ['MessagePopup']:
        return 'MessagePopUpStep'
    elif step_type in ['Action']:
        return 'ActionStep'
    # GenericStep types (flow control, etc.)
    elif step_type in [
        "NI_FTPFiles", "NI_Flow_If", "NI_Flow_ElseIf", "NI_Flow_Else", "NI_Flow_End",
        "NI_Flow_For", "NI_Flow_ForEach", "NI_Flow_Break", "NI_Flow_Continue",
        "NI_Flow_DoWhile", "NI_Flow_While", "NI_Flow_Select", "NI_Flow_Case",
        "NI_Flow_StreamLoop", "NI_Flow_SweepLoop", "NI_Lock", "NI_Rendezvous",
        "NI_Queue", "NI_Notification", "NI_Wait", "NI_Batch_Sync", "NI_AutoSchedule",
        "NI_UseResource", "NI_ThreadPriority", "NI_Semaphore", "NI_BatchSpec",
        "NI_BatchSync", "NI_OpenDatabase", "NI_OpenSQLStatement",
        "NI_CloseSQLStatement", "NI_CloseDatabase", "NI_DataOperation",
        "NI_CPUAffinity", "NI_IviDmm", "NI_IviScope", "NI_IviFgen", "NI_IviDCPower",
        "NI_IviSwitch", "NI_IviTools", "NI_LV_DeployLibrary", "NI_LV_CheckSystemStatus",
        "NI_LV_RunVIAsynchronously", "NI_PropertyLoader", "NI_VariableAndPropertyLoader",
        "NI_NewCsvFileInputRecordStream", "NI_NewCsvFileOutputRecordStream",
        "NI_WriteRecord", "Goto", "Statement", "Label"
    ]:
        return 'GenericStep'
    else:
        # Unknown/unsupported step type - fallback to UnknownStep
        return 'unknown'

# Union of all Step types with discriminated union for robust parsing
# The discriminator function maps stepType values to the appropriate class,
# with UnknownStep as the ultimate fallback for unrecognized types.
StepType = Annotated[
    Union[
        Annotated['SequenceCall', Tag('SequenceCall')],
        Annotated['ChartStep', Tag('ChartStep')],
        Annotated['MultiNumericStep', Tag('MultiNumericStep')],
        Annotated['NumericStep', Tag('NumericStep')],
        Annotated['MultiBooleanStep', Tag('MultiBooleanStep')],
        Annotated['BooleanStep', Tag('BooleanStep')],
        Annotated['MultiStringStep', Tag('MultiStringStep')],
        Annotated['StringStep', Tag('StringStep')],
        Annotated['CallExeStep', Tag('CallExeStep')],
        Annotated['MessagePopUpStep', Tag('MessagePopUpStep')],
        Annotated['ActionStep', Tag('ActionStep')],
        Annotated['GenericStep', Tag('GenericStep')],
        Annotated['UnknownStep', Tag('unknown')]
    ],
    Discriminator(_discriminate_step_type)
]

# Import step classes after StepType definition to avoid circular imports
from .steps import NumericStep,MultiNumericStep,SequenceCall,BooleanStep,MultiBooleanStep,MultiStringStep,StringStep,ChartStep,CallExeStep,MessagePopUpStep,GenericStep,ActionStep,UnknownStep  # noqa: E402

Step.model_rebuild()
