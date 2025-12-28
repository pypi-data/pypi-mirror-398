"""
Project model for project management.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from typing import List, Optional
from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey
from geek_cafe_saas_sdk.core.models.base_tenant_user_model import BaseTenantUserModel


class ProjectStatus:
    """Project status constants."""
    DRAFT = "draft"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    
    ALL = [DRAFT, ACTIVE, ON_HOLD, COMPLETED, ARCHIVED]
    
    # Valid transitions
    TRANSITIONS = {
        DRAFT: [ACTIVE, ARCHIVED],
        ACTIVE: [ON_HOLD, COMPLETED, ARCHIVED],
        ON_HOLD: [ACTIVE, COMPLETED, ARCHIVED],
        COMPLETED: [ARCHIVED],
        ARCHIVED: [],  # Terminal state
    }
    
    @classmethod
    def can_transition(cls, from_status: str, to_status: str) -> bool:
        """Check if a status transition is valid."""
        return to_status in cls.TRANSITIONS.get(from_status, [])


class ProjectPriority:
    """Project priority constants."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"
    
    ALL = [LOW, NORMAL, HIGH, CRITICAL]


class ProjectType:
    """Project type constants."""
    SOFTWARE = "software"
    CLOUD_DESIGN = "cloud-design"
    PK_ANALYSIS = "pk-analysis"
    NCA_ANALYSIS = "nca-analysis"
    GENERIC = "generic"
    
    ALL = [SOFTWARE, CLOUD_DESIGN, PK_ANALYSIS, NCA_ANALYSIS, GENERIC]


