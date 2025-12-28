"""
Factory for creating Lambda handlers based on configuration.

Centralizes handler selection logic and provides a single point
for configuring authentication strategy across all Lambda functions.
"""

import os
from typing import Optional, Type, TypeVar, Any, TYPE_CHECKING
from aws_lambda_powertools import Logger

from .base_handler import BaseLambdaHandler
from .api_key_handler import ApiKeyLambdaHandler
from .public_handler import PublicLambdaHandler
from .secure_handler import SecureLambdaHandler
from .authorized_secure_handler import AuthorizedSecureLambdaHandler
from .environment_loader import load_environment

if TYPE_CHECKING:
    from geek_cafe_saas_sdk.core.services_container import ServicesContainer

logger = Logger()

T = TypeVar('T')  # Service type


class HandlerFactory:
    """
    Factory for creating Lambda handlers with appropriate authentication.
    
    Configuration via environment variables:
    
    - AUTH_TYPE (default: "secure"):
        - "secure": Uses API Gateway authorizer (Cognito/Lambda/IAM)
        - "api_key": Validates x-api-key header against API_KEY env var
        - "public": No authentication required
        - "none": Alias for "public"
    
    - AUTH_STRICT (default: "true"):
        - "true": Strict validation, fail if auth is missing
        - "false": Permissive mode for local dev/testing
    
    Usage:
        # Simple usage - defaults to secure handler
        handler = HandlerFactory.create(
            service_class=VoteService,
            require_body=True
        )
        
        # Explicit type
        handler = HandlerFactory.create(
            service_class=VoteService,
            auth_type="api_key",  # Override environment
            require_body=True
        )
        
        # Public endpoint
        handler = HandlerFactory.create_public(
            service_class=ConfigService
        )
        
        # In lambda function
        def lambda_handler(event, context):
            return handler.execute(event, context, business_logic)
    """
    
    # Auth type constants
    AUTH_TYPE_SECURE = "secure"
    AUTH_TYPE_API_KEY = "api_key"
    AUTH_TYPE_PUBLIC = "public"
    AUTH_TYPE_NONE = "none"  # Alias for public
    
    # Environment variable names
    ENV_AUTH_TYPE = "AUTH_TYPE"
    ENV_AUTH_STRICT = "AUTH_STRICT"
    
    @classmethod
    def create(
        cls,
        service_class: Optional[Type[T]] = None,
        services_container: Optional['ServicesContainer'] = None,
        auth_type: Optional[str] = None,
        strict: Optional[bool] = None,
        require_authorization: bool = False,
        operation: Optional[Any] = None,
        resource_type: Optional[str] = None,
        environment_file: Optional[str] = None,
        **handler_kwargs
    ) -> BaseLambdaHandler:
        """
        Create a handler with appropriate authentication and optional authorization.
        
        Args:
            service_class: Service class to instantiate
            services_container: ServicesContainer with security, audit, etc. (NEW)
            auth_type: Override AUTH_TYPE env var ("secure", "api_key", "public")
            strict: Override AUTH_STRICT env var (True/False)
            require_authorization: Enable fine-grained authorization for hierarchical routes
            operation: Operation to authorize (Operation.READ, etc.). If None, inferred from HTTP method
            resource_type: Type of resource for authorization (e.g., "message", "contact_thread")
            environment_file: Path to environment file to load (optional)
            **handler_kwargs: Additional arguments for handler (require_body, etc.)
            
        Returns:
            Configured handler instance
        
        Examples:
            # Simple secure handler (existing behavior)
            handler = HandlerFactory.create(service_class=MessageService)
            
            # With authorization for hierarchical routes
            handler = HandlerFactory.create(
                service_class=MessageService,
                require_authorization=True,
                operation=Operation.READ,
                resource_type="message"
            )
        """
        if environment_file:
            from geek_cafe_saas_sdk.lambda_handlers._base.environment_loader import load_environment
            load_environment(environment_file=environment_file)

        # Get auth type from args or environment
        if auth_type is None:
            auth_type = os.getenv(cls.ENV_AUTH_TYPE, cls.AUTH_TYPE_SECURE).lower()
        else:
            auth_type = auth_type.lower()
        
        # Get strict mode
        if strict is None:
            strict_str = os.getenv(cls.ENV_AUTH_STRICT, "true").lower()
            strict = strict_str in ("true", "1", "yes")
        
        # Log configuration
        logger.info(
            f"Creating handler with auth_type={auth_type}, strict={strict}, "
            f"service={service_class.__name__ if service_class else 'None'}"
        )
        
        # Prepare service kwargs, including the system inbox ID if applicable
        service_kwargs = {}
        if service_class and hasattr(service_class, '__init__') and 'system_inbox_id' in service_class.__init__.__code__.co_varnames:
            service_kwargs['system_inbox_id'] = os.getenv('SYSTEM_INBOX_ID', 'support-inbox')

        # Create appropriate handler (pass services_container to all)
        if auth_type == cls.AUTH_TYPE_API_KEY:
            return ApiKeyLambdaHandler(
                service_class=service_class,
                service_kwargs=service_kwargs,
                services_container=services_container,
                **handler_kwargs
            )
        elif auth_type in (cls.AUTH_TYPE_PUBLIC, cls.AUTH_TYPE_NONE):
            return PublicLambdaHandler(
                service_class=service_class,
                service_kwargs=service_kwargs,
                services_container=services_container,
                **handler_kwargs
            )
        elif auth_type == cls.AUTH_TYPE_SECURE:
            # Use AuthorizedSecureLambdaHandler if authorization is required
            if require_authorization:
                return AuthorizedSecureLambdaHandler(
                    service_class=service_class,
                    service_kwargs=service_kwargs,
                    services_container=services_container,
                    require_authorizer_claims=strict,
                    operation=operation,
                    resource_type=resource_type,
                    **handler_kwargs
                )
            else:
                return SecureLambdaHandler(
                    service_class=service_class,
                    service_kwargs=service_kwargs,
                    services_container=services_container,
                    require_authorizer_claims=strict,
                    **handler_kwargs
                )
        else:
            logger.warning(
                f"Unknown auth_type '{auth_type}', defaulting to secure handler"
            )
            # Use AuthorizedSecureLambdaHandler if authorization is required
            if require_authorization:
                return AuthorizedSecureLambdaHandler(
                    service_class=service_class,
                    service_kwargs=service_kwargs,
                    services_container=services_container,
                    require_authorizer_claims=strict,
                    operation=operation,
                    resource_type=resource_type,
                    **handler_kwargs
                )
            else:
                return SecureLambdaHandler(
                    service_class=service_class,
                    service_kwargs=service_kwargs,
                    services_container=services_container,
                    require_authorizer_claims=strict,
                    **handler_kwargs
                )
    
    @classmethod
    def create_secure(
        cls,
        service_class: Optional[Type[T]] = None,
        **handler_kwargs
    ) -> SecureLambdaHandler:
        """
        Create a secure handler (API Gateway authorizer).
        
        Convenience method that explicitly creates a secure handler
        regardless of environment configuration.
        """
        return SecureLambdaHandler(
            service_class=service_class,
            **handler_kwargs
        )
    
    @classmethod
    def create_api_key(
        cls,
        service_class: Optional[Type[T]] = None,
        **handler_kwargs
    ) -> ApiKeyLambdaHandler:
        """
        Create an API key handler.
        
        Convenience method that explicitly creates an API key handler
        regardless of environment configuration.
        """
        return ApiKeyLambdaHandler(
            service_class=service_class,
            **handler_kwargs
        )
    
    @classmethod
    def create_public(
        cls,
        service_class: Optional[Type[T]] = None,
        **handler_kwargs
    ) -> PublicLambdaHandler:
        """
        Create a public handler (no auth).
        
        Convenience method that explicitly creates a public handler
        regardless of environment configuration.
        """
        return PublicLambdaHandler(
            service_class=service_class,
            **handler_kwargs
        )


# Convenience function for quick handler creation
def create_handler(
    service_class: Optional[Type[T]] = None,
    **kwargs
) -> BaseLambdaHandler:
    """
    Convenience function for creating handlers.
    
    Equivalent to HandlerFactory.create()
    
    Example:
        from geek_cafe_saas_sdk.lambda_handlers import create_handler
        
        handler = create_handler(
            service_class=VoteService,
            require_body=True
        )
    """
    return HandlerFactory.create(service_class=service_class, **kwargs)
