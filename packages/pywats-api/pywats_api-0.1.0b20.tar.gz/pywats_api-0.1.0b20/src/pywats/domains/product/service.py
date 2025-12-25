"""Product service - business logic layer.

High-level operations for product management.
"""
from typing import Optional, List, Dict, TYPE_CHECKING, Any
import logging

if TYPE_CHECKING:
    from .models import BomItem

from .models import Product, ProductRevision, ProductGroup, ProductView

logger = logging.getLogger(__name__)
from .enums import ProductState
from .repository import ProductRepository


class ProductService:
    """
    Product business logic.

    Provides high-level operations for managing products, revisions,
    groups, and vendors.
    """

    def __init__(self, repository: ProductRepository):
        """
        Initialize with repository.

        Args:
            repository: ProductRepository for data access
        """
        self._repository = repository

    # =========================================================================
    # Product Operations
    # =========================================================================

    def get_products(self) -> List[ProductView]:
        """
        Get all products as simplified views.

        Returns:
            List of ProductView objects
        """
        products = self._repository.get_all()
        return [
            ProductView(
                part_number=p.part_number,
                name=p.name,
                non_serial=p.non_serial,
                state=p.state
            )
            for p in products
        ]

    def get_products_full(self) -> List[Product]:
        """
        Get all products with full details.

        Returns:
            List of Product objects
        """
        return self._repository.get_all()

    def get_product(self, part_number: str) -> Optional[Product]:
        """
        Get a product by part number.

        Args:
            part_number: The product part number

        Returns:
            Product if found, None otherwise
        """
        return self._repository.get_by_part_number(part_number)

    def create_product(
        self,
        part_number: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        non_serial: bool = False,
        state: ProductState = ProductState.ACTIVE,
        *,
        xml_data: Optional[str] = None,
        product_category_id: Optional[str] = None,
    ) -> Optional[Product]:
        """
        Create a new product.

        Args:
            part_number: Unique part number (required)
            name: Product display name
            description: Product description text
            non_serial: If True, product cannot have serialized units (default: False)
            state: Product state (default: ProductState.ACTIVE). Values: ACTIVE, INACTIVE
            xml_data: Custom XML data for key-value storage
            product_category_id: UUID of product category to assign

        Returns:
            Created Product object, or None on failure
            
        Example:
            >>> product = service.create_product(
            ...     part_number="WIDGET-001",
            ...     name="Widget Model A",
            ...     description="Standard widget for testing",
            ...     state=ProductState.ACTIVE
            ... )
        """
        product = Product(
            part_number=part_number,
            name=name,
            description=description,
            non_serial=non_serial,
            state=state,
            xml_data=xml_data,
            product_category_id=product_category_id,
        )
        result = self._repository.save(product)
        if result:
            logger.info(f"PRODUCT_CREATED: {result.part_number} (name={name}, state={state.name})")
        return result

    def update_product(self, product: Product) -> Optional[Product]:
        """
        Update an existing product.

        Args:
            product: Product object with updated fields

        Returns:
            Updated Product object
        """
        result = self._repository.save(product)
        if result:
            logger.info(f"PRODUCT_UPDATED: {result.part_number}")
        return result

    def bulk_save_products(
        self, products: List[Product]
    ) -> List[Product]:
        """
        Bulk create or update products.

        Args:
            products: List of Product objects

        Returns:
            List of saved Product objects
        """
        results = self._repository.save_bulk(products)
        if results:
            logger.info(f"PRODUCTS_BULK_SAVED: count={len(results)}")
        return results

    def is_active(self, product: Product) -> bool:
        """
        Check if a product is active.

        Args:
            product: Product to check

        Returns:
            True if product is active
        """
        return product.state == ProductState.ACTIVE

    def get_active_products(self) -> List[ProductView]:
        """
        Get all active products.

        Returns:
            List of active ProductView objects
        """
        return [p for p in self.get_products() if p.state == ProductState.ACTIVE]

    # =========================================================================
    # Revision Operations
    # =========================================================================

    def get_revision(
        self, part_number: str, revision: str
    ) -> Optional[ProductRevision]:
        """
        Get a specific product revision.

        Args:
            part_number: The product part number
            revision: The revision identifier

        Returns:
            ProductRevision if found, None otherwise
        """
        return self._repository.get_revision(part_number, revision)

    def get_revisions(self, part_number: str) -> List[ProductRevision]:
        """
        Get all revisions for a product.

        Args:
            part_number: The product part number

        Returns:
            List of ProductRevision objects
        """
        product = self._repository.get_by_part_number(part_number)
        return product.revisions if product else []

    def create_revision(
        self,
        part_number: str,
        revision: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        state: ProductState = ProductState.ACTIVE,
        *,
        xml_data: Optional[str] = None,
    ) -> Optional[ProductRevision]:
        """
        Create a new product revision.

        Args:
            part_number: Product part number (required)
            revision: Revision identifier string (required), e.g., "1.0", "A"
            name: Revision display name
            description: Revision description text
            state: Revision state (default: ProductState.ACTIVE). Values: ACTIVE, INACTIVE
            xml_data: Custom XML data for key-value storage

        Returns:
            Created ProductRevision object, or None if product not found
            
        Example:
            >>> rev = service.create_revision(
            ...     part_number="WIDGET-001",
            ...     revision="1.0",
            ...     name="Initial Release",
            ...     state=ProductState.ACTIVE
            ... )
        """
        # Get product to link revision
        product = self._repository.get_by_part_number(part_number)
        if not product:
            return None

        rev = ProductRevision(
            revision=revision,
            name=name,
            description=description,
            state=state,
            product_id=product.product_id,
            part_number=part_number,
            xml_data=xml_data,
        )
        result = self._repository.save_revision(rev)
        if result:
            logger.info(f"REVISION_CREATED: {part_number}/{revision} (name={name})")
        return result

    def update_revision(
        self, revision: ProductRevision
    ) -> Optional[ProductRevision]:
        """
        Update an existing product revision.

        Args:
            revision: ProductRevision object with updated fields

        Returns:
            Updated ProductRevision object
        """
        result = self._repository.save_revision(revision)
        if result:
            logger.info(f"REVISION_UPDATED: {result.part_number}/{result.revision}")
        return result

    def bulk_save_revisions(
        self, revisions: List[ProductRevision]
    ) -> List[ProductRevision]:
        """
        Bulk create or update revisions.

        Args:
            revisions: List of ProductRevision objects

        Returns:
            List of saved ProductRevision objects
        """
        results = self._repository.save_revisions_bulk(revisions)
        if results:
            logger.info(f"REVISIONS_BULK_SAVED: count={len(results)}")
        return results

    # =========================================================================
    # Bill of Materials
    # =========================================================================

    def get_bom(
        self,
        part_number: str,
        revision: str
    ) -> Optional[str]:
        """
        Get BOM (Bill of Materials) as WSBF XML string.

        Args:
            part_number: Product part number
            revision: Product revision

        Returns:
            WSBF XML string or None if not found
        """
        return self._repository.get_bom(part_number, revision)

    def get_bom_items(
        self,
        part_number: str,
        revision: str
    ) -> List["BomItem"]:
        """
        Get BOM items as parsed BomItem objects.

        Args:
            part_number: Product part number
            revision: Product revision

        Returns:
            List of BomItem objects
        """
        return self._repository.get_bom_items(part_number, revision)

    def update_bom(
        self,
        part_number: str,
        revision: str,
        bom_items: List["BomItem"],
        description: Optional[str] = None
    ) -> bool:
        """
        Update product BOM (Bill of Materials).
        
        Uses the public API which accepts WSBF (WATS Standard BOM Format) XML.

        Args:
            part_number: Product part number
            revision: Product revision
            bom_items: List of BomItem objects
            description: Optional product description

        Returns:
            True if successful
        """
        result = self._repository.update_bom(part_number, revision, bom_items, description)
        if result:
            logger.info(f"BOM_UPDATED: {part_number}/{revision} (items={len(bom_items)})")
        return result

    # =========================================================================
    # Product Groups
    # =========================================================================

    def get_groups(
        self,
        filter_str: Optional[str] = None,
        top: Optional[int] = None
    ) -> List[ProductGroup]:
        """
        Get product groups.

        Args:
            filter_str: OData filter string
            top: Max number of results

        Returns:
            List of ProductGroup objects
        """
        return self._repository.get_groups(filter_str=filter_str, top=top)

    def get_groups_for_product(
        self, part_number: str, revision: str
    ) -> List[ProductGroup]:
        """
        Get product groups for a specific product.

        Args:
            part_number: The product part number
            revision: The revision identifier

        Returns:
            List of ProductGroup objects
        """
        return self._repository.get_groups_for_product(part_number, revision)

    # =========================================================================
    # Tags
    # =========================================================================

    def get_product_tags(self, part_number: str) -> List[Dict[str, str]]:
        """
        Get tags for a product.

        Args:
            part_number: Product part number

        Returns:
            List of tag dictionaries with 'key' and 'value'
        """
        product = self.get_product(part_number)
        if product and product.tags:
            return [{"key": t.key, "value": t.value or ""} for t in product.tags]
        return []

    def set_product_tags(
        self, 
        part_number: str, 
        tags: List[Dict[str, str]]
    ) -> Optional[Product]:
        """
        Set tags for a product (replaces existing tags).

        Args:
            part_number: Product part number
            tags: List of tag dictionaries with 'key' and 'value'

        Returns:
            Updated Product or None if not found
        """
        product = self.get_product(part_number)
        if not product:
            return None
        
        # Convert tags to Setting objects format for XML
        from ...shared import Setting, ChangeType
        product.tags = [
            Setting(key=t["key"], value=t["value"], change=ChangeType.ADD)
            for t in tags
        ]
        return self.update_product(product)

    def add_product_tag(
        self, 
        part_number: str, 
        key: str, 
        value: str
    ) -> Optional[Product]:
        """
        Add a tag to a product.

        Args:
            part_number: Product part number
            key: Tag key
            value: Tag value

        Returns:
            Updated Product or None if not found
        """
        product = self.get_product(part_number)
        if not product:
            return None
        
        from ...shared import Setting, ChangeType
        
        # Check if tag already exists
        for tag in product.tags:
            if tag.key == key:
                tag.value = value
                tag.change = ChangeType.UPDATE
                return self.update_product(product)
        
        # Add new tag
        product.tags.append(Setting(key=key, value=value, change=ChangeType.ADD))
        return self.update_product(product)

    def get_revision_tags(
        self, 
        part_number: str, 
        revision: str
    ) -> List[Dict[str, str]]:
        """
        Get tags for a product revision.

        Args:
            part_number: Product part number
            revision: Revision identifier

        Returns:
            List of tag dictionaries with 'key' and 'value'
        """
        rev = self.get_revision(part_number, revision)
        if rev and rev.tags:
            return [{"key": t.key, "value": t.value or ""} for t in rev.tags]
        return []

    def set_revision_tags(
        self, 
        part_number: str, 
        revision: str,
        tags: List[Dict[str, str]]
    ) -> Optional[ProductRevision]:
        """
        Set tags for a product revision (replaces existing tags).

        Args:
            part_number: Product part number
            revision: Revision identifier
            tags: List of tag dictionaries with 'key' and 'value'

        Returns:
            Updated ProductRevision or None if not found
        """
        rev = self.get_revision(part_number, revision)
        if not rev:
            return None
        
        from ...shared import Setting, ChangeType
        rev.tags = [
            Setting(key=t["key"], value=t["value"], change=ChangeType.ADD)
            for t in tags
        ]
        return self.update_revision(rev)

    def add_revision_tag(
        self, 
        part_number: str, 
        revision: str,
        key: str, 
        value: str
    ) -> Optional[ProductRevision]:
        """
        Add a tag to a product revision.

        Args:
            part_number: Product part number
            revision: Revision identifier
            key: Tag key
            value: Tag value

        Returns:
            Updated ProductRevision or None if not found
        """
        rev = self.get_revision(part_number, revision)
        if not rev:
            return None
        
        from ...shared import Setting, ChangeType
        
        # Check if tag already exists
        for tag in rev.tags:
            if tag.key == key:
                tag.value = value
                tag.change = ChangeType.UPDATE
                return self.update_revision(rev)
        
        # Add new tag
        rev.tags.append(Setting(key=key, value=value, change=ChangeType.ADD))
        return self.update_revision(rev)

    # =========================================================================
    # Vendors
    # =========================================================================

    def get_vendors(self) -> List[Dict[str, Any]]:
        """
        Get all vendors.

        Returns:
            List of vendor dictionaries
        """
        return self._repository.get_vendors()

    def save_vendor(
        self, vendor_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Create or update a vendor.

        Args:
            vendor_data: Vendor data dictionary

        Returns:
            Created/updated vendor data
        """
        return self._repository.save_vendor(vendor_data)

    def delete_vendor(self, vendor_id: str) -> bool:
        """
        Delete a vendor.

        Args:
            vendor_id: The vendor ID

        Returns:
            True if successful
        """
        return self._repository.delete_vendor(vendor_id)
