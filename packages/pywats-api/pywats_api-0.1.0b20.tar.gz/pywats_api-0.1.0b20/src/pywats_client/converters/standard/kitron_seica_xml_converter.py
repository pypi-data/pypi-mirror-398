"""
Kitron Seica XML Converter

Converts Kitron/Seica XML test result files into WATS reports.
Port of the C# KitronSeicaXMLConverter.

Expected XML structure:
<R>
    <PrgC>...</PrgC>
    <FidMrk>...</FidMrk>
    <ST NM="programname_version" OP="OperatorName" NMP="BoardName">...</ST>
    <BI BC="Barcode" BCP="SerialNumber" SD="StartDate">
        <TEST F="TestGroup" NM="StepName" MR="Measurement" ML="LowLimit" 
              MH="HighLimit" MU="Unit" TR="Status" TT="TestTime"/>
        ...
    </BI>
    <ET ED="EndDate" NF="FinalStatus"/>
</R>

Status codes:
    TR="0" -> Passed
    TR="1" -> Failed
    NF="0" -> UUT Passed
    NF="1" -> UUT Failed
"""

import xml.etree.ElementTree as ET
import re
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


class KitronSeicaXMLConverter(FileConverter):
    """
    Converts Kitron/Seica XML test result files to WATS reports.
    
    File qualification:
    - File extension must be .xml or .Xml
    - Root element must be 'R'
    - Must contain 'ST', 'BI', and 'ET' elements
    """
    
    @property
    def name(self) -> str:
        return "Kitron Seica XML Converter"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Converts Kitron/Seica XML test result files into WATS reports"
    
    @property
    def file_patterns(self) -> List[str]:
        return ["*.xml", "*.Xml"]
    
    @property
    def arguments_schema(self) -> Dict[str, ArgumentDefinition]:
        return {
            "operationTypeCode": ArgumentDefinition(
                arg_type=ArgumentType.STRING,
                default="10",
                description="Operation type code",
            ),
            "sequenceName": ArgumentDefinition(
                arg_type=ArgumentType.STRING,
                default="SoftwareName",
                description="Sequence name from XML attribute",
            ),
            "sequenceVersion": ArgumentDefinition(
                arg_type=ArgumentType.STRING,
                default="SoftwareVersion",
                description="Sequence version from XML attribute",
            ),
        }
    
    def validate(self, source: ConverterSource, context: ConverterContext) -> ValidationResult:
        """
        Validate that the file is a properly formatted Kitron/Seica XML file.
        
        Confidence levels:
        - 0.95: Has root 'R' element with ST, BI, ET elements and TEST children
        - 0.75: Has 'R' root with partial structure
        - 0.4: Valid XML with 'R' root but missing required elements
        - 0.0: Not valid XML or different structure
        """
        if not source.path or not source.path.exists():
            return ValidationResult.no_match("File not found")
        
        suffix = source.path.suffix.lower()
        if suffix != '.xml':
            return ValidationResult.no_match("Not an XML file")
        
        try:
            tree = ET.parse(source.path)
            root = tree.getroot()
            
            # Check for 'R' root element
            if root.tag != 'R':
                return ValidationResult.no_match(
                    f"XML file but root is '{root.tag}', not 'R'"
                )
            
            # Check for required elements
            xml_st = root.find('ST')
            xml_bis = list(root.findall('BI'))
            xml_et = root.find('ET')
            
            if xml_st is None:
                return ValidationResult(
                    can_convert=True,
                    confidence=0.4,
                    message="Kitron XML but missing ST element"
                )
            
            if not xml_bis:
                return ValidationResult(
                    can_convert=True,
                    confidence=0.5,
                    message="Kitron XML but missing BI elements"
                )
            
            if xml_et is None:
                return ValidationResult(
                    can_convert=True,
                    confidence=0.6,
                    message="Kitron XML but missing ET element"
                )
            
            # Extract info for validation result
            nm = xml_st.get('NM', '')
            # Split name on _ or space to get part number and revision
            splitted_nm = re.split(r'[_\s]', nm)
            part_number = splitted_nm[0] if splitted_nm else ''
            
            # Get serial from first BI
            serial_number = xml_bis[0].get('BCP', '') if xml_bis else ''
            
            # Get status from ET
            nf = xml_et.get('NF', '0') if xml_et is not None else '0'
            result_str = "Passed" if nf == "0" else "Failed"
            
            # Check for TEST elements
            has_tests = any(bi.findall('TEST') for bi in xml_bis)
            confidence = 0.85 if has_tests else 0.7
            
            return ValidationResult(
                can_convert=True,
                confidence=confidence,
                message=f"Valid Kitron/Seica XML ({len(xml_bis)} board(s))",
                detected_serial_number=serial_number,
                detected_part_number=part_number,
                detected_result=result_str,
            )
            
        except ET.ParseError as e:
            return ValidationResult.no_match(f"Invalid XML: {e}")
        except Exception as e:
            return ValidationResult.no_match(f"Error reading file: {e}")
    
    def convert(self, source: ConverterSource, context: ConverterContext) -> ConverterResult:
        """Convert Kitron/Seica XML test file to WATS report(s)"""
        if not source.path:
            return ConverterResult.failed_result(error="No file path provided")
        
        try:
            tree = ET.parse(source.path)
            xml_r = tree.getroot()
            
            # Get arguments
            operation_code = context.get_argument("operationTypeCode", "10")
            seq_name_attr = context.get_argument("sequenceName", "SoftwareName")
            seq_version_attr = context.get_argument("sequenceVersion", "SoftwareVersion")
            
            # Get sections
            xml_st = xml_r.find('ST')
            xml_bis = list(xml_r.findall('BI'))
            xml_et = xml_r.find('ET')
            
            if xml_st is None:
                return ConverterResult.failed_result(error="Missing ST element")
            if not xml_bis:
                return ConverterResult.failed_result(error="Missing BI elements")
            
            # Extract program info from ST
            nm = xml_st.get('NM', '')
            operator = xml_st.get('OP', '')
            board_name = xml_st.get('NMP', '')
            
            # Split name to get part number and revision
            splitted_nm = re.split(r'[_\s]', nm)
            part_number = splitted_nm[0] if len(splitted_nm) > 0 else nm
            part_revision = splitted_nm[1] if len(splitted_nm) > 1 else '1'
            
            # Get end time and status from ET
            end_date_string = xml_et.get('ED', '') if xml_et is not None else ''
            uut_status_string = xml_et.get('NF', '0') if xml_et is not None else '0'
            
            reports = []
            
            # Process each board (BI element)
            for xml_bi in xml_bis:
                report = self._process_board(
                    xml_bi=xml_bi,
                    operator=operator,
                    part_number=part_number,
                    part_revision=part_revision,
                    board_name=board_name,
                    operation_code=operation_code,
                    seq_name=seq_name_attr,
                    seq_version=seq_version_attr,
                    end_date_string=end_date_string,
                    uut_status_string=uut_status_string,
                )
                reports.append(report)
            
            # If single report, return it directly
            # If multiple, return the first one (batch mode would handle multiple)
            if len(reports) == 1:
                return ConverterResult.success_result(
                    report=reports[0],
                    post_action=PostProcessAction.MOVE,
                )
            else:
                return ConverterResult.success_result(
                    report=reports[0],
                    post_action=PostProcessAction.MOVE,
                )
            
        except Exception as e:
            return ConverterResult.failed_result(error=f"Conversion error: {e}")
    
    def _process_board(
        self,
        xml_bi: ET.Element,
        operator: str,
        part_number: str,
        part_revision: str,
        board_name: str,
        operation_code: str,
        seq_name: str,
        seq_version: str,
        end_date_string: str,
        uut_status_string: str,
    ) -> Dict[str, Any]:
        """Process a single board (BI element) into a UUT report"""
        
        # Get board info
        serial_number = xml_bi.get('BCP', '')
        start_date_string = xml_bi.get('SD', '')
        
        # Parse dates
        date_format = "%d-%m-%Y %H:%M:%S"
        start_time = None
        execution_time = 0.0
        
        try:
            if start_date_string:
                start_time = datetime.strptime(start_date_string, date_format)
            if end_date_string and start_time:
                end_time = datetime.strptime(end_date_string, date_format)
                execution_time = (end_time - start_time).total_seconds()
        except ValueError:
            pass  # Use defaults if parsing fails
        
        # Build report
        report: Dict[str, Any] = {
            "type": "Test",
            "processCode": operation_code,
            "partNumber": part_number,
            "partRevision": part_revision,
            "serialNumber": serial_number,
            "operator": operator,
            "sequenceName": seq_name,
            "sequenceVersion": seq_version,
            "result": "P" if uut_status_string == "0" else "F",
        }
        
        if start_time:
            report["start"] = start_time.isoformat()
        
        if execution_time > 0:
            report["execTime"] = execution_time
        
        # Add misc info
        report["miscInfos"] = [
            {"name": "Board Name", "value": board_name}
        ]
        
        # Create root sequence
        root_step: Dict[str, Any] = {
            "type": "SEQ",
            "name": "Root",
            "status": "Done",
            "stepResults": []
        }
        
        # Process tests grouped by test group (F attribute)
        tests = list(xml_bi.findall('TEST'))
        self._process_tests(tests, root_step)
        
        report["root"] = root_step
        
        return report
    
    def _process_tests(self, tests: List[ET.Element], root_step: Dict[str, Any]) -> None:
        """Process TEST elements, grouping by test group (F attribute)"""
        
        current_group = ""
        current_sequence: Optional[Dict[str, Any]] = None
        
        for test in tests:
            test_group = test.get('F', '')
            step_name = test.get('NM', '')
            
            # Parse measurement values
            try:
                measurement = float(test.get('MR', '0'))
            except ValueError:
                measurement = 0.0
            
            try:
                lower_limit = float(test.get('ML', '0'))
            except ValueError:
                lower_limit = 0.0
            
            try:
                upper_limit = float(test.get('MH', '0'))
            except ValueError:
                upper_limit = 0.0
            
            unit = test.get('MU', '')
            status = test.get('TR', '0')
            
            try:
                test_time = float(test.get('TT', '0')) / 1000.0  # Convert ms to seconds
            except ValueError:
                test_time = 0.0
            
            # Create new sequence if group changed
            if current_group == "" or test_group != current_group:
                current_group = test_group
                current_sequence = {
                    "type": "SEQ",
                    "name": test_group,
                    "status": "Done",
                    "stepResults": []
                }
                root_step["stepResults"].append(current_sequence)
            
            # Create numeric limit step
            step: Dict[str, Any] = {
                "type": "NT",
                "name": step_name,
                "numericValue": measurement,
                "compOp": "GELE",
                "lowLimit": lower_limit,
                "highLimit": upper_limit,
                "stepStatus": "Passed" if status == "0" else "Failed",
            }
            
            if unit:
                step["unit"] = unit
            
            if test_time > 0:
                step["totTime"] = test_time
            
            if current_sequence is not None:
                current_sequence["stepResults"].append(step)
    
    @staticmethod
    def _get_step_status(status: str) -> str:
        """Convert status code to WATS status string"""
        return "Passed" if status == "0" else "Failed"
    
    @staticmethod
    def _get_uut_status(status: str) -> str:
        """Convert status code to WATS UUT result"""
        return "P" if status == "0" else "F"


# Test code
if __name__ == "__main__":
    import json
    
    sample_xml = """<?xml version="1.0" encoding="utf-8"?>
<R>
    <FidMrk PRT="0"/>
    <PrgC>Sample Program</PrgC>
    <ST NM="TestBoard_v1.0" OP="TestOperator" NMP="BoardName123"/>
    <BI BC="12345" BCP="SN001" SD="01-01-2024 10:00:00">
        <TEST F="Resistance" NM="R1" MR="99.5" ML="90" MH="110" MU="Ohm" TR="0" TT="500"/>
        <TEST F="Resistance" NM="R2" MR="101.2" ML="90" MH="110" MU="Ohm" TR="0" TT="500"/>
        <TEST F="Voltage" NM="V1" MR="5.01" ML="4.9" MH="5.1" MU="V" TR="0" TT="300"/>
        <TEST F="Voltage" NM="V2" MR="3.29" ML="3.2" MH="3.4" MU="V" TR="0" TT="300"/>
    </BI>
    <ET ED="01-01-2024 10:05:00" NF="0"/>
</R>"""
    
    import tempfile
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.Xml', delete=False) as f:
        f.write(sample_xml)
        temp_path = Path(f.name)
    
    try:
        converter = KitronSeicaXMLConverter()
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
