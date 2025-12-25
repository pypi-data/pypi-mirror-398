"""
Converters Module

Provides base classes for converting test data files into WATS reports.

Converter Types:
    FileConverter: Triggered by file events (most common)
    FolderConverter: Triggered when a folder is ready
    ScheduledConverter: Runs on timer/cron schedule

Quick Start:
    from pywats_client.converters import FileConverter, ConverterResult, PostProcessAction
    
    class MyConverter(FileConverter):
        @property
        def name(self) -> str:
            return "My CSV Converter"
        
        @property
        def file_patterns(self) -> list:
            return ["*.csv"]
        
        def convert(self, source, context):
            # Parse the file and build a report
            with open(source.path, 'r') as f:
                data = f.read()
            
            report = {
                "type": "UUT",
                "partNumber": "PN-001",
                "serialNumber": "SN-001",
                "result": "Passed",
            }
            
            return ConverterResult.success_result(
                report=report,
                post_action=PostProcessAction.MOVE
            )
"""

# Models (enums, data classes)
from .models import (
    # Enums
    SourceType,
    ConverterType,
    ConversionStatus,
    PostProcessAction,
    ArgumentType,
    # Data classes
    FileInfo,
    ConverterSource,
    ValidationResult,
    ConverterResult,
    ArgumentDefinition,
    ConversionRecord,
    FailureRecord,
)

# Base classes
from .file_converter import FileConverter
from .folder_converter import FolderConverter
from .scheduled_converter import ScheduledConverter
from .context import ConverterContext

# Standard converters
from .standard import (
    KitronSeicaXMLConverter,
    TeradyneICTConverter,
    TerradyneSpectrumICTConverter,
    WATSStandardTextConverter,
    WATSStandardJsonConverter,
    WATSStandardXMLConverter,
)

# Legacy support (ConverterBase from base.py)
# Note: ConverterBase is deprecated. Use FileConverter instead.
from .base import ConverterBase
from .base import ConverterResult as LegacyConverterResult

__all__ = [
    # Enums
    "SourceType",
    "ConverterType",
    "ConversionStatus",
    "PostProcessAction",
    "ArgumentType",
    # Data classes
    "FileInfo",
    "ConverterSource",
    "ValidationResult",
    "ConverterResult",
    "ArgumentDefinition",
    "ConversionRecord",
    "FailureRecord",
    # New base classes
    "FileConverter",
    "FolderConverter",
    "ScheduledConverter",
    "ConverterContext",
    # Standard converters
    "KitronSeicaXMLConverter",
    "TeradyneICTConverter",
    "TerradyneSpectrumICTConverter",
    "WATSStandardTextConverter",
    "WATSStandardJsonConverter",
    "WATSStandardXMLConverter",
    # Legacy support
    "ConverterBase",
]
