"""
Execution model for async task/workflow execution tracking.

Tracks the status and progress of asynchronous operations like Step Functions,
Lambda invocations, SQS processing, etc.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from typing import Dict, Any, Optional, List
from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey
from geek_cafe_saas_sdk.core.models.base_tenant_user_model import BaseTenantUserModel


class ExecutionStatus:
    """Execution status constants."""
    PENDING = "pending"        # Created but not yet started
    RUNNING = "running"        # Currently executing
    SUCCEEDED = "succeeded"    # Completed successfully
    FAILED = "failed"          # Completed with error
    CANCELLED = "cancelled"    # Manually cancelled
    TIMED_OUT = "timed_out"    # Exceeded time limit
    
    ALL = [PENDING, RUNNING, SUCCEEDED, FAILED, CANCELLED, TIMED_OUT]
    
    # Terminal states (execution is complete)
    TERMINAL = [SUCCEEDED, FAILED, CANCELLED, TIMED_OUT]
    
    # Valid transitions
    TRANSITIONS = {
        PENDING: [RUNNING, CANCELLED],
        RUNNING: [SUCCEEDED, FAILED, CANCELLED, TIMED_OUT],
        SUCCEEDED: [],  # Terminal
        FAILED: [PENDING],  # Allow retry
        CANCELLED: [],  # Terminal
        TIMED_OUT: [PENDING],  # Allow retry
    }
    
    @classmethod
    def can_transition(cls, from_status: str, to_status: str) -> bool:
        """Check if a status transition is valid."""
        return to_status in cls.TRANSITIONS.get(from_status, [])
    
    @classmethod
    def is_terminal(cls, status: str) -> bool:
        """Check if status is a terminal state."""
        return status in cls.TERMINAL


class ExecutionType:
    """Execution type constants."""
    STEP_FUNCTION = "step_function"
    LAMBDA = "lambda"
    SQS = "sqs"
    SNS = "sns"
    EVENT_BRIDGE = "event_bridge"
    CUSTOM = "custom"
    
    ALL = [STEP_FUNCTION, LAMBDA, SQS, SNS, EVENT_BRIDGE, CUSTOM]


class Execution(BaseTenantUserModel):
    """
    Execution model for tracking async operations.
    
    Represents a single execution unit (Step Function, Lambda, etc.) with
    support for hierarchical tracking via root_id and parent_id.
    
    Multi-Tenancy:
    - tenant_id: Organization/company (can have multiple users)
    - owner_id: Specific user within the tenant who owns this execution
    
    Hierarchy:
    - root_id: The root execution in a chain (self.id for root executions)
    - parent_id: Direct parent execution (None for root executions)
    
    Access Patterns (DynamoDB Keys):
    - pk: EXECUTION#{execution_id}
    - sk: metadata
    - gsi1: Executions by owner + root_id (all related executions)
    - gsi2: Executions by owner + parent_id (direct children)
    - gsi3: Executions by owner + status (for monitoring)
    - gsi4: Executions by tenant + correlation_id (cross-service tracking)
    - gsi5: Executions by owner + resource (linked resource tracking)
    """

    def __init__(self):
        super().__init__()
        
        # Identity
        self._execution_id: str | None = None
        
        # Hierarchy (like file lineage)
        self._root_id: str | None = None      # Root execution in chain (self.id for roots)
        self._parent_id: str | None = None    # Direct parent execution
        
        # Correlation (cross-service tracking)
        self._correlation_id: str | None = None   # Links related executions across services
        self._idempotency_key: str | None = None  # Prevents duplicate processing
        
        # Classification
        self._execution_type: str = ExecutionType.CUSTOM
        self._name: str | None = None             # Human-readable name
        self._description: str | None = None
        
        # AWS Resource (optional)
        self._resource_arn: str | None = None     # AWS ARN if applicable (Step Function ARN, etc.)
        self._execution_arn: str | None = None    # Specific execution ARN
        
        # Status
        self._status: str = ExecutionStatus.PENDING
        self._progress_percent: int | None = None  # 0-100 for progress tracking
        self._current_step: str | None = None      # Current step name
        self._current_step_index: int | None = None  # Current step index (0-based)
        self._total_steps: int | None = None       # Total steps if known
        
        # Timestamps
        self._started_at: str | None = None        # ISO datetime when started
        self._completed_at: str | None = None      # ISO datetime when completed
        self._started_at_ts: float | None = None   # Timestamp for sorting
        self._completed_at_ts: float | None = None
        self._duration_ms: int | None = None       # Duration in milliseconds
        
        # Input/Output
        self._input_payload: Dict[str, Any] | None = None   # What was passed in
        self._output_payload: Dict[str, Any] | None = None  # Result data
        
        # Error handling
        self._error_code: str | None = None
        self._error_message: str | None = None
        self._error_details: Dict[str, Any] | None = None
        self._retry_count: int = 0
        self._max_retries: int = 3
        
        # Context
        self._triggered_by: str | None = None      # What initiated this (s3_event, api_call, schedule, etc.)
        self._triggered_by_id: str | None = None   # ID of the trigger (e.g., S3 object key)
        
        # Linked Resource (optional - what this execution is processing)
        self._resource_id: str | None = None       # ID of the resource being processed
        self._resource_type: str | None = None     # Type of resource (file, directory, etc.)
        
        # Flexible metadata
        self._metadata: Dict[str, Any] | None = None
        
        # TTL (optional - for auto-expiration)
        self._ttl: int | None = None               # Unix timestamp for DynamoDB TTL
        
        # Child tracking (denormalized for quick access)
        self._child_count: int = 0
        self._completed_child_count: int = 0
        self._failed_child_count: int = 0
        
        # Model metadata
        self.model_name = "execution"
        self.model_name_plural = "executions"
        
        # CRITICAL: Call _setup_indexes() as LAST line in __init__
        self._setup_indexes()
    
    def _setup_indexes(self):
        """Setup DynamoDB indexes for execution queries."""
        
        # Primary index: Execution by ID (allows direct lookup)
        primary = DynamoDBIndex()
        primary.name = "primary"
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(("execution", self.id))
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: "metadata"
        self.indexes.add_primary(primary)
        
        # GSI1: Executions by root_id (all related executions in a chain)
        self._setup_gsi1()
        
        # GSI2: Executions by parent_id (direct children)
        self._setup_gsi2()
        
        # GSI3: Executions by status (for monitoring)
        self._setup_gsi3()
        
        # GSI4: Executions by execution_type (execution_type tracking)
        self._setup_gsi4()
        
        # GSI5: Executions by resource (linked resource tracking)
        self._setup_gsi5()
    
    def _setup_gsi1(self):
        """GSI1: Executions by root_id (all related executions)."""
        gsi = DynamoDBIndex()
        gsi.name = "gsi1"
        gsi.partition_key.attribute_name = "gsi1_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(
            ("tenant", self.tenant_id),
            ("owner", self.owner_id)
        )
        gsi.sort_key.attribute_name = "gsi1_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
            ("root", self._query_index_root_id()),
            ("ts", self._query_index_started_at_ts())
        )
        self.indexes.add_secondary(gsi)
    
    def _setup_gsi2(self):
        """GSI2: Executions by parent_id (direct children)."""
        gsi = DynamoDBIndex()
        gsi.name = "gsi2"
        gsi.partition_key.attribute_name = "gsi2_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(
            ("tenant", self.tenant_id),
            ("owner", self.owner_id)
        )
        gsi.sort_key.attribute_name = "gsi2_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
            ("parent", self._query_index_parent_id()),
            ("ts", self._query_index_started_at_ts())
        )
        self.indexes.add_secondary(gsi)
    
    def _setup_gsi3(self):
        """GSI3: Executions by status (for monitoring)."""
        gsi = DynamoDBIndex()
        gsi.name = "gsi3"
        gsi.partition_key.attribute_name = "gsi3_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(
            ("tenant", self.tenant_id),
            ("owner", self.owner_id)
        )
        gsi.sort_key.attribute_name = "gsi3_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
            ("status", self._status or ""),
            ("ts", self._query_index_started_at_ts())
        )
        self.indexes.add_secondary(gsi)
    
    def _setup_gsi4(self):
        """GSI4: Executions by execution_type (cross-service tracking)."""
        gsi = DynamoDBIndex()
        gsi.name = "gsi4"
        gsi.partition_key.attribute_name = "gsi4_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(
            ("owner", self.owner_id),
            ("execution_type", self._query_index_execution_type())
        )
        gsi.sort_key.attribute_name = "gsi4_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
            ("ts", self._query_index_started_at_ts())
        )
        self.indexes.add_secondary(gsi)
    
    def _setup_gsi5(self):
        """GSI5: Executions by resource (linked resource tracking)."""
        gsi = DynamoDBIndex()
        gsi.name = "gsi5"
        gsi.partition_key.attribute_name = "gsi5_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(
            ("tenant", self.tenant_id),
            ("owner", self.owner_id)
        )
        gsi.sort_key.attribute_name = "gsi5_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
            ("resource_type", self._resource_type or ""),
            ("resource", self._resource_id or ""),
            ("ts", self._query_index_started_at_ts())
        )
        self.indexes.add_secondary(gsi)
    
    # Query index helpers (return empty string for begins_with queries)
    def _query_index_root_id(self) -> str:
        return self._root_id or self.id or ""
    
    def _query_index_parent_id(self) -> str:
        return self._parent_id or ""
    
    def _query_index_execution_type(self) -> str:
        return self._execution_type or ""
    
    def _query_index_started_at_ts(self) -> float:
        return self._started_at_ts or self.created_utc_ts or ""
    
    # Properties - Identity
    @property
    def execution_id(self) -> str | None:
        """Unique execution ID."""
        return self._execution_id or self.id
    
    @execution_id.setter
    def execution_id(self, value: str | None):
        self._execution_id = value
        if value:
            self.id = value
    
    # Properties - Hierarchy
    @property
    def root_id(self) -> str | None:
        """Root execution in chain (self.id for root executions)."""
        return self._root_id or self.id
    
    @root_id.setter
    def root_id(self, value: str | None):
        self._root_id = value
    
    @property
    def parent_id(self) -> str | None:
        """Direct parent execution (None for root executions)."""
        return self._parent_id
    
    @parent_id.setter
    def parent_id(self, value: str | None):
        self._parent_id = value
    
    # Properties - Correlation
    @property
    def correlation_id(self) -> str | None:
        """Correlation ID for cross-service tracking."""
        return self._correlation_id
    
    @correlation_id.setter
    def correlation_id(self, value: str | None):
        self._correlation_id = value
    
    @property
    def idempotency_key(self) -> str | None:
        """Idempotency key to prevent duplicate processing."""
        return self._idempotency_key
    
    @idempotency_key.setter
    def idempotency_key(self, value: str | None):
        self._idempotency_key = value
    
    # Properties - Classification
    @property
    def execution_type(self) -> str:
        """Type of execution (step_function, lambda, sqs, etc.)."""
        return self._execution_type
    
    @execution_type.setter
    def execution_type(self, value: str):
        self._execution_type = value
    
    @property
    def name(self) -> str | None:
        """Human-readable name."""
        return self._name
    
    @name.setter
    def name(self, value: str | None):
        self._name = value
    
    @property
    def description(self) -> str | None:
        """Description of the execution."""
        return self._description
    
    @description.setter
    def description(self, value: str | None):
        self._description = value
    
    # Properties - AWS Resource
    @property
    def resource_arn(self) -> str | None:
        """AWS ARN of the resource (Step Function ARN, etc.)."""
        return self._resource_arn
    
    @resource_arn.setter
    def resource_arn(self, value: str | None):
        self._resource_arn = value
    
    @property
    def execution_arn(self) -> str | None:
        """Specific execution ARN."""
        return self._execution_arn
    
    @execution_arn.setter
    def execution_arn(self, value: str | None):
        self._execution_arn = value
    
    # Properties - Status
    @property
    def status(self) -> str:
        """Current execution status."""
        return self._status
    
    @status.setter
    def status(self, value: str):
        self._status = value
    
    @property
    def progress_percent(self) -> int | None:
        """Progress percentage (0-100)."""
        return self._progress_percent
    
    @progress_percent.setter
    def progress_percent(self, value: int | None):
        if value is not None:
            value = max(0, min(100, value))  # Clamp to 0-100
        self._progress_percent = value
    
    @property
    def current_step(self) -> str | None:
        """Current step name."""
        return self._current_step
    
    @current_step.setter
    def current_step(self, value: str | None):
        self._current_step = value
    
    @property
    def current_step_index(self) -> int | None:
        """Current step index (0-based)."""
        return self._current_step_index
    
    @current_step_index.setter
    def current_step_index(self, value: int | None):
        self._current_step_index = value
    
    @property
    def total_steps(self) -> int | None:
        """Total number of steps."""
        return self._total_steps
    
    @total_steps.setter
    def total_steps(self, value: int | None):
        self._total_steps = value
    
    # Properties - Timestamps
    @property
    def started_at(self) -> str | None:
        """ISO datetime when execution started."""
        return self._started_at
    
    @started_at.setter
    def started_at(self, value: str | None):
        self._started_at = value
    
    @property
    def completed_at(self) -> str | None:
        """ISO datetime when execution completed."""
        return self._completed_at
    
    @completed_at.setter
    def completed_at(self, value: str | None):
        self._completed_at = value
    
    @property
    def started_at_ts(self) -> float | None:
        """Timestamp when execution started (for sorting)."""
        return self._started_at_ts
    
    @started_at_ts.setter
    def started_at_ts(self, value: float | None):
        self._started_at_ts = value
    
    @property
    def completed_at_ts(self) -> float | None:
        """Timestamp when execution completed."""
        return self._completed_at_ts
    
    @completed_at_ts.setter
    def completed_at_ts(self, value: float | None):
        self._completed_at_ts = value
    
    @property
    def duration_ms(self) -> int | None:
        """Duration in milliseconds."""
        return self._duration_ms
    
    @duration_ms.setter
    def duration_ms(self, value: int | None):
        self._duration_ms = value
    
    # Properties - Input/Output
    @property
    def input_payload(self) -> Dict[str, Any] | None:
        """Input payload passed to the execution."""
        return self._input_payload
    
    @input_payload.setter
    def input_payload(self, value: Dict[str, Any] | None):
        self._input_payload = value
    
    @property
    def output_payload(self) -> Dict[str, Any] | None:
        """Output/result data from the execution."""
        return self._output_payload
    
    @output_payload.setter
    def output_payload(self, value: Dict[str, Any] | None):
        self._output_payload = value
    
    # Properties - Error handling
    @property
    def error_code(self) -> str | None:
        """Error code if execution failed."""
        return self._error_code
    
    @error_code.setter
    def error_code(self, value: str | None):
        self._error_code = value
    
    @property
    def error_message(self) -> str | None:
        """Error message if execution failed."""
        return self._error_message
    
    @error_message.setter
    def error_message(self, value: str | None):
        self._error_message = value
    
    @property
    def error_details(self) -> Dict[str, Any] | None:
        """Additional error details."""
        return self._error_details
    
    @error_details.setter
    def error_details(self, value: Dict[str, Any] | None):
        self._error_details = value
    
    @property
    def retry_count(self) -> int:
        """Number of retry attempts."""
        return self._retry_count
    
    @retry_count.setter
    def retry_count(self, value: int):
        self._retry_count = value
    
    @property
    def max_retries(self) -> int:
        """Maximum number of retries allowed."""
        return self._max_retries
    
    @max_retries.setter
    def max_retries(self, value: int):
        self._max_retries = value
    
    # Properties - Context
    @property
    def triggered_by(self) -> str | None:
        """What initiated this execution (s3_event, api_call, schedule, etc.)."""
        return self._triggered_by
    
    @triggered_by.setter
    def triggered_by(self, value: str | None):
        self._triggered_by = value
    
    @property
    def triggered_by_id(self) -> str | None:
        """ID of the trigger (e.g., S3 object key)."""
        return self._triggered_by_id
    
    @triggered_by_id.setter
    def triggered_by_id(self, value: str | None):
        self._triggered_by_id = value
    
    # Properties - Linked Resource
    @property
    def resource_id(self) -> str | None:
        """ID of the resource being processed."""
        return self._resource_id
    
    @resource_id.setter
    def resource_id(self, value: str | None):
        self._resource_id = value
    
    @property
    def resource_type(self) -> str | None:
        """Type of resource being processed (file, directory, etc.)."""
        return self._resource_type
    
    @resource_type.setter
    def resource_type(self, value: str | None):
        self._resource_type = value
    
    # Properties - Metadata
    @property
    def metadata(self) -> Dict[str, Any] | None:
        """Flexible additional metadata."""
        return self._metadata
    
    @metadata.setter
    def metadata(self, value: Dict[str, Any] | None):
        self._metadata = value
    
    # Properties - TTL
    @property
    def ttl(self) -> int | None:
        """Unix timestamp for DynamoDB TTL (auto-expiration)."""
        return self._ttl
    
    @ttl.setter
    def ttl(self, value: int | None):
        self._ttl = value
    
    # Properties - Child tracking
    @property
    def child_count(self) -> int:
        """Total number of child executions."""
        return self._child_count
    
    @child_count.setter
    def child_count(self, value: int):
        self._child_count = value
    
    @property
    def completed_child_count(self) -> int:
        """Number of completed child executions."""
        return self._completed_child_count
    
    @completed_child_count.setter
    def completed_child_count(self, value: int):
        self._completed_child_count = value
    
    @property
    def failed_child_count(self) -> int:
        """Number of failed child executions."""
        return self._failed_child_count
    
    @failed_child_count.setter
    def failed_child_count(self, value: int):
        self._failed_child_count = value
    
    # Computed properties
    @property
    def is_root(self) -> bool:
        """Check if this is a root execution (no parent)."""
        return self._parent_id is None
    
    @property
    def is_terminal(self) -> bool:
        """Check if execution is in a terminal state."""
        return ExecutionStatus.is_terminal(self._status)
    
    @property
    def can_retry(self) -> bool:
        """Check if execution can be retried."""
        return (
            self._status in [ExecutionStatus.FAILED, ExecutionStatus.TIMED_OUT] and
            self._retry_count < self._max_retries
        )
