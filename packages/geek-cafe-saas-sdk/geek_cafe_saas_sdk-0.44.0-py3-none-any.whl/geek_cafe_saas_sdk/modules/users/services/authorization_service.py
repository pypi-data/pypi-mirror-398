"""
Copyright 2024-2025 Geek Cafe, LLC
MIT License. See Project Root for the license information.

Authorization Service for permission checking with DB lookups and caching.
"""

from typing import List, Set, Optional, Dict, Any
import time
from dataclasses import dataclass
from ....core.service_errors import ValidationError, AccessDeniedError, NotFoundError
from .permission_registry import permission_registry
from geek_cafe_saas_sdk.modules.users.models import User, ResourcePermission


@dataclass
class AuthorizationContext:
    """
    Authorization context for a user.
    Cached per-request to avoid repeated DB lookups.
    """
    user_id: str
    tenant_id: str
    roles: List[str]
    permissions: Set[str]  # Resolved from roles
    resource_grants: Dict[str, Set[str]]  # resource_key -> set of permissions
    plan_tier: str = "free"
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission from roles."""
        # Check for wildcard permission (platform admin)
        if "*:*" in self.permissions or "platform:admin" in self.permissions:
            return True
        
        # Check exact permission
        if permission in self.permissions:
            return True
        
        # Check wildcard category (e.g., "events:*")
        category = permission.split(":")[0] if ":" in permission else ""
        if category and f"{category}:*" in self.permissions:
            return True
        
        return False
    
    def has_resource_permission(self, resource_type: str, resource_id: str, permission: str) -> bool:
        """Check if user has permission on a specific resource."""
        resource_key = f"{resource_type}:{resource_id}"
        resource_perms = self.resource_grants.get(resource_key, set())
        
        # Check for wildcard or specific permission
        return "*" in resource_perms or permission in resource_perms


class AuthorizationService:
    """
    Authorization service for permission checking.
    
    Provides:
    - Role-based permission checks (RBAC)
    - Resource-level permission checks (ABAC)
    - Per-request caching to minimize DB lookups
    - Real-time permission resolution from DB
    """
    
    def __init__(self, db=None, user_service=None, resource_permission_service=None, tenant_service=None):
        """
        Initialize authorization service.
        
        Args:
            db: DynamoDB connection (optional, will create if not provided)
            user_service: UserService instance (optional, will create if not provided)
            resource_permission_service: Service for ResourcePermission (optional)
            tenant_service: TenantService instance (optional, will create if not provided)
        """
        self.db = db
        self.user_service = user_service
        self.resource_permission_service = resource_permission_service
        self.tenant_service = tenant_service
        
        # Per-request cache
        self._request_cache: Dict[str, AuthorizationContext] = {}
    
    def clear_cache(self):
        """Clear the request cache. Call this at the end of each request."""
        self._request_cache.clear()
    
    def get_user_context(self, user_id: str, tenant_id: str) -> AuthorizationContext:
        """
        Get or build authorization context for a user.
        
        Args:
            user_id: User ID
            tenant_id: Tenant ID
            
        Returns:
            AuthorizationContext with resolved permissions
        """
        cache_key = f"{user_id}:{tenant_id}"
        
        # Check cache first
        if cache_key in self._request_cache:
            return self._request_cache[cache_key]
        
        # Load from DB
        context = self._load_user_context(user_id, tenant_id)
        
        # Cache for this request
        self._request_cache[cache_key] = context
        
        return context
    
    def _load_user_context(self, user_id: str, tenant_id: str) -> AuthorizationContext:
        """
        Load user context from database.
        
        Args:
            user_id: User ID
            tenant_id: Tenant ID
            
        Returns:
            AuthorizationContext
        """
        # Import here to avoid circular dependencies
        if self.user_service is None:
            from geek_cafe_saas_sdk.modules.users.services import UserService
            self.user_service = UserService(dynamodb=self.db)
        
        # Set up system context for internal authorization lookups
        # System context has elevated permissions to look up any user for authorization
        from geek_cafe_saas_sdk.core.anonymous_context import AnonymousContextFactory
        self.user_service._request_context = AnonymousContextFactory.create_system_context(
            tenant_id=tenant_id,
            operation_name="authorization_lookup"
        )
        
        # Get user from DB
        user_result = self.user_service.get_by_id(user_id=user_id)
        
        if not user_result.success or not user_result.data:

            if user_result.error_code:
                raise AccessDeniedError(user_result.message)
            
            
            
            # User not found, return minimal context
            return AuthorizationContext(
                user_id=user_id,
                tenant_id=tenant_id,
                roles=[],
                permissions=set(),
                resource_grants={}
            )
        
        user: User = user_result.data
        
        # Resolve permissions from roles
        permissions = set(permission_registry.get_permissions_for_roles(user.roles))
        
        # Load resource-level grants
        resource_grants = self._load_resource_grants(user_id, tenant_id)
        
        # Get plan tier from tenant
        plan_tier = self._load_plan_tier(tenant_id)
        
        return AuthorizationContext(
            user_id=user_id,
            tenant_id=tenant_id,
            roles=user.roles,
            permissions=permissions,
            resource_grants=resource_grants,
            plan_tier=plan_tier
        )
    
    def _load_resource_grants(self, user_id: str, tenant_id: str) -> Dict[str, Set[str]]:
        """
        Load resource-level permission grants for user.
        
        Args:
            user_id: User ID
            tenant_id: Tenant ID
            
        Returns:
            Dict mapping resource_key to set of permissions
        """
        # Import here to avoid circular dependencies
        if self.resource_permission_service is None:
            from geek_cafe_saas_sdk.modules.users.services import ResourcePermissionService
            self.resource_permission_service = ResourcePermissionService(dynamodb=self.db)
        
        # Set up request context for resource permission service call
        from geek_cafe_saas_sdk.core.request_context import RequestContext
        self.resource_permission_service.request_context = RequestContext({
            'user_id': user_id,
            'tenant_id': tenant_id,
            'roles': [],
            'permissions': []
        })
        
        # Load all grants for this user
        grants_result = self.resource_permission_service.list_user_grants(user_id, limit=100)
        
        if not grants_result.success or not grants_result.data:
            return {}
        
        # Build dict mapping resource_key -> set of permissions
        resource_grants: Dict[str, Set[str]] = {}
        
        for grant in grants_result.data:
            resource_key = f"{grant.resource_type}:{grant.resource_id}"
            resource_grants[resource_key] = set(grant.permissions)
        
        return resource_grants
    
    def _load_plan_tier(self, tenant_id: str) -> str:
        """
        Load plan tier from tenant.
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            Plan tier string (free, basic, pro, enterprise)
        """
        # Import here to avoid circular dependencies
        if self.tenant_service is None:
            from geek_cafe_saas_sdk.modules.tenancy.services import TenantService
            self.tenant_service = TenantService(dynamodb=self.db)
        
        # Set up request context for tenant service call
        from geek_cafe_saas_sdk.core.request_context import RequestContext
        self.tenant_service.request_context = RequestContext({
            'user_id': 'system',
            'tenant_id': tenant_id,
            'roles': [],
            'permissions': []
        })
        
        # Get tenant from DB
        tenant_result = self.tenant_service.get_by_id(tenant_id=tenant_id)
        
        if not tenant_result.success or not tenant_result.data:
            return "free"  # Default if tenant not found
        
        return tenant_result.data.plan_tier
    
    def can_user_perform(
        self,
        user_id: str,
        tenant_id: str,
        permission: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None
    ) -> bool:
        """
        Check if user can perform an action.
        
        Args:
            user_id: User ID
            tenant_id: Tenant ID
            permission: Permission code (e.g., "events:write")
            resource_type: Optional resource type for ABAC check
            resource_id: Optional resource ID for ABAC check
            
        Returns:
            True if user has permission, False otherwise
        """
        context = self.get_user_context(user_id, tenant_id)
        
        # First check role-based permissions (RBAC)
        if context.has_permission(permission):
            return True
        
        # If resource specified, check resource-level permissions (ABAC)
        if resource_type and resource_id:
            # Extract action from permission (e.g., "write" from "events:write")
            action = permission.split(":")[-1] if ":" in permission else permission
            
            if context.has_resource_permission(resource_type, resource_id, action):
                return True
        
        return False
    
    def get_user_permissions(self, user_id: str, tenant_id: str) -> List[str]:
        """
        Get all permissions for a user.
        
        Args:
            user_id: User ID
            tenant_id: Tenant ID
            
        Returns:
            List of permission codes
        """
        context = self.get_user_context(user_id, tenant_id)
        return list(context.permissions)
    
    def get_user_roles(self, user_id: str, tenant_id: str) -> List[str]:
        """
        Get all roles for a user.
        
        Args:
            user_id: User ID
            tenant_id: Tenant ID
            
        Returns:
            List of role codes
        """
        context = self.get_user_context(user_id, tenant_id)
        return context.roles
    
    def grant_resource_permission(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        permissions: List[str],
        granted_by: str,
        reason: Optional[str] = None,
        expires_at: Optional[int] = None
    ) -> ResourcePermission:
        """
        Grant resource-level permissions to a user.
        
        Args:
            user_id: User to grant to
            tenant_id: Tenant context
            resource_type: Type of resource
            resource_id: Resource ID
            permissions: List of permissions to grant
            granted_by: User ID who is granting
            reason: Optional reason
            expires_at: Optional expiration timestamp
            
        Returns:
            Created ResourcePermission object
        """
        grant = ResourcePermission()
        grant.user_id = user_id
        grant.tenant_id = tenant_id
        grant.resource_type = resource_type
        grant.resource_id = resource_id
        grant.permissions = permissions
        grant.granted_by = granted_by
        grant.granted_at = int(time.time())
        grant.expires_at = expires_at
        grant.reason = reason
        
        # Import here to avoid circular dependencies
        if self.resource_permission_service is None:
            from geek_cafe_saas_sdk.modules.users.services import ResourcePermissionService
            self.resource_permission_service = ResourcePermissionService(dynamodb=self.db)
        
        # Save to DB
        result = self.resource_permission_service.grant_permission(
            grantee_user_id=user_id,
            tenant_id=tenant_id,
            resource_type=resource_type,
            resource_id=resource_id,
            permissions=permissions,
            granted_by=granted_by,
            reason=reason,
            expires_at=expires_at
        )
        
        # Invalidate cache for this user
        cache_key = f"{user_id}:{tenant_id}"
        self._request_cache.pop(cache_key, None)
        
        if result.success:
            return result.data
        
        return grant
    
    def revoke_resource_permission(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str
    ):
        """
        Revoke resource-level permissions from a user.
        
        Args:
            user_id: User to revoke from
            tenant_id: Tenant context
            resource_type: Type of resource
            resource_id: Resource ID
        """
        # Import here to avoid circular dependencies
        if self.resource_permission_service is None:
            from geek_cafe_saas_sdk.modules.users.services import ResourcePermissionService
            self.resource_permission_service = ResourcePermissionService(dynamodb=self.db)
        
        # Revoke from DB
        self.resource_permission_service.revoke_permission(
            grantee_user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            tenant_id=tenant_id
        )
        
        # Invalidate cache for this user
        cache_key = f"{user_id}:{tenant_id}"
        self._request_cache.pop(cache_key, None)
