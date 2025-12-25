"""
WATS Standard Text Format Converter

Converts WATS Standard Text Format files into WATS reports.
Port of the C# WATSStandardTextFormat converter.

Expected file format:
- Tab-delimited text file
- Starts with --Header-Start--
- Header section with key-value pairs (SerialNumber, PartNumber, etc.)
- --Step-Data-Start-- marks beginning of test data
- Step types: SequenceCall, NumericLimitTest, PassFailTest, StringValueTest, ActionStep
- --Step-Data-End-- marks end of test data
- --UUT-End-- marks end of report

Format:
--Header-Start--
SerialNumber    12345
PartNumber      PN-001
...
--Step-Data-Start--
StepType    StepName    MeasureName    Value    LowLimit    HighLimit    CompOperator    Unit    Status    ...
NumericLimitTest    Test1        10.5    9    11    GELE    V    Passed    ...
...
--Step-Data-End--
--UUT-End--
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

from pywats_client.converters.file_converter import FileConverter
from pywats_client.converters.context import ConverterContext
from pywats_client.converters.models import (
    ConverterSource,
    ConverterResult,
    ValidationResult,
    PostProcessAction,
    ArgumentDefinition,
    ArgumentType,
)


class ReportReadState(Enum):
    """Parser state"""
    UNKNOWN = "unknown"
    IN_HEADER = "in_header"
    IN_TEST = "in_test"
    IN_FOOTER = "in_footer"
    END_OF_FILE = "end_of_file"


# Comparison operator mapping
COMP_OPERATORS = {
    "LOG": "LOG", "EQ": "EQ", "NE": "NE", 
    "GE": "GE", "GT": "GT", "LE": "LE", "LT": "LT",
    "GELE": "GELE", "GELT": "GELT", "GTLE": "GTLE", "GTLT": "GTLT",
    "LEGE": "LEGE", "LEGT": "LEGT", "LTGE": "LTGE", "LTGT": "LTGT",
}


class WATSStandardTextConverter(FileConverter):
    """
    Converts WATS Standard Text Format files to WATS reports.
    
    File qualification:
    - Tab-delimited text file
    - Contains --Header-Start-- marker
    - Contains --Step-Data-Start-- and --Step-Data-End-- markers
    """
    
    @property
    def name(self) -> str:
        return "WATS Standard Text Format Converter"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Converts WATS Standard Text Format files into WATS reports"
    
    @property
    def file_patterns(self) -> List[str]:
        return ["*.txt"]
    
    @property
    def arguments_schema(self) -> Dict[str, ArgumentDefinition]:
        return {
            "defaultOperationTypeCode": ArgumentDefinition(
                arg_type=ArgumentType.STRING,
                default="10",
                description="Default operation type code if not specified in file",
            ),
        }
    
    def validate(self, source: ConverterSource, context: ConverterContext) -> ValidationResult:
        """
        Validate that the file is a WATS Standard Text Format file.
        
        Confidence levels:
        - 0.98: Contains --Header-Start-- and --Step-Data-Start--
        - 0.85: Contains --Header-Start-- only
        - 0.0: No recognizable markers
        """
        if not source.path or not source.path.exists():
            return ValidationResult.no_match("File not found")
        
        suffix = source.path.suffix.lower()
        if suffix != '.txt':
            return ValidationResult.no_match("Not a text file")
        
        try:
            with open(source.path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(10000)  # Read first 10KB
            
            has_header_start = '--Header-Start--' in content
            has_step_start = '--Step-Data-Start--' in content
            has_uut_end = '--UUT-End--' in content
            
            if has_header_start and has_step_start:
                # Try to extract some info
                serial_number = ""
                part_number = ""
                
                for line in content.split('\n'):
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        if parts[0].strip() == 'SerialNumber':
                            serial_number = parts[1].strip()
                        elif parts[0].strip() == 'PartNumber':
                            part_number = parts[1].strip()
                
                return ValidationResult(
                    can_convert=True,
                    confidence=0.98,
                    message="WATS Standard Text Format file",
                    detected_serial_number=serial_number,
                    detected_part_number=part_number,
                )
            
            if has_header_start:
                return ValidationResult(
                    can_convert=True,
                    confidence=0.85,
                    message="WATS Standard Text Format (partial)",
                )
            
            return ValidationResult.no_match("No WATS Standard Text Format markers found")
            
        except Exception as e:
            return ValidationResult.no_match(f"Error reading file: {e}")
    
    def convert(self, source: ConverterSource, context: ConverterContext) -> ConverterResult:
        """Convert WATS Standard Text Format file to WATS report"""
        if not source.path:
            return ConverterResult.failed_result(error="No file path provided")
        
        try:
            with open(source.path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            return self._parse_lines(lines, source, context)
            
        except Exception as e:
            return ConverterResult.failed_result(error=f"Conversion error: {e}")
    
    def _parse_lines(
        self,
        lines: List[str],
        source: ConverterSource,
        context: ConverterContext
    ) -> ConverterResult:
        """Parse all lines and build WATS report"""
        
        default_op_code = context.get_argument("defaultOperationTypeCode", "10")
        
        state = ReportReadState.UNKNOWN
        report: Dict[str, Any] = {
            "type": "Test",
            "processCode": default_op_code,
            "partNumber": "",
            "partRevision": "1",
            "serialNumber": "",
            "result": "P",
        }
        
        misc_infos: List[Dict[str, str]] = []
        subunits: List[Dict[str, str]] = []
        
        # Root sequence
        root_step: Dict[str, Any] = {
            "type": "SEQ",
            "name": "Root",
            "status": "Done",
            "stepResults": []
        }
        
        # Stack for nested sequences
        sequence_stack: List[Dict[str, Any]] = [root_step]
        current_step: Optional[Dict[str, Any]] = None
        
        for line_num, line in enumerate(lines, 1):
            line = line.rstrip('\n\r')
            
            if not line:
                continue
            
            # Check for markers
            if '--Header-Start--' in line:
                state = ReportReadState.IN_HEADER
                continue
            elif '--Step-Data-Start--' in line:
                state = ReportReadState.IN_TEST
                continue
            elif '--Step-Data-End--' in line:
                state = ReportReadState.IN_FOOTER
                continue
            elif '--UUT-End--' in line or '-- UUT-End--' in line:
                state = ReportReadState.END_OF_FILE
                continue
            
            parts = line.split('\t')
            
            if state == ReportReadState.IN_HEADER:
                self._process_header_line(parts, report, misc_infos, subunits)
            
            elif state == ReportReadState.IN_TEST:
                # Skip header row
                if parts[0] == 'StepType':
                    continue
                
                current_step = self._process_test_line(
                    parts, sequence_stack, current_step
                )
            
            elif state == ReportReadState.IN_FOOTER:
                self._process_footer_line(parts, report)
        
        # Add collected data to report
        if misc_infos:
            report["miscInfos"] = misc_infos
        
        if subunits:
            report["uutParts"] = subunits
        
        report["root"] = root_step
        
        return ConverterResult.success_result(
            report=report,
            post_action=PostProcessAction.MOVE,
        )
    
    def _process_header_line(
        self,
        parts: List[str],
        report: Dict[str, Any],
        misc_infos: List[Dict[str, str]],
        subunits: List[Dict[str, str]]
    ) -> None:
        """Process a header line"""
        if len(parts) < 2:
            return
        
        key = parts[0].strip()
        value = parts[1].strip() if len(parts) > 1 else ""
        
        # Map header fields to report fields
        header_mapping = {
            'SerialNumber': 'serialNumber',
            'PartNumber': 'partNumber',
            'Revision': 'partRevision',
            'OperationTypeName': 'processName',
            'OperationTypeCode': 'processCode',
            'StationName': 'machineName',
            'OperatorName': 'operator',
            'SoftwareName': 'sequenceName',
            'SoftwareVersion': 'sequenceVersion',
            'BatchSerialNumber': 'batchSerialNumber',
            'Comment': 'comment',
            'FixtureId': 'fixtureId',
        }
        
        if key in header_mapping:
            report[header_mapping[key]] = value
        elif key == 'UUTStatus':
            report['result'] = self._map_uut_status(value)
        elif key == 'ErrorCode':
            try:
                report['errorCode'] = int(value)
            except ValueError:
                pass
        elif key == 'ErrorMessage':
            report['errorMessage'] = value
        elif key == 'UTCStartDateTime' or key == 'StartDateTime':
            try:
                dt = datetime.fromisoformat(value)
                report['start'] = dt.isoformat()
            except ValueError:
                pass
        elif key == 'ExecutionTime':
            try:
                report['execTime'] = float(value)
            except ValueError:
                pass
        elif key == 'TestSocketIndex':
            try:
                report['socketIdx'] = int(value)
            except ValueError:
                pass
        elif key == 'Subunit':
            # Subunit format: Description, PartNumber, SerialNumber, Revision
            if len(parts) >= 4:
                subunits.append({
                    "description": parts[1].strip() if len(parts) > 1 else "",
                    "partNumber": parts[2].strip() if len(parts) > 2 else "",
                    "serialNumber": parts[3].strip() if len(parts) > 3 else "",
                    "revision": parts[4].strip() if len(parts) > 4 else "",
                })
        else:
            # Add as misc info
            if value:
                misc_infos.append({"name": key, "value": value})
    
    def _process_test_line(
        self,
        parts: List[str],
        sequence_stack: List[Dict[str, Any]],
        current_step: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Process a test step line"""
        if len(parts) < 1:
            return current_step
        
        step_type = parts[0].strip()
        
        # Get current sequence
        current_seq = sequence_stack[-1] if sequence_stack else None
        if not current_seq:
            return current_step
        
        # Parse common fields
        step_name = parts[1].strip() if len(parts) > 1 else ""
        measure_name = parts[2].strip() if len(parts) > 2 else ""
        value_str = parts[3].strip() if len(parts) > 3 else ""
        low_limit_str = parts[4].strip() if len(parts) > 4 else ""
        high_limit_str = parts[5].strip() if len(parts) > 5 else ""
        comp_op = parts[6].strip() if len(parts) > 6 else ""
        unit = parts[7].strip() if len(parts) > 7 else ""
        status_str = parts[8].strip() if len(parts) > 8 else ""
        exec_time_str = parts[9].strip() if len(parts) > 9 else ""
        report_text = parts[10].strip() if len(parts) > 10 else ""
        error_code_str = parts[11].strip() if len(parts) > 11 else ""
        error_msg = parts[12].strip() if len(parts) > 12 else ""
        
        if step_type == 'SequenceCall':
            new_seq: Dict[str, Any] = {
                "type": "SEQ",
                "name": step_name or "Sequence",
                "status": self._map_step_status(status_str),
                "stepResults": []
            }
            
            self._add_general_step_info(new_seq, exec_time_str, report_text, error_code_str, error_msg)
            
            current_seq["stepResults"].append(new_seq)
            sequence_stack.append(new_seq)
            return new_seq
        
        elif step_type == 'EndSequenceCall':
            if len(sequence_stack) > 1:
                # Update status if provided
                if status_str:
                    sequence_stack[-1]["status"] = self._map_step_status(status_str)
                self._add_general_step_info(sequence_stack[-1], exec_time_str, report_text, error_code_str, error_msg)
                sequence_stack.pop()
            return None
        
        elif step_type in ('NumericLimitTest', 'MultipleNumericLimitTest'):
            # Check if we should add to existing step or create new
            if current_step and current_step.get("type") == "NT" and not step_name:
                # Add measurement to existing step
                pass  # Multiple measurements not fully implemented
            else:
                step = self._create_numeric_step(
                    step_name, measure_name, value_str, low_limit_str, high_limit_str,
                    comp_op, unit, status_str, exec_time_str, report_text, error_code_str, error_msg
                )
                if step:
                    current_seq["stepResults"].append(step)
                    return step
        
        elif step_type == 'PassFailTest':
            step = self._create_passfail_step(
                step_name, measure_name, value_str, status_str,
                exec_time_str, report_text, error_code_str, error_msg
            )
            if step:
                current_seq["stepResults"].append(step)
                return step
        
        elif step_type == 'StringValueTest':
            step = self._create_string_step(
                step_name, measure_name, value_str, low_limit_str, comp_op,
                status_str, exec_time_str, report_text, error_code_str, error_msg
            )
            if step:
                current_seq["stepResults"].append(step)
                return step
        
        elif step_type == 'ActionStep':
            step: Dict[str, Any] = {
                "type": "GEN",
                "stepType": "Action",
                "name": step_name or "Action",
                "stepStatus": self._map_step_status(status_str),
            }
            self._add_general_step_info(step, exec_time_str, report_text, error_code_str, error_msg)
            current_seq["stepResults"].append(step)
            return step
        
        elif step_type == 'Chart':
            # Chart handling - attach to current step if available
            pass  # Simplified: charts not fully implemented
        
        elif step_type == 'Series':
            # Series handling
            pass  # Simplified: series not fully implemented
        
        return current_step
    
    def _create_numeric_step(
        self,
        step_name: str,
        measure_name: str,
        value_str: str,
        low_limit_str: str,
        high_limit_str: str,
        comp_op: str,
        unit: str,
        status_str: str,
        exec_time_str: str,
        report_text: str,
        error_code_str: str,
        error_msg: str
    ) -> Optional[Dict[str, Any]]:
        """Create a numeric limit step"""
        try:
            value = float(value_str) if value_str else 0.0
        except ValueError:
            return None
        
        step: Dict[str, Any] = {
            "type": "NT",
            "name": step_name or measure_name or "NumericTest",
            "numericValue": value,
            "stepStatus": self._map_step_status(status_str),
        }
        
        # Add limits based on comparison operator
        comp_op_upper = comp_op.upper() if comp_op else ""
        
        if comp_op_upper in COMP_OPERATORS:
            step["compOp"] = COMP_OPERATORS[comp_op_upper]
        
        try:
            if low_limit_str:
                step["lowLimit"] = float(low_limit_str)
        except ValueError:
            pass
        
        try:
            if high_limit_str:
                step["highLimit"] = float(high_limit_str)
        except ValueError:
            pass
        
        if unit:
            step["unit"] = unit
        
        if measure_name:
            step["index"] = measure_name
        
        self._add_general_step_info(step, exec_time_str, report_text, error_code_str, error_msg)
        
        return step
    
    def _create_passfail_step(
        self,
        step_name: str,
        measure_name: str,
        value_str: str,
        status_str: str,
        exec_time_str: str,
        report_text: str,
        error_code_str: str,
        error_msg: str
    ) -> Optional[Dict[str, Any]]:
        """Create a pass/fail step"""
        value_upper = value_str.upper() if value_str else ""
        passed = value_upper in ('TRUE', '1', 'PASS', 'PASSED')
        
        step: Dict[str, Any] = {
            "type": "PF",
            "name": step_name or measure_name or "PassFailTest",
            "passFailStatus": passed,
            "stepStatus": self._map_step_status(status_str),
        }
        
        if measure_name:
            step["index"] = measure_name
        
        self._add_general_step_info(step, exec_time_str, report_text, error_code_str, error_msg)
        
        return step
    
    def _create_string_step(
        self,
        step_name: str,
        measure_name: str,
        value_str: str,
        string_limit: str,
        comp_op: str,
        status_str: str,
        exec_time_str: str,
        report_text: str,
        error_code_str: str,
        error_msg: str
    ) -> Optional[Dict[str, Any]]:
        """Create a string value step"""
        step: Dict[str, Any] = {
            "type": "ST",
            "name": step_name or measure_name or "StringTest",
            "stringValue": value_str,
            "stepStatus": self._map_step_status(status_str),
        }
        
        if string_limit:
            step["stringLimit"] = string_limit
        
        comp_op_upper = comp_op.upper() if comp_op else ""
        if comp_op_upper in COMP_OPERATORS:
            step["compOp"] = COMP_OPERATORS[comp_op_upper]
        
        if measure_name:
            step["index"] = measure_name
        
        self._add_general_step_info(step, exec_time_str, report_text, error_code_str, error_msg)
        
        return step
    
    def _add_general_step_info(
        self,
        step: Dict[str, Any],
        exec_time_str: str,
        report_text: str,
        error_code_str: str,
        error_msg: str
    ) -> None:
        """Add general step information"""
        try:
            if exec_time_str:
                step["totTime"] = float(exec_time_str)
        except ValueError:
            pass
        
        if report_text:
            step["reportText"] = report_text
        
        try:
            if error_code_str:
                step["errorCode"] = int(error_code_str)
        except ValueError:
            pass
        
        if error_msg:
            step["errorMessage"] = error_msg
    
    def _process_footer_line(
        self,
        parts: List[str],
        report: Dict[str, Any]
    ) -> None:
        """Process a footer line"""
        if len(parts) < 2:
            return
        
        key = parts[0].strip()
        value = parts[1].strip()
        
        if key == 'UUTStatus':
            report['result'] = self._map_uut_status(value)
        elif key == 'ErrorCode':
            try:
                report['errorCode'] = int(value)
            except ValueError:
                pass
        elif key == 'ErrorMessage':
            report['errorMessage'] = value
        elif key == 'ExecutionTime':
            try:
                report['execTime'] = float(value)
            except ValueError:
                pass
    
    def _map_uut_status(self, status: str) -> str:
        """Map UUT status string to WATS result code"""
        status_upper = status.upper() if status else ""
        if status_upper in ('PASSED', 'PASS', 'P'):
            return "P"
        elif status_upper in ('FAILED', 'FAIL', 'F'):
            return "F"
        elif status_upper in ('ERROR', 'E'):
            return "E"
        elif status_upper in ('TERMINATED', 'T'):
            return "T"
        else:
            return "P"
    
    def _map_step_status(self, status: str) -> str:
        """Map step status string to WATS status"""
        status_upper = status.upper() if status else ""
        if status_upper in ('PASSED', 'PASS'):
            return "Passed"
        elif status_upper in ('FAILED', 'FAIL'):
            return "Failed"
        elif status_upper in ('ERROR',):
            return "Error"
        elif status_upper in ('DONE',):
            return "Done"
        elif status_upper in ('SKIPPED',):
            return "Skipped"
        elif status_upper in ('TERMINATED',):
            return "Terminated"
        else:
            return "Done"


