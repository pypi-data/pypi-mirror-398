"""
TaskService for project task management.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from boto3_assist.dynamodb.dynamodb import DynamoDB
from geek_cafe_saas_sdk.core.services.database_service import DatabaseService
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.core.error_codes import ErrorCode
from geek_cafe_saas_sdk.modules.projects.models.project_task import (
    ProjectTask,
    TaskStatus,
    TaskPriority,
)
from geek_cafe_saas_sdk.modules.projects.models.project_activity import ActivityType, EntityType


class TaskService(DatabaseService[ProjectTask]):
    """
    Task service for project task management.
    
    Handles:
    - Task CRUD operations
    - Task status transitions
    - Task assignment
    - Listing tasks by project or assignee
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._activity_service = None
        self._keyword_service = None
    
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
    
    @property
    def keyword_service(self):
        """Lazy-load keyword search service."""
        if self._keyword_service is None:
            from geek_cafe_saas_sdk.core.services.keyword_search_service import KeywordSearchService
            self._keyword_service = KeywordSearchService(
                dynamodb=self.dynamodb,
                table_name=self.table_name,
                request_context=self.request_context,
            )
        return self._keyword_service
    
    def create(self, **kwargs) -> ServiceResult[ProjectTask]:
        """
        Create a new task.
        
        Args:
            project_id: Project ID (required)
            title: Task title (required)
            description: Task description
            priority: Task priority
            assignee_user_id: Assigned user ID
            due_date: Due date (ISO format)
            milestone_id: Linked milestone ID
            workflow_step_id: Linked workflow step ID
            tags: List of tags
            
        Returns:
            ServiceResult with ProjectTask model
        """
        self.request_context.require_authentication()
        tenant_id = self.request_context.target_tenant_id
        user_id = self.request_context.target_user_id
        
        try:
            project_id = kwargs.get("project_id")
            title = kwargs.get("title")
            
            if not project_id:
                return ServiceResult.error_result(
                    message="project_id is required",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            if not title or not title.strip():
                return ServiceResult.error_result(
                    message="title is required",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            # Create task model
            task = ProjectTask()
            task.tenant_id = tenant_id
            task.owner_id = user_id
            task.user_id = user_id
            task.project_id = project_id
            task.title = title.strip()
            task.reporter_user_id = user_id
            task.status = TaskStatus.TODO
            
            # Optional fields
            if kwargs.get("description"):
                task.description = kwargs.get("description")
            if kwargs.get("priority"):
                task.priority = kwargs.get("priority")
            if kwargs.get("assignee_user_id"):
                task.assignee_user_id = kwargs.get("assignee_user_id")
            if kwargs.get("due_date"):
                task.due_date = kwargs.get("due_date")
            if kwargs.get("milestone_id"):
                task.milestone_id = kwargs.get("milestone_id")
            if kwargs.get("workflow_step_id"):
                task.workflow_step_id = kwargs.get("workflow_step_id")
            if kwargs.get("tags"):
                task.tags = kwargs.get("tags")
            
            # Save
            task.prep_for_save()
            save_result = self._save_model(task)
            
            if not save_result.success:
                return save_result
            
            # Log activity
            self.activity_service.log_activity(
                project_id=project_id,
                activity_type=ActivityType.TASK_CREATED,
                summary=f"Task '{title}' created",
                entity_type=EntityType.TASK,
                entity_id=task.task_id,
                entity_name=title,
            )
            
            # Update keyword search
            self._update_task_keywords(task)
            
            return save_result
            
        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="TaskService.create"
            )
    
    def get_by_id(self, task_id: str, **kwargs) -> ServiceResult[ProjectTask]:
        """
        Get task by ID.
        
        Args:
            task_id: Task ID
            project_id: Project ID (required for adjacency pattern)
            
        Returns:
            ServiceResult with ProjectTask model
        """
        project_id = kwargs.get("project_id")
        if not project_id:
            return ServiceResult.error_result(
                message="project_id is required to get task",
                error_code=ErrorCode.VALIDATION_ERROR
            )
        
        self.request_context.require_authentication()
        
        try:
            # Build query model for adjacency pattern
            query_model = ProjectTask()
            query_model.project_id = project_id
            query_model.id = task_id
            
            key = query_model.get_key("primary")
            response = self.dynamodb.query(
                table_name=self.table_name,
                key=key,
                limit=1,
            )
            
            items = response.get("Items", [])
            if not items:
                return ServiceResult.error_result(
                    message=f"Task not found: {task_id}",
                    error_code=ErrorCode.NOT_FOUND
                )
            
            task = ProjectTask().map(items[0])
            return ServiceResult.success_result(task)
            
        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="TaskService.get_by_id"
            )
    
    def update(self, task_id: str, **kwargs) -> ServiceResult[ProjectTask]:
        """
        Update a task.
        
        Args:
            task_id: Task ID
            project_id: Project ID (required)
            updates: Dict of fields to update
            
        Returns:
            ServiceResult with updated ProjectTask model
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
            # Get existing task
            get_result = self.get_by_id(task_id, project_id=project_id)
            if not get_result.success:
                return get_result
            
            old_task = get_result.data
            task = ProjectTask().map(old_task.to_dictionary())
            
            # Apply updates
            if "title" in updates:
                task.title = updates["title"]
            if "description" in updates:
                task.description = updates["description"]
            if "priority" in updates:
                task.priority = updates["priority"]
            if "due_date" in updates:
                task.due_date = updates["due_date"]
            if "milestone_id" in updates:
                task.milestone_id = updates["milestone_id"]
            if "workflow_step_id" in updates:
                task.workflow_step_id = updates["workflow_step_id"]
            if "tags" in updates:
                task.tags = updates["tags"]
            
            # Save with change tracking
            task.prep_for_save()
            save_result = self._save_model(task, old_model=old_task)
            
            if not save_result.success:
                return save_result
            
            # Log activity
            self.activity_service.log_activity(
                project_id=project_id,
                activity_type=ActivityType.TASK_MODIFIED,
                summary=f"Task '{task.title}' updated",
                entity_type=EntityType.TASK,
                entity_id=task_id,
                entity_name=task.title,
                details={"updated_fields": list(updates.keys())},
            )
            
            # Update keyword search
            self._update_task_keywords(task)
            
            return save_result
            
        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="TaskService.update"
            )
    
    def delete(self, task_id: str, **kwargs) -> ServiceResult[bool]:
        """
        Delete a task (soft delete by setting status to cancelled).
        
        Args:
            task_id: Task ID
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
        
        # Soft delete by changing status
        result = self.change_task_status(
            task_id=task_id,
            project_id=project_id,
            new_status=TaskStatus.CANCELLED,
        )
        
        if result.success:
            # Clean up keywords
            self.keyword_service.delete_resource_keywords(
                resource_type="task",
                resource_id=task_id,
            )
            return ServiceResult.success_result(True)
        
        return ServiceResult.error_result(
            message=result.message,
            error_code=result.error_code
        )
    
    def change_task_status(
        self,
        task_id: str,
        project_id: str,
        new_status: str,
    ) -> ServiceResult[ProjectTask]:
        """
        Change task status with validation.
        
        Args:
            task_id: Task ID
            project_id: Project ID
            new_status: New status
            
        Returns:
            ServiceResult with updated ProjectTask model
        """
        self.request_context.require_authentication()
        
        try:
            if new_status not in TaskStatus.ALL:
                return ServiceResult.error_result(
                    message=f"Invalid status: {new_status}",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            # Get existing task
            get_result = self.get_by_id(task_id, project_id=project_id)
            if not get_result.success:
                return get_result
            
            old_task = get_result.data
            old_status = old_task.status
            
            # Validate transition
            if not old_task.can_transition_to(new_status):
                return ServiceResult.error_result(
                    message=f"Cannot transition from {old_status} to {new_status}",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            # Create updated task
            task = ProjectTask().map(old_task.to_dictionary())
            task.status = new_status
            
            # Set completed date if transitioning to done
            if new_status == TaskStatus.DONE:
                task.completed_date = datetime.now(timezone.utc).isoformat()
            elif old_status == TaskStatus.DONE:
                task.completed_date = None
            
            # Save
            task.prep_for_save()
            save_result = self._save_model(task, old_model=old_task)
            
            if not save_result.success:
                return save_result
            
            # Determine activity type
            if new_status == TaskStatus.DONE:
                activity_type = ActivityType.TASK_COMPLETED
            else:
                activity_type = ActivityType.TASK_STATUS_CHANGED
            
            # Log activity
            self.activity_service.log_activity(
                project_id=project_id,
                activity_type=activity_type,
                summary=f"Task '{task.title}' status changed from {old_status} to {new_status}",
                entity_type=EntityType.TASK,
                entity_id=task_id,
                entity_name=task.title,
                details={"old_status": old_status, "new_status": new_status},
            )
            
            return save_result
            
        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="TaskService.change_task_status"
            )
    
    def assign_task(
        self,
        task_id: str,
        project_id: str,
        assignee_user_id: Optional[str],
    ) -> ServiceResult[ProjectTask]:
        """
        Assign or unassign a task.
        
        Args:
            task_id: Task ID
            project_id: Project ID
            assignee_user_id: User ID to assign (None to unassign)
            
        Returns:
            ServiceResult with updated ProjectTask model
        """
        self.request_context.require_authentication()
        
        try:
            # Get existing task
            get_result = self.get_by_id(task_id, project_id=project_id)
            if not get_result.success:
                return get_result
            
            old_task = get_result.data
            old_assignee = old_task.assignee_user_id
            
            # Create updated task
            task = ProjectTask().map(old_task.to_dictionary())
            task.assignee_user_id = assignee_user_id
            
            # Save
            task.prep_for_save()
            save_result = self._save_model(task, old_model=old_task)
            
            if not save_result.success:
                return save_result
            
            # Log activity
            if assignee_user_id:
                activity_type = ActivityType.TASK_ASSIGNED
                summary = f"Task '{task.title}' assigned to {assignee_user_id}"
            else:
                activity_type = ActivityType.TASK_UNASSIGNED
                summary = f"Task '{task.title}' unassigned"
            
            self.activity_service.log_activity(
                project_id=project_id,
                activity_type=activity_type,
                summary=summary,
                entity_type=EntityType.TASK,
                entity_id=task_id,
                entity_name=task.title,
                details={"old_assignee": old_assignee, "new_assignee": assignee_user_id},
            )
            
            return save_result
            
        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="TaskService.assign_task"
            )
    
    def list_tasks_for_project(
        self,
        project_id: str,
        *,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> ServiceResult[List[ProjectTask]]:
        """
        List tasks for a project.
        
        Args:
            project_id: Project ID
            status: Optional status filter
            limit: Maximum number of tasks to return
            
        Returns:
            ServiceResult with list of ProjectTask models
        """
        self.request_context.require_authentication()
        
        try:
            # Build query model with project_id set, id empty for begins_with
            query_model = ProjectTask()
            query_model.project_id = project_id
            # Leave id empty for begins_with query
            
            key = query_model.get_key("primary").key(query_key=True, condition="begins_with")
            
            response = self.dynamodb.query(
                key=key,
                table_name=self.table_name,
                limit=limit,
                ascending=True,
            )
            
            items = response.get("Items", [])
            tasks = [ProjectTask().map(item) for item in items]
            
            # Filter by status if specified
            if status:
                tasks = [t for t in tasks if t.status == status]
            
            return ServiceResult.success_result(tasks)
            
        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="TaskService.list_tasks_for_project"
            )
    
    def list_tasks_for_assignee(
        self,
        assignee_user_id: Optional[str] = None,
        *,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> ServiceResult[List[ProjectTask]]:
        """
        List tasks assigned to a user.
        
        Args:
            assignee_user_id: User ID (defaults to current user)
            status: Optional status filter
            limit: Maximum number of tasks to return
            
        Returns:
            ServiceResult with list of ProjectTask models
        """
        self.request_context.require_authentication()
        tenant_id = self.request_context.target_tenant_id
        
        try:
            target_user_id = assignee_user_id or self.request_context.target_user_id
            
            # Build query model for GSI1
            query_model = ProjectTask()
            query_model.tenant_id = tenant_id
            query_model.assignee_user_id = target_user_id
            if status:
                query_model.status = status
            
            # Query using GSI1
            key = query_model.get_key("gsi1")
            response = self.dynamodb.query(
                table_name=self.table_name,
                key=key,
                index_name="gsi1",
                limit=limit,
            )
            
            items = response.get("Items", [])
            tasks = [ProjectTask().map(item) for item in items]
            
            # Filter by status if specified (in case GSI doesn't fully filter)
            if status:
                tasks = [t for t in tasks if t.status == status]
            
            return ServiceResult.success_result(tasks)
            
        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="TaskService.list_tasks_for_assignee"
            )
    
    def _update_task_keywords(self, task: ProjectTask):
        """Update keyword search index for a task."""
        try:
            searchable_text = task.get_searchable_text()
            self.keyword_service.refresh_from_text(
                resource_type="task",
                resource_id=task.task_id,
                text=searchable_text,
                user_id=task.owner_id,
            )
        except Exception:
            # Don't fail task operations if keyword update fails
            pass
