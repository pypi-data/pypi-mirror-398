"""Analytics domain models.

Statistics, KPI, and yield analysis data models.

BACKEND API MAPPING
-------------------
These models are returned from the WATS /api/App/* endpoints.
The 'analytics' module name was chosen for clarity while the backend
uses 'App' as the controller name.

FIELD NAMING CONVENTION:
------------------------
All fields use Python snake_case naming (e.g., part_number, station_name).
Backend API aliases (camelCase) are handled automatically.
Always use the Python field names when creating or accessing these models.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import Field, AliasChoices, ConfigDict

from ...shared.base_model import PyWATSModel


# =============================================================================
# Top Failed Analysis Models
# =============================================================================

class TopFailedStep(PyWATSModel):
    """
    Represents a top failed step from failure analysis.
    
    Returned from GET/POST /api/App/TopFailed.
    
    Attributes:
        step_name: Name of the failed step
        step_path: Full path to the step
        step_type: Type of step
        part_number: Product part number
        revision: Product revision
        product_group: Product group
        fail_count: Number of failures
        total_count: Total executions
        fail_rate: Failure rate (0-100)
        first_fail_date: Date of first failure
        last_fail_date: Date of most recent failure
        
    Example:
        >>> step = TopFailedStep(step_name="Voltage Test", fail_count=15, total_count=100)
        >>> print(f"Failure rate: {step.fail_rate}%")
    """

    step_name: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("stepName", "step_name"),
        serialization_alias="stepName",
        description="Name of the failed step"
    )
    step_path: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("stepPath", "step_path"),
        serialization_alias="stepPath",
        description="Full path to the step"
    )
    step_type: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("stepType", "step_type"),
        serialization_alias="stepType",
        description="Type of step"
    )
    step_group: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("stepGroup", "step_group"),
        serialization_alias="stepGroup",
        description="Step group"
    )
    part_number: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("partNumber", "part_number"),
        serialization_alias="partNumber",
        description="Product part number"
    )
    revision: Optional[str] = Field(
        default=None,
        description="Product revision"
    )
    product_group: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("productGroup", "product_group"),
        serialization_alias="productGroup",
        description="Product group"
    )
    fail_count: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("failCount", "fail_count"),
        serialization_alias="failCount",
        description="Number of failures"
    )
    total_count: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("totalCount", "total_count"),
        serialization_alias="totalCount",
        description="Total executions"
    )
    fail_rate: Optional[float] = Field(
        default=None,
        validation_alias=AliasChoices("failRate", "fail_rate"),
        serialization_alias="failRate",
        description="Failure rate (0-100)"
    )
    first_fail_date: Optional[datetime] = Field(
        default=None,
        validation_alias=AliasChoices("firstFailDate", "first_fail_date"),
        serialization_alias="firstFailDate",
        description="Date of first failure"
    )
    last_fail_date: Optional[datetime] = Field(
        default=None,
        validation_alias=AliasChoices("lastFailDate", "last_fail_date"),
        serialization_alias="lastFailDate",
        description="Date of most recent failure"
    )


# =============================================================================
# Repair Statistics Models  
# =============================================================================

class RepairStatistics(PyWATSModel):
    """
    Represents repair statistics data from dynamic repair analysis.
    
    Returned from POST /api/App/DynamicRepair (PREVIEW API).
    
    Supports all dimensions from the Swagger specification (server-dependent):
        partNumber, revision, productName, productGroup, unitType, repairOperation,
        period, level, stationName, location, purpose, operator,
        miscInfoDescription, miscInfoString,
        repairCode, repairCategory, repairType,
        componentRef, componentNumber, componentRevision, componentVendor,
        componentDescription,
        functionBlock, referencedStep, referencedStepPath,
        testOperation, testPeriod, testLevel, testStationName, testLocation,
        testPurpose, testOperator,
        batchNumber, swFilename, swVersion

    Supported KPIs:
        repairReportCount, repairCount

    Attributes:
        part_number: Product part number
        revision: Product revision
        product_name: Product name
        product_group: Product group
        unit_type: Unit type
        repair_operation: Repair operation
        period: Time period
        level: Production level
        station_name: Station where repair occurred
        location: Location
        purpose: Purpose
        operator: Operator
        misc_info_description: Misc info description
        misc_info_string: Misc info string
        repair_code: Repair action code
        repair_category: Repair category
        repair_type: Repair type
        component_ref: Component reference
        component_number: Component number
        component_revision: Component revision
        component_vendor: Component vendor
        component_description: Component description
        function_block: Function block
        referenced_step: Referenced step
        referenced_step_path: Referenced step path
        test_operation: Test operation
        test_period: Test period
        test_level: Test level
        test_station_name: Test station name
        test_location: Test location
        test_purpose: Test purpose
        test_operator: Test operator
        batch_number: Batch number
        sw_filename: Software filename
        sw_version: Software version
        repair_report_count: Number of repair reports (KPI)
        repair_count: Number of repairs (KPI)
        total_count: Total units
        repair_rate: Repair rate (0-100)
        fail_code: Failure code (legacy/deprecated)
        
    Example:
        >>> stats = RepairStatistics(part_number="WIDGET-001", repair_count=5)
        >>> print(f"Repairs: {stats.repair_count}")
    """

    # Preserve forward-compatible fields returned by the backend.
    model_config = ConfigDict(**PyWATSModel.model_config, extra="allow")

    part_number: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("partNumber", "part_number"),
        serialization_alias="partNumber",
        description="Product part number"
    )
    revision: Optional[str] = Field(
        default=None,
        description="Product revision"
    )
    product_group: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("productGroup", "product_group"),
        serialization_alias="productGroup",
        description="Product group"
    )
    product_name: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("productName", "product_name"),
        serialization_alias="productName",
        description="Product name"
    )
    unit_type: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("unitType", "unit_type"),
        serialization_alias="unitType",
        description="Unit type"
    )
    repair_operation: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("repairOperation", "repair_operation"),
        serialization_alias="repairOperation",
        description="Repair operation"
    )
    station_name: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("stationName", "station_name"),
        serialization_alias="stationName",
        description="Station name"
    )
    test_operation: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("testOperation", "test_operation"),
        serialization_alias="testOperation",
        description="Test operation"
    )
    period: Optional[str] = Field(
        default=None,
        description="Time period"
    )
    level: Optional[str] = Field(
        default=None,
        description="Production level"
    )
    location: Optional[str] = Field(
        default=None,
        description="Location"
    )
    purpose: Optional[str] = Field(
        default=None,
        description="Purpose"
    )
    operator: Optional[str] = Field(
        default=None,
        description="Operator"
    )

    misc_info_description: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(
            "miscInfoDescription", "misc_info_description"
        ),
        serialization_alias="miscInfoDescription",
        description="Misc info description"
    )
    misc_info_string: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("miscInfoString", "misc_info_string"),
        serialization_alias="miscInfoString",
        description="Misc info string"
    )

    repair_category: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("repairCategory", "repair_category"),
        serialization_alias="repairCategory",
        description="Repair category"
    )
    repair_type: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("repairType", "repair_type"),
        serialization_alias="repairType",
        description="Repair type"
    )

    component_ref: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("componentRef", "component_ref"),
        serialization_alias="componentRef",
        description="Component reference"
    )
    component_number: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("componentNumber", "component_number"),
        serialization_alias="componentNumber",
        description="Component number"
    )
    component_revision: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(
            "componentRevision", "component_revision"
        ),
        serialization_alias="componentRevision",
        description="Component revision"
    )
    component_vendor: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("componentVendor", "component_vendor"),
        serialization_alias="componentVendor",
        description="Component vendor"
    )
    component_description: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(
            "componentDescription", "component_description"
        ),
        serialization_alias="componentDescription",
        description="Component description"
    )

    function_block: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("functionBlock", "function_block"),
        serialization_alias="functionBlock",
        description="Function block"
    )
    referenced_step: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("referencedStep", "referenced_step"),
        serialization_alias="referencedStep",
        description="Referenced step"
    )
    referenced_step_path: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(
            "referencedStepPath", "referenced_step_path"
        ),
        serialization_alias="referencedStepPath",
        description="Referenced step path"
    )

    test_period: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("testPeriod", "test_period"),
        serialization_alias="testPeriod",
        description="Test period"
    )
    test_level: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("testLevel", "test_level"),
        serialization_alias="testLevel",
        description="Test level"
    )
    test_station_name: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(
            "testStationName", "test_station_name"
        ),
        serialization_alias="testStationName",
        description="Test station name"
    )
    test_location: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("testLocation", "test_location"),
        serialization_alias="testLocation",
        description="Test location"
    )
    test_purpose: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("testPurpose", "test_purpose"),
        serialization_alias="testPurpose",
        description="Test purpose"
    )
    test_operator: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("testOperator", "test_operator"),
        serialization_alias="testOperator",
        description="Test operator"
    )

    batch_number: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("batchNumber", "batch_number"),
        serialization_alias="batchNumber",
        description="Batch number"
    )
    sw_filename: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("swFilename", "sw_filename"),
        serialization_alias="swFilename",
        description="Software filename"
    )
    sw_version: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("swVersion", "sw_version"),
        serialization_alias="swVersion",
        description="Software version"
    )

    repair_report_count: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices(
            "repairReportCount", "repair_report_count"
        ),
        serialization_alias="repairReportCount",
        description="Number of repair reports (KPI)"
    )
    repair_count: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("repairCount", "repair_count"),
        serialization_alias="repairCount",
        description="Number of repairs (KPI)"
    )
    total_count: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("totalCount", "total_count"),
        serialization_alias="totalCount",
        description="Total units"
    )
    repair_rate: Optional[float] = Field(
        default=None,
        validation_alias=AliasChoices("repairRate", "repair_rate"),
        serialization_alias="repairRate",
        description="Repair rate (0-100)"
    )
    fail_code: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("failCode", "fail_code"),
        serialization_alias="failCode",
        description="Failure code (legacy/deprecated)"
    )
    repair_code: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("repairCode", "repair_code"),
        serialization_alias="repairCode",
        description="Repair action code"
    )


class RepairHistoryRecord(PyWATSModel):
    """
    Represents a repair history record for a specific part.
    
    Returned from GET /api/App/RelatedRepairHistory.
    
    Attributes:
        serial_number: Unit serial number
        part_number: Product part number
        revision: Product revision
        report_id: Report ID
        repair_date: Date of repair
        fail_step_name: Name of failed step
        fail_step_path: Path of failed step
        fail_code: Failure code
        repair_code: Repair action code
        symptom: Symptom description
        cause: Root cause
        action: Repair action taken
        
    Example:
        >>> record = RepairHistoryRecord(serial_number="SN001", fail_step_name="Voltage Test")
        >>> print(f"Failed step: {record.fail_step_name}")
    """

    serial_number: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("serialNumber", "serial_number"),
        serialization_alias="serialNumber",
        description="Unit serial number"
    )
    part_number: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("partNumber", "part_number"),
        serialization_alias="partNumber",
        description="Product part number"
    )
    revision: Optional[str] = Field(
        default=None,
        description="Product revision"
    )
    report_id: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("reportId", "report_id"),
        serialization_alias="reportId",
        description="Report ID"
    )
    repair_date: Optional[datetime] = Field(
        default=None,
        validation_alias=AliasChoices("repairDate", "repair_date"),
        serialization_alias="repairDate",
        description="Date of repair"
    )
    fail_step_name: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("failStepName", "fail_step_name"),
        serialization_alias="failStepName",
        description="Name of failed step"
    )
    fail_step_path: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("failStepPath", "fail_step_path"),
        serialization_alias="failStepPath",
        description="Path of failed step"
    )
    fail_code: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("failCode", "fail_code"),
        serialization_alias="failCode",
        description="Failure code"
    )
    repair_code: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("repairCode", "repair_code"),
        serialization_alias="repairCode",
        description="Repair action code"
    )
    symptom: Optional[str] = Field(
        default=None,
        description="Symptom description"
    )
    cause: Optional[str] = Field(
        default=None,
        description="Root cause"
    )
    action: Optional[str] = Field(
        default=None,
        description="Repair action taken"
    )


# =============================================================================
# Measurement Data Models
# =============================================================================

class MeasurementData(PyWATSModel):
    """
    Represents individual measurement data points.
    
    Returned from POST /api/App/Measurements (PREVIEW API).
    
    Attributes:
        serial_number: Unit serial number
        part_number: Product part number
        step_name: Measurement step name
        step_path: Full step path
        value: Measured value
        limit_low: Low limit
        limit_high: High limit
        unit: Unit of measurement
        status: Measurement status (Pass/Fail)
        timestamp: Measurement timestamp
        
    Example:
        >>> data = MeasurementData(step_name="Voltage", value=5.02, limit_low=4.5, limit_high=5.5)
        >>> print(f"{data.step_name}: {data.value}")
    """

    serial_number: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("serialNumber", "serial_number"),
        serialization_alias="serialNumber",
        description="Unit serial number"
    )
    part_number: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("partNumber", "part_number"),
        serialization_alias="partNumber",
        description="Product part number"
    )
    revision: Optional[str] = Field(
        default=None,
        description="Product revision"
    )
    report_id: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("reportId", "report_id"),
        serialization_alias="reportId",
        description="Report ID"
    )
    step_name: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("stepName", "step_name"),
        serialization_alias="stepName",
        description="Measurement step name"
    )
    step_path: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("stepPath", "step_path"),
        serialization_alias="stepPath",
        description="Full step path"
    )
    value: Optional[float] = Field(
        default=None,
        description="Measured value"
    )
    limit_low: Optional[float] = Field(
        default=None,
        validation_alias=AliasChoices("limitLow", "limit_low", "limit1"),
        serialization_alias="limitLow",
        description="Low limit"
    )
    limit_high: Optional[float] = Field(
        default=None,
        validation_alias=AliasChoices("limitHigh", "limit_high", "limit2"),
        serialization_alias="limitHigh",
        description="High limit"
    )
    unit: Optional[str] = Field(
        default=None,
        description="Unit of measurement"
    )
    status: Optional[str] = Field(
        default=None,
        description="Measurement status (Pass/Fail)"
    )
    timestamp: Optional[datetime] = Field(
        default=None,
        description="Measurement timestamp"
    )


class AggregatedMeasurement(PyWATSModel):
    """
    Represents aggregated measurement statistics.
    
    Returned from POST /api/App/AggregatedMeasurements.
    
    Attributes:
        step_name: Measurement step name
        step_path: Full step path
        count: Number of measurements
        min: Minimum value
        max: Maximum value
        avg: Average value
        stdev: Standard deviation
        limit_low: Low limit
        limit_high: High limit
        cpk: Process capability index
        cp: Process capability
        
    Example:
        >>> agg = AggregatedMeasurement(step_name="Voltage", count=1000, avg=5.01, cpk=1.33)
        >>> print(f"{agg.step_name}: Cpk={agg.cpk}")
    """

    step_name: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("stepName", "step_name"),
        serialization_alias="stepName",
        description="Measurement step name"
    )
    step_path: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("stepPath", "step_path"),
        serialization_alias="stepPath",
        description="Full step path"
    )
    part_number: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("partNumber", "part_number"),
        serialization_alias="partNumber",
        description="Product part number"
    )
    revision: Optional[str] = Field(
        default=None,
        description="Product revision"
    )
    count: Optional[int] = Field(
        default=None,
        description="Number of measurements"
    )
    min: Optional[float] = Field(
        default=None,
        description="Minimum value"
    )
    max: Optional[float] = Field(
        default=None,
        description="Maximum value"
    )
    avg: Optional[float] = Field(
        default=None,
        description="Average value"
    )
    stdev: Optional[float] = Field(
        default=None,
        description="Standard deviation"
    )
    variance: Optional[float] = Field(
        default=None,
        validation_alias=AliasChoices("var", "variance"),
        serialization_alias="var",
        description="Variance"
    )
    limit_low: Optional[float] = Field(
        default=None,
        validation_alias=AliasChoices("limitLow", "limit_low", "limit1"),
        serialization_alias="limitLow",
        description="Low limit"
    )
    limit_high: Optional[float] = Field(
        default=None,
        validation_alias=AliasChoices("limitHigh", "limit_high", "limit2"),
        serialization_alias="limitHigh",
        description="High limit"
    )
    cpk: Optional[float] = Field(
        default=None,
        description="Process capability index"
    )
    cp: Optional[float] = Field(
        default=None,
        description="Process capability"
    )
    cp_lower: Optional[float] = Field(
        default=None,
        validation_alias=AliasChoices("cpLower", "cp_lower"),
        serialization_alias="cpLower",
        description="Lower process capability"
    )
    cp_upper: Optional[float] = Field(
        default=None,
        validation_alias=AliasChoices("cpUpper", "cp_upper"),
        serialization_alias="cpUpper",
        description="Upper process capability"
    )
    unit: Optional[str] = Field(
        default=None,
        description="Unit of measurement"
    )


# =============================================================================
# OEE (Overall Equipment Effectiveness) Models
# =============================================================================

class OeeAnalysisResult(PyWATSModel):
    """
    Represents OEE (Overall Equipment Effectiveness) analysis results.
    
    Returned from POST /api/App/OeeAnalysis.
    
    OEE = Availability × Performance × Quality
    
    Attributes:
        oee: Overall Equipment Effectiveness (0-100)
        availability: Availability rate (0-100)
        performance: Performance rate (0-100)
        quality: Quality rate (0-100)
        total_time: Total time in minutes
        run_time: Actual run time in minutes
        down_time: Downtime in minutes
        planned_production_time: Planned production time
        total_count: Total units produced
        good_count: Good units count
        reject_count: Rejected units count
        ideal_cycle_time: Ideal cycle time per unit
        actual_cycle_time: Actual cycle time per unit
        period: Analysis period
        
    Example:
        >>> oee = OeeAnalysisResult(oee=85.0, availability=90.0, performance=95.0, quality=99.5)
        >>> print(f"OEE: {oee.oee}%")
    """

    oee: Optional[float] = Field(
        default=None,
        description="Overall Equipment Effectiveness (0-100)"
    )
    availability: Optional[float] = Field(
        default=None,
        description="Availability rate (0-100)"
    )
    performance: Optional[float] = Field(
        default=None,
        description="Performance rate (0-100)"
    )
    quality: Optional[float] = Field(
        default=None,
        description="Quality rate (0-100)"
    )
    total_time: Optional[float] = Field(
        default=None,
        validation_alias=AliasChoices("totalTime", "total_time"),
        serialization_alias="totalTime",
        description="Total time in minutes"
    )
    run_time: Optional[float] = Field(
        default=None,
        validation_alias=AliasChoices("runTime", "run_time"),
        serialization_alias="runTime",
        description="Actual run time in minutes"
    )
    down_time: Optional[float] = Field(
        default=None,
        validation_alias=AliasChoices("downTime", "down_time"),
        serialization_alias="downTime",
        description="Downtime in minutes"
    )
    planned_production_time: Optional[float] = Field(
        default=None,
        validation_alias=AliasChoices("plannedProductionTime", "planned_production_time"),
        serialization_alias="plannedProductionTime",
        description="Planned production time"
    )
    total_count: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("totalCount", "total_count"),
        serialization_alias="totalCount",
        description="Total units produced"
    )
    good_count: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("goodCount", "good_count"),
        serialization_alias="goodCount",
        description="Good units count"
    )
    reject_count: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("rejectCount", "reject_count"),
        serialization_alias="rejectCount",
        description="Rejected units count"
    )
    ideal_cycle_time: Optional[float] = Field(
        default=None,
        validation_alias=AliasChoices("idealCycleTime", "ideal_cycle_time"),
        serialization_alias="idealCycleTime",
        description="Ideal cycle time per unit"
    )
    actual_cycle_time: Optional[float] = Field(
        default=None,
        validation_alias=AliasChoices("actualCycleTime", "actual_cycle_time"),
        serialization_alias="actualCycleTime",
        description="Actual cycle time per unit"
    )
    period: Optional[str] = Field(
        default=None,
        description="Analysis period"
    )
    part_number: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("partNumber", "part_number"),
        serialization_alias="partNumber",
        description="Product part number"
    )
    station_name: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("stationName", "station_name"),
        serialization_alias="stationName",
        description="Station name"
    )


# =============================================================================
# Yield Statistics Models
# =============================================================================

class YieldData(PyWATSModel):
    """
    Represents yield statistics data.

    Attributes:
        part_number: Product part number (use this, not 'partNumber')
        revision: Product revision
        product_name: Product name (use this, not 'productName')
        product_group: Product group (use this, not 'productGroup')
        station_name: Test station name (use this, not 'stationName')
        test_operation: Test operation (use this, not 'testOperation')
        period: Time period
        unit_count: Total unit count (use this, not 'unitCount')
        fp_count: First pass count (use this, not 'fpCount')
        sp_count: Second pass count
        tp_count: Third pass count
        lp_count: Last pass count
        fpy: First pass yield
        spy: Second pass yield
        tpy: Third pass yield
        lpy: Last pass yield
        
    Example:
        >>> yield_data = YieldData(part_number="WIDGET-001", station_name="Station1")
        >>> print(yield_data.part_number)  # Access with Python field name
    """

    # Preserve forward-compatible fields returned by the backend.
    # Some WATS servers include built-in trend/baseline fields in yield payloads.
    model_config = ConfigDict(**PyWATSModel.model_config, extra="allow")

    part_number: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("partNumber", "part_number"),
        serialization_alias="partNumber",
        description="Product part number"
    )
    revision: Optional[str] = Field(default=None, description="Product revision")
    product_name: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("productName", "product_name"),
        serialization_alias="productName",
        description="Product name"
    )
    product_group: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("productGroup", "product_group"),
        serialization_alias="productGroup",
        description="Product group"
    )
    station_name: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("stationName", "station_name"),
        serialization_alias="stationName",
        description="Test station name"
    )
    test_operation: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("testOperation", "test_operation"),
        serialization_alias="testOperation",
        description="Test operation"
    )
    period: Optional[str] = Field(default=None, description="Time period")
    unit_count: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("unitCount", "unit_count"),
        serialization_alias="unitCount",
        description="Total unit count"
    )
    fp_count: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("fpCount", "fp_count"),
        serialization_alias="fpCount",
        description="First pass count"
    )
    sp_count: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("spCount", "sp_count"),
        serialization_alias="spCount",
        description="Second pass count"
    )
    tp_count: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("tpCount", "tp_count"),
        serialization_alias="tpCount",
        description="Third pass count"
    )
    lp_count: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("lpCount", "lp_count"),
        serialization_alias="lpCount",
        description="Last pass count"
    )
    fpy: Optional[float] = Field(default=None, description="First pass yield")
    spy: Optional[float] = Field(default=None, description="Second pass yield")
    tpy: Optional[float] = Field(default=None, description="Third pass yield")
    lpy: Optional[float] = Field(default=None, description="Last pass yield")


class ProcessInfo(PyWATSModel):
    """
    Represents process/test operation information.

    Attributes:
        code: Process code (e.g., 100, 500)
        name: Process name (e.g., "End of line test", "Repair")
        description: Process description
        is_test_operation: True if this is a test operation (use this, not 'isTestOperation')
        is_repair_operation: True if this is a repair operation (use this, not 'isRepairOperation')
        is_wip_operation: True if this is a WIP operation (use this, not 'isWipOperation')
        process_index: Process order index (use this, not 'processIndex')
        state: Process state
        
    Example:
        >>> process = ProcessInfo(code=100, name="EOL Test", is_test_operation=True)
        >>> print(process.is_test_operation)  # Access with Python field name
    """

    code: Optional[int] = Field(default=None, description="Process code")
    name: Optional[str] = Field(default=None, description="Process name")
    description: Optional[str] = Field(default=None, description="Process description")
    is_test_operation: bool = Field(
        default=False,
        validation_alias=AliasChoices("isTestOperation", "is_test_operation"),
        serialization_alias="isTestOperation",
        description="True if this is a test operation"
    )
    is_repair_operation: bool = Field(
        default=False,
        validation_alias=AliasChoices("isRepairOperation", "is_repair_operation"),
        serialization_alias="isRepairOperation",
        description="True if this is a repair operation"
    )
    is_wip_operation: bool = Field(
        default=False,
        validation_alias=AliasChoices("isWipOperation", "is_wip_operation"),
        serialization_alias="isWipOperation",
        description="True if this is a WIP operation"
    )
    process_index: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("processIndex", "process_index"),
        serialization_alias="processIndex",
        description="Process order index"
    )
    state: Optional[int] = Field(default=None, description="Process state")
    
    # Backward compatibility aliases
    @property
    def process_code(self) -> Optional[int]:
        """Alias for code (backward compatibility)"""
        return self.code
    
    @property
    def process_name(self) -> Optional[str]:
        """Alias for name (backward compatibility)"""
        return self.name


class LevelInfo(PyWATSModel):
    """
    Represents production level information.

    Attributes:
        level_id: Level ID (use this, not 'levelId')
        level_name: Level name (use this, not 'levelName')
        
    Example:
        >>> level = LevelInfo(level_id=1, level_name="PCBA")
        >>> print(level.level_name)  # Access with Python field name
    """

    level_id: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("levelId", "level_id"),
        serialization_alias="levelId",
        description="Level ID"
    )
    level_name: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("levelName", "level_name"),
        serialization_alias="levelName",
        description="Level name"
    )


class ProductGroup(PyWATSModel):
    """
    Represents a product group.

    Attributes:
        product_group_id: Product group ID (use this, not 'productGroupId')
        product_group_name: Product group name (use this, not 'productGroupName')
        
    Example:
        >>> group = ProductGroup(product_group_id=1, product_group_name="Electronics")
        >>> print(group.product_group_name)  # Access with Python field name
    """

    product_group_id: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("productGroupId", "product_group_id"),
        serialization_alias="productGroupId",
        description="Product group ID"
    )
    product_group_name: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("productGroupName", "product_group_name"),
        serialization_alias="productGroupName",
        description="Product group name"
    )


class StepAnalysisRow(PyWATSModel):
    """Represents a single step (and optional measurement) KPI row.

    Returned from POST /api/App/TestStepAnalysis.
    The API is in preview and the schema may change.
    
    IMPORTANT: Use Python field names (snake_case), not camelCase aliases.
    
    Attributes:
        step_name: Name of the test step (use this, not 'stepName')
        step_path: Full path to the step (use this, not 'stepPath')
        step_type: Type of step (use this, not 'stepType')
        step_group: Step group (use this, not 'stepGroup')
        step_count: Total step executions (use this, not 'stepCount')
        ... and many more statistical fields
        
    Example:
        >>> row = StepAnalysisRow(step_name="Voltage Test", step_count=100)
        >>> print(row.step_name)  # Access with Python field name
    """

    step_name: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("stepName", "step_name"),
        serialization_alias="stepName"
    )
    step_path: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("stepPath", "step_path"),
        serialization_alias="stepPath"
    )
    step_type: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("stepType", "step_type"),
        serialization_alias="stepType"
    )
    step_group: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("stepGroup", "step_group"),
        serialization_alias="stepGroup"
    )

    step_count: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("stepCount", "step_count"),
        serialization_alias="stepCount"
    )
    step_passed_count: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("stepPassedCount", "step_passed_count"),
        serialization_alias="stepPassedCount"
    )
    step_done_count: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("stepDoneCount", "step_done_count"),
        serialization_alias="stepDoneCount"
    )
    step_skipped_count: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("stepSkippedCount", "step_skipped_count"),
        serialization_alias="stepSkippedCount"
    )
    step_failed_count: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("stepFailedCount", "step_failed_count"),
        serialization_alias="stepFailedCount"
    )
    step_error_count: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("stepErrorCount", "step_error_count"),
        serialization_alias="stepErrorCount"
    )
    step_terminated_count: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("stepTerminatedCount", "step_terminated_count"),
        serialization_alias="stepTerminatedCount"
    )
    step_other_count: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("stepOtherCount", "step_other_count"),
        serialization_alias="stepOtherCount"
    )

    step_failed_error_terminated_count: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("stepFailedErrorTerminatedCount", "step_failed_error_terminated_count"),
        serialization_alias="stepFailedErrorTerminatedCount"
    )
    step_caused_uut_failed_error_terminated: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("stepCausedUutFailedErrorTerminated", "step_caused_uut_failed_error_terminated"),
        serialization_alias="stepCausedUutFailedErrorTerminated"
    )
    step_caused_uut_failed: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("stepCausedUutFailed", "step_caused_uut_failed"),
        serialization_alias="stepCausedUutFailed"
    )
    step_caused_uut_error: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("stepCausedUutError", "step_caused_uut_error"),
        serialization_alias="stepCausedUutError"
    )
    step_caused_uut_terminated: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("stepCausedUutTerminated", "step_caused_uut_terminated"),
        serialization_alias="stepCausedUutTerminated"
    )

    limit1: Optional[float] = Field(default=None)
    limit1_wof: Optional[float] = Field(
        default=None,
        validation_alias=AliasChoices("limit1Wof", "limit1_wof"),
        serialization_alias="limit1Wof"
    )
    limit2: Optional[float] = Field(default=None)
    limit2_wof: Optional[float] = Field(
        default=None,
        validation_alias=AliasChoices("limit2Wof", "limit2_wof"),
        serialization_alias="limit2Wof"
    )
    comp_operator: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("compOperator", "comp_operator"),
        serialization_alias="compOperator"
    )

    step_time_avg: Optional[float] = Field(
        default=None,
        validation_alias=AliasChoices("stepTimeAvg", "step_time_avg"),
        serialization_alias="stepTimeAvg"
    )
    step_time_max: Optional[float] = Field(
        default=None,
        validation_alias=AliasChoices("stepTimeMax", "step_time_max"),
        serialization_alias="stepTimeMax"
    )
    step_time_min: Optional[float] = Field(
        default=None,
        validation_alias=AliasChoices("stepTimeMin", "step_time_min"),
        serialization_alias="stepTimeMin"
    )

    measure_name: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("measureName", "measure_name"),
        serialization_alias="measureName"
    )
    measure_count: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("measureCount", "measure_count"),
        serialization_alias="measureCount"
    )
    measure_count_wof: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices("measureCountWof", "measure_count_wof"),
        serialization_alias="measureCountWof"
    )

    min: Optional[float] = Field(default=None)
    min_wof: Optional[float] = Field(
        default=None,
        validation_alias=AliasChoices("minWof", "min_wof"),
        serialization_alias="minWof"
    )
    max: Optional[float] = Field(default=None)
    max_wof: Optional[float] = Field(
        default=None,
        validation_alias=AliasChoices("maxWof", "max_wof"),
        serialization_alias="maxWof"
    )
    avg: Optional[float] = Field(default=None)
    avg_wof: Optional[float] = Field(
        default=None,
        validation_alias=AliasChoices("avgWof", "avg_wof"),
        serialization_alias="avgWof"
    )
    stdev: Optional[float] = Field(default=None)
    stdev_wof: Optional[float] = Field(
        default=None,
        validation_alias=AliasChoices("stdevWof", "stdev_wof"),
        serialization_alias="stdevWof"
    )
    var: Optional[float] = Field(default=None)
    var_wof: Optional[float] = Field(
        default=None,
        validation_alias=AliasChoices("varWof", "var_wof"),
        serialization_alias="varWof"
    )

    cpk: Optional[float] = Field(default=None)
    cpk_wof: Optional[float] = Field(
        default=None,
        validation_alias=AliasChoices("cpkWof", "cpk_wof"),
        serialization_alias="cpkWof"
    )
    cp: Optional[float] = Field(default=None)
    cp_wof: Optional[float] = Field(
        default=None,
        validation_alias=AliasChoices("cpWof", "cp_wof"),
        serialization_alias="cpWof"
    )
    cp_lower: Optional[float] = Field(
        default=None,
        validation_alias=AliasChoices("cpLower", "cp_lower"),
        serialization_alias="cpLower"
    )
    cp_lower_wof: Optional[float] = Field(
        default=None,
        validation_alias=AliasChoices("cpLowerWof", "cp_lower_wof"),
        serialization_alias="cpLowerWof"
    )
    cp_upper: Optional[float] = Field(
        default=None,
        validation_alias=AliasChoices("cpUpper", "cp_upper"),
        serialization_alias="cpUpper"
    )
    cp_upper_wof: Optional[float] = Field(
        default=None,
        validation_alias=AliasChoices("cpUpperWof", "cp_upper_wof"),
        serialization_alias="cpUpperWof"
    )

    sigma_high_3: Optional[float] = Field(
        default=None,
        validation_alias=AliasChoices("sigmaHigh3", "sigma_high_3"),
        serialization_alias="sigmaHigh3"
    )
    sigma_high_3_wof: Optional[float] = Field(
        default=None,
        validation_alias=AliasChoices("sigmaHigh3Wof", "sigma_high_3_wof"),
        serialization_alias="sigmaHigh3Wof"
    )
    sigma_low_3: Optional[float] = Field(
        default=None,
        validation_alias=AliasChoices("sigmaLow3", "sigma_low_3"),
        serialization_alias="sigmaLow3"
    )
    sigma_low_3_wof: Optional[float] = Field(
        default=None,
        validation_alias=AliasChoices("sigmaLow3Wof", "sigma_low_3_wof"),
        serialization_alias="sigmaLow3Wof"
    )
