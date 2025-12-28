"""
ResourceMetaEntryService for managing extended metadata entries on any resource.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from typing import Optional, List
from boto3_assist.dynamodb.dynamodb import DynamoDB
from geek_cafe_saas_sdk.core.services.database_service import DatabaseService
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.core.error_codes import ErrorCode
from geek_cafe_saas_sdk.core.service_errors import ValidationError
from geek_cafe_saas_sdk.core.request_context import RequestContext
from geek_cafe_saas_sdk.core.models.resource_meta_entry import ResourceMetaEntry

import logging

logger = logging.getLogger(__name__)


class ResourceMetaEntryService(DatabaseService[ResourceMetaEntry]):
    """
    Service for managing extended metadata entries on any resource.

    Provides CRUDL operations for ResourceMetaEntry records which store
    additional metadata associated with any resource without overloading
    the main resource record.

    Each resource can have multiple metadata entries, distinguished by a unique key.

    Usage Examples:
        # For files
        service.create(resource_id=file_id, key="thumbnails", metadata={...})

        # For users
        service.create(resource_id=user_id, key="preferences", metadata={...})

        # For orders
        service.create(resource_id=order_id, key="shipping_updates", metadata={...})
    """

    def __init__(
        self,
        *,
        dynamodb: Optional[DynamoDB] = None,
        table_name: Optional[str] = None,
        request_context: RequestContext,
        resource_type: Optional[str] = None,
    ):
        """
        Initialize ResourceMetaEntryService.

        Args:
            dynamodb: DynamoDB instance
            table_name: DynamoDB table name
            request_context: Security context (REQUIRED)
        """
        super().__init__(
            dynamodb=dynamodb, table_name=table_name, request_context=request_context
        )

        self.resource_type = resource_type
    
    def create(self, **kwargs) -> ServiceResult[ResourceMetaEntry]:
        """
        Create a new metadata entry for a resource.

        Args:
            **kwargs: Metadata entry attributes
                resource_id: The resource ID this metadata belongs to (required)
                key: Unique key for this metadata entry (required)
                name: Display name for this entry (optional)
                description: Description of this entry (optional)
                metadata: Dict of arbitrary metadata (optional)
                tenant_id: Auto-injected from RequestContext if not provided
                user_id: Auto-injected from RequestContext if not provided

        Returns:
            ServiceResult with ResourceMetaEntry model
        """
        try:
            # Validate required fields
            resource_id = kwargs.get("resource_id")
            key = kwargs.get("key")

            if not resource_id:
                return ServiceResult.error_result(
                    message="resource_id is required",
                    error_code=ErrorCode.VALIDATION_ERROR,
                )

            if not key:
                return ServiceResult.error_result(
                    message="key is required",
                    error_code=ErrorCode.VALIDATION_ERROR,
                )

            # Create model and map fields
            entry = ResourceMetaEntry()
            entry.id = resource_id
            entry.key = key
            entry.name = kwargs.get("name")
            entry.description = kwargs.get("description")
            # Use resource_type from kwargs if provided, otherwise use the service's resource_type
            entry.resource_type = kwargs.get("resource_type") or self.resource_type

            # Handle metadata dict
            if "metadata" in kwargs and kwargs["metadata"]:
                entry.metadata = kwargs["metadata"]

            # Auto-inject security context
            entry.tenant_id = kwargs.get("tenant_id") or self.request_context.target_tenant_id
            entry.user_id = kwargs.get("user_id") or self.request_context.target_user_id
            entry.owner_id = kwargs.get("owner_id") or self.request_context.target_user_id

            # Validate tenant access
            if not self.request_context.validate_tenant_access(entry.tenant_id):
                return ServiceResult.error_result(
                    message="Access denied to tenant",
                    error_code=ErrorCode.ACCESS_DENIED,
                )

            # Prepare and save
            entry.prep_for_save()
            return self._save_model(entry)

        except ValidationError as e:
            return ServiceResult.error_result(
                message=str(e), error_code=ErrorCode.VALIDATION_ERROR
            )
        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="ResourceMetaEntryService.create",
            )

    def get_by_id(self, **kwargs) -> ServiceResult[ResourceMetaEntry]:
        """
        Get a metadata entry by resource_id and key.

        Args:
            **kwargs: Query parameters
                resource_id: The resource ID (required)
                key: The metadata key (required)

        Returns:
            ServiceResult with ResourceMetaEntry model
        """
        try:
            resource_id = kwargs.get("resource_id")
            key = kwargs.get("key")

            if not resource_id:
                return ServiceResult.error_result(
                    message="resource_id is required",
                    error_code=ErrorCode.VALIDATION_ERROR,
                )

            if not key:
                return ServiceResult.error_result(
                    message="key is required",
                    error_code=ErrorCode.VALIDATION_ERROR,
                )

            # Build the composite key and fetch
            entry = self._get_entry_by_resource_and_key(resource_id, key)

            if not entry:
                message = kwargs.get("error_message")
                if not message:
                    message = (
                        f"Metadata entry '{key}' not found: resource_id={resource_id}, key={key}. "
                        "resource_id is a generic term for any resource type (e.g. file, user, order)"
                    )
                return ServiceResult.error_result(
                    message=message,
                    error_code=ErrorCode.NOT_FOUND,
                )

            return ServiceResult.success_result(entry)

        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="ResourceMetaEntryService.get_by_id",
            )

    def _get_entry_by_resource_and_key(self, resource_id: str, key: str) -> Optional[ResourceMetaEntry]:
        """
        Internal method to fetch entry by resource_id and key.

        Uses the composite primary key: pk=resource#{resource_id}, sk=metadata#key#{key}
        """
        try:
            query_model = ResourceMetaEntry()
            query_model.id = resource_id
            query_model.key = key

            result = self.dynamodb.get(
                table_name=self.table_name,
                model=query_model,
            )

            if not result or "Item" not in result:
                return None

            entry = ResourceMetaEntry()
            entry.map(result["Item"])

            # Security check - validate access
            if entry.tenant_id != self.request_context.target_tenant_id:
                return None  # Hide existence from other tenants

            if entry.owner_id != self.request_context.authenticated_user_id:
                # Check if tenant-wide access is allowed
                if not self.request_context.allow_tenant_wide_access:
                    return None

            return entry

        except Exception as e:
            logger.error(f"Error fetching metadata entry: {e}")
            raise

    def update(self, **kwargs) -> ServiceResult[ResourceMetaEntry]:
        """
        Update a metadata entry.

        Args:
            **kwargs: Update parameters
                resource_id: The resource ID (required)
                key: The metadata key (required)
                name: New display name (optional)
                description: New description (optional)
                metadata: New metadata dict (optional)

        Returns:
            ServiceResult with updated ResourceMetaEntry model
        """
        try:
            resource_id = kwargs.get("resource_id")
            key = kwargs.get("key")

            if not resource_id:
                return ServiceResult.error_result(
                    message="resource_id is required",
                    error_code=ErrorCode.VALIDATION_ERROR,
                )

            if not key:
                return ServiceResult.error_result(
                    message="key is required",
                    error_code=ErrorCode.VALIDATION_ERROR,
                )

            # Get existing entry
            entry = self._get_entry_by_resource_and_key(resource_id, key)
            if not entry:
                return ServiceResult.error_result(
                    message=f"Metadata entry not found: resource_id={resource_id}, key={key}",
                    error_code=ErrorCode.NOT_FOUND,
                )

            # Store old model for audit
            old_entry = self._get_entry_by_resource_and_key(resource_id, key)

            # Apply updates
            if "name" in kwargs:
                entry.name = kwargs["name"]
            if "description" in kwargs:
                entry.description = kwargs["description"]
            if "metadata" in kwargs:
                entry.metadata = kwargs["metadata"]

            # Prepare and save with old_model for audit
            entry.prep_for_save()
            return self._save_model(entry, old_model=old_entry)

        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="ResourceMetaEntryService.update",
            )

    def delete(self, **kwargs) -> ServiceResult[bool]:
        """
        Delete a metadata entry.

        Args:
            **kwargs: Delete parameters
                resource_id: The resource ID (required)
                key: The metadata key (required)

        Returns:
            ServiceResult with success boolean
        """
        try:
            resource_id = kwargs.get("resource_id")
            key = kwargs.get("key")

            if not resource_id:
                return ServiceResult.error_result(
                    message="resource_id is required",
                    error_code=ErrorCode.VALIDATION_ERROR,
                )

            if not key:
                return ServiceResult.error_result(
                    message="key is required",
                    error_code=ErrorCode.VALIDATION_ERROR,
                )

            # Get existing entry
            entry = self._get_entry_by_resource_and_key(resource_id, key)
            if not entry:
                return ServiceResult.error_result(
                    message=f"Metadata entry not found: resource_id={resource_id}, key={key}",
                    error_code=ErrorCode.NOT_FOUND,
                )

            # Delete using the model
            return self._delete_model(entry)

        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="ResourceMetaEntryService.delete",
            )

    def list_by_resource(self, **kwargs) -> ServiceResult[List[ResourceMetaEntry]]:
        """
        List all metadata entries for a resource.

        Args:
            **kwargs: Query parameters
                resource_id: The resource ID (required)
                limit: Maximum number of results (optional, default: 50)

        Returns:
            ServiceResult with list of ResourceMetaEntry models
        """
        try:
            resource_id = kwargs.get("resource_id")
            limit = kwargs.get("limit", 50)

            if not resource_id:
                return ServiceResult.error_result(
                    message="resource_id is required",
                    error_code=ErrorCode.VALIDATION_ERROR,
                )

            query_model = ResourceMetaEntry()
            query_model.id = resource_id

            key = query_model.get_key("primary")
            response = self.dynamodb.query(
                table_name=self.table_name,
                key=key,
                limit=limit,
            )

            # Map results to model instances
            items = response.get("Items", [])
            entries = [ResourceMetaEntry().map(item) for item in items]

            # Filter by tenant access
            filtered_entries = []
            for entry in entries:
                if entry.tenant_id == self.request_context.target_tenant_id:
                    if (entry.owner_id == self.request_context.authenticated_user_id or
                            self.request_context.allow_tenant_wide_access):
                        filtered_entries.append(entry)

            return ServiceResult.success_result(filtered_entries)

        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="ResourceMetaEntryService.list_by_resource",
            )

    def upsert(self, **kwargs) -> ServiceResult[ResourceMetaEntry]:
        """
        Create or update a metadata entry.

        If an entry with the given resource_id and key exists, it will be updated.
        Otherwise, a new entry will be created.

        Args:
            **kwargs: Same as create()

        Returns:
            ServiceResult with ResourceMetaEntry model
        """
        try:
            resource_id = kwargs.get("resource_id")
            key = kwargs.get("key")

            if not resource_id or not key:
                return ServiceResult.error_result(
                    message="resource_id and key are required",
                    error_code=ErrorCode.VALIDATION_ERROR,
                )

            # Check if entry exists
            existing = self._get_entry_by_resource_and_key(resource_id, key)

            if existing:
                # Update existing
                return self.update(**kwargs)
            else:
                # Create new
                return self.create(**kwargs)

        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="ResourceMetaEntryService.upsert",
            )
