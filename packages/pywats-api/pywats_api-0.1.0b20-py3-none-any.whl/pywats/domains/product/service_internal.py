"""Product service - internal API business logic layer.

⚠️ INTERNAL API - SUBJECT TO CHANGE ⚠️

Uses internal WATS API endpoints that are not publicly documented.
These methods may change or be removed without notice.

BOX BUILD TEMPLATE OVERVIEW
===========================

The Box Build Template functionality defines WHAT subunits are required to build 
a parent product. This is a PRODUCT-LEVEL definition (design-time), not production.

Key Distinction:
- Box Build Template (this module): Defines required subunits (WHAT is needed)
- Unit Assembly (production domain): Attaches actual units (WHO gets attached)

Example:
    # Define the template (Product domain)
    template = api.product_internal.get_box_build("CONTROLLER", "A")
    template.add_subunit("POWER-SUPPLY", "A", quantity=1)
    template.add_subunit("SENSOR-BOARD", "A", quantity=2)
    template.save()
    
    # Later, during production (Production domain)
    api.production.add_child_to_assembly("CTRL-001", "CONTROLLER", "PSU-456", "POWER-SUPPLY")
    api.production.add_child_to_assembly("CTRL-001", "CONTROLLER", "SNS-789", "SENSOR-BOARD")
    
See Also:
    - BoxBuildTemplate: Builder class for managing templates
    - ProductionService.add_child_to_assembly(): Attach actual units
    - ProductionService.verify_assembly(): Verify units match template
"""
import logging
from typing import List, Optional, Dict, Any
from uuid import UUID

logger = logging.getLogger(__name__)

from .repository import ProductRepository
from .repository_internal import ProductRepositoryInternal
from .models import (
    Product, ProductRevision, ProductRevisionRelation, 
    BomItem, ProductCategory
)
from .box_build import BoxBuildTemplate


