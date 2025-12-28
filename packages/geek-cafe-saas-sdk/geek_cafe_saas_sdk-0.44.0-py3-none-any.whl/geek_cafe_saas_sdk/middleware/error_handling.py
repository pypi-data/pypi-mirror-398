"""
Error handling middleware for Lambda handlers.
"""
import json
import logging
import traceback
import functools
from typing import Dict, Any, Callable
from ..core.service_errors import ValidationError, NotFoundError, AccessDeniedError
logger = logging.getLogger(__name__)


def handle_errors(handler: Callable) -> Callable:
    """
    Decorator that converts service errors to appropriate HTTP responses.
    """
    @functools.wraps(handler)
    def wrapper(event: Dict[str, Any], context: Any, *args, **kwargs) -> Dict[str, Any]:
        try:
            return handler(event, context, *args, **kwargs)
        except ValidationError as e:
            logger.warning(f"Validation error: {str(e)}")
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': str(e),
                    'error_code': 'VALIDATION_ERROR'
                })
            }
        except AccessDeniedError as e:
            logger.warning(f"Access denied: {str(e)}")
            return {
                'statusCode': 403,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': str(e),
                    'error_code': 'ACCESS_DENIED'
                })
            }
        except NotFoundError as e:
            logger.info(f"Resource not found: {str(e)}")
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': str(e),
                    'error_code': 'NOT_FOUND'
                })
            }
        except Exception as e:
            logger.error(f"Unexpected error in {handler.__name__}: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': 'Internal server error',
                    'error_code': 'INTERNAL_ERROR'
                })
            }
    
    return wrapper


def validate_request_body(required_fields: list = None, optional_fields: list = None):
    """
    Decorator that validates request body fields.
    
    Args:
        required_fields: List of required field names
        optional_fields: List of optional field names (for documentation)
    """
    def decorator(handler: Callable) -> Callable:
        @functools.wraps(handler)
        def wrapper(event: Dict[str, Any], context: Any, *args, **kwargs) -> Dict[str, Any]:
            # Parse request body
            body_str = event.get('body', '{}')
            try:
                body = json.loads(body_str) if isinstance(body_str, str) else body_str
                if body is None:
                    raise json.JSONDecodeError("Body is None", "", 0)
            except json.JSONDecodeError:
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({
                        'error': 'Invalid JSON in request body',
                        'error_code': 'INVALID_JSON'
                    })
                }
            
            # Check required fields
            if required_fields:
                missing_fields = [field for field in required_fields if field not in body]
                if missing_fields:
                    return {
                        'statusCode': 400,
                        'headers': {'Content-Type': 'application/json'},
                        'body': json.dumps({
                            'error': f'Missing required fields: {", ".join(missing_fields)}',
                            'error_code': 'MISSING_FIELDS'
                        })
                    }
            
            # Add parsed body to event for handler
            event['parsed_body'] = body
            return handler(event, context, *args, **kwargs)
        
        return wrapper
    return decorator


# Custom exception classes are imported from core module
