"""Product repository - internal API data access layer.

⚠️ INTERNAL API - SUBJECT TO CHANGE ⚠️

Uses internal WATS API endpoints that are not publicly documented.
These endpoints may change without notice. This module should be
replaced with public API endpoints as soon as they become available.

The internal API requires the Referer header to be set to the base URL.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID

from ...core import HttpClient
from .models import Product, BomItem, ProductRevisionRelation


class ProductRepositoryInternal:
    """
    Product data access layer using internal API.
    
    ⚠️ INTERNAL API - SUBJECT TO CHANGE ⚠️
    
    Uses:
    - GET /api/internal/Product/Bom
    - PUT /api/internal/Product/BOM
    - GET /api/internal/Product/GetProduct
    - POST /api/internal/Product/PostProductRevisionRelation
    - PUT /api/internal/Product/PutProductRevisionRelation
    - DELETE /api/internal/Product/DeleteProductRevisionRelation
    
    The internal API requires the Referer header.
    """
    
    def __init__(self, http_client: HttpClient, base_url: str):
        """
        Initialize repository with HTTP client and base URL.
        
        Args:
            http_client: The HTTP client for API calls
            base_url: The base URL (needed for Referer header)
        """
        self._http = http_client
        self._base_url = base_url.rstrip('/')
    
    def _internal_get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Make an internal API GET request with Referer header.
        
        ⚠️ INTERNAL: Adds Referer header required by internal API.
        """
        response = self._http.get(
            endpoint,
            params=params,
            headers={"Referer": self._base_url}
        )
        if response.is_success:
            return response.data
        return None
    
    def _internal_post(self, endpoint: str, data: Any = None, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Make an internal API POST request with Referer header.
        
        ⚠️ INTERNAL: Adds Referer header required by internal API.
        """
        response = self._http.post(
            endpoint,
            data=data,
            params=params,
            headers={"Referer": self._base_url}
        )
        if response.is_success:
            return response.data
        return None
    
    def _internal_put(self, endpoint: str, data: Any = None, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Make an internal API PUT request with Referer header.
        
        ⚠️ INTERNAL: Adds Referer header required by internal API.
        """
        response = self._http.put(
            endpoint,
            data=data,
            params=params,
            headers={"Referer": self._base_url}
        )
        if response.is_success:
            return response.data
        return None
    
    def _internal_delete(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> bool:
        """
        Make an internal API DELETE request with Referer header.
        
        ⚠️ INTERNAL: Adds Referer header required by internal API.
        """
        response = self._http.delete(
            endpoint,
            params=params,
            headers={"Referer": self._base_url}
        )
        return response.is_success
    
    # =========================================================================
    # BOM Operations
    # =========================================================================
    
    def get_bom(self, part_number: str, revision: str) -> List[BomItem]:
        """
        Get BOM (Bill of Materials) for a product revision.
        
        ⚠️ INTERNAL API - uses /api/internal/Product/Bom
        
        Args:
            part_number: Product part number
            revision: Product revision
            
        Returns:
            List of BomItem objects
        """
        data = self._internal_get(
            "/api/internal/Product/Bom",
            params={"partNumber": part_number, "revision": revision}
        )
        if data and isinstance(data, list):
            return [BomItem.model_validate(item) for item in data]
        return []
    
    def upload_bom(
        self,
        part_number: str,
        revision: str,
        bom_items: List[Dict[str, Any]],
        format: str = "json"
    ) -> bool:
        """
        Upload/update BOM items.
        
        ⚠️ INTERNAL API - uses PUT /api/internal/Product/BOM
        
        Args:
            part_number: Product part number
            revision: Product revision
            bom_items: List of BOM item dictionaries
            format: BOM format (default: "json")
            
        Returns:
            True if successful
        """
        result = self._internal_put(
            "/api/internal/Product/BOM",
            data=bom_items,
            params={
                "partNumber": part_number,
                "revision": revision,
                "format": format
            }
        )
        return result is not None
    
    # =========================================================================
    # Product Revision Relations (Box Build Templates)
    # =========================================================================
    
    def get_product_with_relations(
        self, 
        part_number: str, 
        revision: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get product with revision relations (box build template).
        
        ⚠️ INTERNAL API - uses /api/internal/Product/GetProductByPN
        
        NOTE: This endpoint does NOT return ChildProductRevisionRelations.
        Use get_product_hierarchy() instead for box build relations.
        
        Args:
            part_number: Product part number
            revision: Optional specific revision to filter
            
        Returns:
            Product data with relations or None
        """
        data = self._internal_get(
            "/api/internal/Product/GetProductByPN",
            params={"PN": part_number}
        )
        return data
    
    def get_product_hierarchy(
        self,
        part_number: str,
        revision: str
    ) -> List[Dict[str, Any]]:
        """
        Get product hierarchy including all child revision relations.
        
        ⚠️ INTERNAL API - uses /api/internal/Product/GetProductInfo
        
        This returns the full product tree including:
        - The parent product at hlevel=0
        - All child relations at hlevel=1+ with ProductRevisionRelationId
        
        Args:
            part_number: Product part number
            revision: Product revision
            
        Returns:
            List of hierarchy items. Each item includes:
            - PartNumber, Revision, ProductRevisionId
            - ParentProductRevisionId, ProductRevisionRelationId (for children)
            - hlevel (0=parent, 1+=children)
            - Quantity, RevisionMask
        """
        data = self._internal_get(
            "/api/internal/Product/GetProductInfo",
            params={"partNumber": part_number, "revision": revision}
        )
        return data if isinstance(data, list) else []
    
    def create_revision_relation(
        self,
        parent_revision_id: UUID,
        child_revision_id: UUID,
        quantity: int = 1,
        item_number: Optional[str] = None,
        revision_mask: Optional[str] = None
    ) -> Optional[ProductRevisionRelation]:
        """
        Create a product revision relation (add subunit to box build).
        
        ⚠️ INTERNAL API - uses POST /api/internal/Product/PostProductRevisionRelation
        
        Args:
            parent_revision_id: Parent product revision ID
            child_revision_id: Child product revision ID
            quantity: Number of child units required
            item_number: Optional item/position number
            revision_mask: Optional revision mask pattern (comma-separated, % wildcard)
            
        Returns:
            Created ProductRevisionRelation or None
        """
        # API expects PascalCase field names:
        # - ParentProductRevisionId: Parent revision
        # - ProductRevisionId: Child revision (NOT "childProductRevisionId")
        # - Quantity, RevisionMask (optional)
        data = {
            "ParentProductRevisionId": str(parent_revision_id),
            "ProductRevisionId": str(child_revision_id),
            "Quantity": quantity,
        }
        if revision_mask:
            data["RevisionMask"] = revision_mask
            
        result = self._internal_post(
            "/api/internal/Product/PostProductRevisionRelation",
            data=data
        )
        
        # API returns the full hierarchy as a list, find the newly created relation
        if result and isinstance(result, list):
            # Look for the child relation with matching revision ID
            for item in result:
                if (item.get("ProductRevisionId") == str(child_revision_id) and 
                    item.get("ParentProductRevisionId") == str(parent_revision_id) and
                    item.get("ProductRevisionRelationId")):
                    return ProductRevisionRelation.model_validate(item)
            # If not found by exact match, return None (relation already existed)
            return None
        elif result:
            # If single object returned
            return ProductRevisionRelation.model_validate(result)
        return None
    
    def update_revision_relation(
        self,
        relation: ProductRevisionRelation
    ) -> Optional[ProductRevisionRelation]:
        """
        Update a product revision relation.
        
        ⚠️ INTERNAL API - uses PUT /api/internal/Product/PutProductRevisionRelation
        
        Args:
            relation: ProductRevisionRelation with updated data
            
        Returns:
            Updated ProductRevisionRelation or None
        """
        # Use mode='json' to convert UUIDs to strings for JSON serialization
        data = relation.model_dump(by_alias=True, exclude_none=True, mode='json')
        result = self._internal_put(
            "/api/internal/Product/PutProductRevisionRelation",
            data=data
        )
        if result:
            return ProductRevisionRelation.model_validate(result)
        return None
    
    def delete_revision_relation(self, relation_id: UUID) -> bool:
        """
        Delete a product revision relation.
        
        ⚠️ INTERNAL API - uses DELETE /api/internal/Product/DeleteProductRevisionRelation
        
        Args:
            relation_id: The relation ID to delete
            
        Returns:
            True if successful
        """
        return self._internal_delete(
            "/api/internal/Product/DeleteProductRevisionRelation",
            params={"productRevisionRelationId": str(relation_id)}
        )
    
    # =========================================================================
    # Product Categories
    # =========================================================================
    
    def get_categories(self) -> List[Dict[str, Any]]:
        """
        Get all product categories.
        
        ⚠️ INTERNAL API - uses /api/internal/Product/GetProductCategories
        
        Returns:
            List of category dictionaries
        """
        data = self._internal_get("/api/internal/Product/GetProductCategories")
        if data and isinstance(data, list):
            return data
        return []
    
    def save_categories(self, categories: List[Dict[str, Any]]) -> bool:
        """
        Save product categories.
        
        ⚠️ INTERNAL API - uses PUT /api/internal/Product/PutProductCategories
        
        Args:
            categories: List of category dictionaries
            
        Returns:
            True if successful
        """
        result = self._internal_put(
            "/api/internal/Product/PutProductCategories",
            data=categories
        )
        return result is not None
