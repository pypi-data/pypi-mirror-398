"""
Authorization middleware for hierarchical routing with tenant sharing support.

This module provides centralized authorization logic that supports:
- Multi-tenant access control
- Tenant-to-tenant resource sharing
- Role-based permissions (global admin, tenant admin, user)
- Operation-level access control (read, write, delete)
"""

import json
import functools
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple, Callable
from dataclasses import dataclass, field


class Permission(Enum):
    """System-wide permissions."""
    
    # Platform permissions
    PLATFORM_ADMIN = "platform_admin"
    PLATFORM_READ = "platform_read"
    
    # Tenant permissions
    TENANT_ADMIN = "tenant_admin"
    TENANT_READ = "tenant_read"
    TENANT_WRITE = "tenant_write"
    
    # User permissions
    USER_READ_OWN = "user_read_own"
    USER_WRITE_OWN = "user_write_own"
    USER_READ_OTHERS = "user_read_others"
    USER_WRITE_OTHERS = "user_write_others"
    
    # Shared resource permissions
    USER_READ_SHARED = "user_read_shared"
    USER_WRITE_SHARED = "user_write_shared"


class Operation(Enum):
    """Resource operations."""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    CREATE = "create"


@dataclass
class AuthContext:
    """
    Actor information from JWT.
    
    Represents WHO is making the request and their permissions.
    """
    user_id: str
    tenant_id: str
    roles: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    shared_tenants: List[str] = field(default_factory=list)
    email: Optional[str] = None
    name: Optional[str] = None
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if actor has a specific permission."""
        return permission.value in self.permissions
    
    def has_role(self, role: str) -> bool:
        """Check if actor has a specific role."""
        return role in self.roles
    
    def can_access_tenant(self, tenant_id: str) -> bool:
        """
        Check if actor can access a specific tenant.
        
        Returns True if:
        - It's the actor's own tenant
        - The tenant is in the actor's shared_tenants list
        - The actor has global admin permission
        """
        # Own tenant
        if self.tenant_id == tenant_id:
            return True
        
        # Shared tenant
        if tenant_id in self.shared_tenants:
            return True
        
        # Global admin can access any tenant
        if self.has_permission(Permission.PLATFORM_ADMIN):
            return True
        
        return False
    
    def is_own_tenant(self, tenant_id: str) -> bool:
        """Check if tenant_id is actor's own tenant."""
        return self.tenant_id == tenant_id
    
    def is_shared_tenant(self, tenant_id: str) -> bool:
        """Check if tenant_id is a shared tenant."""
        return tenant_id in self.shared_tenants


@dataclass
class ResourceContext:
    """
    Target resource information from path parameters.
    
    Represents WHAT resource is being accessed.
    """
    tenant_id: str
    user_id: Optional[str] = None
    resource_id: Optional[str] = None
    resource_type: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'tenant_id': self.tenant_id,
            'user_id': self.user_id,
            'resource_id': self.resource_id,
            'resource_type': self.resource_type
        }


@dataclass
class AuthorizationResult:
    """Result of an authorization check."""
    allowed: bool
    reason: str
    context: Optional[Dict[str, Any]] = None
    
    @staticmethod
    def allow(reason: str, context: Optional[Dict[str, Any]] = None) -> 'AuthorizationResult':
        """Create an allow result."""
        return AuthorizationResult(allowed=True, reason=reason, context=context)
    
    @staticmethod
    def deny(reason: str, context: Optional[Dict[str, Any]] = None) -> 'AuthorizationResult':
        """Create a deny result."""
        return AuthorizationResult(allowed=False, reason=reason, context=context)


