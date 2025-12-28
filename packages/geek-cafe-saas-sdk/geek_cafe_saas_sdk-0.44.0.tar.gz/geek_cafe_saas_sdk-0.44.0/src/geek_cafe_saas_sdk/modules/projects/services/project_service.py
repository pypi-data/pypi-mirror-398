"""
ProjectService for project management.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from boto3_assist.dynamodb.dynamodb import DynamoDB
from boto3_assist.dynamodb.dynamodb_index import DynamoDBKey
from geek_cafe_saas_sdk.core.services.database_service import DatabaseService
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.core.error_codes import ErrorCode
from geek_cafe_saas_sdk.modules.projects.models.project import (
    Project,
    ProjectStatus,
    ProjectPriority,
    ProjectType,
)
from geek_cafe_saas_sdk.modules.projects.models.project_activity import ActivityType, EntityType


class ProjectService(DatabaseService[Project]):
    """
    Project service for project management.
    
    Handles:
    - Project lifecycle management
    - Project listing
    - Coordinating with sub-services
    - Keyword search integration
    
    Sub-services are lazy-loaded for efficiency.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Lazy-loaded sub-services
        self._actor_service = None
        self._workflow_service = None
        self._milestone_service = None
        self._task_service = None
        self._activity_service = None
        self._keyword_service = None
    
    # ========================================
    # Lazy-loaded Sub-services
    # ========================================
    
    @property
    def actor_service(self):
        """Lazy-load actor service."""
        if self._actor_service is None:
            from geek_cafe_saas_sdk.modules.projects.services.actor_service import ActorService
            self._actor_service = ActorService(
                dynamodb=self.dynamodb,
                table_name=self.table_name,
                request_context=self.request_context,
            )
        return self._actor_service
    
    @property
    def workflow_service(self):
        """Lazy-load workflow service."""
        if self._workflow_service is None:
            from geek_cafe_saas_sdk.modules.projects.services.workflow_service import WorkflowService
            self._workflow_service = WorkflowService(
                dynamodb=self.dynamodb,
                table_name=self.table_name,
                request_context=self.request_context,
            )
        return self._workflow_service
    
    @property
    def milestone_service(self):
        """Lazy-load milestone service."""
        if self._milestone_service is None:
            from geek_cafe_saas_sdk.modules.projects.services.milestone_service import MilestoneService
            self._milestone_service = MilestoneService(
                dynamodb=self.dynamodb,
                table_name=self.table_name,
                request_context=self.request_context,
            )
        return self._milestone_service
    
    @property
    def task_service(self):
        """Lazy-load task service."""
        if self._task_service is None:
            from geek_cafe_saas_sdk.modules.projects.services.task_service import TaskService
            self._task_service = TaskService(
                dynamodb=self.dynamodb,
                table_name=self.table_name,
                request_context=self.request_context,
            )
        return self._task_service
    
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
    
    # ========================================
    # Project CRUD Operations
    # ========================================
    
    def create(self, **kwargs) -> ServiceResult[Project]:
        """
        Create a new project.
        
        Args:
            name: Project name (required)
            description: Project description
            project_type: Project type (default: generic)
            priority: Project priority (default: normal)
            start_date: Start date (ISO format)
            target_end_date: Target end date (ISO format)
            tags: List of tags
            category: Project category
            domain: Project domain
            
        Returns:
            ServiceResult with Project model
        """
        self.request_context.require_authentication()
        tenant_id = self.request_context.target_tenant_id
        user_id = self.request_context.target_user_id
        
        try:
            name = kwargs.get("name")
            
            if not name or not name.strip():
                return ServiceResult.error_result(
                    message="name is required",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            # Create project model
            project = Project()
            project.tenant_id = tenant_id
            project.owner_id = user_id
            project.user_id = user_id
            project.name = name.strip()
            project.status = ProjectStatus.DRAFT
            
            # Optional fields
            if kwargs.get("description"):
                project.description = kwargs.get("description")
            if kwargs.get("project_type"):
                project.project_type = kwargs.get("project_type")
            if kwargs.get("priority"):
                project.priority = kwargs.get("priority")
            if kwargs.get("start_date"):
                project.start_date = kwargs.get("start_date")
            if kwargs.get("target_end_date"):
                project.target_end_date = kwargs.get("target_end_date")
            if kwargs.get("tags"):
                project.tags = kwargs.get("tags")
            if kwargs.get("category"):
                project.category = kwargs.get("category")
            if kwargs.get("domain"):
                project.domain = kwargs.get("domain")
            
            # Save
            project.prep_for_save()
            save_result = self._save_model(project)
            
            if not save_result.success:
                return save_result
            
            # Log activity
            self.activity_service.log_activity(
                project_id=project.project_id,
                activity_type=ActivityType.PROJECT_CREATED,
                summary=f"Project '{name}' created",
                entity_type=EntityType.PROJECT,
                entity_id=project.project_id,
                entity_name=name,
            )
            
            # Update keyword search
            self._update_project_keywords(project)
            
            return save_result
            
        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="ProjectService.create"
            )
    
    def get_by_id(self, project_id: str, **kwargs) -> ServiceResult[Project]:
        """
        Get project by ID.
        
        Args:
            project_id: Project ID
            
        Returns:
            ServiceResult with Project model
        """
        self.request_context.require_authentication()
        
        try:
            # Build query model
            query_model = Project()
            query_model.id = project_id
            
            key = query_model.get_key("primary")
            response = self.dynamodb.query(
                table_name=self.table_name,
                key=key,
                limit=1,
            )
            
            items = response.get("Items", [])
            if not items:
                return ServiceResult.error_result(
                    message=f"Project not found: {project_id}",
                    error_code=ErrorCode.NOT_FOUND
                )
            
            project = Project().map(items[0])
            
            # Check tenant access
            if project.tenant_id != self.request_context.target_tenant_id:
                return ServiceResult.error_result(
                    message="Access denied",
                    error_code=ErrorCode.ACCESS_DENIED
                )
            
            return ServiceResult.success_result(project)
            
        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="ProjectService.get_by_id"
            )
    
    def update(self, project_id: str, **kwargs) -> ServiceResult[Project]:
        """
        Update a project.
        
        Args:
            project_id: Project ID
            updates: Dict of fields to update
            
        Returns:
            ServiceResult with updated Project model
        """
        updates = kwargs.get("updates", {})
        
        self.request_context.require_authentication()
        
        try:
            # Get existing project
            get_result = self.get_by_id(project_id)
            if not get_result.success:
                return get_result
            
            old_project = get_result.data
            
            # Check if project is editable
            if not old_project.is_editable():
                return ServiceResult.error_result(
                    message="Cannot modify a completed or archived project",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            project = Project().map(old_project.to_dictionary())
            
            # Apply updates
            if "name" in updates:
                project.name = updates["name"]
            if "description" in updates:
                project.description = updates["description"]
            if "project_type" in updates:
                project.project_type = updates["project_type"]
            if "priority" in updates:
                project.priority = updates["priority"]
            if "start_date" in updates:
                project.start_date = updates["start_date"]
            if "target_end_date" in updates:
                project.target_end_date = updates["target_end_date"]
            if "tags" in updates:
                project.tags = updates["tags"]
            if "category" in updates:
                project.category = updates["category"]
            if "domain" in updates:
                project.domain = updates["domain"]
            
            # Save with change tracking
            project.prep_for_save()
            save_result = self._save_model(project, old_model=old_project)
            
            if not save_result.success:
                return save_result
            
            # Log activity
            self.activity_service.log_activity(
                project_id=project_id,
                activity_type=ActivityType.PROJECT_MODIFIED,
                summary=f"Project '{project.name}' updated",
                entity_type=EntityType.PROJECT,
                entity_id=project_id,
                entity_name=project.name,
                details={"updated_fields": list(updates.keys())},
            )
            
            # Update keyword search
            self._update_project_keywords(project)
            
            return save_result
            
        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="ProjectService.update"
            )
    
    def delete(self, project_id: str, **kwargs) -> ServiceResult[bool]:
        """
        Delete a project (archive it).
        
        Args:
            project_id: Project ID
            
        Returns:
            ServiceResult with success boolean
        """
        result = self.archive_project(project_id)
        if result.success:
            return ServiceResult.success_result(True)
        return ServiceResult.error_result(
            message=result.message,
            error_code=result.error_code
        )
    
    # ========================================
    # Project Status Operations
    # ========================================
    
    def change_project_status(
        self,
        project_id: str,
        new_status: str,
    ) -> ServiceResult[Project]:
        """
        Change project status with validation.
        
        Args:
            project_id: Project ID
            new_status: New status
            
        Returns:
            ServiceResult with updated Project model
        """
        self.request_context.require_authentication()
        
        try:
            if new_status not in ProjectStatus.ALL:
                return ServiceResult.error_result(
                    message=f"Invalid status: {new_status}",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            # Get existing project
            get_result = self.get_by_id(project_id)
            if not get_result.success:
                return get_result
            
            old_project = get_result.data
            old_status = old_project.status
            
            # Validate transition
            if not old_project.can_transition_to(new_status):
                return ServiceResult.error_result(
                    message=f"Cannot transition from {old_status} to {new_status}",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            # Create updated project
            project = Project().map(old_project.to_dictionary())
            project.status = new_status
            
            # Set actual end date if completing
            if new_status == ProjectStatus.COMPLETED:
                project.actual_end_date = datetime.now(timezone.utc).date().isoformat()
            
            # Save
            project.prep_for_save()
            save_result = self._save_model(project, old_model=old_project)
            
            if not save_result.success:
                return save_result
            
            # Log activity
            self.activity_service.log_activity(
                project_id=project_id,
                activity_type=ActivityType.PROJECT_STATUS_CHANGED,
                summary=f"Project '{project.name}' status changed from {old_status} to {new_status}",
                entity_type=EntityType.PROJECT,
                entity_id=project_id,
                entity_name=project.name,
                details={"old_status": old_status, "new_status": new_status},
            )
            
            return save_result
            
        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="ProjectService.change_project_status"
            )
    
    def archive_project(self, project_id: str) -> ServiceResult[Project]:
        """
        Archive a project.
        
        Args:
            project_id: Project ID
            
        Returns:
            ServiceResult with archived Project model
        """
        result = self.change_project_status(project_id, ProjectStatus.ARCHIVED)
        
        if result.success:
            # Log specific archive activity
            self.activity_service.log_activity(
                project_id=project_id,
                activity_type=ActivityType.PROJECT_ARCHIVED,
                summary=f"Project '{result.data.name}' archived",
                entity_type=EntityType.PROJECT,
                entity_id=project_id,
                entity_name=result.data.name,
            )
            
            # Clean up keywords
            self.keyword_service.delete_resource_keywords(
                resource_type="project",
                resource_id=project_id,
            )
        
        return result
    
    # ========================================
    # Project Listing Operations
    # ========================================
    
    def list_projects_for_tenant(
        self,
        *,
        status: Optional[str] = None,
        limit: int = 50,
        ascending: bool = False,
    ) -> ServiceResult[List[Project]]:
        """
        List projects for the current tenant.
        
        Args:
            status: Optional status filter
            limit: Maximum number of projects to return
            ascending: Sort order (False = newest first)
            
        Returns:
            ServiceResult with list of Project models
        """
        self.request_context.require_authentication()
        tenant_id = self.request_context.target_tenant_id
        
        try:
            # Build query model for GSI1 with begins_with
            query_model = Project()
            query_model.tenant_id = tenant_id
            query_model.status = status
            
            key = query_model.get_key("gsi1").key(query_key=True, condition="begins_with")
            
            response = self.dynamodb.query(
                key=key,
                table_name=self.table_name,
                index_name="gsi1",
                limit=limit,
                ascending=ascending,
            )
            
            items = response.get("Items", [])
            projects = [Project().map(item) for item in items]
            
            # Filter by status if specified
            if status:
                projects = [p for p in projects if p.status == status]
            
            return ServiceResult.success_result(projects)
            
        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="ProjectService.list_projects_for_tenant"
            )
    
    # ========================================
    # Project Details Operations
    # ========================================
    
    def get_project_with_details(
        self,
        project_id: str,
    ) -> ServiceResult[Dict[str, Any]]:
        """
        Get project with all related data.
        
        Args:
            project_id: Project ID
            
        Returns:
            ServiceResult with dict containing project and related data
        """
        self.request_context.require_authentication()
        
        try:
            # Get project
            project_result = self.get_by_id(project_id)
            if not project_result.success:
                return ServiceResult.error_result(
                    message=project_result.message,
                    error_code=project_result.error_code
                )
            
            project = project_result.data
            
            # Get related data
            actors_result = self.actor_service.list_project_actors(project_id)
            workflows_result = self.workflow_service.list_workflows(project_id)
            milestones_result = self.milestone_service.list_milestones(project_id)
            tasks_result = self.task_service.list_tasks_for_project(project_id)
            activities_result = self.activity_service.get_project_activity_stream(
                project_id, limit=20
            )
            
            return ServiceResult.success_result({
                "project": project,
                "actors": actors_result.data if actors_result.success else [],
                "workflows": workflows_result.data if workflows_result.success else [],
                "milestones": milestones_result.data if milestones_result.success else [],
                "tasks": tasks_result.data if tasks_result.success else [],
                "recent_activities": activities_result.data if activities_result.success else [],
            })
            
        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="ProjectService.get_project_with_details"
            )
    
    # ========================================
    # Search Operations
    # ========================================
    
    def search_projects(
        self,
        keyword: str,
        *,
        limit: int = 50,
    ) -> ServiceResult[List[Project]]:
        """
        Search projects by keyword.
        
        Args:
            keyword: Search keyword
            limit: Maximum number of results
            
        Returns:
            ServiceResult with list of Project models
        """
        self.request_context.require_authentication()
        
        try:
            # Search using keyword service
            search_result = self.keyword_service.search(
                keyword,
                resource_type="project",
                limit=limit,
            )
            
            if not search_result.success:
                return ServiceResult.error_result(
                    message=search_result.message,
                    error_code=search_result.error_code
                )
            
            # Get project IDs from search results
            project_ids = [entry.resource_id for entry in search_result.data or []]
            
            # Fetch projects
            projects = []
            for project_id in project_ids:
                result = self.get_by_id(project_id)
                if result.success:
                    projects.append(result.data)
            
            return ServiceResult.success_result(projects)
            
        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="ProjectService.search_projects"
            )
    
    # ========================================
    # Helper Methods
    # ========================================
    
    def _update_project_keywords(self, project: Project):
        """Update keyword search index for a project."""
        try:
            searchable_text = project.get_searchable_text()
            self.keyword_service.refresh_from_text(
                resource_type="project",
                resource_id=project.project_id,
                text=searchable_text,
                user_id=project.owner_id,
            )
        except Exception:
            # Don't fail project operations if keyword update fails
            pass
    
    # ========================================
    # Counter Update Methods (called by sub-services)
    # ========================================
    
    def increment_actor_count(self, project_id: str) -> ServiceResult[Project]:
        """Increment project actor count."""
        return self._update_counter(project_id, "actor_count", 1)
    
    def decrement_actor_count(self, project_id: str) -> ServiceResult[Project]:
        """Decrement project actor count."""
        return self._update_counter(project_id, "actor_count", -1)
    
    def increment_task_count(self, project_id: str) -> ServiceResult[Project]:
        """Increment project task count."""
        return self._update_counter(project_id, "task_count", 1)
    
    def decrement_task_count(self, project_id: str) -> ServiceResult[Project]:
        """Decrement project task count."""
        return self._update_counter(project_id, "task_count", -1)
    
    def increment_completed_task_count(self, project_id: str) -> ServiceResult[Project]:
        """Increment project completed task count."""
        return self._update_counter(project_id, "completed_task_count", 1)
    
    def decrement_completed_task_count(self, project_id: str) -> ServiceResult[Project]:
        """Decrement project completed task count."""
        return self._update_counter(project_id, "completed_task_count", -1)
    
    def increment_milestone_count(self, project_id: str) -> ServiceResult[Project]:
        """Increment project milestone count."""
        return self._update_counter(project_id, "milestone_count", 1)
    
    def decrement_milestone_count(self, project_id: str) -> ServiceResult[Project]:
        """Decrement project milestone count."""
        return self._update_counter(project_id, "milestone_count", -1)
    
    def increment_completed_milestone_count(self, project_id: str) -> ServiceResult[Project]:
        """Increment project completed milestone count."""
        return self._update_counter(project_id, "completed_milestone_count", 1)
    
    def decrement_completed_milestone_count(self, project_id: str) -> ServiceResult[Project]:
        """Decrement project completed milestone count."""
        return self._update_counter(project_id, "completed_milestone_count", -1)
    
    def _update_counter(
        self,
        project_id: str,
        counter_name: str,
        delta: int,
    ) -> ServiceResult[Project]:
        """Update a project counter."""
        try:
            get_result = self.get_by_id(project_id)
            if not get_result.success:
                return get_result
            
            project = get_result.data
            current_value = getattr(project, counter_name, 0)
            new_value = max(0, current_value + delta)
            setattr(project, counter_name, new_value)
            
            project.prep_for_save()
            return self._save_model(project)
            
        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context=f"ProjectService._update_counter({counter_name})"
            )
