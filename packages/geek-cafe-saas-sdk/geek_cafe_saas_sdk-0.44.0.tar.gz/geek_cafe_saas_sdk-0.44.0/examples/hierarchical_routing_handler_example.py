"""
Example Lambda handlers using hierarchical routing with authorization middleware.

This demonstrates:
1. How to use @require_authorization decorator
2. Path parameter structure for hierarchical routes
3. Accessing authorization context in handlers
4. Different permission scenarios
"""

import json
from typing import Dict, Any
from geek_cafe_saas_sdk.middleware.authorization import (
    require_authorization,
    Operation,
    Permission
)


# Example 1: Get user's message (READ operation)
@require_authorization(operation=Operation.READ, resource_type="message")
def get_message_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Get a message by ID with automatic authorization.
    
    Route: GET /tenants/{tenant_id}/users/{user_id}/messages/{message_id}
    
    Authorization is automatically checked:
    - User can access target tenant (own, shared, or admin)
    - User can access target user's resources
    - User has read permission
    """
    # Extract path parameters
    path_params = event['pathParameters']
    tenant_id = path_params['tenant_id']
    user_id = path_params['user_id']
    message_id = path_params['message_id']
    
    # Get authorization context (added by decorator)
    auth_context = event.get('authorization_context', {})
    actor = auth_context.get('actor')
    access_reason = auth_context.get('reason')
    
    # Log access for audit
    print(f"User {actor.user_id} from tenant {actor.tenant_id} "
          f"accessing message {message_id} in tenant {tenant_id} "
          f"(reason: {access_reason})")
    
    # Get the message from database
    # service = MessageService()
    # message = service.get_by_id(message_id)
    
    # Mock response
    message = {
        'id': message_id,
        'tenant_id': tenant_id,
        'user_id': user_id,
        'content': 'Hello, World!',
        'created_at': 1234567890
    }
    
    # Return message with access type
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({
            'message': message,
            'access_type': access_reason,
            'accessed_by': {
                'user_id': actor.user_id,
                'tenant_id': actor.tenant_id
            }
        })
    }


# Example 2: Create message (CREATE operation)
@require_authorization(operation=Operation.CREATE, resource_type="message")
def create_message_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Create a new message with authorization.
    
    Route: POST /tenants/{tenant_id}/users/{user_id}/messages
    
    Authorization checks:
    - User can access tenant
    - User can create resources for target user
    - User has write/create permission
    """
    path_params = event['pathParameters']
    tenant_id = path_params['tenant_id']
    user_id = path_params['user_id']
    
    # Get authorization context
    auth_context = event['authorization_context']
    actor = auth_context['actor']
    
    # Parse request body
    body = json.loads(event.get('body', '{}'))
    
    # Validate: Regular users can only create for themselves
    # (unless they're admin)
    if not actor.has_permission(Permission.PLATFORM_ADMIN) and \
       not actor.has_permission(Permission.TENANT_ADMIN):
        if user_id != actor.user_id:
            return {
                'statusCode': 403,
                'body': json.dumps({
                    'error': 'Forbidden',
                    'message': 'You can only create messages for yourself'
                })
            }
    
    # Create the message
    # service = MessageService()
    # message = service.create(tenant_id, user_id, body)
    
    # Mock response
    message = {
        'id': 'msg_new_123',
        'tenant_id': tenant_id,
        'user_id': user_id,
        'content': body.get('content', ''),
        'created_at': 1234567890,
        'created_by': actor.user_id
    }
    
    return {
        'statusCode': 201,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'message': message})
    }


# Example 3: Update message (WRITE operation)
@require_authorization(operation=Operation.WRITE, resource_type="message")
def update_message_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Update a message with authorization.
    
    Route: PUT /tenants/{tenant_id}/users/{user_id}/messages/{message_id}
    
    Authorization checks:
    - User can access tenant
    - User can modify target user's resources
    - User has write permission
    """
    path_params = event['pathParameters']
    tenant_id = path_params['tenant_id']
    user_id = path_params['user_id']
    message_id = path_params['message_id']
    
    auth_context = event['authorization_context']
    body = json.loads(event.get('body', '{}'))
    
    # Update the message
    # service = MessageService()
    # message = service.update(message_id, body)
    
    # Mock response
    message = {
        'id': message_id,
        'tenant_id': tenant_id,
        'user_id': user_id,
        'content': body.get('content', 'Updated content'),
        'updated_at': 1234567890
    }
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'message': message})
    }


# Example 4: Delete message (DELETE operation)
@require_authorization(operation=Operation.DELETE, resource_type="message")
def delete_message_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Delete a message with authorization.
    
    Route: DELETE /tenants/{tenant_id}/users/{user_id}/messages/{message_id}
    """
    path_params = event['pathParameters']
    message_id = path_params['message_id']
    
    # Delete the message
    # service = MessageService()
    # service.delete(message_id)
    
    return {
        'statusCode': 204,
        'headers': {'Content-Type': 'application/json'},
        'body': ''
    }


