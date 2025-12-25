"""
Test UUT Report Generator

Creates a comprehensive test UUT report demonstrating all pyWATS features.
This is useful for:
- Testing connectivity to WATS server
- Verifying report submission works
- Providing an example of pyWATS capabilities
- Debugging report serialization
"""

from datetime import datetime
from typing import Optional
import random
import math

from ..domains.report.report_models.uut.uut_report import UUTReport
from ..domains.report.report_models.uut.uut_info import UUTInfo
from ..domains.report.report_models.uut.steps.sequence_call import SequenceCall, SequenceCallInfo
from ..domains.report.report_models.uut.steps.comp_operator import CompOp
from ..domains.report.report_models.uut.steps.generic_step import FlowType
from ..domains.report.report_models.chart import Chart, ChartSeries, ChartType
from ..domains.report.report_models.misc_info import MiscInfo
from ..domains.report.report_models.sub_unit import SubUnit


def create_test_uut_report(
    part_number: str = "PYWATS-TEST-001",
    serial_number: Optional[str] = None,
    station_name: str = "pyWATS-TestStation",
    location: str = "TestLocation",
    operator_name: str = "pyWATS-Client",
) -> UUTReport:
    """
    Create a comprehensive test UUT report demonstrating all pyWATS features.
    
    This function creates a fully populated UUT report with:
    - Multiple sequence calls with nested structure
    - Various numeric tests (all comparison operators)
    - Pass/fail tests
    - String value tests
    - Chart/graph data
    - Misc info entries
    - Sub-units
    
    Args:
        part_number: Part number for the test report (default: "PYWATS-TEST-001")
        serial_number: Serial number (auto-generated if None)
        station_name: Name of the test station
        location: Location/site name
        operator_name: Operator name
        
    Returns:
        UUTReport: A fully populated test report ready to submit
        
    Example:
        >>> from pywats.tools import create_test_uut_report
        >>> report = create_test_uut_report()
        >>> # Submit using pywats client
        >>> client.submit_report(report)
    """
    # Generate serial number if not provided
    if serial_number is None:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        serial_number = f"PYWATS-{timestamp}-{random.randint(1000, 9999)}"
    
    # Create report with process code 10 = "SW Debug"
    report = UUTReport(
        pn=part_number,
        sn=serial_number,
        rev="1.0",
        process_code=10,  # SW Debug
        station_name=station_name,
        location=location,
        purpose="Debug",
        result="P",  # Will be set based on test results
        start=datetime.now().astimezone(),
    )
    
    # Set UUT Info - using the correct field names
    report.info = UUTInfo(
        operator=operator_name,
        fixture_id="pyWATS-Fixture-001",
        comment="pyWATS Test Report - Generated for connection testing",
    )
    # Set exec_time via alias
    report.info.exec_time = 2.5
    
    # Get root sequence call
    root = report.get_root_sequence_call()
    root.sequence.file_name = "pyWATS_TestSequence.py"
    root.sequence.path = "pyWATS/tests"
    root.sequence.version = "1.0.0"
    
    # =========================================================================
    # Sequence 1: Numeric Limit Tests
    # =========================================================================
    numeric_seq = root.add_sequence_call(
        name="Numeric Limit Tests",
        file_name="numeric_tests.py",
        version="1.0.0",
        path="pyWATS/tests/numeric"
    )
    
    # Add various numeric tests demonstrating all comparison operators
    
    # LOG - Log value only (no comparison)
    numeric_seq.add_numeric_step(
        name="Voltage Reading (LOG)",
        value=12.45,
        unit="V",
        comp_op=CompOp.LOG,
        status="P"
    )
    
    # EQ - Equal to
    numeric_seq.add_numeric_step(
        name="Reference Voltage (EQ)",
        value=5.0,
        unit="V",
        comp_op=CompOp.EQ,
        low_limit=5.0,
        status="P"
    )
    
    # GE - Greater than or Equal
    numeric_seq.add_numeric_step(
        name="Minimum Current (GE)",
        value=1.25,
        unit="A",
        comp_op=CompOp.GE,
        low_limit=1.0,
        status="P"
    )
    
    # LE - Less than or Equal
    numeric_seq.add_numeric_step(
        name="Max Temperature (LE)",
        value=65.3,
        unit="C",
        comp_op=CompOp.LE,
        low_limit=85.0,
        status="P"
    )
    
    # GT - Greater Than (strict)
    numeric_seq.add_numeric_step(
        name="Signal Strength (GT)",
        value=-45.2,
        unit="dBm",
        comp_op=CompOp.GT,
        low_limit=-50.0,
        status="P"
    )
    
    # LT - Less Than (strict)
    numeric_seq.add_numeric_step(
        name="Noise Level (LT)",
        value=0.002,
        unit="V",
        comp_op=CompOp.LT,
        low_limit=0.01,
        status="P"
    )
    
    # GELE - Between (inclusive)
    numeric_seq.add_numeric_step(
        name="Supply Voltage (GELE)",
        value=3.3,
        unit="V",
        comp_op=CompOp.GELE,
        low_limit=3.0,
        high_limit=3.6,
        status="P"
    )
    
    # GELT - Low inclusive, high exclusive
    numeric_seq.add_numeric_step(
        name="Clock Frequency (GELT)",
        value=25.0,
        unit="MHz",
        comp_op=CompOp.GELT,
        low_limit=24.0,
        high_limit=26.0,
        status="P"
    )
    
    # GTLT - Strictly between
    numeric_seq.add_numeric_step(
        name="Phase Margin (GTLT)",
        value=55.0,
        unit="deg",
        comp_op=CompOp.GTLT,
        low_limit=45.0,
        high_limit=65.0,
        status="P"
    )
    
    # GTLE - Low exclusive, high inclusive
    numeric_seq.add_numeric_step(
        name="Gain (GTLE)",
        value=10.0,
        unit="dB",
        comp_op=CompOp.GTLE,
        low_limit=0.0,
        high_limit=20.0,
        status="P"
    )
    
    # Multi-numeric step
    multi_num = numeric_seq.add_multi_numeric_step(
        name="Power Supply Measurements",
        status="P"
    )
    multi_num.add_measurement(
        name="3V3 Rail",
        value=3.31,
        unit="V",
        comp_op=CompOp.GELE,
        low_limit=3.1,
        high_limit=3.5,
        status="P"
    )
    multi_num.add_measurement(
        name="5V Rail",
        value=5.02,
        unit="V",
        comp_op=CompOp.GELE,
        low_limit=4.8,
        high_limit=5.2,
        status="P"
    )
    multi_num.add_measurement(
        name="12V Rail",
        value=12.1,
        unit="V",
        comp_op=CompOp.GELE,
        low_limit=11.5,
        high_limit=12.5,
        status="P"
    )
    
    # =========================================================================
    # Sequence 2: Pass/Fail Tests
    # =========================================================================
    pf_seq = root.add_sequence_call(
        name="Pass/Fail Tests",
        file_name="boolean_tests.py",
        version="1.0.0",
        path="pyWATS/tests/boolean"
    )
    
    # Simple pass/fail tests
    pf_seq.add_boolean_step(name="Self-Test", status="P")
    pf_seq.add_boolean_step(name="Communication Check", status="P")
    pf_seq.add_boolean_step(name="Hardware Present", status="P")
    pf_seq.add_boolean_step(name="Firmware Valid", status="P")
    
    # Multi-boolean step
    multi_bool = pf_seq.add_multi_boolean_step(
        name="System Health Checks",
        status="P"
    )
    multi_bool.add_measurement(name="CPU OK", status="P")
    multi_bool.add_measurement(name="Memory OK", status="P")
    multi_bool.add_measurement(name="Storage OK", status="P")
    multi_bool.add_measurement(name="Network OK", status="P")
    
    # =========================================================================
    # Sequence 3: String Tests
    # =========================================================================
    string_seq = root.add_sequence_call(
        name="String Value Tests",
        file_name="string_tests.py",
        version="1.0.0",
        path="pyWATS/tests/string"
    )
    
    # LOG - Just log value
    string_seq.add_string_step(
        name="Firmware Version",
        value="v2.5.1-build-1234",
        comp_op=CompOp.LOG,
        status="P"
    )
    
    # CASESENSIT - Case sensitive comparison
    string_seq.add_string_step(
        name="Product ID (Case Sensitive)",
        value="PROD-ABC-123",
        comp_op=CompOp.CASESENSIT,
        limit="PROD-ABC-123",
        status="P"
    )
    
    # IGNORECASE - Case insensitive comparison
    string_seq.add_string_step(
        name="Status Response",
        value="OK",
        comp_op=CompOp.IGNORECASE,
        limit="ok",
        status="P"
    )
    
    # Multi-string step
    multi_str = string_seq.add_multi_string_step(
        name="Device Information",
        status="P"
    )
    multi_str.add_measurement(
        name="Manufacturer",
        value="pyWATS Test Corp",
        comp_op=CompOp.LOG,
        status="P"
    )
    multi_str.add_measurement(
        name="Model",
        value="TEST-MODEL-X",
        comp_op=CompOp.CASESENSIT,
        limit="TEST-MODEL-X",
        status="P"
    )
    multi_str.add_measurement(
        name="Calibration Date",
        value=datetime.now().strftime("%Y-%m-%d"),
        comp_op=CompOp.LOG,
        status="P"
    )
    
    # =========================================================================
    # Sequence 4: Chart/Graph Data
    # =========================================================================
    chart_seq = root.add_sequence_call(
        name="Graph Tests",
        file_name="chart_tests.py",
        version="1.0.0",
        path="pyWATS/tests/charts"
    )
    
    # Create a sine wave chart
    x_values = [i * 0.1 for i in range(100)]
    y_values = [math.sin(x * 2 * math.pi / 10) * 5 for x in x_values]
    
    sine_series = ChartSeries(
        name="Sine Wave",
        x_data=";".join(str(x) for x in x_values),
        y_data=";".join(f"{y:.3f}" for y in y_values)
    )
    
    # Add reference lines
    upper_limit_series = ChartSeries(
        name="Upper Limit",
        x_data="0;10",
        y_data="4;4"
    )
    lower_limit_series = ChartSeries(
        name="Lower Limit",
        x_data="0;10",
        y_data="-4;-4"
    )
    
    chart_seq.add_chart_step(
        name="Signal Response",
        chart_type=ChartType.LINE,
        label="Signal Output",
        x_label="Time",
        x_unit="s",
        y_label="Amplitude",
        y_unit="V",
        series=[sine_series, upper_limit_series, lower_limit_series],
        status="P"
    )
    
    # Power consumption over time
    time_points = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    power_values = [2.1, 2.3, 4.5, 4.2, 4.3, 4.1, 4.4, 4.2, 2.2, 2.1, 2.0]
    
    power_series = ChartSeries(
        name="Power Consumption",
        x_data=";".join(str(t) for t in time_points),
        y_data=";".join(str(p) for p in power_values)
    )
    
    chart_seq.add_chart_step(
        name="Power Profile",
        chart_type=ChartType.LINE,
        label="Power Consumption During Test",
        x_label="Time",
        x_unit="min",
        y_label="Power",
        y_unit="W",
        series=[power_series],
        status="P"
    )
    
    # =========================================================================
    # Sequence 5: Generic/Action Steps
    # =========================================================================
    action_seq = root.add_sequence_call(
        name="Actions and Setup",
        file_name="action_steps.py",
        version="1.0.0",
        path="pyWATS/tests/actions"
    )
    
    action_seq.add_generic_step(
        step_type=FlowType.Action,
        name="Initialize Hardware",
        status="P",
        tot_time=0.5
    )
    
    action_seq.add_generic_step(
        step_type=FlowType.Action,
        name="Load Firmware",
        status="P",
        tot_time=1.2
    )
    
    action_seq.add_generic_step(
        step_type=FlowType.Action,
        name="Configure DUT",
        status="P",
        tot_time=0.3
    )
    
    action_seq.add_generic_step(
        step_type=FlowType.Action,
        name="Cleanup",
        status="P",
        tot_time=0.2
    )
    
    # =========================================================================
    # Add Misc Info
    # =========================================================================
    report.add_misc_info("pyWATS Version", "1.0.0")
    report.add_misc_info("Test Type", "Connection Verification")
    report.add_misc_info("Timestamp", datetime.now().isoformat())
    report.add_misc_info("Random Seed", str(random.randint(1, 100000)))
    
    # =========================================================================
    # Add Sub-Units
    # =========================================================================
    report.add_sub_unit(
        part_type="PCBA",
        sn=f"PCBA-{datetime.now().strftime('%Y%m%d')}-001",
        pn="PCBA-MAIN-001",
        rev="A"
    )
    report.add_sub_unit(
        part_type="MODULE",
        sn=f"MOD-{datetime.now().strftime('%Y%m%d')}-001",
        pn="MOD-POWER-001",
        rev="B"
    )
    
    # Set overall result to Passed
    report.result = "P"
    
    return report


def create_minimal_test_report(
    part_number: str = "PYWATS-MIN-001",
    serial_number: Optional[str] = None,
    station_name: str = "pyWATS-TestStation",
    location: str = "TestLocation",
) -> UUTReport:
    """
    Create a minimal test report with just basic information.
    
    Useful for quick connection tests with minimal data.
    
    Args:
        part_number: Part number for the test report
        serial_number: Serial number (auto-generated if None)
        station_name: Name of the test station
        location: Location/site name
        
    Returns:
        UUTReport: A minimal test report ready to submit
    """
    if serial_number is None:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        serial_number = f"PYWATS-{timestamp}"
    
    report = UUTReport(
        pn=part_number,
        sn=serial_number,
        rev="1.0",
        process_code=10,  # SW Debug
        station_name=station_name,
        location=location,
        purpose="Debug",
        result="P",
        start=datetime.now().astimezone(),
    )
    
    # Add one simple pass step
    root = report.get_root_sequence_call()
    root.add_boolean_step(name="Connection Test", status="P")
    
    report.add_misc_info("Test Type", "Minimal Connection Test")
    
    return report
