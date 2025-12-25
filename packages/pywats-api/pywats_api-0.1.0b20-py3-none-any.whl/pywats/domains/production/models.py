"""Production domain models - pure data classes."""
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from pydantic import Field, AliasChoices

from ...shared import PyWATSModel, Setting
from .enums import SerialNumberIdentifier

if TYPE_CHECKING:
    from ..product.models import Product, ProductRevision


class UnitPhase(PyWATSModel):
    """
    Represents a unit phase in WATS.
    
    Unit phases are predefined states that units can be in during their lifecycle.
    These are constant values defined server-side. Each phase ID is a power of 2,
    allowing potential bitwise combination for filtering.
    
    See Also:
        UnitPhaseFlag: Enum with predefined phase values for type-safe usage.
    
    Phase Values (from UnitPhaseFlag enum):
        - UNKNOWN = 1
        - UNDER_PRODUCTION = 2
        - PRODUCTION_REPAIR = 4
        - SERVICE_REPAIR = 8
        - FINALIZED = 16
        - SCRAPPED = 32
        - EXTENDED_TEST = 64
        - CUSTOMIZATION = 128
        - REPAIRED = 256
        - MISSING = 512
        - IN_STORAGE = 1024
        - SHIPPED = 2048
    
    Attributes:
        phase_id: Unique phase identifier (power of 2)
        code: Machine-readable code (e.g., "Finalized", "Under_Production")
        name: Human-readable name (e.g., "Finalized", "Under production")
        description: Optional description
    """
    phase_id: int = Field(
        validation_alias=AliasChoices("UnitPhaseId", "unitPhaseId", "phase_id"),
        serialization_alias="UnitPhaseId"
    )
    code: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("Code", "code"),
        serialization_alias="Code"
    )
    name: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("Name", "name"),
        serialization_alias="Name"
    )
    description: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("Description", "description"),
        serialization_alias="Description"
    )
    
    def __str__(self) -> str:
        """String representation."""
        return f"{self.name} (ID={self.phase_id})"
    
    def __repr__(self) -> str:
        """Detailed representation."""
        return f"UnitPhase(id={self.phase_id}, code='{self.code}', name='{self.name}')"


class SerialNumberType(PyWATSModel):
    """
    Represents a serial number type configuration.

    Attributes:
        name: Type name
        description: Type description
        format: Serial number format pattern
        reg_ex: Validation regex
        identifier: Identifier type (0=SerialNumber, 1=MAC, 2=IMEI)
        identifier_name: Human readable identifier name
    """
    name: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    format: Optional[str] = Field(default=None)
    reg_ex: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("regEx", "reg_ex"),
        serialization_alias="regEx"
    )
    identifier: SerialNumberIdentifier = Field(
        default=SerialNumberIdentifier.SERIAL_NUMBER
    )
    identifier_name: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("identifierName", "identifier_name"),
        serialization_alias="identifierName"
    )


class ProductionBatch(PyWATSModel):
    """
    Represents a production batch.

    Attributes:
        batch_number: Batch number/identifier
        batch_size: Number of units in batch
    """
    batch_number: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("batchNumber", "batch_number"),
        serialization_alias="batchNumber"
    )
    batch_size: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("batchSize", "batch_size"),
        serialization_alias="batchSize"
    )


class UnitChange(PyWATSModel):
    """
    Represents a unit change record.

    Attributes:
        id: Change record ID
        unit_serial_number: Serial number of the unit
        new_parent_serial_number: New parent serial number
        new_part_number: New part number
        new_revision: New revision
        new_unit_phase_id: New unit phase ID
    """
    id: Optional[int] = Field(default=None)
    unit_serial_number: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("unitSerialNumber", "unit_serial_number"),
        serialization_alias="unitSerialNumber"
    )
    new_parent_serial_number: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(
            "newParentSerialNumber", "new_parent_serial_number"
        ),
        serialization_alias="newParentSerialNumber"
    )
    new_part_number: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("newPartNumber", "new_part_number"),
        serialization_alias="newPartNumber"
    )
    new_revision: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("newRevision", "new_revision"),
        serialization_alias="newRevision"
    )
    new_unit_phase_id: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("newUnitPhaseId", "new_unit_phase_id"),
        serialization_alias="newUnitPhaseId"
    )


