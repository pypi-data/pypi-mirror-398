"""
Execution service for async task/workflow execution tracking.

Provides CRUD operations and query methods for tracking executions.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

import time
import uuid
from datetime import datetime, UTC, timedelta
from typing import Optional, Dict, Any, List

from aws_lambda_powertools import Logger
from boto3_assist.dynamodb.dynamodb import DynamoDB

from geek_cafe_saas_sdk.core.services.database_service import DatabaseService
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.core.error_codes import ErrorCode
from geek_cafe_saas_sdk.core.request_context import RequestContext
from geek_cafe_saas_sdk.lambda_handlers._base.decorators import service_method
from geek_cafe_saas_sdk.core.services.resource_meta_entry_service import (
    ResourceMetaEntryService,
)
from ..models.execution import Execution, ExecutionStatus, ExecutionType

logger = Logger()


class ExecutionService(DatabaseService[Execution]):
    """
    Service for managing execution tracking.
    
    Provides methods for creating, updating, and querying executions
    with support for hierarchical tracking (root_id, parent_id).
    """

    def __init__(
        self,
        dynamodb: DynamoDB,
        table_name: str,
        request_context: Optional[RequestContext] = None,
        **kwargs
    ):
        super().__init__(
            dynamodb=dynamodb,
            table_name=table_name,
            request_context=request_context,
            **kwargs
        )

        self._resource_meta_entry_service: Optional[ResourceMetaEntryService] = None
    # =========================================================================
    # Create Operations
    # =========================================================================

    @service_method("create_execution")
    def create(
        self,
        name: str,
        execution_type: str = ExecutionType.CUSTOM,
        parent_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        description: Optional[str] = None,
        resource_arn: Optional[str] = None,
        execution_arn: Optional[str] = None,
        triggered_by: Optional[str] = None,
        triggered_by_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        input_payload: Optional[Dict[str, Any]] = None,
        total_steps: Optional[int] = None,
        max_retries: int = 3,
        ttl_days: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ServiceResult[Execution]:
        """
        Create a new execution record.
        
        Args:
            name: Human-readable name for the execution
            execution_type: Type of execution (step_function, lambda, sqs, etc.)
            parent_id: Parent execution ID (for child executions)
            correlation_id: Correlation ID for cross-service tracking
            idempotency_key: Key to prevent duplicate processing
            description: Optional description
            resource_arn: AWS ARN of the resource (Step Function ARN, etc.)
            execution_arn: Specific execution ARN
            triggered_by: What initiated this (s3_event, api_call, schedule, etc.)
            triggered_by_id: ID of the trigger
            resource_id: ID of the resource being processed
            resource_type: Type of resource (file, directory, etc.)
            input_payload: Input data for the execution
            total_steps: Total number of steps if known
            max_retries: Maximum retry attempts (default: 3)
            ttl_days: Days until auto-expiration (None = no TTL)
            metadata: Additional metadata
            
        Returns:
            ServiceResult with created Execution
        """
        try:
            # Check for duplicate via idempotency key
            if idempotency_key:
                existing = self._find_by_idempotency_key(idempotency_key)
                if existing:
                    logger.info(f"Returning existing execution for idempotency_key: {idempotency_key}")
                    return ServiceResult.success_result(existing)
            
            execution = Execution()
            execution.id = str(uuid.uuid4())
            execution.name = name
            execution.execution_type = execution_type
            execution.description = description
            execution.status = ExecutionStatus.PENDING
            
            # Hierarchy
            if parent_id:
                # Get parent to inherit root_id
                parent = self._get_by_id(parent_id, Execution)
                if parent:
                    execution.parent_id = parent_id
                    execution.root_id = parent.root_id  # Inherit root from parent
                    # Update parent's child count
                    self._increment_child_count(parent_id)
                else:
                    logger.warning(f"Parent execution {parent_id} not found, creating as root")
                    execution.root_id = execution.id
            else:
                # This is a root execution
                execution.root_id = execution.id
            
            # Correlation
            execution.correlation_id = correlation_id or str(uuid.uuid4())
            execution.idempotency_key = idempotency_key
            
            # AWS resources
            execution.resource_arn = resource_arn
            execution.execution_arn = execution_arn
            
            # Context
            execution.triggered_by = triggered_by
            execution.triggered_by_id = triggered_by_id
            
            # Linked resource
            execution.resource_id = resource_id
            execution.resource_type = resource_type
            
            # Input/Output
            execution.input_payload = input_payload
            
            # Progress
            execution.total_steps = total_steps
            execution.progress_percent = 0
            
            # Retries
            execution.max_retries = max_retries
            execution.retry_count = 0
            
            # TTL (optional)
            if ttl_days:
                ttl_timestamp = int((datetime.now(UTC) + timedelta(days=ttl_days)).timestamp())
                execution.ttl = ttl_timestamp
            
            # Metadata
            execution.metadata = metadata
            
            # Inject security context from request
            if self.request_context:
                execution.tenant_id = self.request_context.authenticated_tenant_id
                execution.owner_id = self.request_context.authenticated_user_id
                execution.user_id = self.request_context.authenticated_user_id
            
            # Save
            execution.prep_for_save()
            result = self._save_model(execution)
            
            if result.success:
                self._emit_execution_event("execution.created", execution)
            
            return result
            
        except Exception as e:
            logger.exception(f"Error creating execution: {e}")
            return ServiceResult.error_result(
                message=str(e),
                error_code=ErrorCode.INTERNAL_ERROR
            )

    # =========================================================================
    # Status Update Operations
    # =========================================================================

    @service_method("start_execution")
    def start(self, execution_id: str) -> ServiceResult[Execution]:
        """
        Mark an execution as started (RUNNING).
        
        Args:
            execution_id: ID of the execution to start
            
        Returns:
            ServiceResult with updated Execution
        """
        try:
            execution = self._get_by_id(execution_id, Execution)
            if not execution:
                return ServiceResult.error_result(
                    message=f"Execution {execution_id} not found",
                    error_code=ErrorCode.NOT_FOUND
                )
            
            if not ExecutionStatus.can_transition(execution.status, ExecutionStatus.RUNNING):
                return ServiceResult.error_result(
                    message=f"Cannot start execution in status '{execution.status}'",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            now = datetime.now(UTC)
            execution.status = ExecutionStatus.RUNNING
            execution.started_at = now.isoformat()
            execution.started_at_ts = now.timestamp()
            
            execution.prep_for_save()
            result = self._save_model(execution)
            
            if result.success:
                self._emit_execution_event("execution.started", execution)
            
            return result
            
        except Exception as e:
            logger.exception(f"Error starting execution: {e}")
            return ServiceResult.error_result(
                message=str(e),
                error_code=ErrorCode.INTERNAL_ERROR
            )

    @service_method("update_progress")
    def update_progress(
        self,
        execution_id: str,
        progress_percent: Optional[int] = None,
        current_step: Optional[str] = None,
        current_step_index: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ServiceResult[Execution]:
        """
        Update execution progress.
        
        Args:
            execution_id: ID of the execution
            progress_percent: Progress percentage (0-100)
            current_step: Current step name
            current_step_index: Current step index (0-based)
            metadata: Additional metadata to merge
            
        Returns:
            ServiceResult with updated Execution
        """
        try:
            execution = self._get_by_id(execution_id, Execution)
            if not execution:
                return ServiceResult.error_result(
                    message=f"Execution {execution_id} not found",
                    error_code=ErrorCode.NOT_FOUND
                )
            
            if execution.is_terminal:
                return ServiceResult.error_result(
                    message=f"Cannot update progress for terminal execution (status: {execution.status})",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            if progress_percent is not None:
                execution.progress_percent = progress_percent
            if current_step is not None:
                execution.current_step = current_step
            if current_step_index is not None:
                execution.current_step_index = current_step_index
            if metadata:
                existing = execution.metadata or {}
                existing.update(metadata)
                execution.metadata = existing
            
            execution.prep_for_save()
            result = self._save_model(execution)
            
            if result.success:
                self._emit_execution_event("execution.progress", execution)
            
            return result
            
        except Exception as e:
            logger.exception(f"Error updating execution progress: {e}")
            return ServiceResult.error_result(
                message=str(e),
                error_code=ErrorCode.INTERNAL_ERROR
            )

    @service_method("complete_execution")
    def complete(
        self,
        execution_id: str,
        output_payload: Optional[Dict[str, Any]] = None,
    ) -> ServiceResult[Execution]:
        """
        Mark an execution as successfully completed.
        
        Args:
            execution_id: ID of the execution
            output_payload: Result data from the execution
            
        Returns:
            ServiceResult with updated Execution
        """
        try:
            execution = self._get_by_id(execution_id, Execution)
            if not execution:
                return ServiceResult.error_result(
                    message=f"Execution {execution_id} not found",
                    error_code=ErrorCode.NOT_FOUND
                )
            
            if not ExecutionStatus.can_transition(execution.status, ExecutionStatus.SUCCEEDED):
                return ServiceResult.error_result(
                    message=f"Cannot complete execution in status '{execution.status}'",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            now = datetime.now(UTC)
            execution.status = ExecutionStatus.SUCCEEDED
            execution.completed_at = now.isoformat()
            execution.completed_at_ts = now.timestamp()
            execution.progress_percent = 100
            execution.output_payload = output_payload
            
            # Calculate duration
            if execution.started_at_ts:
                execution.duration_ms = int((now.timestamp() - execution.started_at_ts) * 1000)
            
            execution.prep_for_save()
            result = self._save_model(execution)
            
            if result.success:
                self._emit_execution_event("execution.succeeded", execution)
                # Update parent's completed child count
                if execution.parent_id:
                    self._increment_completed_child_count(execution.parent_id)
            
            return result
            
        except Exception as e:
            logger.exception(f"Error completing execution: {e}")
            return ServiceResult.error_result(
                message=str(e),
                error_code=ErrorCode.INTERNAL_ERROR
            )

    @service_method("fail_execution")
    def fail(
        self,
        execution_id: str,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
    ) -> ServiceResult[Execution]:
        """
        Mark an execution as failed.
        
        Args:
            execution_id: ID of the execution
            error_code: Error code
            error_message: Error message
            error_details: Additional error details
            
        Returns:
            ServiceResult with updated Execution
        """
        try:
            execution = self._get_by_id(execution_id, Execution)
            if not execution:
                return ServiceResult.error_result(
                    message=f"Execution {execution_id} not found",
                    error_code=ErrorCode.NOT_FOUND
                )
            
            if not ExecutionStatus.can_transition(execution.status, ExecutionStatus.FAILED):
                return ServiceResult.error_result(
                    message=f"Cannot fail execution in status '{execution.status}'",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            now = datetime.now(UTC)
            execution.status = ExecutionStatus.FAILED
            execution.completed_at = now.isoformat()
            execution.completed_at_ts = now.timestamp()
            execution.error_code = error_code
            execution.error_message = error_message
            execution.error_details = error_details
            
            # Calculate duration
            if execution.started_at_ts:
                execution.duration_ms = int((now.timestamp() - execution.started_at_ts) * 1000)
            
            execution.prep_for_save()
            result = self._save_model(execution)
            
            if result.success:
                self._emit_execution_event("execution.failed", execution)
                # Update parent's failed child count
                if execution.parent_id:
                    self._increment_failed_child_count(execution.parent_id)
            
            return result
            
        except Exception as e:
            logger.exception(f"Error failing execution: {e}")
            return ServiceResult.error_result(
                message=str(e),
                error_code=ErrorCode.INTERNAL_ERROR
            )

    @service_method("cancel_execution")
    def cancel(self, execution_id: str) -> ServiceResult[Execution]:
        """
        Cancel an execution.
        
        Args:
            execution_id: ID of the execution to cancel
            
        Returns:
            ServiceResult with updated Execution
        """
        try:
            execution = self._get_by_id(execution_id, Execution)
            if not execution:
                return ServiceResult.error_result(
                    message=f"Execution {execution_id} not found",
                    error_code=ErrorCode.NOT_FOUND
                )
            
            if not ExecutionStatus.can_transition(execution.status, ExecutionStatus.CANCELLED):
                return ServiceResult.error_result(
                    message=f"Cannot cancel execution in status '{execution.status}'",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            now = datetime.now(UTC)
            execution.status = ExecutionStatus.CANCELLED
            execution.completed_at = now.isoformat()
            execution.completed_at_ts = now.timestamp()
            
            # Calculate duration
            if execution.started_at_ts:
                execution.duration_ms = int((now.timestamp() - execution.started_at_ts) * 1000)
            
            execution.prep_for_save()
            result = self._save_model(execution)
            
            if result.success:
                self._emit_execution_event("execution.cancelled", execution)
            
            return result
            
        except Exception as e:
            logger.exception(f"Error cancelling execution: {e}")
            return ServiceResult.error_result(
                message=str(e),
                error_code=ErrorCode.INTERNAL_ERROR
            )

    @service_method("retry_execution")
    def retry(self, execution_id: str) -> ServiceResult[Execution]:
        """
        Retry a failed or timed-out execution.
        
        Args:
            execution_id: ID of the execution to retry
            
        Returns:
            ServiceResult with updated Execution (reset to PENDING)
        """
        try:
            execution = self._get_by_id(execution_id, Execution)
            if not execution:
                return ServiceResult.error_result(
                    message=f"Execution {execution_id} not found",
                    error_code=ErrorCode.NOT_FOUND
                )
            
            if not execution.can_retry:
                return ServiceResult.error_result(
                    message=f"Cannot retry execution (status: {execution.status}, retries: {execution.retry_count}/{execution.max_retries})",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            # Reset for retry
            execution.status = ExecutionStatus.PENDING
            execution.retry_count += 1
            execution.started_at = None
            execution.started_at_ts = None
            execution.completed_at = None
            execution.completed_at_ts = None
            execution.duration_ms = None
            execution.progress_percent = 0
            execution.current_step = None
            execution.current_step_index = None
            execution.error_code = None
            execution.error_message = None
            execution.error_details = None
            execution.output_payload = None
            
            execution.prep_for_save()
            result = self._save_model(execution)
            
            if result.success:
                self._emit_execution_event("execution.retried", execution)
            
            return result
            
        except Exception as e:
            logger.exception(f"Error retrying execution: {e}")
            return ServiceResult.error_result(
                message=str(e),
                error_code=ErrorCode.INTERNAL_ERROR
            )

    # =========================================================================
    # Read Operations
    # =========================================================================

    @service_method("get_execution")
    def get(self, execution_id: str) -> ServiceResult[Execution]:
        """
        Get an execution by ID.
        
        Args:
            execution_id: ID of the execution
            
        Returns:
            ServiceResult with Execution
        """
        try:
            execution = self._get_by_id(execution_id, Execution)
            if not execution:
                return ServiceResult.error_result(
                    message=f"Execution {execution_id} not found",
                    error_code=ErrorCode.NOT_FOUND
                )
            return ServiceResult.success_result(execution)
        except Exception as e:
            logger.exception(f"Error getting execution: {e}")
            return ServiceResult.error_result(
                message=str(e),
                error_code=ErrorCode.INTERNAL_ERROR
            )

    # =========================================================================
    # Abstract Method Implementations (required by DatabaseService)
    # =========================================================================

    def get_by_id(self, **kwargs) -> ServiceResult[Execution]:
        """
        Get execution by ID (abstract method implementation).
        
        Args:
            execution_id: ID of the execution
            
        Returns:
            ServiceResult with Execution
        """
        execution_id = kwargs.get("execution_id") or kwargs.get("id")
        return self.get(execution_id)

    def update(self, **kwargs) -> ServiceResult[Execution]:
        """
        Update execution (abstract method implementation).
        
        For executions, use specific methods like start(), complete(), fail(), etc.
        This generic update is provided for interface compliance.
        
        Args:
            execution_id: ID of the execution
            **kwargs: Fields to update
            
        Returns:
            ServiceResult with updated Execution
        """
        try:
            execution_id = kwargs.get("execution_id") or kwargs.get("id")
            execution = self._get_by_id(execution_id, Execution)
            if not execution:
                return ServiceResult.error_result(
                    message=f"Execution {execution_id} not found",
                    error_code=ErrorCode.NOT_FOUND
                )
            
            # Update allowed fields
            if "metadata" in kwargs:
                existing = execution.metadata or {}
                existing.update(kwargs["metadata"])
                execution.metadata = existing
            
            execution.prep_for_save()
            return self._save_model(execution)
            
        except Exception as e:
            logger.exception(f"Error updating execution: {e}")
            return ServiceResult.error_result(
                message=str(e),
                error_code=ErrorCode.INTERNAL_ERROR
            )

    def delete(self, **kwargs) -> ServiceResult[bool]:
        """
        Delete execution (abstract method implementation).
        
        Args:
            execution_id: ID of the execution to delete
            
        Returns:
            ServiceResult with boolean success
        """
        try:
            execution_id = kwargs.get("execution_id") or kwargs.get("id")
            execution = self._get_by_id(execution_id, Execution)
            if not execution:
                return ServiceResult.error_result(
                    message=f"Execution {execution_id} not found",
                    error_code=ErrorCode.NOT_FOUND
                )
            
            return self._delete_model(execution)
            
        except Exception as e:
            logger.exception(f"Error deleting execution: {e}")
            return ServiceResult.error_result(
                message=str(e),
                error_code=ErrorCode.INTERNAL_ERROR
            )

    @service_method("list_by_root")
    def list_by_root(
        self,
        root_id: str,
        limit: int = 50,
        ascending: bool = False,
    ) -> ServiceResult[List[Execution]]:
        """
        List all executions in a chain by root_id.
        
        Args:
            root_id: Root execution ID
            limit: Maximum results
            ascending: Sort order by started_at
            
        Returns:
            ServiceResult with list of Executions
        """
        try:
            user_id = self.request_context.authenticated_user_id
            tenant_id = self.request_context.authenticated_tenant_id
            
            query_model = Execution()
            query_model.tenant_id = tenant_id
            query_model.owner_id = user_id
            query_model.root_id = root_id
            
            return self._query_by_index(
                query_model, "gsi1", limit=limit, ascending=ascending
            )
            
        except Exception as e:
            logger.exception(f"Error listing executions by root: {e}")
            return ServiceResult.error_result(
                message=str(e),
                error_code=ErrorCode.INTERNAL_ERROR
            )

    @service_method("list_children")
    def list_children(
        self,
        parent_id: str,
        limit: int = 50,
        ascending: bool = False,
    ) -> ServiceResult[List[Execution]]:
        """
        List direct children of an execution.
        
        Args:
            parent_id: Parent execution ID
            limit: Maximum results
            ascending: Sort order by started_at
            
        Returns:
            ServiceResult with list of child Executions
        """
        try:
            user_id = self.request_context.authenticated_user_id
            tenant_id = self.request_context.authenticated_tenant_id
            
            query_model = Execution()
            query_model.tenant_id = tenant_id
            query_model.owner_id = user_id
            query_model.parent_id = parent_id
            
            return self._query_by_index(
                query_model, "gsi2", limit=limit, ascending=ascending
            )
            
        except Exception as e:
            logger.exception(f"Error listing child executions: {e}")
            return ServiceResult.error_result(
                message=str(e),
                error_code=ErrorCode.INTERNAL_ERROR
            )

    @service_method("list_by_status")
    def list_by_status(
        self,
        status: str,
        limit: int = 50,
        ascending: bool = False,
    ) -> ServiceResult[List[Execution]]:
        """
        List executions by status.
        
        Args:
            status: Execution status to filter by
            limit: Maximum results
            ascending: Sort order by started_at
            
        Returns:
            ServiceResult with list of Executions
        """
        try:
            user_id = self.request_context.authenticated_user_id
            tenant_id = self.request_context.authenticated_tenant_id
            
            query_model = Execution()
            query_model.tenant_id = tenant_id
            query_model.owner_id = user_id
            query_model.status = status
            
            return self._query_by_index(
                query_model, "gsi3", limit=limit, ascending=ascending
            )
            
        except Exception as e:
            logger.exception(f"Error listing executions by status: {e}")
            return ServiceResult.error_result(
                message=str(e),
                error_code=ErrorCode.INTERNAL_ERROR
            )

    @service_method("list_by_correlation")
    def list_by_correlation(
        self,
        correlation_id: str,
        limit: int = 50,
        ascending: bool = False,
    ) -> ServiceResult[List[Execution]]:
        """
        List executions by correlation ID (cross-service tracking).
        
        Args:
            correlation_id: Correlation ID
            limit: Maximum results
            ascending: Sort order by started_at
            
        Returns:
            ServiceResult with list of Executions
        """
        try:
            tenant_id = self.request_context.authenticated_tenant_id
            
            query_model = Execution()
            query_model.tenant_id = tenant_id
            query_model.correlation_id = correlation_id
            
            return self._query_by_index(
                query_model, "gsi4", limit=limit, ascending=ascending
            )
            
        except Exception as e:
            logger.exception(f"Error listing executions by correlation: {e}")
            return ServiceResult.error_result(
                message=str(e),
                error_code=ErrorCode.INTERNAL_ERROR
            )

    @service_method("list_by_resource")
    def list_by_resource(
        self,
        resource_type: str,
        resource_id: str,
        limit: int = 50,
        ascending: bool = False,
    ) -> ServiceResult[List[Execution]]:
        """
        List executions for a specific resource.
        
        Args:
            resource_type: Type of resource (file, directory, etc.)
            resource_id: ID of the resource
            limit: Maximum results
            ascending: Sort order by started_at
            
        Returns:
            ServiceResult with list of Executions
        """
        try:
            user_id = self.request_context.authenticated_user_id
            tenant_id = self.request_context.authenticated_tenant_id
            
            query_model = Execution()
            query_model.tenant_id = tenant_id
            query_model.owner_id = user_id
            query_model.resource_type = resource_type
            query_model.resource_id = resource_id
            
            return self._query_by_index(
                query_model, "gsi5", limit=limit, ascending=ascending
            )
            
        except Exception as e:
            logger.exception(f"Error listing executions by resource: {e}")
            return ServiceResult.error_result(
                message=str(e),
                error_code=ErrorCode.INTERNAL_ERROR
            )

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _find_by_idempotency_key(self, idempotency_key: str) -> Optional[Execution]:
        """Find an execution by idempotency key (scan - use sparingly)."""
        # Note: For production, consider adding a GSI for idempotency_key
        # For now, this is a simple scan with filter
        # This should be rare since idempotency is typically checked on creation
        return None  # TODO: Implement if needed

    def _increment_child_count(self, parent_id: str) -> None:
        """Increment the child_count of a parent execution."""
        try:
            parent = self._get_by_id(parent_id, Execution)
            if parent:
                parent.child_count += 1
                parent.prep_for_save()
                self._save_model(parent)
        except Exception as e:
            logger.warning(f"Failed to increment child count for {parent_id}: {e}")

    def _increment_completed_child_count(self, parent_id: str) -> None:
        """Increment the completed_child_count of a parent execution."""
        try:
            parent = self._get_by_id(parent_id, Execution)
            if parent:
                parent.completed_child_count += 1
                parent.prep_for_save()
                self._save_model(parent)
        except Exception as e:
            logger.warning(f"Failed to increment completed child count for {parent_id}: {e}")

    def _increment_failed_child_count(self, parent_id: str) -> None:
        """Increment the failed_child_count of a parent execution."""
        try:
            parent = self._get_by_id(parent_id, Execution)
            if parent:
                parent.failed_child_count += 1
                parent.prep_for_save()
                self._save_model(parent)
        except Exception as e:
            logger.warning(f"Failed to increment failed child count for {parent_id}: {e}")

    def _emit_execution_event(self, event_type: str, execution: Execution) -> None:
        """
        Emit an execution event (placeholder for future implementation).
        
        This will eventually publish to SNS/EventBridge for downstream consumers.
        
        Args:
            event_type: Type of event (execution.created, execution.started, etc.)
            execution: The execution that triggered the event
        """
        # TODO: Implement event emission to SNS/EventBridge
        logger.info(
            f"[EVENT NOT IMPLEMENTED] Would emit event: {event_type}",
            extra={
                "event_type": event_type,
                "execution_id": execution.id,
                "status": execution.status,
                "correlation_id": execution.correlation_id,
            }
        )

    @property
    def resource_meta_entry_service(self) -> ResourceMetaEntryService:
        """Lazy-loaded resource meta entry service."""
        if self._resource_meta_entry_service is None:
            self._resource_meta_entry_service = ResourceMetaEntryService(
                dynamodb=self.dynamodb,
                table_name=self.table_name,
                request_context=self.request_context,
                resource_type="execution",
            )
        return self._resource_meta_entry_service