# Example 5: List user's messages with query params
@require_authorization(operation=Operation.READ, resource_type="message")
def list_messages_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    List messages for a user.
    
    Route: GET /tenants/{tenant_id}/users/{user_id}/messages
    
    Query params: ?limit=50&status=unread
    """
    path_params = event['pathParameters']
    tenant_id = path_params['tenant_id']
    user_id = path_params['user_id']
    
    # Get query parameters
    query_params = event.get('queryStringParameters', {}) or {}
    limit = int(query_params.get('limit', 50))
    status = query_params.get('status')
    
    # List messages
    # service = MessageService()
    # messages = service.list_by_user(tenant_id, user_id, limit=limit, status=status)
    
    # Mock response
    messages = [
        {
            'id': 'msg_1',
            'tenant_id': tenant_id,
            'user_id': user_id,
            'content': 'Message 1',
            'status': 'read'
        },
        {
            'id': 'msg_2',
            'tenant_id': tenant_id,
            'user_id': user_id,
            'content': 'Message 2',
            'status': 'unread'
        }
    ]
    
    # Filter by status if provided
    if status:
        messages = [m for m in messages if m['status'] == status]
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({
            'messages': messages[:limit],
            'count': len(messages[:limit])
        })
    }


# Example 6: Tenant-level resource (no user_id)
@require_authorization(operation=Operation.READ, resource_type="channel")
def get_channel_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Get a tenant-level resource (channel).
    
    Route: GET /tenants/{tenant_id}/channels/{channel_id}
    
    Note: No user_id in path - this is a tenant-wide resource
    """
    path_params = event['pathParameters']
    tenant_id = path_params['tenant_id']
    channel_id = path_params['channel_id']
    
    auth_context = event['authorization_context']
    actor = auth_context['actor']
    
    # Get the channel
    # service = ChannelService()
    # channel = service.get_by_id(channel_id)
    
    # Mock response
    channel = {
        'id': channel_id,
        'tenant_id': tenant_id,
        'name': 'General',
        'type': 'public',
        'member_count': 42
    }
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'channel': channel})
    }


# Example 7: Using inferred operation (no explicit operation parameter)
@require_authorization(resource_type="message")
def message_handler_auto_operation(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handler that infers operation from HTTP method.
    
    Routes:
    - GET /tenants/{tid}/users/{uid}/messages/{mid} → READ
    - POST /tenants/{tid}/users/{uid}/messages → CREATE
    - PUT /tenants/{tid}/users/{uid}/messages/{mid} → WRITE
    - DELETE /tenants/{tid}/users/{uid}/messages/{mid} → DELETE
    """
    auth_context = event['authorization_context']
    operation = auth_context['operation']
    
    # Handle based on operation
    if operation == 'read':
        return {'statusCode': 200, 'body': json.dumps({'action': 'read'})}
    elif operation == 'create':
        return {'statusCode': 201, 'body': json.dumps({'action': 'create'})}
    elif operation == 'write':
        return {'statusCode': 200, 'body': json.dumps({'action': 'update'})}
    elif operation == 'delete':
        return {'statusCode': 204, 'body': ''}


# Example 8: Admin-only endpoint
@require_authorization(operation=Operation.READ, resource_type="tenant")
def list_all_tenants_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    List all tenants (admin only).
    
    Route: GET /tenants
    
    This would typically be at API Gateway level, but shows how
    global admin permission would be checked.
    """
    auth_context = event['authorization_context']
    actor = auth_context['actor']
    
    # Verify global admin (additional check)
    if not actor.has_permission(Permission.PLATFORM_ADMIN):
        return {
            'statusCode': 403,
            'body': json.dumps({
                'error': 'Forbidden',
                'message': 'This endpoint requires global admin permission'
            })
        }
    
    # List all tenants
    # service = TenantService()
    # tenants = service.list_all()
    
    # Mock response
    tenants = [
        {'id': 'tenant_a', 'name': 'Acme Corp'},
        {'id': 'tenant_b', 'name': 'Tech Startup'},
        {'id': 'tenant_c', 'name': 'Enterprise Inc'}
    ]
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'tenants': tenants})
    }


# Example Usage in SAM/CloudFormation template:
"""
Resources:
  GetMessageFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: hierarchical_routing_handler_example.get_message_handler
      Events:
        GetMessage:
          Type: Api
          Properties:
            Path: /tenants/{tenant_id}/users/{user_id}/messages/{message_id}
            Method: GET
            Auth:
              Authorizer: CognitoAuthorizer

  CreateMessageFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: hierarchical_routing_handler_example.create_message_handler
      Events:
        CreateMessage:
          Type: Api
          Properties:
            Path: /tenants/{tenant_id}/users/{user_id}/messages
            Method: POST
            Auth:
              Authorizer: CognitoAuthorizer
"""

# Example JWT Claims Structure:
"""
Regular User:
{
  "sub": "cognito-user-id",
  "custom:user_id": "user_123",
  "custom:tenant_id": "tenant_a",
  "custom:roles": "user",
  "custom:permissions": "user_read_own,user_write_own",
  "email": "user@example.com",
  "name": "John Doe"
}

Tenant Admin:
{
  "sub": "cognito-admin-id",
  "custom:user_id": "admin_123",
  "custom:tenant_id": "tenant_a",
  "custom:roles": "tenant_admin",
  "custom:permissions": "tenant_admin,tenant_read,tenant_write,user_read_others,user_write_others",
  "email": "admin@acme.com",
  "name": "Admin User"
}

Platform Admin:
{
  "sub": "cognito-platform-admin-id",
  "custom:user_id": "platform_admin_123",
  "custom:tenant_id": "platform_admin",
  "custom:roles": "platform_admin",
  "custom:permissions": "platform_admin,tenant_admin,tenant_read,tenant_write",
  "email": "admin@platform.com",
  "name": "Platform Admin"
}

User with Shared Tenant Access:
{
  "sub": "cognito-user-id",
  "custom:user_id": "user_123",
  "custom:tenant_id": "tenant_a",
  "custom:roles": "user",
  "custom:permissions": "user_read_own,user_write_own,user_read_shared",
  "custom:shared_tenants": "tenant_b,tenant_c",  # Has access to these tenants
  "email": "user@example.com",
  "name": "John Doe"
}
"""
