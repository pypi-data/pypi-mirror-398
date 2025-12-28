"""
Real-world examples: Lambda handlers using decorator pattern.

This file shows complete, production-ready handlers using the decorator
pattern for authorization, error handling, CORS, etc.

Pattern:
    @handle_errors              # Catch exceptions → error responses
    @add_cors()                 # Add CORS headers
    @require_authorization(...) # Check authorization
    @parse_request_body(...)    # Parse JSON body
    @validate_path_params(...)  # Validate path params
    @inject_service(...)        # Inject service instance
    def lambda_handler(event, context, service):
        # Pure business logic - no HTTP concerns
        pass
"""

import json
from typing import Dict, Any

from geek_cafe_saas_sdk.decorators import (
    handle_errors,
    add_cors,
    parse_request_body,
    inject_service,
    log_execution,
    validate_path_params,
    require_authorization,
    require_admin,
    require_platform_admin,
    public
)
from geek_cafe_saas_sdk.middleware.authorization import Operation
from geek_cafe_saas_sdk.core.services.message_service import MessageService
from geek_cafe_saas_sdk.core.services.contact_thread_service import ContactThreadService


# =============================================================================
# Example 1: GET Handler - Read Message
# =============================================================================

@handle_errors
@add_cors()
@require_authorization(operation=Operation.READ, resource_type="message")
@validate_path_params(['tenant_id', 'user_id', 'message_id'])
@inject_service(MessageService)
def get_message_handler(event: Dict[str, Any], context: Any, service: MessageService) -> Dict[str, Any]:
    """
    GET /tenants/{tenant_id}/users/{user_id}/messages/{message_id}
    
    Decorators handle:
    - Error handling (exceptions → 500 responses)
    - CORS headers (Access-Control-Allow-Origin)
    - Authorization (can user access this message?)
    - Path validation (all required params present?)
    - Service injection (MessageService instance)
    
    Handler does:
    - Pure business logic
    """
    message_id = event['pathParameters']['message_id']
    
    # Optional: Use authorization context
    auth_context = event.get('authorization_context', {})
    if auth_context:
        # Log for audit
        actor = auth_context['actor']
        reason = auth_context['reason']
        print(f"User {actor.user_id} accessed message {message_id} (reason: {reason})")
    
    # Get message from service
    message = service.get_by_id(message_id)
    
    return {
        'statusCode': 200,
        'body': json.dumps({'message': message})
    }


# =============================================================================
# Example 2: POST Handler - Create Message
# =============================================================================

@handle_errors
@add_cors()
@require_authorization(operation=Operation.CREATE, resource_type="message")
@parse_request_body(required=True, convert_case=True)
@validate_path_params(['tenant_id', 'user_id'])
@inject_service(MessageService)
def create_message_handler(event: Dict[str, Any], context: Any, service: MessageService) -> Dict[str, Any]:
    """
    POST /tenants/{tenant_id}/users/{user_id}/messages
    
    Body:
    {
        "content": "Message content",
        "subject": "Optional subject"
    }
    """
    path_params = event['pathParameters']
    payload = event['parsed_body']
    
    message = service.create(
        tenant_id=path_params['tenant_id'],
        user_id=path_params['user_id'],
        content=payload['content'],
        subject=payload.get('subject')
    )
    
    return {
        'statusCode': 201,
        'body': json.dumps({'message': message})
    }


# =============================================================================
# Example 3: PUT Handler - Update Message
# =============================================================================

@handle_errors
@add_cors()
@require_authorization(operation=Operation.WRITE, resource_type="message")
@parse_request_body(required=True, convert_case=True)
@validate_path_params(['tenant_id', 'user_id', 'message_id'])
@inject_service(MessageService)
def update_message_handler(event: Dict[str, Any], context: Any, service: MessageService) -> Dict[str, Any]:
    """
    PUT /tenants/{tenant_id}/users/{user_id}/messages/{message_id}
    
    Body:
    {
        "content": "Updated content",
        "subject": "Updated subject"
    }
    """
    message_id = event['pathParameters']['message_id']
    updates = event['parsed_body']
    
    message = service.update(message_id, updates)
    
    return {
        'statusCode': 200,
        'body': json.dumps({'message': message})
    }


# =============================================================================
# Example 4: DELETE Handler - Delete Message
# =============================================================================