# Test code
if __name__ == "__main__":
    import json
    
    sample = """--Header-Start--
SerialNumber	SN12345
PartNumber	PN-001
Revision	A
OperationTypeName	Functional Test
UUTStatus	Passed
StationName	Station1
OperatorName	JohnDoe
SoftwareName	TestSeq
SoftwareVersion	1.0.0
ExecutionTime	10.5
--Step-Data-Start--
StepType	StepName	MeasureName	Value	LowLimit	HighLimit	CompOperator	Unit	StepStatus	StepExecutionTime
SequenceCall	MainTests							Passed	5
NumericLimitTest	VoltageTest		12.05	11.5	12.5	GELE	V	Passed	1
NumericLimitTest	CurrentTest		0.95	0.8	1.2	GELE	A	Passed	1
PassFailTest	SelfTest		TRUE					Passed	0.5
EndSequenceCall
--Step-Data-End--
UUTStatus	Passed
--UUT-End--
"""
    
    import tempfile
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(sample)
        temp_path = Path(f.name)
    
    try:
        converter = WATSStandardTextConverter()
        source = ConverterSource.from_file(temp_path)
        context = ConverterContext()
        
        # Validate
        validation = converter.validate(source, context)
        print(f"Validation: can_convert={validation.can_convert}, confidence={validation.confidence:.2f}")
        print(f"  Message: {validation.message}")
        print(f"  Detected: SN={validation.detected_serial_number}, PN={validation.detected_part_number}")
        
        # Convert
        result = converter.convert(source, context)
        print(f"\nConversion status: {result.status.value}")
        if result.report:
            print("\nGenerated report:")
            print(json.dumps(result.report, indent=2))
    finally:
        temp_path.unlink()
