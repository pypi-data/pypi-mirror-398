"""
UsageRecord model for metered addon usage tracking.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

import datetime as dt
from typing import Dict, Any, Optional
from geek_cafe_saas_sdk.core.models.base_model import BaseModel
from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey


class UsageRecord(BaseModel):
    """
    Usage record for metered billing.
    
    Tracks usage events for metered addons (API calls, storage, etc.)
    Aggregated for billing at end of period.
    
    Key Features:
    - Event-based tracking
    - Aggregation support
    - Idempotency keys
    - Metadata for debugging
    
    Examples:
    - API Calls: 1000 calls made
    - Storage: 50GB used
    - SMS Sent: 150 messages
    - Compute Hours: 25 hours
    """
    
    # Action constants
    ACTION_INCREMENT = "increment"  # Add to usage
    ACTION_DECREMENT = "decrement"  # Subtract from usage
    ACTION_SET = "set"  # Set absolute value
    
    def __init__(self):
        super().__init__()
        
        # Identification
        self._tenant_id: str = ""
        self._subscription_id: str = ""
        self._addon_code: str = ""
        
        # Usage details
        self._quantity: float = 0.0  # Amount of usage
        self._action: str = self.ACTION_INCREMENT  # increment|decrement|set
        self._timestamp_utc_ts: float = 0.0  # When usage occurred
        
        # Metering
        self._meter_event_name: str = ""  # e.g., "api_call", "storage_gb"
        self._unit_name: Optional[str] = None  # e.g., "call", "GB", "hour"
        
        # Billing period
        self._billing_period_start_utc_ts: Optional[float] = None
        self._billing_period_end_utc_ts: Optional[float] = None
        
        # Idempotency
        self._idempotency_key: Optional[str] = None  # Prevent duplicate recording
        
        # Status
        self._is_processed: bool = False  # Whether included in invoice
        self._processed_utc_ts: Optional[float] = None
        self._invoice_id: Optional[str] = None
        
        # Metadata
        self._metadata: Dict[str, Any] = {}  # Custom metadata
        self._source: Optional[str] = None  # Where usage came from
        self._description: Optional[str] = None
        
        # CRITICAL: Call _setup_indexes() as LAST line in __init__
        self._setup_indexes()
    
    def _setup_indexes(self):
        """Setup DynamoDB indexes for usage record queries."""
        
        # Primary index: Usage record by ID
        primary: DynamoDBIndex = DynamoDBIndex()
        primary.name = "primary"
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(("usage", self.id))
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: "metadata"
        self.indexes.add_primary(primary)
        
        # GSI1: Usage by tenant and subscription
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi1"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(("tenant", self.tenant_id), ("subscription", self.subscription_id))
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(("timestamp", self.timestamp_utc_ts))
        self.indexes.add_secondary(gsi)
        
        # GSI2: Usage by addon and period (for aggregation)
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi2"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(("tenant", self.tenant_id), ("addon", self.addon_code))
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(("timestamp", self.timestamp_utc_ts))
        self.indexes.add_secondary(gsi)
    
    # Tenant ID
    @property
    def tenant_id(self) -> str:
        """Tenant ID."""
        return self._tenant_id
    
    @tenant_id.setter
    def tenant_id(self, value: str):
        self._tenant_id = value
    
    # Subscription ID
    @property
    def subscription_id(self) -> str:
        """Subscription ID."""
        return self._subscription_id
    
    @subscription_id.setter
    def subscription_id(self, value: str):
        self._subscription_id = value
    
    # Addon Code
    @property
    def addon_code(self) -> str:
        """Addon code."""
        return self._addon_code
    
    @addon_code.setter
    def addon_code(self, value: str):
        self._addon_code = value
    
    # Quantity
    @property
    def quantity(self) -> float:
        """Usage quantity."""
        return self._quantity
    
    @quantity.setter
    def quantity(self, value: float):
        if value < 0:
            raise ValueError("quantity cannot be negative")
        self._quantity = value
    
    # Action
    @property
    def action(self) -> str:
        """Usage action."""
        return self._action
    
    @action.setter
    def action(self, value: str):
        valid_actions = [self.ACTION_INCREMENT, self.ACTION_DECREMENT, self.ACTION_SET]
        if value not in valid_actions:
            raise ValueError(f"Invalid action: {value}. Must be one of {valid_actions}")
        self._action = value
    
    # Timestamp
    @property
    def timestamp_utc_ts(self) -> float:
        """Timestamp when usage occurred."""
        return self._timestamp_utc_ts
    
    @timestamp_utc_ts.setter
    def timestamp_utc_ts(self, value: float):
        self._timestamp_utc_ts = value
    
    # Meter Event Name
    @property
    def meter_event_name(self) -> str:
        """Meter event name."""
        return self._meter_event_name
    
    @meter_event_name.setter
    def meter_event_name(self, value: str):
        self._meter_event_name = value
    
    # Unit Name
    @property
    def unit_name(self) -> Optional[str]:
        """Unit name."""
        return self._unit_name
    
    @unit_name.setter
    def unit_name(self, value: Optional[str]):
        self._unit_name = value
    
    # Billing Period Start
    @property
    def billing_period_start_utc_ts(self) -> Optional[float]:
        """Billing period start timestamp."""
        return self._billing_period_start_utc_ts
    
    @billing_period_start_utc_ts.setter
    def billing_period_start_utc_ts(self, value: Optional[float]):
        self._billing_period_start_utc_ts = value
    
    # Billing Period End
    @property
    def billing_period_end_utc_ts(self) -> Optional[float]:
        """Billing period end timestamp."""
        return self._billing_period_end_utc_ts
    
    @billing_period_end_utc_ts.setter
    def billing_period_end_utc_ts(self, value: Optional[float]):
        self._billing_period_end_utc_ts = value
    
    # Idempotency Key
    @property
    def idempotency_key(self) -> Optional[str]:
        """Idempotency key."""
        return self._idempotency_key
    
    @idempotency_key.setter
    def idempotency_key(self, value: Optional[str]):
        self._idempotency_key = value
    
    # Is Processed
    @property
    def is_processed(self) -> bool:
        """Whether usage has been processed/billed."""
        return self._is_processed
    
    @is_processed.setter
    def is_processed(self, value: bool):
        self._is_processed = value
    
    # Processed Timestamp
    @property
    def processed_utc_ts(self) -> Optional[float]:
        """When usage was processed."""
        return self._processed_utc_ts
    
    @processed_utc_ts.setter
    def processed_utc_ts(self, value: Optional[float]):
        self._processed_utc_ts = value
    
    # Invoice ID
    @property
    def invoice_id(self) -> Optional[str]:
        """Invoice ID if processed."""
        return self._invoice_id
    
    @invoice_id.setter
    def invoice_id(self, value: Optional[str]):
        self._invoice_id = value
    
    # Metadata
    @property
    def metadata(self) -> Dict[str, Any]:
        """Custom metadata."""
        return self._metadata
    
    @metadata.setter
    def metadata(self, value: Dict[str, Any]):
        self._metadata = value if value else {}
    
    # Source
    @property
    def source(self) -> Optional[str]:
        """Usage source."""
        return self._source
    
    @source.setter
    def source(self, value: Optional[str]):
        self._source = value
    
    # Description
    @property
    def description(self) -> Optional[str]:
        """Usage description."""
        return self._description
    
    @description.setter
    def description(self, value: Optional[str]):
        self._description = value
    
    # Helper Methods
    
    def mark_processed(self, invoice_id: Optional[str] = None):
        """Mark usage record as processed."""
        self._is_processed = True
        self._processed_utc_ts = dt.datetime.now(dt.UTC).timestamp()
        if invoice_id:
            self._invoice_id = invoice_id
    
    def is_increment(self) -> bool:
        """Check if action is increment."""
        return self._action == self.ACTION_INCREMENT
    
    def is_decrement(self) -> bool:
        """Check if action is decrement."""
        return self._action == self.ACTION_DECREMENT
    
    def is_set(self) -> bool:
        """Check if action is set."""
        return self._action == self.ACTION_SET
