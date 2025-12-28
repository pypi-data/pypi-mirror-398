"""
List Executions Lambda Handler.

GET /executions
GET /executions/{execution-id}/children

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from typing import Any
from geek_cafe_saas_sdk.lambda_handlers import BaseLambdaHandler, LambdaEvent
from geek_cafe_saas_sdk.modules.executions.services import ExecutionService
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.core.error_codes import ErrorCode

DEFAULT_LIMIT = 50

handler_wrapper = BaseLambdaHandler(
    service_class=ExecutionService,
    require_auth=True,
)


def handler(event: dict, context: Any) -> dict:
    """Lambda entry point."""
    return handler_wrapper.execute(event, context, list_executions)


def list_executions(
    event: LambdaEvent,
    service: ExecutionService
) -> Any:
    """
    List executions with various filters.
    
    Query parameters:
        root_id: str - List all executions in a chain by root ID
        parent_id: str - List direct children of an execution
        status: str - Filter by status (pending, running, succeeded, failed, etc.)
        correlation_id: str - List by correlation ID (cross-service tracking)
        resource_type: str - Filter by resource type (requires resource_id)
        resource_id: str - Filter by resource ID (requires resource_type)
        limit: int - Maximum results (default: 50)
        ascending: bool - Sort order by started_at (default: false = newest first)
    """
    # Get filter parameters
    root_id = event.query("root_id", "rootId")
    parent_id = event.query("parent_id", "parentId")
    status = event.query("status")
    correlation_id = event.query("correlation_id", "correlationId")
    resource_type = event.query("resource_type", "resourceType")
    resource_id = event.query("resource_id", "resourceId")
    
    limit = event.query_int("limit", default=DEFAULT_LIMIT)
    ascending = event.query_bool("ascending", default=False)
    
    # Determine which query to use based on parameters
    if root_id:
        return service.list_by_root(
            root_id=root_id,
            limit=limit,
            ascending=ascending,
        )
    
    elif parent_id:
        return service.list_children(
            parent_id=parent_id,
            limit=limit,
            ascending=ascending,
        )
    
    elif status:
        return service.list_by_status(
            status=status,
            limit=limit,
            ascending=ascending,
        )
    
    elif correlation_id:
        return service.list_by_correlation(
            correlation_id=correlation_id,
            limit=limit,
            ascending=ascending,
        )
    
    elif resource_type and resource_id:
        return service.list_by_resource(
            resource_type=resource_type,
            resource_id=resource_id,
            limit=limit,
            ascending=ascending,
        )
    
    else:
        return ServiceResult.error_result(
            message="At least one filter is required: root_id, parent_id, status, correlation_id, or (resource_type + resource_id)",
            error_code=ErrorCode.VALIDATION_ERROR
        )


# Separate handler for children endpoint
children_handler_wrapper = BaseLambdaHandler(
    service_class=ExecutionService,
    require_auth=True,
)


def children_handler(event: dict, context: Any) -> dict:
    """Lambda entry point for /executions/{id}/children."""
    return children_handler_wrapper.execute(event, context, list_children)


def list_children(
    event: LambdaEvent,
    service: ExecutionService
) -> Any:
    """
    List direct children of an execution.
    
    Path parameters:
        execution-id or executionId: Parent execution ID
        
    Query parameters:
        limit: int - Maximum results (default: 50)
        ascending: bool - Sort order (default: false = newest first)
    """
    parent_id = event.path("execution-id", "executionId", "id")
    limit = event.query_int("limit", default=DEFAULT_LIMIT)
    ascending = event.query_bool("ascending", default=False)
    
    return service.list_children(
        parent_id=parent_id,
        limit=limit,
        ascending=ascending,
    )
