"""Box Build Template management.

This module manages **product-level** box build definitions (templates).

KEY CONCEPT DISTINCTION:
========================

Box Build Template (Product Domain - THIS MODULE)
-------------------------------------------------
Defines WHAT subunits are REQUIRED to build a parent product.
This is a blueprint/template that specifies:
- Which child products are needed (e.g., PCBA, Power Supply)  
- How many of each (quantity)
- Which revisions are acceptable (revision mask)

This is DESIGN-TIME configuration - it defines the structure of the product,
not specific production units.

Example: "A Controller Module (CTRL-100 rev A) requires:
         - 1x Power Supply (PSU-200, any revision)
         - 2x Sensor Board (SNS-300, revision A or B)"

Unit Assembly (Production Domain - see production.service)
----------------------------------------------------------
Actually BUILDS a specific unit by attaching child UNITS to a parent UNIT.
This happens at RUNTIME during production when real serial numbers are involved.

Example: "Unit CTRL-SN-001 now contains:
         - PSU-SN-456 (Power Supply)
         - SNS-SN-789 (Sensor Board slot 1)
         - SNS-SN-790 (Sensor Board slot 2)"

WORKFLOW:
=========
1. Define box build template (Product Domain):
   api.product_internal.get_box_build("CTRL-100", "A").add_subunit("PSU-200", "A").save()

2. Create production units (Production Domain):
   api.production.create_units([parent_unit, child_units...])

3. Finalize child units before assembly:
   api.production.set_unit_phase(child_serial, child_part, "Finalized")

4. Build assembly (Production Domain):
   api.production.add_child_to_assembly(parent_sn, parent_pn, child_sn, child_pn)

5. Verify assembly matches template:
   api.production.verify_assembly(parent_sn, parent_pn, parent_rev)
"""
from typing import List, Optional, TYPE_CHECKING
from uuid import UUID

from .models import ProductRevision, ProductRevisionRelation

if TYPE_CHECKING:
    from .service_internal import ProductServiceInternal


