"""
Lambda Handler Factory Examples

Demonstrates different patterns for using the handler factory
in various authentication scenarios.
"""

from typing import Dict, Any
from geek_cafe_saas_sdk.lambda_handlers import create_handler, HandlerFactory
from geek_cafe_saas_sdk.core.services.vote_service import VoteService
from geek_cafe_saas_sdk.core.services.event_service import EventService


# ==============================================================================
# Example 1: Recommended Pattern - Factory with Environment Config
# ==============================================================================

# This is the recommended pattern for all new Lambda handlers.
# The factory automatically selects the handler type based on AUTH_TYPE env var:
#   - AUTH_TYPE=secure (default) → API Gateway authorizer
#   - AUTH_TYPE=api_key → x-api-key header validation
#   - AUTH_TYPE=public → No authentication

handler = create_handler(
    service_class=VoteService,
    require_body=True,
    convert_case=True
)

def lambda_handler_example_1(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Standard authenticated endpoint.
    
    In production:
        AUTH_TYPE=secure - Uses API Gateway Cognito/Lambda authorizer
    
    In development:
        AUTH_TYPE=api_key - Uses simple x-api-key validation
        AUTH_STRICT=false - Allows missing keys for local testing
    """
    return handler.execute(event, context, create_vote)


def create_vote(event: Dict[str, Any], service: VoteService, user_context: Dict[str, str]) -> Any:
    """Business logic - all boilerplate handled by factory."""
    payload = event["parsed_body"]
    
    return service.create_single_choice_vote(
        tenant_id=user_context.get("tenant_id", "anonymous"),
        user_id=user_context.get("user_id", "anonymous"),
        target_id=payload["target_id"],
        choice_id=payload["choice_id"],
        available_choices=payload.get("available_choices"),
        content=payload.get("content")
    )


# ==============================================================================
# Example 2: Override Auth Type Per Handler
# ==============================================================================

# Force API key auth regardless of environment
api_key_handler = create_handler(
    service_class=EventService,
    auth_type="api_key",  # Override AUTH_TYPE env var
    require_body=True
)

def lambda_handler_example_2(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Webhook endpoint that always uses API key.
    
    Useful for:
    - Third-party webhooks
    - Internal service-to-service calls
    - Simple authentication without API Gateway
    """
    return api_key_handler.execute(event, context, process_webhook)


def process_webhook(event: Dict[str, Any], service: EventService, user_context: Dict[str, str]) -> Any:
    """Process webhook payload."""
    payload = event["parsed_body"]
    return {"received": True, "event_type": payload.get("type")}


# ==============================================================================
# Example 3: Public Endpoint (No Auth)
# ==============================================================================

public_handler = create_handler(
    auth_type="public",  # No authentication required
    require_body=False,
    service_class=None  # No service needed
)

def lambda_handler_example_3(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Public health check endpoint.
    
    Useful for:
    - Health checks
    - Public configuration
    - Version info
    - Metrics endpoints
    """
    return public_handler.execute(event, context, health_check)


def health_check(event: Dict[str, Any], service: Any, user_context: Dict[str, str]) -> Dict[str, Any]:
    """Return health status."""
    import datetime
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.datetime.now().isoformat()
    }


# ==============================================================================
# Example 4: Using Factory Class Methods
# ==============================================================================

# Explicit factory methods for clarity
secure_handler = HandlerFactory.create_secure(
    service_class=VoteService,
    require_body=True
)

api_key_explicit = HandlerFactory.create_api_key(
    service_class=VoteService,
    api_key_header="x-custom-key",  # Custom header name
    api_key_env_var="CUSTOM_API_KEY"  # Custom env var
)

public_explicit = HandlerFactory.create_public(
    service_class=None
)


def lambda_handler_example_4a(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Secure handler - trusts API Gateway."""
    return secure_handler.execute(event, context, business_logic_secure)


def lambda_handler_example_4b(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """API key with custom configuration."""
    return api_key_explicit.execute(event, context, business_logic_api_key)


def lambda_handler_example_4c(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Public endpoint."""
    return public_explicit.execute(event, context, business_logic_public)


def business_logic_secure(event, service, user_context):
    """Logic for secure endpoint."""
    return {"message": "Authenticated via API Gateway"}


def business_logic_api_key(event, service, user_context):
    """Logic for API key endpoint."""
    return {"message": "Authenticated via custom API key"}


def business_logic_public(event, service, user_context):
    """Logic for public endpoint."""
    return {"message": "No authentication required"}


# ==============================================================================
# Example 5: Development vs Production Configuration
# ==============================================================================

# In your serverless.yml or SAM template:
"""
# Production (API Gateway with Cognito)
functions:
  createVote:
    handler: votes/create/app.lambda_handler
    environment:
      AUTH_TYPE: secure          # API Gateway handles auth
      AUTH_STRICT: true
    events:
      - http:
          path: /votes
          method: post
          authorizer:
            type: COGNITO_USER_POOLS
            authorizerId: ${self:custom.cognitoAuthorizerId}

# Development (API Key)
functions:
  createVote:
    handler: votes/create/app.lambda_handler
    environment:
      AUTH_TYPE: api_key         # Simple key validation
      AUTH_STRICT: false         # Allow testing without key
      API_KEY: ${env:DEV_API_KEY}
    events:
      - http:
          path: /votes
          method: post

# Public endpoint (Health Check)
functions:
  healthCheck:
    handler: health/app.lambda_handler
    environment:
      AUTH_TYPE: public          # No authentication
    events:
      - http:
          path: /health
          method: get
"""


# ==============================================================================
# Example 6: Testing with Dependency Injection
# ==============================================================================

def lambda_handler_testable(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handler designed for easy testing.
    
    The factory and execute() method support dependency injection
    for testing without mocking environment or AWS services.
    """
    return handler.execute(event, context, testable_logic)


def testable_logic(event, service, user_context):
    """Pure business logic - easy to test."""
    payload = event["parsed_body"]
    return service.create_vote(**payload)


# In your tests:
"""
def test_vote_creation():
    from unittest.mock import Mock
    
    # Mock service
    mock_service = Mock()
    mock_service.create_vote.return_value = ServiceResult.success_result({"id": "vote-123"})
    
    # Create event
    event = {
        "body": json.dumps({"target_id": "test", "choice_id": "option1"})
    }
    
    # Execute with injected service
    response = handler.execute(event, None, testable_logic, injected_service=mock_service)
    
    assert response["statusCode"] == 200
"""


# ==============================================================================
# Example 7: Real-World CRUD Handler
# ==============================================================================

crud_handler = create_handler(
    service_class=EventService,
    require_body=True,
    convert_case=True
)


def create_event_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Create event endpoint."""
    return crud_handler.execute(event, context, create_event_logic)


def update_event_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Update event endpoint."""
    return crud_handler.execute(event, context, update_event_logic)


def delete_event_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Delete event endpoint."""
    return crud_handler.execute(event, context, delete_event_logic)


def create_event_logic(event, service: EventService, user_context):
    """Create event business logic."""
    payload = event["parsed_body"]
    
    return service.create(
        tenant_id=user_context["tenant_id"],
        user_id=user_context["user_id"],
        **payload
    )


def update_event_logic(event, service: EventService, user_context):
    """Update event business logic."""
    event_id = event["pathParameters"]["id"]
    payload = event["parsed_body"]
    
    return service.update(
        event_id=event_id,
        tenant_id=user_context["tenant_id"],
        user_id=user_context["user_id"],
        updates=payload
    )


def delete_event_logic(event, service: EventService, user_context):
    """Delete event business logic."""
    event_id = event["pathParameters"]["id"]
    
    return service.delete(
        event_id=event_id,
        tenant_id=user_context["tenant_id"],
        user_id=user_context["user_id"]
    )


# ==============================================================================
# Summary
# ==============================================================================

"""
Key Takeaways:

1. **Use create_handler() for everything**
   - Factory handles auth selection via AUTH_TYPE env var
   - Defaults to secure (API Gateway authorizer)
   - Easy to override per handler or environment

2. **Environment Configuration**
   - AUTH_TYPE: secure, api_key, or public
   - AUTH_STRICT: true/false for validation strictness
   
3. **Production Best Practice**
   - Use AUTH_TYPE=secure with API Gateway authorizer (Cognito/Lambda)
   - Handler trusts API Gateway did the authentication
   - Zero authentication logic in Lambda code

4. **Development/Testing**
   - Use AUTH_TYPE=api_key for simple key validation
   - Use AUTH_STRICT=false for permissive local testing
   - Override auth_type parameter in tests

5. **Zero Boilerplate**
   - No decorators needed
   - No manual parsing
   - No service initialization
   - Just write business logic

6. **Type Safe**
   - Full type hints
   - IDE autocomplete
   - Type checking support
"""
