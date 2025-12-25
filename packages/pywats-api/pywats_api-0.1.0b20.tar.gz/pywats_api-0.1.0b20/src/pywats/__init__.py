"""
pyWATS - Python API for WATS (Web-based Automatic Test System)

A clean, object-oriented Python library for interacting with the WATS server.

Usage:
    from pywats import pyWATS
    
    api = pyWATS(base_url="https://your-wats-server.com", token="your-token")
    
    # Access modules
    products = api.product.get_products()
    product = api.product.get_product("PART-001")
    
    # Use query models
    from pywats.domains.report import WATSFilter
    filter = WATSFilter(part_number="PART-001")
    headers = api.report.query_uut_headers(filter)
    
    # Use report models (WSJF format)
    from pywats.models import UUTReport, UURReport
    report = UUTReport(pn="PART-001", sn="SN-12345", rev="A", ...)
"""

from .pywats import pyWATS
from .exceptions import (
    PyWATSError,
    AuthenticationError,
    NotFoundError,
    ValidationError,
    ServerError,
    ConnectionError
)
from .core.logging import enable_debug_logging
from .core.station import Station, StationRegistry, StationConfig, Purpose
from .core.throttle import configure_throttling, RateLimiter

# Import commonly used models from domains for convenience
from .domains.product import Product, ProductRevision, ProductGroup, ProductView
from .domains.product.enums import ProductState
from .domains.asset import Asset, AssetType, AssetLog
from .domains.asset.enums import AssetState, AssetLogType
from .domains.production import (
    Unit, UnitChange, ProductionBatch, SerialNumberType,
    UnitVerification, UnitVerificationGrade
)
from .domains.rootcause import (
    Ticket, TicketStatus, TicketPriority, TicketView,
    TicketUpdate, TicketUpdateType, TicketAttachment
)
from .domains.report import WATSFilter, ReportHeader, Attachment
from .domains.analytics import (
    YieldData, ProcessInfo, LevelInfo,
    # New typed models for analytics
    TopFailedStep, RepairStatistics, RepairHistoryRecord,
    MeasurementData, AggregatedMeasurement, OeeAnalysisResult,
)

# Common models from shared
from .shared import Setting, PyWATSModel

# Result types for structured error handling (LLM/Agent-friendly)
from .shared import Result, Success, Failure, ErrorCode, failure_from_exception

# Discovery helpers for API exploration (LLM/Agent-friendly)
from .shared import discover

# Comparison operator for step limits (convenient top-level import)
from .domains.report.report_models.uut.steps.comp_operator import CompOp

# UUT/UUR Report models (import separately to avoid name conflicts)
# from pywats.models import UUTReport, UURReport, Step, etc.

__version__ = "0.1.0b20"
__wats_server_version__ = "2025.3.9.824"  # Minimum required WATS server version
__all__ = [
    # Main class
    "pyWATS",
    # Station concept
    "Station",
    "StationRegistry",
    "StationConfig",
    "Purpose",
    # Rate limiting
    "configure_throttling",
    "RateLimiter",
    # Logging utilities
    "enable_debug_logging",
    # Exceptions
    "PyWATSError",
    "AuthenticationError",
    "NotFoundError",
    "ValidationError",
    "ServerError",
    "ConnectionError",
    # Product models
    "Product",
    "ProductRevision",
    "ProductView",
    "ProductState",
    "ProductGroup",
    # Asset models
    "Asset",
    "AssetType",
    "AssetLog",
    "AssetState",
    "AssetLogType",
    # Production models
    "Unit",
    "UnitChange",
    "ProductionBatch",
    "SerialNumberType",
    "UnitVerification",
    "UnitVerificationGrade",
    # RootCause (Ticketing) models
    "Ticket",
    "TicketStatus",
    "TicketPriority",
    "TicketView",
    "TicketUpdate",
    "TicketUpdateType",
    "TicketAttachment",
    # Query/filter models
    "ReportHeader",
    "WATSFilter",
    "Attachment",
    "YieldData",
    "ProcessInfo",
    "LevelInfo",
    # Analytics typed models
    "TopFailedStep",
    "RepairStatistics",
    "RepairHistoryRecord",
    "MeasurementData",
    "AggregatedMeasurement",
    "OeeAnalysisResult",
    # Common models
    "Setting",
    "PyWATSModel",
    # Result types for structured error handling
    "Result",
    "Success",
    "Failure",
    "ErrorCode",
    "failure_from_exception",
    # Discovery helpers
    "discover",
    # Comparison operator for limits
    "CompOp",
]
