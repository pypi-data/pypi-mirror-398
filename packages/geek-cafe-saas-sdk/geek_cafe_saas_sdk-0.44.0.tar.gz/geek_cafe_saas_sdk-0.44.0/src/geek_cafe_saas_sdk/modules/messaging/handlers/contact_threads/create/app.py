"""
Lambda handler for creating contact threads.

Supports both guest contact forms (API key auth) and authenticated users.
Auth strategy is controlled by AUTH_TYPE environment variable:
- AUTH_TYPE=api_key - For public contact forms (validates x-api-key)
- AUTH_TYPE=secure - For authenticated app users (API Gateway authorizer)
"""

from typing import Dict, Any
from geek_cafe_saas_sdk.lambda_handlers import create_handler, LambdaEvent
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.modules.messaging.services import ContactThreadService

# Factory automatically selects handler based on AUTH_TYPE env var
handler_wrapper = create_handler(
    service_class=ContactThreadService,
    require_body=True,
    convert_request_case=True
)


def lambda_handler(event: Dict[str, Any], context: Any, injected_service=None) -> Dict[str, Any]:
    """
    Create a new contact thread.
    
    Two deployment modes:
    
    1. Public Contact Form (AUTH_TYPE=api_key):
       - Validates x-api-key header
       - Creates contact from guest/anonymous user
       - Used for website contact forms
    
    2. Authenticated App (AUTH_TYPE=secure):
       - Trusts API Gateway Cognito authorizer
       - Creates contact from logged-in user
       - Used for in-app support tickets
    
    Args:
        event: Lambda event from API Gateway
        context: Lambda context
        injected_service: Optional ContactThreadService for testing
    
    Expected body (camelCase from frontend):
    {
        "subject": "Contact inquiry",
        "sender": {
            "id": "guest-session-xyz",
            "name": "John Doe",
            "email": "john@example.com"
        },
        "initialMessage": "Message content",
        "inboxId": "support" | "sales" | "billing",
        "priority": "low" | "medium" | "high" | "urgent",
        "source": "web" | "mobile" | "api"
    }
    
    Returns 201 with created contact thread
    """
    return handler_wrapper.execute(event, context, create_contact_thread, injected_service)


def create_contact_thread(event: LambdaEvent, service: ContactThreadService) -> ServiceResult:
    """
    Business logic for creating contact threads.
    
    Handles both guest users (API key) and authenticated users (Cognito).
    """
    payload = event.body()

    # Create the contact thread
    # Service uses request_context for tenant_id and user_id
    result = service.create(payload=payload)

    return result
