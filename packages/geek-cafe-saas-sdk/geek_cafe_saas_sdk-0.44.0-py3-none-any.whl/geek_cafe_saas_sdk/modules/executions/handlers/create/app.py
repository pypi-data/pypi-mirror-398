"""
Create Execution Lambda Handler.

POST /executions

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from typing import Any
from geek_cafe_saas_sdk.lambda_handlers import BaseLambdaHandler, LambdaEvent
from geek_cafe_saas_sdk.modules.executions.services import ExecutionService

handler_wrapper = BaseLambdaHandler(
    service_class=ExecutionService,
    require_auth=True,
    require_body=True,
)


def handler(event: dict, context: Any) -> dict:
    """Lambda entry point."""
    return handler_wrapper.execute(event, context, create_execution)


def create_execution(
    event: LambdaEvent,
    service: ExecutionService
) -> Any:
    """
    Create a new execution record.
    
    Request body:
        name: str (required) - Human-readable name
        execution_type: str - Type (step_function, lambda, sqs, etc.)
        parent_id: str - Parent execution ID for child executions
        correlation_id: str - Correlation ID for cross-service tracking
        idempotency_key: str - Key to prevent duplicate processing
        description: str - Optional description
        resource_arn: str - AWS ARN of the resource
        execution_arn: str - Specific execution ARN
        triggered_by: str - What initiated this (s3_event, api_call, etc.)
        triggered_by_id: str - ID of the trigger
        resource_id: str - ID of the resource being processed
        resource_type: str - Type of resource (file, directory, etc.)
        input_payload: dict - Input data for the execution
        total_steps: int - Total number of steps if known
        max_retries: int - Maximum retry attempts (default: 3)
        ttl_days: int - Days until auto-expiration (None = no TTL)
        metadata: dict - Additional metadata
    """
    body = event.body
    
    return service.create(
        name=body.get("name"),
        execution_type=body.get("execution_type", "custom"),
        parent_id=body.get("parent_id"),
        correlation_id=body.get("correlation_id"),
        idempotency_key=body.get("idempotency_key"),
        description=body.get("description"),
        resource_arn=body.get("resource_arn"),
        execution_arn=body.get("execution_arn"),
        triggered_by=body.get("triggered_by"),
        triggered_by_id=body.get("triggered_by_id"),
        resource_id=body.get("resource_id"),
        resource_type=body.get("resource_type"),
        input_payload=body.get("input_payload"),
        total_steps=body.get("total_steps"),
        max_retries=body.get("max_retries", 3),
        ttl_days=body.get("ttl_days"),
        metadata=body.get("metadata"),
    )
