"""Production domain.

Provides models, services, and repository for production unit management.
"""
from .models import (
    Unit, UnitChange, ProductionBatch, SerialNumberType,
    UnitVerification, UnitVerificationGrade, UnitPhase
)
from .enums import SerialNumberIdentifier, UnitPhaseFlag
from .service import ProductionService
from .repository import ProductionRepository
from .service_internal import ProductionServiceInternal
from .repository_internal import ProductionRepositoryInternal

# Rebuild Unit model to resolve forward references to Product/ProductRevision
from ..product.models import Product, ProductRevision
Unit.model_rebuild()

__all__ = [
    # Models
    "Unit",
    "UnitChange",
    "UnitPhase",
    "ProductionBatch",
    "SerialNumberType",
    "UnitVerification",
    "UnitVerificationGrade",
    # Enums
    "SerialNumberIdentifier",
    "UnitPhaseFlag",
    # Service & Repository
    "ProductionService",
    "ProductionRepository",
    # Internal Service & Repository
    "ProductionServiceInternal",
    "ProductionRepositoryInternal",
]