class AuthorizationMiddleware:
    """
    Centralized authorization logic with support for:
    - Multi-tenant access control
    - Tenant sharing
    - Role-based permissions
    - Operation-level access control
    """
    
    @staticmethod
    def can_access_tenant(actor: AuthContext, target_tenant_id: str) -> AuthorizationResult:
        """
        Check if actor can access target tenant.
        
        Args:
            actor: The actor making the request
            target_tenant_id: The tenant being accessed
            
        Returns:
            AuthorizationResult with allowed status and reason
        """
        # Platform admins can access any tenant
        if actor.has_permission(Permission.PLATFORM_ADMIN):
            return AuthorizationResult.allow("platform_admin")
        
        # Own tenant access
        if actor.is_own_tenant(target_tenant_id):
            return AuthorizationResult.allow("own_tenant")
        
        # Shared tenant access
        if actor.is_shared_tenant(target_tenant_id):
            return AuthorizationResult.allow("shared_tenant")
        
        return AuthorizationResult.deny("tenant_access_denied")
    
    @staticmethod
    def can_access_user(
        actor: AuthContext,
        target_tenant_id: str,
        target_user_id: str
    ) -> AuthorizationResult:
        """
        Check if actor can access target user's data.
        
        Args:
            actor: The actor making the request
            target_tenant_id: The tenant the user belongs to
            target_user_id: The user whose data is being accessed
            
        Returns:
            AuthorizationResult with allowed status and reason
        """
        # Platform admins can access any user
        if actor.has_permission(Permission.PLATFORM_ADMIN):
            return AuthorizationResult.allow("platform_admin")
        
        # Must be able to access the tenant first
        tenant_result = AuthorizationMiddleware.can_access_tenant(actor, target_tenant_id)
        if not tenant_result.allowed:
            return tenant_result
        
        # Own tenant - check additional permissions
        if actor.is_own_tenant(target_tenant_id):
            # Tenant admins can access any user in their tenant
            if actor.has_permission(Permission.TENANT_ADMIN):
                return AuthorizationResult.allow("tenant_admin")
            
            # User accessing their own data
            if actor.user_id == target_user_id:
                return AuthorizationResult.allow("own_user")
            
            # User accessing another user's data (requires special permission)
            if actor.has_permission(Permission.USER_READ_OTHERS):
                return AuthorizationResult.allow("user_read_others")
            
            return AuthorizationResult.deny("user_access_denied")
        
        # Shared tenant - can access if they have shared read permission
        if actor.is_shared_tenant(target_tenant_id):
            if actor.has_permission(Permission.USER_READ_SHARED):
                return AuthorizationResult.allow("shared_tenant_user_access")
            return AuthorizationResult.deny("shared_tenant_permission_required")
        
        return AuthorizationResult.deny("user_access_denied")
    
    @staticmethod
    def can_perform_operation(
        actor: AuthContext,
        resource: ResourceContext,
        operation: Operation
    ) -> AuthorizationResult:
        """
        Check if actor can perform operation on resource.
        
        Args:
            actor: The actor making the request
            resource: The target resource
            operation: The operation to perform
            
        Returns:
            AuthorizationResult with allowed status and reason
        """
        # Platform admins can do anything
        if actor.has_permission(Permission.PLATFORM_ADMIN):
            return AuthorizationResult.allow("platform_admin", {
                'operation': operation.value,
                'resource': resource.to_dict()
            })
        
        # Check tenant-level access
        tenant_result = AuthorizationMiddleware.can_access_tenant(actor, resource.tenant_id)
        if not tenant_result.allowed:
            return tenant_result
        
        # Check user-level access if user_id is specified
        if resource.user_id:
            user_result = AuthorizationMiddleware.can_access_user(
                actor, resource.tenant_id, resource.user_id
            )
            if not user_result.allowed:
                return user_result
        
        # Determine if this is own tenant or shared tenant
        is_own_tenant = actor.is_own_tenant(resource.tenant_id)
        is_shared_tenant = actor.is_shared_tenant(resource.tenant_id)
        
        # Own tenant access rules
        if is_own_tenant:
            # Tenant admin can do anything in their tenant
            if actor.has_permission(Permission.TENANT_ADMIN):
                return AuthorizationResult.allow("tenant_admin", {
                    'operation': operation.value
                })
            
            # User accessing their own resource
            if resource.user_id and resource.user_id == actor.user_id:
                if operation == Operation.READ:
                    if actor.has_permission(Permission.USER_READ_OWN):
                        return AuthorizationResult.allow("user_read_own")
                elif operation in [Operation.WRITE, Operation.DELETE, Operation.CREATE]:
                    if actor.has_permission(Permission.USER_WRITE_OWN):
                        return AuthorizationResult.allow("user_write_own")
            
            # User accessing another user's resource
            if resource.user_id and resource.user_id != actor.user_id:
                if operation == Operation.READ:
                    if actor.has_permission(Permission.USER_READ_OTHERS):
                        return AuthorizationResult.allow("user_read_others")
                elif operation in [Operation.WRITE, Operation.DELETE]:
                    if actor.has_permission(Permission.USER_WRITE_OTHERS):
                        return AuthorizationResult.allow("user_write_others")
            
            # Tenant-level resource (no user_id)
            if not resource.user_id:
                if operation == Operation.READ:
                    if actor.has_permission(Permission.TENANT_READ):
                        return AuthorizationResult.allow("tenant_read")
                elif operation in [Operation.WRITE, Operation.DELETE, Operation.CREATE]:
                    if actor.has_permission(Permission.TENANT_WRITE):
                        return AuthorizationResult.allow("tenant_write")
        
        # Shared tenant access rules
        if is_shared_tenant:
            # Read access to shared resources
            if operation == Operation.READ:
                if actor.has_permission(Permission.USER_READ_SHARED):
                    return AuthorizationResult.allow("shared_read")
                return AuthorizationResult.deny("shared_read_permission_required")
            
            # Write access to shared resources (typically not allowed)
            if operation in [Operation.WRITE, Operation.DELETE, Operation.CREATE]:
                if actor.has_permission(Permission.USER_WRITE_SHARED):
                    return AuthorizationResult.allow("shared_write")
                return AuthorizationResult.deny("shared_resources_readonly")
        
        # Default deny
        return AuthorizationResult.deny("no_permission", {
            'required_operation': operation.value,
            'resource': resource.to_dict()
        })


