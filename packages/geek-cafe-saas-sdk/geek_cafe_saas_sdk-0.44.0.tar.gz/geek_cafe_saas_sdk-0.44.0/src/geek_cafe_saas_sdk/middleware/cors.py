"""
CORS middleware for Lambda handlers.
"""
import functools
from typing import Dict, Any, Callable


def add_cors_headers(lambda_handler: Callable) -> Callable:
    """
    Decorator that adds CORS headers to Lambda response.
    """
    @functools.wraps(lambda_handler)
    def wrapper(event: Dict[str, Any], context: Any, *args, **kwargs) -> Dict[str, Any]:
        response = lambda_handler(event, context, *args, **kwargs)
        
        # Ensure headers exist
        if 'headers' not in response:
            response['headers'] = {}
        
        # Add CORS headers
        cors_headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
            'Content-Type': 'application/json'
        }
        
        response['headers'].update(cors_headers)
        return response
    
    return wrapper


def handle_preflight(lambda_handler: Callable) -> Callable:
    """
    Decorator that handles OPTIONS preflight requests.
    """
    @functools.wraps(lambda_handler)
    def wrapper(event: Dict[str, Any], context: Any, *args, **kwargs) -> Dict[str, Any]:
        # Handle OPTIONS request
        if event.get('httpMethod') == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
                    'Content-Type': 'application/json'
                },
                'body': ''
            }
        
        return lambda_handler(event, context, *args, **kwargs)
    
    return wrapper


# Convenience decorator that combines both CORS functionalities
def handle_cors(lambda_handler: Callable) -> Callable:
    """
    Decorator that handles both preflight requests and adds CORS headers.
    """
    return add_cors_headers(handle_preflight(lambda_handler))
