"""Product domain models - pure data classes."""
from typing import Optional, List
from uuid import UUID
from pydantic import Field, AliasChoices

from ...shared import PyWATSModel, Setting
from .enums import ProductState


class ProductRevision(PyWATSModel):
    """
    Represents a product revision in WATS.

    Attributes:
        revision: Revision name/number (required)
        name: Human readable name
        description: Revision description
        state: Active(1) or Inactive(0)
        product_revision_id: Unique identifier for this revision
        product_id: ID of the product this revision belongs to
        xml_data: XML document with custom key-value pairs
        part_number: Part number (read-only, from parent product)
        tags: JSON formatted xmlData (read-only)
    """
    revision: str = Field(...)
    name: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    state: ProductState = Field(default=ProductState.ACTIVE)
    product_revision_id: Optional[UUID] = Field(
        default=None,
        validation_alias=AliasChoices(
            "productRevisionId", "product_revision_id"
        ),
        serialization_alias="productRevisionId"
    )
    product_id: Optional[UUID] = Field(
        default=None,
        validation_alias=AliasChoices("productId", "product_id"),
        serialization_alias="productId"
    )
    xml_data: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("xmlData", "xml_data"),
        serialization_alias="xmlData"
    )
    part_number: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("partNumber", "part_number"),
        serialization_alias="partNumber"
    )
    tags: List[Setting] = Field(default_factory=list)


class ProductRevisionRelation(PyWATSModel):
    """
    Represents a parent-child relationship between product revisions.
    
    Used for box build templates where a parent product contains subunits.
    For example, a main board (parent) may contain multiple PCBAs (children).

    Attributes:
        relation_id: Unique identifier for this relation (ProductRevisionRelationId)
        parent_product_revision_id: Parent product revision ID
        child_product_revision_id: Child product revision ID (API field: ProductRevisionId)
        quantity: Number of child units required (default 1)
        item_number: Optional item/position number
        child_part_number: Child product part number (read-only)
        child_revision: Child product revision (read-only)
    """
    relation_id: Optional[UUID] = Field(
        default=None,
        validation_alias=AliasChoices(
            "ProductRevisionRelationId", "productRevisionRelationId", 
            "relationId", "relation_id", "RelationId"
        ),
        serialization_alias="ProductRevisionRelationId"
    )
    parent_product_revision_id: UUID = Field(
        ...,
        validation_alias=AliasChoices(
            "ParentProductRevisionId", "parentProductRevisionId", "parent_product_revision_id"
        ),
        serialization_alias="ParentProductRevisionId"
    )
    # Note: The API uses "ProductRevisionId" for the CHILD revision (confusingly named)
    child_product_revision_id: UUID = Field(
        ...,
        validation_alias=AliasChoices(
            "ProductRevisionId", "productRevisionId",
            "childProductRevisionId", "child_product_revision_id", "ChildProductRevisionId"
        ),
        serialization_alias="ProductRevisionId"
    )
    quantity: int = Field(
        default=1,
        validation_alias=AliasChoices("Quantity", "quantity"),
        serialization_alias="Quantity"
    )
    item_number: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("ItemNumber", "itemNumber", "item_number"),
        serialization_alias="ItemNumber"
    )
    # Read-only fields populated by API
    child_part_number: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("ChildPartNumber", "childPartNumber", "child_part_number"),
        serialization_alias="ChildPartNumber"
    )
    child_revision: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("ChildRevision", "childRevision", "child_revision"),
        serialization_alias="ChildRevision"
    )
    revision_mask: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("RevisionMask", "revisionMask", "revision_mask"),
        serialization_alias="RevisionMask",
        description="Comma-separated revision patterns with optional % wildcard (e.g., '1.0,2.%,3.1')"
    )
    
    def matches_revision(self, revision: str) -> bool:
        """
        Check if a revision matches this relation's revision mask.
        
        The revision mask can contain:
        - Exact matches: '1.0' matches only '1.0'
        - Wildcards: '1.%' matches '1.0', '1.1', '1.2a', etc.
        - Multiple values: '1.0,2.0,3.%' matches any of those
        
        Args:
            revision: The revision string to check
            
        Returns:
            True if revision matches the mask, False otherwise
        """
        if not self.revision_mask:
            # No mask - use exact child_revision match
            return self.child_revision == revision
        
        # Split by comma and check each pattern
        patterns = [p.strip() for p in self.revision_mask.split(",")]
        for pattern in patterns:
            if pattern.endswith("%"):
                # Wildcard match - check prefix
                prefix = pattern[:-1]
                if revision.startswith(prefix):
                    return True
            else:
                # Exact match
                if revision == pattern:
                    return True
        
        return False


