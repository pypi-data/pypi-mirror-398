"""
MilestoneService for project milestone management.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from boto3_assist.dynamodb.dynamodb import DynamoDB
from geek_cafe_saas_sdk.core.services.database_service import DatabaseService
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.core.error_codes import ErrorCode
from geek_cafe_saas_sdk.modules.projects.models.project_milestone import (
    ProjectMilestone,
    MilestoneStatus,
)
from geek_cafe_saas_sdk.modules.projects.models.project_activity import ActivityType, EntityType


class MilestoneService(DatabaseService[ProjectMilestone]):
    """
    Milestone service for project milestone management.
    
    Handles:
    - Milestone CRUD operations
    - Milestone completion
    - Listing milestones by project
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
    
    def create(self, **kwargs) -> ServiceResult[ProjectMilestone]:
        """
        Create a new milestone.
        
        Args:
            project_id: Project ID (required)
            name: Milestone name (required)
            description: Milestone description
            due_date: Due date (ISO format)
            workflow_step_id: Linked workflow step ID
            owner_user_id: Responsible user ID
            
        Returns:
            ServiceResult with ProjectMilestone model
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
            
            # Create milestone model
            milestone = ProjectMilestone()
            milestone.tenant_id = tenant_id
            milestone.owner_id = user_id
            milestone.user_id = user_id
            milestone.project_id = project_id
            milestone.name = name.strip()
            milestone.status = MilestoneStatus.PLANNED
            
            # Optional fields
            if kwargs.get("description"):
                milestone.description = kwargs.get("description")
            if kwargs.get("due_date"):
                milestone.due_date = kwargs.get("due_date")
            if kwargs.get("workflow_step_id"):
                milestone.workflow_step_id = kwargs.get("workflow_step_id")
            if kwargs.get("owner_user_id"):
                milestone.owner_user_id = kwargs.get("owner_user_id")
            
            # Save
            milestone.prep_for_save()
            save_result = self._save_model(milestone)
            
            if not save_result.success:
                return save_result
            
            # Log activity
            self.activity_service.log_activity(
                project_id=project_id,
                activity_type=ActivityType.MILESTONE_CREATED,
                summary=f"Milestone '{name}' created",
                entity_type=EntityType.MILESTONE,
                entity_id=milestone.milestone_id,
                entity_name=name,
            )
            
            # Update keyword search
            self._update_milestone_keywords(milestone)
            
            return save_result
            
        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="MilestoneService.create"
            )
    
    def get_by_id(self, milestone_id: str, **kwargs) -> ServiceResult[ProjectMilestone]:
        """
        Get milestone by ID.
        
        Args:
            milestone_id: Milestone ID
            project_id: Project ID (required for adjacency pattern)
            
        Returns:
            ServiceResult with ProjectMilestone model
        """
        project_id = kwargs.get("project_id")
        if not project_id:
            return ServiceResult.error_result(
                message="project_id is required to get milestone",
                error_code=ErrorCode.VALIDATION_ERROR
            )
        
        self.request_context.require_authentication()
        
        try:
            # Build query model for adjacency pattern
            query_model = ProjectMilestone()
            query_model.project_id = project_id
            query_model.id = milestone_id
            
            key = query_model.get_key("primary")
            response = self.dynamodb.query(
                table_name=self.table_name,
                key=key,
                limit=1,
            )
            
            items = response.get("Items", [])
            if not items:
                return ServiceResult.error_result(
                    message=f"Milestone not found: {milestone_id}",
                    error_code=ErrorCode.NOT_FOUND
                )
            
            milestone = ProjectMilestone().map(items[0])
            return ServiceResult.success_result(milestone)
            
        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="MilestoneService.get_by_id"
            )
    
    def update(self, milestone_id: str, **kwargs) -> ServiceResult[ProjectMilestone]:
        """
        Update a milestone.
        
        Args:
            milestone_id: Milestone ID
            project_id: Project ID (required)
            updates: Dict of fields to update
            
        Returns:
            ServiceResult with updated ProjectMilestone model
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
            # Get existing milestone
            get_result = self.get_by_id(milestone_id, project_id=project_id)
            if not get_result.success:
                return get_result
            
            old_milestone = get_result.data
            milestone = ProjectMilestone().map(old_milestone.to_dictionary())
            
            # Apply updates
            if "name" in updates:
                milestone.name = updates["name"]
            if "description" in updates:
                milestone.description = updates["description"]
            if "due_date" in updates:
                milestone.due_date = updates["due_date"]
            if "workflow_step_id" in updates:
                milestone.workflow_step_id = updates["workflow_step_id"]
            if "owner_user_id" in updates:
                milestone.owner_user_id = updates["owner_user_id"]
            
            # Save with change tracking
            milestone.prep_for_save()
            save_result = self._save_model(milestone, old_model=old_milestone)
            
            if not save_result.success:
                return save_result
            
            # Log activity
            self.activity_service.log_activity(
                project_id=project_id,
                activity_type=ActivityType.MILESTONE_MODIFIED,
                summary=f"Milestone '{milestone.name}' updated",
                entity_type=EntityType.MILESTONE,
                entity_id=milestone_id,
                entity_name=milestone.name,
                details={"updated_fields": list(updates.keys())},
            )
            
            # Update keyword search
            self._update_milestone_keywords(milestone)
            
            return save_result
            
        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="MilestoneService.update"
            )
    
    def delete(self, milestone_id: str, **kwargs) -> ServiceResult[bool]:
        """
        Delete a milestone (soft delete by setting status to cancelled).
        
        Args:
            milestone_id: Milestone ID
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
        
        self.request_context.require_authentication()
        
        try:
            # Get existing milestone
            get_result = self.get_by_id(milestone_id, project_id=project_id)
            if not get_result.success:
                return ServiceResult.error_result(
                    message=get_result.message,
                    error_code=get_result.error_code
                )
            
            old_milestone = get_result.data
            milestone = ProjectMilestone().map(old_milestone.to_dictionary())
            milestone.status = MilestoneStatus.CANCELLED
            
            # Save
            milestone.prep_for_save()
            save_result = self._save_model(milestone, old_model=old_milestone)
            
            if not save_result.success:
                return ServiceResult.error_result(
                    message=save_result.message,
                    error_code=save_result.error_code
                )
            
            # Log activity
            self.activity_service.log_activity(
                project_id=project_id,
                activity_type=ActivityType.MILESTONE_CANCELLED,
                summary=f"Milestone '{milestone.name}' cancelled",
                entity_type=EntityType.MILESTONE,
                entity_id=milestone_id,
                entity_name=milestone.name,
            )
            
            # Clean up keywords
            self.keyword_service.delete_resource_keywords(
                resource_type="milestone",
                resource_id=milestone_id,
            )
            
            return ServiceResult.success_result(True)
            
        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="MilestoneService.delete"
            )
    
    def complete_milestone(
        self,
        milestone_id: str,
        project_id: str,
    ) -> ServiceResult[ProjectMilestone]:
        """
        Mark a milestone as completed.
        
        Args:
            milestone_id: Milestone ID
            project_id: Project ID
            
        Returns:
            ServiceResult with updated ProjectMilestone model
        """
        self.request_context.require_authentication()
        
        try:
            # Get existing milestone
            get_result = self.get_by_id(milestone_id, project_id=project_id)
            if not get_result.success:
                return get_result
            
            old_milestone = get_result.data
            
            if old_milestone.status == MilestoneStatus.COMPLETED:
                return ServiceResult.error_result(
                    message="Milestone is already completed",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            if old_milestone.status == MilestoneStatus.CANCELLED:
                return ServiceResult.error_result(
                    message="Cannot complete a cancelled milestone",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            # Create updated milestone
            milestone = ProjectMilestone().map(old_milestone.to_dictionary())
            milestone.status = MilestoneStatus.COMPLETED
            milestone.completed_date = datetime.now(timezone.utc).date().isoformat()
            
            # Save
            milestone.prep_for_save()
            save_result = self._save_model(milestone, old_model=old_milestone)
            
            if not save_result.success:
                return save_result
            
            # Log activity
            self.activity_service.log_activity(
                project_id=project_id,
                activity_type=ActivityType.MILESTONE_COMPLETED,
                summary=f"Milestone '{milestone.name}' completed",
                entity_type=EntityType.MILESTONE,
                entity_id=milestone_id,
                entity_name=milestone.name,
            )
            
            return save_result
            
        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="MilestoneService.complete_milestone"
            )
    
    def list_milestones(
        self,
        project_id: str,
        *,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> ServiceResult[List[ProjectMilestone]]:
        """
        List milestones for a project.
        
        Args:
            project_id: Project ID
            status: Optional status filter
            limit: Maximum number of milestones to return
            
        Returns:
            ServiceResult with list of ProjectMilestone models
        """
        self.request_context.require_authentication()
        
        try:
            # Build query model with project_id set, id empty for begins_with
            query_model = ProjectMilestone()
            query_model.project_id = project_id
            
            key = query_model.get_key("primary").key(query_key=True, condition="begins_with")
            
            response = self.dynamodb.query(
                key=key,
                table_name=self.table_name,
                limit=limit,
                ascending=True,
            )
            
            items = response.get("Items", [])
            milestones = [ProjectMilestone().map(item) for item in items]
            
            # Filter by status if specified
            if status:
                milestones = [m for m in milestones if m.status == status]
            
            return ServiceResult.success_result(milestones)
            
        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="MilestoneService.list_milestones"
            )
    
    def _update_milestone_keywords(self, milestone: ProjectMilestone):
        """Update keyword search index for a milestone."""
        try:
            searchable_text = milestone.get_searchable_text()
            self.keyword_service.refresh_from_text(
                resource_type="milestone",
                resource_id=milestone.milestone_id,
                text=searchable_text,
                user_id=milestone.owner_id,
            )
        except Exception:
            # Don't fail milestone operations if keyword update fails
            pass
