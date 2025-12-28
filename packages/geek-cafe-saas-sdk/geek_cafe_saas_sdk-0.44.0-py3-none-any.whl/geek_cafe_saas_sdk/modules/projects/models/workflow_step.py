"""
WorkflowStep model for workflow steps.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from typing import Optional
from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey
from geek_cafe_saas_sdk.core.models.base_tenant_user_model import BaseTenantUserModel


class StepStatus:
    """Workflow step status constants."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    
    ALL = [NOT_STARTED, IN_PROGRESS, COMPLETED, SKIPPED]


class WorkflowStep(BaseTenantUserModel):
    """
    WorkflowStep model for individual workflow steps.
    
    Represents a single step in a project workflow.
    
    Access Patterns (DynamoDB Keys):
    - pk: project#{project_id}
    - sk: step#{workflow_id}#{sort_order:04d}
    """

    def __init__(self):
        super().__init__()
        
        # Identity
        self._step_id: str | None = None
        self._workflow_id: str | None = None
        self._project_id: str | None = None
        
        # Step Information
        self._name: str | None = None
        self._description: str | None = None
        self._sort_order: int | None = None  # 1-based sequence
        
        # Status
        self._status: str = StepStatus.NOT_STARTED
        
        # Optional fields
        self._expected_duration_days: int | None = None
        self._entry_criteria: str | None = None
        self._exit_criteria: str | None = None
        
        # Timestamps
        self._started_at: str | None = None  # ISO datetime
        self._completed_at: str | None = None  # ISO datetime
        
        # Model metadata
        self.model_name = "workflow_step"
        self.model_name_plural = "workflow_steps"
        
        # CRITICAL: Call _setup_indexes() as LAST line in __init__
        self._setup_indexes()
    
    def _setup_indexes(self):
        """Setup DynamoDB indexes for step queries."""
        
        # Primary index: Step within project (adjacency pattern)
        # Sort key includes workflow_id and sort_order for ordering
        primary = DynamoDBIndex()
        primary.name = "primary"
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(("project", self.project_id))
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: DynamoDBKey.build_key(
            ("step", self.workflow_id or ""),
            ("order", self._query_index_sort_order()),
        )
        self.indexes.add_primary(primary)
    
    # Properties - Identity
    @property
    def step_id(self) -> str | None:
        """Unique step ID."""
        return self._step_id or self.id
    
    @step_id.setter
    def step_id(self, value: str | None):
        self._step_id = value
        if value:
            self.id = value
    
    @property
    def workflow_id(self) -> str | None:
        """Workflow ID this step belongs to."""
        return self._workflow_id
    
    @workflow_id.setter
    def workflow_id(self, value: str | None):
        self._workflow_id = value
    
    @property
    def project_id(self) -> str | None:
        """Project ID this step belongs to."""
        return self._project_id
    
    @project_id.setter
    def project_id(self, value: str | None):
        self._project_id = value
    
    # Properties - Step Information
    @property
    def name(self) -> str | None:
        """Step name."""
        return self._name
    
    @name.setter
    def name(self, value: str | None):
        self._name = value
    
    @property
    def description(self) -> str | None:
        """Step description."""
        return self._description
    
    @description.setter
    def description(self, value: str | None):
        self._description = value
    
    @property
    def sort_order(self) -> int | None:
        """Step order in the workflow (1-based)."""
                    
        return self._sort_order
    
    @sort_order.setter
    def sort_order(self, value: int | None):
        self._sort_order = value if value is not None else 1
    
    # Properties - Status
    @property
    def status(self) -> str:
        """Step status."""
        return self._status
    
    @status.setter
    def status(self, value: str):
        if value and value not in StepStatus.ALL:
            raise ValueError(f"Invalid status: {value}. Must be one of {StepStatus.ALL}")
        self._status = value or StepStatus.NOT_STARTED
    
    # Properties - Optional
    @property
    def expected_duration_days(self) -> int | None:
        """Expected duration in days."""
        return self._expected_duration_days
    
    @expected_duration_days.setter
    def expected_duration_days(self, value: int | None):
        self._expected_duration_days = value
    
    @property
    def entry_criteria(self) -> str | None:
        """Entry criteria for this step."""
        return self._entry_criteria
    
    @entry_criteria.setter
    def entry_criteria(self, value: str | None):
        self._entry_criteria = value
    
    @property
    def exit_criteria(self) -> str | None:
        """Exit criteria for this step."""
        return self._exit_criteria
    
    @exit_criteria.setter
    def exit_criteria(self, value: str | None):
        self._exit_criteria = value
    
    # Properties - Timestamps
    @property
    def started_at(self) -> str | None:
        """When the step was started (ISO datetime)."""
        return self._started_at
    
    @started_at.setter
    def started_at(self, value: str | None):
        self._started_at = value
    
    @property
    def completed_at(self) -> str | None:
        """When the step was completed (ISO datetime)."""
        return self._completed_at
    
    @completed_at.setter
    def completed_at(self, value: str | None):
        self._completed_at = value
    
    # Helper Methods
    def is_not_started(self) -> bool:
        """Check if step has not started."""
        return self._status == StepStatus.NOT_STARTED
    
    def is_in_progress(self) -> bool:
        """Check if step is in progress."""
        return self._status == StepStatus.IN_PROGRESS
    
    def is_completed(self) -> bool:
        """Check if step is completed."""
        return self._status == StepStatus.COMPLETED
    
    def is_skipped(self) -> bool:
        """Check if step was skipped."""
        return self._status == StepStatus.SKIPPED
    
    def is_done(self) -> bool:
        """Check if step is done (completed or skipped)."""
        return self._status in [StepStatus.COMPLETED, StepStatus.SKIPPED]

    def _query_index_sort_order(self) -> str:
        """Get the sort order for the primary index."""
        if not self.sort_order:
            return ""
        return f"{self.sort_order:06d}"