"""
WATS Standard JSON Format Converter (WSJF)

Converts WATS Standard JSON Format (WSJF) files into WATS reports.
Port of the C# WATSStandardJsonFormat converter.

Expected file format:
- JSON file with WSJF schema
- Root object with type, pn, sn, rev, result, root (step tree)

The WSJF format is a JSON representation of WATS test reports that closely
mirrors the WATS data model. This converter essentially passes through
the data with minimal transformation since it's already in WATS-compatible format.

Step types:
- SequenceCall: Container for nested steps
- ET_NLT: Numeric Limit Test
- ET_MNLT: Multiple Numeric Limit Test
- ET_PFT: Pass/Fail Test
- ET_SVT: String Value Test
- ET_A: Action Step
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

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


# Step type mapping from WSJF to WATS internal format
STEP_TYPE_MAP = {
    "SequenceCall": "SEQ",
    "ET_NLT": "NT",
    "ET_MNLT": "NT",
    "ET_PFT": "PF",
    "ET_SVT": "ST",
    "ET_A": "GEN",
    "ET_GEN": "GEN",
}


class WATSStandardJsonConverter(FileConverter):
    """
    Converts WATS Standard JSON Format (WSJF) files to WATS reports.
    
    File qualification:
    - JSON file with .json extension
    - Contains required WSJF fields: type, pn/partNumber, sn/serialNumber, root
    """
    
    @property
    def name(self) -> str:
        return "WATS Standard JSON Format Converter"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Converts WATS Standard JSON Format (WSJF) files into WATS reports"
    
    @property
    def file_patterns(self) -> List[str]:
        return ["*.json"]
    
    @property
    def arguments_schema(self) -> Dict[str, ArgumentDefinition]:
        return {
            "defaultProcessCode": ArgumentDefinition(
                arg_type=ArgumentType.STRING,
                default="10",
                description="Default process code if not specified in file",
            ),
        }
    
    def validate(self, source: ConverterSource, context: ConverterContext) -> ValidationResult:
        """
        Validate that the file is a WSJF format file.
        
        Confidence levels:
        - 0.98: Valid JSON with all required WSJF fields
        - 0.85: Valid JSON with partial WSJF fields
        - 0.5: Valid JSON but not WSJF format
        - 0.0: Not valid JSON
        """
        if not source.path or not source.path.exists():
            return ValidationResult.no_match("File not found")
        
        suffix = source.path.suffix.lower()
        if suffix != '.json':
            return ValidationResult.no_match("Not a JSON file")
        
        try:
            with open(source.path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, dict):
                return ValidationResult.no_match("JSON is not an object")
            
            # Check for WSJF required fields
            has_type = 'type' in data
            has_pn = 'pn' in data or 'partNumber' in data
            has_sn = 'sn' in data or 'serialNumber' in data
            has_root = 'root' in data
            
            # Type should be 'T' (Test/UUT) or 'U' (UUR)
            report_type = data.get('type', '')
            is_valid_type = report_type in ('T', 'U', 'UUT', 'UUR', 'Test')
            
            if has_type and has_root and is_valid_type:
                part_number = data.get('pn', data.get('partNumber', ''))
                serial_number = data.get('sn', data.get('serialNumber', ''))
                result = data.get('result', 'P')
                
                return ValidationResult(
                    can_convert=True,
                    confidence=0.98,
                    message="WATS Standard JSON Format (WSJF) file",
                    detected_part_number=part_number,
                    detected_serial_number=serial_number,
                    detected_result="Passed" if result in ('P', 'Passed') else "Failed",
                )
            
            if has_pn or has_sn:
                return ValidationResult(
                    can_convert=True,
                    confidence=0.7,
                    message="Possible WSJF file (partial structure)",
                )
            
            return ValidationResult(
                can_convert=True,
                confidence=0.5,
                message="JSON file but not WSJF format",
            )
            
        except json.JSONDecodeError as e:
            return ValidationResult.no_match(f"Invalid JSON: {e}")
        except Exception as e:
            return ValidationResult.no_match(f"Error reading file: {e}")
    
    def convert(self, source: ConverterSource, context: ConverterContext) -> ConverterResult:
        """Convert WSJF file to WATS report"""
        if not source.path:
            return ConverterResult.failed_result(error="No file path provided")
        
        try:
            with open(source.path, 'r', encoding='utf-8') as f:
                wsjf_data = json.load(f)
            
            return self._convert_wsjf(wsjf_data, source, context)
            
        except json.JSONDecodeError as e:
            return ConverterResult.failed_result(error=f"Invalid JSON: {e}")
        except Exception as e:
            return ConverterResult.failed_result(error=f"Conversion error: {e}")
    
    def _convert_wsjf(
        self,
        wsjf_data: Dict[str, Any],
        source: ConverterSource,
        context: ConverterContext
    ) -> ConverterResult:
        """Convert WSJF data to WATS report format"""
        
        default_process_code = context.get_argument("defaultProcessCode", "10")
        
        # Build report from WSJF data
        report: Dict[str, Any] = {
            "type": "Test",
        }
        
        # Map WSJF fields to WATS report fields
        field_mapping = {
            'pn': 'partNumber',
            'sn': 'serialNumber',
            'rev': 'partRevision',
            'processCode': 'processCode',
            'processName': 'processName',
            'machineName': 'machineName',
            'location': 'location',
            'purpose': 'purpose',
            'operator': 'operator',
            'batchSn': 'batchSerialNumber',
            'comment': 'comment',
            'execTime': 'execTime',
            'socketIdx': 'socketIdx',
            'fixtureId': 'fixtureId',
            'seqName': 'sequenceName',
            'seqVersion': 'sequenceVersion',
            'errorCode': 'errorCode',
            'errorMessage': 'errorMessage',
        }
        
        for wsjf_field, wats_field in field_mapping.items():
            if wsjf_field in wsjf_data and wsjf_data[wsjf_field] is not None:
                report[wats_field] = wsjf_data[wsjf_field]
        
        # Handle alternate field names
        if 'partNumber' in wsjf_data:
            report['partNumber'] = wsjf_data['partNumber']
        if 'serialNumber' in wsjf_data:
            report['serialNumber'] = wsjf_data['serialNumber']
        if 'partRevision' in wsjf_data:
            report['partRevision'] = wsjf_data['partRevision']
        
        # Set default process code if not provided
        if 'processCode' not in report:
            report['processCode'] = default_process_code
        
        # Map result
        result = wsjf_data.get('result', 'P')
        if result in ('P', 'Passed', 'Pass'):
            report['result'] = 'P'
        elif result in ('F', 'Failed', 'Fail'):
            report['result'] = 'F'
        elif result in ('E', 'Error'):
            report['result'] = 'E'
        elif result in ('T', 'Terminated'):
            report['result'] = 'T'
        else:
            report['result'] = result
        
        # Handle start time
        if 'start' in wsjf_data:
            report['start'] = wsjf_data['start']
        elif 'startUTC' in wsjf_data:
            report['start'] = wsjf_data['startUTC']
        
        # Handle misc infos
        if 'miscInfos' in wsjf_data:
            report['miscInfos'] = wsjf_data['miscInfos']
        
        # Handle UUT parts (subunits)
        if 'uutParts' in wsjf_data:
            report['uutParts'] = wsjf_data['uutParts']
        elif 'subUnits' in wsjf_data:
            report['uutParts'] = wsjf_data['subUnits']
        
        # Convert step tree
        if 'root' in wsjf_data and wsjf_data['root']:
            report['root'] = self._convert_step(wsjf_data['root'])
        else:
            # Create empty root
            report['root'] = {
                "type": "SEQ",
                "name": "Root",
                "status": "Done",
                "stepResults": []
            }
        
        return ConverterResult.success_result(
            report=report,
            post_action=PostProcessAction.MOVE,
        )
    
    def _convert_step(self, wsjf_step: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a WSJF step to WATS step format"""
        
        step_type = wsjf_step.get('stepType', 'SequenceCall')
        wats_type = STEP_TYPE_MAP.get(step_type, 'GEN')
        
        step: Dict[str, Any] = {
            "type": wats_type,
            "name": wsjf_step.get('name', 'Step'),
        }
        
        # Map status
        status = wsjf_step.get('status', 'D')
        step["status"] = self._map_status(status)
        
        # Add timing
        if wsjf_step.get('totTime') is not None:
            step["totTime"] = wsjf_step['totTime']
        
        # Add report text
        if wsjf_step.get('reportText'):
            step["reportText"] = wsjf_step['reportText']
        
        # Add error info
        if wsjf_step.get('errorCode') is not None:
            step["errorCode"] = wsjf_step['errorCode']
        if wsjf_step.get('errorMessage'):
            step["errorMessage"] = wsjf_step['errorMessage']
        
        # Handle step-type-specific data
        if step_type == 'SequenceCall':
            step["stepResults"] = []
            if 'steps' in wsjf_step and wsjf_step['steps']:
                for child_step in wsjf_step['steps']:
                    converted = self._convert_step(child_step)
                    step["stepResults"].append(converted)
        
        elif step_type in ('ET_NLT', 'ET_MNLT'):
            # Numeric limit test
            if 'numericMeas' in wsjf_step and wsjf_step['numericMeas']:
                meas = wsjf_step['numericMeas']
                if isinstance(meas, list) and len(meas) > 0:
                    first_meas = meas[0]
                    step["numericValue"] = first_meas.get('value', 0)
                    
                    comp_op = first_meas.get('compOp', 'LOG')
                    step["compOp"] = comp_op
                    
                    if first_meas.get('lowLimit') is not None:
                        step["lowLimit"] = first_meas['lowLimit']
                    if first_meas.get('highLimit') is not None:
                        step["highLimit"] = first_meas['highLimit']
                    if first_meas.get('unit'):
                        step["unit"] = first_meas['unit']
                    
                    # Handle multiple measurements
                    if len(meas) > 1:
                        step["measurements"] = []
                        for m in meas:
                            measurement = {
                                "numericValue": m.get('value', 0),
                                "status": self._map_status(m.get('status', 'D')),
                            }
                            if m.get('name'):
                                measurement["index"] = m['name']
                            if m.get('compOp'):
                                measurement["compOp"] = m['compOp']
                            if m.get('lowLimit') is not None:
                                measurement["lowLimit"] = m['lowLimit']
                            if m.get('highLimit') is not None:
                                measurement["highLimit"] = m['highLimit']
                            if m.get('unit'):
                                measurement["unit"] = m['unit']
                            step["measurements"].append(measurement)
        
        elif step_type == 'ET_PFT':
            # Pass/fail test
            if 'passFail' in wsjf_step:
                pf = wsjf_step['passFail']
                if isinstance(pf, list) and len(pf) > 0:
                    step["passFailStatus"] = pf[0].get('status') == 'P'
        
        elif step_type == 'ET_SVT':
            # String value test
            if 'stringMeas' in wsjf_step:
                sm = wsjf_step['stringMeas']
                if isinstance(sm, list) and len(sm) > 0:
                    step["stringValue"] = sm[0].get('value', '')
                    if sm[0].get('stringLimit'):
                        step["stringLimit"] = sm[0]['stringLimit']
                    if sm[0].get('compOp'):
                        step["compOp"] = sm[0]['compOp']
        
        elif step_type in ('ET_A', 'ET_GEN'):
            # Action/Generic step
            step["stepType"] = wsjf_step.get('genStepType', 'Action')
        
        # Handle charts
        if 'chart' in wsjf_step and wsjf_step['chart']:
            step["chart"] = wsjf_step['chart']
        
        # Handle attachments
        if 'attachments' in wsjf_step and wsjf_step['attachments']:
            step["attachments"] = wsjf_step['attachments']
        
        return step
    
    def _map_status(self, status: str) -> str:
        """Map WSJF status to WATS status"""
        if status in ('P', 'Passed'):
            return "Passed"
        elif status in ('F', 'Failed'):
            return "Failed"
        elif status in ('E', 'Error'):
            return "Error"
        elif status in ('S', 'Skipped'):
            return "Skipped"
        elif status in ('T', 'Terminated'):
            return "Terminated"
        else:
            return "Done"


# Test code
if __name__ == "__main__":
    sample = {
        "type": "T",
        "pn": "TestPart-001",
        "sn": "SN12345",
        "rev": "A",
        "processCode": 10,
        "processName": "Functional Test",
        "result": "P",
        "machineName": "Station1",
        "start": "2024-01-15T10:00:00",
        "root": {
            "stepType": "SequenceCall",
            "name": "MainSequence",
            "status": "P",
            "totTime": 10.5,
            "steps": [
                {
                    "stepType": "ET_NLT",
                    "name": "VoltageTest",
                    "status": "P",
                    "totTime": 1.2,
                    "numericMeas": [
                        {
                            "compOp": "GELE",
                            "status": "P",
                            "unit": "V",
                            "value": 12.05,
                            "lowLimit": 11.5,
                            "highLimit": 12.5
                        }
                    ]
                },
                {
                    "stepType": "ET_PFT",
                    "name": "SelfTest",
                    "status": "P",
                    "totTime": 0.5,
                    "passFail": [
                        {"status": "P"}
                    ]
                }
            ]
        }
    }
    
    import tempfile
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample, f)
        temp_path = Path(f.name)
    
    try:
        converter = WATSStandardJsonConverter()
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