@handle_errors
@add_cors()
@require_authorization(operation=Operation.DELETE, resource_type="message")
@validate_path_params(['tenant_id', 'user_id', 'message_id'])
@inject_service(MessageService)
def delete_message_handler(event: Dict[str, Any], context: Any, service: MessageService) -> Dict[str, Any]:
    """
    DELETE /tenants/{tenant_id}/users/{user_id}/messages/{message_id}
    """
    message_id = event['pathParameters']['message_id']
    
    service.delete(message_id)
    
    return {
        'statusCode': 204,
        'body': ''
    }


# =============================================================================
# Example 5: LIST Handler - List Messages
# =============================================================================

@handle_errors
@add_cors()
@require_authorization(operation=Operation.READ, resource_type="message")
@validate_path_params(['tenant_id', 'user_id'])
@inject_service(MessageService)
def list_messages_handler(event: Dict[str, Any], context: Any, service: MessageService) -> Dict[str, Any]:
    """
    GET /tenants/{tenant_id}/users/{user_id}/messages?status=unread&limit=50
    """
    path_params = event['pathParameters']
    query_params = event.get('queryStringParameters') or {}
    
    tenant_id = path_params['tenant_id']
    user_id = path_params['user_id']
    status = query_params.get('status')
    limit = int(query_params.get('limit', 50))
    
    messages = service.list_by_user(
        tenant_id=tenant_id,
        user_id=user_id,
        status=status,
        limit=limit
    )
    
    return {
        'statusCode': 200,
        'body': json.dumps({'messages': messages, 'count': len(messages)})
    }


# =============================================================================
# Example 6: Admin Handler - Delete Any Message
# =============================================================================

@handle_errors
@add_cors()
@require_admin
@validate_path_params(['tenant_id', 'message_id'])
@inject_service(MessageService)
def admin_delete_message_handler(event: Dict[str, Any], context: Any, service: MessageService) -> Dict[str, Any]:
    """
    DELETE /admin/tenants/{tenant_id}/messages/{message_id}
    
    Admin-only endpoint - can delete any message.
    """
    message_id = event['pathParameters']['message_id']
    
    service.delete(message_id)
    
    return {
        'statusCode': 204,
        'body': ''
    }


# =============================================================================
# Example 7: Global Admin Handler - Platform Management
# =============================================================================

@handle_errors
@add_cors()
@require_platform_admin
@inject_service(MessageService)
def platform_stats_handler(event: Dict[str, Any], context: Any, service: MessageService) -> Dict[str, Any]:
    """
    GET /platform/stats
    
    Global admin only - platform-wide statistics.
    """
    stats = service.get_platform_stats()
    
    return {
        'statusCode': 200,
        'body': json.dumps({'stats': stats})
    }


# =============================================================================
# Example 8: Public Handler - No Authentication
# =============================================================================

@handle_errors
@add_cors()
@public
@inject_service(ContactThreadService)
def public_contact_handler(event: Dict[str, Any], context: Any, service: ContactThreadService) -> Dict[str, Any]:
    """
    POST /public/contact
    
    Public endpoint - no authentication required.
    Used for contact forms on public website.
    
    Body:
    {
        "name": "John Doe",
        "email": "john@example.com",
        "message": "Contact message"
    }
    """
    # No authorization - public endpoint
    payload = json.loads(event.get('body', '{}'))
    
    thread = service.create_from_public_form(
        name=payload.get('name'),
        email=payload.get('email'),
        message=payload.get('message')
    )
    
    return {
        'statusCode': 201,
        'body': json.dumps({'thread_id': thread['id']})
    }


# =============================================================================
# Example 9: Auto-Infer Operation from HTTP Method
# =============================================================================

@handle_errors
@add_cors()
@require_authorization(resource_type="message")  # Operation inferred from httpMethod
@parse_request_body(required=True)
@validate_path_params(['tenant_id', 'user_id'])
@inject_service(MessageService)
def auto_infer_handler(event: Dict[str, Any], context: Any, service: MessageService) -> Dict[str, Any]:
    """
    POST /tenants/{tenant_id}/users/{user_id}/messages
    
    Operation is automatically inferred:
    - POST → CREATE
    - GET → READ
    - PUT/PATCH → WRITE
    - DELETE → DELETE
    """
    path_params = event['pathParameters']
    payload = event['parsed_body']
    
    message = service.create(
        tenant_id=path_params['tenant_id'],
        user_id=path_params['user_id'],
        payload=payload
    )
    
    return {
        'statusCode': 201,
        'body': json.dumps({'message': message})
    }


# =============================================================================
# Example 10: Conditional Logic Based on Authorization Context
# =============================================================================

