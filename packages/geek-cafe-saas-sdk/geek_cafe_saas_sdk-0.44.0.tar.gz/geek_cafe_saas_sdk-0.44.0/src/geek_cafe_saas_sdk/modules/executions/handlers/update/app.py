"""
Update Execution Lambda Handler.

PATCH /executions/{execution-id}

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from typing import Any
from geek_cafe_saas_sdk.lambda_handlers import BaseLambdaHandler, LambdaEvent
from geek_cafe_saas_sdk.modules.executions.services import ExecutionService
from geek_cafe_saas_sdk.modules.executions.models import ExecutionStatus
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.core.error_codes import ErrorCode

handler_wrapper = BaseLambdaHandler(
    service_class=ExecutionService,
    require_auth=True,
    require_body=True,
)


def handler(event: dict, context: Any) -> dict:
    """Lambda entry point."""
    return handler_wrapper.execute(event, context, update_execution)


def update_execution(
    event: LambdaEvent,
    service: ExecutionService
) -> Any:
    """
    Update an execution's status or progress.
    
    Path parameters:
        execution-id or executionId: Execution ID
        
    Request body:
        action: str - Action to perform (start, complete, fail, cancel, retry, progress)
        
        For action=progress:
            progress_percent: int - Progress percentage (0-100)
            current_step: str - Current step name
            current_step_index: int - Current step index
            metadata: dict - Additional metadata to merge
            
        For action=complete:
            output_payload: dict - Result data
            
        For action=fail:
            error_code: str - Error code
            error_message: str - Error message
            error_details: dict - Additional error details
    """
    execution_id = event.path("execution-id", "executionId", "id")
    body = event.body
    action = body.get("action", "").lower()
    
    if action == "start":
        return service.start(execution_id=execution_id)
    
    elif action == "complete":
        return service.complete(
            execution_id=execution_id,
            output_payload=body.get("output_payload"),
        )
    
    elif action == "fail":
        return service.fail(
            execution_id=execution_id,
            error_code=body.get("error_code"),
            error_message=body.get("error_message"),
            error_details=body.get("error_details"),
        )
    
    elif action == "cancel":
        return service.cancel(execution_id=execution_id)
    
    elif action == "retry":
        return service.retry(execution_id=execution_id)
    
    elif action == "progress":
        return service.update_progress(
            execution_id=execution_id,
            progress_percent=body.get("progress_percent"),
            current_step=body.get("current_step"),
            current_step_index=body.get("current_step_index"),
            metadata=body.get("metadata"),
        )
    
    else:
        return ServiceResult.error_result(
            message=f"Invalid action: {action}. Valid actions: start, complete, fail, cancel, retry, progress",
            error_code=ErrorCode.VALIDATION_ERROR
        )
