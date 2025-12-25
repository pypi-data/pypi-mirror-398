"""
Control Panel Manager Tool for WATS Agent.

Comprehensive administrative tool for managing WATS configuration across domains:
- Asset: Equipment, fixtures, calibration, maintenance
- Product: Products, revisions, BOM, box build templates
- Production: Units, phases, assembly relationships
- Software: Packages, releases, deployment
- Process: Test/repair/WIP operations

DESIGN PHILOSOPHY:
This tool is designed for LLM agents to perform administrative tasks.
It uses a unified interface with domain/operation/parameters pattern
to keep the tool count low while maintaining full functionality.

SECURITY NOTE:
Many operations modify production data. The tool validates inputs
but the LLM should confirm destructive operations with the user.
"""

from typing import Any, Dict, List, Optional, TYPE_CHECKING, Literal, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

from .._base import AgentTool, ToolInput
from ...result import AgentResult

if TYPE_CHECKING:
    from pywats import pyWATS


# =============================================================================
# Enums and Constants
# =============================================================================

class ManagementDomain(str, Enum):
    """Domain to manage."""
    ASSET = "asset"
    PRODUCT = "product"
    PRODUCTION = "production"
    SOFTWARE = "software"
    PROCESS = "process"


class OperationType(str, Enum):
    """Type of operation to perform."""
    # Read operations
    LIST = "list"
    GET = "get"
    SEARCH = "search"
    
    # Write operations
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    
    # Domain-specific operations
    SET_STATE = "set_state"
    SET_PHASE = "set_phase"
    ADD_CHILD = "add_child"
    REMOVE_CHILD = "remove_child"
    VERIFY = "verify"
    RELEASE = "release"
    REVOKE = "revoke"


# Domain-specific entity types
DOMAIN_ENTITIES = {
    ManagementDomain.ASSET: ["asset", "asset_type", "calibration", "maintenance"],
    ManagementDomain.PRODUCT: ["product", "revision", "bom", "box_build", "product_group"],
    ManagementDomain.PRODUCTION: ["unit", "batch", "assembly", "phase"],
    ManagementDomain.SOFTWARE: ["package", "package_file", "virtual_folder"],
    ManagementDomain.PROCESS: ["test_operation", "repair_operation", "wip_operation"],
}


# =============================================================================
# Result Model
# =============================================================================

class ControlPanelResult(BaseModel):
    """Result from control panel operation."""
    domain: ManagementDomain
    operation: OperationType
    entity_type: str
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    items: Optional[List[Dict[str, Any]]] = None
    count: int = 0


# =============================================================================
# Tool Input
# =============================================================================

class ControlPanelInput(ToolInput):
    """Input parameters for control panel operations."""
    
    domain: ManagementDomain = Field(
        description="The domain to manage: asset, product, production, software, or process"
    )
    
    operation: OperationType = Field(
        description="The operation to perform: list, get, create, update, delete, or domain-specific operations"
    )
    
    entity_type: Optional[str] = Field(
        default=None,
        description="The type of entity within the domain (e.g., 'asset', 'product', 'package'). "
                    "If not specified, defaults to the primary entity for the domain."
    )
    
    identifier: Optional[str] = Field(
        default=None,
        description="The identifier for get/update/delete operations (ID, serial number, part number, etc.)"
    )
    
    parameters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional parameters for the operation (varies by domain and operation)"
    )
    
    confirm_destructive: bool = Field(
        default=False,
        description="Set to true to confirm destructive operations (delete, revoke, etc.)"
    )


# =============================================================================
# Control Panel Tool
# =============================================================================