class ProductServiceInternal:
    """
    Product business logic layer using internal API.
    
    ⚠️ INTERNAL API - SUBJECT TO CHANGE ⚠️
    
    Provides extended operations including:
    - Box build template management
    - BOM operations
    - Product categories
    """
    
    def __init__(
        self, 
        repository: ProductRepository,
        repository_internal: ProductRepositoryInternal
    ):
        """
        Initialize service with repositories.
        
        Args:
            repository: ProductRepository for public API
            repository_internal: ProductRepositoryInternal for internal API
        """
        self._repository = repository
        self._repo_internal = repository_internal
    
    # =========================================================================
    # Product/Revision Lookup (uses public API)
    # =========================================================================
    
    def get_product(self, part_number: str) -> Optional[Product]:
        """
        Get a product by part number.
        
        Args:
            part_number: The product part number
            
        Returns:
            Product or None if not found
        """
        return self._repository.get_by_part_number(part_number)
    
    def get_revision(self, part_number: str, revision: str) -> Optional[ProductRevision]:
        """
        Get a specific product revision.
        
        Args:
            part_number: The product part number
            revision: The revision identifier
            
        Returns:
            ProductRevision or None if not found
        """
        # Get the product which includes revisions
        product = self.get_product(part_number)
        if not product:
            return None
        
        # Find the matching revision
        for rev in product.revisions:
            if rev.revision == revision:
                # Ensure part_number is set
                rev.part_number = part_number
                return rev
        
        return None
    
    # =========================================================================
    # Box Build Templates (Product-Level Definitions)
    # =========================================================================
    #
    # These methods manage box build TEMPLATES - the design-time definition
    # of what subunits are required to build a product.
    #
    # To attach ACTUAL units during production, use:
    #   api.production.add_child_to_assembly()
    #
    # =========================================================================
    
    def get_box_build(self, part_number: str, revision: str) -> BoxBuildTemplate:
        """
        Get or create a box build template for a product revision.
        
        ⚠️ INTERNAL API
        
        A box build template defines WHAT subunits are required to build a product.
        This is a PRODUCT-LEVEL definition - it does not create production units.
        
        Use the returned BoxBuildTemplate to add/remove subunits, then call
        save() to persist changes to the server.
        
        Args:
            part_number: Parent product part number
            revision: Parent product revision
            
        Returns:
            BoxBuildTemplate for managing subunits
            
        Raises:
            ValueError: If product revision not found
            
        Example:
            # Define what subunits a product needs (Product domain)
            template = api.product_internal.get_box_build("MAIN-BOARD", "A")
            template.add_subunit("PCBA-001", "A", quantity=2)
            template.add_subunit("PSU-100", "B", quantity=1)
            template.save()
            
            # Context manager (auto-save)
            with api.product_internal.get_box_build("MAIN-BOARD", "A") as bb:
                bb.add_subunit("PCBA-001", "A", quantity=2)
                bb.add_subunit("PSU-100", "B")
        """
        # Get the parent revision
        parent_revision = self.get_revision(part_number, revision)
        if not parent_revision:
            raise ValueError(f"Product revision not found: {part_number}/{revision}")
        
        # Load existing relations
        relations = self._load_box_build_relations(part_number, revision)
        
        return BoxBuildTemplate(
            parent_revision=parent_revision,
            service=self,
            existing_relations=relations
        )
    
    def _load_box_build_relations(
        self, 
        part_number: str, 
        revision: str
    ) -> List[ProductRevisionRelation]:
        """
        Load existing box build relations from server.
        
        ⚠️ INTERNAL API
        
        Uses GetProductInfo which returns the full hierarchy including
        all child relations with their ProductRevisionRelationId.
        
        Args:
            part_number: Product part number
            revision: Product revision
            
        Returns:
            List of ProductRevisionRelation
        """
        hierarchy = self._repo_internal.get_product_hierarchy(part_number, revision)
        if not hierarchy:
            return []
        
        # Extract child relations (hlevel > 0 with ProductRevisionRelationId)
        relations = []
        for item in hierarchy:
            if item.get("hlevel", 0) > 0 and item.get("ProductRevisionRelationId"):
                try:
                    # Map hierarchy fields to ProductRevisionRelation fields
                    # Note: Hierarchy uses PartNumber/Revision, model expects ChildPartNumber/ChildRevision
                    rel_data = {
                        "ProductRevisionRelationId": item.get("ProductRevisionRelationId"),
                        "ParentProductRevisionId": item.get("ParentProductRevisionId"),
                        "ProductRevisionId": item.get("ProductRevisionId"),  # Child revision ID
                        "Quantity": item.get("Quantity", 1),
                        "RevisionMask": item.get("RevisionMask"),
                        # Map PartNumber/Revision to ChildPartNumber/ChildRevision
                        "ChildPartNumber": item.get("PartNumber"),
                        "ChildRevision": item.get("Revision"),
                    }
                    relations.append(ProductRevisionRelation.model_validate(rel_data))
                except Exception as e:
                    logger.debug(f"Skipping invalid product revision relation: {e}")
        
        return relations
    
    def get_box_build_subunits(
        self, 
        part_number: str, 
        revision: str
    ) -> List[ProductRevisionRelation]:
        """
        Get subunits for a box build (read-only).
        
        ⚠️ INTERNAL API
        
        Args:
            part_number: Parent product part number
            revision: Parent product revision
            
        Returns:
            List of ProductRevisionRelation representing subunits
        """
        return self._load_box_build_relations(part_number, revision)
    
    # =========================================================================
    # BOM Operations
    # =========================================================================
    
    def get_bom(self, part_number: str, revision: str) -> List[BomItem]:
        """
        Get BOM (Bill of Materials) for a product revision.
        
        ⚠️ INTERNAL API
        
        Args:
            part_number: Product part number
            revision: Product revision
            
        Returns:
            List of BomItem objects
        """
        return self._repo_internal.get_bom(part_number, revision)
    
    def upload_bom(
        self, 
        part_number: str, 
        revision: str,
        bom_items: List[BomItem]
    ) -> bool:
        """
        Upload/update BOM for a product revision.
        
        ⚠️ INTERNAL API
        
        Args:
            part_number: Product part number
            revision: Product revision
            bom_items: List of BomItem objects
            
        Returns:
            True if successful
        """
        # Get the product revision to get its ID
        rev = self.get_revision(part_number, revision)
        if not rev or not rev.product_revision_id:
            raise ValueError(f"Product revision not found: {part_number}/{revision}")
        
        # Set the product revision ID on all items
        items_data = []
        for item in bom_items:
            item_dict = item.model_dump(by_alias=True, exclude_none=True)
            item_dict["productRevisionId"] = str(rev.product_revision_id)
            items_data.append(item_dict)
        
        return self._repo_internal.upload_bom(part_number, revision, items_data)
    
    def upload_bom_from_dict(
        self,
        part_number: str,
        revision: str,
        bom_data: List[Dict[str, Any]]
    ) -> bool:
        """
        Upload BOM from dictionary data.
        
        ⚠️ INTERNAL API
        
        Args:
            part_number: Product part number
            revision: Product revision
            bom_data: List of BOM item dictionaries
            
        Returns:
            True if successful
        """
        # Get the product revision to get its ID
        rev = self.get_revision(part_number, revision)
        if not rev or not rev.product_revision_id:
            raise ValueError(f"Product revision not found: {part_number}/{revision}")
        
        # Set the product revision ID on all items
        for item in bom_data:
            item["productRevisionId"] = str(rev.product_revision_id)
        
        return self._repo_internal.upload_bom(part_number, revision, bom_data)
    
    # =========================================================================
    # Product Categories
    # =========================================================================
    
    def get_categories(self) -> List[Dict[str, Any]]:
        """
        Get all product categories.
        
        ⚠️ INTERNAL API
        
        Returns:
            List of category dictionaries
        """
        return self._repo_internal.get_categories()
    
    def save_categories(self, categories: List[Dict[str, Any]]) -> bool:
        """
        Save product categories.
        
        ⚠️ INTERNAL API
        
        Args:
            categories: List of category dictionaries
            
        Returns:
            True if successful
        """
        return self._repo_internal.save_categories(categories)
