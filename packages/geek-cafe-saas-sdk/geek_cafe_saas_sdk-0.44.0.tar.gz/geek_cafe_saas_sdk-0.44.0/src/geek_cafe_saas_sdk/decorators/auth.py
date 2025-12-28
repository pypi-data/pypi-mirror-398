"""
Authentication and authorization decorators for Lambda handlers.

These decorators integrate with the authorization middleware to provide
fine-grained access control for hierarchical multi-tenant routes.

Design:
- Uses existing authorization middleware (tested, proven)
- Composable with other decorators
- Explicit and readable
- Follows industry patterns (Flask, FastAPI, Django)
"""

import json
import functools
from typing import Callable, Any, Dict, Optional

from aws_lambda_powertools import Logger

from geek_cafe_saas_sdk.middleware.authorization import (
    Operation,
    Permission,
    AuthorizationMiddleware,
    extract_auth_context,
    extract_resource_context,
    AuthorizationResult
)
from geek_cafe_saas_sdk.utilities.response import error_response

logger = Logger()


def require_authorization(
    operation: Optional[Operation] = None,
    resource_type: Optional[str] = None,
    extract_resource_fn: Optional[Callable] = None
) -> Callable:
    """
    Require authorization for handler based on hierarchical route.
    
    Checks:
    - Can actor access target tenant?
    - Can actor access target user's resources?
    - Does actor have permission for operation?
    
    Args:
        operation: Operation to authorize (READ, WRITE, DELETE, CREATE).
                  If None, inferred from HTTP method.
        resource_type: Type of resource (for logging/audit)
        extract_resource_fn: Custom function to extract resource from event
    
    Usage:
        @require_authorization(operation=Operation.READ, resource_type="message")
        def lambda_handler(event, context):
            # Authorization already checked
            message_id = event['pathParameters']['message_id']
            return {'statusCode': 200}
        
        # Auto-infer operation from HTTP method
        @require_authorization(resource_type="message")
        def lambda_handler(event, context):
            # GET -> READ, POST -> CREATE, etc.
            pass
    
    Returns:
        Decorated handler with authorization check
    """
    def decorator(handler: Callable) -> Callable:
        @functools.wraps(handler)
        def wrapper(event: Dict[str, Any], context: Any, *args, **kwargs) -> Dict[str, Any]:
            try:
                # Extract actor from JWT
                actor = extract_auth_context(event)
                
                # Extract resource from path
                if extract_resource_fn:
                    resource = extract_resource_fn(event)
                else:
                    resource = extract_resource_context(event, resource_type)
                
                # Validate tenant_id is in path
                if not resource.tenant_id:
                    logger.warning("Authorization failed: tenant_id not in path parameters")
                    return error_response(
                        "tenant_id is required in path parameters",
                        "AUTHORIZATION_ERROR",
                        400
                    )
                
                # Determine operation (explicit or inferred)
                op = operation
                if op is None:
                    # Infer from HTTP method
                    method = event.get('httpMethod', 'GET').upper()
                    if method == 'GET':
                        op = Operation.READ
                    elif method == 'POST':
                        op = Operation.CREATE
                    elif method in ['PUT', 'PATCH']:
                        op = Operation.WRITE
                    elif method == 'DELETE':
                        op = Operation.DELETE
                    else:
                        op = Operation.READ  # Default
                
                # Check authorization
                result: AuthorizationResult = AuthorizationMiddleware.can_perform_operation(
                    actor, resource, op
                )
                
                if not result.allowed:
                    logger.warning(
                        f"Authorization denied: {result.reason}",
                        extra={
                            'actor_user_id': actor.user_id,
                            'actor_tenant_id': actor.tenant_id,
                            'resource_tenant_id': resource.tenant_id,
                            'resource_user_id': resource.user_id,
                            'resource_id': resource.resource_id,
                            'operation': op.value,
                            'reason': result.reason
                        }
                    )
                    return error_response(
                        f"You do not have permission to access this resource. Reason: {result.reason}",
                        "AUTHORIZATION_DENIED",
                        403
                    )
                
                # Add authorization context to event
                event['authorization_context'] = {
                    'actor': actor,
                    'resource': resource,
                    'operation': op.value,
                    'reason': result.reason,
                    'context': result.context
                }
                
                # Log successful authorization for audit
                logger.info(
                    f"Authorization granted: {result.reason}",
                    extra={
                        'actor_user_id': actor.user_id,
                        'actor_tenant_id': actor.tenant_id,
                        'resource_tenant_id': resource.tenant_id,
                        'resource_user_id': resource.user_id,
                        'resource_id': resource.resource_id,
                        'operation': op.value,
                        'reason': result.reason
                    }
                )
                
                # Authorization passed - call handler
                return handler(event, context, *args, **kwargs)
                
            except KeyError as e:
                logger.error(f"Authorization check failed: Missing JWT claim: {e}")
                return error_response(
                    f"Missing required authentication claim: {str(e)}",
                    "AUTHENTICATION_ERROR",
                    401
                )
            except Exception as e:
                logger.exception(f"Authorization check failed: {e}")
                return error_response(
                    "Authorization check failed",
                    "AUTHORIZATION_ERROR",
                    500
                )
        
        return wrapper
    return decorator


