"""
Teradyne Spectrum ICT Converter - V2 Using UUTReport Model

Converts Teradyne Spectrum ICT test result files into WATS reports using pyWATS UUTReport model.
Port of the C# TerradyneSpectrumICTConverter.

IMPORTANT: This converter uses the pyWATS UUTReport model - NOT raw dictionaries!

Expected file format:
- Text-based with parenthesized fields
- (PROGRAM_NAME: "ProgramName")
- (SECTION_NAME: "SectionName")
- (TYPE: xxx) (TIME: MM/dd/yyyy HH:mm:ss)
- (SNAME: "StepName")
- (DESC: "Description")
- (PAGE_NAME: "PageName") (STAT: Pass|Fail)
- (MEASVAL: (VAL: value) (SCALE: x) (UNIT: unit))
- (LOLIM: (VAL: value) (SCALE: x))
- (HILIM: (VAL: value) (SCALE: x))
- (USER: Keyword: Value)
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field

# pyWATS model imports - REQUIRED
from pywats.domains.report.report_models import UUTReport
from pywats.domains.report.report_models.uut.steps.sequence_call import SequenceCall
from pywats.domains.report.report_models.uut.steps.comp_operator import CompOp
from pywats.domains.report.report_models.uut.step import StepStatus

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


# Scale/prefix factors for unit alignment
SCALE_FACTORS: Dict[str, float] = {
    "p": 1e-12, "pico": 1e-12,
    "n": 1e-9, "nano": 1e-9,
    "u": 1e-6, "micro": 1e-6, "µ": 1e-6,
    "m": 1e-3, "milli": 1e-3,
    "": 1.0,
    "K": 1e3, "k": 1e3, "kilo": 1e3,
    "M": 1e6, "meg": 1e6, "mega": 1e6,
    "G": 1e9, "giga": 1e9,
}


def align_units(from_unit: str, value: float, to_unit: str) -> float:
    """Align a value from one unit scale to another"""
    from_scale = ""
    to_scale = ""
    
    for prefix in SCALE_FACTORS.keys():
        if prefix and from_unit.startswith(prefix):
            from_scale = prefix
            break
    
    for prefix in SCALE_FACTORS.keys():
        if prefix and to_unit.startswith(prefix):
            to_scale = prefix
            break
    
    from_factor = SCALE_FACTORS.get(from_scale, 1.0)
    to_factor = SCALE_FACTORS.get(to_scale, 1.0)
    
    base_value = value * from_factor
    return base_value / to_factor


@dataclass
class SubStep:
    """Represents a sub-step measurement"""
    name: str = ""
    type: str = ""
    meas: Optional[float] = None
    meas_scale: str = ""
    unit: str = ""
    low_lim: Optional[float] = None
    low_scale: str = ""
    high_lim: Optional[float] = None
    high_scale: str = ""
    comment: str = ""
    status: str = "P"  # P=Passed, F=Failed, D=Done


@dataclass
class MainStep:
    """Represents a main step with sub-steps"""
    name: str = ""
    status: str = "P"
    start: Optional[datetime] = None
    description: str = ""
    sub_steps: List[SubStep] = field(default_factory=list)


class TerradyneSpectrumICTConverterV2(FileConverter):
    """
    Converts Teradyne Spectrum ICT test result files to WATS reports using UUTReport model.
    
    File qualification:
    - Text file containing (PROGRAM_NAME: pattern
    - Contains (STEP:, (PAGE:, (MEASVAL:) patterns
    """
    
    # Regex patterns (same as original)
    RE_PROGRAM_NAME = re.compile(r'\(PROGRAM_NAME:\s*"(?P<ProgramName>[^"]+)"\s*\)')
    RE_SECTION_NAME = re.compile(r'\(SECTION_NAME:\s*"(?P<SequenceName>[^"]+)"\s*\)')
    RE_NEW_STEP = re.compile(r'\(TYPE:\s*(?P<TYPE>[^)]+)\s*\)\s*\(TIME:\s*(?P<TIME>[^)]+)\s*\)')
    RE_SNAME = re.compile(r'\(SNAME:\s*"(?P<SNAME>[^"]+)"\s*\)')
    RE_DESC = re.compile(r'\(DESC:\s*"(?P<DESC>[^"]+?)\s*"\s*\)\s*\(PAGE:')
    RE_STEP_TYPE = re.compile(
        r'(?:\(TYPE:\s*(?P<TYPE>[^)]+)\s*\))?\s*'
        r'\(PAGE_NAME:\s*"(?P<PAGE_NAME>[^"]+)"\s*\)\s*'
        r'(?:\(COMMENT:\s*"(?P<COMMENT>[^"]+?)"\s*\))?\s*'
        r'\(STAT:\s*(?P<STAT>\w+)\s*\)'
    )
    RE_GROUP_NAME = re.compile(
        r'\(GROUP_NAME:\s*(?P<GROUP_NAME>[\w\d]+)\s*\)\s*'
        r'\(STAT:\s*(?P<STAT>[\w]+)\s*\)\s*'
        r'\(MEASVAL:\s*\(VAL:\s*(?P<VAL>[0-9.]+)\s*\)\s*\(UNIT:\s*(?P<UNIT>\w+)\s*\)\s*\)'
    )
    RE_CONNECTED_NODES = re.compile(r'\(CONNECTED_NODES:.*?TPNAME:\s*(?P<TPNAME>[^)]+)\)')
    RE_FSCAN_PIN = re.compile(
        r'\(FSCAN_PIN:\s*\(STAT:\s*(?P<STAT>[\w]+)\s*\).*?\(TPNAME:\s*(?P<TPNAME>\w+)\s*\)\s*\)'
    )
    RE_MEAS_VAL_THRESHOLD = re.compile(
        r'\(MEAS_VAL:\s*\(VAL:\s*(?P<VAL>[0-9+\-.E]+)\s*\)\s*\)\s*\(THRESH:\s*(?P<THRESH>[0-9+\-.E]+)\s*\)'
    )
    RE_SERIAL = re.compile(r'\(USER:\s*Serialnumber:\s*(?P<Val>[^)]+)\s*\)')
    RE_OPERATOR = re.compile(r'\(USER:\s*Operator:\s*(?P<Val>[^)]+)\s*\)')
    RE_USER = re.compile(r'\(USER:\s*(?P<Keyword>[^:]+):\s*(?P<Value>[^)]+)\s*\)')
    RE_PROG_NAME = re.compile(r'\(PROG_NAME:\s*(?P<PName>[^)]+)\s*\)')
    
    @property
    def name(self) -> str:
        return "Teradyne Spectrum ICT Converter V2"
    
    @property
    def version(self) -> str:
        return "2.0.0"
    
    @property
    def description(self) -> str:
        return "Converts Teradyne Spectrum ICT test result files into WATS reports using UUTReport model"
    
    @property
    def file_patterns(self) -> List[str]:
        return ["*.txt", "PB*.txt"]
    
    @property
    def arguments_schema(self) -> Dict[str, ArgumentDefinition]:
        return {
            "operationTypeCode": ArgumentDefinition(
                arg_type=ArgumentType.STRING,
                default="30",
                description="Operation type code",
            ),
            "programNameToPartNumberRegEx": ArgumentDefinition(
                arg_type=ArgumentType.STRING,
                default=r"(?P<PartNumber>\w+)",
                description="Regex to extract part number from program name",
            ),
            "userInfoAddMiscInfo": ArgumentDefinition(
                arg_type=ArgumentType.STRING,
                default="OrderNumber;CustomerSerialnumber;TestSpecRef",
                description="Semicolon-separated list of USER fields to add as MiscInfo",
            ),
            "userInfoStationName": ArgumentDefinition(
                arg_type=ArgumentType.STRING,
                default="Machine",
                description="USER field to use as station name",
            ),
            "userInfoSequenceVersion": ArgumentDefinition(
                arg_type=ArgumentType.STRING,
                default="SequenceRev",
                description="USER field to use as sequence version",
            ),
        }
    
    def validate(self, source: ConverterSource, context: ConverterContext) -> ValidationResult:
        """Validate that the file is a Teradyne Spectrum format file."""
        if not source.path or not source.path.exists():
            return ValidationResult.no_match("File not found")
        
        suffix = source.path.suffix.lower()
        if suffix != '.txt':
            return ValidationResult.no_match("Not a text file")
        
        try:
            with open(source.path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(30000)
            
            has_program = bool(self.RE_PROGRAM_NAME.search(content))
            has_measval = bool(re.search(r'\(MEASVAL:', content))
            has_step_type = bool(self.RE_STEP_TYPE.search(content))
            
            if has_program and has_measval:
                prog_match = self.RE_PROGRAM_NAME.search(content)
                program_name = prog_match.group('ProgramName') if prog_match else ""
                
                pn_regex = context.get_argument(
                    "programNameToPartNumberRegEx",
                    r"(?P<PartNumber>\w+)"
                )
                try:
                    pn_match = re.search(pn_regex, program_name)
                    part_number = pn_match.group('PartNumber') if pn_match else program_name
                except Exception:
                    part_number = program_name
                
                sn_match = self.RE_SERIAL.search(content)
                serial_number = sn_match.group('Val').strip() if sn_match else ""
                
                return ValidationResult(
                    can_convert=True,
                    confidence=0.95,
                    message="Teradyne Spectrum ICT format",
                    detected_part_number=part_number,
                    detected_serial_number=serial_number,
                )
            
            if has_program:
                return ValidationResult(
                    can_convert=True,
                    confidence=0.85,
                    message="Teradyne Spectrum format (partial match)",
                )
            
            if has_step_type:
                return ValidationResult(
                    can_convert=True,
                    confidence=0.7,
                    message="Possible Teradyne format",
                )
            
            return ValidationResult.no_match("No Teradyne Spectrum patterns found")
            
        except Exception as e:
            return ValidationResult.no_match(f"Error reading file: {e}")
    
    def convert(self, source: ConverterSource, context: ConverterContext) -> ConverterResult:
        """Convert Teradyne Spectrum test file to WATS UUTReport"""
        if not source.path:
            return ConverterResult.failed_result(error="No file path provided")
        
        try:
            with open(source.path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            content = self._preprocess_content(content)
            return self._parse_content(content, source, context)
            
        except Exception as e:
            return ConverterResult.failed_result(error=f"Conversion error: {e}")
    
    def _preprocess_content(self, content: str) -> str:
        """Preprocess content to handle multi-line entries"""
        lines = content.split('\n')
        result_lines = []
        buffer = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line.endswith(':') or line.endswith(')'):
                if buffer:
                    result_lines.append(buffer + line)
                    buffer = ""
                else:
                    result_lines.append(line)
            else:
                buffer += line
        
        if buffer:
            result_lines.append(buffer)
        
        return '\n'.join(result_lines)
    
    def _parse_content(
        self,
        content: str,
        source: ConverterSource,
        context: ConverterContext
    ) -> ConverterResult:
        """Parse content and build WATS UUTReport"""
        
        operation_code = int(context.get_argument("operationTypeCode", "30"))
        pn_regex = context.get_argument("programNameToPartNumberRegEx", r"(?P<PartNumber>\w+)")
        misc_info_fields = context.get_argument(
            "userInfoAddMiscInfo",
            "OrderNumber;CustomerSerialnumber;TestSpecRef"
        ).split(';')
        station_name_field = context.get_argument("userInfoStationName", "Machine")
        seq_version_field = context.get_argument("userInfoSequenceVersion", "SequenceRev")
        
        # Parse program name
        prog_match = self.RE_PROGRAM_NAME.search(content)
        program_name = prog_match.group('ProgramName') if prog_match else (source.path.stem if source.path else "Unknown")
        
        # Extract part number
        try:
            pn_match = re.search(pn_regex, program_name)
            part_number = pn_match.group('PartNumber') if pn_match else program_name
        except Exception:
            part_number = program_name
        
        # Parse serial and operator
        sn_match = self.RE_SERIAL.search(content)
        serial_number = sn_match.group('Val').strip() if sn_match else datetime.now().strftime("%Y%m%d%H%M%S")
        
        op_match = self.RE_OPERATOR.search(content)
        operator = op_match.group('Val').strip() if op_match else ""
        
        # Parse USER fields
        station_name = "TeradyneSpectrum"
        sequence_version = "1.0"
        misc_infos: List[Tuple[str, str]] = []
        uut_status = "P"
        
        for user_match in self.RE_USER.finditer(content):
            keyword = user_match.group('Keyword').strip()
            value = user_match.group('Value').strip()
            
            if keyword in misc_info_fields:
                misc_infos.append((keyword, value))
            
            if keyword == station_name_field:
                station_name = value
            
            if keyword == seq_version_field:
                sequence_version = value
            
            if keyword == "STATUS" and "FAIL" in value.upper():
                uut_status = "F"
        
        # ========================================
        # BUILD REPORT USING UUTReport MODEL
        # ========================================
        
        report = UUTReport(
            pn=part_number,
            sn=serial_number,
            rev="1",
            process_code=operation_code,
            station_name=station_name,
            location="Production",
            purpose="ICT Test",
            result=uut_status,
            start=datetime.now(),  # Will be updated when we find first step time
        )
        
        # Add file name as misc info using factory method
        if source.path:
            report.add_misc_info(description="File", value=source.path.name)
        
        # Add operator as misc info (since operator field may not be directly on report)
        if operator:
            report.add_misc_info(description="Operator", value=operator)
        
        # Add USER fields as misc info
        for name, value in misc_infos:
            report.add_misc_info(description=name, value=value)
        
        # Get root sequence
        root = report.get_root_sequence_call()
        root.name = program_name
        root.sequence.version = sequence_version
        
        # Parse steps and update report
        start_time, execution_time = self._parse_steps(content, root, report)
        
        if start_time:
            report.start = start_time
        
        # Update result based on any failed steps
        if uut_status == "F":
            report.result = "F"
        
        return ConverterResult.success_result(
            report=report,
            post_action=PostProcessAction.MOVE,
        )
    
    def _parse_steps(
        self,
        content: str,
        root: SequenceCall,
        report: UUTReport
    ) -> Tuple[Optional[datetime], float]:
        """Parse step content and return (start_time, execution_time)"""
        
        current_sequence: SequenceCall = root
        current_main_step: Optional[MainStep] = None
        prev_main_step: Optional[MainStep] = None
        start_time: Optional[datetime] = None
        
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for new section
            section_match = self.RE_SECTION_NAME.search(line)
            if section_match:
                if current_main_step and current_sequence:
                    self._create_steps(current_main_step, current_sequence, prev_main_step, report)
                    if current_main_step.start:
                        prev_main_step = current_main_step
                    current_main_step = MainStep()
                
                seq_name = section_match.group('SequenceName')
                new_sequence = root.add_sequence_call(name=seq_name, file_name=f"{seq_name}.seq")
                assert isinstance(new_sequence, SequenceCall)
                current_sequence = new_sequence
                continue
            
            # Check for new step (TYPE/TIME)
            step_match = self.RE_NEW_STEP.search(line)
            if step_match:
                if current_main_step and current_sequence:
                    self._create_steps(current_main_step, current_sequence, prev_main_step, report)
                
                if current_main_step and current_main_step.start:
                    prev_main_step = current_main_step
                
                current_main_step = MainStep()
                
                try:
                    time_str = step_match.group('TIME').strip()
                    current_main_step.start = datetime.strptime(time_str, "%m/%d/%Y %H:%M:%S")
                    if start_time is None:
                        start_time = current_main_step.start
                except ValueError:
                    pass
                continue
            
            # Check for step name (SNAME)
            sname_match = self.RE_SNAME.search(line)
            if sname_match and current_main_step:
                current_main_step.name = sname_match.group('SNAME')
                continue
            
            # Check for description
            desc_match = self.RE_DESC.search(line)
            if desc_match and current_main_step:
                current_main_step.description = desc_match.group('DESC')
                continue
            
            # Check for step type (PAGE_NAME with STAT)
            step_type_match = self.RE_STEP_TYPE.search(line)
            if step_type_match and current_main_step:
                sub_step = SubStep(
                    name=step_type_match.group('PAGE_NAME'),
                    comment=step_type_match.group('COMMENT') or "",
                    status=self._parse_status(step_type_match.group('STAT'))
                )
                current_main_step.sub_steps.append(sub_step)
                
                if sub_step.status == "F":
                    report.result = "F"
                continue
            
            # Check for connected nodes
            nodes_match = self.RE_CONNECTED_NODES.search(line)
            if nodes_match and current_main_step and current_main_step.sub_steps:
                tpname = nodes_match.group('TPNAME')
                current_main_step.sub_steps[-1].name += f" - {tpname}"
                continue
            
            # Check for GROUP_NAME
            group_match = self.RE_GROUP_NAME.search(line)
            if group_match and current_main_step:
                sub_step = SubStep(
                    name=group_match.group('GROUP_NAME'),
                    meas=float(group_match.group('VAL')),
                    status=self._parse_status(group_match.group('STAT'))
                )
                if current_main_step.sub_steps:
                    sub_step.high_lim = current_main_step.sub_steps[0].high_lim
                current_main_step.sub_steps.append(sub_step)
                
                if sub_step.status == "F":
                    report.result = "F"
                continue
            
            # Check for FSCAN_PIN
            fscan_match = self.RE_FSCAN_PIN.search(line)
            if fscan_match and current_main_step:
                sub_step = SubStep(
                    name=fscan_match.group('TPNAME'),
                    status=self._parse_status(fscan_match.group('STAT'))
                )
                current_main_step.sub_steps.append(sub_step)
                
                if sub_step.status == "F":
                    report.result = "F"
                continue
            
            # Check for MEAS_VAL_THRESHOLD
            thresh_match = self.RE_MEAS_VAL_THRESHOLD.search(line)
            if thresh_match and current_main_step and current_main_step.sub_steps:
                current_main_step.sub_steps[-1].meas = float(thresh_match.group('VAL'))
                current_main_step.sub_steps[-1].low_lim = float(thresh_match.group('THRESH'))
                continue
            
            # Check for limits and measurements
            if current_main_step and current_main_step.sub_steps:
                self._parse_limits_and_meas(line, current_main_step.sub_steps[-1])
            
            # Check for PROG_NAME
            prog_name_match = self.RE_PROG_NAME.search(line)
            if prog_name_match and current_main_step and current_main_step.sub_steps:
                current_main_step.sub_steps[-1].comment = f"EXT_PROG: {prog_name_match.group('PName')}"
        
        # Process final main step
        if current_main_step and current_sequence:
            self._create_steps(current_main_step, current_sequence, prev_main_step, report)
        
        # Calculate execution time
        execution_time = 0.0
        if start_time and current_main_step and current_main_step.start:
            execution_time = (current_main_step.start - start_time).total_seconds()
        elif start_time and prev_main_step and prev_main_step.start:
            execution_time = (prev_main_step.start - start_time).total_seconds()
        
        return start_time, execution_time
    
    def _parse_limits_and_meas(self, line: str, sub_step: SubStep) -> None:
        """Parse LOLIM, HILIM, MEASVAL from a line"""
        
        lo_match = re.search(
            r'\((?:LOLIM|LOW):\s*\(VAL:\s*(?P<VAL>[0-9+\-.E]+)\s*\)\s*(?:\(SCALE:\s*(?P<SCALE>[^)]+)\s*\))?\s*(?:\(UNIT:\s*(?P<UNIT>[^)]+)\s*\))?\s*\)',
            line
        )
        if lo_match:
            sub_step.low_lim = float(lo_match.group('VAL'))
            sub_step.low_scale = lo_match.group('SCALE') or ""
        
        hi_match = re.search(
            r'\((?:HILIM|HIGH):\s*\(VAL:\s*(?P<VAL>[0-9+\-.E]+)\s*\)\s*(?:\(SCALE:\s*(?P<SCALE>[^)]+)\s*\))?\s*(?:\(UNIT:\s*(?P<UNIT>[^)]+)\s*\))?\s*\)',
            line
        )
        if hi_match:
            sub_step.high_lim = float(hi_match.group('VAL'))
            sub_step.high_scale = hi_match.group('SCALE') or ""
        
        meas_match = re.search(
            r'\(MEASVAL:\s*\(VAL:\s*(?P<VAL>[0-9+\-.E]+)\s*\)\s*(?:\(SCALE:\s*(?P<SCALE>[^)]+)\s*\))?\s*(?:\(UNIT:\s*(?P<UNIT>[^)]+)\s*\))?\s*\)',
            line
        )
        if meas_match:
            sub_step.meas = float(meas_match.group('VAL'))
            sub_step.meas_scale = meas_match.group('SCALE') or ""
            sub_step.unit = meas_match.group('UNIT') or ""
    
    def _create_steps(
        self,
        main_step: MainStep,
        sequence: SequenceCall,
        prev_step: Optional[MainStep],
        report: UUTReport
    ) -> None:
        """Create WATS steps from a MainStep using UUTReport factory methods"""
        
        if not main_step.sub_steps:
            return
        
        target_seq = sequence
        
        # If multiple sub-steps, create a nested sequence
        if len(main_step.sub_steps) > 1:
            new_seq = sequence.add_sequence_call(
                name=main_step.name or "Step",
                file_name=f"{main_step.name or 'Step'}.seq"
            )
            assert isinstance(new_seq, SequenceCall)
            
            # Note: reportText would be set via the step's report_text field if needed
            target_seq = new_seq
        
        for sub_step in main_step.sub_steps:
            self._create_sub_step(sub_step, main_step, target_seq, report)
        
        # For single sub-step, add description to the step if it exists
        # This would need to be handled via the step's report_text
    
    def _create_sub_step(
        self,
        sub_step: SubStep,
        main_step: MainStep,
        sequence: SequenceCall,
        report: UUTReport
    ) -> None:
        """Create a WATS step from a SubStep using factory methods"""
        
        if sub_step.type == "DELAY":
            # Add as a string step for actions/wait
            sequence.add_string_step(
                name=sub_step.name,
                value="Wait",
                status=sub_step.status,
            )
            return
        
        if sub_step.meas is not None:
            # Numeric limit step using add_numeric_step factory method
            unit = sub_step.unit or "?"
            meas_scale = sub_step.meas_scale or ""
            
            # Align limits to measurement scale
            low_lim = sub_step.low_lim
            high_lim = sub_step.high_lim
            
            if low_lim is not None and sub_step.low_scale and sub_step.low_scale != meas_scale:
                low_lim = align_units(
                    sub_step.low_scale + unit,
                    low_lim,
                    meas_scale + unit
                )
            
            if high_lim is not None and sub_step.high_scale and sub_step.high_scale != meas_scale:
                high_lim = align_units(
                    sub_step.high_scale + unit,
                    high_lim,
                    meas_scale + unit
                )
            
            # Determine comp_op based on limits
            comp_op = CompOp.LOG
            if low_lim is not None and high_lim is not None:
                comp_op = CompOp.GELE
            elif low_lim is not None:
                comp_op = CompOp.GE
            elif high_lim is not None:
                comp_op = CompOp.LE
            
            # Build report text from comment
            report_text = None
            if sub_step.comment:
                comment = sub_step.comment.replace("Analysis Comments:", "").replace("Testable.", "").strip()
                if comment:
                    report_text = comment
            
            # Add numeric step using factory method
            sequence.add_numeric_step(
                name=sub_step.name,
                value=sub_step.meas,
                unit=meas_scale + unit,
                comp_op=comp_op,
                low_limit=low_lim,
                high_limit=high_lim,
                status=sub_step.status,
                reportText=report_text,
            )
        else:
            # Boolean step for pass/fail actions without measurements
            report_text = None
            if sub_step.comment:
                comment = sub_step.comment.replace("Analysis Comments:", "").replace("Testable.", "").strip()
                if comment:
                    report_text = comment
            
            sequence.add_boolean_step(
                name=sub_step.name,
                status=sub_step.status,
                report_text=report_text,
            )
    
    def _parse_status(self, status: str) -> str:
        """Convert status string to WATS status (P/F/D/S)"""
        status_upper = status.upper().strip()
        if status_upper in ('PASS', 'PASSED', 'P'):
            return "P"
        elif status_upper in ('FAIL', 'FAILED', 'F'):
            return "F"
        elif status_upper in ('ERROR', 'E'):
            return "F"  # Treat error as failed
        else:
            return "P"  # Default to passed for "Done" etc


# Test code
if __name__ == "__main__":
    import json
    
    sample = """(PROGRAM_NAME: "PB2941200_TestBoard")
(SECTION_NAME: "Initial Tests")
(TYPE: Analog) (TIME: 01/15/2024 10:30:00)
(SNAME: "Resistance Test")
(DESC: "Test board resistance")
(PAGE_NAME: "R101") (STAT: Pass)
(LOLIM: (VAL: 90) (SCALE: ) (UNIT: Ohm))
(HILIM: (VAL: 110) (SCALE: ) (UNIT: Ohm))
(MEASVAL: (VAL: 100.5) (SCALE: ) (UNIT: Ohm))
(TYPE: Analog) (TIME: 01/15/2024 10:30:05)
(SNAME: "Capacitance Test")
(DESC: "Test board capacitance")
(PAGE_NAME: "C101") (STAT: Pass)
(LOLIM: (VAL: 9) (SCALE: u) (UNIT: F))
(HILIM: (VAL: 11) (SCALE: u) (UNIT: F))
(MEASVAL: (VAL: 10.2) (SCALE: u) (UNIT: F))
(USER: Serialnumber: SN12345)
(USER: Operator: JohnDoe)
(USER: Machine: Station1)
"""
    
    import tempfile
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(sample)
        temp_path = Path(f.name)
    
    try:
        converter = TerradyneSpectrumICTConverterV2()
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
            print(json.dumps(report_dict, indent=2)[:2000])  # First 2000 chars
    finally:
        temp_path.unlink()
