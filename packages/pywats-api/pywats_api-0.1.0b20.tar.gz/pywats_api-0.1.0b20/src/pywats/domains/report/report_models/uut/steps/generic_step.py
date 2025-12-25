# NI_Step

# Type/lib
from typing import Literal, Optional
from pydantic import Field
from enum import Enum

# Imports
from ..step import Step
# Example json object and schema:

class FlowType(Enum):
    FTPFiles = "NI_FTPFiles"
    If = "NI_Flow_If"
    ElseIf = "NI_Flow_ElseIf"
    Else = "NI_Flow_Else"
    End = "NI_Flow_End"
    For = "NI_Flow_For"
    ForEach = "NI_Flow_ForEach"
    Break = "NI_Flow_Break"
    Continue = "NI_Flow_Continue"
    DoWhile = "NI_Flow_DoWhile"
    While = "NI_Flow_While"
    Select = "NI_Flow_Select"
    Case = "NI_Flow_Case"
    NI_Flow_StreamLoop = "NI_Flow_StreamLoop"
    NI_Flow_SweepLoop = "NI_Flow_SweepLoop"
    Lock = "NI_Lock"
    Rendezvous = "NI_Rendezvous"
    Queue = "NI_Queue"
    Notification = "NI_Notification"
    Wait = "NI_Wait"
    Batch_Sync = "NI_Batch_Sync"
    AutoSchedule = "NI_AutoSchedule"
    UseResource = "NI_UseResource"
    ThreadPriority = "NI_ThreadPriority"
    Semaphore = "NI_Semaphore"
    BatchSpec = "NI_BatchSpec"
    BatchSync = "NI_BatchSync"
    OpenDatabase = "NI_OpenDatabase"
    OpenSQLStatement = "NI_OpenSQLStatement"
    CloseSQLStatement = "NI_CloseSQLStatement"
    CloseDatabase = "NI_CloseDatabase"
    DataOperation = "NI_DataOperation"
    NI_CPUAffinity = "NI_CPUAffinity"
    NI_IviDmm = "NI_IviDmm"
    NI_IviScope = "NI_IviScope"
    NI_IviFgen = "NI_IviFgen"
    NI_IviDCPower = "NI_IviDCPower"
    NI_IviSwitch = "NI_IviSwitch"
    NI_IviTools = "NI_IviTools"
    NI_LV_DeployLibrary = "NI_LV_DeployLibrary"
    LV_CheckSystemStatus = "NI_LV_CheckSystemStatus"
    LV_RunVIAsynchronously = "NI_LV_RunVIAsynchronously"
    NI_PropertyLoader = "NI_PropertyLoader"
    NI_VariableAndPropertyLoader = "NI_VariableAndPropertyLoader"
    NI_NewCsvFileInputRecordStream = "NI_NewCsvFileInputRecordStream"
    NI_NewCsvFileOutputRecordStream = "NI_NewCsvFileOutputRecordStream"
    NI_WriteRecord = "NI_WriteRecord"
    Goto = "Goto"
    Action = "Action"
    Statement = "Statement"
    Label = "Label"

# Define all possible GenericStep step_type values as a Literal
# This is required for Pydantic's discriminated union to work correctly
# NOTE: "Action" is included because it's just a GenericStep with a specific literal value
# used to select the correct icon. Only specialized steps like NumericStep, StringStep,
# BooleanStep, SequenceCall, and ChartStep have their own dedicated classes.
GenericStepLiteral = Literal[
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
    "NI_WriteRecord", "Goto", "Action", "Statement", "Label"
]

# Class: GenericStep
# A step type that displays flow icon and handles all flow control step types
# Uses explicit Literal to work with Pydantic's discriminated union
class GenericStep(Step):
    # Use Literal with all FlowType values for proper discriminator support
    # This ensures Pydantic can correctly discriminate GenericStep from other types
    step_type: GenericStepLiteral = Field(..., validation_alias="stepType", serialization_alias="stepType")

    def validate_step(self, trigger_children=False, errors=None) -> bool:
        if not super().validate_step(trigger_children=trigger_children, errors=errors):
            return False
        return True