def require_admin(handler: Callable) -> Callable:
    """
    Require admin role (tenant admin or global admin).
    
    This is a convenience decorator that checks for admin roles
    without fine-grained resource-level authorization.
    
    Usage:
        @require_admin
        def lambda_handler(event, context):
            # User is guaranteed to be an admin
            return {'statusCode': 200}
    
    Returns:
        Decorated handler requiring admin role
    """
    @functools.wraps(handler)
    def wrapper(event: Dict[str, Any], context: Any, *args, **kwargs) -> Dict[str, Any]:
        try:
            actor = extract_auth_context(event)
            
            # Check for admin permissions
            is_admin = (
                actor.has_permission(Permission.PLATFORM_ADMIN) or
                actor.has_permission(Permission.TENANT_ADMIN) or
                actor.has_role('admin') or
                actor.has_role('tenant_admin')
            )
            
            if not is_admin:
                logger.warning(
                    f"Admin access denied for user {actor.user_id}",
                    extra={'user_id': actor.user_id, 'tenant_id': actor.tenant_id}
                )
                return error_response(
                    "Admin role required",
                    "ADMIN_REQUIRED",
                    403
                )
            
            # Add auth context to event
            event['authorization_context'] = {
                'actor': actor,
                'reason': 'admin_role'
            }
            
            logger.info(
                f"Admin access granted for user {actor.user_id}",
                extra={'user_id': actor.user_id, 'tenant_id': actor.tenant_id}
            )
            
            return handler(event, context, *args, **kwargs)
            
        except Exception as e:
            logger.exception(f"Admin check failed: {e}")
            return error_response(
                "Authorization check failed",
                "AUTHORIZATION_ERROR",
                500
            )
    
    return wrapper


def require_tenant_admin(handler: Callable) -> Callable:
    """
    Require tenant admin role (admin for their own tenant).
    
    Usage:
        @require_tenant_admin
        def lambda_handler(event, context):
            # User is tenant admin for their tenant
            return {'statusCode': 200}
    
    Returns:
        Decorated handler requiring tenant admin role
    """
    @functools.wraps(handler)
    def wrapper(event: Dict[str, Any], context: Any, *args, **kwargs) -> Dict[str, Any]:
        try:
            actor = extract_auth_context(event)
            
            # Check for tenant admin permission
            is_tenant_admin = (
                actor.has_permission(Permission.TENANT_ADMIN) or
                actor.has_role('tenant_admin')
            )
            
            if not is_tenant_admin:
                logger.warning(
                    f"Tenant admin access denied for user {actor.user_id}",
                    extra={'user_id': actor.user_id, 'tenant_id': actor.tenant_id}
                )
                return error_response(
                    "Tenant admin role required",
                    "TENANT_ADMIN_REQUIRED",
                    403
                )
            
            # Add auth context to event
            event['authorization_context'] = {
                'actor': actor,
                'reason': 'tenant_admin_role'
            }
            
            return handler(event, context, *args, **kwargs)
            
        except Exception as e:
            logger.exception(f"Tenant admin check failed: {e}")
            return error_response(
                "Authorization check failed",
                "AUTHORIZATION_ERROR",
                500
            )
    
    return wrapper


def require_platform_admin(handler: Callable) -> Callable:
    """
    Require platform admin role (platform-level admin).
    
    Usage:
        @require_platform_admin
        def lambda_handler(event, context):
            # User is platform admin
            return {'statusCode': 200}
    
    Returns:
        Decorated handler requiring global admin role
    """
    @functools.wraps(handler)
    def wrapper(event: Dict[str, Any], context: Any, *args, **kwargs) -> Dict[str, Any]:
        try:
            actor = extract_auth_context(event)
            
            # Check for platform admin permission
            is_platform_admin = (
                actor.has_permission(Permission.PLATFORM_ADMIN) or
                actor.has_role('platform_admin')
            )
            
            if not is_platform_admin:
                logger.warning(
                    f"Platform admin access denied for user {actor.user_id}",
                    extra={'user_id': actor.user_id, 'tenant_id': actor.tenant_id}
                )
                return error_response(
                    "Platform admin role required",
                    "PLATFORM_ADMIN_REQUIRED",
                    403
                )
            
            # Add auth context to event
            event['authorization_context'] = {
                'actor': actor,
                'reason': 'platform_admin_role'
            }
            
            logger.info(
                f"Platform admin access granted for user {actor.user_id}",
                extra={'user_id': actor.user_id, 'tenant_id': actor.tenant_id}
            )
            
            return handler(event, context, *args, **kwargs)
            
        except Exception as e:
            logger.exception(f"Platform admin check failed: {e}")
            return error_response(
                "Authorization check failed",
                "AUTHORIZATION_ERROR",
                500
            )
    
    return wrapper


def public(handler: Callable) -> Callable:
    """
    Mark handler as public (no authentication required).
    
    This is primarily a marker decorator for documentation purposes.
    The actual public access must be configured at the API Gateway level.
    
    Usage:
        @public
        def lambda_handler(event, context):
            # Public endpoint - no auth check
            return {'statusCode': 200}
    
    Returns:
        Decorated handler (no actual modification)
    """
    @functools.wraps(handler)
    def wrapper(event: Dict[str, Any], context: Any, *args, **kwargs) -> Dict[str, Any]:
        logger.info("Public endpoint accessed (no authentication required)")
        return handler(event, context, *args, **kwargs)
    
    return wrapper