class BoxBuildTemplate:
    """
    Builder class for managing box build templates (product-level definitions).
    
    A box build template defines the subunits required to build a parent product.
    For example, a controller module may require 2 PCBAs, 1 power supply, etc.
    
    This is a PRODUCT-LEVEL definition - it specifies WHAT is needed to build
    the product, not the actual production units. To attach actual units during
    production, use the Production domain's add_child_to_assembly() method.
    
    This class provides a fluent interface for adding/removing subunits and
    commits all changes to the server when save() is called.
    
    Example:
        # Get or create a box build template
        template = api.product_internal.get_box_build("MAIN-BOARD", "A")
        
        # Add subunits (defines what's needed)
        template.add_subunit("PCBA-001", "A", quantity=2)
        template.add_subunit("PSU-100", "B", quantity=1)
        
        # Remove a subunit
        template.remove_subunit("OLD-PART", "A")
        
        # Save all changes
        template.save()
        
        # Or use context manager for auto-save
        with api.product_internal.get_box_build("MAIN-BOARD", "A") as template:
            template.add_subunit("PCBA-001", "A", quantity=2)
        # Changes saved automatically
        
    See Also:
        - ProductionService.add_child_to_assembly(): Attach actual units
        - ProductionService.verify_assembly(): Verify assembly matches template
    """
    
    def __init__(
        self,
        parent_revision: ProductRevision,
        service: "ProductServiceInternal",
        existing_relations: Optional[List[ProductRevisionRelation]] = None
    ):
        """
        Initialize box build template.
        
        Args:
            parent_revision: The parent product revision
            service: ProductServiceInternal for API operations
            existing_relations: Existing relations loaded from server
        """
        self._parent = parent_revision
        self._service = service
        
        # Track current state
        self._relations: List[ProductRevisionRelation] = list(existing_relations or [])
        
        # Track pending changes
        self._to_add: List[ProductRevisionRelation] = []
        self._to_update: List[ProductRevisionRelation] = []
        self._to_delete: List[UUID] = []
    
    # =========================================================================
    # Properties
    # =========================================================================
    
    @property
    def parent_part_number(self) -> Optional[str]:
        """Get the parent product part number."""
        return self._parent.part_number
    
    @property
    def parent_revision(self) -> str:
        """Get the parent product revision."""
        return self._parent.revision
    
    @property
    def parent_revision_id(self) -> Optional[UUID]:
        """Get the parent product revision ID."""
        return self._parent.product_revision_id
    
    @property
    def subunits(self) -> List[ProductRevisionRelation]:
        """
        Get current subunits (including pending additions, excluding pending deletions).
        
        Returns:
            List of ProductRevisionRelation representing subunits
        """
        # Current relations minus deletions plus additions
        current = [r for r in self._relations if r.relation_id not in self._to_delete]
        return current + self._to_add
    
    @property
    def has_pending_changes(self) -> bool:
        """Check if there are unsaved changes."""
        return bool(self._to_add or self._to_update or self._to_delete)
    
    # =========================================================================
    # Fluent Builder Methods
    # =========================================================================
    
    def add_subunit(
        self,
        part_number: str,
        revision: str,
        quantity: int = 1,
        item_number: Optional[str] = None,
        revision_mask: Optional[str] = None
    ) -> "BoxBuildTemplate":
        """
        Add a subunit to the box build template.
        
        Args:
            part_number: Subunit part number
            revision: Subunit revision (default revision for the subunit)
            quantity: Number of subunits required (default: 1)
            item_number: Optional item/position number
            revision_mask: Optional revision mask pattern for flexible matching.
                          Comma-separated values with optional % wildcard.
                          Examples:
                          - "1.0" - Accept only revision 1.0
                          - "1.%" - Accept any revision starting with "1."
                          - "1.0,2.0,3.%" - Accept 1.0, 2.0, or any 3.x
            
        Returns:
            Self for method chaining
            
        Example:
            # Exact revision
            template.add_subunit("PCBA-001", "1.0", quantity=2)
            
            # Accept any 2.x revision
            template.add_subunit("PSU-100", "2.0", revision_mask="2.%")
            
            # Accept multiple specific revisions
            template.add_subunit("CABLE-01", "A", revision_mask="A,B,C")
        """
        # Get the child revision ID
        child_revision = self._service.get_revision(part_number, revision)
        if not child_revision or not child_revision.product_revision_id:
            raise ValueError(f"Product revision not found: {part_number}/{revision}")
        
        if not self._parent.product_revision_id:
            raise ValueError("Parent product revision ID is not set")
        
        # Check if already exists
        for rel in self.subunits:
            if rel.child_product_revision_id == child_revision.product_revision_id:
                # Update quantity instead of adding duplicate
                return self.update_subunit(
                    part_number, revision, 
                    quantity=quantity, 
                    item_number=item_number,
                    revision_mask=revision_mask
                )
        
        # Create new relation with revision mask
        relation = ProductRevisionRelation(
            parent_product_revision_id=self._parent.product_revision_id,
            child_product_revision_id=child_revision.product_revision_id,
            quantity=quantity,
            item_number=item_number,
            child_part_number=part_number,
            child_revision=revision,
            revision_mask=revision_mask
        )
        self._to_add.append(relation)
        
        return self
    
    def update_subunit(
        self,
        part_number: str,
        revision: str,
        quantity: Optional[int] = None,
        item_number: Optional[str] = None,
        revision_mask: Optional[str] = None
    ) -> "BoxBuildTemplate":
        """
        Update an existing subunit in the box build template.
        
        Args:
            part_number: Subunit part number
            revision: Subunit revision
            quantity: New quantity (if provided)
            item_number: New item number (if provided)
            revision_mask: New revision mask pattern (if provided)
            
        Returns:
            Self for method chaining
        """
        # Find existing relation
        for rel in self._relations:
            if rel.child_part_number == part_number and rel.child_revision == revision:
                if quantity is not None:
                    rel.quantity = quantity
                if item_number is not None:
                    rel.item_number = item_number
                if revision_mask is not None:
                    rel.revision_mask = revision_mask
                if rel not in self._to_update:
                    self._to_update.append(rel)
                return self
        
        # Check pending additions
        for rel in self._to_add:
            if rel.child_part_number == part_number and rel.child_revision == revision:
                if quantity is not None:
                    rel.quantity = quantity
                if item_number is not None:
                    rel.item_number = item_number
                if revision_mask is not None:
                    rel.revision_mask = revision_mask
                return self
        
        raise ValueError(f"Subunit not found: {part_number}/{revision}")
    
    def remove_subunit(self, part_number: str, revision: str) -> "BoxBuildTemplate":
        """
        Remove a subunit from the box build template.
        
        Args:
            part_number: Subunit part number
            revision: Subunit revision
            
        Returns:
            Self for method chaining
        """
        # Check existing relations
        for rel in self._relations:
            if rel.child_part_number == part_number and rel.child_revision == revision:
                if rel.relation_id:
                    self._to_delete.append(rel.relation_id)
                # Remove from update list if present
                if rel in self._to_update:
                    self._to_update.remove(rel)
                return self
        
        # Check pending additions
        for rel in self._to_add:
            if rel.child_part_number == part_number and rel.child_revision == revision:
                self._to_add.remove(rel)
                return self
        
        raise ValueError(f"Subunit not found: {part_number}/{revision}")
    
    def clear_all(self) -> "BoxBuildTemplate":
        """
        Mark all subunits for removal.
        
        Returns:
            Self for method chaining
        """
        for rel in self._relations:
            if rel.relation_id:
                self._to_delete.append(rel.relation_id)
        self._to_add.clear()
        self._to_update.clear()
        return self
    
    def set_quantity(self, part_number: str, revision: str, quantity: int) -> "BoxBuildTemplate":
        """
        Set the quantity for a subunit.
        
        Args:
            part_number: Subunit part number
            revision: Subunit revision
            quantity: New quantity
            
        Returns:
            Self for method chaining
        """
        return self.update_subunit(part_number, revision, quantity=quantity)
    
    # =========================================================================
    # Save/Commit Operations
    # =========================================================================
    
    def save(self) -> "BoxBuildTemplate":
        """
        Save all pending changes to the server.
        
        Performs all additions, updates, and deletions in order.
        
        Returns:
            Self for method chaining
        """
        # Process deletions first
        for relation_id in self._to_delete:
            self._service._repo_internal.delete_revision_relation(relation_id)
        
        # Remove deleted relations from our list
        self._relations = [r for r in self._relations if r.relation_id not in self._to_delete]
        self._to_delete.clear()
        
        # Process updates
        for relation in self._to_update:
            updated = self._service._repo_internal.update_revision_relation(relation)
            if updated:
                # Update our local copy
                idx = next((i for i, r in enumerate(self._relations) if r.relation_id == updated.relation_id), None)
                if idx is not None:
                    self._relations[idx] = updated
        self._to_update.clear()
        
        # Process additions
        for relation in self._to_add:
            created = self._service._repo_internal.create_revision_relation(
                parent_revision_id=relation.parent_product_revision_id,
                child_revision_id=relation.child_product_revision_id,
                quantity=relation.quantity,
                item_number=relation.item_number,
                revision_mask=relation.revision_mask
            )
            if created:
                self._relations.append(created)
        self._to_add.clear()
        
        return self
    
    def discard(self) -> "BoxBuildTemplate":
        """
        Discard all pending changes.
        
        Returns:
            Self for method chaining
        """
        self._to_add.clear()
        self._to_update.clear()
        self._to_delete.clear()
        return self
    
    def reload(self) -> "BoxBuildTemplate":
        """
        Reload relations from server, discarding pending changes.
        
        Returns:
            Self for method chaining
        """
        self.discard()
        self._relations = self._service._load_box_build_relations(
            self._parent.part_number or "",
            self._parent.revision
        )
        return self
    
    # =========================================================================
    # Validation Helpers
    # =========================================================================
    
    def validate_subunit(self, part_number: str, revision: str) -> bool:
        """
        Check if a specific subunit revision is valid for this box build.
        
        This checks if the part number exists in the template and if the
        provided revision matches the revision mask (if defined).
        
        Args:
            part_number: The part number to validate
            revision: The revision to validate
            
        Returns:
            True if the subunit/revision combination is valid
            
        Example:
            # Template has PSU-100 with revision_mask="2.%"
            template.validate_subunit("PSU-100", "2.0")  # True
            template.validate_subunit("PSU-100", "2.5")  # True
            template.validate_subunit("PSU-100", "3.0")  # False
        """
        for rel in self.subunits:
            if rel.child_part_number == part_number:
                return rel.matches_revision(revision)
        return False
    
    def get_matching_subunits(self, part_number: str) -> List[ProductRevisionRelation]:
        """
        Get all subunit definitions for a given part number.
        
        Args:
            part_number: The part number to search for
            
        Returns:
            List of matching ProductRevisionRelation objects
        """
        return [rel for rel in self.subunits if rel.child_part_number == part_number]
    
    def get_required_parts(self) -> List[dict]:
        """
        Get a summary of all required parts for this box build.
        
        Returns:
            List of dicts with part_number, default_revision, quantity, revision_mask
        """
        return [
            {
                "part_number": rel.child_part_number,
                "default_revision": rel.child_revision,
                "quantity": rel.quantity,
                "revision_mask": rel.revision_mask,
                "item_number": rel.item_number
            }
            for rel in self.subunits
        ]
    
    # =========================================================================
    # Context Manager Support
    # =========================================================================
    
    def __enter__(self) -> "BoxBuildTemplate":
        """Enter context manager."""
        return self
    
    def __exit__(
        self, 
        exc_type: Optional[type], 
        exc_val: Optional[BaseException], 
        exc_tb: Optional[object]
    ) -> None:
        """Exit context manager - auto-save if no exception."""
        if exc_type is None and self.has_pending_changes:
            self.save()
    
    # =========================================================================
    # String Representation
    # =========================================================================
    
    def __repr__(self) -> str:
        return (
            f"BoxBuildTemplate(parent='{self.parent_part_number}/{self.parent_revision}', "
            f"subunits={len(self.subunits)}, pending_changes={self.has_pending_changes})"
        )
    
    def __str__(self) -> str:
        lines = [f"Box Build: {self.parent_part_number}/{self.parent_revision}"]
        lines.append(f"Subunits ({len(self.subunits)}):")
        for sub in self.subunits:
            mask_info = f" [mask: {sub.revision_mask}]" if sub.revision_mask else ""
            lines.append(f"  - {sub.child_part_number}/{sub.child_revision} x{sub.quantity}{mask_info}")
        if self.has_pending_changes:
            lines.append(f"Pending: +{len(self._to_add)} ~{len(self._to_update)} -{len(self._to_delete)}")
        return "\n".join(lines)
