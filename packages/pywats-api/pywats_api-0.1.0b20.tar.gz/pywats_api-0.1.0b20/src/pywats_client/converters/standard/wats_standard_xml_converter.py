"""
WATS Standard XML Format Converter (WSXF)

Converts WATS Standard XML Format (WSXF) files into WATS reports.
Port of the C# WATSStandardXMLFormat converter.

Expected file format:
- XML file with WSXF schema
- Root element: <Reports xmlns="http://wats.virinco.com/schemas/WATS/Report/wsxf">
- Contains <Report> elements with UUT/UUR data
- Nested <Step> elements for test results

Step types:
- SequenceCall: Container for nested steps
- ET_NLT: Numeric Limit Test
- ET_MNLT: Multiple Numeric Limit Test
- ET_PFT: Pass/Fail Test
- ET_SVT: String Value Test
- ET_A: Action Step

This format is similar to WSJF but in XML representation.
"""

import xml.etree.ElementTree as ET
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


# WSXF namespace
WSXF_NS = "http://wats.virinco.com/schemas/WATS/Report/wsxf"
WRML_NS = "http://wats.virinco.com/schemas/WATS/Report/wrml"


class WATSStandardXMLConverter(FileConverter):
    """
    Converts WATS Standard XML Format (WSXF/WRML) files to WATS reports.
    
    File qualification:
    - XML file with .xml extension
    - Contains Reports element with WSXF or WRML namespace
    - Contains Report elements with test data
    """
    
    @property
    def name(self) -> str:
        return "WATS Standard XML Format Converter"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Converts WATS Standard XML Format (WSXF/WRML) files into WATS reports"
    
    @property
    def file_patterns(self) -> List[str]:
        return ["*.xml"]
    
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
        Validate that the file is a WSXF/WRML format file.
        
        Confidence levels:
        - 0.98: Valid XML with WSXF/WRML namespace and Report elements
        - 0.85: Valid XML with Reports root but no namespace
        - 0.0: Not valid XML or different format
        """
        if not source.path or not source.path.exists():
            return ValidationResult.no_match("File not found")
        
        suffix = source.path.suffix.lower()
        if suffix != '.xml':
            return ValidationResult.no_match("Not an XML file")
        
        try:
            tree = ET.parse(source.path)
            root = tree.getroot()
            
            # Check for Reports root element
            root_tag = root.tag
            
            # Handle namespaced tag
            is_wsxf = WSXF_NS in root_tag
            is_wrml = WRML_NS in root_tag
            is_reports = 'Reports' in root_tag or root_tag == 'Reports'
            
            if not (is_wsxf or is_wrml or is_reports):
                return ValidationResult.no_match(f"Root element is '{root_tag}', not Reports")
            
            # Find first Report element
            ns = {'wsxf': WSXF_NS, 'wrml': WRML_NS}
            report_elem = None
            
            for prefix, namespace in ns.items():
                report_elem = root.find(f'{{{namespace}}}Report')
                if report_elem is not None:
                    break
            
            if report_elem is None:
                report_elem = root.find('Report')
            
            if report_elem is None:
                # Try direct child
                for child in root:
                    if 'Report' in child.tag:
                        report_elem = child
                        break
            
            if report_elem is None:
                return ValidationResult(
                    can_convert=True,
                    confidence=0.6,
                    message="WSXF/WRML structure but no Report elements found",
                )
            
            # Extract info from Report
            serial_number = report_elem.get('SN', '')
            part_number = report_elem.get('PN', '')
            result = report_elem.get('Result', 'Passed')
            
            return ValidationResult(
                can_convert=True,
                confidence=0.98 if (is_wsxf or is_wrml) else 0.85,
                message="WATS Standard XML Format (WSXF/WRML) file",
                detected_serial_number=serial_number,
                detected_part_number=part_number,
                detected_result=result,
            )
            
        except ET.ParseError as e:
            return ValidationResult.no_match(f"Invalid XML: {e}")
        except Exception as e:
            return ValidationResult.no_match(f"Error reading file: {e}")
    
    def convert(self, source: ConverterSource, context: ConverterContext) -> ConverterResult:
        """Convert WSXF/WRML file to WATS report"""
        if not source.path:
            return ConverterResult.failed_result(error="No file path provided")
        
        try:
            tree = ET.parse(source.path)
            root = tree.getroot()
            
            # Find Report elements
            report_elems = self._find_report_elements(root)
            
            if not report_elems:
                return ConverterResult.failed_result(error="No Report elements found")
            
            # Convert first report (for single report mode)
            # TODO: Support multiple reports
            report = self._convert_report(report_elems[0], context)
            
            return ConverterResult.success_result(
                report=report,
                post_action=PostProcessAction.MOVE,
            )
            
        except ET.ParseError as e:
            return ConverterResult.failed_result(error=f"Invalid XML: {e}")
        except Exception as e:
            return ConverterResult.failed_result(error=f"Conversion error: {e}")
    
    def _find_report_elements(self, root: ET.Element) -> List[ET.Element]:
        """Find all Report elements in the XML"""
        reports = []
        
        # Try with namespaces
        for namespace in [WSXF_NS, WRML_NS]:
            reports.extend(root.findall(f'{{{namespace}}}Report'))
        
        # Try without namespace
        reports.extend(root.findall('Report'))
        
        # Try direct children
        for child in root:
            if 'Report' in child.tag and child not in reports:
                reports.append(child)
        
        return reports
    
    def _convert_report(
        self,
        report_elem: ET.Element,
        context: ConverterContext
    ) -> Dict[str, Any]:
        """Convert a Report element to WATS report format"""
        
        default_process_code = context.get_argument("defaultProcessCode", "10")
        
        # Build report
        report: Dict[str, Any] = {
            "type": "Test",
        }
        
        # Map Report attributes
        attr_mapping = {
            'SN': 'serialNumber',
            'PN': 'partNumber',
            'Rev': 'partRevision',
            'MachineName': 'machineName',
            'Location': 'location',
            'Purpose': 'purpose',
        }
        
        for xml_attr, wats_field in attr_mapping.items():
            value = report_elem.get(xml_attr)
            if value:
                report[wats_field] = value
        
        # Handle result
        result = report_elem.get('Result', 'Passed')
        if result in ('Passed', 'Pass', 'P'):
            report['result'] = 'P'
        elif result in ('Failed', 'Fail', 'F'):
            report['result'] = 'F'
        elif result in ('Error', 'E'):
            report['result'] = 'E'
        elif result in ('Terminated', 'T'):
            report['result'] = 'T'
        else:
            report['result'] = 'P'
        
        # Handle start time
        start = report_elem.get('Start')
        start_utc = report_elem.get('Start_utc')
        if start:
            report['start'] = start
        elif start_utc:
            report['start'] = start_utc
        
        # Find and parse UUT element
        uut_elem = self._find_child(report_elem, 'UUT')
        if uut_elem is not None:
            if uut_elem.get('UserLoginName'):
                report['operator'] = uut_elem.get('UserLoginName')
            if uut_elem.get('BatchSN'):
                report['batchSerialNumber'] = uut_elem.get('BatchSN')
            if uut_elem.get('ExecutionTime'):
                try:
                    report['execTime'] = float(uut_elem.get('ExecutionTime'))
                except ValueError:
                    pass
            if uut_elem.get('FixtureId'):
                report['fixtureId'] = uut_elem.get('FixtureId')
            if uut_elem.get('ErrorCode'):
                try:
                    report['errorCode'] = int(uut_elem.get('ErrorCode'))
                except ValueError:
                    pass
            if uut_elem.get('ErrorMessage'):
                report['errorMessage'] = uut_elem.get('ErrorMessage')
            
            # Get comment
            comment_elem = self._find_child(uut_elem, 'Comment')
            if comment_elem is not None and comment_elem.text:
                report['comment'] = comment_elem.text
        
        # Find and parse Process element
        process_elem = self._find_child(report_elem, 'Process')
        if process_elem is not None:
            if process_elem.get('Code'):
                report['processCode'] = process_elem.get('Code')
            if process_elem.get('Name'):
                report['processName'] = process_elem.get('Name')
        else:
            report['processCode'] = default_process_code
        
        # Parse MiscInfo elements
        misc_infos = []
        for misc_elem in self._find_children(report_elem, 'MiscInfo'):
            desc = misc_elem.get('Description', '')
            value = misc_elem.text or misc_elem.get('Numeric', '')
            if desc:
                misc_infos.append({"name": desc, "value": str(value)})
        
        if misc_infos:
            report['miscInfos'] = misc_infos
        
        # Parse ReportUnitHierarchy (subunits)
        subunits = []
        for unit_elem in self._find_children(report_elem, 'ReportUnitHierarchy'):
            subunits.append({
                "partType": unit_elem.get('PartType', ''),
                "partNumber": unit_elem.get('PN', ''),
                "serialNumber": unit_elem.get('SN', ''),
                "revision": unit_elem.get('Rev', ''),
            })
        
        if subunits:
            report['uutParts'] = subunits
        
        # Parse Step tree
        root_step: Dict[str, Any] = {
            "type": "SEQ",
            "name": "Root",
            "status": "Done",
            "stepResults": []
        }
        
        # Find Step elements
        for step_elem in self._find_children(report_elem, 'Step'):
            converted_step = self._convert_step(step_elem)
            root_step["stepResults"].append(converted_step)
        
        # Update root status based on result
        if report['result'] == 'F':
            root_step["status"] = "Failed"
        
        report['root'] = root_step
        
        return report
    
    def _convert_step(self, step_elem: ET.Element) -> Dict[str, Any]:
        """Convert a Step element to WATS step format"""
        
        step_type = step_elem.get('StepType', 'SequenceCall')
        name = step_elem.get('Name', 'Step')
        status = step_elem.get('Status', 'Done')
        
        step: Dict[str, Any] = {
            "name": name,
            "status": self._map_status(status),
        }
        
        # Add timing
        total_time = step_elem.get('total_time')
        if total_time:
            try:
                step["totTime"] = float(total_time)
            except ValueError:
                pass
        
        # Add report text
        report_text_elem = self._find_child(step_elem, 'ReportText')
        if report_text_elem is not None and report_text_elem.text:
            step["reportText"] = report_text_elem.text
        
        # Add error info
        error_code = step_elem.get('ErrorCode')
        if error_code:
            try:
                step["errorCode"] = int(error_code)
            except ValueError:
                pass
        
        error_msg = step_elem.get('ErrorMessage')
        if error_msg:
            step["errorMessage"] = error_msg
        
        # Handle step type
        if step_type == 'SequenceCall':
            step["type"] = "SEQ"
            step["stepResults"] = []
            
            # Process child steps
            for child_step in self._find_children(step_elem, 'Step'):
                converted = self._convert_step(child_step)
                step["stepResults"].append(converted)
        
        elif step_type in ('ET_NLT', 'NumericLimitTest'):
            step["type"] = "NT"
            
            # Find NumericLimit element
            num_limit = self._find_child(step_elem, 'NumericLimit')
            if num_limit is not None:
                try:
                    step["numericValue"] = float(num_limit.get('NumericValue', '0'))
                except ValueError:
                    step["numericValue"] = 0
                
                comp_op = num_limit.get('CompOperator', 'LOG')
                step["compOp"] = comp_op
                
                if num_limit.get('LowLimit'):
                    try:
                        step["lowLimit"] = float(num_limit.get('LowLimit'))
                    except ValueError:
                        pass
                
                if num_limit.get('HighLimit'):
                    try:
                        step["highLimit"] = float(num_limit.get('HighLimit'))
                    except ValueError:
                        pass
                
                if num_limit.get('Units'):
                    step["unit"] = num_limit.get('Units')
        
        elif step_type in ('ET_MNLT', 'MultipleNumericLimitTest'):
            step["type"] = "NT"
            step["measurements"] = []
            
            # Find all NumericLimit elements
            for num_limit in self._find_children(step_elem, 'NumericLimit'):
                meas: Dict[str, Any] = {
                    "status": self._map_status(num_limit.get('Status', 'Done')),
                }
                
                try:
                    meas["numericValue"] = float(num_limit.get('NumericValue', '0'))
                except ValueError:
                    meas["numericValue"] = 0
                
                if num_limit.get('Name'):
                    meas["index"] = num_limit.get('Name')
                
                if num_limit.get('CompOperator'):
                    meas["compOp"] = num_limit.get('CompOperator')
                
                if num_limit.get('LowLimit'):
                    try:
                        meas["lowLimit"] = float(num_limit.get('LowLimit'))
                    except ValueError:
                        pass
                
                if num_limit.get('HighLimit'):
                    try:
                        meas["highLimit"] = float(num_limit.get('HighLimit'))
                    except ValueError:
                        pass
                
                if num_limit.get('Units'):
                    meas["unit"] = num_limit.get('Units')
                
                step["measurements"].append(meas)
            
            # Set main value from first measurement
            if step["measurements"]:
                first = step["measurements"][0]
                step["numericValue"] = first.get("numericValue", 0)
                if "compOp" in first:
                    step["compOp"] = first["compOp"]
                if "lowLimit" in first:
                    step["lowLimit"] = first["lowLimit"]
                if "highLimit" in first:
                    step["highLimit"] = first["highLimit"]
                if "unit" in first:
                    step["unit"] = first["unit"]
        
        elif step_type in ('ET_PFT', 'PassFailTest'):
            step["type"] = "PF"
            
            # Find PassFail element
            pf_elem = self._find_child(step_elem, 'PassFail')
            if pf_elem is not None:
                pf_status = pf_elem.get('Status', 'Passed')
                step["passFailStatus"] = pf_status in ('Passed', 'Pass', 'P')
        
        elif step_type in ('ET_SVT', 'StringValueTest'):
            step["type"] = "ST"
            
            # Find StringValue element
            sv_elem = self._find_child(step_elem, 'StringValue')
            if sv_elem is not None:
                step["stringValue"] = sv_elem.get('Value', '')
                if sv_elem.get('StringLimit'):
                    step["stringLimit"] = sv_elem.get('StringLimit')
                if sv_elem.get('CompOperator'):
                    step["compOp"] = sv_elem.get('CompOperator')
        
        elif step_type in ('ET_A', 'ActionStep', 'ET_GEN', 'GenericStep'):
            step["type"] = "GEN"
            step["stepType"] = step_elem.get('GenericStepType', 'Action')
        
        else:
            # Default to generic step
            step["type"] = "GEN"
            step["stepType"] = "Action"
        
        return step
    
    def _find_child(self, parent: ET.Element, tag: str) -> Optional[ET.Element]:
        """Find a child element, handling namespaces"""
        # Try without namespace
        elem = parent.find(tag)
        if elem is not None:
            return elem
        
        # Try with namespaces
        for namespace in [WSXF_NS, WRML_NS]:
            elem = parent.find(f'{{{namespace}}}{tag}')
            if elem is not None:
                return elem
        
        # Try matching tag suffix
        for child in parent:
            if child.tag.endswith(tag) or child.tag == tag:
                return child
        
        return None
    
    def _find_children(self, parent: ET.Element, tag: str) -> List[ET.Element]:
        """Find all child elements with given tag, handling namespaces"""
        results = []
        
        # Try without namespace
        results.extend(parent.findall(tag))
        
        # Try with namespaces
        for namespace in [WSXF_NS, WRML_NS]:
            results.extend(parent.findall(f'{{{namespace}}}{tag}'))
        
        # Try matching tag suffix in direct children
        for child in parent:
            if (child.tag.endswith(tag) or child.tag == tag) and child not in results:
                results.append(child)
        
        return results
    
    def _map_status(self, status: str) -> str:
        """Map XML status to WATS status"""
        if status in ('Passed', 'Pass', 'P'):
            return "Passed"
        elif status in ('Failed', 'Fail', 'F'):
            return "Failed"
        elif status in ('Error', 'E'):
            return "Error"
        elif status in ('Skipped', 'S'):
            return "Skipped"
        elif status in ('Terminated', 'T'):
            return "Terminated"
        else:
            return "Done"


# Test code
if __name__ == "__main__":
    import json
    
    sample_xml = """<?xml version="1.0" encoding="utf-8"?>
<Reports xmlns="http://wats.virinco.com/schemas/WATS/Report/wsxf">
  <Report type="UUT" SN="SN12345" PN="PN-001" Rev="A" Result="Passed" 
          MachineName="Station1" Start="2024-01-15T10:00:00">
    <UUT UserLoginName="JohnDoe" ExecutionTime="10.5"/>
    <Process Code="10" Name="Functional Test"/>
    <MiscInfo Description="TestInfo">Some value</MiscInfo>
    <Step Id="1" Name="MainSequence" StepType="SequenceCall" Status="Passed">
      <Step Id="2" Name="VoltageTest" StepType="ET_NLT" Status="Passed">
        <NumericLimit NumericValue="12.05" LowLimit="11.5" HighLimit="12.5" 
                      Units="V" CompOperator="GELE" Status="Passed"/>
      </Step>
      <Step Id="3" Name="SelfTest" StepType="ET_PFT" Status="Passed">
        <PassFail Status="Passed"/>
      </Step>
    </Step>
  </Report>
</Reports>"""
    
    import tempfile
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
        f.write(sample_xml)
        temp_path = Path(f.name)
    
    try:
        converter = WATSStandardXMLConverter()
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