@handle_errors
@add_cors()
@require_authorization(operation=Operation.READ, resource_type="message")
@validate_path_params(['tenant_id', 'user_id', 'message_id'])
@inject_service(MessageService)
def conditional_handler(event: Dict[str, Any], context: Any, service: MessageService) -> Dict[str, Any]:
    """
    GET /tenants/{tenant_id}/users/{user_id}/messages/{message_id}
    
    Returns different data based on how user got access.
    """
    message_id = event['pathParameters']['message_id']
    message = service.get_by_id(message_id)
    
    # Check authorization context
    auth_context = event.get('authorization_context', {})
    access_reason = auth_context.get('reason')
    
    if access_reason == 'shared_read':
        # Shared access - hide sensitive fields
        message['internal_notes'] = '[REDACTED]'
        message['metadata'] = '[REDACTED]'
    elif access_reason == 'user_read_own':
        # User's own data - show everything
        pass
    elif access_reason == 'platform_admin':
        # Admin - add audit info
        message['_admin_view'] = True
        message['_accessed_by'] = auth_context['actor'].user_id
    
    return {
        'statusCode': 200,
        'body': json.dumps({'message': message})
    }


# =============================================================================
# Example 11: With Logging
# =============================================================================

@handle_errors
@log_execution(log_response=False, log_duration=True)
@add_cors()
@require_authorization(operation=Operation.READ, resource_type="message")
@validate_path_params(['tenant_id', 'user_id', 'message_id'])
@inject_service(MessageService)
def logged_handler(event: Dict[str, Any], context: Any, service: MessageService) -> Dict[str, Any]:
    """
    GET /tenants/{tenant_id}/users/{user_id}/messages/{message_id}
    
    With execution logging for monitoring.
    """
    message_id = event['pathParameters']['message_id']
    message = service.get_by_id(message_id)
    
    return {
        'statusCode': 200,
        'body': json.dumps({'message': message})
    }


# =============================================================================
# SAM Template Example
# =============================================================================

"""
# template.yaml

Resources:
  # GET handler
  GetMessageFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: src/
      Handler: examples.decorator_pattern_handlers.get_message_handler
      Runtime: python3.11
      Environment:
        Variables:
          DYNAMODB_TABLE_NAME: !Ref MessagesTable
      Events:
        GetMessage:
          Type: Api
          Properties:
            Path: /tenants/{tenant_id}/users/{user_id}/messages/{message_id}
            Method: GET
            Auth:
              Authorizer: CognitoAuthorizer
  
  # POST handler  
  CreateMessageFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: src/
      Handler: examples.decorator_pattern_handlers.create_message_handler
      Runtime: python3.11
      Environment:
        Variables:
          DYNAMODB_TABLE_NAME: !Ref MessagesTable
      Events:
        CreateMessage:
          Type: Api
          Properties:
            Path: /tenants/{tenant_id}/users/{user_id}/messages
            Method: POST
            Auth:
              Authorizer: CognitoAuthorizer
  
  # Public handler (no auth)
  PublicContactFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: src/
      Handler: examples.decorator_pattern_handlers.public_contact_handler
      Runtime: python3.11
      Events:
        PublicContact:
          Type: Api
          Properties:
            Path: /public/contact
            Method: POST
            Auth:
              Authorizer: NONE  # Public endpoint
"""

# =============================================================================
# Testing Examples
# =============================================================================

"""
# Unit test (test business logic)
def test_get_message_business_logic():
    mock_service = Mock()
    mock_service.get_by_id = Mock(return_value={'id': 'msg_123', 'content': 'Hello'})
    
    # Test handler directly with injected service
    event = {
        'pathParameters': {'message_id': 'msg_123'},
        'authorization_context': {'actor': {...}, 'reason': 'user_read_own'}
    }
    
    # Note: Decorators won't run in unit test, test business logic only
    # For full decorator testing, use integration tests

# Integration test (test full stack)
def test_get_message_handler():
    event = {
        'httpMethod': 'GET',
        'pathParameters': {
            'tenant_id': 'tenant_a',
            'user_id': 'user_123',
            'message_id': 'msg_456'
        },
        'requestContext': {
            'authorizer': {
                'claims': {
                    'custom:user_id': 'user_123',
                    'custom:tenant_id': 'tenant_a',
                    'custom:permissions': 'user_read_own'
                }
            }
        }
    }
    
    response = get_message_handler(event, None)
    
    assert response['statusCode'] == 200
    assert 'Access-Control-Allow-Origin' in response['headers']
    body = json.loads(response['body'])
    assert 'message' in body
"""
