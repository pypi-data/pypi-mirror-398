"""
Authentication middleware for Lambda handlers.
"""
import json
import functools
from typing import Dict, Any, Callable


def require_auth(handler: Callable) -> Callable:
    """
    Decorator that ensures the request has valid authentication.
    Expects API Gateway authorizer to populate requestContext.authorizer.
    """
    @functools.wraps(handler)
    def wrapper(event: Dict[str, Any], context: Any, *args, **kwargs) -> Dict[str, Any]:
        # Check if authorizer context exists
        request_context = event.get('requestContext', {})
        authorizer = request_context.get('authorizer', {})
        
        if not authorizer:
            return {
                'statusCode': 401,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Unauthorized',
                    'error_code': 'AUTH_REQUIRED',
                    'message': 'Missing authorizer context'
                })
            }
        
        # Validate required auth fields
        claims = authorizer.get('claims', {})
        required_fields = ['custom:user_id', 'custom:tenant_id']
        for field in required_fields:
            if not claims.get(field):
                return {
                    'statusCode': 401,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'error': f'Missing required auth field: {field}',
                        'error_code': 'AUTH_INVALID',
                        'message': 'Missing required auth field'
                    })
                }
        
        # Call the original handler
        return handler(event, context, *args, **kwargs)
    
    return wrapper


def extract_user_context(event: Dict[str, Any]) -> Dict[str, str]:
    """
    Extract user context from API Gateway authorizer.
    
    Returns:
        Dict containing user_id, tenant_id, roles, permissions, inboxes, and other claims
    """
    authorizer = event.get('requestContext', {}).get('authorizer', {})
    claims = authorizer.get('claims', {})
    
    # Parse comma-separated custom claims (strip whitespace and filter empty)
    def parse_csv_claim(claim_value: str) -> list:
        """Parse comma-separated claim value into list."""
        if not claim_value:
            return []
        return [item.strip() for item in claim_value.split(',') if item.strip()]
    
    # Optional chaos engineering configuration via claim
    chaos_claim = claims.get('custom:chaos')
    chaos_engineering = None
    if chaos_claim:
        try:
            chaos_engineering = json.loads(chaos_claim) if isinstance(chaos_claim, str) else chaos_claim
        except Exception:
            chaos_engineering = None

    context = {
        'user_id': claims.get('custom:user_id'),
        'tenant_id': claims.get('custom:tenant_id'),
        'roles': parse_csv_claim(claims.get('custom:roles', '')),
        'permissions': parse_csv_claim(claims.get('custom:permissions', '')),
        'inboxes': parse_csv_claim(claims.get('custom:inboxes', '')),
        'shared_tenants': parse_csv_claim(claims.get('custom:shared_tenants', '')),
        'email': claims.get('email'),
        'name': claims.get('name'),
        'sub': claims.get('sub')  # Cognito user ID
    }

    if chaos_engineering:
        context['chaos_engineering'] = chaos_engineering

    return context
