"""Report domain.

Provides services and repository for test reports (UUT/UUR).

For creating test reports, see the TestUUT factory class:
    from pywats.tools.test_uut import TestUUT
"""
# Report models (UUT/UUR report structure)
from .report_models import (
    UUTReport,
    UURReport,
    Report,
    MiscInfo,
    Step,
    StepStatus,
    WATSBase,
    ReportInfo,
    AdditionalData,
    BinaryData,
    Asset as ReportAsset,
    AssetStats,
    Chart,
    ChartSeries,
    ChartType,
    SubUnit,
    Attachment as ReportAttachment,
    DeserializationContext,
)
from .report_models.uut.steps.sequence_call import SequenceCall, StepList

# Import query-related models
from .enums import DateGrouping
from .models import WATSFilter, ReportHeader, Attachment

# Import service and repository
from .service import ReportService
from .repository import ReportRepository

__all__ = [
    # Report Models (UUT/UUR)
    "UUTReport",
    "UURReport",
    "Report",
    "SequenceCall",
    "StepList",
    "Step",
    "StepStatus",
    "MiscInfo",
    "WATSBase",
    "ReportInfo",
    "AdditionalData",
    "BinaryData",
    "ReportAsset",
    "AssetStats",
    "Chart",
    "ChartSeries",
    "ChartType",
    "SubUnit",
    "ReportAttachment",
    "DeserializationContext",
    # Query Models
    "WATSFilter",
    "ReportHeader",
    "Attachment",
    # Enums
    "DateGrouping",
    # Service & Repository
    "ReportService",
    "ReportRepository",
]
