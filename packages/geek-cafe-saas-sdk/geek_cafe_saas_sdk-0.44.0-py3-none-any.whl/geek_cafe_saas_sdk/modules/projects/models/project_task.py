"""
ProjectTask model for project tasks.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from typing import List, Optional
from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey
from geek_cafe_saas_sdk.core.models.base_tenant_user_model import BaseTenantUserModel


class TaskStatus:
    """Task status constants."""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    DONE = "done"
    CANCELLED = "cancelled"
    
    ALL = [TODO, IN_PROGRESS, BLOCKED, DONE, CANCELLED]
    
    # Valid transitions
    TRANSITIONS = {
        TODO: [IN_PROGRESS, BLOCKED, DONE, CANCELLED],
        IN_PROGRESS: [TODO, BLOCKED, DONE, CANCELLED],
        BLOCKED: [TODO, IN_PROGRESS, DONE, CANCELLED],
        DONE: [TODO, IN_PROGRESS],  # Allow reopening
        CANCELLED: [TODO],  # Allow restoring
    }
    
    @classmethod
    def can_transition(cls, from_status: str, to_status: str) -> bool:
        """Check if a status transition is valid."""
        return to_status in cls.TRANSITIONS.get(from_status, [])


class TaskPriority:
    """Task priority constants."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"
    
    ALL = [LOW, NORMAL, HIGH, CRITICAL]