class Unit(PyWATSModel):
    """
    Represents a production unit in WATS.

    Attributes:
        serial_number: Unit serial number
        part_number: Product part number
        revision: Product revision
        parent_serial_number: Parent unit serial number
        batch_number: Production batch number
        serial_date: Serial number assignment date
        current_location: Current location
        xml_data: XML document with custom data
        unit_phase_id: Current unit phase ID
        unit_phase: Current unit phase name (read-only)
        process_code: Current process code
        tags: Custom key-value tags (read-only)
        product_revision: Associated product revision
        product: Associated product
        sub_units: Child units
    """
    serial_number: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("serialNumber", "serial_number"),
        serialization_alias="serialNumber"
    )
    part_number: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("partNumber", "part_number"),
        serialization_alias="partNumber"
    )
    revision: Optional[str] = Field(default=None)
    parent_serial_number: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(
            "parentSerialNumber", "parent_serial_number"
        ),
        serialization_alias="parentSerialNumber"
    )
    batch_number: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("batchNumber", "batch_number"),
        serialization_alias="batchNumber"
    )
    serial_date: Optional[datetime] = Field(
        default=None,
        validation_alias=AliasChoices("serialDate", "serial_date"),
        serialization_alias="serialDate"
    )
    current_location: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("currentLocation", "current_location"),
        serialization_alias="currentLocation"
    )
    xml_data: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("xmlData", "xml_data"),
        serialization_alias="xmlData"
    )
    unit_phase_id: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("unitPhaseId", "unit_phase_id"),
        serialization_alias="unitPhaseId"
    )
    unit_phase: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("unitPhase", "unit_phase"),
        serialization_alias="unitPhase"
    )
    process_code: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("processCode", "process_code"),
        serialization_alias="processCode"
    )
    tags: List[Setting] = Field(default_factory=list)
    # Note: These would be Product/ProductRevision but kept as Any to avoid
    # circular imports. In practice, parsed as dicts or use lazy imports.
    product_revision: Optional["ProductRevision"] = Field(
        default=None,
        validation_alias=AliasChoices("productRevision", "product_revision"),
        serialization_alias="productRevision"
    )
    product: Optional["Product"] = Field(default=None)
    sub_units: List["Unit"] = Field(
        default_factory=list,
        validation_alias=AliasChoices("subUnits", "sub_units"),
        serialization_alias="subUnits"
    )


class UnitVerification(PyWATSModel):
    """
    Represents unit verification result for a single process.

    Attributes:
        process_code: Test operation code
        process_name: Test operation name
        process_index: Test operation order index
        status: Unit test status in this process
        start_utc: Test start date and time
        station_name: Name of test station
        total_count: How many times the unit was tested
        non_passed_count: How many times the unit didn't pass
        repair_count: How many times the unit was repaired
    """
    process_code: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("processCode", "process_code"),
        serialization_alias="processCode"
    )
    process_name: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("processName", "process_name"),
        serialization_alias="processName"
    )
    process_index: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("processIndex", "process_index"),
        serialization_alias="processIndex"
    )
    status: Optional[str] = Field(default=None)
    start_utc: Optional[datetime] = Field(
        default=None,
        validation_alias=AliasChoices("startUtc", "start_utc"),
        serialization_alias="startUtc"
    )
    station_name: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("stationName", "station_name"),
        serialization_alias="stationName"
    )
    total_count: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("totalCount", "total_count"),
        serialization_alias="totalCount"
    )
    non_passed_count: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("nonPassedCount", "non_passed_count"),
        serialization_alias="nonPassedCount"
    )
    repair_count: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("repairCount", "repair_count"),
        serialization_alias="repairCount"
    )


class UnitVerificationGrade(PyWATSModel):
    """
    Represents complete unit verification grade result.

    Attributes:
        status: Unit status
        grade: Unit grade
        all_processes_executed_in_correct_order: Unit tested in correct order
        all_processes_passed_first_run: Unit passed each process first time
        all_processes_passed_any_run: Unit passed at some point in each process
        all_processes_passed_last_run: Unit eventually passed each process
        no_repairs: Unit never needed repair
        results: Unit results per process
    """
    status: Optional[str] = Field(default=None)
    grade: Optional[str] = Field(default=None)
    all_processes_executed_in_correct_order: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "allProcessesExecutedInCorrectOrder",
            "all_processes_executed_in_correct_order"
        ),
        serialization_alias="allProcessesExecutedInCorrectOrder"
    )
    all_processes_passed_first_run: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "allProcessesPassedFirstRun",
            "all_processes_passed_first_run"
        ),
        serialization_alias="allProcessesPassedFirstRun"
    )
    all_processes_passed_any_run: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "allProcessesPassedAnyRun",
            "all_processes_passed_any_run"
        ),
        serialization_alias="allProcessesPassedAnyRun"
    )
    all_processes_passed_last_run: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "allProcessesPassedLastRun",
            "all_processes_passed_last_run"
        ),
        serialization_alias="allProcessesPassedLastRun"
    )
    no_repairs: bool = Field(
        default=False,
        validation_alias=AliasChoices("noRepairs", "no_repairs"),
        serialization_alias="noRepairs"
    )
    results: List[UnitVerification] = Field(default_factory=list)
