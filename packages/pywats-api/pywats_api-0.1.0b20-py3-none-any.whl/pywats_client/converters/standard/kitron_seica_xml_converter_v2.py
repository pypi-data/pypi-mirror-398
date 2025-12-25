"""
Kitron Seica XML Converter - V2 Using UUTReport Model

Converts Kitron/Seica XML test result files into WATS reports using pyWATS UUTReport model.
Port of the C# KitronSeicaXMLConverter.

IMPORTANT: This converter uses the pyWATS UUTReport model - NOT raw dictionaries!

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

# pyWATS model imports - REQUIRED
from pywats.domains.report.report_models import UUTReport
from pywats.domains.report.report_models.uut.steps.sequence_call import SequenceCall
from pywats.domains.report.report_models.uut.steps.comp_operator import CompOp

# Converter infrastructure
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


class KitronSeicaXMLConverterV2(FileConverter):
    """
    Converts Kitron/Seica XML test result files to WATS reports using UUTReport model.
    
    File qualification:
    - File extension must be .xml or .Xml
    - Root element must be 'R'
    - Must contain 'ST', 'BI', and 'ET' elements
    """
    
    @property
    def name(self) -> str:
        return "Kitron Seica XML Converter V2"
    
    @property
    def version(self) -> str:
        return "2.0.0"
    
    @property
    def description(self) -> str:
        return "Converts Kitron/Seica XML test result files into WATS reports using UUTReport model"
    
    @property
    def file_patterns(self) -> List[str]:
        return ["*.xml", "*.Xml"]
    
    @property
    def arguments_schema(self) -> Dict[str, ArgumentDefinition]:
        return {
            "operationTypeCode": ArgumentDefinition(
                arg_type=ArgumentType.INTEGER,
                default=10,
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
        """Validate that the file is a properly formatted Kitron/Seica XML file."""
        if not source.path or not source.path.exists():
            return ValidationResult.no_match("File not found")
        
        suffix = source.path.suffix.lower()
        if suffix != '.xml':
            return ValidationResult.no_match("Not an XML file")
        
        try:
            tree = ET.parse(source.path)
            root = tree.getroot()
            
            if root.tag != 'R':
                return ValidationResult.no_match(
                    f"XML file but root is '{root.tag}', not 'R'"
                )
            
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
            
            nm = xml_st.get('NM', '')
            splitted_nm = re.split(r'[_\s]', nm)
            part_number = splitted_nm[0] if splitted_nm else ''
            
            serial_number = xml_bis[0].get('BCP', '') if xml_bis else ''
            
            nf = xml_et.get('NF', '0') if xml_et is not None else '0'
            result_str = "Passed" if nf == "0" else "Failed"
            
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
        """Convert Kitron/Seica XML test file to WATS UUTReport(s)"""
        if not source.path:
            return ConverterResult.failed_result(error="No file path provided")
        
        try:
            tree = ET.parse(source.path)
            xml_r = tree.getroot()
            
            operation_code = context.get_argument("operationTypeCode", 10)
            seq_name_attr = context.get_argument("sequenceName", "SoftwareName")
            seq_version_attr = context.get_argument("sequenceVersion", "1.0")
            
            xml_st = xml_r.find('ST')
            xml_bis = list(xml_r.findall('BI'))
            xml_et = xml_r.find('ET')
            
            if xml_st is None:
                return ConverterResult.failed_result(error="Missing ST element")
            if not xml_bis:
                return ConverterResult.failed_result(error="Missing BI elements")
            
            nm = xml_st.get('NM', '')
            operator = xml_st.get('OP', '')
            board_name = xml_st.get('NMP', '')
            
            splitted_nm = re.split(r'[_\s]', nm)
            part_number = splitted_nm[0] if len(splitted_nm) > 0 else nm
            part_revision = splitted_nm[1] if len(splitted_nm) > 1 else '1'
            
            end_date_string = xml_et.get('ED', '') if xml_et is not None else ''
            uut_status_string = xml_et.get('NF', '0') if xml_et is not None else '0'
            
            reports = []
            
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
        operation_code: int,
        seq_name: str,
        seq_version: str,
        end_date_string: str,
        uut_status_string: str,
    ) -> UUTReport:
        """Process a single board (BI element) into a UUTReport"""
        
        serial_number = xml_bi.get('BCP', '')
        start_date_string = xml_bi.get('SD', '')
        
        date_format = "%d-%m-%Y %H:%M:%S"
        start_time = datetime.now()
        
        try:
            if start_date_string:
                start_time = datetime.strptime(start_date_string, date_format)
        except ValueError:
            pass
        
        # ========================================
        # BUILD REPORT USING UUTReport MODEL
        # ========================================
        
        report = UUTReport(
            pn=part_number,
            sn=serial_number,
            rev=part_revision,
            process_code=operation_code,
            station_name="Seica",
            location="Production",
            purpose="ICT Test",
            result="P" if uut_status_string == "0" else "F",
            start=start_time,
        )
        
        # Add misc info using factory method
        report.add_misc_info(description="Board Name", value=board_name)
        if operator:
            report.add_misc_info(description="Operator", value=operator)
        
        # Get root sequence
        root = report.get_root_sequence_call()
        root.name = seq_name
        root.sequence.version = seq_version
        
        # Process tests grouped by test group (F attribute)
        tests = list(xml_bi.findall('TEST'))
        self._process_tests(tests, root)
        
        return report
    
    def _process_tests(self, tests: List[ET.Element], root: SequenceCall) -> None:
        """Process TEST elements, grouping by test group (F attribute)"""
        
        current_group = ""
        current_sequence: SequenceCall = root
        
        for test in tests:
            test_group = test.get('F', '')
            step_name = test.get('NM', '')
            
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
                test_time = float(test.get('TT', '0')) / 1000.0
            except ValueError:
                test_time = 0.0
            
            # Create new sequence if group changed
            if current_group == "" or test_group != current_group:
                current_group = test_group
                new_sequence = root.add_sequence_call(
                    name=test_group,
                    file_name=f"{test_group}.seq"
                )
                assert isinstance(new_sequence, SequenceCall)
                current_sequence = new_sequence
            
            # Convert status: "0" = Passed, "1" = Failed
            step_status = "P" if status == "0" else "F"
            
            # Create numeric limit step using factory method
            current_sequence.add_numeric_step(
                name=step_name,
                value=measurement,
                unit=unit or "?",
                comp_op=CompOp.GELE,
                low_limit=lower_limit,
                high_limit=upper_limit,
                status=step_status,
                tot_time=test_time if test_time > 0 else None,
            )


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
        converter = KitronSeicaXMLConverterV2()
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
        
        if result.report and isinstance(result.report, UUTReport):
            report = result.report
            print(f"\nGenerated UUTReport:")
            print(f"  Part Number: {report.pn}")
            print(f"  Serial Number: {report.sn}")
            print(f"  Result: {report.result}")
            
            # Serialize to JSON
            report_dict = report.model_dump(mode="json", by_alias=True, exclude_none=True)
            print("\nSerialized Report:")
            print(json.dumps(report_dict, indent=2))
    finally:
        temp_path.unlink()