class Project(BaseTenantUserModel):
    """
    Project model for project management.
    
    Represents a unit of work (software project, cloud design, PK analysis, etc.).
    
    Access Patterns (DynamoDB Keys):
    - pk: project#{project_id}
    - sk: metadata
    - gsi1_pk: tenant#{tenant_id}
    - gsi1_sk: project#{status}#{modified_utc_ts}
    """

    def __init__(self):
        super().__init__()
        
        # Identity
        self._project_id: str | None = None
        
        # Project Information
        self._name: str | None = None
        self._description: str | None = None
        self._project_type: str = ProjectType.GENERIC
        
        # Status & Priority
        self._status: str = ProjectStatus.DRAFT
        self._priority: str = ProjectPriority.NORMAL
        
        # Dates
        self._start_date: str | None = None  # ISO date string
        self._target_end_date: str | None = None
        self._actual_end_date: str | None = None
        
        # Classification
        self._tags: List[str] = []
        self._category: str | None = None
        self._domain: str | None = None
        
        # Counters (denormalized for performance)
        self._actor_count: int = 0
        self._task_count: int = 0
        self._milestone_count: int = 0
        self._completed_task_count: int = 0
        self._completed_milestone_count: int = 0
        
        # Model metadata
        self.model_name = "project"
        self.model_name_plural = "projects"
        
        # CRITICAL: Call _setup_indexes() as LAST line in __init__
        self._setup_indexes()
    
    def _setup_indexes(self):
        """Setup DynamoDB indexes for project queries."""
        
        # Primary index: Project by ID
        primary = DynamoDBIndex()
        primary.name = "primary"
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(("project", self.id))
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: "metadata"
        self.indexes.add_primary(primary)
        
        # GSI1: Projects by tenant and status (for listing)
        gsi = DynamoDBIndex()
        gsi.name = "gsi1"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(("tenant", self.tenant_id))
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
            ("project", ""),
            ("status", self._query_index_status()),
            ("modified", self._query_index_modified()),
        )
        self.indexes.add_secondary(gsi)
    
    # Properties - Identity
    @property
    def project_id(self) -> str | None:
        """Unique project ID."""
        return self._project_id or self.id
    
    @project_id.setter
    def project_id(self, value: str | None):
        self._project_id = value
        if value:
            self.id = value
    
    # Properties - Project Information
    @property
    def name(self) -> str | None:
        """Project name."""
        return self._name
    
    @name.setter
    def name(self, value: str | None):
        self._name = value
    
    @property
    def description(self) -> str | None:
        """Project description."""
        return self._description
    
    @description.setter
    def description(self, value: str | None):
        self._description = value
    
    @property
    def project_type(self) -> str:
        """Project type."""
        return self._project_type
    
    @project_type.setter
    def project_type(self, value: str):
        if value and value not in ProjectType.ALL:
            raise ValueError(f"Invalid project type: {value}. Must be one of {ProjectType.ALL}")
        self._project_type = value or ProjectType.GENERIC
    
    # Properties - Status & Priority
    @property
    def status(self) -> str:
        """Project status."""
        return self._status
    
    @status.setter
    def status(self, value: str):
        if value and value not in ProjectStatus.ALL:
            raise ValueError(f"Invalid status: {value}. Must be one of {ProjectStatus.ALL}")
        self._status = value or ProjectStatus.DRAFT
    
    @property
    def priority(self) -> str:
        """Project priority."""
        return self._priority
    
    @priority.setter
    def priority(self, value: str):
        if value and value not in ProjectPriority.ALL:
            raise ValueError(f"Invalid priority: {value}. Must be one of {ProjectPriority.ALL}")
        self._priority = value or ProjectPriority.NORMAL
    
    # Properties - Dates
    @property
    def start_date(self) -> str | None:
        """Project start date (ISO format)."""
        return self._start_date
    
    @start_date.setter
    def start_date(self, value: str | None):
        self._start_date = value
    
    @property
    def target_end_date(self) -> str | None:
        """Target end date (ISO format)."""
        return self._target_end_date
    
    @target_end_date.setter
    def target_end_date(self, value: str | None):
        self._target_end_date = value
    
    @property
    def actual_end_date(self) -> str | None:
        """Actual end date (ISO format)."""
        return self._actual_end_date
    
    @actual_end_date.setter
    def actual_end_date(self, value: str | None):
        self._actual_end_date = value
    
    # Properties - Classification
    @property
    def tags(self) -> List[str]:
        """Project tags."""
        return self._tags
    
    @tags.setter
    def tags(self, value: List[str]):
        self._tags = value if value else []
    
    @property
    def category(self) -> str | None:
        """Project category."""
        return self._category
    
    @category.setter
    def category(self, value: str | None):
        self._category = value
    
    @property
    def domain(self) -> str | None:
        """Project domain."""
        return self._domain
    
    @domain.setter
    def domain(self, value: str | None):
        self._domain = value
    
    # Properties - Counters
    @property
    def actor_count(self) -> int:
        """Number of actors on the project."""
        return self._actor_count
    
    @actor_count.setter
    def actor_count(self, value: int):
        self._actor_count = value if value is not None else 0
    
    @property
    def task_count(self) -> int:
        """Total number of tasks."""
        return self._task_count
    
    @task_count.setter
    def task_count(self, value: int):
        self._task_count = value if value is not None else 0
    
    @property
    def milestone_count(self) -> int:
        """Total number of milestones."""
        return self._milestone_count
    
    @milestone_count.setter
    def milestone_count(self, value: int):
        self._milestone_count = value if value is not None else 0
    
    @property
    def completed_task_count(self) -> int:
        """Number of completed tasks."""
        return self._completed_task_count
    
    @completed_task_count.setter
    def completed_task_count(self, value: int):
        self._completed_task_count = value if value is not None else 0
    
    @property
    def completed_milestone_count(self) -> int:
        """Number of completed milestones."""
        return self._completed_milestone_count
    
    @completed_milestone_count.setter
    def completed_milestone_count(self, value: int):
        self._completed_milestone_count = value if value is not None else 0
    
    # Helper Methods
    def is_active(self) -> bool:
        """Check if project is active."""
        return self._status == ProjectStatus.ACTIVE
    
    def is_completed(self) -> bool:
        """Check if project is completed."""
        return self._status == ProjectStatus.COMPLETED
    
    def is_archived(self) -> bool:
        """Check if project is archived."""
        return self._status == ProjectStatus.ARCHIVED
    
    def is_editable(self) -> bool:
        """Check if project can be edited."""
        return self._status not in [ProjectStatus.COMPLETED, ProjectStatus.ARCHIVED]
    
    def can_transition_to(self, new_status: str) -> bool:
        """Check if project can transition to a new status."""
        return ProjectStatus.can_transition(self._status, new_status)
    
    def get_progress_percent(self) -> float:
        """Calculate task completion percentage."""
        if self._task_count == 0:
            return 0.0
        return (self._completed_task_count / self._task_count) * 100
    
    def get_milestone_progress_percent(self) -> float:
        """Calculate milestone completion percentage."""
        if self._milestone_count == 0:
            return 0.0
        return (self._completed_milestone_count / self._milestone_count) * 100
    
    def increment_actor_count(self, count: int = 1):
        """Increment actor count."""
        self._actor_count += count
    
    def decrement_actor_count(self, count: int = 1):
        """Decrement actor count."""
        self._actor_count = max(0, self._actor_count - count)
    
    def increment_task_count(self, count: int = 1):
        """Increment task count."""
        self._task_count += count
    
    def decrement_task_count(self, count: int = 1):
        """Decrement task count."""
        self._task_count = max(0, self._task_count - count)
    
    def increment_completed_task_count(self, count: int = 1):
        """Increment completed task count."""
        self._completed_task_count += count
    
    def decrement_completed_task_count(self, count: int = 1):
        """Decrement completed task count."""
        self._completed_task_count = max(0, self._completed_task_count - count)
    
    def increment_milestone_count(self, count: int = 1):
        """Increment milestone count."""
        self._milestone_count += count
    
    def decrement_milestone_count(self, count: int = 1):
        """Decrement milestone count."""
        self._milestone_count = max(0, self._milestone_count - count)
    
    def increment_completed_milestone_count(self, count: int = 1):
        """Increment completed milestone count."""
        self._completed_milestone_count += count
    
    def decrement_completed_milestone_count(self, count: int = 1):
        """Decrement completed milestone count."""
        self._completed_milestone_count = max(0, self._completed_milestone_count - count)
    
    def get_searchable_text(self) -> str:
        """Get text for keyword search indexing."""
        parts = [self._name or ""]
        if self._description:
            parts.append(self._description)
        if self._tags:
            parts.extend(self._tags)
        if self._category:
            parts.append(self._category)
        if self._domain:
            parts.append(self._domain)
        return " ".join(parts)
    
    def _query_index_status(self) -> str:
        """Get status for query index. Returns empty string if not set for begins_with queries."""
        return self._status or ""
    
    def _query_index_modified(self) -> str:
        """Get modified timestamp for query index. Returns empty string if not set for begins_with queries."""
        if not self.modified_utc_ts:
            return ""
        return str(self.modified_utc_ts)
