# Resource Permission Service

from typing import Dict, Any, List, Optional
from boto3_assist.dynamodb.dynamodb import DynamoDB
from geek_cafe_saas_sdk.core.services.database_service import DatabaseService
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.lambda_handlers._base.decorators import service_method
from geek_cafe_saas_sdk.core.service_errors import ValidationError, NotFoundError, AccessDeniedError
from geek_cafe_saas_sdk.modules.users.models import ResourcePermission
import datetime as dt
import time


class ResourcePermissionService(DatabaseService[ResourcePermission]):
    """
    Service for ResourcePermission operations (ABAC).
    
    Manages resource-level permission grants for fine-grained sharing.
    """    
    
    # Required abstract methods from DatabaseService
    @service_method("create")

    def create(self, **kwargs) -> ServiceResult[ResourcePermission]:
        """Create method - delegates to grant_permission()."""
        self.request_context.require_authentication()
        tenant_id = self.request_context.target_tenant_id
        user_id = self.request_context.target_user_id
        
        required = ['resource_type', 'resource_id', 'permissions', 'grantee_user_id']
        for field in required:
            if field not in kwargs:
                return ServiceResult.error_result(f"{field} is required", "VALIDATION_ERROR")
        
        return self.grant_permission(
            grantee_user_id=kwargs['grantee_user_id'],
            tenant_id=tenant_id,
            resource_type=kwargs['resource_type'],
            resource_id=kwargs['resource_id'],
            permissions=kwargs['permissions'],
            granted_by=user_id,
            reason=kwargs.get('reason'),
            expires_at=kwargs.get('expires_at')
        )
    
    @service_method("get_by_id")
    def get_by_id(self, resource_id: str) -> ServiceResult[ResourcePermission]:
        """Get a specific grant by ID."""
        self.request_context.require_authentication()
        tenant_id = self.request_context.target_tenant_id
        try:
            grant = self._get_model_by_id(resource_id, ResourcePermission)
            
            if not grant:
                raise NotFoundError(f"Grant with ID {resource_id} not found")
            
            # Validate tenant access
            if grant.tenant_id != tenant_id:
                raise AccessDeniedError("Access denied: different tenant")
            
            return ServiceResult.success_result(grant)
            
        except Exception as e:
            return self._handle_service_exception(e, 'get_by_id', resource_id=resource_id)
    
    @service_method("update")
    def update(self, resource_id: str, updates: Dict[str, Any]) -> ServiceResult[ResourcePermission]:
        """Update a grant (e.g., change permissions or expiration)."""
        self.request_context.require_authentication()
        tenant_id = self.request_context.target_tenant_id
        try:
            grant = self._get_model_by_id(resource_id, ResourcePermission)
            
            if not grant:
                raise NotFoundError(f"Grant with ID {resource_id} not found")
            
            # Validate tenant access
            if grant.tenant_id != tenant_id:
                raise AccessDeniedError("Access denied: different tenant")
            
            # Apply updates
            if 'permissions' in updates:
                grant.permissions = updates['permissions']
            if 'expires_at' in updates:
                grant.expires_at = updates['expires_at']
            if 'reason' in updates:
                grant.reason = updates['reason']
            if 'metadata' in updates:
                grant.metadata = updates['metadata']
            
            grant.prep_for_save()
            return self._save_model(grant)
            
        except Exception as e:
            return self._handle_service_exception(e, 'update', resource_id=resource_id)
    
    @service_method("delete")
    def delete(self, resource_id: str) -> ServiceResult[bool]:
        """Revoke a grant."""
        self.request_context.require_authentication()
        tenant_id = self.request_context.target_tenant_id
        try:
            grant = self._get_model_by_id(resource_id, ResourcePermission)
            
            if not grant:
                return ServiceResult.success_result(True)  # Already revoked
            
            # Validate tenant access
            if grant.tenant_id != tenant_id:
                raise AccessDeniedError("Access denied: different tenant")
            
            # Hard delete (or could soft delete with deleted_at timestamp)
            result = self._delete_model(grant)
            
            if result.success:
                return ServiceResult.success_result(True)
            return result
            
        except Exception as e:
            return self._handle_service_exception(e, 'delete', resource_id=resource_id)

    # Grant Management Methods
    
    def grant_permission(
        self,
        grantee_user_id: str,
        resource_type: str,
        resource_id: str,
        permissions: List[str],
        reason: Optional[str] = None,
        expires_at: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ServiceResult[ResourcePermission]:
        """
        Grant resource-level permissions to a user.
        
        Args:
            grantee_user_id: User to grant permissions to
            resource_type: Type of resource (event, community, chat_channel, etc.)
            resource_id: ID of specific resource
            permissions: List of permissions to grant (e.g., ["read", "write"])
            reason: Optional reason for the grant
            expires_at: Optional expiration timestamp
            metadata: Optional additional metadata
            
        Security:
            - Requires authentication
        """
        self.request_context.require_authentication()
        tenant_id = self.request_context.target_tenant_id
        granted_by = self.request_context.target_user_id
        
        try:
            # Validate inputs
            if not permissions or len(permissions) == 0:
                raise ValidationError("At least one permission is required")
            
            # Check if grant already exists
            existing = self.get_grant(grantee_user_id, resource_type, resource_id)
            
            if existing.success and existing.data:
                # Update existing grant
                grant = existing.data
                grant.permissions = permissions
                grant.granted_by = granted_by
                grant.granted_at = int(time.time())
                grant.expires_at = expires_at
                grant.reason = reason
                if metadata:
                    grant.metadata = metadata
            else:
                # Create new grant
                grant = ResourcePermission()
                grant.user_id = grantee_user_id
                grant.tenant_id = tenant_id
                grant.resource_type = resource_type
                grant.resource_id = resource_id
                grant.permissions = permissions
                grant.granted_by = granted_by
                grant.granted_at = int(time.time())
                grant.expires_at = expires_at
                grant.reason = reason
                if metadata:
                    grant.metadata = metadata
            
            grant.prep_for_save()
            return self._save_model(grant)
            
        except Exception as e:
            return self._handle_service_exception(
                e, 'grant_permission',
                user_id=grantee_user_id,
                resource_type=resource_type,
                resource_id=resource_id
            )
    
    def revoke_permission(
        self,
        grantee_user_id: str,
        resource_type: str,
        resource_id: str
    ) -> ServiceResult[bool]:
        """
        Revoke all permissions for a user on a resource.
        
        Args:
            grantee_user_id: User to revoke from
            resource_type: Type of resource
            resource_id: ID of resource
            
        Security:
            - Requires authentication
        """
        self.request_context.require_authentication()
        try:
            grant_result = self.get_grant(grantee_user_id, resource_type, resource_id)
            
            if not grant_result.success or not grant_result.data:
                return ServiceResult.success_result(True)  # Already revoked
            
            grant = grant_result.data
            result = self._delete_model(grant)
            
            if result.success:
                return ServiceResult.success_result(True)
            return result
            
        except Exception as e:
            return self._handle_service_exception(
                e, 'revoke_permission',
                user_id=grantee_user_id,
                resource_type=resource_type,
                resource_id=resource_id
            )
    
    def get_grant(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str
    ) -> ServiceResult[ResourcePermission]:
        """
        Get a specific grant for user on resource.
        
        Args:
            user_id: User ID
            resource_type: Type of resource
            resource_id: ID of resource
            
        Security:
            - Requires authentication
        """
        self.request_context.require_authentication()
        tenant_id = self.request_context.target_tenant_id
        try:
            # Query using GSI1 (user + resource)
            temp = ResourcePermission()
            temp.user_id = user_id
            temp.resource_type = resource_type
            temp.resource_id = resource_id
            temp.tenant_id = tenant_id
            
            result = self._query_by_index(temp, "gsi1", limit=1)
            
            if not result.success:
                return result
            
            if not result.data or len(result.data) == 0:
                return ServiceResult.error_result("Grant not found", "NOT_FOUND")
            
            grant = result.data[0]
            
            # Check if expired
            if grant.expires_at and grant.expires_at < int(time.time()):
                return ServiceResult.error_result("Grant has expired", "EXPIRED")
            
            return ServiceResult.success_result(grant)
            
        except Exception as e:
            return self._handle_service_exception(
                e, 'get_grant',
                user_id=user_id,
                resource_type=resource_type,
                resource_id=resource_id
            )
    
    def list_user_grants(
        self,
        user_id: str,
        limit: int = 50
    ) -> ServiceResult[List[ResourcePermission]]:
        """
        List all grants for a user.
        
        Args:
            user_id: User ID
            limit: Max results
            
        Security:
            - Requires authentication
        """
        self.request_context.require_authentication()
        tenant_id = self.request_context.target_tenant_id
        try:
            temp = ResourcePermission()
            temp.user_id = user_id
            temp.tenant_id = tenant_id
            
            result = self._query_by_index(temp, "gsi2", limit=limit)
            
            if not result.success:
                return result
            
            # Filter out expired grants
            current_time = int(time.time())
            active_grants = [
                grant for grant in result.data
                if not grant.expires_at or grant.expires_at > current_time
            ]
            
            return ServiceResult.success_result(active_grants)
            
        except Exception as e:
            return self._handle_service_exception(
                e, 'list_user_grants',
                user_id=user_id
            )
    
    def list_resource_grants(
        self,
        resource_type: str,
        resource_id: str,
        limit: int = 50
    ) -> ServiceResult[List[ResourcePermission]]:
        """
        List all grants on a resource (who has access).
        
        Args:
            resource_type: Type of resource
            resource_id: ID of resource
            tenant_id: Tenant context
            limit: Max results
        """
        try:
            temp = ResourcePermission()
            temp.resource_type = resource_type
            temp.resource_id = resource_id
            temp.tenant_id = tenant_id
            
            result = self._query_by_index(temp, "gsi3", limit=limit)
            
            if not result.success:
                return result
            
            # Filter out expired grants
            current_time = int(time.time())
            active_grants = [
                grant for grant in result.data
                if not grant.expires_at or grant.expires_at > current_time
            ]
            
            return ServiceResult.success_result(active_grants)
            
        except Exception as e:
            return self._handle_service_exception(
                e, 'list_resource_grants',
                resource_type=resource_type,
                resource_id=resource_id
            )
    
    def get_user_permissions_on_resource(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str
    ) -> List[str]:
        """
        Get list of permissions user has on a resource.
        
        Args:
            user_id: User ID
            resource_type: Type of resource
            resource_id: ID of resource
            
        Returns:
            List of permission strings (e.g., ["read", "write"])
            
        Security:
            - Requires authentication
        """
        self.request_context.require_authentication()
        try:
            grant_result = self.get_grant(user_id, resource_type, resource_id)
            
            if grant_result.success and grant_result.data:
                return grant_result.data.permissions
            
            return []
            
        except:
            return []
    
    def has_permission_on_resource(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        permission: str
    ) -> bool:
        """
        Check if user has a specific permission on a resource.
        
        Args:
            user_id: User ID
            resource_type: Type of resource
            resource_id: ID of resource
            permission: Permission to check (e.g., "write")
            
        Returns:
            True if user has permission, False otherwise
            
        Security:
            - Requires authentication
        """
        self.request_context.require_authentication()
        try:
            perms = self.get_user_permissions_on_resource(
                user_id, resource_type, resource_id
            )
            
            # Check for wildcard or specific permission
            return "*" in perms or permission in perms
            
        except:
            return False
