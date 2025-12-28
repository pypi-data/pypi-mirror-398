"""
Lambda handler wrappers for reducing boilerplate in AWS Lambda functions.

This module provides a flexible, composable system for creating Lambda handlers
with built-in support for:
- API key validation
- API Gateway authorization (Cognito/Lambda authorizers)
- Public endpoints (no auth)
- Request/response transformation
- Service initialization and pooling
- Error handling and CORS
- User context extraction

Example Usage with Factory (Recommended):
    from geek_cafe_saas_sdk.lambda_handlers import create_handler
    from geek_cafe_saas_sdk.core.services.vote_service import VoteService
    
    # Factory automatically selects handler based on AUTH_TYPE env var
    # Defaults to secure (API Gateway authorizer) if not set
    handler = create_handler(
        service_class=VoteService,
        require_body=True,
        convert_request_case=True
    )
    
    def lambda_handler(event, context):
        return handler.execute(event, context, business_logic)
    
    def business_logic(event, service, user_context):
        payload = event["parsed_body"]
        return service.create_vote(...)

Environment Configuration:
    AUTH_TYPE=secure    # API Gateway authorizer (default)
    AUTH_TYPE=api_key   # x-api-key header validation
    AUTH_TYPE=public    # No authentication
    
    AUTH_STRICT=true    # Strict validation (default)
    AUTH_STRICT=false   # Permissive for local dev

Direct Usage (if needed):
    from geek_cafe_saas_sdk.lambda_handlers import SecureLambdaHandler
    
    handler = SecureLambdaHandler(
        service_class=VoteService,
        require_body=True
    )
"""

from ._base.base_handler import BaseLambdaHandler
from ._base.api_key_handler import ApiKeyLambdaHandler
from ._base.public_handler import PublicLambdaHandler
from ._base.secure_handler import SecureLambdaHandler
from ._base.authorized_secure_handler import AuthorizedSecureLambdaHandler
from ._base.service_pool import ServicePool
from ._base.handler_factory import HandlerFactory, create_handler
from ._base.lambda_event import LambdaEvent
from ._base.decorators import (
    service_method,
    require_params,
    validate_enum,
    require_ownership,
    cache_result,
)

__all__ = [
    "BaseLambdaHandler",
    "ApiKeyLambdaHandler", 
    "PublicLambdaHandler",
    "SecureLambdaHandler",
    "AuthorizedSecureLambdaHandler",
    "ServicePool",
    "HandlerFactory",
    "create_handler",
    "LambdaEvent",
    "service_method",
    "require_params",
    "validate_enum",
    "require_ownership",
    "cache_result",
]