def extract_auth_context(event: Dict[str, Any]) -> AuthContext:
    """
    Extract AuthContext from API Gateway event.
    
    Args:
        event: API Gateway Lambda event
        
    Returns:
        AuthContext with actor information from JWT
    """
    from .auth import extract_user_context
    
    user_context = extract_user_context(event)
    
    return AuthContext(
        user_id=user_context.get('user_id', ''),
        tenant_id=user_context.get('tenant_id', ''),
        roles=user_context.get('roles', []),
        permissions=user_context.get('permissions', []),
        shared_tenants=user_context.get('shared_tenants', []),
        email=user_context.get('email'),
        name=user_context.get('name')
    )


def extract_resource_context(
    event: Dict[str, Any],
    resource_type: Optional[str] = None
) -> ResourceContext:
    """
    Extract ResourceContext from API Gateway path parameters.
    
    Args:
        event: API Gateway Lambda event
        resource_type: Optional resource type override
        
    Returns:
        ResourceContext with target resource information
    """
    path_params = event.get('pathParameters', {})
    
    # Extract resource_id from various possible parameter names
    resource_id = (
        path_params.get('id') or
        path_params.get('message_id') or
        path_params.get('thread_id') or
        path_params.get('channel_id') or
        path_params.get('resource_id')
    )
    
    return ResourceContext(
        tenant_id=path_params.get('tenant_id', ''),
        user_id=path_params.get('user_id'),
        resource_id=resource_id,
        resource_type=resource_type
    )


def infer_operation(event: Dict[str, Any]) -> Operation:
    """
    Infer operation from HTTP method.
    
    Args:
        event: API Gateway Lambda event
        
    Returns:
        Operation enum value
    """
    method = event.get('httpMethod', 'GET').upper()
    
    if method == 'GET':
        return Operation.READ
    elif method == 'POST':
        return Operation.CREATE
    elif method in ['PUT', 'PATCH']:
        return Operation.WRITE
    elif method == 'DELETE':
        return Operation.DELETE
    else:
        return Operation.READ  # Default to read


def require_authorization(
    operation: Optional[Operation] = None,
    resource_type: Optional[str] = None,
    extract_resource: Optional[Callable[[Dict[str, Any]], ResourceContext]] = None
) -> Callable:
    """
    Decorator for automatic authorization checks on Lambda handlers.
    
    This decorator:
    1. Extracts actor context from JWT
    2. Extracts resource context from path parameters
    3. Checks if actor can perform operation on resource
    4. Returns 403 if unauthorized
    5. Adds authorization context to event for handler use
    
    Args:
        operation: Operation to check (if None, inferred from HTTP method)
        resource_type: Type of resource being accessed
        extract_resource: Custom function to extract ResourceContext from event
        
    Usage:
        @require_authorization(operation=Operation.READ, resource_type="message")
        def lambda_handler(event, context):
            # Authorization already checked
            # Access auth info via event['authorization_context']
            pass
    """
    def decorator(handler_func: Callable) -> Callable:
        @functools.wraps(handler_func)
        def wrapper(event: Dict[str, Any], context: Any, *args, **kwargs) -> Dict[str, Any]:
            try:
                # Extract actor from JWT
                actor = extract_auth_context(event)
                
                # Extract resource from path
                if extract_resource:
                    resource = extract_resource(event)
                else:
                    resource = extract_resource_context(event, resource_type)
                
                # Validate tenant_id is provided in path
                if not resource.tenant_id:
                    return {
                        'statusCode': 400,
                        'headers': {
                            'Content-Type': 'application/json',
                            'Access-Control-Allow-Origin': '*'
                        },
                        'body': json.dumps({
                            'error': 'Bad Request',
                            'message': 'tenant_id is required in path parameters'
                        })
                    }
                
                # Determine operation
                op = operation if operation else infer_operation(event)
                
                # Check authorization
                result = AuthorizationMiddleware.can_perform_operation(actor, resource, op)
                
                if not result.allowed:
                    return {
                        'statusCode': 403,
                        'headers': {
                            'Content-Type': 'application/json',
                            'Access-Control-Allow-Origin': '*'
                        },
                        'body': json.dumps({
                            'error': 'Forbidden',
                            'message': 'You do not have permission to access this resource',
                            'reason': result.reason
                        })
                    }
                
                # Add authorization context to event for handler use
                event['authorization_context'] = {
                    'actor': actor,
                    'resource': resource,
                    'operation': op.value,
                    'reason': result.reason,
                    'context': result.context
                }
                
                # Authorization passed - call handler
                return handler_func(event, context, *args, **kwargs)
                
            except KeyError as e:
                # Missing required JWT claim
                return {
                    'statusCode': 401,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'error': 'Unauthorized',
                        'message': f'Missing required authentication claim: {str(e)}'
                    })
                }
            except Exception as e:
                # Unexpected error during authorization
                return {
                    'statusCode': 500,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'error': 'Internal Server Error',
                        'message': 'Authorization check failed',
                        'detail': str(e)
                    })
                }
        
        return wrapper
    return decorator
