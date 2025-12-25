"""
Teradyne ICT Converter (i3070 Format)

Converts Teradyne ICT i3070 test result files into WATS reports.
Port of the C# TeradyneICTConverter.

Expected file format:
- Text-based with lines starting with special patterns
- Program header: path\\PartNumber_x.obc[DD-MMM-YY  HH:MM:SS
- Start test: @DD-MMM-YY  HH:MM:SS
- Main events: ?|"|/|*|&|!|] followed by datetime
- Measurements: CompRef=value(low,high)Type

Event codes:
    ? -> Aborted
    " -> Pass
    / -> Fail
    * -> Error
    & -> SystemError
    ! -> Cancelled
    ] -> ReturnToDiagnose

Also supports newer format with:
    {@BATCH|...}
    {@BTEST|...}
    {@BLOCK|...}
    etc.
"""

import re
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


class Event(Enum):
    """Main event types"""
    ABORTED = "?"
    PASS = '"'
    FAIL = "/"
    ERROR = "*"
    SYSTEM_ERROR = "&"
    CANCELLED = "!"
    RETURN_TO_DIAGNOSE = "]"


class PrefixUnit:
    """Unit prefix with conversion factor"""
    
    def __init__(self, symbol: str, factor: float):
        self.symbol = symbol
        self.factor = factor
    
    def get_value(self, value: float) -> float:
        return value * self.factor
    
    def get_value_inv(self, value: float) -> float:
        return value / self.factor if self.factor != 0 else value


# SI prefix units
PREFIX_UNITS: Dict[str, PrefixUnit] = {
    "P": PrefixUnit("p", 0.000000000001),   # Pico
    "N": PrefixUnit("n", 0.000000001),      # Nano
    "U": PrefixUnit("µ", 0.000001),         # Micro
    "M": PrefixUnit("m", 0.001),            # Milli
    "": PrefixUnit("", 1.0),                # No prefix
    "K": PrefixUnit("K", 1000),             # Kilo
    "MEG": PrefixUnit("M", 1000000),        # Mega
}

# Test type descriptions
TEST_TYPES: Dict[str, Tuple[str, str]] = {
    "AC": ("MEAS DVM ACV", "V"),
    "AI": ("MEAS ACI ACM", ""),
    "AR": ("TEST ARITH", ""),
    "AV": ("MEAS ACV ACM", ""),
    "AY": ("MEAS {DVM | {DMM {VOLTAGE|CURRENT}}}", ""),
    "CS": ("MEAS ACZ CS", ""),
    "CP": ("MEAS ACZ CP", "F"),
    "DC": ("MEAS DVM DCV", "V"),
    "DD": ("MEAS ACZ D", ""),
    "EV": ("FTM EVENT", ""),
    "HZ": ("FTM FREQ", ""),
    "I": ("MEAS DCM DCI", ""),
    "IS": ("TEST DCS DCI", ""),
    "LP": ("MEAS ACZ LP", ""),
    "LS": ("MEAS ACZ LS", ""),
    "QQ": ("MEAS ACZ Q", ""),
    "R": ("MEAS R", "ohm"),
    "RA": ("FTM RATIO", ""),
    "RP": ("MEAS ACZ RP", ""),
    "RS": ("MEAS ACZ RS", ""),
    "S": ("FTM PERIOD", ""),
    "TI": ("FTM INTERNAL", ""),
    "V": ("MEAS DCM DCV", ""),
    "VS": ("TEST DCS DCV", ""),
    "XS": ("MEAS ACZ XS", ""),
    "XP": ("MEAS ACZ XP", ""),
    "ZM": ("MEAS ACZ Z", ""),
}

# General failure messages
GEN_FAILURES: Dict[str, str] = {
    "(S": "SHORTS test, failed",
    "(O": "OPENS test, failed",
    "(B": "BUSTEST, failure caused by bus",
    "(C": "SCRATCHPROBING connection failure",
    "(F": "CONTACT fixture failure",
}


