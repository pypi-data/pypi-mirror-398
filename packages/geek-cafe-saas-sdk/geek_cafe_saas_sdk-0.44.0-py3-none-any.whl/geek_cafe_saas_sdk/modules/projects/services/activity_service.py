"""
ActivityService for project activity logging.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from typing import Dict, Any, Optional, List
from boto3_assist.dynamodb.dynamodb import DynamoDB
from geek_cafe_saas_sdk.core.services.database_service import DatabaseService
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.core.error_codes import ErrorCode
from geek_cafe_saas_sdk.modules.projects.models.project_activity import (
    ProjectActivity,
    ActivityType,
    EntityType,
)


class ActivityService(DatabaseService[ProjectActivity]):
    """
    Activity service for project activity logging.
    
    Handles:
    - Logging project activities (append-only)
    - Retrieving activity streams
    - Filtering activities by entity
    """
    
    def create(self, **kwargs) -> ServiceResult[ProjectActivity]:
        """
        Log a new activity.
        
        Args:
            project_id: Project ID
            activity_type: Type of activity
            summary: Human-readable summary
            entity_type: Optional entity type
            entity_id: Optional entity ID
            entity_name: Optional entity name
            details: Optional additional details
            
        Returns:
            ServiceResult with ProjectActivity model
        """
        self.request_context.require_authentication()
        tenant_id = self.request_context.target_tenant_id
        user_id = self.request_context.target_user_id
        
        try:
            project_id = kwargs.get("project_id")
            activity_type = kwargs.get("activity_type")
            summary = kwargs.get("summary")
            
            if not project_id:
                return ServiceResult.error_result(
                    message="project_id is required",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            if not activity_type:
                return ServiceResult.error_result(
                    message="activity_type is required",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            # Create activity model
            activity = ProjectActivity()
            activity.tenant_id = tenant_id
            activity.owner_id = user_id
            activity.user_id = user_id
            activity.project_id = project_id
            activity.activity_type = activity_type
            activity.summary = summary or f"{activity_type} activity"
            activity.actor_user_id = user_id
            
            # Optional fields
            if kwargs.get("entity_type"):
                activity.entity_type = kwargs.get("entity_type")
            if kwargs.get("entity_id"):
                activity.entity_id = kwargs.get("entity_id")
            if kwargs.get("entity_name"):
                activity.entity_name = kwargs.get("entity_name")
            if kwargs.get("details"):
                activity.details = kwargs.get("details")
            if kwargs.get("actor_display_name"):
                activity.actor_display_name = kwargs.get("actor_display_name")
            
            # Save
            activity.prep_for_save()
            return self._save_model(activity)
            
        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="ActivityService.create"
            )
    
    def log_activity(
        self,
        project_id: str,
        activity_type: str,
        summary: str,
        *,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        entity_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> ServiceResult[ProjectActivity]:
        """
        Convenience method to log an activity.
        
        Args:
            project_id: Project ID
            activity_type: Type of activity (from ActivityType)
            summary: Human-readable summary
            entity_type: Optional entity type (from EntityType)
            entity_id: Optional entity ID
            entity_name: Optional entity name
            details: Optional additional context
            
        Returns:
            ServiceResult with ProjectActivity model
        """
        return self.create(
            project_id=project_id,
            activity_type=activity_type,
            summary=summary,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=entity_name,
            details=details,
        )
    
    def get_by_id(self, activity_id: str, **kwargs) -> ServiceResult[ProjectActivity]:
        """
        Get activity by ID.
        
        Note: Activities are typically queried by project, not by ID.
        This method requires project_id in kwargs.
        """
        project_id = kwargs.get("project_id")
        if not project_id:
            return ServiceResult.error_result(
                message="project_id is required to get activity",
                error_code=ErrorCode.VALIDATION_ERROR
            )
        
        return self._get_model_by_id(activity_id, ProjectActivity)
    
    def update(self, activity_id: str, **kwargs) -> ServiceResult[ProjectActivity]:
        """
        Activities are immutable - updates not supported.
        """
        return ServiceResult.error_result(
            message="Activities are immutable and cannot be updated",
            error_code=ErrorCode.VALIDATION_ERROR
        )
    
    def delete(self, activity_id: str, **kwargs) -> ServiceResult[bool]:
        """
        Activities are immutable - deletes not supported.
        """
        return ServiceResult.error_result(
            message="Activities are immutable and cannot be deleted",
            error_code=ErrorCode.VALIDATION_ERROR
        )
    
    def get_project_activity_stream(
        self,
        project_id: str,
        *,
        limit: int = 50,
        ascending: bool = False,
    ) -> ServiceResult[List[ProjectActivity]]:
        """
        Get activity stream for a project.
        
        Args:
            project_id: Project ID
            limit: Maximum number of activities to return
            ascending: If True, oldest first; if False, newest first
            
        Returns:
            ServiceResult with list of ProjectActivity models
        """
        self.request_context.require_authentication()
        
        try:
            # Build query model with project_id set, SK components empty for begins_with
            query_model = ProjectActivity()
            query_model.project_id = project_id
            # Leave created_utc_ts and id empty for begins_with query
            
            key = query_model.get_key("primary").key(query_key=True, condition="begins_with")
            
            response = self.dynamodb.query(
                key=key,
                table_name=self.table_name,
                limit=limit,
                ascending=ascending,
            )
            
            items = response.get("Items", [])
            activities = [ProjectActivity().map(item) for item in items]
            
            return ServiceResult.success_result(activities)
            
        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="ActivityService.get_project_activity_stream"
            )
    
    def filter_activity_by_entity(
        self,
        project_id: str,
        entity_type: str,
        entity_id: Optional[str] = None,
        *,
        limit: int = 50,
    ) -> ServiceResult[List[ProjectActivity]]:
        """
        Filter activities by entity type and optionally entity ID.
        
        Args:
            project_id: Project ID
            entity_type: Entity type to filter by
            entity_id: Optional entity ID to filter by
            limit: Maximum number of activities to return
            
        Returns:
            ServiceResult with filtered list of ProjectActivity models
        """
        # Get all activities and filter in memory
        # (For MVP, this is acceptable; could add GSI for entity filtering later)
        result = self.get_project_activity_stream(project_id, limit=limit * 2)
        
        if not result.success:
            return result
        
        filtered = []
        for activity in result.data or []:
            if activity.entity_type == entity_type:
                if entity_id is None or activity.entity_id == entity_id:
                    filtered.append(activity)
                    if len(filtered) >= limit:
                        break
        
        return ServiceResult.success_result(filtered)
