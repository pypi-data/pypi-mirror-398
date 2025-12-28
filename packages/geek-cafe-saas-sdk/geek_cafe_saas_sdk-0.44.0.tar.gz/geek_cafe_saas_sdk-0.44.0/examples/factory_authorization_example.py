"""
Example: Migrating handlers to use factory-based authorization.

This shows:
1. Before: Existing handler pattern (still works!)
2. After: Enhanced with authorization (minimal changes)
3. Comparison: All three authorization patterns
"""

from typing import Dict, Any
from geek_cafe_saas_sdk.lambda_handlers import create_handler
from geek_cafe_saas_sdk.middleware.authorization import Operation, require_authorization
from geek_cafe_saas_sdk.core.services.message_service import MessageService


# =============================================================================
# EXAMPLE 1: BEFORE - Existing Pattern (Still Works!)
# =============================================================================

# Before: No authorization (relies on API Gateway only)
existing_handler_wrapper = create_handler(
    service_class=MessageService,
    require_body=False
)

def existing_handler(event, context):
    """Existing handler - backward compatible, no changes needed."""
    return existing_handler_wrapper.execute(event, context, existing_business_logic)

def existing_business_logic(event, service, user_context):
    """
    Existing business logic - completely unchanged.
    
    Route: GET /messages/{id}  (old pattern)
    """
    message_id = event['pathParameters']['id']
    
    # User context from JWT (tenant_id, user_id)
    tenant_id = user_context.get('tenant_id')
    user_id = user_context.get('user_id')
    
    # Service handles tenant scoping
    return service.get_by_id(message_id, tenant_id, user_id)


# =============================================================================
# EXAMPLE 2: AFTER - Enhanced Factory with Authorization (RECOMMENDED)
# =============================================================================

# After: Add 3 parameters to factory
enhanced_handler_wrapper = create_handler(
    service_class=MessageService,
    require_body=False,
    require_authorization=True,  # ← ADD LINE 1
    operation=Operation.READ,     # ← ADD LINE 2
    resource_type="message"       # ← ADD LINE 3
)

def enhanced_handler(event, context):
    """Enhanced handler with authorization - same structure."""
    return enhanced_handler_wrapper.execute(event, context, enhanced_business_logic)

def enhanced_business_logic(event, service, user_context):
    """
    Enhanced business logic - ZERO changes to logic!
    
    Route: GET /tenants/{tenant_id}/users/{user_id}/messages/{message_id}
    
    Authorization automatically checked:
    - Can actor access target tenant?
    - Can actor access target user's data?
    - Does actor have read permission?
    """
    # Get message ID from new hierarchical path
    path_params = event['pathParameters']
    message_id = path_params['message_id']
    
    # Authorization already verified by handler wrapper
    # Just implement business logic
    message = service.get_by_id(message_id)
    
    # Optional: Access authorization context for audit/logging
    auth_context = event.get('authorization_context', {})
    if auth_context:
        # Log who accessed what and why they had permission
        actor = auth_context['actor']
        reason = auth_context['reason']
        print(f"User {actor.user_id} accessed message {message_id} (reason: {reason})")
        
        # Conditional logic based on access type
        if reason == "shared_read":
            # Hide sensitive fields for shared access
            message['internal_notes'] = "[REDACTED]"
    
    return message


# =============================================================================
# EXAMPLE 3: Create Handler (Inferred Operation)
# =============================================================================

# Let factory infer operation from HTTP method
inferred_handler_wrapper = create_handler(
    service_class=MessageService,
    require_body=True,
    require_authorization=True,
    resource_type="message"  # operation auto-detected: POST = CREATE
)

def create_handler_example(event, context):
    """Create message - operation inferred from POST method."""
    return inferred_handler_wrapper.execute(event, context, create_message_logic)

def create_message_logic(event, service, user_context):
    """
    Route: POST /tenants/{tenant_id}/users/{user_id}/messages
    
    Operation automatically inferred as CREATE from POST method.
    """
    path_params = event['pathParameters']
    payload = event['parsed_body']  # Already parsed by handler
    
    return service.create(
        tenant_id=path_params['tenant_id'],
        user_id=path_params['user_id'],
        payload=payload
    )


# =============================================================================
# EXAMPLE 4: Update Handler
# =============================================================================

update_handler_wrapper = create_handler(
    service_class=MessageService,
    require_body=True,
    require_authorization=True,
    operation=Operation.WRITE,
    resource_type="message"
)

def update_handler_example(event, context):
    """Update message."""
    return update_handler_wrapper.execute(event, context, update_message_logic)

def update_message_logic(event, service, user_context):
    """
    Route: PUT /tenants/{tenant_id}/users/{user_id}/messages/{message_id}
    """
    path_params = event['pathParameters']
    payload = event['parsed_body']
    
    return service.update(
        message_id=path_params['message_id'],
        updates=payload
    )


# =============================================================================
# EXAMPLE 5: Delete Handler
# =============================================================================

delete_handler_wrapper = create_handler(
    service_class=MessageService,
    require_body=False,
    require_authorization=True,
    operation=Operation.DELETE,
    resource_type="message"
)

def delete_handler_example(event, context):
    """Delete message."""
    return delete_handler_wrapper.execute(event, context, delete_message_logic)

def delete_message_logic(event, service, user_context):
    """
    Route: DELETE /tenants/{tenant_id}/users/{user_id}/messages/{message_id}
    """
    message_id = event['pathParameters']['message_id']
    return service.delete(message_id)


# =============================================================================
# EXAMPLE 6: List Handler with Query Parameters
# =============================================================================

