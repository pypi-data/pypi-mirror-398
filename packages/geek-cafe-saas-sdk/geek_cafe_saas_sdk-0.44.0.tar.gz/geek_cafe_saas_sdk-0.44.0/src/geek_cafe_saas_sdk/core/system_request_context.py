"""
System Request Context - For system-triggered operations without user authentication.

This module provides a security context for operations triggered by:
- S3 events (file uploads)
- SQS/SNS messages
- EventBridge scheduled events
- Other system-initiated processes

These operations don't have a JWT token but still need tenant/user context
for proper data isolation and audit trails.
"""

from typing import Optional, List, Any, Dict
from geek_cafe_saas_sdk.core.request_context import RequestContext


class SystemRequestContext(RequestContext):
    """
    Security context for system-triggered operations.
    
    Unlike regular RequestContext (which extracts identity from JWT),
    SystemRequestContext is explicitly constructed with known tenant/user IDs
    derived from the event source (e.g., S3 key path).
    
    Usage:
        # In S3-triggered Lambda
        tenant_id, user_id = parse_from_s3_key(s3_key)
        context = SystemRequestContext(
            tenant_id=tenant_id,
            user_id=user_id,
            source="s3-file-upload"
        )
        
        file_service = FileSystemService(request_context=context)
        result = file_service.save(file=file_model)
    
    Security Model:
        - System context has access ONLY to the tenant it was created for
        - All operations are logged with source identifier for audit
        - No cross-tenant access is permitted
    """
    
    # System user ID used when no specific user is associated
    SYSTEM_USER_ID = "system"
    
    def __init__(
        self,
        tenant_id: str,
        user_id: Optional[str] = None,
        source: str = "system",
        roles: Optional[List[str]] = None,
        permissions: Optional[List[str]] = None,
    ):
        """
        Initialize system request context.
        
        Args:
            tenant_id: Tenant ID for this operation (REQUIRED)
            user_id: User ID associated with this operation (optional, defaults to "system")
            source: Identifier for the trigger source (e.g., "s3-file-upload", "sqs-processor")
            roles: Optional roles to assign (defaults to ["system"])
            permissions: Optional permissions to assign
        """
        # Don't call super().__init__() as it expects a Lambda event
        # Instead, directly set the attributes
        
        if not tenant_id:
            raise ValueError("tenant_id is required for SystemRequestContext")
        
        self._tenant_id = tenant_id
        self._user_id = user_id or self.SYSTEM_USER_ID
        self._source = source
        
        # Set authenticated identity (same as target for system context)
        self.authenticated_user_id: str = self._user_id
        self.authenticated_tenant_id: str = self._tenant_id
        self.authenticated_user_email: Optional[str] = f"{self._source}@system.internal"
        
        # Target is the same as authenticated for system operations
        self.target_tenant_id: str = self._tenant_id
        self.target_user_id: str = self._user_id
        
        # Roles and permissions
        self.roles: List[str] = roles or ["system"]
        self.permissions: List[str] = permissions or []
        self.inboxes: List[str] = []
        
        # System context is never "public" - it always has identity
        self.is_public = False
        
        # No chaos config for system operations
        self._chaos_config = None
        
        # Store user context for compatibility
        self._user_context = {
            'user_id': self._user_id,
            'tenant_id': self._tenant_id,
            'email': self.authenticated_user_email,
            'roles': self.roles,
            'permissions': self.permissions,
            'source': self._source,
        }
    
    @property
    def source(self) -> str:
        """Get the source identifier for this system operation."""
        return self._source
    
    @property
    def is_system_context(self) -> bool:
        """Check if this is a system context (always True for this class)."""
        return True
    
    def validate_tenant_access(self, tenant_id: str) -> bool:
        """
        Validate system context can access the specified tenant.
        
        System context can ONLY access the tenant it was created for.
        No cross-tenant access is permitted.
        
        Args:
            tenant_id: Tenant ID to validate
            
        Returns:
            True if tenant matches, False otherwise
        """
        return tenant_id == self._tenant_id
    
    def is_platform_admin(self) -> bool:
        """System context is not a platform admin."""
        return False
    
    def is_tenant_admin(self) -> bool:
        """System context is not a tenant admin."""
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for logging/debugging."""
        base_dict = super().to_dict()
        base_dict['source'] = self._source
        base_dict['is_system_context'] = True
        return base_dict
    
    def __repr__(self) -> str:
        return f"SystemRequestContext(tenant={self._tenant_id}, user={self._user_id}, source={self._source})"
