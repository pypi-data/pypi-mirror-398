"""
WorkflowService for project workflow management.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from boto3_assist.dynamodb.dynamodb import DynamoDB
from geek_cafe_saas_sdk.core.services.database_service import DatabaseService
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.core.error_codes import ErrorCode
from geek_cafe_saas_sdk.modules.projects.models.project_workflow import (
    ProjectWorkflow,
    WorkflowStatus,
)
from geek_cafe_saas_sdk.modules.projects.models.workflow_step import (
    WorkflowStep,
    StepStatus,
)
from geek_cafe_saas_sdk.modules.projects.models.project_activity import ActivityType, EntityType


class WorkflowService(DatabaseService[ProjectWorkflow]):
    """
    Workflow service for project workflow management.
    
    Handles:
    - Workflow CRUD operations
    - Workflow step management
    - Workflow advancement
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._activity_service = None
    
    @property
    def activity_service(self):
        """Lazy-load activity service."""
        if self._activity_service is None:
            from geek_cafe_saas_sdk.modules.projects.services.activity_service import ActivityService
            self._activity_service = ActivityService(
                dynamodb=self.dynamodb,
                table_name=self.table_name,
                request_context=self.request_context,
            )
        return self._activity_service
    
    def create(self, **kwargs) -> ServiceResult[ProjectWorkflow]:
        """
        Create a new workflow.
        
        Args:
            project_id: Project ID (required)
            name: Workflow name (required)
            description: Workflow description
            is_primary: Whether this is the primary workflow
            
        Returns:
            ServiceResult with ProjectWorkflow model
        """
        self.request_context.require_authentication()
        tenant_id = self.request_context.target_tenant_id
        user_id = self.request_context.target_user_id
        
        try:
            project_id = kwargs.get("project_id")
            name = kwargs.get("name")
            
            if not project_id:
                return ServiceResult.error_result(
                    message="project_id is required",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            if not name or not name.strip():
                return ServiceResult.error_result(
                    message="name is required",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            # Create workflow model
            workflow = ProjectWorkflow()
            workflow.tenant_id = tenant_id
            workflow.owner_id = user_id
            workflow.user_id = user_id
            workflow.project_id = project_id
            workflow.name = name.strip()
            workflow.status = WorkflowStatus.DRAFT
            
            # Optional fields
            if kwargs.get("description"):
                workflow.description = kwargs.get("description")
            if kwargs.get("is_primary") is not None:
                workflow.is_primary = kwargs.get("is_primary")
            
            # Save
            workflow.prep_for_save()
            save_result = self._save_model(workflow)
            
            if not save_result.success:
                return save_result
            
            # Log activity
            self.activity_service.log_activity(
                project_id=project_id,
                activity_type=ActivityType.WORKFLOW_CREATED,
                summary=f"Workflow '{name}' created",
                entity_type=EntityType.WORKFLOW,
                entity_id=workflow.workflow_id,
                entity_name=name,
            )
            
            return save_result
            
        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="WorkflowService.create"
            )
    
    def get_by_id(self, workflow_id: str, **kwargs) -> ServiceResult[ProjectWorkflow]:
        """
        Get workflow by ID.
        
        Args:
            workflow_id: Workflow ID
            project_id: Project ID (required for adjacency pattern)
            
        Returns:
            ServiceResult with ProjectWorkflow model
        """
        project_id = kwargs.get("project_id")
        if not project_id:
            return ServiceResult.error_result(
                message="project_id is required to get workflow",
                error_code=ErrorCode.VALIDATION_ERROR
            )
        
        self.request_context.require_authentication()
        
        try:
            # Build query model for adjacency pattern
            query_model = ProjectWorkflow()
            query_model.project_id = project_id
            query_model.id = workflow_id
            
            key = query_model.get_key("primary")
            response = self.dynamodb.query(
                table_name=self.table_name,
                key=key,
                limit=1,
            )
            
            items = response.get("Items", [])
            if not items:
                return ServiceResult.error_result(
                    message=f"Workflow not found: {workflow_id}",
                    error_code=ErrorCode.NOT_FOUND
                )
            
            workflow = ProjectWorkflow().map(items[0])
            return ServiceResult.success_result(workflow)
            
        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="WorkflowService.get_by_id"
            )
    
    def update(self, workflow_id: str, **kwargs) -> ServiceResult[ProjectWorkflow]:
        """
        Update a workflow.
        
        Args:
            workflow_id: Workflow ID
            project_id: Project ID (required)
            updates: Dict of fields to update
            
        Returns:
            ServiceResult with updated ProjectWorkflow model
        """
        project_id = kwargs.get("project_id")
        updates = kwargs.get("updates", {})
        
        if not project_id:
            return ServiceResult.error_result(
                message="project_id is required",
                error_code=ErrorCode.VALIDATION_ERROR
            )
        
        self.request_context.require_authentication()
        
        try:
            # Get existing workflow
            get_result = self.get_by_id(workflow_id, project_id=project_id)
            if not get_result.success:
                return get_result
            
            old_workflow = get_result.data
            workflow = ProjectWorkflow().map(old_workflow.to_dictionary())
            
            # Apply updates
            if "name" in updates:
                workflow.name = updates["name"]
            if "description" in updates:
                workflow.description = updates["description"]
            if "is_primary" in updates:
                workflow.is_primary = updates["is_primary"]
            if "status" in updates:
                workflow.status = updates["status"]
            
            # Save with change tracking
            workflow.prep_for_save()
            return self._save_model(workflow, old_model=old_workflow)
            
        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="WorkflowService.update"
            )
    
    def delete(self, workflow_id: str, **kwargs) -> ServiceResult[bool]:
        """
        Delete a workflow (soft delete by archiving).
        
        Args:
            workflow_id: Workflow ID
            project_id: Project ID (required)
            
        Returns:
            ServiceResult with success boolean
        """
        project_id = kwargs.get("project_id")
        
        if not project_id:
            return ServiceResult.error_result(
                message="project_id is required",
                error_code=ErrorCode.VALIDATION_ERROR
            )
        
        result = self.update(
            workflow_id,
            project_id=project_id,
            updates={"status": WorkflowStatus.ARCHIVED},
        )
        
        if result.success:
            return ServiceResult.success_result(True)
        
        return ServiceResult.error_result(
            message=result.message,
            error_code=result.error_code
        )
    
    # ========================================
    # Workflow Step Operations
    # ========================================
    
    def add_step(
        self,
        workflow_id: str,
        project_id: str,
        name: str,
        *,
        description: Optional[str] = None,
        sort_order: Optional[int] = None,
        expected_duration_days: Optional[int] = None,
        entry_criteria: Optional[str] = None,
        exit_criteria: Optional[str] = None,
    ) -> ServiceResult[WorkflowStep]:
        """
        Add a step to a workflow.
        
        Args:
            workflow_id: Workflow ID
            project_id: Project ID
            name: Step name
            description: Step description
            sort_order: Step order (auto-assigned if not provided)
            expected_duration_days: Expected duration
            entry_criteria: Entry criteria text
            exit_criteria: Exit criteria text
            
        Returns:
            ServiceResult with WorkflowStep model
        """
        self.request_context.require_authentication()
        tenant_id = self.request_context.target_tenant_id
        user_id = self.request_context.target_user_id
        
        try:
            if not name or not name.strip():
                return ServiceResult.error_result(
                    message="name is required",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            # Get workflow to verify it exists and get step count
            workflow_result = self.get_by_id(workflow_id, project_id=project_id)
            if not workflow_result.success:
                return ServiceResult.error_result(
                    message=workflow_result.message,
                    error_code=workflow_result.error_code
                )
            
            workflow = workflow_result.data
            
            # Determine sort order
            if sort_order is None:
                sort_order = workflow.step_count + 1
            
            # Create step model
            step = WorkflowStep()
            step.tenant_id = tenant_id
            step.owner_id = user_id
            step.user_id = user_id
            step.workflow_id = workflow_id
            step.project_id = project_id
            step.name = name.strip()
            step.sort_order = sort_order
            step.status = StepStatus.NOT_STARTED
            
            # Optional fields
            if description:
                step.description = description
            if expected_duration_days:
                step.expected_duration_days = expected_duration_days
            if entry_criteria:
                step.entry_criteria = entry_criteria
            if exit_criteria:
                step.exit_criteria = exit_criteria
            
            # Save step
            step.prep_for_save()
            save_result = self._save_model(step)
            
            if not save_result.success:
                return save_result
            
            # Update workflow step count
            workflow.increment_step_count()
            workflow.prep_for_save()
            self._save_model(workflow)
            
            # Log activity
            self.activity_service.log_activity(
                project_id=project_id,
                activity_type=ActivityType.WORKFLOW_STEP_ADDED,
                summary=f"Step '{name}' added to workflow",
                entity_type=EntityType.WORKFLOW_STEP,
                entity_id=step.step_id,
                entity_name=name,
                details={"workflow_id": workflow_id, "sort_order": sort_order},
            )
            
            return save_result
            
        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="WorkflowService.add_step"
            )
    
    def get_step(
        self,
        step_id: str,
        project_id: str,
        workflow_id: str,
        sort_order: int,
    ) -> ServiceResult[WorkflowStep]:
        """
        Get a workflow step.
        
        Args:
            step_id: Step ID
            project_id: Project ID
            workflow_id: Workflow ID
            sort_order: Step sort order
            
        Returns:
            ServiceResult with WorkflowStep model
        """
        self.request_context.require_authentication()
        
        try:
            # Build query model for adjacency pattern
            query_model = WorkflowStep()
            query_model.project_id = project_id
            query_model.workflow_id = workflow_id
            query_model.sort_order = sort_order
            
            key = query_model.get_key("primary")
            response = self.dynamodb.query(
                table_name=self.table_name,
                key=key,
                limit=1,
            )
            
            items = response.get("Items", [])
            if not items:
                return ServiceResult.error_result(
                    message=f"Step not found: {step_id}",
                    error_code=ErrorCode.NOT_FOUND
                )
            
            step = WorkflowStep().map(items[0])
            return ServiceResult.success_result(step)
            
        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="WorkflowService.get_step"
            )
    
    def modify_step(
        self,
        step_id: str,
        project_id: str,
        workflow_id: str,
        sort_order: int,
        updates: Dict[str, Any],
    ) -> ServiceResult[WorkflowStep]:
        """
        Modify a workflow step.
        
        Args:
            step_id: Step ID
            project_id: Project ID
            workflow_id: Workflow ID
            sort_order: Current sort order
            updates: Dict of fields to update
            
        Returns:
            ServiceResult with updated WorkflowStep model
        """
        self.request_context.require_authentication()
        
        try:
            # Get existing step
            get_result = self.get_step(step_id, project_id, workflow_id, sort_order)
            if not get_result.success:
                return get_result
            
            old_step = get_result.data
            step = WorkflowStep().map(old_step.to_dictionary())
            
            # Apply updates
            if "name" in updates:
                step.name = updates["name"]
            if "description" in updates:
                step.description = updates["description"]
            if "expected_duration_days" in updates:
                step.expected_duration_days = updates["expected_duration_days"]
            if "entry_criteria" in updates:
                step.entry_criteria = updates["entry_criteria"]
            if "exit_criteria" in updates:
                step.exit_criteria = updates["exit_criteria"]
            
            # Save with change tracking
            step.prep_for_save()
            save_result = self._save_model(step, old_model=old_step)
            
            if not save_result.success:
                return save_result
            
            # Log activity
            self.activity_service.log_activity(
                project_id=project_id,
                activity_type=ActivityType.WORKFLOW_STEP_MODIFIED,
                summary=f"Step '{step.name}' modified",
                entity_type=EntityType.WORKFLOW_STEP,
                entity_id=step_id,
                entity_name=step.name,
                details={"updated_fields": list(updates.keys())},
            )
            
            return save_result
            
        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="WorkflowService.modify_step"
            )
    
    def advance_workflow(
        self,
        workflow_id: str,
        project_id: str,
    ) -> ServiceResult[ProjectWorkflow]:
        """
        Advance workflow to the next step.
        
        Marks current step as completed and next step as in_progress.
        
        Args:
            workflow_id: Workflow ID
            project_id: Project ID
            
        Returns:
            ServiceResult with updated ProjectWorkflow model
        """
        self.request_context.require_authentication()
        
        try:
            # Get workflow
            workflow_result = self.get_by_id(workflow_id, project_id=project_id)
            if not workflow_result.success:
                return workflow_result
            
            workflow = workflow_result.data
            
            # Get all steps
            steps_result = self.get_workflow_with_steps(workflow_id, project_id)
            if not steps_result.success:
                return ServiceResult.error_result(
                    message=steps_result.message,
                    error_code=steps_result.error_code
                )
            
            steps = steps_result.data.get("steps", [])
            if not steps:
                return ServiceResult.error_result(
                    message="Workflow has no steps",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            # Find current step (in_progress) and next step
            current_step = None
            next_step = None
            
            for i, step in enumerate(steps):
                if step.status == StepStatus.IN_PROGRESS:
                    current_step = step
                    if i + 1 < len(steps):
                        next_step = steps[i + 1]
                    break
            
            # If no current step, start the first one
            if current_step is None:
                first_step = steps[0]
                if first_step.status == StepStatus.NOT_STARTED:
                    first_step.status = StepStatus.IN_PROGRESS
                    first_step.started_at = datetime.now(timezone.utc).isoformat()
                    first_step.prep_for_save()
                    self._save_model(first_step)
                    
                    workflow.current_step_order = first_step.sort_order
                    workflow.prep_for_save()
                    self._save_model(workflow)
                    
                    self.activity_service.log_activity(
                        project_id=project_id,
                        activity_type=ActivityType.WORKFLOW_STEP_STARTED,
                        summary=f"Step '{first_step.name}' started",
                        entity_type=EntityType.WORKFLOW_STEP,
                        entity_id=first_step.step_id,
                        entity_name=first_step.name,
                    )
                    
                    return ServiceResult.success_result(workflow)
            
            # Complete current step
            if current_step:
                current_step.status = StepStatus.COMPLETED
                current_step.completed_at = datetime.now(timezone.utc).isoformat()
                current_step.prep_for_save()
                self._save_model(current_step)
                
                workflow.increment_completed_step_count()
                
                self.activity_service.log_activity(
                    project_id=project_id,
                    activity_type=ActivityType.WORKFLOW_STEP_COMPLETED,
                    summary=f"Step '{current_step.name}' completed",
                    entity_type=EntityType.WORKFLOW_STEP,
                    entity_id=current_step.step_id,
                    entity_name=current_step.name,
                )
            
            # Start next step if available
            if next_step:
                next_step.status = StepStatus.IN_PROGRESS
                next_step.started_at = datetime.now(timezone.utc).isoformat()
                next_step.prep_for_save()
                self._save_model(next_step)
                
                workflow.current_step_order = next_step.sort_order
                
                self.activity_service.log_activity(
                    project_id=project_id,
                    activity_type=ActivityType.WORKFLOW_STEP_STARTED,
                    summary=f"Step '{next_step.name}' started",
                    entity_type=EntityType.WORKFLOW_STEP,
                    entity_id=next_step.step_id,
                    entity_name=next_step.name,
                )
            else:
                workflow.current_step_order = None
            
            # Save workflow
            workflow.prep_for_save()
            return self._save_model(workflow)
            
        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="WorkflowService.advance_workflow"
            )
    
    def get_workflow_with_steps(
        self,
        workflow_id: str,
        project_id: str,
    ) -> ServiceResult[Dict[str, Any]]:
        """
        Get workflow with all its steps.
        
        Args:
            workflow_id: Workflow ID
            project_id: Project ID
            
        Returns:
            ServiceResult with dict containing workflow and steps
        """
        self.request_context.require_authentication()
        
        try:
            # Get workflow
            workflow_result = self.get_by_id(workflow_id, project_id=project_id)
            if not workflow_result.success:
                return ServiceResult.error_result(
                    message=workflow_result.message,
                    error_code=workflow_result.error_code
                )
            
            workflow = workflow_result.data
            
            # Build query model for steps within this workflow
            query_model = WorkflowStep()
            query_model.project_id = project_id
            query_model.workflow_id = workflow_id
            # Leave sort_order empty for begins_with query
            
            key = query_model.get_key("primary").key(query_key=True, condition="begins_with")
            
            response = self.dynamodb.query(key=key, table_name=self.table_name)
            items = response.get("Items", [])
            steps = [WorkflowStep().map(item) for item in items]
            
            return ServiceResult.success_result({
                "workflow": workflow,
                "steps": steps,
            })
            
        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="WorkflowService.get_workflow_with_steps"
            )
    
    def list_workflows(
        self,
        project_id: str,
        *,
        limit: int = 10,
    ) -> ServiceResult[List[ProjectWorkflow]]:
        """
        List workflows for a project.
        
        Args:
            project_id: Project ID
            limit: Maximum number of workflows to return
            
        Returns:
            ServiceResult with list of ProjectWorkflow models
        """
        self.request_context.require_authentication()
        
        try:
            # Build query model with project_id set, id empty for begins_with
            query_model = ProjectWorkflow()
            query_model.project_id = project_id
            
            key = query_model.get_key("primary").key(query_key=True, condition="begins_with")
            
            response = self.dynamodb.query(
                key=key,
                table_name=self.table_name,
                limit=limit,
                ascending=True,
            )
            
            items = response.get("Items", [])
            workflows = [ProjectWorkflow().map(item) for item in items]
            
            return ServiceResult.success_result(workflows)
            
        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="WorkflowService.list_workflows"
            )
