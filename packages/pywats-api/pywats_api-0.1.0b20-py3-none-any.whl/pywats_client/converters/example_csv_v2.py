"""
Example Converter - CSV to WATS Report (New Architecture)

This is an example converter that demonstrates the new FileConverter
architecture. This converter reads CSV files containing test results
and converts them to WATS reports.

CSV Format Expected:
    serial_number,part_number,station,result,test_name,value,unit,status
    SN001,PN-123,Station1,Pass,Voltage Test,5.2,V,P
    SN001,PN-123,Station1,Pass,Current Test,1.1,A,P
"""

import csv
from datetime import datetime
from typing import Dict, Any, List

from pywats_client.converters import (
    FileConverter,
    ConverterSource,
    ConverterResult,
    ValidationResult,
    PostProcessAction,
    ArgumentDefinition,
    ArgumentType,
)
from pywats_client.converters.context import ConverterContext


class CSVTestConverter(FileConverter):
    """
    Converts CSV test result files to WATS reports.
    
    This example demonstrates:
    - File pattern matching for .csv files
    - Content-based validation for confidence scoring
    - Configurable arguments (delimiter, encoding)
    - Proper conversion with error handling
    """
    
    @property
    def name(self) -> str:
        return "CSV Test Results Converter"
    
    @property
    def description(self) -> str:
        return "Converts CSV files containing test results to WATS UUT reports"
    
    @property
    def version(self) -> str:
        return "2.0.0"
    
    @property
    def author(self) -> str:
        return "pyWATS Team"
    
    @property
    def file_patterns(self) -> List[str]:
        """Only process .csv files"""
        return ["*.csv"]
    
    @property
    def arguments_schema(self) -> Dict[str, ArgumentDefinition]:
        """Define configurable arguments for GUI"""
        return {
            "delimiter": ArgumentDefinition(
                arg_type=ArgumentType.STRING,
                default=",",
                description="CSV field delimiter"
            ),
            "encoding": ArgumentDefinition(
                arg_type=ArgumentType.CHOICE,
                default="utf-8",
                choices=["utf-8", "utf-16", "latin-1", "cp1252"],
                description="File encoding"
            ),
            "skip_empty_rows": ArgumentDefinition(
                arg_type=ArgumentType.BOOLEAN,
                default=True,
                description="Skip rows with empty values"
            ),
        }
    
    def validate(
        self, 
        source: ConverterSource, 
        context: ConverterContext
    ) -> ValidationResult:
        """
        Validate the CSV file and rate confidence.
        
        High confidence if:
        - File has expected column headers
        - At least one data row exists
        
        Low confidence if:
        - Just a .csv extension match
        """
        if source.path is None:
            return ValidationResult.no_match("No file path provided")
        
        try:
            encoding = context.get_argument("encoding", "utf-8")
            file_path = source.path
            
            with open(file_path, 'r', encoding=encoding) as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames or []
                
                # Check for required headers
                has_serial = "serial_number" in headers or "sn" in headers
                has_part = "part_number" in headers or "pn" in headers
                has_test_name = "test_name" in headers or "name" in headers
                
                # Try to read at least one data row
                try:
                    first_row = next(reader)
                    has_data = True
                    
                    # Try to detect part number from first row
                    detected_part = first_row.get("part_number") or first_row.get("pn")
                    detected_serial = first_row.get("serial_number") or first_row.get("sn")
                except StopIteration:
                    has_data = False
                    detected_part = None
                    detected_serial = None
            
            # Score based on what we found
            if has_serial and has_part and has_test_name and has_data:
                return ValidationResult.perfect_match(
                    message="Found expected CSV headers and data",
                    detected_part_number=detected_part,
                    detected_serial_number=detected_serial,
                )
            elif (has_serial or has_part) and has_data:
                return ValidationResult.good_match(
                    confidence=0.7,
                    message="Found some expected headers",
                    detected_part_number=detected_part,
                    detected_serial_number=detected_serial,
                )
            elif has_data:
                return ValidationResult.pattern_match(
                    message="CSV file but missing expected headers"
                )
            else:
                return ValidationResult.no_match("CSV file is empty")
                
        except Exception as e:
            return ValidationResult.no_match(f"Cannot read CSV: {e}")
    
    def convert(
        self, 
        source: ConverterSource, 
        context: ConverterContext
    ) -> ConverterResult:
        """
        Convert a CSV file to WATS report format.
        
        Args:
            source: The CSV file to convert
            context: Converter context with arguments and API client
            
        Returns:
            ConverterResult with the converted report or error
        """
        if source.path is None:
            return ConverterResult.failed_result(error="No file path provided")
        
        try:
            # Get configured arguments
            delimiter = context.get_argument("delimiter", ",")
            encoding = context.get_argument("encoding", "utf-8")
            skip_empty = context.get_argument("skip_empty_rows", True)
            file_path = source.path
            
            # Read CSV content
            with open(file_path, 'r', encoding=encoding) as f:
                reader = csv.DictReader(f, delimiter=delimiter)
                rows = list(reader)
            
            if not rows:
                return ConverterResult.failed_result(
                    error="CSV file is empty or has no data rows"
                )
            
            # Filter empty rows if configured
            if skip_empty:
                rows = [r for r in rows if any(r.values())]
            
            # Get common fields from first row
            first_row = rows[0]
            
            # Build the WATS report
            report: Dict[str, Any] = {
                "type": "Test",
                "pn": first_row.get("part_number", first_row.get("pn", "UNKNOWN")),
                "sn": first_row.get("serial_number", first_row.get("sn", "UNKNOWN")),
                "result": self._determine_overall_result(rows),
                "start": datetime.now().isoformat(),
                "root": {
                    "status": self._determine_overall_result(rows),
                    "stepType": "SequenceCall",
                    "group": "Main",
                    "steps": []
                }
            }
            
            # Add optional fields if present
            if "station" in first_row:
                report["machineName"] = first_row["station"]
            elif context.station_name:
                report["machineName"] = context.station_name
            
            if "process" in first_row:
                report["processCode"] = first_row["process"]
            
            # Convert each row to a test step
            for row in rows:
                step = self._row_to_step(row)
                report["root"]["steps"].append(step)
            
            return ConverterResult.success_result(
                report=report,
                post_action=PostProcessAction.MOVE,
                metadata={
                    "rows_processed": len(rows),
                    "source_file": source.primary_name,
                }
            )
            
        except UnicodeDecodeError as e:
            return ConverterResult.failed_result(
                error=f"Encoding error: {e}. Try a different encoding."
            )
        except Exception as e:
            return ConverterResult.failed_result(error=str(e))
    
    def _determine_overall_result(self, rows: list) -> str:
        """Determine overall test result from all rows"""
        for row in rows:
            status = row.get("status", row.get("result", "")).upper()
            if status in ["F", "FAIL", "FAILED"]:
                return "F"
        return "P"
    
    def _row_to_step(self, row: dict) -> dict:
        """Convert a CSV row to a WATS test step"""
        status = row.get("status", row.get("result", "P")).upper()
        if status in ["P", "PASS", "PASSED"]:
            status = "P"
        elif status in ["F", "FAIL", "FAILED"]:
            status = "F"
        else:
            status = "D"  # Done/skipped
        
        step: Dict[str, Any] = {
            "stepType": "NumericLimitTest",
            "name": row.get("test_name", row.get("name", "Test")),
            "status": status,
            "group": row.get("group", "Tests")
        }
        
        # Add numeric value if present
        if "value" in row:
            try:
                step["numericMeas"] = [{
                    "name": row.get("test_name", row.get("name", "Measurement")),
                    "status": status,
                    "value": float(row["value"]),
                    "unit": row.get("unit", ""),
                }]
                
                # Add limits if present
                if "low_limit" in row:
                    step["numericMeas"][0]["lowLimit"] = float(row["low_limit"])
                if "high_limit" in row:
                    step["numericMeas"][0]["highLimit"] = float(row["high_limit"])
                    
            except ValueError:
                # If value is not numeric, treat as string
                step["stepType"] = "StringValueTest"
                step["stringMeas"] = [{
                    "name": row.get("test_name", row.get("name", "Measurement")),
                    "status": status,
                    "value": row["value"],
                }]
        
        return step