class BomItem(PyWATSModel):
    """
    Represents a Bill of Materials (BOM) item.
    
    BOM items define the components that make up a product revision.

    Attributes:
        bom_item_id: Unique identifier for this BOM item
        product_revision_id: Product revision this BOM item belongs to
        component_ref: Component reference designator (e.g., "R1", "C12")
        part_number: Component part number
        description: Component description
        quantity: Number of components
        manufacturer: Component manufacturer
        manufacturer_pn: Manufacturer part number
        vendor: Vendor/supplier name
        vendor_pn: Vendor part number
    """
    bom_item_id: Optional[UUID] = Field(
        default=None,
        validation_alias=AliasChoices("bomItemId", "bom_item_id", "BomItemId"),
        serialization_alias="bomItemId"
    )
    product_revision_id: Optional[UUID] = Field(
        default=None,
        validation_alias=AliasChoices(
            "productRevisionId", "product_revision_id", "ProductRevisionId"
        ),
        serialization_alias="productRevisionId"
    )
    component_ref: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("componentRef", "component_ref", "ComponentRef", "compRef"),
        serialization_alias="componentRef"
    )
    part_number: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("partNumber", "part_number", "PartNumber"),
        serialization_alias="partNumber"
    )
    description: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("description", "Description"),
        serialization_alias="description"
    )
    quantity: int = Field(
        default=1,
        validation_alias=AliasChoices("quantity", "Quantity"),
        serialization_alias="quantity"
    )
    manufacturer: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("manufacturer", "Manufacturer"),
        serialization_alias="manufacturer"
    )
    manufacturer_pn: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("manufacturerPn", "manufacturer_pn", "ManufacturerPn"),
        serialization_alias="manufacturerPn"
    )
    vendor: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("vendor", "Vendor"),
        serialization_alias="vendor"
    )
    vendor_pn: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("vendorPn", "vendor_pn", "VendorPn"),
        serialization_alias="vendorPn"
    )


class Product(PyWATSModel):
    """
    Represents a product in WATS.

    Attributes:
        part_number: Part number (required)
        name: Product name
        description: Product description
        non_serial: Flag indicating if product can have units
        state: Active(1) or Inactive(0)
        product_id: Unique product identifier
        xml_data: XML document with custom key-value pairs
        product_category_id: ID of category this product belongs to
        product_category_name: Name of product category (read-only)
        revisions: List of product revisions
        tags: JSON formatted xmlData (read-only)
    """
    part_number: str = Field(
        ...,
        validation_alias=AliasChoices("partNumber", "part_number"),
        serialization_alias="partNumber"
    )
    name: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    non_serial: bool = Field(
        default=False,
        validation_alias=AliasChoices("nonSerial", "non_serial"),
        serialization_alias="nonSerial"
    )
    state: ProductState = Field(default=ProductState.ACTIVE)
    product_id: Optional[UUID] = Field(
        default=None,
        validation_alias=AliasChoices("productId", "product_id"),
        serialization_alias="productId"
    )
    xml_data: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("xmlData", "xml_data"),
        serialization_alias="xmlData"
    )
    product_category_id: Optional[UUID] = Field(
        default=None,
        validation_alias=AliasChoices(
            "productCategoryId", "product_category_id"
        ),
        serialization_alias="productCategoryId"
    )
    product_category_name: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(
            "productCategoryName", "product_category_name"
        ),
        serialization_alias="productCategoryName"
    )
    revisions: List[ProductRevision] = Field(default_factory=list)
    tags: List[Setting] = Field(default_factory=list)


class ProductView(PyWATSModel):
    """
    Simplified product view (used in list views).

    Attributes:
        part_number: Part number (required)
        name: Product name
        category: Category name
        non_serial: Flag indicating if product can have units
        state: Active(1) or Inactive(0)
    """
    part_number: str = Field(
        ...,
        validation_alias=AliasChoices("partNumber", "part_number"),
        serialization_alias="partNumber"
    )
    name: Optional[str] = Field(default=None)
    category: Optional[str] = Field(default=None)
    non_serial: bool = Field(
        default=False,
        validation_alias=AliasChoices("nonSerial", "non_serial"),
        serialization_alias="nonSerial"
    )
    state: ProductState = Field(default=ProductState.ACTIVE)


class ProductGroup(PyWATSModel):
    """
    Represents a product group.

    Attributes:
        product_group_id: Product group ID
        product_group_name: Product group name
        name: Alias for product_group_name (convenience)
    """
    product_group_id: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices(
            "productGroupId", "product_group_id"
        ),
        serialization_alias="productGroupId"
    )
    product_group_name: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(
            "productGroupName", "product_group_name"
        ),
        serialization_alias="productGroupName"
    )
    
    @property
    def name(self) -> Optional[str]:
        """Convenience alias for product_group_name."""
        return self.product_group_name


class ProductCategory(PyWATSModel):
    """
    Represents a product category.

    Attributes:
        category_id: Category ID
        name: Category name
        description: Category description
    """
    category_id: Optional[UUID] = Field(
        default=None,
        validation_alias=AliasChoices("categoryId", "category_id", "CategoryId"),
        serialization_alias="categoryId"
    )
    name: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("name", "Name"),
        serialization_alias="name"
    )
    description: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("description", "Description"),
        serialization_alias="description"
    )
