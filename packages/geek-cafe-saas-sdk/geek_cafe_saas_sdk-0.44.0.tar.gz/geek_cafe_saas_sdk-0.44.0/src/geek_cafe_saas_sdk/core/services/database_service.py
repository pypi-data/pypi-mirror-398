# Database Service

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Dict, Any, List, Optional, TYPE_CHECKING
from boto3_assist.dynamodb.dynamodb import DynamoDB, DynamoDBIndex
from ..service_result import ServiceResult
from ..service_errors import ValidationError, AccessDeniedError, NotFoundError
from ..error_codes import ErrorCode
from ..request_context import RequestContext
import os
from aws_lambda_powertools import Logger

# Import audit logging infrastructure
from ..audit import AuditEvent, AuditAction, AuditLoggerFactory
# Import access control infrastructure
from ..access import AccessChecker, AccessLevel, AccessResult, IShareChecker, NoOpShareChecker
if TYPE_CHECKING:
    from ..audit import IAuditLogger

T = TypeVar("T")

logger = Logger()


class DatabaseService(ABC, Generic[T]):
    """Base service class for database operations with AUTOMATIC security and audit logging.
    
    SECURITY (Job Zero - Always On):
        All CRUD operations automatically enforce access control:
        - READ: Checks owner, admin, or resource share (VIEW permission)
        - UPDATE: Checks owner, admin, or resource share (EDIT permission)
        - DELETE: Checks owner or admin only (no share-based delete)
        
        Access is granted if ANY of these conditions are met:
        1. User is platform_admin (full access everywhere)
        2. User is tenant_admin (full access within their tenant)
        3. User is the resource owner (owner_id or created_by_id matches)
        4. User has a valid ResourceShare for this resource
        
        Security CANNOT be disabled. The only escape hatch is `skip_access_check=True`
        for rare internal operations where access was already verified.
    
    Audit Logging:
        When configured via environment variables, all CRUD operations are
        automatically logged to the configured audit destination (DynamoDB, S3, or both).
        
        Environment Variables:
            AUDIT_LOG_ENABLED: "true" to enable audit logging
            AUDIT_LOG_DESTINATION: "dynamodb", "s3", or "both"
            AUDIT_LOG_TABLE_NAME: DynamoDB table for audit logs
            AUDIT_LOG_BUCKET_NAME: S3 bucket for audit logs
        
        Audit events capture:
            - Who: user_id, tenant_id, user_email
            - What: action (CREATE/UPDATE/DELETE), resource_type, resource_id
            - When: timestamp
            - Changes: old_values, new_values, changed_fields
    """

    def __init__(
        self,
        *,
        dynamodb: DynamoDB = None,
        table_name: str = None,
        request_context: RequestContext,
        audit_logger: Optional["IAuditLogger"] = None
    ):
        """
        Initialize DatabaseService with AUTOMATIC security.
        
        Args:
            dynamodb: DynamoDB client instance
            table_name: DynamoDB table name
            request_context: **REQUIRED** Security context with JWT token
            audit_logger: Optional audit logger (auto-configured from environment if not provided)
            
        Raises:
            ValueError: If table_name is not provided
            AccessDeniedError: If request_context is not provided
            
        Security:
            Access control is AUTOMATIC and ALWAYS ON. The share checker is
            automatically initialized to check ResourceShare records in the
            same table. Security cannot be disabled.
        """
        if request_context is None:
            raise AccessDeniedError("request_context is required for all database operations. All services must have security context.")
        
        self.dynamodb = dynamodb or DynamoDB()
        self.table_name = (
            table_name or os.getenv("DYNAMODB_TABLE_NAME")
        )

        if not self.table_name:
            raise ValueError("Table name is required.  You can pass the table name as a parameter or set the DYNAMODB_TABLE_NAME environment variable.")

        self.LOG_DYNAMO_DB_QUERY = os.getenv("LOG_DYNAMO_DB_QUERY", False)
        self._request_context = request_context
        
        # Initialize audit logger (auto-configured from environment if not provided)
        self._audit_logger = audit_logger or AuditLoggerFactory.create_from_environment(
            dynamodb=self.dynamodb
        )
        
        # AUTOMATIC share checker - always enabled, uses same table for ResourceShare records
        # This is NOT optional - security is Job Zero
        # NOTE: Pass a lambda to get current context - this ensures checkers always use
        # the latest context even if _request_context is refreshed (e.g., handler injection)
        from ..access import ResourceShareChecker
        self._share_checker: IShareChecker = ResourceShareChecker(
            dynamodb=self.dynamodb,
            table_name=self.table_name,
            request_context=lambda: self._request_context
        )
        
        # Initialize access checker with share support - ALWAYS ON
        # Pass lambda to ensure it always uses current _request_context
        self._access_checker = AccessChecker(
            request_context=lambda: self._request_context,
            share_checker=self._share_checker
        )

        if not self._request_context:
            raise AccessDeniedError("Request context is required for all database operations")
    
    @property
    def request_context(self) -> RequestContext:
        """Get the request context (security token)."""
        if self._request_context is None:
            raise AccessDeniedError("No security context set for this service")
        return self._request_context
    
    @request_context.setter
    def request_context(self, value: RequestContext):
        """Set the request context (security token)."""
        self._request_context = value
    
    @property
    def audit_logger(self) -> "IAuditLogger":
        """Get the audit logger."""
        return self._audit_logger
    
    @audit_logger.setter
    def audit_logger(self, value: "IAuditLogger"):
        """Set the audit logger."""
        self._audit_logger = value
    
    @property
    def access_checker(self) -> AccessChecker:
        """Get the access checker (read-only - security cannot be modified)."""
        return self._access_checker

    @abstractmethod
    def create(self, tenant_id: str, user_id: str, **kwargs) -> ServiceResult[T]:
        """Create a new resource."""
        pass

    @abstractmethod
    def get_by_id(
        self, resource_id: str, tenant_id: str, user_id: str
    ) -> ServiceResult[T]:
        """Get resource by ID with access control."""
        pass

    @abstractmethod
    def update(
        self, resource_id: str, tenant_id: str, user_id: str, updates: Dict[str, Any]
    ) -> ServiceResult[T]:
        """Update resource with access control."""
        pass

    @abstractmethod
    def delete(
        self, resource_id: str, tenant_id: str, user_id: str
    ) -> ServiceResult[bool]:
        """Delete resource with access control."""
        pass

    def _is_system_context(self) -> bool:
        """
        Check if the current request context is a system context.
        
        System contexts are used for internal operations (background jobs,
        authorization lookups, etc.) and bypass normal security checks.
        
        Returns:
            True if this is a system context
        """
        if not self._request_context:
            return False
        # Check for system role or system user ID
        return (
            'system' in getattr(self._request_context, 'roles', []) or
            getattr(self._request_context, 'authenticated_user_id', None) == 'system'
        )

    def _validate_required_fields(
        self, data: Dict[str, Any], required_fields: List[str]
    ) -> None:
        """Validate required fields are present."""
        missing_fields = []
        for field in required_fields:
            if field not in data or data[field] is None:
                missing_fields.append(field)
        
        if missing_fields:
            if len(missing_fields) == 1:
                raise ValidationError(f"Field '{missing_fields[0]}' is required", missing_fields[0])
            else:
                field_list = "', '".join(missing_fields)
                raise ValidationError(f"Fields '{field_list}' are required", missing_fields)
    
    def _validate_owner_field(
        self, payload: Dict[str, Any], authenticated_user_id: str, field_name: str = "owner_id"
    ) -> str:
        """
        Validate and resolve owner field following Rule #3.
        
        Pattern:
        - Missing owner_id: Default to authenticated user (self-service)
        - Present owner_id with value: Use specified owner (admin-on-behalf)
        - Present owner_id but empty/null: ERROR (explicit but invalid)
        
        Args:
            payload: Request payload
            authenticated_user_id: User ID from JWT
            field_name: Name of owner field (default: "owner_id")
            
        Returns:
            Resolved owner user ID
            
        Raises:
            ValidationError: If owner_id is explicitly provided but empty/null
        """
        # Check if field is explicitly provided in payload
        if field_name in payload:
            owner_id = payload[field_name]
            # Explicit but empty/null = error (fail fast)
            if not owner_id:
                raise ValidationError(
                    f"{field_name} cannot be empty when explicitly provided",
                    field_name
                )
            return owner_id
        
        # Field not provided = default to authenticated user (self-service)
        return authenticated_user_id

    # REMOVED: _validate_tenant_access - too strict, doesn't support shares/admins
    # Use _get_by_id() which has proper security checks built-in

    def _check_resource_access(
        self,
        resource_id: str,
        resource_owner_id: Optional[str],
        resource_tenant_id: Optional[str],
        required_permission: AccessLevel = AccessLevel.VIEW,
        allow_tenant_access: bool = False
    ) -> AccessResult:
        """
        Manually check access (for edge cases only - CRUD methods check automatically).
        
        NOTE: You typically don't need to call this. All CRUD operations
        (_get_model_by_id_with_access_check, _save_model, _delete_model)
        automatically check access. Use this only for:
        - Pre-flight checks before expensive operations
        - Custom access logic not covered by standard CRUD
        
        Args:
            resource_id: The resource ID
            resource_owner_id: The owner's user ID
            resource_tenant_id: The resource's tenant ID
            required_permission: Required permission level (VIEW, EDIT, etc.)
            allow_tenant_access: If True, any user in same tenant can access
            
        Returns:
            AccessResult with granted status and reason
        """
        return self._access_checker.check_access(
            resource_id=resource_id,
            resource_owner_id=resource_owner_id,
            resource_tenant_id=resource_tenant_id,
            required_permission=required_permission,
            allow_tenant_access=allow_tenant_access
        )
    
    def _require_resource_access(
        self,
        resource_id: str,
        resource_owner_id: Optional[str],
        resource_tenant_id: Optional[str],
        required_permission: AccessLevel = AccessLevel.VIEW,
        allow_tenant_access: bool = False
    ) -> AccessResult:
        """
        Manually require access (for edge cases only - CRUD methods check automatically).
        
        NOTE: You typically don't need to call this. All CRUD operations
        automatically check access. Use this only for edge cases.
        
        Raises:
            AccessDeniedError: If access is denied
        """
        return self._access_checker.require_access(
            resource_id=resource_id,
            resource_owner_id=resource_owner_id,
            resource_tenant_id=resource_tenant_id,
            required_permission=required_permission,
            allow_tenant_access=allow_tenant_access
        )

    def _save_model(
        self,
        model: T,
        *,
        old_model: Optional[T] = None,
        preserve_timestamps: bool = False,
        skip_access_check: bool = False
    ) -> ServiceResult[T]:
        """Save model to database with **AUTOMATIC** security validation and audit trail.
        
        Args:
            model: Model to save
            old_model: Optional previous state of model (for UPDATE audit logging)
                      If provided, enables detailed change tracking in audit log.
            preserve_timestamps: If True, don't update modified_utc_ts.
                               Useful for migrations and data imports where
                               you want to preserve the original timestamps.
            skip_access_check: If True, skip access validation (use with caution -
                              only for internal operations where access was already verified)
        
        Returns:
            ServiceResult with saved model or error
            
        Security:
            - **AUTOMATIC** access validation for UPDATES (owner, admin, or edit share)
            - **ALWAYS** validates tenant access
            - **ALWAYS** auto-populates audit fields (created_by, updated_by)
            - **ALWAYS** prevents cross-tenant resource creation
            - request_context is required (enforced in __init__)
            
        Audit Logging:
            - Automatically logs CREATE or UPDATE events when audit logging is enabled
            - Captures old_values and new_values for change tracking
            - Fail-safe: audit failures don't break business operations
        """
        try:
            # MANDATORY security validation - always validate tenant access
            # EXCEPTION: SYSTEM tenant can provision new tenants (signup flow)
            from geek_cafe_saas_sdk.core.anonymous_context import AnonymousContextFactory
            is_system_tenant = (self._request_context.authenticated_tenant_id == 
                               AnonymousContextFactory.SYSTEM_TENANT_ID)
            
            if hasattr(model, 'tenant_id') and model.tenant_id:
                # SYSTEM tenant can create resources in any tenant (provisioning)
                if not is_system_tenant:
                    if not self._request_context.validate_tenant_access(model.tenant_id):
                        return ServiceResult.error_result(
                            ErrorCode.ACCESS_DENIED,
                            "Cannot save resources in other tenants"
                            f"Target Tenant ID: {model.tenant_id}, User Tenant ID: {self._request_context.authenticated_tenant_id}"
                        )
            
            if not old_model:
                try:
                    old_model = self._get_model_by_id(model.id, model.__class__)
                except Exception as e:
                    logger.error(f"Failed to get old model: {e}")
                    pass
            # Determine if this is a CREATE or UPDATE
            # SIMPLE RULE: If old_model is provided, it's an UPDATE. Otherwise, it's a CREATE.
            # 
            # For proper UPDATE behavior (access check + audit logging with change tracking),
            # services SHOULD pass old_model when updating existing records:
            #   old_model = self._get_model_by_id(id, ModelClass)
            #   # ... modify model ...
            #   return self._save_model(model, old_model=old_model)
            #
            # If old_model is not provided, we treat it as a CREATE (no access check needed
            # since the user is creating their own resource).
            is_create = old_model is None
            
            # AUTOMATIC access check for UPDATES (not creates)
            # For updates, user must have EDIT permission
            if not is_create and not skip_access_check and not is_system_tenant:
                access_result = self._access_checker.check_model_access(
                    model=model,
                    required_permission=AccessLevel.EDIT
                )
                
                if not access_result.granted:
                    return ServiceResult.error_result(
                        ErrorCode.ACCESS_DENIED,
                        f"You do not have permission to modify this resource. Reason: {access_result.reason}"
                    )
            
            # MANDATORY audit trail - always populate audit fields
            # Set created_by_id if this is a new resource
            if hasattr(model, 'created_by_id') and not model.created_by_id:
                model.created_by_id = self._request_context.authenticated_user_id
            
            # Always update updated_by_id
            if hasattr(model, 'updated_by_id'):
                model.updated_by_id = self._request_context.authenticated_user_id
            
            # Prepare model for save (sets id, timestamps, computes keys)
            # This is idempotent and safe to call multiple times
            if hasattr(model, 'prep_for_save') and callable(model.prep_for_save):
                model.prep_for_save(preserve_timestamps=preserve_timestamps)
            
            # The boto3_assist library handles all GSI key population automatically.
            self.dynamodb.save(table_name=self.table_name, item=model)
            
            # Log audit event (fail-safe - doesn't break business operations)
            self._log_audit_event(
                action=AuditAction.CREATE if is_create else AuditAction.UPDATE,
                model=model,
                old_model=old_model,
                success=True
            )
            http_status = 201 if is_create else 200
            return ServiceResult.success_result(model, http_status=http_status)
        except Exception as e:
            # Log failed audit event
            self._log_audit_event(
                action=AuditAction.CREATE if old_model is None else AuditAction.UPDATE,
                model=model,
                old_model=old_model,
                success=False,
                error_message=str(e)
            )
            return ServiceResult.exception_result(
                e,
                error_code=ErrorCode.DATABASE_SAVE_FAILED,
                context=f"Failed to save model to table {self.table_name}",
            )

    def _fetch_model_raw(self, resource_id: str, model_class) -> Optional[T]:
        """
        Raw database fetch - NO security checks.
        
        INTERNAL USE ONLY. This method bypasses all security checks.
        Use _get_by_id() for normal operations.
        
        Only use this for:
        - Building composite operations where you'll check access separately
        - Fetching old_model for audit logging comparison
        - System operations that have already verified access
        """
        try:
            temp_model = model_class()
            temp_model.id = resource_id
            key = temp_model.get_key("primary").key()

            result = self.dynamodb.get(table_name=self.table_name, key=key)
            if not result or "Item" not in result:
                return None

            model = model_class()
            model.map(result["Item"])
            return model
        except Exception:
            return None

    # Backward compatibility alias - will be removed in future version
    def _get_model_by_id(self, resource_id: str, model_class) -> Optional[T]:
        """DEPRECATED: Use _get_by_id() with skip_security_check=True instead."""
        return self._fetch_model_raw(resource_id, model_class)

    def _get_by_id(
        self,
        resource_id: str,
        model_class,
        *,
        skip_security_check: bool = False,
        required_permission: AccessLevel = AccessLevel.VIEW,
        include_deleted: bool = True # getting by ID should always include deleted records
    ) -> Optional[T]:
        """
        Get model by ID - THE primary method for fetching resources.
        
        Security is ON by default. This method automatically:
        1. Requires authentication
        2. Fetches the resource from DynamoDB
        3. Validates access (owner, admin, tenant settings, shares)
        4. Returns None if access denied (prevents enumeration)
        
        Args:
            resource_id: The resource ID to fetch
            model_class: The model class to instantiate
            skip_security_check: Set True ONLY for system records without tenant data
                                or when access was already verified upstream.
                                Default: False (security ON)
            required_permission: Required permission level (VIEW, DOWNLOAD, EDIT)
            include_deleted: If True, returns soft-deleted items
            
        Returns:
            The model if found AND access granted, None otherwise
            
        Example:
            # Normal usage - security is automatic
            file = self._get_by_id(file_id, File)
            
            # System record without tenant - skip security
            config = self._get_by_id(config_id, SystemConfig, skip_security_check=True)
        """
        # Require authentication unless skipping security
        if not skip_security_check:
            self.request_context.require_authentication()
        
        # Fetch raw model
        model = self._fetch_model_raw(resource_id, model_class)
        if not model:
            return None
        
        # Filter deleted if requested
        if not include_deleted:
            if hasattr(model, 'is_deleted') and callable(model.is_deleted):
                if model.is_deleted():
                    return None
            elif hasattr(model, 'status') and model.status == 'deleted':
                return None
        
        # Skip security checks if requested (for system records)
        if skip_security_check:
            return model
        
        # CENTRALIZED SECURITY CHECK via AccessChecker
        access_result = self._access_checker.check_model_access(
            model=model,
            required_permission=required_permission
        )
        
        if access_result.granted:
            return model
        
        # Access denied - log the real reason for audit/troubleshooting, return None to hide existence
        logger.warning(
            f"Access denied for resource {resource_id}",
            extra={
                "resource_id": resource_id,
                "user_id": self._request_context.authenticated_user_id,
                "resource_tenant_id": getattr(model, 'tenant_id', None),
                "user_tenant_id": self._request_context.authenticated_tenant_id,
                "required_permission": required_permission.value,
                "denial_reason": access_result.reason,
                "action": "ACCESS_DENIED_MASKED_AS_NOT_FOUND"
            }
        )
        return None

    # ========================================
    # DEPRECATED METHODS - Use _get_by_id() instead
    # These are kept for backward compatibility only
    # ========================================

    def _get_model_by_id_with_access_check(
        self,
        resource_id: str,
        model_class,
        required_permission: AccessLevel = AccessLevel.VIEW,
        include_deleted: bool = False,
        allow_tenant_access: bool = False
    ) -> Optional[T]:
        """DEPRECATED: Use _get_by_id() instead. Will be removed in future version."""
        return self._get_by_id(
            resource_id,
            model_class,
            required_permission=required_permission,
            include_deleted=include_deleted
        )

    def _get_model_by_id_with_tenant_check(
        self, resource_id: str, model_class, tenant_id: Optional[str] = None, include_deleted: bool = True
    ) -> Optional[T]:
        """DEPRECATED: Use _get_by_id() instead. Will be removed in future version."""
        logger.warning("DEPRECATED: Use _get_by_id() instead. Will be removed in future version.")
        return self._get_by_id(
            resource_id,
            model_class,
            include_deleted=include_deleted
        )

    def _delete_model(self, model: T, *, skip_access_check: bool = False) -> ServiceResult[bool]:
        """Delete model from database with **AUTOMATIC** access validation and audit logging.
        
        Args:
            model: Model to delete
            skip_access_check: If True, skip access validation (use with caution - 
                              only for internal operations where access was already verified)
            
        Returns:
            ServiceResult[bool] - True if successful
            
        Security:
            - **AUTOMATIC** access validation - only owner or admin can delete
            - Returns ACCESS_DENIED error if user lacks permission
            
        Audit Logging:
            - Logs DELETE event with full model state as old_values
            - Fail-safe: audit failures don't break business operations
        """
        try:
            # AUTOMATIC access check - only owner/admin can delete
            if not skip_access_check:
                resource_owner_id = getattr(model, 'owner_id', None) or getattr(model, 'created_by_id', None)
                resource_tenant_id = getattr(model, 'tenant_id', None)
                
                access_result = self._access_checker.check_access(
                    resource_id=model.id,
                    resource_owner_id=resource_owner_id,
                    resource_tenant_id=resource_tenant_id,
                    required_permission=AccessLevel.OWNER,  # Delete requires owner-level access
                    allow_tenant_access=False
                )
                
                # Only owner or admin can delete
                if not access_result.granted or access_result.level not in (AccessLevel.OWNER, AccessLevel.ADMIN):
                    return ServiceResult.error_result(
                        ErrorCode.ACCESS_DENIED,
                        "Only the owner or an admin can delete this resource"
                    )
            
            primary_key = model.get_key("primary").key()
            self.dynamodb.delete(table_name=self.table_name, primary_key=primary_key)
            
            # Log audit event for delete
            self._log_audit_event(
                action=AuditAction.DELETE,
                model=model,
                old_model=model,  # For DELETE, old_model is the deleted state
                success=True
            )
            
            return ServiceResult.success_result(True)
        except Exception as e:
            # Log failed audit event
            self._log_audit_event(
                action=AuditAction.DELETE,
                model=model,
                old_model=model,
                success=False,
                error_message=str(e)
            )
            return ServiceResult.exception_result(
                e,
                error_code=ErrorCode.DATABASE_DELETE_FAILED,
                context=f"Failed to delete model from table {self.table_name}",
            )

    def _query_by_index(
        self,
        model: T,
        index_name: str,
        *,
        ascending: bool = False,
        strongly_consistent: bool = False,
        projection_expression: Optional[str] = None,
        expression_attribute_names: Optional[dict] = None,
        start_key: Optional[dict] = None,
        limit: Optional[int] = None,
    ) -> ServiceResult[List[T]]:
        """
        Generic query method for GSI queries with automatic model mapping.

        Args:
            model: The pre-configured model instance to use for the query
            index_name: The name of the GSI index to query

        Returns:
            ServiceResult containing a list of mapped model instances.
            Pagination info is included in error_details as 'last_evaluated_key' if more results exist.
        """
        try:
            # Get the key for the specified index from the provided model
            key = model.get_key(index_name).key()

            # key.to_string()
            # extract_key_values(key_expression) is coming soon from boto3_assist
            if self.LOG_DYNAMO_DB_QUERY:
                if hasattr(DynamoDBIndex, 'extract_key_values'):
                    values = DynamoDBIndex.extract_key_values(key)
                    logger.info(f"Querying index {index_name} with key {values}")
                else:
                    try:
                        value = {
                            'pk': key._values[0]._values[1],
                            'sk': key._values[1]._values[1],
                            'operator': key._values[1].expression_operator,
                            'format': key._values[1].expression_format,
                            'index_name': index_name
                        }
                        logger.info(f"Querying index {index_name} with key {value}")
                    except Exception as e:
                        logger.error(f"Failed to extract key values: {e}")
                

            # Execute the query
            response = self.dynamodb.query(
                table_name=self.table_name,
                key=key,
                index_name=index_name,
                ascending=ascending,
                strongly_consistent=strongly_consistent,
                projection_expression=projection_expression,
                expression_attribute_names=expression_attribute_names,
                start_key=start_key,
                limit=limit,
            )

            # Extract items from response
            data = response.get("Items", [])

            # Map each item to a model instance
            model_class = type(model)
            items = [model_class().map(item) for item in data]

            # Include pagination info if present
            result = ServiceResult.success_result(items)
            if "LastEvaluatedKey" in response:
                result.error_details = {"last_evaluated_key": response["LastEvaluatedKey"]}

            return result

        except Exception as e:
            return ServiceResult.exception_result(
                e,
                error_code=ErrorCode.DATABASE_QUERY_FAILED,
                context=f"Failed to query index {index_name} on table {self.table_name}",
            )

    def _delete_by_composite_key(
        self,
        pk: str,
        sk: str,
    ) -> ServiceResult[bool]:
        """
        Delete an item by composite key (pk + sk).
        
        Useful for adjacent record patterns where items use composite keys
        instead of a single id field.
        
        Args:
            pk: Partition key value
            sk: Sort key value
            
        Returns:
            ServiceResult[bool] - True if successful
            
        Example:
            # Delete a specific member from a channel
            result = self._delete_by_composite_key(
                pk="channel#channel_123",
                sk="member#user_456"
            )
        """
        try:
            # Use boto3 resource (simpler API that handles typing)
            key = {"pk": pk, "sk": sk}
            self.dynamodb.delete(table_name=self.table_name, primary_key=key)
            return ServiceResult.success_result(True)
            
        except Exception as e:
            return ServiceResult.exception_result(
                e,
                error_code=ErrorCode.DATABASE_DELETE_FAILED,
                context=f"Failed to delete item by composite key from table {self.table_name}",
            )

    def _handle_service_exception(
        self, e: Exception, operation: str, **context
    ) -> ServiceResult[T]:
        """
        Common exception handler for service operations.
        
        Maps exception types to standardized error codes and formats error details.
        Always includes operation name in error details for debugging.
        
        Args:
            e: The exception that was raised
            operation: Name of the operation that failed (for logging/debugging)
            **context: Additional context information (resource_id, tenant_id, etc.)
        
        Returns:
            ServiceResult with appropriate error information
        """
        # Build base error details with operation
        error_details = {"operation": operation, **context}
        
        # Validation errors (4xx equivalent)
        if isinstance(e, ValidationError):
            field_info = getattr(e, "field", None)
            # Handle both single field and list of fields
            if isinstance(field_info, list):
                error_details["fields"] = field_info
            elif field_info:
                error_details["field"] = field_info
            
            return ServiceResult.error_result(
                message=f"Validation failed: {str(e)}",
                error_code=ErrorCode.VALIDATION_ERROR,
                error_details=error_details,
            )
        
        # Authorization errors (403 equivalent)
        elif isinstance(e, AccessDeniedError):
            return ServiceResult.error_result(
                message=str(e),
                error_code=ErrorCode.ACCESS_DENIED,
                error_details=error_details
            )
        
        # Resource not found (404 equivalent)
        elif isinstance(e, NotFoundError):
            return ServiceResult.error_result(
                message=str(e),
                error_code=ErrorCode.NOT_FOUND,
                error_details=error_details
            )
        
        # Unexpected errors (500 equivalent)
        else:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context=f"Operation '{operation}' failed: {str(e)}"
            )

    # ========== Audit Logging Methods ==========
    
    def _log_audit_event(
        self,
        action: str,
        model: T,
        *,
        old_model: Optional[T] = None,
        success: bool = True,
        error_message: str = ""
    ) -> None:
        """
        Log an audit event for a database operation.
        
        This method is fail-safe - audit logging failures will not break
        business operations. Errors are logged but not raised.
        
        Args:
            action: The action performed (CREATE, UPDATE, DELETE, etc.)
            model: The model being operated on (current/new state)
            old_model: Previous state of model (for UPDATE/DELETE operations)
            success: Whether the operation succeeded
            error_message: Error message if operation failed
        """
        try:
            # Skip if audit logging is disabled
            if not self._audit_logger or not self._audit_logger.is_enabled:
                logger.warning("Audit logging is disabled")
                return
            
            # Extract model information
            resource_type = self._get_model_resource_type(model)
            resource_id = getattr(model, 'id', '') or ''
            resource_name = self._get_model_resource_name(model)
            tenant_id = getattr(model, 'tenant_id', '') or self._request_context.authenticated_tenant_id
            
            # Build old/new values for change tracking
            old_values = {}
            new_values = {}
            
            if old_model is not None:
                old_values = self._model_to_audit_dict(old_model)
            
            if action != AuditAction.DELETE:
                new_values = self._model_to_audit_dict(model)
            
            # Get resource owner user_id if available
            resource_owner_id = getattr(model, 'owner_id', '') or getattr(model, 'user_id', '') or ''
            
            # Create audit event (AuditEvent is now an alias for AuditLog model)
            event = AuditEvent()
            
            # Actor (who performed the action)
            event.actor_tenant_id = self._request_context.authenticated_tenant_id
            event.actor_user_id = self._request_context.authenticated_user_id
            event.actor_email = getattr(self._request_context, 'authenticated_email', '') or ''
            
            # Resource owner (whose data is being modified)
            event.tenant_id = tenant_id
            event.user_id = resource_owner_id
            
            # What
            event.action = action
            event.resource_type = resource_type
            event.resource_id = resource_id
            event.resource_name = resource_name
            event.old_values = old_values
            event.new_values = new_values
            event.service_name = self.__class__.__name__
            event.source_table_name = self.table_name
            event.success = success
            event.error_message = error_message
            event.resource_class_name = self._get_model_class_name(model)
            # Compute changed fields
            event.compute_changed_fields()
            
            # Log the event (fail-safe)
            self._audit_logger.log(event)
            
        except Exception as e:
            # Audit logging should never break business operations
            logger.warning(
                f"Failed to log audit event: {e}",
                extra={
                    "action": action,
                    "model_type": type(model).__name__ if model else "unknown",
                    "error": str(e)
                }
            )
    
    def _get_model_class_name(self, model: T) -> str:
        """
        Get the resource type name from a model (the class name).
        
        Args:
            model: The model instance
            
        Returns:
            Resource type string (e.g., "file", "directory", "user")
        """
        if hasattr(model, 'class_name'):
            return model.class_name()
        
        # Fallback: convert class name to snake_case
        class_name = type(model).__name__
        # Simple snake_case conversion
        return class_name

    def _get_model_resource_type(self, model: T) -> str:
        """
        Get the resource type name from a model (the class name).
        
        Args:
            model: The model instance
            
        Returns:
            Resource type string (e.g., "file", "directory", "user")
        """
        if hasattr(model, 'model_name') and model.model_name:
            return str(model.model_name)
        return 'unknown'
    
    def _get_model_resource_name(self, model: T) -> str:
        """
        Get a human-readable name for the resource (the model name).
        
        Args:
            model: The model instance
            
        Returns:
            Resource name or empty string if not found
        """
        if hasattr(model, 'model_name') and model.model_name:
            return str(model.model_name)
        return 'unknown'
    
    def _model_to_audit_dict(self, model: T) -> Dict[str, Any]:
        """
        Convert a model to a dictionary for audit logging.
        
        Excludes internal fields (starting with _) and large binary data.
        
        Args:
            model: The model instance
            
        Returns:
            Dictionary of model fields suitable for audit logging
        """
        try:
            # Use model's to_dictionary if available
            if hasattr(model, 'to_dictionary') and callable(model.to_dictionary):
                data = model.to_dictionary()
            else:
                # Fallback: extract public attributes
                data = {
                    k: v for k, v in model.__dict__.items()
                    if not k.startswith('_')
                }
            
            # Filter out large values and sensitive data
            filtered = {}
            for key, value in data.items():
                # Skip internal keys
                if key.startswith('_'):
                    continue
                # Skip index-related keys (pk, sk, gsi*_pk, gsi*_sk)
                if key in ('pk', 'sk') or key.startswith('gsi'):
                    continue
                # Skip large binary data
                if isinstance(value, bytes) and len(value) > 1000:
                    filtered[key] = f"<binary data: {len(value)} bytes>"
                    continue
                # Skip large strings (likely file content)
                if isinstance(value, str) and len(value) > 10000:
                    filtered[key] = f"<large string: {len(value)} chars>"
                    continue
                filtered[key] = value
            
            return filtered
            
        except Exception as e:
            logger.warning(f"Failed to convert model to audit dict: {e}")
            return {"error": f"Failed to serialize: {str(e)}"}
    
    def log_custom_audit_event(
        self,
        action: str,
        resource_type: str,
        resource_id: str,
        *,
        resource_name: str = "",
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: str = ""
    ) -> None:
        """
        Log a custom audit event for operations not covered by standard CRUD.
        
        Use this for custom actions like:
        - SHARE / UNSHARE
        - APPROVE / REJECT
        - DOWNLOAD / UPLOAD
        - LOGIN / LOGOUT
        
        Args:
            action: Custom action name (e.g., "SHARE", "APPROVE")
            resource_type: Type of resource (e.g., "file", "workflow")
            resource_id: ID of the resource
            resource_name: Human-readable name (optional)
            old_values: State before the action (optional)
            new_values: State after the action (optional)
            metadata: Additional context (optional)
            success: Whether the operation succeeded
            error_message: Error message if failed
            
        Example:
            self.log_custom_audit_event(
                action="SHARE",
                resource_type="file",
                resource_id="file_123",
                resource_name="report.pdf",
                new_values={"shared_with": "user_456", "permission": "read"},
                metadata={"share_type": "direct"}
            )
        """
        try:
            if not self._audit_logger or not self._audit_logger.is_enabled:
                return
            
            # Create audit event (AuditEvent is now an alias for AuditLog model)
            event = AuditEvent()
            
            # Actor (who performed the action)
            event.actor_tenant_id = self._request_context.authenticated_tenant_id
            event.actor_user_id = self._request_context.authenticated_user_id
            event.actor_email = getattr(self._request_context, 'authenticated_email', '') or ''
            
            # Resource owner - defaults to actor for custom events
            event.tenant_id = self._request_context.authenticated_tenant_id
            event.user_id = self._request_context.authenticated_user_id
            
            # What
            event.action = action
            event.resource_type = resource_type
            event.resource_id = resource_id
            event.resource_name = resource_name
            event.old_values = old_values or {}
            event.new_values = new_values or {}
            event.audit_metadata = metadata or {}
            event.service_name = self.__class__.__name__
            event.source_table_name = self.table_name
            event.success = success
            event.error_message = error_message
            
            event.compute_changed_fields()
            self._audit_logger.log(event)
            
        except Exception as e:
            logger.warning(f"Failed to log custom audit event: {e}")
