"""Analytics domain module.

Provides statistics, KPIs, yield analysis, and dashboard data services.

BACKEND API MAPPING
-------------------
This module maps to the WATS backend '/api/App/*' endpoints.
We chose 'analytics' as the Python module name because it better describes
the functionality (yield analysis, KPIs, statistics, OEE) while 'App' is the
legacy backend controller name.

All API calls in this module target /api/App/* endpoints:
- GET/POST /api/App/DynamicYield
- GET/POST /api/App/DynamicRepair  
- GET/POST /api/App/TopFailed
- GET/POST /api/App/TestStepAnalysis
- etc.

This is purely a naming choice for better developer experience.
"""
from .enums import YieldDataType, ProcessType
from .models import (
    YieldData,
    ProcessInfo,
    LevelInfo,
    ProductGroup,
    StepAnalysisRow,
    # New typed models
    TopFailedStep,
    RepairStatistics,
    RepairHistoryRecord,
    MeasurementData,
    AggregatedMeasurement,
    OeeAnalysisResult,
)
from .repository import AnalyticsRepository
from .service import AnalyticsService

# Backward compatibility aliases (deprecated)
AppRepository = AnalyticsRepository
AppService = AnalyticsService

__all__ = [
    # Enums
    "YieldDataType",
    "ProcessType",
    # Models
    "YieldData",
    "ProcessInfo",
    "LevelInfo",
    "ProductGroup",
    "StepAnalysisRow",
    # New typed models
    "TopFailedStep",
    "RepairStatistics",
    "RepairHistoryRecord",
    "MeasurementData",
    "AggregatedMeasurement",
    "OeeAnalysisResult",
    # Repository & Service
    "AnalyticsRepository",
    "AnalyticsService",
    # Deprecated aliases
    "AppRepository",
    "AppService",
]