class TeradyneICTConverter(FileConverter):
    """
    Converts Teradyne ICT i3070 test result files to WATS reports.
    
    File qualification:
    - Text file containing program path with .obc extension
    - Contains @ prefix for start markers
    - Contains measurement lines with component references
    
    Also handles newer format with {@BATCH|, {@BTEST| patterns.
    """
    
    # Regex patterns
    RE_START_PROGRAM = re.compile(
        r'^[a-zA-Z]:.*\\(?P<PartNumber>[^_]*?)_?.*(?:\.[Oo][Bb][Cc])\[(?P<DateTime>[0-9-A-Z]+ +[0-9:]+)',
        re.MULTILINE
    )
    RE_START_TEST = re.compile(
        r'^@(?P<DateTime>[0-9-A-Z]+ +[0-9:]+)',
        re.MULTILINE
    )
    RE_MAIN_EVENT = re.compile(
        r'^(?P<Event>[?""/&!\]])(?P<DateTime>[0-9-A-Z]+ +[0-9:]+)',
        re.MULTILINE
    )
    RE_FAILURES_GEN = re.compile(
        r'^(?P<Key>\(S|\(O|\(B|\(C|\(F) *(?P<Info>.*)',
        re.MULTILINE
    )
    RE_MEASURE = re.compile(
        r'^(?P<CompRef>.+?)(?P<Result>[=<>#%])(?P<meas>[0-9.E+-]*)(?P<measU>MEG|[NPUMK]?)'
        r'\((?P<LowLim>[0-9.E+-]*)(?P<LowLimU>MEG|[NPUMK]?),(?P<HighLim>[0-9.E+-]*)(?P<HighLimU>MEG|[NPUMK]?)\)'
        r'(?P<Type>\w*) *=*(?P<Message>.*)',
        re.MULTILINE
    )
    
    # Newer format patterns
    RE_BATCH = re.compile(r'\{@BATCH\|(?P<content>[^}]+)\}')
    RE_BTEST = re.compile(r'\{@BTEST\|(?P<content>[^}]+)\}')
    RE_BLOCK = re.compile(r'\{@BLOCK\|(?P<content>[^}]+)\}')
    RE_A_JUM = re.compile(r'\{@A-JUM\|(?P<content>[^}]+)\}')
    
    @property
    def name(self) -> str:
        return "Teradyne ICT Converter"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Converts Teradyne ICT i3070 test result files into WATS reports"
    
    @property
    def file_patterns(self) -> List[str]:
        return ["*"]  # Accept various text files
    
    @property
    def arguments_schema(self) -> Dict[str, ArgumentDefinition]:
        return {
            "operationTypeCode": ArgumentDefinition(
                arg_type=ArgumentType.STRING,
                default="20",
                description="Operation type code",
            ),
            "stationName": ArgumentDefinition(
                arg_type=ArgumentType.STRING,
                default="",
                description="Station name override",
            ),
            "sequenceVersion": ArgumentDefinition(
                arg_type=ArgumentType.STRING,
                default="1.0",
                description="Sequence version",
            ),
            "partRevision": ArgumentDefinition(
                arg_type=ArgumentType.STRING,
                default="1",
                description="Part revision number",
            ),
        }
    
    def validate(self, source: ConverterSource, context: ConverterContext) -> ValidationResult:
        """
        Validate that the file is a Teradyne ICT format file.
        
        Confidence levels:
        - 0.95: Contains .obc reference and measurement patterns
        - 0.85: Contains {@BATCH|, {@BTEST| patterns (newer format)
        - 0.7: Contains @ start markers
        - 0.0: No recognizable patterns
        """
        if not source.path or not source.path.exists():
            return ValidationResult.no_match("File not found")
        
        try:
            # Read first portion of file
            with open(source.path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(50000)  # Read first 50KB
            
            # Check for newer format first
            has_batch = bool(self.RE_BATCH.search(content))
            has_btest = bool(self.RE_BTEST.search(content))
            has_block = bool(self.RE_BLOCK.search(content))
            
            if has_batch or has_btest or has_block:
                # Parse batch info for validation result
                batch_match = self.RE_BATCH.search(content)
                part_number = ""
                serial_number = ""
                
                if batch_match:
                    batch_content = batch_match.group('content')
                    parts = batch_content.split('|')
                    if len(parts) >= 1:
                        part_number = parts[0].strip()
                
                return ValidationResult(
                    can_convert=True,
                    confidence=0.90,
                    message="Teradyne ICT i3070 format (new format with BATCH/BTEST)",
                    detected_part_number=part_number,
                    detected_serial_number=serial_number,
                )
            
            # Check for classic format
            has_obc = '.obc[' in content.lower() or '.OBC[' in content
            has_start = bool(self.RE_START_TEST.search(content))
            has_measure = bool(self.RE_MEASURE.search(content))
            has_event = bool(self.RE_MAIN_EVENT.search(content))
            
            if has_obc and has_measure:
                # Try to extract part number
                prog_match = self.RE_START_PROGRAM.search(content)
                part_number = prog_match.group('PartNumber') if prog_match else ""
                
                return ValidationResult(
                    can_convert=True,
                    confidence=0.95,
                    message="Teradyne ICT i3070 format (classic)",
                    detected_part_number=part_number,
                )
            
            if has_obc or has_start:
                return ValidationResult(
                    can_convert=True,
                    confidence=0.7,
                    message="Teradyne ICT format (partial match)",
                )
            
            return ValidationResult.no_match("No Teradyne ICT patterns found")
            
        except Exception as e:
            return ValidationResult.no_match(f"Error reading file: {e}")
    
    def convert(self, source: ConverterSource, context: ConverterContext) -> ConverterResult:
        """Convert Teradyne ICT test file to WATS report"""
        if not source.path:
            return ConverterResult.failed_result(error="No file path provided")
        
        try:
            with open(source.path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Detect format and convert
            has_batch = bool(self.RE_BATCH.search(content))
            
            if has_batch:
                return self._convert_new_format(content, source, context)
            else:
                return self._convert_classic_format(content, source, context)
                
        except Exception as e:
            return ConverterResult.failed_result(error=f"Conversion error: {e}")
    
    def _convert_new_format(
        self,
        content: str,
        source: ConverterSource,
        context: ConverterContext
    ) -> ConverterResult:
        """Convert new format with {@BATCH|, {@BTEST| patterns"""
        
        operation_code = context.get_argument("operationTypeCode", "20")
        station_name = context.get_argument("stationName", "")
        seq_version = context.get_argument("sequenceVersion", "1.0")
        part_revision = context.get_argument("partRevision", "1")
        
        # Parse BATCH info
        batch_match = self.RE_BATCH.search(content)
        part_number = source.path.stem if source.path else "Unknown"
        sequence_name = part_number
        
        if batch_match:
            batch_content = batch_match.group('content')
            parts = [p.strip() for p in batch_content.split('|')]
            if parts:
                part_number = parts[0] if parts[0] else part_number
        
        # Build report
        report: Dict[str, Any] = {
            "type": "Test",
            "processCode": operation_code,
            "partNumber": part_number,
            "partRevision": part_revision,
            "serialNumber": self._get_serial_number(source),
            "sequenceName": sequence_name,
            "sequenceVersion": seq_version,
            "result": "P",  # Will be updated based on tests
        }
        
        if station_name:
            report["machineName"] = station_name
        
        # Create root sequence
        root_step: Dict[str, Any] = {
            "type": "SEQ",
            "name": "Root",
            "status": "Done",
            "stepResults": []
        }
        
        # Parse BLOCK elements
        self._parse_blocks(content, root_step, report)
        
        # Parse BTEST elements
        self._parse_btests(content, root_step, report)
        
        report["root"] = root_step
        
        return ConverterResult.success_result(
            report=report,
            post_action=PostProcessAction.MOVE,
        )
    
    def _parse_blocks(
        self,
        content: str,
        root_step: Dict[str, Any],
        report: Dict[str, Any]
    ) -> None:
        """Parse {@BLOCK|...} elements"""
        for match in self.RE_BLOCK.finditer(content):
            block_content = match.group('content')
            parts = [p.strip() for p in block_content.split('|')]
            
            if len(parts) >= 2:
                step_name = parts[0]
                status = parts[-1] if parts[-1] in ('P', 'F', 'E') else 'P'
                
                step = {
                    "type": "PF",
                    "name": step_name,
                    "stepStatus": "Passed" if status == 'P' else "Failed",
                }
                root_step["stepResults"].append(step)
                
                if status == 'F':
                    report["result"] = "F"
    
    def _parse_btests(
        self,
        content: str,
        root_step: Dict[str, Any],
        report: Dict[str, Any]
    ) -> None:
        """Parse {@BTEST|...} elements"""
        current_group = ""
        current_sequence: Optional[Dict[str, Any]] = None
        
        for match in self.RE_BTEST.finditer(content):
            btest_content = match.group('content')
            parts = [p.strip() for p in btest_content.split('|')]
            
            if len(parts) < 2:
                continue
            
            comp_ref = parts[0]
            
            # Group by first character
            group_char = comp_ref[0] if comp_ref else 'X'
            
            if current_group != group_char:
                current_group = group_char
                current_sequence = {
                    "type": "SEQ",
                    "name": f"{group_char}-Group",
                    "status": "Done",
                    "stepResults": []
                }
                root_step["stepResults"].append(current_sequence)
            
            # Parse measurement
            step = self._parse_btest_step(parts)
            if step and current_sequence:
                current_sequence["stepResults"].append(step)
                
                if step.get("stepStatus") == "Failed":
                    current_sequence["status"] = "Failed"
                    report["result"] = "F"
    
    def _parse_btest_step(self, parts: List[str]) -> Optional[Dict[str, Any]]:
        """Parse a BTEST step from its parts"""
        if len(parts) < 3:
            return None
        
        comp_ref = parts[0]
        test_type = parts[1] if len(parts) > 1 else ""
        
        # Try to find measurement and limits
        meas = None
        low_limit = None
        high_limit = None
        status = "Passed"
        unit = TEST_TYPES.get(test_type, ("", ""))[1]
        
        for part in parts[2:]:
            if part.startswith('M:'):  # Measurement
                try:
                    meas = float(part[2:])
                except ValueError:
                    pass
            elif part.startswith('L:'):  # Low limit
                try:
                    low_limit = float(part[2:])
                except ValueError:
                    pass
            elif part.startswith('H:'):  # High limit
                try:
                    high_limit = float(part[2:])
                except ValueError:
                    pass
            elif part in ('F', 'FAIL'):
                status = "Failed"
            elif part in ('P', 'PASS'):
                status = "Passed"
        
        step_name = f"{comp_ref}({test_type})" if test_type else comp_ref
        
        if meas is not None:
            step: Dict[str, Any] = {
                "type": "NT",
                "name": step_name,
                "numericValue": meas,
                "stepStatus": status,
            }
            
            if low_limit is not None and high_limit is not None:
                step["compOp"] = "GELE"
                step["lowLimit"] = low_limit
                step["highLimit"] = high_limit
            elif low_limit is not None:
                step["compOp"] = "GE"
                step["lowLimit"] = low_limit
            elif high_limit is not None:
                step["compOp"] = "LE"
                step["highLimit"] = high_limit
            
            if unit:
                step["unit"] = unit
            
            return step
        else:
            return {
                "type": "PF",
                "name": step_name,
                "stepStatus": status,
            }
    
    def _convert_classic_format(
        self,
        content: str,
        source: ConverterSource,
        context: ConverterContext
    ) -> ConverterResult:
        """Convert classic format with .obc and measurement patterns"""
        
        operation_code = context.get_argument("operationTypeCode", "20")
        station_name = context.get_argument("stationName", "")
        seq_version = context.get_argument("sequenceVersion", "1.0")
        part_revision = context.get_argument("partRevision", "1")
        
        # Parse program header
        prog_match = self.RE_START_PROGRAM.search(content)
        part_number = ""
        sequence_name = ""
        
        if prog_match:
            part_number = prog_match.group('PartNumber')
            # Extract sequence name from full path
            line_end = content.find('\n', prog_match.start())
            if line_end > prog_match.start():
                line = content[prog_match.start():line_end]
                bracket_pos = line.find('[')
                if bracket_pos > 0:
                    sequence_name = line[:bracket_pos]
        
        if not part_number and source.path:
            # Try using filename
            part_number = source.path.stem.split('_')[0]
        
        # Parse start test
        start_match = self.RE_START_TEST.search(content)
        start_time = None
        if start_match:
            try:
                start_time = datetime.strptime(
                    start_match.group('DateTime').strip(),
                    "%d-%b-%y  %H:%M:%S"
                )
            except ValueError:
                pass
        
        # Parse main event for end time and status
        event_match = None
        uut_status = "P"
        end_time = None
        
        for match in self.RE_MAIN_EVENT.finditer(content):
            event_match = match
        
        if event_match:
            event_char = event_match.group('Event')
            if event_char == '"':
                uut_status = "P"
            elif event_char == '/':
                uut_status = "F"
            elif event_char in ('?', '!'):
                uut_status = "T"  # Terminated
            elif event_char in ('*', '&'):
                uut_status = "E"  # Error
            
            try:
                end_time = datetime.strptime(
                    event_match.group('DateTime').strip(),
                    "%d-%b-%y  %H:%M:%S"
                )
            except ValueError:
                pass
        
        # Build report
        report: Dict[str, Any] = {
            "type": "Test",
            "processCode": operation_code,
            "partNumber": part_number,
            "partRevision": part_revision,
            "serialNumber": self._get_serial_number(source),
            "sequenceName": sequence_name or part_number,
            "sequenceVersion": seq_version,
            "result": uut_status,
        }
        
        if start_time:
            report["start"] = start_time.isoformat()
        
        if start_time and end_time:
            report["execTime"] = (end_time - start_time).total_seconds()
        
        if station_name:
            report["machineName"] = station_name
        
        # Create root sequence
        root_step: Dict[str, Any] = {
            "type": "SEQ",
            "name": "Root",
            "status": "Done" if uut_status == "P" else "Failed",
            "stepResults": []
        }
        
        # Parse general failures
        for failure_match in self.RE_FAILURES_GEN.finditer(content):
            key = failure_match.group('Key')
            info = failure_match.group('Info')
            
            step = {
                "type": "ST",
                "name": GEN_FAILURES.get(key, "Unknown failure"),
                "stepStatus": "Failed",
                "reportText": info,
            }
            root_step["stepResults"].append(step)
        
        # Parse measurements
        self._parse_measurements(content, root_step)
        
        report["root"] = root_step
        
        return ConverterResult.success_result(
            report=report,
            post_action=PostProcessAction.MOVE,
        )
    
    def _parse_measurements(
        self,
        content: str,
        root_step: Dict[str, Any]
    ) -> None:
        """Parse measurement lines and group by component reference prefix"""
        
        comp_ref_groups: Dict[str, int] = {}
        current_group = ""
        current_sequence: Optional[Dict[str, Any]] = None
        
        for match in self.RE_MEASURE.finditer(content):
            comp_ref = match.group('CompRef')
            result = match.group('Result')
            meas_str = match.group('meas')
            meas_unit = match.group('measU') or ""
            low_lim_str = match.group('LowLim')
            low_lim_unit = match.group('LowLimU') or ""
            high_lim_str = match.group('HighLim')
            high_lim_unit = match.group('HighLimU') or ""
            test_type = match.group('Type')
            message = match.group('Message')
            
            # Group by first character
            comp_ref_type = comp_ref[0] if comp_ref else 'X'
            
            if comp_ref_type not in comp_ref_groups:
                comp_ref_groups[comp_ref_type] = 0
            
            if current_group != comp_ref_type:
                comp_ref_groups[comp_ref_type] += 1
                current_group = comp_ref_type
                current_sequence = {
                    "type": "SEQ",
                    "name": f"{comp_ref_type}-Group{comp_ref_groups[comp_ref_type]}",
                    "status": "Done",
                    "stepResults": []
                }
                root_step["stepResults"].append(current_sequence)
            
            # Create step
            step_name = f"{comp_ref}({test_type})" if test_type else comp_ref
            
            if meas_str:
                try:
                    meas = float(meas_str)
                    meas_prefix = PREFIX_UNITS.get(meas_unit, PREFIX_UNITS[""])
                    
                    step: Dict[str, Any] = {
                        "type": "NT",
                        "name": step_name,
                        "numericValue": meas,
                    }
                    
                    # Add limits
                    if low_lim_str and high_lim_str:
                        low_lim = float(low_lim_str)
                        high_lim = float(high_lim_str)
                        
                        # Convert limits to measurement unit
                        if low_lim_unit != meas_unit:
                            low_prefix = PREFIX_UNITS.get(low_lim_unit, PREFIX_UNITS[""])
                            low_lim = self._convert_units(low_lim, low_prefix, meas_prefix)
                        if high_lim_unit != meas_unit:
                            high_prefix = PREFIX_UNITS.get(high_lim_unit, PREFIX_UNITS[""])
                            high_lim = self._convert_units(high_lim, high_prefix, meas_prefix)
                        
                        step["compOp"] = "GELE"
                        step["lowLimit"] = low_lim
                        step["highLimit"] = high_lim
                    elif low_lim_str:
                        low_lim = float(low_lim_str)
                        step["compOp"] = "GE"
                        step["lowLimit"] = low_lim
                    elif high_lim_str:
                        high_lim = float(high_lim_str)
                        step["compOp"] = "LE"
                        step["highLimit"] = high_lim
                    
                    # Add unit
                    unit_str = f"{meas_prefix.symbol}({test_type})" if test_type else meas_prefix.symbol
                    if unit_str:
                        step["unit"] = unit_str
                    
                    # Set status
                    if result in ('=', '#'):
                        step["stepStatus"] = "Passed" if result == '=' else "Done"
                    else:
                        step["stepStatus"] = "Failed"
                        if current_sequence:
                            current_sequence["status"] = "Failed"
                    
                    if message:
                        step["reportText"] = message
                    
                    if current_sequence:
                        current_sequence["stepResults"].append(step)
                        
                except ValueError:
                    pass  # Skip invalid measurements
            else:
                # Pass/Fail step
                if test_type not in ('IS', 'VS'):  # Filter these
                    step = {
                        "type": "PF",
                        "name": step_name,
                        "stepStatus": "Passed" if result == '=' else "Failed",
                    }
                    
                    if result not in ('=', '#') and current_sequence:
                        current_sequence["status"] = "Failed"
                    
                    if message:
                        step["reportText"] = message
                    
                    if current_sequence:
                        current_sequence["stepResults"].append(step)
    
    def _convert_units(
        self,
        value: float,
        from_unit: PrefixUnit,
        to_unit: PrefixUnit
    ) -> float:
        """Convert value between unit prefixes"""
        real_value = from_unit.get_value(value)
        return to_unit.get_value_inv(real_value)
    
    def _get_serial_number(self, source: ConverterSource) -> str:
        """Get or generate serial number"""
        # Try to load from sn.config in same directory
        if source.path:
            sn_file = source.path.parent / "sn.config"
            if sn_file.exists():
                try:
                    sn = sn_file.read_text().strip()
                    if sn.isdigit():
                        return sn.zfill(10)
                except Exception:
                    pass
        
        # Generate based on timestamp
        return datetime.now().strftime("%Y%m%d%H%M%S")


# Test code
if __name__ == "__main__":
    import json
    
    # Classic format sample
    sample_classic = """M:\\ICtestaus\\teradyne\\Win7\\TS_Released_Programs\\W005506\\binary\\system\\MergedTestProgram.obc[14-SEP-20  12:01:45
@31-JUL-12  14:18:51 SN MP3774501MRS050643E
K500_RLY1_NO=62.532611M(-500M,500M)V
K500_CLEAR#(,)VS
R101=100.5(90,110)R
R102=99.8(90,110)R
C101=10.2U(9U,11U)CP
"31-JUL-12  14:18:59
"""
    
    # New format sample
    sample_new = """{@BATCH|TestBoard|2024-01-15}
{@BLOCK|SHORTS|P}
{@BLOCK|OPENS|P}
{@BTEST|R101|R|M:100.5|L:90|H:110|P}
{@BTEST|R102|R|M:99.8|L:90|H:110|P}
{@BTEST|C101|CP|M:10.2|L:9|H:11|P}
"""
    
    import tempfile
    
    for name, sample in [("Classic", sample_classic), ("New", sample_new)]:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(sample)
            temp_path = Path(f.name)
        
        try:
            converter = TeradyneICTConverter()
            source = ConverterSource.from_file(temp_path)
            context = ConverterContext()
            
            print(f"\n=== {name} Format ===")
            
            # Validate
            validation = converter.validate(source, context)
            print(f"Validation: can_convert={validation.can_convert}, confidence={validation.confidence:.2f}")
            print(f"  Message: {validation.message}")
            
            # Convert
            result = converter.convert(source, context)
            print(f"Conversion status: {result.status.value}")
            if result.report:
                print("Generated report:")
                print(json.dumps(result.report, indent=2))
        finally:
            temp_path.unlink()