list_handler_wrapper = create_handler(
    service_class=MessageService,
    require_body=False,
    require_authorization=True,
    operation=Operation.READ,
    resource_type="message"
)

def list_handler_example(event, context):
    """List messages for a user."""
    return list_handler_wrapper.execute(event, context, list_messages_logic)

def list_messages_logic(event, service, user_context):
    """
    Route: GET /tenants/{tenant_id}/users/{user_id}/messages?status=unread&limit=50
    """
    path_params = event['pathParameters']
    query_params = event.get('queryStringParameters', {}) or {}
    
    tenant_id = path_params['tenant_id']
    user_id = path_params['user_id']
    status = query_params.get('status')
    limit = int(query_params.get('limit', 50))
    
    return service.list_by_user(
        tenant_id=tenant_id,
        user_id=user_id,
        status=status,
        limit=limit
    )


# =============================================================================
# COMPARISON: Three Authorization Patterns
# =============================================================================

# Pattern 1: Enhanced Factory (RECOMMENDED) ✅
def pattern1_factory_handler(event, context):
    """Using enhanced factory - clean and centralized."""
    handler_wrapper = create_handler(
        service_class=MessageService,
        require_authorization=True,
        operation=Operation.READ,
        resource_type="message"
    )
    return handler_wrapper.execute(event, context, pattern1_business_logic)

def pattern1_business_logic(event, service, user_context):
    # Clean business logic - no HTTP concerns
    # Authorization already checked
    message_id = event['pathParameters']['message_id']
    return service.get_by_id(message_id)


# Pattern 2: Decorator (Available for special cases)
@require_authorization(operation=Operation.READ, resource_type="message")
def pattern2_decorator_handler(event, context):
    """
    Using decorator - more flexible but more boilerplate.
    
    Pros: Flexible, clear from signature
    Cons: Manual service creation, CORS, error handling
    """
    message_id = event['pathParameters']['message_id']
    
    # Manual service instantiation
    service = MessageService()
    
    # Manual business logic
    message = service.get_by_id(message_id)
    
    # Manual response formatting
    import json
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({'message': message})
    }


# Pattern 3: Service Layer (NOT RECOMMENDED - shown for comparison only)
class MessageServiceWithAuth:  # DON'T DO THIS!
    """Anti-pattern: Authorization in service layer."""
    
    def get_by_id(self, message_id, requesting_user_id, requesting_tenant_id):
        """BAD: Mixes business logic with authorization."""
        message = self._get_from_db(message_id)
        
        # DON'T: Authorization in service
        if message.tenant_id != requesting_tenant_id:
            raise AccessDeniedError("Cross-tenant access denied")
        
        if message.user_id != requesting_user_id:
            raise AccessDeniedError("User access denied")
        
        return message

def pattern3_service_auth_handler(event, context):
    """DON'T USE: Service layer authorization."""
    service = MessageServiceWithAuth()
    user_context = extract_user_context(event)
    
    message = service.get_by_id(
        event['pathParameters']['message_id'],
        user_context['user_id'],
        user_context['tenant_id']
    )
    
    return {
        'statusCode': 200,
        'body': json.dumps({'message': message})
    }


# =============================================================================
# Testing Examples
# =============================================================================

def test_enhanced_handler_authorized():
    """Test enhanced handler with valid authorization."""
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
    
    # Mock service
    from unittest.mock import Mock
    mock_service = Mock()
    mock_service.get_by_id.return_value = {'id': 'msg_456', 'content': 'Hello'}
    
    # Execute handler (authorization passes)
    response = enhanced_handler(event, None)
    
    assert response['statusCode'] == 200


def test_enhanced_handler_unauthorized():
    """Test enhanced handler blocks unauthorized access."""
    event = {
        'httpMethod': 'GET',
        'pathParameters': {
            'tenant_id': 'tenant_b',  # Different tenant!
            'user_id': 'user_456',
            'message_id': 'msg_789'
        },
        'requestContext': {
            'authorizer': {
                'claims': {
                    'custom:user_id': 'user_123',
                    'custom:tenant_id': 'tenant_a',  # Actor in tenant_a
                    'custom:permissions': 'user_read_own'
                }
            }
        }
    }
    
    # Execute handler (authorization fails)
    response = enhanced_handler(event, None)
    
    assert response['statusCode'] == 403
    assert 'Forbidden' in response['body'] or 'permission' in response['body']


# =============================================================================
# SAM Template Example
# =============================================================================

"""
# template.yaml

Resources:
  # Enhanced handler with authorization
  GetMessageFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: src/
      Handler: lambda_handlers.messages.get.app.enhanced_handler
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
  
  # Cognito Authorizer
  CognitoAuthorizer:
    Type: AWS::ApiGateway::Authorizer
    Properties:
      Name: CognitoAuthorizer
      Type: COGNITO_USER_POOLS
      IdentitySource: method.request.header.Authorization
      ProviderARNs:
        - !GetAtt UserPool.Arn
"""

# =============================================================================
# Summary
# =============================================================================

"""
RECOMMENDED PATTERN: Enhanced Factory

✅ Use enhanced factory for 95% of handlers:
   - Standard CRUD operations
   - Consistent authorization rules
   - Clean separation of concerns
   - Easy to test and audit

⚠️  Use decorator for special cases:
   - Custom authorization logic
   - Non-standard routes
   - Prototyping

❌ Never use service layer authorization:
   - Violates Single Responsibility
   - Hard to test and reuse
   - Mixes concerns

MIGRATION PATH:
1. New handlers: Use enhanced factory from day 1
2. Existing handlers: Gradually add authorization (3 lines each)
3. No breaking changes - existing handlers work unchanged
"""
