"""
KeywordSearchService - Service for managing keyword search indexes.

This service provides CRUD operations for keyword search entries and
supports tenant-wide searches, user-scoped searches, and keyword refresh
for resources.

Copyright 2024-2025 Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

import os
import logging
from typing import Optional, List, Dict, Any

from boto3_assist.dynamodb.dynamodb import DynamoDB

from geek_cafe_saas_sdk.core.request_context import RequestContext
from geek_cafe_saas_sdk.core.services.database_service import DatabaseService
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.core.models.keyword_search import (
    KeywordSearch,
    normalize_keyword,
    extract_keywords,
)

logger = logging.getLogger(__name__)


class KeywordSearchService(DatabaseService[KeywordSearch]):
    """
    Service for managing keyword search indexes.
    
    Provides:
    - Tenant-wide keyword search
    - User-scoped keyword search
    - Resource keyword refresh (sync keywords when resource is saved)
    - CRUD operations for keyword entries
    
    Example:
        service = KeywordSearchService(
            dynamodb=db,
            table_name="keywords-table",
            request_context=context
        )
        
        # Search for resources by keyword
        results = service.search(keyword="report")
        
        # Refresh keywords for a resource
        service.refresh_resource_keywords(
            resource_type="file",
            resource_id="file_123",
            keywords=["report", "quarterly", "sales"]
        )
    """
    
    def __init__(
        self,
        *,
        dynamodb: Optional[DynamoDB] = None,
        table_name: Optional[str] = None,
        request_context: RequestContext,
    ):
        """
        Initialize KeywordSearchService.
        
        Args:
            dynamodb: DynamoDB instance
            table_name: DynamoDB table name
            request_context: Security context (REQUIRED)
        """
        super().__init__(
            dynamodb=dynamodb, table_name=table_name, request_context=request_context
        )
    
    # ========================================
    # Search Operations
    # ========================================
    
    def search(
        self,
        keyword: str,
        *,
        resource_type: Optional[str] = None,
        limit: int = 100,
    ) -> ServiceResult[List[KeywordSearch]]:
        """
        Search for resources by keyword (tenant-wide).
        
        Uses the primary index for efficient tenant-scoped keyword lookup.
        
        Args:
            keyword: Keyword to search for (will be normalized)
            resource_type: Optional filter by resource type
            limit: Maximum results to return
            
        Returns:
            ServiceResult with list of KeywordSearch entries
        """
        try:
            normalized = normalize_keyword(keyword)
            if not normalized:
                return ServiceResult.error_result(
                    error_code="INVALID_KEYWORD",
                    message="Keyword is empty after normalization"
                )
            
            # Build query model for primary index
            query_model = KeywordSearch()
            query_model.tenant_id = self.request_context.authenticated_tenant_id
            query_model.normalized_keyword = normalized
            
            key = query_model.get_key("primary")
            query_result = self.dynamodb.query(
                table_name=self.table_name,
                key=key,
                limit=limit,
            )
            # Query using helper method
            # query_result = self.q(
            #     query_model, "primary", limit=limit, ascending=True
            # )
            
            items = query_result.get("Items", [])
            entries = [KeywordSearch().map(item) for item in items]
            
            # Filter by resource_type if specified
            if resource_type:
                entries = [e for e in entries if e.resource_type == resource_type]
            
            return ServiceResult.success_result(entries)
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return ServiceResult.error_result("SEARCH_FAILED", str(e))
    
    def search_by_user(
        self,
        keyword: str,
        *,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        limit: int = 100,
    ) -> ServiceResult[List[KeywordSearch]]:
        """
        Search for resources by keyword, scoped to a user.
        
        Uses GSI1 for user-scoped keyword lookup.
        
        Args:
            keyword: Keyword to search for (will be normalized)
            user_id: User ID to scope search to (defaults to authenticated user)
            resource_type: Optional filter by resource type
            limit: Maximum results to return
            
        Returns:
            ServiceResult with list of KeywordSearch entries
        """
        try:
            normalized = normalize_keyword(keyword)
            if not normalized:
                return ServiceResult.error_result(
                   error_code="INVALID_KEYWORD",
                   message="Keyword is empty after normalization"
                )
            
            target_user_id = user_id or self.request_context.authenticated_user_id
            
            # Build query model for GSI1
            query_model = KeywordSearch()
            query_model.tenant_id = self.request_context.authenticated_tenant_id
            query_model.user_id = target_user_id
            query_model.normalized_keyword = normalized
            
            # Query using helper method
            query_result = self._query_by_index(
                query_model, "gsi1", limit=limit, ascending=True
            )
            
            if not query_result.success:
                return query_result
            
            # Filter by resource_type if specified
            entries = query_result.data or []
            if resource_type:
                entries = [e for e in entries if e.resource_type == resource_type]
            
            return ServiceResult.success_result(entries)
            
        except Exception as e:
            logger.error(f"User search failed: {e}")
            return ServiceResult.error_result(
                error_code="SEARCH_FAILED",
                message=str(e)
            )
    
    # ========================================
    # Keyword Refresh Operations
    # ========================================
    
    def refresh_resource_keywords(
        self,
        resource_type: str,
        resource_id: str,
        keywords: List[str],
        *,
        user_id: Optional[str] = None,
        field: Optional[str] = None,
    ) -> ServiceResult[Dict[str, int]]:
        """
        Refresh keywords for a resource (sync with new keyword list).
        
        This method:
        1. Queries existing keywords for the resource (via GSI2)
        2. Computes diff (keywords to add, keywords to remove)
        3. Deletes removed keywords
        4. Inserts new keywords
        
        Args:
            resource_type: Type of resource (e.g., 'file', 'project')
            resource_id: ID of the resource
            keywords: New list of keywords (will be normalized)
            user_id: Optional user ID for user-scoped keywords
            field: Optional field name (e.g., 'title', 'tags')
            
        Returns:
            ServiceResult with stats: {"added": N, "removed": M, "unchanged": K}
        """
        try:
            tenant_id = self.request_context.authenticated_tenant_id
            target_user_id = user_id or self.request_context.authenticated_user_id
            
            # Normalize new keywords
            new_keywords = set()
            for kw in keywords:
                normalized = normalize_keyword(kw)
                if normalized:
                    new_keywords.add(normalized)
            
            # Get existing keywords for this resource
            existing_result = self._get_keywords_for_resource(
                resource_type=resource_type,
                resource_id=resource_id,
                field=field,
            )
            
            if not existing_result.success:
                return ServiceResult.error_result(
                    error_code=existing_result.error_code,
                    message=existing_result.error_message
                )
            
            existing_entries = existing_result.data or []
            existing_keywords = {e.normalized_keyword for e in existing_entries}
            
            # Compute diff
            to_add = new_keywords - existing_keywords
            to_remove = existing_keywords - new_keywords
            unchanged = existing_keywords & new_keywords
            
            # Delete removed keywords
            for entry in existing_entries:
                if entry.normalized_keyword in to_remove:
                    self._delete_keyword_entry(entry)
            
            # Add new keywords
            for kw in to_add:
                entry = KeywordSearch()
                entry.tenant_id = tenant_id
                entry.user_id = target_user_id
                entry.normalized_keyword = kw
                entry.resource_type = resource_type
                entry.resource_id = resource_id
                entry.field = field
                
                entry.prep_for_save()
                self._save_model(entry)
            
            stats = {
                "added": len(to_add),
                "removed": len(to_remove),
                "unchanged": len(unchanged),
            }
            
            logger.debug(
                f"Refreshed keywords for {resource_type}/{resource_id}: {stats}"
            )
            
            return ServiceResult.success_result(stats)
            
        except Exception as e:
            logger.error(f"Keyword refresh failed: {e}")
            return ServiceResult.error_result(
                error_code="REFRESH_FAILED",
                message=str(e)
            )
    
    def refresh_from_text(
        self,
        resource_type: str,
        resource_id: str,
        text: str,
        *,
        user_id: Optional[str] = None,
        field: Optional[str] = None,
        min_keyword_length: int = 2,
    ) -> ServiceResult[Dict[str, int]]:
        """
        Extract keywords from text and refresh for a resource.
        
        Convenience method that extracts keywords from text and calls
        refresh_resource_keywords.
        
        Args:
            resource_type: Type of resource
            resource_id: ID of the resource
            text: Text to extract keywords from
            user_id: Optional user ID for user-scoped keywords
            field: Optional field name
            min_keyword_length: Minimum keyword length (default 2)
            
        Returns:
            ServiceResult with stats
        """
        keywords = extract_keywords(text, min_length=min_keyword_length)
        return self.refresh_resource_keywords(
            resource_type=resource_type,
            resource_id=resource_id,
            keywords=keywords,
            user_id=user_id,
            field=field,
        )
    
    def delete_resource_keywords(
        self,
        resource_type: str,
        resource_id: str,
        *,
        field: Optional[str] = None,
    ) -> ServiceResult[int]:
        """
        Delete all keywords for a resource.
        
        Call this when a resource is deleted.
        
        Args:
            resource_type: Type of resource
            resource_id: ID of the resource
            field: Optional field to limit deletion to
            
        Returns:
            ServiceResult with count of deleted entries
        """
        try:
            # Get existing keywords
            existing_result = self._get_keywords_for_resource(
                resource_type=resource_type,
                resource_id=resource_id,
                field=field,
            )
            
            if not existing_result.success:
                return ServiceResult.error_result(
                    existing_result.error_code,
                    existing_result.error_message
                )
            
            entries = existing_result.data or []
            
            # Delete all
            for entry in entries:
                self._delete_keyword_entry(entry)
            
            logger.debug(
                f"Deleted {len(entries)} keywords for {resource_type}/{resource_id}"
            )
            
            return ServiceResult.success_result(len(entries))
            
        except Exception as e:
            logger.error(f"Delete keywords failed: {e}")
            return ServiceResult.error_result("DELETE_FAILED", str(e))
    
    # ========================================
    # Internal Helpers
    # ========================================
    
    def _get_keywords_for_resource(
        self,
        resource_type: str,
        resource_id: str,
        field: Optional[str] = None,
    ) -> ServiceResult[List[KeywordSearch]]:
        """
        Get all keyword entries for a resource using GSI2.
        
        Args:
            resource_type: Type of resource
            resource_id: ID of the resource
            field: Optional field to filter by
            
        Returns:
            ServiceResult with list of KeywordSearch entries
        """
        try:
            # Build query model for GSI2
            query_model = KeywordSearch()
            query_model.tenant_id = self.request_context.authenticated_tenant_id
            query_model.resource_type = resource_type
            query_model.resource_id = resource_id
            
            # Query using helper method
            query_result = self._query_by_index(
                query_model, "gsi2", limit=1000, ascending=True
            )
            
            if not query_result.success:
                return query_result
            
            # Filter by field if specified
            entries = query_result.data or []
            if field is not None:
                entries = [e for e in entries if e.field == field]
            
            return ServiceResult.success_result(entries)
            
        except Exception as e:
            logger.error(f"Get keywords for resource failed: {e}")
            return ServiceResult.error_result("QUERY_FAILED", str(e))
    
    def _delete_keyword_entry(self, entry: KeywordSearch) -> bool:
        """
        Delete a single keyword entry.
        
        Args:
            entry: KeywordSearch entry to delete
            
        Returns:
            True if deleted successfully
        """
        try:
            self.dynamodb.delete(
                table_name=self.table_name,
                model=entry,
            )
            return True
        except Exception as e:
            logger.error(f"Delete keyword entry failed: {e}")
            return False
    
    # ========================================
    # Abstract Method Implementations
    # ========================================
    
    def create(self, **kwargs) -> ServiceResult[KeywordSearch]:
        """
        Create a single keyword entry.
        
        Args:
            **kwargs: Keyword entry attributes
                keyword: Keyword string (required, will be normalized)
                resource_type: Resource type (required)
                resource_id: Resource ID (required)
                field: Optional field name
                user_id: Optional user ID
                
        Returns:
            ServiceResult with created KeywordSearch entry
        """
        try:
            keyword = kwargs.get("keyword")
            resource_type = kwargs.get("resource_type")
            resource_id = kwargs.get("resource_id")
            
            if not keyword:
                return ServiceResult.error_result(
                    error_code="MISSING_KEYWORD",
                    message="keyword is required"
                )
            if not resource_type:
                return ServiceResult.error_result(
                    error_code="MISSING_RESOURCE_TYPE",
                    message="resource_type is required"
                )
            if not resource_id:
                return ServiceResult.error_result(
                    error_code="MISSING_RESOURCE_ID",
                    message="resource_id is required"
                )
            
            normalized = normalize_keyword(keyword)
            if not normalized:
                return ServiceResult.error_result(
                    error_code="INVALID_KEYWORD",
                        message="Keyword is empty after normalization"
                )
            
            entry = KeywordSearch()
            entry.tenant_id = self.request_context.authenticated_tenant_id
            entry.user_id = kwargs.get("user_id") or self.request_context.authenticated_user_id
            entry.normalized_keyword = normalized
            entry.original_keyword = keyword
            entry.resource_type = resource_type
            entry.resource_id = resource_id
            entry.field = kwargs.get("field")
            
            entry.prep_for_save()
            return self._save_model(entry)
            
        except Exception as e:
            logger.error(f"Create keyword entry failed: {e}")
            return ServiceResult.error_result(
                error_code="CREATE_FAILED",
                message=str(e)
            )
    
    def get_by_id(self, resource_id: str, **kwargs) -> ServiceResult[KeywordSearch]:
        """
        Get a keyword entry by its composite key.
        
        Note: KeywordSearch entries don't have a simple ID - they're identified
        by the combination of tenant_id, keyword, resource_type, resource_id, and field.
        
        Use search() or _get_keywords_for_resource() instead.
        """
        return ServiceResult.error_result(
            error_code="NOT_SUPPORTED",
            message="KeywordSearch entries don't have simple IDs. Use search() instead."
        )
    
    def update(self, resource_id: str, **kwargs) -> ServiceResult[KeywordSearch]:
        """
        Update is not supported for keyword entries.
        
        Keywords are immutable - delete and recreate instead.
        """
        return ServiceResult.error_result(
            error_code="NOT_SUPPORTED",
            message="Keyword entries are immutable. Delete and recreate instead."
        )
    
    def delete(self, resource_id: str, **kwargs) -> ServiceResult[bool]:
        """
        Delete keyword entries for a resource.
        
        Args:
            resource_id: Resource ID
            **kwargs:
                resource_type: Resource type (required)
                field: Optional field to limit deletion
                
        Returns:
            ServiceResult with True if successful
        """
        resource_type = kwargs.get("resource_type")
        if not resource_type:
            return ServiceResult.error_result(
                error_code="MISSING_RESOURCE_TYPE",
                message="resource_type is required"
            )
        
        result = self.delete_resource_keywords(
            resource_type=resource_type,
            resource_id=resource_id,
            field=kwargs.get("field"),
        )
        
        if result.success:
            return ServiceResult.success_result(True)
        return ServiceResult.error_result(error_code=result.error_code, message=result.message)
