"""
ProjectWorkflow model for project workflows.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from typing import Optional
from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey
from geek_cafe_saas_sdk.core.models.base_tenant_user_model import BaseTenantUserModel


class WorkflowStatus:
    """Workflow status constants."""
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    
    ALL = [DRAFT, ACTIVE, ARCHIVED]


class ProjectWorkflow(BaseTenantUserModel):
    """
    ProjectWorkflow model for project workflows.
    
    Defines a workflow (set of ordered steps) for a project.
    MVP: One primary workflow per project.
    
    Access Patterns (DynamoDB Keys):
    - pk: project#{project_id}
    - sk: workflow#{workflow_id}
    """

    def __init__(self):
        super().__init__()
        
        # Identity
        self._workflow_id: str | None = None
        self._project_id: str | None = None
        
        # Workflow Information
        self._name: str | None = None
        self._description: str | None = None
        
        # Flags
        self._is_primary: bool = True  # MVP: One primary workflow
        self._status: str = WorkflowStatus.DRAFT
        
        # Counters
        self._step_count: int = 0
        self._completed_step_count: int = 0
        self._current_step_order: int | None = None  # Current active step
        
        # Model metadata
        self.model_name = "project_workflow"
        self.model_name_plural = "project_workflows"
        
        # CRITICAL: Call _setup_indexes() as LAST line in __init__
        self._setup_indexes()
    
    def _setup_indexes(self):
        """Setup DynamoDB indexes for workflow queries."""
        
        # Primary index: Workflow within project (adjacency pattern)
        primary = DynamoDBIndex()
        primary.name = "primary"
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(("project", self.project_id))
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: DynamoDBKey.build_key(("workflow", self.id or ""))
        self.indexes.add_primary(primary)
    
    # Properties - Identity
    @property
    def workflow_id(self) -> str | None:
        """Unique workflow ID."""
        return self._workflow_id or self.id
    
    @workflow_id.setter
    def workflow_id(self, value: str | None):
        self._workflow_id = value
        if value:
            self.id = value
    
    @property
    def project_id(self) -> str | None:
        """Project ID this workflow belongs to."""
        return self._project_id
    
    @project_id.setter
    def project_id(self, value: str | None):
        self._project_id = value
    
    # Properties - Workflow Information
    @property
    def name(self) -> str | None:
        """Workflow name."""
        return self._name
    
    @name.setter
    def name(self, value: str | None):
        self._name = value
    
    @property
    def description(self) -> str | None:
        """Workflow description."""
        return self._description
    
    @description.setter
    def description(self, value: str | None):
        self._description = value
    
    # Properties - Flags
    @property
    def is_primary(self) -> bool:
        """Whether this is the primary workflow."""
        return self._is_primary
    
    @is_primary.setter
    def is_primary(self, value: bool):
        self._is_primary = value if value is not None else True
    
    @property
    def status(self) -> str:
        """Workflow status."""
        return self._status
    
    @status.setter
    def status(self, value: str):
        if value and value not in WorkflowStatus.ALL:
            raise ValueError(f"Invalid status: {value}. Must be one of {WorkflowStatus.ALL}")
        self._status = value or WorkflowStatus.DRAFT
    
    # Properties - Counters
    @property
    def step_count(self) -> int:
        """Total number of steps."""
        return self._step_count
    
    @step_count.setter
    def step_count(self, value: int):
        self._step_count = value if value is not None else 0
    
    @property
    def completed_step_count(self) -> int:
        """Number of completed steps."""
        return self._completed_step_count
    
    @completed_step_count.setter
    def completed_step_count(self, value: int):
        self._completed_step_count = value if value is not None else 0
    
    @property
    def current_step_order(self) -> int | None:
        """Current active step order."""
        return self._current_step_order
    
    @current_step_order.setter
    def current_step_order(self, value: int | None):
        self._current_step_order = value
    
    # Helper Methods
    def is_active(self) -> bool:
        """Check if workflow is active."""
        return self._status == WorkflowStatus.ACTIVE
    
    def is_complete(self) -> bool:
        """Check if all steps are completed."""
        return self._step_count > 0 and self._completed_step_count >= self._step_count
    
    def get_progress_percent(self) -> float:
        """Calculate step completion percentage."""
        if self._step_count == 0:
            return 0.0
        return (self._completed_step_count / self._step_count) * 100
    
    def increment_step_count(self, count: int = 1):
        """Increment step count."""
        self._step_count += count
    
    def decrement_step_count(self, count: int = 1):
        """Decrement step count."""
        self._step_count = max(0, self._step_count - count)
    
    def increment_completed_step_count(self, count: int = 1):
        """Increment completed step count."""
        self._completed_step_count += count
    
    def decrement_completed_step_count(self, count: int = 1):
        """Decrement completed step count."""
        self._completed_step_count = max(0, self._completed_step_count - count)
