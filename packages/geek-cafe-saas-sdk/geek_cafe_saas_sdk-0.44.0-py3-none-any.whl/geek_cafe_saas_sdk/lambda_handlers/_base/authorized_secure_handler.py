"""
Authorized Secure Handler with hierarchical routing support.

Extends SecureLambdaHandler to add fine-grained authorization using the
authorization middleware for hierarchical multi-tenant routes.
"""

from typing import Dict, Any, Optional, Callable
from aws_lambda_powertools import Logger

from .secure_handler import SecureLambdaHandler
from geek_cafe_saas_sdk.middleware.authorization import (
    Operation,
    AuthorizationMiddleware,
    extract_auth_context,
    extract_resource_context,
    AuthorizationResult
)

logger = Logger()


class AuthorizedSecureLambdaHandler(SecureLambdaHandler):
    """
    Secure handler with built-in authorization for hierarchical routes.
    
    Use this when:
    - Using hierarchical routes: /tenants/{tid}/users/{uid}/resources/{rid}
    - Need fine-grained authorization (global admin, tenant admin, user)
    - Want automatic tenant isolation and permission checks
    
    The handler:
    1. Validates JWT via API Gateway (inherited from SecureLambdaHandler)
    2. Extracts actor from JWT (who is making request)
    3. Extracts resource from path (what they want to access)
    4. Checks authorization (can actor access resource?)
    5. Calls business logic only if authorized
    
    Example:
        handler = create_handler(
            service_class=MessageService,
            require_authorization=True,  # Enable authorization
            operation=Operation.READ,
            resource_type="message"
        )
        
        def lambda_handler(event, context):
            return handler.execute(event, context, business_logic)
        
        def business_logic(event, service, user_context):
            # Authorization already checked - just implement logic
            message_id = event['pathParameters']['message_id']
            return service.get_by_id(message_id)
    """
    
    def __init__(
        self,
        operation: Optional[Operation] = None,
        resource_type: Optional[str] = None,
        extract_resource_fn: Optional[Callable[[Dict[str, Any]], Any]] = None,
        skip_authorization: bool = False,
        **kwargs
    ):
        """
        Initialize the authorized secure handler.
        
        Args:
            operation: Operation to authorize (READ, WRITE, DELETE, CREATE).
                      If None, inferred from HTTP method.
            resource_type: Type of resource (e.g., "message", "contact_thread")
            extract_resource_fn: Custom function to extract resource context from event
            skip_authorization: Skip authorization check (for backward compatibility)
            **kwargs: Arguments passed to SecureLambdaHandler
        """
        super().__init__(**kwargs)
        self.operation = operation
        self.resource_type = resource_type
        self.extract_resource_fn = extract_resource_fn
        self.skip_authorization = skip_authorization
    
    def _infer_operation(self, event: Dict[str, Any]) -> Operation:
        """Infer operation from HTTP method."""
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
            return Operation.READ  # Default
    
    def _check_authorization(
        self,
        event: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Check if user is authorized to access the resource.
        
        Returns:
            Error response dict if unauthorized, None if authorized
        """
        if self.skip_authorization:
            return None
        
        try:
            # Extract actor from JWT
            actor = extract_auth_context(event)
            
            # Extract resource from path
            if self.extract_resource_fn:
                resource = self.extract_resource_fn(event)
            else:
                resource = extract_resource_context(event, self.resource_type)
            
            # Validate tenant_id is in path
            if not resource.tenant_id:
                logger.warning("Authorization check failed: tenant_id not in path parameters")
                from geek_cafe_saas_sdk.utilities.response import error_response
                return error_response(
                    "tenant_id is required in path parameters",
                    "AUTHORIZATION_ERROR",
                    400
                )
            
            # Determine operation
            operation = self.operation if self.operation else self._infer_operation(event)
            
            # Check authorization
            result: AuthorizationResult = AuthorizationMiddleware.can_perform_operation(
                actor, resource, operation
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
                        'operation': operation.value,
                        'reason': result.reason
                    }
                )
                from geek_cafe_saas_sdk.utilities.response import error_response
                return error_response(
                    "You do not have permission to access this resource",
                    "AUTHORIZATION_DENIED",
                    403,
                    additional_data={'reason': result.reason}
                )
            
            # Authorization passed - add context to event for business logic
            event['authorization_context'] = {
                'actor': actor,
                'resource': resource,
                'operation': operation.value,
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
                    'operation': operation.value,
                    'reason': result.reason
                }
            )
            
            return None  # Authorized
            
        except KeyError as e:
            logger.error(f"Authorization check failed: Missing JWT claim: {e}")
            from geek_cafe_saas_sdk.utilities.response import error_response
            return error_response(
                f"Missing required authentication claim: {str(e)}",
                "AUTHENTICATION_ERROR",
                401
            )
        except Exception as e:
            logger.exception(f"Authorization check failed with unexpected error: {e}")
            from geek_cafe_saas_sdk.utilities.response import error_response
            return error_response(
                "Authorization check failed",
                "AUTHORIZATION_ERROR",
                500
            )
    
    def execute(
        self,
        event: Dict[str, Any],
        context: Any,
        business_logic: Callable[[Dict[str, Any], Any, Dict[str, Any]], Any],
        injected_service: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Execute handler with authorization check.
        
        Overrides parent execute() to add authorization before calling business logic.
        """
        # Check authorization first
        auth_error = self._check_authorization(event)
        if auth_error:
            return auth_error
        
        # Authorization passed - call parent execute (handles everything else)
        return super().execute(event, context, business_logic, injected_service)
