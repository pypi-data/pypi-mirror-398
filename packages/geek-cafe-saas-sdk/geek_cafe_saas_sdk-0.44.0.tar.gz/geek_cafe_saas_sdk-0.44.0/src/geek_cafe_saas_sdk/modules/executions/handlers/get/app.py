"""
Get Execution Lambda Handler.

GET /executions/{execution-id}

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from typing import Any
from geek_cafe_saas_sdk.lambda_handlers import BaseLambdaHandler, LambdaEvent
from geek_cafe_saas_sdk.modules.executions.services import ExecutionService

handler_wrapper = BaseLambdaHandler(
    service_class=ExecutionService,
    require_auth=True,
)


def handler(event: dict, context: Any) -> dict:
    """Lambda entry point."""
    return handler_wrapper.execute(event, context, get_execution)


def get_execution(
    event: LambdaEvent,
    service: ExecutionService
) -> Any:
    """
    Get an execution by ID.
    
    Path parameters:
        execution-id or executionId: Execution ID
    """
    execution_id = event.path("execution-id", "executionId", "id")
    return service.get(execution_id=execution_id)
