"""
Request Context - Security Token Service for Geek Cafe SaaS SDK.

This module provides a centralized security context that tracks:
- Authenticated user (from JWT)
- Target resource (from API path parameters)
- Authorization helpers (roles, permissions, tenancy validation)
- Chaos engineering configuration (for controlled fault injection)
"""

from typing import Dict, List, Optional, Any, TYPE_CHECKING
from geek_cafe_saas_sdk.core.chaos_config import ChaosConfig, extract_chaos_config
from geek_cafe_saas_sdk.core.tenant_settings import (
    TenantSettings, 
    ITenantSettingsLoader, 
    DefaultTenantSettingsLoader
)

if TYPE_CHECKING:
    pass  # For future type imports that would cause circular dependencies


class RequestContext:
    """
    Security token service - single source of truth for request authentication and authorization.
    
    This class automatically extracts and validates:
    - WHO is making the request (authenticated_user_id, authenticated_tenant_id from JWT)
    - WHAT they're trying to access (target_user_id, target_tenant_id from path parameters)
    
    This separation enables proper security validation:
    - Can user A access resources belonging to user B?
    - Can user from tenant X access resources in tenant Y?
    - Does user have required role/permission?
    """
    
    def __init__(self, event_or_user_context: Optional[Dict[str, Any]] = None):
        """
        Initialize request context from Lambda event or JWT payload.
        
        Args:
            event_or_user_context: Either:
                1. Full Lambda event (auto-extracts JWT and path params)
                2. User context dict from JWT (for backward compatibility)
                
                Lambda event should contain:
                - requestContext.authorizer.claims (JWT)
                - pathParameters.tenant-id (optional)
                - pathParameters.user-id (optional)
                
                User context dict should contain:
                - user_id: Authenticated user ID
                - tenant_id: Authenticated user's tenant ID
                - roles: List of role strings
                - permissions: List of permission strings
                - email: User email
                - inboxes: List of inbox IDs (optional)
        """
        event_or_user_context = event_or_user_context or {}
        
        # Determine if this is a Lambda event or user context dict
        is_lambda_event = 'requestContext' in event_or_user_context or 'pathParameters' in event_or_user_context
        
        if is_lambda_event:
            # Extract user context from Lambda event
            self._user_context = self._extract_user_context_from_event(event_or_user_context)
            # Extract path parameters
            path_params = event_or_user_context.get('pathParameters') or {}
        else:
            # Direct user context dict (backward compatibility)
            self._user_context = event_or_user_context
            path_params = {}
        
        # Authenticated user (from JWT)
        self.authenticated_user_id: Optional[str] = self._user_context.get('user_id')
        self.authenticated_tenant_id: Optional[str] = self._user_context.get('tenant_id')
        self.authenticated_user_email: Optional[str] = self._user_context.get('email')
        self.roles: List[str] = self._user_context.get('roles', [])
        self.permissions: List[str] = self._user_context.get('permissions', [])
        self.inboxes: List[str] = self._user_context.get('inboxes', [])
        
        # Target resource (from path parameters - automatically extracted)
        # Default to authenticated user's values if not specified in path
        self.target_tenant_id: Optional[str] = path_params.get('tenant-id') or path_params.get('tenantId') or self.authenticated_tenant_id
        self.target_user_id: Optional[str] = path_params.get('user-id') or path_params.get('userId') or self.authenticated_user_id
        
        # Public endpoint flag (no authentication required)
        self.is_public = self.authenticated_user_id is None
        
        # Chaos engineering configuration (optional, for testing)
        self._chaos_config: Optional[ChaosConfig] = extract_chaos_config(self._user_context)
        
        # Tenant settings (lazy loaded and cached)
        self._tenant_settings: Optional[TenantSettings] = None
        self._tenant_settings_loader: Optional[ITenantSettingsLoader] = None
        self._tenant_settings_loaded: bool = False
    
    def _extract_user_context_from_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract user context from Lambda event structure.
        
        Args:
            event: Lambda event dict
            
        Returns:
            User context dict
        """
        # Try to get from requestContext.authorizer.claims (API Gateway)
        request_context = event.get('requestContext', {})
        authorizer = request_context.get('authorizer', {})
        claims = authorizer.get('claims', {})
        
        if claims:
            # Standard JWT claims structure
            return {
                'user_id': claims.get('sub') or claims.get('user_id'),
                'tenant_id': claims.get('tenant_id'),
                'email': claims.get('email'),
                'roles': claims.get('roles', []),
                'permissions': claims.get('permissions', []),
                'inboxes': claims.get('inboxes', [])
            }
        
        # Fallback: check if user_context is directly in event (test scenarios)
        if 'user_context' in event:
            return event['user_context']
        
        # No authentication found - public endpoint
        return {}
    
    def set_targets(self, tenant_id: Optional[str] = None, user_id: Optional[str] = None):
        """
        Manually set target resource IDs (for backward compatibility or override).
        
        NOTE: Targets are now automatically extracted from event path parameters.
        Only use this if you need to override the auto-detected values.
        
        Args:
            tenant_id: Target tenant ID from path
            user_id: Target user ID from path
        """
        if tenant_id:
            self.target_tenant_id = tenant_id
        if user_id:
            self.target_user_id = user_id
    
    # ========================================
    # Tenant Settings (Cached)
    # ========================================
    
    def set_tenant_settings_loader(self, loader: ITenantSettingsLoader) -> None:
        """
        Set the tenant settings loader for lazy loading.
        
        This should be called early in the request lifecycle (e.g., in Lambda handler
        or middleware) to enable tenant settings lookup.
        
        Args:
            loader: Implementation of ITenantSettingsLoader
        """
        self._tenant_settings_loader = loader
        # Reset cache if loader changes
        self._tenant_settings = None
        self._tenant_settings_loaded = False
    
    def set_tenant_settings(self, settings: TenantSettings) -> None:
        """
        Directly set tenant settings (for testing or pre-loaded scenarios).
        
        Args:
            settings: Pre-loaded TenantSettings
        """
        self._tenant_settings = settings
        self._tenant_settings_loaded = True
    
    @property
    def tenant_settings(self) -> TenantSettings:
        """
        Get cached tenant settings (lazy loaded on first access).
        
        If no loader is configured, returns secure defaults.
        Settings are cached for the lifetime of this RequestContext.
        
        Returns:
            TenantSettings for the authenticated tenant
        """
        if not self._tenant_settings_loaded:
            self._load_tenant_settings()
        
        # Return cached settings or secure defaults
        if self._tenant_settings:
            return self._tenant_settings
        
        # Fallback to secure defaults
        tenant_id = self.authenticated_tenant_id or "unknown"
        return TenantSettings.default(tenant_id)
    
    def _load_tenant_settings(self) -> None:
        """Load tenant settings using the configured loader."""
        self._tenant_settings_loaded = True  # Mark as loaded (even if fails)
        
        if not self.authenticated_tenant_id:
            return  # No tenant to load settings for
        
        if self._tenant_settings_loader:
            try:
                self._tenant_settings = self._tenant_settings_loader.load_settings(
                    self.authenticated_tenant_id
                )
            except Exception:
                # Fail-safe: use defaults on error
                self._tenant_settings = None
    
    @property
    def allow_tenant_wide_access(self) -> bool:
        """
        Whether the tenant allows any user to access any resource in the tenant.
        
        This is a convenience property that reads from cached tenant settings.
        Default: False (strict mode - users can only access owned/shared resources)
        
        Safety: If tenant settings are None or cannot be loaded, defaults to False
        (strict mode) to ensure security is not accidentally bypassed.
        
        Returns:
            True if tenant allows wide access, False for strict mode
        """
        # Safe access - tenant_settings property always returns a valid object
        # (either cached settings or secure defaults with allow_tenant_wide_access=False)
        try:
            return self.tenant_settings.allow_tenant_wide_access
        except Exception:
            # Fail-safe: strict mode if anything goes wrong
            return False
    
    def require_authentication(self):
        """
        Validate that request has valid authentication.
        
        Raises:
            ValueError: If no authenticated user found (public endpoint)
        """
        if self.is_public:
            raise ValueError(
                "Authentication required but not found. "
                "This endpoint requires a valid JWT token. "
                "If this is a test, ensure request_context has authenticated_user_id set."
            )
    
    def require_targets(self):
        """
        Validate that target tenant/user are set.
        
        Raises:
            ValueError: If target values not set
        """
        if not self.target_tenant_id:
            raise ValueError(
                "Target tenant_id required but not found. "
                "Expected in path parameters as 'tenant-id' or set via set_targets(). "
                "If this is a test, ensure path parameters or set_targets() is called."
            )
        if not self.target_user_id:
            raise ValueError(
                "Target user_id required but not found. "
                "Expected in path parameters as 'user-id' or set via set_targets(). "
                "If this is a test, ensure path parameters or set_targets() is called."
            )
    
    # ========================================
    # Tenancy Validation
    # ========================================
    
    def is_same_tenancy(self) -> bool:
        """Check if authenticated user's tenant matches target tenant."""
        if not self.target_tenant_id:
            return True  # No target specified, assume same
        return self.authenticated_tenant_id == self.target_tenant_id
    
    def validate_tenant_access(self, tenant_id: str) -> bool:
        """
        Validate user can access resources in target tenant.
        
        Args:
            tenant_id: Tenant ID to validate
            
        Returns:
            True if access allowed, False otherwise
        """
        # Platform admins can access any tenant
        if self.is_platform_admin():
            return True
        
        # Regular users can only access their own tenant
        return self.authenticated_tenant_id == tenant_id
    
    # ========================================
    # User Access Validation
    # ========================================
    
    def is_self_user(self) -> bool:
        """Check if authenticated user is the same as target user."""
        if not self.target_user_id:
            return True  # No target specified
        return self.authenticated_user_id == self.target_user_id
    
    def can_access_user_resource(self, resource_user_id: str) -> bool:
        """
        Check if user can access a resource owned by another user.
        
        Args:
            resource_user_id: Owner of the resource
            
        Returns:
            True if access allowed
        """
        # Self access
        if self.authenticated_user_id == resource_user_id:
            return True
        
        # Admins can access
        if self.is_platform_admin() or self.is_tenant_admin():
            return True
        
        return False
    
    # ========================================
    # Role Checks
    # ========================================
    
    def has_role(self, role: str) -> bool:
        """Check if user has a specific role."""
        return role in self.roles
    
    def has_any_role(self, roles: List[str]) -> bool:
        """Check if user has any of the specified roles."""
        return any(role in self.roles for role in roles)
    
    def is_platform_admin(self) -> bool:
        """Check if user is a platform admin (can access all tenants)."""
        return 'platform_admin' in self.roles
    
    def is_tenant_admin(self) -> bool:
        """Check if user is admin of their tenant."""
        return 'tenant_admin' in self.roles
    
    def is_admin(self) -> bool:
        """Check if user is any kind of admin."""
        return self.is_platform_admin() or self.is_tenant_admin()
    
    def is_platform_auditor(self) -> bool:
        """Check if user is a platform auditor (can view audit logs across all tenants)."""
        return 'platform_auditor' in self.roles
    
    def is_tenant_auditor(self) -> bool:
        """Check if user is an auditor for their tenant."""
        return 'tenant_auditor' in self.roles
    
    def is_auditor(self) -> bool:
        """Check if user is any kind of auditor."""
        return self.is_platform_auditor() or self.is_tenant_auditor()
    
    def can_view_audit_logs(self) -> bool:
        """Check if user can view audit logs (admin or auditor)."""
        return self.is_admin() or self.is_auditor()
    
    # ========================================
    # Permission Checks
    # ========================================
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission."""
        return permission in self.permissions
    
    def has_any_permission(self, permissions: List[str]) -> bool:
        """Check if user has any of the specified permissions."""
        return any(perm in self.permissions for perm in permissions)
    
    def has_all_permissions(self, permissions: List[str]) -> bool:
        """Check if user has all specified permissions."""
        return all(perm in self.permissions for perm in permissions)
    
    # ========================================
    # Utility Methods
    # ========================================
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for logging/debugging."""
        return {
            'authenticated_user_id': self.authenticated_user_id,
            'authenticated_tenant_id': self.authenticated_tenant_id,
            'authenticated_user_email': self.authenticated_user_email,
            'target_user_id': self.target_user_id,
            'target_tenant_id': self.target_tenant_id,
            'roles': self.roles,
            'permissions': self.permissions,
            'is_admin': self.is_admin(),
            'is_same_tenancy': self.is_same_tenancy(),
            'is_self_user': self.is_self_user(),
        }
    
    # ========================================
    # Chaos Engineering Support
    # ========================================
    
    def should_inject_fault(self, operation: str) -> bool:
        """
        Check if chaos fault should be injected for operation.
        
        Args:
            operation: Operation identifier (e.g., 'file_service.create')
            
        Returns:
            True if fault should be injected
        """
        if not self._chaos_config:
            return False
        return self._chaos_config.should_trigger(operation)
    
    def get_chaos_config(self) -> Optional[ChaosConfig]:
        """
        Get chaos engineering configuration if present.
        
        Returns:
            ChaosConfig or None
        """
        return self._chaos_config
    
    def __repr__(self) -> str:
        chaos_status = "chaos=enabled" if self._chaos_config and self._chaos_config.enabled else ""
        return f"RequestContext(user={self.authenticated_user_id}, tenant={self.authenticated_tenant_id}{', ' + chaos_status if chaos_status else ''})"


    def _is_action_allowed(self) -> bool:
        """Check if action is allowed based on user roles and permissions."""
        
        if self.is_platform_admin():
            return True
        
        # get the current url
        current_url = self.request_context.get("path")
        # get the method (GET, POST, PUT, DELETE)
        method = self.request_context.get("method")

        if self.is_tenant_admin() and self.target_tenant_id == self.authenticated_tenant_id:
            # if we are a tenant admin and we're trying to do something with our own tenant, allow it
            return True
        
        

        if self.target_user_id == self.authenticated_user_id:
            # TODO: detailed permissions
            # for now all actions are allowed, but we'll need to see about things like shares, roles, and any permissions
            return True

        
        # TODO: shares??
        # TODO: roles??

        
        return False