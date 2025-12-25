"""Product domain.

Provides models, services, and repository for product management.
"""
from .models import (
    Product, 
    ProductRevision, 
    ProductView, 
    ProductGroup,
    ProductCategory,
    ProductRevisionRelation,
    BomItem,
)
from .enums import ProductState
from .service import ProductService
from .repository import ProductRepository
from .box_build import BoxBuildTemplate

# Internal API (⚠️ subject to change)
from .repository_internal import ProductRepositoryInternal
from .service_internal import ProductServiceInternal

__all__ = [
    # Models
    "Product",
    "ProductRevision",
    "ProductView",
    "ProductGroup",
    "ProductCategory",
    "ProductRevisionRelation",
    "BomItem",
    # Box Build
    "BoxBuildTemplate",
    # Enums
    "ProductState",
    # Service & Repository (Public)
    "ProductService",
    "ProductRepository",
    # Internal API (⚠️ subject to change)
    "ProductRepositoryInternal",
    "ProductServiceInternal",
]