class ControlPanelTool(AgentTool):
    """
    Comprehensive administrative tool for WATS configuration.
    
    Manages configuration across all WATS domains through a unified interface.
    Use this tool when you need to:
    
    ASSET MANAGEMENT:
    - List/create/update/delete assets (test equipment, fixtures)
    - Manage asset types (categories of equipment)
    - Track calibration and maintenance schedules
    - Set asset state (OK, Warning, Alarm)
    
    PRODUCT MANAGEMENT:
    - List/create/update products (part numbers)
    - Manage product revisions
    - Configure Bill of Materials (BOM)
    - Set up box build templates (assembly definitions)
    - Manage product groups
    
    PRODUCTION MANAGEMENT:
    - Create/update production units (serialized items)
    - Set unit phase (Under Production, Finalized, Scrapped, etc.)
    - Manage assembly relationships (parent/child units)
    - Verify assembly completeness
    - Manage production batches
    
    SOFTWARE MANAGEMENT:
    - List/create/update software packages
    - Submit packages for review
    - Release or revoke packages
    - Manage package files
    
    PROCESS CONFIGURATION:
    - List test operations (for UUT reports)
    - List repair operations (for UUR reports)
    - List WIP operations (for production tracking)
    - Validate process codes
    
    OPERATION PATTERNS:
    - list: Get all entities of a type
    - get: Get a specific entity by identifier
    - create: Create a new entity (parameters required)
    - update: Modify an existing entity
    - delete: Remove an entity (requires confirm_destructive=true)
    - Domain-specific: set_state, set_phase, release, verify, etc.
    """
    
    name = "control_panel"
    description = """Administrative tool for managing WATS configuration.

Use this tool to manage:
- ASSETS: Equipment, fixtures, calibration tracking
- PRODUCTS: Part numbers, revisions, BOM, box build templates  
- PRODUCTION: Units, phases, assembly relationships
- SOFTWARE: Packages, releases, deployment
- PROCESS: Test/repair/WIP operation definitions

Operations: list, get, create, update, delete, and domain-specific actions.

Examples:
- List all products: domain=product, operation=list
- Create asset: domain=asset, operation=create, parameters={serial_number: "...", type_id: "...", ...}
- Set unit phase: domain=production, operation=set_phase, identifier="SN123", parameters={part_number: "...", phase: "Finalized"}
- Release package: domain=software, operation=release, identifier="package-uuid"

For destructive operations (delete, revoke), set confirm_destructive=true."""

    input_model = ControlPanelInput
    
    def _execute(self, input: ControlPanelInput) -> AgentResult:
        """Execute control panel operation."""
        try:
            # Route to domain handler
            handlers = {
                ManagementDomain.ASSET: self._handle_asset,
                ManagementDomain.PRODUCT: self._handle_product,
                ManagementDomain.PRODUCTION: self._handle_production,
                ManagementDomain.SOFTWARE: self._handle_software,
                ManagementDomain.PROCESS: self._handle_process,
            }
            
            handler = handlers.get(input.domain)
            if not handler:
                return AgentResult.fail(f"Unknown domain: {input.domain}")
            
            result = handler(input)
            
            return AgentResult.ok(
                data=result.model_dump(mode="json"),
                summary=self._build_summary(result)
            )
            
        except Exception as e:
            return AgentResult.fail(f"{type(e).__name__}: {str(e)}")
    
    # =========================================================================
    # Asset Domain Handler
    # =========================================================================
    
    def _handle_asset(self, input: ControlPanelInput) -> ControlPanelResult:
        """Handle asset domain operations."""
        entity_type = input.entity_type or "asset"
        params = input.parameters or {}
        
        if entity_type == "asset":
            return self._handle_asset_entity(input.operation, input.identifier, params, input.confirm_destructive)
        elif entity_type == "asset_type":
            return self._handle_asset_type(input.operation, input.identifier, params)
        else:
            return ControlPanelResult(
                domain=ManagementDomain.ASSET,
                operation=input.operation,
                entity_type=entity_type,
                success=False,
                message=f"Unknown entity type: {entity_type}. Valid types: asset, asset_type"
            )
    
    def _handle_asset_entity(
        self, 
        operation: OperationType, 
        identifier: Optional[str],
        params: Dict[str, Any],
        confirm_destructive: bool
    ) -> ControlPanelResult:
        """Handle asset entity operations."""
        
        if operation == OperationType.LIST:
            assets = self._api.asset.get_assets(
                filter_str=params.get("filter"),
                top=params.get("top", 100)
            )
            items = [self._serialize_asset(a) for a in assets]
            return ControlPanelResult(
                domain=ManagementDomain.ASSET,
                operation=operation,
                entity_type="asset",
                success=True,
                message=f"Found {len(items)} assets",
                items=items,
                count=len(items)
            )
        
        elif operation == OperationType.GET:
            if not identifier:
                return ControlPanelResult(
                    domain=ManagementDomain.ASSET,
                    operation=operation,
                    entity_type="asset",
                    success=False,
                    message="Identifier required for get operation"
                )
            asset = self._api.asset.get_asset(identifier)
            if asset:
                return ControlPanelResult(
                    domain=ManagementDomain.ASSET,
                    operation=operation,
                    entity_type="asset",
                    success=True,
                    message=f"Found asset: {asset.serial_number}",
                    data=self._serialize_asset(asset),
                    count=1
                )
            return ControlPanelResult(
                domain=ManagementDomain.ASSET,
                operation=operation,
                entity_type="asset",
                success=False,
                message=f"Asset not found: {identifier}"
            )
        
        elif operation == OperationType.CREATE:
            required = ["serial_number", "type_id"]
            missing = [r for r in required if r not in params]
            if missing:
                return ControlPanelResult(
                    domain=ManagementDomain.ASSET,
                    operation=operation,
                    entity_type="asset",
                    success=False,
                    message=f"Missing required parameters: {missing}"
                )
            
            asset = self._api.asset.create_asset(**params)
            if asset:
                return ControlPanelResult(
                    domain=ManagementDomain.ASSET,
                    operation=operation,
                    entity_type="asset",
                    success=True,
                    message=f"Created asset: {asset.serial_number}",
                    data=self._serialize_asset(asset),
                    count=1
                )
            return ControlPanelResult(
                domain=ManagementDomain.ASSET,
                operation=operation,
                entity_type="asset",
                success=False,
                message="Failed to create asset"
            )
        
        elif operation == OperationType.DELETE:
            if not confirm_destructive:
                return ControlPanelResult(
                    domain=ManagementDomain.ASSET,
                    operation=operation,
                    entity_type="asset",
                    success=False,
                    message="Destructive operation requires confirm_destructive=true"
                )
            
            success = self._api.asset.delete_asset(
                asset_id=identifier if self._is_uuid(identifier) else None,
                serial_number=identifier if not self._is_uuid(identifier) else None
            )
            return ControlPanelResult(
                domain=ManagementDomain.ASSET,
                operation=operation,
                entity_type="asset",
                success=success,
                message=f"{'Deleted' if success else 'Failed to delete'} asset: {identifier}"
            )
        
        elif operation == OperationType.SET_STATE:
            if not identifier:
                return ControlPanelResult(
                    domain=ManagementDomain.ASSET,
                    operation=operation,
                    entity_type="asset",
                    success=False,
                    message="Identifier required for set_state operation"
                )
            state = params.get("state")
            if not state:
                return ControlPanelResult(
                    domain=ManagementDomain.ASSET,
                    operation=operation,
                    entity_type="asset",
                    success=False,
                    message="State parameter required (OK, Warning, Alarm, etc.)"
                )
            
            from pywats.domains.asset.enums import AssetState
            try:
                state_enum = AssetState[state.upper()] if isinstance(state, str) else AssetState(state)
            except (KeyError, ValueError):
                return ControlPanelResult(
                    domain=ManagementDomain.ASSET,
                    operation=operation,
                    entity_type="asset",
                    success=False,
                    message=f"Invalid state: {state}. Valid: {[s.name for s in AssetState]}"
                )
            
            success = self._api.asset.set_asset_state(
                state=state_enum,
                serial_number=identifier
            )
            return ControlPanelResult(
                domain=ManagementDomain.ASSET,
                operation=operation,
                entity_type="asset",
                success=success,
                message=f"{'Set' if success else 'Failed to set'} asset state to {state}"
            )
        
        return ControlPanelResult(
            domain=ManagementDomain.ASSET,
            operation=operation,
            entity_type="asset",
            success=False,
            message=f"Unsupported operation for asset: {operation}"
        )
    
    def _handle_asset_type(
        self, 
        operation: OperationType, 
        identifier: Optional[str],
        params: Dict[str, Any]
    ) -> ControlPanelResult:
        """Handle asset type operations."""
        
        if operation == OperationType.LIST:
            types = self._api.asset.get_asset_types()
            items = [{"type_id": str(t.type_id), "name": t.name, "description": t.description} for t in types]
            return ControlPanelResult(
                domain=ManagementDomain.ASSET,
                operation=operation,
                entity_type="asset_type",
                success=True,
                message=f"Found {len(items)} asset types",
                items=items,
                count=len(items)
            )
        
        elif operation == OperationType.GET:
            if not identifier:
                return ControlPanelResult(
                    domain=ManagementDomain.ASSET,
                    operation=operation,
                    entity_type="asset_type",
                    success=False,
                    message="Identifier required"
                )
            asset_type = self._api.asset.get_asset_type(identifier)
            if asset_type:
                return ControlPanelResult(
                    domain=ManagementDomain.ASSET,
                    operation=operation,
                    entity_type="asset_type",
                    success=True,
                    message=f"Found asset type: {asset_type.name}",
                    data={"type_id": str(asset_type.type_id), "name": asset_type.name, "description": asset_type.description},
                    count=1
                )
            return ControlPanelResult(
                domain=ManagementDomain.ASSET,
                operation=operation,
                entity_type="asset_type",
                success=False,
                message=f"Asset type not found: {identifier}"
            )
        
        return ControlPanelResult(
            domain=ManagementDomain.ASSET,
            operation=operation,
            entity_type="asset_type",
            success=False,
            message=f"Operation {operation} not supported for asset_type (read-only)"
        )
    
    # =========================================================================
    # Product Domain Handler
    # =========================================================================
    
    def _handle_product(self, input: ControlPanelInput) -> ControlPanelResult:
        """Handle product domain operations."""
        entity_type = input.entity_type or "product"
        params = input.parameters or {}
        
        if entity_type == "product":
            return self._handle_product_entity(input.operation, input.identifier, params, input.confirm_destructive)
        elif entity_type == "revision":
            return self._handle_revision(input.operation, input.identifier, params)
        elif entity_type == "product_group":
            return self._handle_product_group(input.operation, input.identifier, params)
        else:
            return ControlPanelResult(
                domain=ManagementDomain.PRODUCT,
                operation=input.operation,
                entity_type=entity_type,
                success=False,
                message=f"Unknown entity type: {entity_type}. Valid: product, revision, product_group"
            )
    
    def _handle_product_entity(
        self, 
        operation: OperationType, 
        identifier: Optional[str],
        params: Dict[str, Any],
        confirm_destructive: bool
    ) -> ControlPanelResult:
        """Handle product entity operations."""
        
        if operation == OperationType.LIST:
            products = self._api.product.get_products()
            items = [{"part_number": p.part_number, "name": p.name, "state": str(p.state)} for p in products]
            return ControlPanelResult(
                domain=ManagementDomain.PRODUCT,
                operation=operation,
                entity_type="product",
                success=True,
                message=f"Found {len(items)} products",
                items=items,
                count=len(items)
            )
        
        elif operation == OperationType.GET:
            if not identifier:
                return ControlPanelResult(
                    domain=ManagementDomain.PRODUCT,
                    operation=operation,
                    entity_type="product",
                    success=False,
                    message="Part number required"
                )
            product = self._api.product.get_product(identifier)
            if product:
                return ControlPanelResult(
                    domain=ManagementDomain.PRODUCT,
                    operation=operation,
                    entity_type="product",
                    success=True,
                    message=f"Found product: {product.part_number}",
                    data=self._serialize_product(product),
                    count=1
                )
            return ControlPanelResult(
                domain=ManagementDomain.PRODUCT,
                operation=operation,
                entity_type="product",
                success=False,
                message=f"Product not found: {identifier}"
            )
        
        elif operation == OperationType.CREATE:
            if "part_number" not in params:
                return ControlPanelResult(
                    domain=ManagementDomain.PRODUCT,
                    operation=operation,
                    entity_type="product",
                    success=False,
                    message="Missing required parameter: part_number"
                )
            
            product = self._api.product.create_product(**params)
            if product:
                return ControlPanelResult(
                    domain=ManagementDomain.PRODUCT,
                    operation=operation,
                    entity_type="product",
                    success=True,
                    message=f"Created product: {product.part_number}",
                    data=self._serialize_product(product),
                    count=1
                )
            return ControlPanelResult(
                domain=ManagementDomain.PRODUCT,
                operation=operation,
                entity_type="product",
                success=False,
                message="Failed to create product"
            )
        
        return ControlPanelResult(
            domain=ManagementDomain.PRODUCT,
            operation=operation,
            entity_type="product",
            success=False,
            message=f"Unsupported operation for product: {operation}"
        )
    
    def _handle_revision(
        self, 
        operation: OperationType, 
        identifier: Optional[str],
        params: Dict[str, Any]
    ) -> ControlPanelResult:
        """Handle product revision operations."""
        
        if operation == OperationType.LIST:
            part_number = params.get("part_number") or identifier
            if not part_number:
                return ControlPanelResult(
                    domain=ManagementDomain.PRODUCT,
                    operation=operation,
                    entity_type="revision",
                    success=False,
                    message="part_number required to list revisions"
                )
            revisions = self._api.product.get_revisions(part_number)
            items = [{"revision": r.revision, "name": r.name, "state": str(r.state)} for r in revisions]
            return ControlPanelResult(
                domain=ManagementDomain.PRODUCT,
                operation=operation,
                entity_type="revision",
                success=True,
                message=f"Found {len(items)} revisions for {part_number}",
                items=items,
                count=len(items)
            )
        
        elif operation == OperationType.GET:
            part_number = params.get("part_number")
            revision = params.get("revision") or identifier
            if not part_number or not revision:
                return ControlPanelResult(
                    domain=ManagementDomain.PRODUCT,
                    operation=operation,
                    entity_type="revision",
                    success=False,
                    message="part_number and revision required"
                )
            rev = self._api.product.get_revision(part_number, revision)
            if rev:
                return ControlPanelResult(
                    domain=ManagementDomain.PRODUCT,
                    operation=operation,
                    entity_type="revision",
                    success=True,
                    message=f"Found revision: {part_number}/{revision}",
                    data={"part_number": part_number, "revision": rev.revision, "name": rev.name, "state": str(rev.state)},
                    count=1
                )
            return ControlPanelResult(
                domain=ManagementDomain.PRODUCT,
                operation=operation,
                entity_type="revision",
                success=False,
                message=f"Revision not found: {part_number}/{revision}"
            )
        
        elif operation == OperationType.CREATE:
            required = ["part_number", "revision"]
            missing = [r for r in required if r not in params]
            if missing:
                return ControlPanelResult(
                    domain=ManagementDomain.PRODUCT,
                    operation=operation,
                    entity_type="revision",
                    success=False,
                    message=f"Missing required parameters: {missing}"
                )
            
            rev = self._api.product.create_revision(**params)
            if rev:
                return ControlPanelResult(
                    domain=ManagementDomain.PRODUCT,
                    operation=operation,
                    entity_type="revision",
                    success=True,
                    message=f"Created revision: {params['part_number']}/{params['revision']}",
                    data={"revision": rev.revision, "name": rev.name},
                    count=1
                )
            return ControlPanelResult(
                domain=ManagementDomain.PRODUCT,
                operation=operation,
                entity_type="revision",
                success=False,
                message="Failed to create revision"
            )
        
        return ControlPanelResult(
            domain=ManagementDomain.PRODUCT,
            operation=operation,
            entity_type="revision",
            success=False,
            message=f"Unsupported operation for revision: {operation}"
        )
    
    def _handle_product_group(
        self, 
        operation: OperationType, 
        identifier: Optional[str],
        params: Dict[str, Any]
    ) -> ControlPanelResult:
        """Handle product group operations."""
        
        if operation == OperationType.LIST:
            groups = self._api.product.get_groups()
            items = [{"name": g.name, "description": g.description} for g in groups]
            return ControlPanelResult(
                domain=ManagementDomain.PRODUCT,
                operation=operation,
                entity_type="product_group",
                success=True,
                message=f"Found {len(items)} product groups",
                items=items,
                count=len(items)
            )
        
        return ControlPanelResult(
            domain=ManagementDomain.PRODUCT,
            operation=operation,
            entity_type="product_group",
            success=False,
            message=f"Operation {operation} not fully supported for product_group"
        )
    
    # =========================================================================
    # Production Domain Handler
    # =========================================================================
    
    def _handle_production(self, input: ControlPanelInput) -> ControlPanelResult:
        """Handle production domain operations."""
        entity_type = input.entity_type or "unit"
        params = input.parameters or {}
        
        if entity_type == "unit":
            return self._handle_unit(input.operation, input.identifier, params, input.confirm_destructive)
        elif entity_type == "phase":
            return self._handle_phase(input.operation, input.identifier, params)
        elif entity_type == "assembly":
            return self._handle_assembly(input.operation, input.identifier, params)
        else:
            return ControlPanelResult(
                domain=ManagementDomain.PRODUCTION,
                operation=input.operation,
                entity_type=entity_type,
                success=False,
                message=f"Unknown entity type: {entity_type}. Valid: unit, phase, assembly"
            )
    
    def _handle_unit(
        self, 
        operation: OperationType, 
        identifier: Optional[str],
        params: Dict[str, Any],
        confirm_destructive: bool
    ) -> ControlPanelResult:
        """Handle production unit operations."""
        
        if operation == OperationType.GET:
            serial_number = identifier or params.get("serial_number")
            part_number = params.get("part_number")
            if not serial_number or not part_number:
                return ControlPanelResult(
                    domain=ManagementDomain.PRODUCTION,
                    operation=operation,
                    entity_type="unit",
                    success=False,
                    message="serial_number and part_number required"
                )
            unit = self._api.production.get_unit(serial_number, part_number)
            if unit:
                return ControlPanelResult(
                    domain=ManagementDomain.PRODUCTION,
                    operation=operation,
                    entity_type="unit",
                    success=True,
                    message=f"Found unit: {serial_number}",
                    data=self._serialize_unit(unit),
                    count=1
                )
            return ControlPanelResult(
                domain=ManagementDomain.PRODUCTION,
                operation=operation,
                entity_type="unit",
                success=False,
                message=f"Unit not found: {serial_number}/{part_number}"
            )
        
        elif operation == OperationType.CREATE:
            required = ["serial_number", "part_number"]
            missing = [r for r in required if r not in params]
            if missing:
                return ControlPanelResult(
                    domain=ManagementDomain.PRODUCTION,
                    operation=operation,
                    entity_type="unit",
                    success=False,
                    message=f"Missing required parameters: {missing}"
                )
            
            from pywats.domains.production.models import Unit
            unit = Unit(**params)
            results = self._api.production.create_units([unit])
            if results:
                return ControlPanelResult(
                    domain=ManagementDomain.PRODUCTION,
                    operation=operation,
                    entity_type="unit",
                    success=True,
                    message=f"Created unit: {params['serial_number']}",
                    data=self._serialize_unit(results[0]),
                    count=1
                )
            return ControlPanelResult(
                domain=ManagementDomain.PRODUCTION,
                operation=operation,
                entity_type="unit",
                success=False,
                message="Failed to create unit"
            )
        
        elif operation == OperationType.SET_PHASE:
            serial_number = identifier or params.get("serial_number")
            part_number = params.get("part_number")
            phase = params.get("phase")
            comment = params.get("comment")
            
            if not serial_number or not part_number or not phase:
                return ControlPanelResult(
                    domain=ManagementDomain.PRODUCTION,
                    operation=operation,
                    entity_type="unit",
                    success=False,
                    message="serial_number, part_number, and phase required"
                )
            
            success = self._api.production.set_unit_phase(
                serial_number=serial_number,
                part_number=part_number,
                phase=phase,
                comment=comment
            )
            return ControlPanelResult(
                domain=ManagementDomain.PRODUCTION,
                operation=operation,
                entity_type="unit",
                success=success,
                message=f"{'Set' if success else 'Failed to set'} phase to {phase} for {serial_number}"
            )
        
        elif operation == OperationType.VERIFY:
            serial_number = identifier or params.get("serial_number")
            part_number = params.get("part_number")
            revision = params.get("revision")
            
            if not serial_number or not part_number:
                return ControlPanelResult(
                    domain=ManagementDomain.PRODUCTION,
                    operation=operation,
                    entity_type="unit",
                    success=False,
                    message="serial_number and part_number required"
                )
            
            grade = self._api.production.get_unit_grade(serial_number, part_number, revision)
            if grade:
                return ControlPanelResult(
                    domain=ManagementDomain.PRODUCTION,
                    operation=operation,
                    entity_type="unit",
                    success=True,
                    message=f"Unit verification: {grade.grade or 'No grade'}",
                    data={
                        "status": grade.status,
                        "grade": grade.grade,
                        "all_passed_last_run": grade.all_processes_passed_last_run,
                        "all_passed_first_run": grade.all_processes_passed_first_run,
                        "no_repairs": grade.no_repairs,
                    },
                    count=1
                )
            return ControlPanelResult(
                domain=ManagementDomain.PRODUCTION,
                operation=operation,
                entity_type="unit",
                success=False,
                message="No verification rules configured for this product"
            )
        
        return ControlPanelResult(
            domain=ManagementDomain.PRODUCTION,
            operation=operation,
            entity_type="unit",
            success=False,
            message=f"Unsupported operation for unit: {operation}"
        )
    
    def _handle_phase(
        self, 
        operation: OperationType, 
        identifier: Optional[str],
        params: Dict[str, Any]
    ) -> ControlPanelResult:
        """Handle unit phase operations."""
        
        if operation == OperationType.LIST:
            phases = self._api.production.get_phases()
            items = [{"phase_id": p.phase_id, "code": p.code, "name": p.name} for p in phases]
            return ControlPanelResult(
                domain=ManagementDomain.PRODUCTION,
                operation=operation,
                entity_type="phase",
                success=True,
                message=f"Found {len(items)} unit phases",
                items=items,
                count=len(items)
            )
        
        elif operation == OperationType.GET:
            if not identifier:
                return ControlPanelResult(
                    domain=ManagementDomain.PRODUCTION,
                    operation=operation,
                    entity_type="phase",
                    success=False,
                    message="Phase identifier required (ID, code, or name)"
                )
            
            # Try to parse as int first
            try:
                phase_id = int(identifier)
                phase = self._api.production.get_phase(phase_id)
            except ValueError:
                phase = self._api.production.get_phase(identifier)
            
            if phase:
                return ControlPanelResult(
                    domain=ManagementDomain.PRODUCTION,
                    operation=operation,
                    entity_type="phase",
                    success=True,
                    message=f"Found phase: {phase.name}",
                    data={"phase_id": phase.phase_id, "code": phase.code, "name": phase.name},
                    count=1
                )
            return ControlPanelResult(
                domain=ManagementDomain.PRODUCTION,
                operation=operation,
                entity_type="phase",
                success=False,
                message=f"Phase not found: {identifier}"
            )
        
        return ControlPanelResult(
            domain=ManagementDomain.PRODUCTION,
            operation=operation,
            entity_type="phase",
            success=False,
            message=f"Phases are read-only. Use set_phase on unit to change unit phase."
        )
    
    def _handle_assembly(
        self, 
        operation: OperationType, 
        identifier: Optional[str],
        params: Dict[str, Any]
    ) -> ControlPanelResult:
        """Handle assembly operations (parent/child relationships)."""
        
        if operation == OperationType.ADD_CHILD:
            required = ["parent_serial", "parent_part", "child_serial", "child_part"]
            missing = [r for r in required if r not in params]
            if missing:
                return ControlPanelResult(
                    domain=ManagementDomain.PRODUCTION,
                    operation=operation,
                    entity_type="assembly",
                    success=False,
                    message=f"Missing required parameters: {missing}"
                )
            
            success = self._api.production.add_child_to_assembly(
                parent_serial=params["parent_serial"],
                parent_part=params["parent_part"],
                child_serial=params["child_serial"],
                child_part=params["child_part"]
            )
            return ControlPanelResult(
                domain=ManagementDomain.PRODUCTION,
                operation=operation,
                entity_type="assembly",
                success=success,
                message=f"{'Added' if success else 'Failed to add'} {params['child_serial']} to {params['parent_serial']}"
            )
        
        elif operation == OperationType.REMOVE_CHILD:
            required = ["parent_serial", "parent_part", "child_serial", "child_part"]
            missing = [r for r in required if r not in params]
            if missing:
                return ControlPanelResult(
                    domain=ManagementDomain.PRODUCTION,
                    operation=operation,
                    entity_type="assembly",
                    success=False,
                    message=f"Missing required parameters: {missing}"
                )
            
            success = self._api.production.remove_child_from_assembly(
                parent_serial=params["parent_serial"],
                parent_part=params["parent_part"],
                child_serial=params["child_serial"],
                child_part=params["child_part"]
            )
            return ControlPanelResult(
                domain=ManagementDomain.PRODUCTION,
                operation=operation,
                entity_type="assembly",
                success=success,
                message=f"{'Removed' if success else 'Failed to remove'} {params['child_serial']} from {params['parent_serial']}"
            )
        
        elif operation == OperationType.VERIFY:
            required = ["serial_number", "part_number", "revision"]
            missing = [r for r in required if r not in params]
            if missing:
                return ControlPanelResult(
                    domain=ManagementDomain.PRODUCTION,
                    operation=operation,
                    entity_type="assembly",
                    success=False,
                    message=f"Missing required parameters: {missing}"
                )
            
            result = self._api.production.verify_assembly(
                serial_number=params["serial_number"],
                part_number=params["part_number"],
                revision=params["revision"]
            )
            return ControlPanelResult(
                domain=ManagementDomain.PRODUCTION,
                operation=operation,
                entity_type="assembly",
                success=result is not None,
                message="Assembly verification complete" if result else "Assembly verification failed",
                data=result
            )
        
        return ControlPanelResult(
            domain=ManagementDomain.PRODUCTION,
            operation=operation,
            entity_type="assembly",
            success=False,
            message=f"Unsupported assembly operation: {operation}. Use add_child, remove_child, or verify."
        )
    
    # =========================================================================
    # Software Domain Handler
    # =========================================================================
    
    def _handle_software(self, input: ControlPanelInput) -> ControlPanelResult:
        """Handle software domain operations."""
        entity_type = input.entity_type or "package"
        params = input.parameters or {}
        
        if entity_type == "package":
            return self._handle_package(input.operation, input.identifier, params, input.confirm_destructive)
        elif entity_type == "virtual_folder":
            return self._handle_virtual_folder(input.operation)
        else:
            return ControlPanelResult(
                domain=ManagementDomain.SOFTWARE,
                operation=input.operation,
                entity_type=entity_type,
                success=False,
                message=f"Unknown entity type: {entity_type}. Valid: package, virtual_folder"
            )
    
    def _handle_package(
        self, 
        operation: OperationType, 
        identifier: Optional[str],
        params: Dict[str, Any],
        confirm_destructive: bool
    ) -> ControlPanelResult:
        """Handle software package operations."""
        
        if operation == OperationType.LIST:
            packages = self._api.software.get_packages()
            items = [{
                "package_id": str(p.package_id),
                "name": p.name,
                "version": p.version,
                "status": str(p.status) if p.status else None
            } for p in packages]
            return ControlPanelResult(
                domain=ManagementDomain.SOFTWARE,
                operation=operation,
                entity_type="package",
                success=True,
                message=f"Found {len(items)} packages",
                items=items,
                count=len(items)
            )
        
        elif operation == OperationType.GET:
            if not identifier:
                return ControlPanelResult(
                    domain=ManagementDomain.SOFTWARE,
                    operation=operation,
                    entity_type="package",
                    success=False,
                    message="Package ID or name required"
                )
            
            # Try by ID first, then by name
            package = self._api.software.get_package(identifier) if self._is_uuid(identifier) else None
            if not package:
                package = self._api.software.get_package_by_name(identifier)
            
            if package:
                return ControlPanelResult(
                    domain=ManagementDomain.SOFTWARE,
                    operation=operation,
                    entity_type="package",
                    success=True,
                    message=f"Found package: {package.name}",
                    data=self._serialize_package(package),
                    count=1
                )
            return ControlPanelResult(
                domain=ManagementDomain.SOFTWARE,
                operation=operation,
                entity_type="package",
                success=False,
                message=f"Package not found: {identifier}"
            )
        
        elif operation == OperationType.CREATE:
            if "name" not in params:
                return ControlPanelResult(
                    domain=ManagementDomain.SOFTWARE,
                    operation=operation,
                    entity_type="package",
                    success=False,
                    message="Missing required parameter: name"
                )
            
            package = self._api.software.create_package(**params)
            if package:
                return ControlPanelResult(
                    domain=ManagementDomain.SOFTWARE,
                    operation=operation,
                    entity_type="package",
                    success=True,
                    message=f"Created package: {package.name} (version {package.version})",
                    data=self._serialize_package(package),
                    count=1
                )
            return ControlPanelResult(
                domain=ManagementDomain.SOFTWARE,
                operation=operation,
                entity_type="package",
                success=False,
                message="Failed to create package"
            )
        
        elif operation == OperationType.DELETE:
            if not confirm_destructive:
                return ControlPanelResult(
                    domain=ManagementDomain.SOFTWARE,
                    operation=operation,
                    entity_type="package",
                    success=False,
                    message="Destructive operation requires confirm_destructive=true"
                )
            
            if self._is_uuid(identifier):
                success = self._api.software.delete_package(identifier)
            else:
                success = self._api.software.delete_package_by_name(identifier)
            
            return ControlPanelResult(
                domain=ManagementDomain.SOFTWARE,
                operation=operation,
                entity_type="package",
                success=success,
                message=f"{'Deleted' if success else 'Failed to delete'} package: {identifier}"
            )
        
        elif operation == OperationType.RELEASE:
            if not identifier:
                return ControlPanelResult(
                    domain=ManagementDomain.SOFTWARE,
                    operation=operation,
                    entity_type="package",
                    success=False,
                    message="Package ID required"
                )
            
            # First submit for review if draft
            self._api.software.submit_for_review(identifier)
            success = self._api.software.release_package(identifier)
            return ControlPanelResult(
                domain=ManagementDomain.SOFTWARE,
                operation=operation,
                entity_type="package",
                success=success,
                message=f"{'Released' if success else 'Failed to release'} package: {identifier}"
            )
        
        elif operation == OperationType.REVOKE:
            if not confirm_destructive:
                return ControlPanelResult(
                    domain=ManagementDomain.SOFTWARE,
                    operation=operation,
                    entity_type="package",
                    success=False,
                    message="Destructive operation requires confirm_destructive=true"
                )
            
            if not identifier:
                return ControlPanelResult(
                    domain=ManagementDomain.SOFTWARE,
                    operation=operation,
                    entity_type="package",
                    success=False,
                    message="Package ID required"
                )
            
            success = self._api.software.revoke_package(identifier)
            return ControlPanelResult(
                domain=ManagementDomain.SOFTWARE,
                operation=operation,
                entity_type="package",
                success=success,
                message=f"{'Revoked' if success else 'Failed to revoke'} package: {identifier}"
            )
        
        return ControlPanelResult(
            domain=ManagementDomain.SOFTWARE,
            operation=operation,
            entity_type="package",
            success=False,
            message=f"Unsupported operation for package: {operation}"
        )
    
    def _handle_virtual_folder(self, operation: OperationType) -> ControlPanelResult:
        """Handle virtual folder operations."""
        
        if operation == OperationType.LIST:
            folders = self._api.software.get_virtual_folders()
            items = [{"name": f.name, "path": f.path} for f in folders]
            return ControlPanelResult(
                domain=ManagementDomain.SOFTWARE,
                operation=operation,
                entity_type="virtual_folder",
                success=True,
                message=f"Found {len(items)} virtual folders",
                items=items,
                count=len(items)
            )
        
        return ControlPanelResult(
            domain=ManagementDomain.SOFTWARE,
            operation=operation,
            entity_type="virtual_folder",
            success=False,
            message="Virtual folders are read-only in this interface"
        )
    
    # =========================================================================
    # Process Domain Handler
    # =========================================================================
    
    def _handle_process(self, input: ControlPanelInput) -> ControlPanelResult:
        """Handle process domain operations."""
        entity_type = input.entity_type or "test_operation"
        params = input.parameters or {}
        
        if operation := input.operation:
            if operation == OperationType.LIST:
                return self._list_processes(entity_type)
            elif operation == OperationType.GET:
                return self._get_process(entity_type, input.identifier, params)
        
        return ControlPanelResult(
            domain=ManagementDomain.PROCESS,
            operation=input.operation,
            entity_type=entity_type,
            success=False,
            message=f"Processes are read-only. Use list or get operations."
        )
    
    def _list_processes(self, entity_type: str) -> ControlPanelResult:
        """List processes by type."""
        if entity_type == "test_operation":
            processes = self._api.process.get_test_operations()
        elif entity_type == "repair_operation":
            processes = self._api.process.get_repair_operations()
        elif entity_type == "wip_operation":
            processes = self._api.process.get_wip_operations()
        else:
            processes = self._api.process.get_processes()
        
        items = [{"code": p.code, "name": p.name, "description": p.description} for p in processes]
        return ControlPanelResult(
            domain=ManagementDomain.PROCESS,
            operation=OperationType.LIST,
            entity_type=entity_type,
            success=True,
            message=f"Found {len(items)} {entity_type.replace('_', ' ')}s",
            items=items,
            count=len(items)
        )
    
    def _get_process(
        self, 
        entity_type: str, 
        identifier: Optional[str],
        params: Dict[str, Any]
    ) -> ControlPanelResult:
        """Get a specific process."""
        if not identifier:
            return ControlPanelResult(
                domain=ManagementDomain.PROCESS,
                operation=OperationType.GET,
                entity_type=entity_type,
                success=False,
                message="Process code or name required"
            )
        
        # Try to parse as int
        try:
            code = int(identifier)
        except ValueError:
            code = identifier
        
        if entity_type == "test_operation":
            process = self._api.process.get_test_operation(code)
        elif entity_type == "repair_operation":
            process = self._api.process.get_repair_operation(code)
        elif entity_type == "wip_operation":
            process = self._api.process.get_wip_operation(code)
        else:
            process = self._api.process.get_process(code)
        
        if process:
            return ControlPanelResult(
                domain=ManagementDomain.PROCESS,
                operation=OperationType.GET,
                entity_type=entity_type,
                success=True,
                message=f"Found process: {process.name}",
                data={"code": process.code, "name": process.name, "description": process.description},
                count=1
            )
        return ControlPanelResult(
            domain=ManagementDomain.PROCESS,
            operation=OperationType.GET,
            entity_type=entity_type,
            success=False,
            message=f"Process not found: {identifier}"
        )
    
    # =========================================================================
    # Helper Methods
    # =========================================================================
    
    def _is_uuid(self, value: Optional[str]) -> bool:
        """Check if a string looks like a UUID."""
        if not value:
            return False
        import re
        uuid_pattern = re.compile(
            r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
            re.IGNORECASE
        )
        return bool(uuid_pattern.match(value))
    
    def _serialize_asset(self, asset: Any) -> Dict[str, Any]:
        """Serialize an asset to a dictionary."""
        return {
            "asset_id": str(getattr(asset, 'asset_id', None)),
            "serial_number": getattr(asset, 'serial_number', None),
            "asset_name": getattr(asset, 'asset_name', None),
            "type_id": str(getattr(asset, 'type_id', None)),
            "state": str(getattr(asset, 'state', None)),
            "location": getattr(asset, 'location', None),
            "description": getattr(asset, 'description', None),
        }
    
    def _serialize_product(self, product: Any) -> Dict[str, Any]:
        """Serialize a product to a dictionary."""
        revisions = []
        if hasattr(product, 'revisions') and product.revisions:
            revisions = [{"revision": r.revision, "name": r.name} for r in product.revisions[:5]]
        
        return {
            "part_number": getattr(product, 'part_number', None),
            "name": getattr(product, 'name', None),
            "description": getattr(product, 'description', None),
            "state": str(getattr(product, 'state', None)),
            "non_serial": getattr(product, 'non_serial', False),
            "revisions": revisions,
        }
    
    def _serialize_unit(self, unit: Any) -> Dict[str, Any]:
        """Serialize a production unit to a dictionary."""
        return {
            "serial_number": getattr(unit, 'serial_number', None),
            "part_number": getattr(unit, 'part_number', None),
            "revision": getattr(unit, 'revision', None),
            "phase": getattr(unit, 'unit_phase', None),
            "phase_id": getattr(unit, 'unit_phase_id', None),
            "batch_number": getattr(unit, 'batch_number', None),
            "location": getattr(unit, 'current_location', None),
            "parent_serial": getattr(unit, 'parent_serial_number', None),
        }
    
    def _serialize_package(self, package: Any) -> Dict[str, Any]:
        """Serialize a software package to a dictionary."""
        return {
            "package_id": str(getattr(package, 'package_id', None)),
            "name": getattr(package, 'name', None),
            "version": getattr(package, 'version', None),
            "status": str(getattr(package, 'status', None)) if getattr(package, 'status', None) else None,
            "description": getattr(package, 'description', None),
        }
    
    def _build_summary(self, result: ControlPanelResult) -> str:
        """Build human-readable summary."""
        icon = "✅" if result.success else "❌"
        
        lines = [f"{icon} Control Panel: {result.domain.value.upper()} / {result.entity_type}"]
        lines.append(f"   Operation: {result.operation.value}")
        lines.append(f"   {result.message}")
        
        if result.count > 0:
            lines.append(f"   Items: {result.count}")
        
        if result.items and len(result.items) <= 5:
            lines.append("   Results:")
            for item in result.items:
                # Get a reasonable display string
                name = item.get('name') or item.get('serial_number') or item.get('part_number') or item.get('code') or str(item)
                lines.append(f"      • {name}")
        elif result.items:
            lines.append(f"   (Showing first 5 of {len(result.items)} items)")
            for item in result.items[:5]:
                name = item.get('name') or item.get('serial_number') or item.get('part_number') or item.get('code') or str(item)
                lines.append(f"      • {name}")
        
        return "\n".join(lines)


# =============================================================================
# Tool Definition Helper
# =============================================================================

def get_definition() -> Dict[str, Any]:
    """Get tool definition for registration."""
    return ControlPanelTool.get_definition()