class ProjectTask(BaseTenantUserModel):
    """
    ProjectTask model for project tasks.
    
    Represents a fine-grained work item associated with a project.
    
    Access Patterns (DynamoDB Keys):
    - pk: project#{project_id}
    - sk: task#{task_id}
    - gsi1_pk: tenant#{tenant_id}#assignee#{assignee_user_id}
    - gsi1_sk: task#{status}#{due_date_ts}
    """

    def __init__(self):
        super().__init__()
        
        # Identity
        self._task_id: str | None = None
        self._project_id: str | None = None
        
        # Task Information
        self._title: str | None = None
        self._description: str | None = None
        
        # Status & Priority
        self._status: str = TaskStatus.TODO
        self._priority: str = TaskPriority.NORMAL
        
        # Assignment
        self._assignee_user_id: str | None = None
        self._reporter_user_id: str | None = None
        
        # Dates
        self._due_date: str | None = None  # ISO date string
        self._due_date_ts: float | None = None  # Timestamp for sorting
        self._completed_date: str | None = None
        
        # Optional links
        self._milestone_id: str | None = None
        self._workflow_step_id: str | None = None
        
        # Classification
        self._tags: List[str] = []
        
        # Model metadata
        self.model_name = "project_task"
        self.model_name_plural = "project_tasks"
        
        # CRITICAL: Call _setup_indexes() as LAST line in __init__
        self._setup_indexes()
    
    def _setup_indexes(self):
        """Setup DynamoDB indexes for task queries."""
        
        # Primary index: Task within project (adjacency pattern)
        primary = DynamoDBIndex()
        primary.name = "primary"
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(("project", self.project_id))
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: DynamoDBKey.build_key(("task", self.id or ""))
        self.indexes.add_primary(primary)
        
        # GSI1: Tasks by assignee (find all tasks for a user)
        # PK: tenant + assignee (required for query)
        # SK: status + due date (optional for begins_with filtering)
        gsi = DynamoDBIndex()
        gsi.name = "gsi1"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(
            ("tenant", self.tenant_id),
            ("assignee", self._query_index_assignee()),
        )
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
            ("task", ""),
            ("status", self._query_index_status()),
            ("due", self._query_index_due_date()),
        )
        self.indexes.add_secondary(gsi)
    
    # Properties - Identity
    @property
    def task_id(self) -> str | None:
        """Unique task ID."""
        return self._task_id or self.id
    
    @task_id.setter
    def task_id(self, value: str | None):
        self._task_id = value
        if value:
            self.id = value
    
    @property
    def project_id(self) -> str | None:
        """Project ID this task belongs to."""
        return self._project_id
    
    @project_id.setter
    def project_id(self, value: str | None):
        self._project_id = value
    
    # Properties - Task Information
    @property
    def title(self) -> str | None:
        """Task title."""
        return self._title
    
    @title.setter
    def title(self, value: str | None):
        self._title = value
    
    @property
    def description(self) -> str | None:
        """Task description."""
        return self._description
    
    @description.setter
    def description(self, value: str | None):
        self._description = value
    
    # Properties - Status & Priority
    @property
    def status(self) -> str:
        """Task status."""
        return self._status
    
    @status.setter
    def status(self, value: str):
        if value and value not in TaskStatus.ALL:
            raise ValueError(f"Invalid status: {value}. Must be one of {TaskStatus.ALL}")
        self._status = value or TaskStatus.TODO
    
    @property
    def priority(self) -> str:
        """Task priority."""
        return self._priority
    
    @priority.setter
    def priority(self, value: str):
        if value and value not in TaskPriority.ALL:
            raise ValueError(f"Invalid priority: {value}. Must be one of {TaskPriority.ALL}")
        self._priority = value or TaskPriority.NORMAL
    
    # Properties - Assignment
    @property
    def assignee_user_id(self) -> str | None:
        """Assigned user ID."""
        return self._assignee_user_id
    
    @assignee_user_id.setter
    def assignee_user_id(self, value: str | None):
        self._assignee_user_id = value
    
    @property
    def reporter_user_id(self) -> str | None:
        """Reporter user ID."""
        return self._reporter_user_id
    
    @reporter_user_id.setter
    def reporter_user_id(self, value: str | None):
        self._reporter_user_id = value
    
    # Properties - Dates
    @property
    def due_date(self) -> str | None:
        """Due date (ISO format)."""
        return self._due_date
    
    @due_date.setter
    def due_date(self, value: str | None):
        self._due_date = value
        # Also set timestamp for sorting
        if value:
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                self._due_date_ts = dt.timestamp()
            except (ValueError, AttributeError):
                self._due_date_ts = None
        else:
            self._due_date_ts = None
    
    @property
    def due_date_ts(self) -> float | None:
        """Due date timestamp for sorting."""
        return self._due_date_ts
    
    @due_date_ts.setter
    def due_date_ts(self, value: float | None):
        self._due_date_ts = value
    
    @property
    def completed_date(self) -> str | None:
        """Completed date (ISO format)."""
        return self._completed_date
    
    @completed_date.setter
    def completed_date(self, value: str | None):
        self._completed_date = value
    
    # Properties - Optional Links
    @property
    def milestone_id(self) -> str | None:
        """Linked milestone ID."""
        return self._milestone_id
    
    @milestone_id.setter
    def milestone_id(self, value: str | None):
        self._milestone_id = value
    
    @property
    def workflow_step_id(self) -> str | None:
        """Linked workflow step ID."""
        return self._workflow_step_id
    
    @workflow_step_id.setter
    def workflow_step_id(self, value: str | None):
        self._workflow_step_id = value
    
    # Properties - Classification
    @property
    def tags(self) -> List[str]:
        """Task tags."""
        return self._tags
    
    @tags.setter
    def tags(self, value: List[str]):
        self._tags = value if value else []
    
    # Helper Methods
    def is_todo(self) -> bool:
        """Check if task is todo."""
        return self._status == TaskStatus.TODO
    
    def is_in_progress(self) -> bool:
        """Check if task is in progress."""
        return self._status == TaskStatus.IN_PROGRESS
    
    def is_blocked(self) -> bool:
        """Check if task is blocked."""
        return self._status == TaskStatus.BLOCKED
    
    def is_done(self) -> bool:
        """Check if task is done."""
        return self._status == TaskStatus.DONE
    
    def is_cancelled(self) -> bool:
        """Check if task is cancelled."""
        return self._status == TaskStatus.CANCELLED
    
    def is_open(self) -> bool:
        """Check if task is open (not done or cancelled)."""
        return self._status not in [TaskStatus.DONE, TaskStatus.CANCELLED]
    
    def is_assigned(self) -> bool:
        """Check if task is assigned."""
        return self._assignee_user_id is not None
    
    def can_transition_to(self, new_status: str) -> bool:
        """Check if task can transition to a new status."""
        return TaskStatus.can_transition(self._status, new_status)
    
    def is_overdue(self) -> bool:
        """Check if task is overdue."""
        if not self._due_date or self._status in [TaskStatus.DONE, TaskStatus.CANCELLED]:
            return False
        from datetime import datetime
        try:
            due = datetime.fromisoformat(self._due_date.replace('Z', '+00:00'))
            return datetime.now(due.tzinfo) > due
        except (ValueError, AttributeError):
            return False
    
    def get_searchable_text(self) -> str:
        """Get text for keyword search indexing."""
        parts = [self._title or ""]
        if self._description:
            parts.append(self._description)
        if self._tags:
            parts.extend(self._tags)
        return " ".join(parts)
    
    # Query Index Helpers
    def _query_index_assignee(self) -> str:
        """Get assignee for query index. Returns 'unassigned' if not set."""
        return self._assignee_user_id or "unassigned"
    
    def _query_index_status(self) -> str:
        """Get status for query index. Returns empty string if not set for begins_with queries."""
        return self._status or ""
    
    def _query_index_due_date(self) -> str:
        """Get due date for query index. Returns empty string if not set for begins_with queries."""
        if not self._due_date_ts:
            return ""
        return str(self._due_date_ts)
