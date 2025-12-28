"""
ProjectActivity model for project activity log.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from typing import Dict, Any, Optional
from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey
from geek_cafe_saas_sdk.core.models.base_tenant_user_model import BaseTenantUserModel


class ActivityType:
    """Activity type constants."""
    # Project activities
    PROJECT_CREATED = "PROJECT_CREATED"
    PROJECT_MODIFIED = "PROJECT_MODIFIED"
    PROJECT_STATUS_CHANGED = "PROJECT_STATUS_CHANGED"
    PROJECT_ARCHIVED = "PROJECT_ARCHIVED"
    
    # Actor activities
    ACTOR_ADDED = "ACTOR_ADDED"
    ACTOR_REMOVED = "ACTOR_REMOVED"
    ACTOR_ROLE_CHANGED = "ACTOR_ROLE_CHANGED"
    
    # Workflow activities
    WORKFLOW_CREATED = "WORKFLOW_CREATED"
    WORKFLOW_STEP_ADDED = "WORKFLOW_STEP_ADDED"
    WORKFLOW_STEP_MODIFIED = "WORKFLOW_STEP_MODIFIED"
    WORKFLOW_STEP_STARTED = "WORKFLOW_STEP_STARTED"
    WORKFLOW_STEP_COMPLETED = "WORKFLOW_STEP_COMPLETED"
    WORKFLOW_STEP_SKIPPED = "WORKFLOW_STEP_SKIPPED"
    
    # Milestone activities
    MILESTONE_CREATED = "MILESTONE_CREATED"
    MILESTONE_MODIFIED = "MILESTONE_MODIFIED"
    MILESTONE_COMPLETED = "MILESTONE_COMPLETED"
    MILESTONE_CANCELLED = "MILESTONE_CANCELLED"
    
    # Task activities
    TASK_CREATED = "TASK_CREATED"
    TASK_MODIFIED = "TASK_MODIFIED"
    TASK_STATUS_CHANGED = "TASK_STATUS_CHANGED"
    TASK_ASSIGNED = "TASK_ASSIGNED"
    TASK_UNASSIGNED = "TASK_UNASSIGNED"
    TASK_COMPLETED = "TASK_COMPLETED"
    
    # Comment activities (future)
    COMMENT_ADDED = "COMMENT_ADDED"


class EntityType:
    """Entity type constants for activity context."""
    PROJECT = "project"
    ACTOR = "actor"
    WORKFLOW = "workflow"
    WORKFLOW_STEP = "workflow_step"
    MILESTONE = "milestone"
    TASK = "task"
    COMMENT = "comment"


class ProjectActivity(BaseTenantUserModel):
    """
    ProjectActivity model for append-only activity log.
    
    Records all significant events in a project's lifecycle.
    Never updated, only appended.
    
    Access Patterns (DynamoDB Keys):
    - pk: project#{project_id}
    - sk: activity#{timestamp}#{activity_id}
    """

    def __init__(self):
        super().__init__()
        
        # Identity
        self._activity_id: str | None = None
        self._project_id: str | None = None
        
        # Activity Information
        self._activity_type: str | None = None
        self._summary: str | None = None  # Human-readable summary
        self._details: Dict[str, Any] = {}  # Additional context
        
        # Actor (who performed the action)
        self._actor_user_id: str | None = None
        self._actor_display_name: str | None = None
        
        # Entity context (what was affected)
        self._entity_type: str | None = None
        self._entity_id: str | None = None
        self._entity_name: str | None = None
        
        # Model metadata
        self.model_name = "project_activity"
        self.model_name_plural = "project_activities"
        
        # CRITICAL: Call _setup_indexes() as LAST line in __init__
        self._setup_indexes()
    
    def _setup_indexes(self):
        """Setup DynamoDB indexes for activity queries."""
        
        # Primary index: Activity within project (adjacency pattern)
        # Sort key includes timestamp for chronological ordering
        primary = DynamoDBIndex()
        primary.name = "primary"
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(("project", self.project_id))
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: self._build_activity_sk()
        self.indexes.add_primary(primary)
    
    # Properties - Identity
    @property
    def activity_id(self) -> str | None:
        """Unique activity ID."""
        return self._activity_id or self.id
    
    @activity_id.setter
    def activity_id(self, value: str | None):
        self._activity_id = value
        if value:
            self.id = value
    
    @property
    def project_id(self) -> str | None:
        """Project ID this activity belongs to."""
        return self._project_id
    
    @project_id.setter
    def project_id(self, value: str | None):
        self._project_id = value
    
    # Properties - Activity Information
    @property
    def activity_type(self) -> str | None:
        """Type of activity."""
        return self._activity_type
    
    @activity_type.setter
    def activity_type(self, value: str | None):
        self._activity_type = value
    
    @property
    def summary(self) -> str | None:
        """Human-readable summary."""
        return self._summary
    
    @summary.setter
    def summary(self, value: str | None):
        self._summary = value
    
    @property
    def details(self) -> Dict[str, Any]:
        """Additional context details."""
        return self._details
    
    @details.setter
    def details(self, value: Dict[str, Any]):
        self._details = value if value else {}
    
    # Properties - Actor
    @property
    def actor_user_id(self) -> str | None:
        """User ID of who performed the action."""
        return self._actor_user_id
    
    @actor_user_id.setter
    def actor_user_id(self, value: str | None):
        self._actor_user_id = value
    
    @property
    def actor_display_name(self) -> str | None:
        """Display name of who performed the action."""
        return self._actor_display_name
    
    @actor_display_name.setter
    def actor_display_name(self, value: str | None):
        self._actor_display_name = value
    
    # Properties - Entity Context
    @property
    def entity_type(self) -> str | None:
        """Type of entity affected."""
        return self._entity_type
    
    @entity_type.setter
    def entity_type(self, value: str | None):
        self._entity_type = value
    
    @property
    def entity_id(self) -> str | None:
        """ID of entity affected."""
        return self._entity_id
    
    @entity_id.setter
    def entity_id(self, value: str | None):
        self._entity_id = value
    
    @property
    def entity_name(self) -> str | None:
        """Name of entity affected."""
        return self._entity_name
    
    @entity_name.setter
    def entity_name(self, value: str | None):
        self._entity_name = value
    
    # Helper Methods
    def set_entity(self, entity_type: str, entity_id: str, entity_name: str | None = None):
        """Set entity context."""
        self._entity_type = entity_type
        self._entity_id = entity_id
        self._entity_name = entity_name
    
    def add_detail(self, key: str, value: Any):
        """Add a detail to the activity."""
        self._details[key] = value
    
    def get_detail(self, key: str, default: Any = None) -> Any:
        """Get a detail from the activity."""
        return self._details.get(key, default)
    
    def _query_index_timestamp(self) -> str:
        """Get timestamp for query index. Returns empty string if not set for begins_with queries."""
        if not self.created_utc_ts:
            return ""
        return str(self.created_utc_ts)
    
    def _build_activity_sk(self) -> str:
        """Build the sort key for activity records.
        
        For saves: activity#<timestamp>#id#<activity_id>
        For queries (begins_with): activity#
        """
        # If no timestamp or id, return just the prefix for begins_with queries
        if not self.created_utc_ts and not self.id:
            return "activity#"
        
        # Build full SK for saves
        return DynamoDBKey.build_key(
            ("activity", self.created_utc_ts or 0),
            ("id", self.id or ""),
        )
