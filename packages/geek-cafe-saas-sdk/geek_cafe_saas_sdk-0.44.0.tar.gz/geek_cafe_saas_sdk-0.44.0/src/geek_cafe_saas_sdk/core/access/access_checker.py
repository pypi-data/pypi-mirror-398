"""
Access Checker - Centralized access validation for resources.

This module provides a unified interface for checking resource access
that considers:
- Direct ownership (owner_id matches user)
- Tenant membership (same tenant)
- Resource shares (shared via ResourceShare)
- Admin privileges (platform_admin, tenant_admin)

Design Principles:
- Single Responsibility: Only handles access checking logic
- Open/Closed: Extensible via IShareChecker protocol
- Dependency Inversion: Depends on abstractions (protocols), not concrete implementations

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Protocol, runtime_checkable, Any, Dict, List


class AccessLevel(str, Enum):
    """Permission levels for resource access."""
    NONE = "none"
    VIEW = "view"
    DOWNLOAD = "download"
    EDIT = "edit"
    OWNER = "owner"  # Full access as owner
    ADMIN = "admin"  # Full access as admin


@dataclass
class AccessResult:
    """Result of an access check."""
    granted: bool
    level: AccessLevel
    reason: str
    share_id: Optional[str] = None  # If access via share, the share ID
    
    @classmethod
    def denied(cls, reason: str) -> "AccessResult":
        """Create a denied result."""
        return cls(granted=False, level=AccessLevel.NONE, reason=reason)
    
    @classmethod
    def granted_as_owner(cls) -> "AccessResult":
        """Create a granted result for owner access."""
        return cls(granted=True, level=AccessLevel.OWNER, reason="owner")
    
    @classmethod
    def granted_as_admin(cls, admin_type: str = "admin") -> "AccessResult":
        """Create a granted result for admin access."""
        return cls(granted=True, level=AccessLevel.ADMIN, reason=admin_type)
    
    @classmethod
    def granted_via_share(cls, level: AccessLevel, share_id: str) -> "AccessResult":
        """Create a granted result for shared access."""
        return cls(granted=True, level=level, reason="shared", share_id=share_id)
    
    def has_permission(self, required: AccessLevel) -> bool:
        """Check if this access level satisfies the required level."""
        if not self.granted:
            return False
        
        # Owner and Admin have full access
        if self.level in (AccessLevel.OWNER, AccessLevel.ADMIN):
            return True
        
        # Permission hierarchy: edit > download > view
        hierarchy = {
            AccessLevel.NONE: 0,
            AccessLevel.VIEW: 1,
            AccessLevel.DOWNLOAD: 2,
            AccessLevel.EDIT: 3,
            AccessLevel.OWNER: 4,
            AccessLevel.ADMIN: 4
        }
        return hierarchy.get(self.level, 0) >= hierarchy.get(required, 0)


@runtime_checkable
class IShareChecker(Protocol):
    """
    Protocol for checking resource shares.
    
    This abstraction allows DatabaseService to check shares without
    directly depending on ResourceShareService, avoiding circular imports.
    
    Implementations:
    - ResourceShareChecker: Uses ResourceShareService (production)
    - NoOpShareChecker: Always returns no share (testing/disabled)
    """
    
    def check_share(
        self,
        resource_id: str,
        user_id: str,
        tenant_id: str,
        required_permission: str = "view"
    ) -> Optional[Dict[str, Any]]:
        """
        Check if user has access to resource via sharing.
        
        Args:
            resource_id: The resource ID to check
            user_id: The user requesting access
            tenant_id: The tenant context
            required_permission: Required permission level (view, download, edit)
            
        Returns:
            Dict with share info if access granted, None otherwise.
            Dict should contain: share_id, permission_level, reason
        """
        ...


class NoOpShareChecker:
    """
    No-op implementation of IShareChecker.
    
    Always returns None (no share found). Used when:
    - Share checking is disabled
    - Testing without share dependencies
    - Bootstrap scenarios before ResourceShareService is available
    """
    
    def check_share(
        self,
        resource_id: str,
        user_id: str,
        tenant_id: str,
        required_permission: str = "view"
    ) -> Optional[Dict[str, Any]]:
        """Always returns None - no share checking."""
        return None


class AccessChecker:
    """
    Centralized access validation for resources.
    
    Checks access in the following order (first match wins):
    1. Platform admin - full access to all resources
    2. Tenant admin - full access within their tenant
    3. Owner - full access to owned resources
    4. Shared access - permission-based access via ResourceShare
    5. Same tenant - configurable (some resources allow tenant-wide access)
    
    Usage:
        # In DatabaseService or any service
        checker = AccessChecker(
            request_context=self._request_context,
            share_checker=self._share_checker  # Optional
        )
        
        result = checker.check_access(
            resource_id=file.id,
            resource_owner_id=file.owner_id,
            resource_tenant_id=file.tenant_id,
            required_permission=AccessLevel.VIEW
        )
        
        if not result.granted:
            raise AccessDeniedError(result.reason)
    """
    
    def __init__(
        self,
        request_context: Any,  # RequestContext or Callable[[], RequestContext]
        share_checker: Optional[IShareChecker] = None
    ):
        """
        Initialize AccessChecker.
        
        Args:
            request_context: The current request context with auth info.
                Can be a RequestContext instance or a callable that returns one.
                Using a callable ensures the checker always uses the current context
                even if it's refreshed (e.g., in Lambda handler injection scenarios).
            share_checker: Optional share checker for resource sharing support
        """
        self._request_context_source = request_context
        self._share_checker = share_checker or NoOpShareChecker()
    
    @property
    def _request_context(self) -> Any:
        """Get the current request context (supports both direct and callable sources)."""
        if callable(self._request_context_source):
            return self._request_context_source()
        return self._request_context_source
    
    # Default fields that grant access - models can override via _access_fields
    DEFAULT_ACCESS_FIELDS = ['owner_id', 'created_by_id', 'user_id', 'recipient_id', 'account_holder_id']
    
    def check_model_access(
        self,
        model: Any,
        required_permission: AccessLevel = AccessLevel.VIEW
    ) -> AccessResult:
        """
        Check if current user can access a model instance.
        
        This is the PRIMARY method for access checking. It extracts access-granting
        fields from the model and checks if the authenticated user matches any of them.
        
        Access is granted if the user matches ANY of these (in order):
        1. System context (internal operations)
        2. Platform admin
        3. Tenant admin (within same tenant)
        4. Any access field on the model (owner_id, user_id, recipient_id, etc.)
        5. Self-access (model.id == user_id, for User-type models)
        6. Resource shares
        7. Tenant-wide access (if enabled)
        
        Args:
            model: The model instance to check access for
            required_permission: Required permission level (VIEW, EDIT, etc.)
            
        Returns:
            AccessResult with granted status and reason
        """
        user_id = self._request_context.authenticated_user_id
        user_tenant_id = self._request_context.authenticated_tenant_id
        resource_id = getattr(model, 'id', None)
        resource_tenant_id = getattr(model, 'tenant_id', None)
        
        # 1. System context - internal operations bypass security
        if self._is_system_context():
            return AccessResult.granted_as_admin("system")
        
        # 2. Platform admin - full access everywhere
        if self._request_context.is_platform_admin():
            return AccessResult.granted_as_admin("platform_admin")
        
        # 3. Tenant admin - full access within their tenant
        if self._request_context.is_tenant_admin():
            if resource_tenant_id == user_tenant_id:
                return AccessResult.granted_as_admin("tenant_admin")
        
        # Determine if same tenant for subsequent checks
        is_same_tenant = (
            resource_tenant_id is None or  # System/global resource (no tenant)
            resource_tenant_id == user_tenant_id
        )
        
        # 4. Check access fields on model (ONLY for same tenant)
        # Cross-tenant access via fields would be a security issue
        # Models can define _access_fields to specify which fields grant access
        if is_same_tenant:
            access_fields = getattr(model, '_access_fields', None) or self.DEFAULT_ACCESS_FIELDS
            for field_name in access_fields:
                field_value = getattr(model, field_name, None)
                if field_value and field_value == user_id:
                    return AccessResult.granted_as_owner()  # Any matching field grants owner-level access
            
            # 5. Self-access - for User-type models where model.id IS the user
            if resource_id and resource_id == user_id:
                return AccessResult.granted_as_owner()
        
        # 6. Check resource shares (works for BOTH same-tenant AND cross-tenant)
        # This enables cross-tenant sharing - a resource can be shared with
        # users in other tenants via explicit ResourceShare records
        if self._share_checker and resource_id:
            share_info = self._share_checker.check_share(
                resource_id=resource_id,
                user_id=user_id,
                tenant_id=user_tenant_id,
                required_permission=required_permission.value
            )
            if share_info and share_info.get("has_access"):
                permission = share_info.get("permission", "view")
                share_level = AccessLevel(permission) if permission in AccessLevel.__members__.values() else AccessLevel.VIEW
                return AccessResult.granted_via_share(
                    level=share_level,
                    share_id=share_info.get("share_id", "")
                )
        
        # 7. Tenant-wide access (only for same tenant)
        if is_same_tenant and self._request_context.allow_tenant_wide_access:
            return AccessResult(
                granted=True,
                level=AccessLevel.VIEW,
                reason="tenant_wide_access"
            )
        
        # 8. Cross-tenant without share - deny
        if not is_same_tenant:
            return AccessResult.denied("cross_tenant_requires_share")
        
        # 9. No access - same tenant but no specific permission
        return AccessResult.denied("no_access")
    
    def _is_system_context(self) -> bool:
        """Check if the current context is a system context."""
        return (
            'system' in getattr(self._request_context, 'roles', []) or
            getattr(self._request_context, 'authenticated_user_id', None) == 'system'
        )

    def check_access(
        self,
        resource_id: str,
        resource_owner_id: Optional[str],
        resource_tenant_id: Optional[str],
        required_permission: AccessLevel = AccessLevel.VIEW,
        allow_tenant_access: bool = False
    ) -> AccessResult:
        """
        Check if current user can access a resource (legacy method).
        
        PREFER check_model_access() when you have the model instance.
        This method is kept for backward compatibility and edge cases
        where only IDs are available.
        
        Args:
            resource_id: The resource ID
            resource_owner_id: The owner's user ID (None if no owner concept)
            resource_tenant_id: The resource's tenant ID
            required_permission: Required permission level
            allow_tenant_access: If True, any user in same tenant can access
            
        Returns:
            AccessResult with granted status and reason
        """
        user_id = self._request_context.authenticated_user_id
        user_tenant_id = self._request_context.authenticated_tenant_id
        
        # 1. System context - internal operations bypass security
        if self._is_system_context():
            return AccessResult.granted_as_admin("system")
        
        # 2. Platform admin - full access everywhere
        if self._request_context.is_platform_admin():
            return AccessResult.granted_as_admin("platform_admin")
        
        # 3. Tenant admin - full access within their tenant
        if self._request_context.is_tenant_admin():
            if resource_tenant_id == user_tenant_id:
                return AccessResult.granted_as_admin("tenant_admin")
        
        # 4. Owner - full access to owned resources
        if resource_owner_id and resource_owner_id == user_id:
            return AccessResult.granted_as_owner()
        
        # 5. Self-access - for User-type models where resource_id IS the user
        if resource_id and resource_id == user_id:
            return AccessResult.granted_as_owner()
        
        # 6. Check resource shares
        if self._share_checker:
            share_info = self._share_checker.check_share(
                resource_id=resource_id,
                user_id=user_id,
                tenant_id=user_tenant_id,
                required_permission=required_permission.value
            )
            if share_info and share_info.get("has_access"):
                permission = share_info.get("permission", "view")
                share_level = AccessLevel(permission) if permission in AccessLevel.__members__.values() else AccessLevel.VIEW
                return AccessResult.granted_via_share(
                    level=share_level,
                    share_id=share_info.get("share_id", "")
                )
        
        # 7. Same tenant access (if allowed)
        if allow_tenant_access and resource_tenant_id == user_tenant_id:
            return AccessResult(
                granted=True,
                level=AccessLevel.VIEW,
                reason="same_tenant"
            )
        
        # 8. Tenant-wide access (check tenant settings)
        if self._request_context.allow_tenant_wide_access:
            if resource_tenant_id == user_tenant_id:
                return AccessResult(
                    granted=True,
                    level=AccessLevel.VIEW,
                    reason="tenant_wide_access"
                )
        
        # 9. Cross-tenant check - deny if different tenant
        if resource_tenant_id and resource_tenant_id != user_tenant_id:
            return AccessResult.denied("cross_tenant_access_denied")
        
        # 10. No access
        return AccessResult.denied("no_access")
    
    def require_access(
        self,
        resource_id: str,
        resource_owner_id: Optional[str],
        resource_tenant_id: Optional[str],
        required_permission: AccessLevel = AccessLevel.VIEW,
        allow_tenant_access: bool = False
    ) -> AccessResult:
        """
        Check access and raise exception if denied.
        
        Same as check_access but raises AccessDeniedError if access is denied.
        
        Raises:
            AccessDeniedError: If access is denied
        """
        from ..service_errors import AccessDeniedError
        
        result = self.check_access(
            resource_id=resource_id,
            resource_owner_id=resource_owner_id,
            resource_tenant_id=resource_tenant_id,
            required_permission=required_permission,
            allow_tenant_access=allow_tenant_access
        )
        
        if not result.granted:
            raise AccessDeniedError(
                f"Access denied: {result.reason}. "
                f"Required permission: {required_permission.value}"
            )
        
        return result
    
    def can_view(
        self,
        resource_id: str,
        resource_owner_id: Optional[str],
        resource_tenant_id: Optional[str]
    ) -> bool:
        """Convenience method: Check if user can view resource."""
        return self.check_access(
            resource_id, resource_owner_id, resource_tenant_id,
            AccessLevel.VIEW
        ).granted
    
    def can_edit(
        self,
        resource_id: str,
        resource_owner_id: Optional[str],
        resource_tenant_id: Optional[str]
    ) -> bool:
        """Convenience method: Check if user can edit resource."""
        return self.check_access(
            resource_id, resource_owner_id, resource_tenant_id,
            AccessLevel.EDIT
        ).granted
    
    def can_delete(
        self,
        resource_id: str,
        resource_owner_id: Optional[str],
        resource_tenant_id: Optional[str]
    ) -> bool:
        """Convenience method: Check if user can delete resource (requires owner/admin)."""
        result = self.check_access(
            resource_id, resource_owner_id, resource_tenant_id,
            AccessLevel.OWNER
        )
        # Only owner or admin can delete
        return result.level in (AccessLevel.OWNER, AccessLevel.ADMIN)
