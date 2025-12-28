"""
Lambda handler decorators for cross-cutting concerns.

This module provides composable decorators for Lambda handlers following
industry best practices (AWS Lambda Powertools, Flask, FastAPI patterns).

Usage:
    from geek_cafe_saas_sdk.decorators import (
        handle_errors,
        add_cors,
        parse_request_body,
        inject_service
    )
    
    @handle_errors
    @add_cors
    @parse_request_body(convert_request_case=True)
    @inject_service(MessageService)
    def lambda_handler(event, context, service):
        return service.get_by_id(event['pathParameters']['id'])

Design Principles:
    - Explicit > Implicit: See all behaviors in handler signature
    - Composable: Stack decorators as needed
    - Single Responsibility: Each decorator has one job
    - Testable: Test handlers and decorators independently
    - Industry Standard: Follows AWS Lambda Powertools patterns
"""

from .core import (
    handle_errors,
    add_cors,
    parse_request_body,
    inject_service,
    log_execution,
    validate_path_params,
    extract_user_context_decorator
)

from .auth import (
    require_authorization,
    require_admin,
    require_tenant_admin,
    require_platform_admin,
    public
)

__all__ = [
    # Core decorators
    "handle_errors",
    "add_cors",
    "parse_request_body",
    "inject_service",
    "log_execution",
    "validate_path_params",
    "extract_user_context_decorator",
    
    # Auth decorators
    "require_authorization",
    "require_admin",
    "require_tenant_admin",
    "require_platform_admin",
    "public",
]
