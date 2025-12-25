"""
Example Converter - CSV to WATS Report

This is an example converter that demonstrates how to create
a converter for pyWATS Client. This converter reads CSV files
containing test results and converts them to WATS reports.

CSV Format Expected:
    serial_number,part_number,station,result,test_name,value,unit,status
    SN001,PN-123,Station1,Pass,Voltage Test,5.2,V,P
    SN001,PN-123,Station1,Pass,Current Test,1.1,A,P
"""

import csv
from io import TextIOWrapper
from datetime import datetime
from typing import Dict, Any, BinaryIO

from pywats_client.converters import ConverterBase, ConverterResult


class CSVConverter(ConverterBase):
    """
    Converts CSV test result files to WATS reports.
    """
    
    @property
    def name(self) -> str:
        return "CSV Test Results Converter"
    
    @property
    def description(self) -> str:
        return "Converts CSV files containing test results to WATS UUT reports"
    
    @property
    def extensions(self) -> list[str]:
        return [".csv"]
    
    def convert(self, file: BinaryIO, filename: str) -> ConverterResult:
        """
        Convert a CSV file to WATS report format.
        
        Args:
            file: Binary file object
            filename: Original filename
            
        Returns:
            ConverterResult with the converted report or error
        """
        try:
            # Read CSV content
            text_file = TextIOWrapper(file, encoding='utf-8')
            reader = csv.DictReader(text_file)
            
            rows = list(reader)
            if not rows:
                return ConverterResult(
                    success=False,
                    error="CSV file is empty or has no data rows"
                )
            
            # Get common fields from first row
            first_row = rows[0]
            
            # Build the WATS report
            report: Dict[str, Any] = {
                "type": "Test",
                "pn": first_row.get("part_number", "UNKNOWN"),
                "sn": first_row.get("serial_number", "UNKNOWN"),
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
            
            if "process" in first_row:
                report["processCode"] = first_row["process"]
            
            # Convert each row to a test step
            for row in rows:
                step = self._row_to_step(row)
                report["root"]["steps"].append(step)
            
            return ConverterResult(success=True, report=report)
            
        except Exception as e:
            return ConverterResult(success=False, error=str(e))
    
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
            "name": row.get("test_name", "Test"),
            "status": status,
            "group": row.get("group", "Tests")
        }
        
        # Add numeric value if present
        if "value" in row:
            try:
                step["numericMeas"] = [{
                    "name": row.get("test_name", "Measurement"),
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
                    "name": row.get("test_name", "Measurement"),
                    "status": status,
                    "value": row["value"],
                }]
        
        return step
