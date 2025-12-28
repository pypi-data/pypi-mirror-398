"""
Middleware decorators for Lambda functions.
"""

from .auth import require_auth, extract_user_context
from .cors import handle_cors
from .error_handling import handle_errors
from .validation import validate_request_body
from .authorization import (
    require_authorization,
    Permission,
    Operation,
    AuthContext,
    ResourceContext,
    AuthorizationResult,
    AuthorizationMiddleware,
    extract_auth_context,
    extract_resource_context
)

__all__ = [
    "require_auth",
    "extract_user_context",
    "handle_cors",
    "handle_errors",
    "validate_request_body",
    "require_authorization",
    "Permission",
    "Operation",
    "AuthContext",
    "ResourceContext",
    "AuthorizationResult",
    "AuthorizationMiddleware",
    "extract_auth_context",
    "extract_resource_context"
]
