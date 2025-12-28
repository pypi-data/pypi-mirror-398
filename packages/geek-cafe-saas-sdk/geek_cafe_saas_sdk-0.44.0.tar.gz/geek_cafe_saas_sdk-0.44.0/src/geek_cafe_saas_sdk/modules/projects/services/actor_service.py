"""
ActorService for project actor management.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from typing import Dict, Any, Optional, List
from boto3_assist.dynamodb.dynamodb import DynamoDB
from geek_cafe_saas_sdk.core.services.database_service import DatabaseService
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.core.error_codes import ErrorCode
from geek_cafe_saas_sdk.modules.projects.models.project_actor import (
    ProjectActor,
    ActorStatus,
)
from geek_cafe_saas_sdk.modules.projects.models.project_activity import ActivityType, EntityType


class ActorService(DatabaseService[ProjectActor]):
    """
    Actor service for project actor management.
    
    Handles:
    - Adding/removing actors from projects
    - Role management
    - Listing actors by project or user
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
    
    def create(self, **kwargs) -> ServiceResult[ProjectActor]:
        """
        Add an actor to a project.
        
        Args:
            project_id: Project ID (required)
            user_id: User ID to add (required)
            role_code: Role code (required)
            display_name: Optional display name
            allocation_percent: Optional allocation percentage
            notes: Optional notes
            
        Returns:
            ServiceResult with ProjectActor model
        """
        return self.add_actor_to_project(**kwargs)
    
    def add_actor_to_project(
        self,
        project_id: str = None,
        user_id: str = None,
        role_code: str = None,
        *,
        display_name: Optional[str] = None,
        allocation_percent: Optional[int] = None,
        notes: Optional[str] = None,
        **kwargs,
    ) -> ServiceResult[ProjectActor]:
        """
        Add an actor to a project.
        
        Args:
            project_id: Project ID
            user_id: User ID to add
            role_code: Role code
            display_name: Optional display name
            allocation_percent: Optional allocation percentage
            notes: Optional notes
            
        Returns:
            ServiceResult with ProjectActor model
        """
        # Handle kwargs for create() compatibility
        project_id = project_id or kwargs.get("project_id")
        user_id = user_id or kwargs.get("user_id")
        role_code = role_code or kwargs.get("role_code")
        display_name = display_name or kwargs.get("display_name")
        allocation_percent = allocation_percent or kwargs.get("allocation_percent")
        notes = notes or kwargs.get("notes")
        
        self.request_context.require_authentication()
        tenant_id = self.request_context.target_tenant_id
        current_user_id = self.request_context.target_user_id
        
        try:
            if not project_id:
                return ServiceResult.error_result(
                    message="project_id is required",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            if not user_id:
                return ServiceResult.error_result(
                    message="user_id is required",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            if not role_code:
                return ServiceResult.error_result(
                    message="role_code is required",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            # Check for duplicate (same user with same role)
            existing = self._find_actor(project_id, user_id, role_code)
            if existing and existing.status == ActorStatus.ACTIVE:
                return ServiceResult.error_result(
                    message=f"User {user_id} already has role {role_code} on this project",
                    error_code=ErrorCode.VALIDATION_ERROR
                )
            
            # Create actor model
            actor = ProjectActor()
            actor.tenant_id = tenant_id
            actor.owner_id = current_user_id
            actor.user_id = user_id
            actor.project_id = project_id
            actor.role_code = role_code
            actor.status = ActorStatus.ACTIVE
            
            # Optional fields
            if display_name:
                actor.display_name = display_name
            if allocation_percent is not None:
                actor.allocation_percent = allocation_percent
            if notes:
                actor.notes = notes
            
            # Save
            actor.prep_for_save()
            save_result = self._save_model(actor)
            
            if not save_result.success:
                return save_result
            
            # Log activity
            self.activity_service.log_activity(
                project_id=project_id,
                activity_type=ActivityType.ACTOR_ADDED,
                summary=f"Actor {display_name or user_id} added with role {role_code}",
                entity_type=EntityType.ACTOR,
                entity_id=actor.actor_id,
                entity_name=display_name or user_id,
                details={"user_id": user_id, "role_code": role_code},
            )
            
            return save_result
            
        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="ActorService.add_actor_to_project"
            )
    
    def get_by_id(self, actor_id: str, **kwargs) -> ServiceResult[ProjectActor]:
        """
        Get actor by ID.
        
        Args:
            actor_id: Actor ID
            project_id: Project ID (required for adjacency pattern)
            
        Returns:
            ServiceResult with ProjectActor model
        """
        project_id = kwargs.get("project_id")
        if not project_id:
            return ServiceResult.error_result(
                message="project_id is required to get actor",
                error_code=ErrorCode.VALIDATION_ERROR
            )
        
        self.request_context.require_authentication()
        
        try:
            # Build query model for adjacency pattern
            query_model = ProjectActor()
            query_model.project_id = project_id
            query_model.id = actor_id
            
            key = query_model.get_key("primary")
            response = self.dynamodb.query(
                table_name=self.table_name,
                key=key,
                limit=1,
            )
            
            items = response.get("Items", [])
            if not items:
                return ServiceResult.error_result(
                    message=f"Actor not found: {actor_id}",
                    error_code=ErrorCode.NOT_FOUND
                )
            
            actor = ProjectActor().map(items[0])
            return ServiceResult.success_result(actor)
            
        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="ActorService.get_by_id"
            )
    
    def update(self, actor_id: str, **kwargs) -> ServiceResult[ProjectActor]:
        """
        Update an actor.
        
        Args:
            actor_id: Actor ID
            project_id: Project ID (required)
            updates: Dict of fields to update
            
        Returns:
            ServiceResult with updated ProjectActor model
        """
        return self.modify_actor_role(actor_id, **kwargs)
    
    def modify_actor_role(
        self,
        actor_id: str,
        project_id: str = None,
        updates: Dict[str, Any] = None,
        **kwargs,
    ) -> ServiceResult[ProjectActor]:
        """
        Modify an actor's role or other attributes.
        
        Args:
            actor_id: Actor ID
            project_id: Project ID
            updates: Dict of fields to update (role_code, display_name, allocation_percent, notes)
            
        Returns:
            ServiceResult with updated ProjectActor model
        """
        project_id = project_id or kwargs.get("project_id")
        updates = updates or kwargs.get("updates", {})
        
        if not project_id:
            return ServiceResult.error_result(
                message="project_id is required",
                error_code=ErrorCode.VALIDATION_ERROR
            )
        
        self.request_context.require_authentication()
        
        try:
            # Get existing actor
            get_result = self.get_by_id(actor_id, project_id=project_id)
            if not get_result.success:
                return get_result
            
            old_actor = get_result.data
            actor = ProjectActor().map(old_actor.to_dictionary())
            
            old_role = actor.role_code
            
            # Apply updates
            if "role_code" in updates:
                actor.role_code = updates["role_code"]
            if "display_name" in updates:
                actor.display_name = updates["display_name"]
            if "allocation_percent" in updates:
                actor.allocation_percent = updates["allocation_percent"]
            if "notes" in updates:
                actor.notes = updates["notes"]
            
            # Save with change tracking
            actor.prep_for_save()
            save_result = self._save_model(actor, old_model=old_actor)
            
            if not save_result.success:
                return save_result
            
            # Log activity if role changed
            if "role_code" in updates and updates["role_code"] != old_role:
                self.activity_service.log_activity(
                    project_id=project_id,
                    activity_type=ActivityType.ACTOR_ROLE_CHANGED,
                    summary=f"Actor {actor.display_name or actor.user_id} role changed from {old_role} to {actor.role_code}",
                    entity_type=EntityType.ACTOR,
                    entity_id=actor_id,
                    entity_name=actor.display_name or actor.user_id,
                    details={"old_role": old_role, "new_role": actor.role_code},
                )
            
            return save_result
            
        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="ActorService.modify_actor_role"
            )
    
    def delete(self, actor_id: str, **kwargs) -> ServiceResult[bool]:
        """
        Remove an actor from a project (soft delete).
        
        Args:
            actor_id: Actor ID
            project_id: Project ID (required)
            
        Returns:
            ServiceResult with success boolean
        """
        return self.remove_actor_from_project(actor_id, **kwargs)
    
    def remove_actor_from_project(
        self,
        actor_id: str,
        project_id: str = None,
        **kwargs,
    ) -> ServiceResult[bool]:
        """
        Remove an actor from a project (soft delete by setting status to removed).
        
        Args:
            actor_id: Actor ID
            project_id: Project ID
            
        Returns:
            ServiceResult with success boolean
        """
        project_id = project_id or kwargs.get("project_id")
        
        if not project_id:
            return ServiceResult.error_result(
                message="project_id is required",
                error_code=ErrorCode.VALIDATION_ERROR
            )
        
        self.request_context.require_authentication()
        
        try:
            # Get existing actor
            get_result = self.get_by_id(actor_id, project_id=project_id)
            if not get_result.success:
                return ServiceResult.error_result(
                    message=get_result.message,
                    error_code=get_result.error_code
                )
            
            old_actor = get_result.data
            actor = ProjectActor().map(old_actor.to_dictionary())
            actor.status = ActorStatus.REMOVED
            
            # Save
            actor.prep_for_save()
            save_result = self._save_model(actor, old_model=old_actor)
            
            if not save_result.success:
                return ServiceResult.error_result(
                    message=save_result.message,
                    error_code=save_result.error_code
                )
            
            # Log activity
            self.activity_service.log_activity(
                project_id=project_id,
                activity_type=ActivityType.ACTOR_REMOVED,
                summary=f"Actor {actor.display_name or actor.user_id} removed from project",
                entity_type=EntityType.ACTOR,
                entity_id=actor_id,
                entity_name=actor.display_name or actor.user_id,
                details={"user_id": actor.user_id, "role_code": actor.role_code},
            )
            
            return ServiceResult.success_result(True)
            
        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="ActorService.remove_actor_from_project"
            )
    
    def list_project_actors(
        self,
        project_id: str,
        *,
        include_removed: bool = False,
        limit: int = 50,
    ) -> ServiceResult[List[ProjectActor]]:
        """
        List actors for a project.
        
        Args:
            project_id: Project ID
            include_removed: Include removed actors
            limit: Maximum number of actors to return
            
        Returns:
            ServiceResult with list of ProjectActor models
        """
        self.request_context.require_authentication()
        
        try:
            # Build query model with project_id set, id empty for begins_with
            query_model = ProjectActor()
            query_model.project_id = project_id
            
            key = query_model.get_key("primary").key(query_key=True, condition="begins_with")
            
            response = self.dynamodb.query(
                key=key,
                table_name=self.table_name,
                limit=limit,
                ascending=True,
            )
            
            items = response.get("Items", [])
            actors = [ProjectActor().map(item) for item in items]
            
            # Filter out removed actors unless requested
            if not include_removed:
                actors = [a for a in actors if a.status != ActorStatus.REMOVED]
            
            return ServiceResult.success_result(actors)
            
        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="ActorService.list_project_actors"
            )
    
    def list_projects_for_actor(
        self,
        user_id: Optional[str] = None,
        *,
        limit: int = 50,
    ) -> ServiceResult[List[ProjectActor]]:
        """
        List projects where a user is an actor.
        
        Args:
            user_id: User ID (defaults to current user)
            limit: Maximum number of results
            
        Returns:
            ServiceResult with list of ProjectActor models
        """
        self.request_context.require_authentication()
        tenant_id = self.request_context.target_tenant_id
        
        try:
            target_user_id = user_id or self.request_context.target_user_id
            
            # Build query model for GSI1
            query_model = ProjectActor()
            query_model.tenant_id = tenant_id
            query_model.user_id = target_user_id
            
            # Query using GSI1
            key = query_model.get_key("gsi1")
            response = self.dynamodb.query(
                table_name=self.table_name,
                key=key,
                index_name="gsi1",
                limit=limit,
            )
            
            items = response.get("Items", [])
            actors = [ProjectActor().map(item) for item in items]
            
            # Filter out removed actors
            actors = [a for a in actors if a.status != ActorStatus.REMOVED]
            
            return ServiceResult.success_result(actors)
            
        except Exception as e:
            return ServiceResult.exception_result(
                exception=e,
                error_code=ErrorCode.INTERNAL_ERROR,
                context="ActorService.list_projects_for_actor"
            )
    
    def _find_actor(
        self,
        project_id: str,
        user_id: str,
        role_code: str,
    ) -> Optional[ProjectActor]:
        """
        Find an actor by project, user, and role.
        
        Returns None if not found.
        """
        try:
            result = self.list_project_actors(project_id, include_removed=True)
            if not result.success:
                return None
            
            for actor in result.data or []:
                if actor.user_id == user_id and actor.role_code == role_code:
                    return actor
            
            return None
        except Exception:
            return None
