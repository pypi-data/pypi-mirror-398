"""
Resource Share Checker - Implementation of IShareChecker using ResourceShareService.

This module bridges the AccessChecker with the ResourceShareService,
allowing access checks to consider resource shares without creating
circular dependencies.

Design:
- Implements IShareChecker protocol
- Uses lazy initialization to avoid import-time circular deps
- Can be injected into AccessChecker or DatabaseService

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from typing import Optional, Dict, Any, TYPE_CHECKING
from boto3_assist.dynamodb.dynamodb import DynamoDB

if TYPE_CHECKING:
    from geek_cafe_saas_sdk.core.request_context import RequestContext


class ResourceShareChecker:
    """
    IShareChecker implementation using ResourceShareService.
    
    This class provides share checking by querying the ResourceShare table.
    It's designed to be injected into AccessChecker or DatabaseService.
    
    Key Design Decisions:
    1. Uses direct DynamoDB queries instead of ResourceShareService
       to avoid circular dependency (ResourceShareService extends DatabaseService)
    2. Caches share lookups within a request for performance
    3. Thread-safe for Lambda concurrent execution
    
    Usage:
        # Create checker with DynamoDB connection
        checker = ResourceShareChecker(
            dynamodb=db,
            table_name="my-table",
            request_context=ctx
        )
        
        # Use in AccessChecker
        access_checker = AccessChecker(
            request_context=ctx,
            share_checker=checker
        )
    """
    
    def __init__(
        self,
        dynamodb: DynamoDB,
        table_name: str,
        request_context: "RequestContext"
    ):
        """
        Initialize ResourceShareChecker.
        
        Args:
            dynamodb: DynamoDB client instance
            table_name: Table containing ResourceShare records
            request_context: Current request context or callable that returns one.
                Using a callable ensures the checker always uses the current context
                even if it's refreshed (e.g., in Lambda handler injection scenarios).
        """
        self._dynamodb = dynamodb
        self._table_name = table_name
        self._request_context_source = request_context
        self._cache: Dict[str, Optional[Dict[str, Any]]] = {}
    
    @property
    def _request_context(self) -> "RequestContext":
        """Get the current request context (supports both direct and callable sources)."""
        if callable(self._request_context_source):
            return self._request_context_source()
        return self._request_context_source
    
    def check_share(
        self,
        resource_id: str,
        user_id: str,
        tenant_id: str,
        required_permission: str = "view"
    ) -> Optional[Dict[str, Any]]:
        """
        Check if user has access to resource via sharing.
        
        Queries the ResourceShare GSI to find active shares for this
        resource and user combination.
        
        Args:
            resource_id: The resource ID to check
            user_id: The user requesting access
            tenant_id: The tenant context
            required_permission: Required permission level (view, download, edit)
            
        Returns:
            Dict with share info if access granted:
            {
                "has_access": True,
                "share_id": "...",
                "permission": "view|download|edit",
                "reason": "granted|insufficient_permission"
            }
            None if no share found
        """
        # Check cache first
        cache_key = f"{resource_id}:{user_id}"
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if cached:
                # Re-evaluate permission against cached share
                return self._evaluate_permission(cached, required_permission)
            return None
        
        # Query for shares - use GSI2 (shared_with_user_id)
        try:
            from boto3_assist.dynamodb.dynamodb_index import DynamoDBKey
            from geek_cafe_saas_sdk.modules.resource_shares.models.resource_share import ResourceShare
            import datetime as dt
            
            # Build query for shares to this user
            temp_share = ResourceShare()
            temp_share.shared_with_user_id = user_id
            
            # Get the GSI2 key
            gsi_key = temp_share.get_key("gsi2").key()
            
            # Query DynamoDB
            result = self._dynamodb.query(
                table_name=self._table_name,
                key=gsi_key,
                index_name="gsi2",
                ascending=False,
                limit=100  # Get recent shares
            )
            
            if not result or "Items" not in result:
                self._cache[cache_key] = None
                return None
            
            # Find matching share for this resource
            now = dt.datetime.now(dt.UTC).timestamp()
            
            for item in result["Items"]:
                share = ResourceShare()
                share.map(item)
                
                # Check if this share is for the requested resource
                if share.resource_id != resource_id:
                    continue
                
                # Check if share is active
                if share.status != "active":
                    continue
                
                # Check if share is expired
                if share.expires_at_ts and share.expires_at_ts < now:
                    continue
                
                # Found a valid share - cache it
                share_info = {
                    "share_id": share.id,
                    "permission": share.permission_level,
                    "resource_type": share.resource_type,
                    "owner_id": share.owner_id
                }
                self._cache[cache_key] = share_info
                
                return self._evaluate_permission(share_info, required_permission)
            
            # No valid share found
            self._cache[cache_key] = None
            return None
            
        except Exception as e:
            # Log error but don't fail - share checking is supplementary
            import logging
            logging.warning(f"Error checking resource share: {e}")
            return None
    
    def _evaluate_permission(
        self,
        share_info: Dict[str, Any],
        required_permission: str
    ) -> Optional[Dict[str, Any]]:
        """
        Evaluate if share permission satisfies required permission.
        
        Permission hierarchy: edit > download > view
        """
        hierarchy = {"view": 1, "download": 2, "edit": 3}
        
        share_level = hierarchy.get(share_info.get("permission", "view"), 0)
        required_level = hierarchy.get(required_permission, 0)
        
        has_access = share_level >= required_level
        
        return {
            "has_access": has_access,
            "share_id": share_info.get("share_id"),
            "permission": share_info.get("permission"),
            "reason": "granted" if has_access else "insufficient_permission"
        }
    
    def clear_cache(self):
        """Clear the share cache (call at end of request)."""
        self._cache.clear()
    
    def invalidate_resource(self, resource_id: str):
        """Invalidate cache entries for a specific resource."""
        keys_to_remove = [k for k in self._cache if k.startswith(f"{resource_id}:")]
        for key in keys_to_remove:
            del self._cache[key]
