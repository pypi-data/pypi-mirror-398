"""
ProjectMilestone model for project milestones.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from typing import Optional
from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey
from geek_cafe_saas_sdk.core.models.base_tenant_user_model import BaseTenantUserModel


class MilestoneStatus:
    """Milestone status constants."""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    
    ALL = [PLANNED, IN_PROGRESS, COMPLETED, CANCELLED]


class ProjectMilestone(BaseTenantUserModel):
    """
    ProjectMilestone model for project milestones.
    
    Represents a major delivery point or business milestone.
    
    Access Patterns (DynamoDB Keys):
    - pk: project#{project_id}
    - sk: milestone#{milestone_id}
    """

    def __init__(self):
        super().__init__()
        
        # Identity
        self._milestone_id: str | None = None
        self._project_id: str | None = None
        
        # Milestone Information
        self._name: str | None = None
        self._description: str | None = None
        
        # Status
        self._status: str = MilestoneStatus.PLANNED
        
        # Dates
        self._due_date: str | None = None  # ISO date string
        self._completed_date: str | None = None  # ISO date string
        
        # Optional links
        self._workflow_step_id: str | None = None  # Link to workflow step
        self._owner_user_id: str | None = None  # Responsible person
        
        # Model metadata
        self.model_name = "project_milestone"
        self.model_name_plural = "project_milestones"
        
        # CRITICAL: Call _setup_indexes() as LAST line in __init__
        self._setup_indexes()
    
    def _setup_indexes(self):
        """Setup DynamoDB indexes for milestone queries."""
        
        # Primary index: Milestone within project (adjacency pattern)
        primary = DynamoDBIndex()
        primary.name = "primary"
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(("project", self.project_id))
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: DynamoDBKey.build_key(("milestone", self.id or ""))
        self.indexes.add_primary(primary)
    
    # Properties - Identity
    @property
    def milestone_id(self) -> str | None:
        """Unique milestone ID."""
        return self._milestone_id or self.id
    
    @milestone_id.setter
    def milestone_id(self, value: str | None):
        self._milestone_id = value
        if value:
            self.id = value
    
    @property
    def project_id(self) -> str | None:
        """Project ID this milestone belongs to."""
        return self._project_id
    
    @project_id.setter
    def project_id(self, value: str | None):
        self._project_id = value
    
    # Properties - Milestone Information
    @property
    def name(self) -> str | None:
        """Milestone name."""
        return self._name
    
    @name.setter
    def name(self, value: str | None):
        self._name = value
    
    @property
    def description(self) -> str | None:
        """Milestone description."""
        return self._description
    
    @description.setter
    def description(self, value: str | None):
        self._description = value
    
    # Properties - Status
    @property
    def status(self) -> str:
        """Milestone status."""
        return self._status
    
    @status.setter
    def status(self, value: str):
        if value and value not in MilestoneStatus.ALL:
            raise ValueError(f"Invalid status: {value}. Must be one of {MilestoneStatus.ALL}")
        self._status = value or MilestoneStatus.PLANNED
    
    # Properties - Dates
    @property
    def due_date(self) -> str | None:
        """Due date (ISO format)."""
        return self._due_date
    
    @due_date.setter
    def due_date(self, value: str | None):
        self._due_date = value
    
    @property
    def completed_date(self) -> str | None:
        """Completed date (ISO format)."""
        return self._completed_date
    
    @completed_date.setter
    def completed_date(self, value: str | None):
        self._completed_date = value
    
    # Properties - Optional Links
    @property
    def workflow_step_id(self) -> str | None:
        """Linked workflow step ID."""
        return self._workflow_step_id
    
    @workflow_step_id.setter
    def workflow_step_id(self, value: str | None):
        self._workflow_step_id = value
    
    @property
    def owner_user_id(self) -> str | None:
        """Responsible user ID."""
        return self._owner_user_id
    
    @owner_user_id.setter
    def owner_user_id(self, value: str | None):
        self._owner_user_id = value
    
    # Helper Methods
    def is_planned(self) -> bool:
        """Check if milestone is planned."""
        return self._status == MilestoneStatus.PLANNED
    
    def is_in_progress(self) -> bool:
        """Check if milestone is in progress."""
        return self._status == MilestoneStatus.IN_PROGRESS
    
    def is_completed(self) -> bool:
        """Check if milestone is completed."""
        return self._status == MilestoneStatus.COMPLETED
    
    def is_cancelled(self) -> bool:
        """Check if milestone is cancelled."""
        return self._status == MilestoneStatus.CANCELLED
    
    def is_overdue(self) -> bool:
        """Check if milestone is overdue (past due date and not completed)."""
        if not self._due_date or self._status in [MilestoneStatus.COMPLETED, MilestoneStatus.CANCELLED]:
            return False
        from datetime import datetime
        try:
            due = datetime.fromisoformat(self._due_date.replace('Z', '+00:00'))
            return datetime.now(due.tzinfo) > due
        except (ValueError, AttributeError):
            return False
    
    def get_searchable_text(self) -> str:
        """Get text for keyword search indexing."""
        parts = [self._name or ""]
        if self._description:
            parts.append(self._description)
        return " ".join(parts)
