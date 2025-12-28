"""
WebhookSubscription Model - Outbound webhook event subscriptions.

Allows tenants to subscribe to platform events via webhooks for integrations.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from typing import Dict, List, Any
from geek_cafe_saas_sdk.core.models.base_tenant_user_model import BaseTenantUserModel
from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey


class WebhookSubscription(BaseTenantUserModel):
    """
    Webhook subscription for outbound event notifications.
    
    Tenants can subscribe to platform events (payment completed, user created, etc.)
    and receive HTTP POSTs to their endpoint.
    """
    
    # Subscription status
    STATUS_ACTIVE = "active"
    STATUS_PAUSED = "paused"
    STATUS_DISABLED = "disabled"
    
    def __init__(self):
        super().__init__()
        
        # Core fields
        self._subscription_name: str = ""  # Display name
        self._url: str = ""  # Webhook endpoint
        self._status: str = self.STATUS_ACTIVE
        
        # Event subscription
        self._event_types: List[str] = []  # Events to subscribe to
        self._event_filters: Dict[str, Any] = {}  # Optional filters
        
        # Security
        self._secret: str | None = None  # For HMAC signature
        self._api_key: str | None = None  # Optional API key header
        self._custom_headers: Dict[str, str] = {}  # Additional headers
        
        # Configuration
        self._http_method: str = "POST"  # POST, PUT
        self._content_type: str = "application/json"
        self._timeout_seconds: int = 30
        self._retry_enabled: bool = True
        self._max_retries: int = 3
        self._retry_delay_seconds: int = 60
        
        # Statistics
        self._total_deliveries: int = 0
        self._successful_deliveries: int = 0
        self._failed_deliveries: int = 0
        self._last_delivery_utc_ts: float | None = None
        self._last_success_utc_ts: float | None = None
        self._last_failure_utc_ts: float | None = None
        self._last_error: str | None = None
        
        # Metadata
        self._description: str | None = None
        self._metadata: Dict[str, Any] = {}
        
        # Setup indexes
        self._setup_indexes()
        
        # Mark initialization as complete
        object.__setattr__(self, '_initializing', False)
    
    def _setup_indexes(self):
        """Setup DynamoDB indexes for webhook subscription queries."""
        
        # Primary index: Webhook subscription by ID
        primary: DynamoDBIndex = DynamoDBIndex()
        primary.name = "primary"
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(("webhook", self.id))
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: "metadata"
        self.indexes.add_primary(primary)
        
        # GSI1: Webhooks by tenant (for listing)
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi1"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(("tenant", self.tenant_id))
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(("webhook", self.created_utc_ts))
        self.indexes.add_secondary(gsi)
    
    # Properties
    # Note: tenant_id and user_id inherited from BaseTenantUserModel
    
    @property
    def subscription_name(self) -> str:
        return self._subscription_name
    
    @subscription_name.setter
    def subscription_name(self, value: str):
        self._subscription_name = value
    
    @property
    def url(self) -> str:
        return self._url
    
    @url.setter
    def url(self, value: str):
        self._url = value
    
    @property
    def status(self) -> str:
        return self._status
    
    @status.setter
    def status(self, value: str):
        self._status = value
    
    @property
    def event_types(self) -> List[str]:
        return self._event_types
    
    @event_types.setter
    def event_types(self, value: List[str]):
        self._event_types = value if value else []
    
    @property
    def event_filters(self) -> Dict[str, Any]:
        return self._event_filters
    
    @event_filters.setter
    def event_filters(self, value: Dict[str, Any]):
        self._event_filters = value if value else {}
    
    @property
    def secret(self) -> str | None:
        return self._secret
    
    @secret.setter
    def secret(self, value: str | None):
        self._secret = value
    
    @property
    def api_key(self) -> str | None:
        return self._api_key
    
    @api_key.setter
    def api_key(self, value: str | None):
        self._api_key = value
    
    @property
    def custom_headers(self) -> Dict[str, str]:
        return self._custom_headers
    
    @custom_headers.setter
    def custom_headers(self, value: Dict[str, str]):
        self._custom_headers = value if value else {}
    
    @property
    def http_method(self) -> str:
        return self._http_method
    
    @http_method.setter
    def http_method(self, value: str):
        self._http_method = value
    
    @property
    def content_type(self) -> str:
        return self._content_type
    
    @content_type.setter
    def content_type(self, value: str):
        self._content_type = value
    
    @property
    def timeout_seconds(self) -> int:
        return self._timeout_seconds
    
    @timeout_seconds.setter
    def timeout_seconds(self, value: int):
        self._timeout_seconds = value
    
    @property
    def retry_enabled(self) -> bool:
        return self._retry_enabled
    
    @retry_enabled.setter
    def retry_enabled(self, value: bool):
        self._retry_enabled = value
    
    @property
    def max_retries(self) -> int:
        return self._max_retries
    
    @max_retries.setter
    def max_retries(self, value: int):
        self._max_retries = value
    
    @property
    def retry_delay_seconds(self) -> int:
        return self._retry_delay_seconds
    
    @retry_delay_seconds.setter
    def retry_delay_seconds(self, value: int):
        self._retry_delay_seconds = value
    
    @property
    def total_deliveries(self) -> int:
        return self._total_deliveries
    
    @total_deliveries.setter
    def total_deliveries(self, value: int):
        self._total_deliveries = value
    
    @property
    def successful_deliveries(self) -> int:
        return self._successful_deliveries
    
    @successful_deliveries.setter
    def successful_deliveries(self, value: int):
        self._successful_deliveries = value
    
    @property
    def failed_deliveries(self) -> int:
        return self._failed_deliveries
    
    @failed_deliveries.setter
    def failed_deliveries(self, value: int):
        self._failed_deliveries = value
    
    @property
    def last_delivery_utc_ts(self) -> float | None:
        return self._last_delivery_utc_ts
    
    @last_delivery_utc_ts.setter
    def last_delivery_utc_ts(self, value: float | None):
        self._last_delivery_utc_ts = value
    
    @property
    def last_success_utc_ts(self) -> float | None:
        return self._last_success_utc_ts
    
    @last_success_utc_ts.setter
    def last_success_utc_ts(self, value: float | None):
        self._last_success_utc_ts = value
    
    @property
    def last_failure_utc_ts(self) -> float | None:
        return self._last_failure_utc_ts
    
    @last_failure_utc_ts.setter
    def last_failure_utc_ts(self, value: float | None):
        self._last_failure_utc_ts = value
    
    @property
    def last_error(self) -> str | None:
        return self._last_error
    
    @last_error.setter
    def last_error(self, value: str | None):
        self._last_error = value
    
    @property
    def description(self) -> str | None:
        return self._description
    
    @description.setter
    def description(self, value: str | None):
        self._description = value
    
    @property
    def metadata(self) -> Dict[str, Any]:
        return self._metadata
    
    @metadata.setter
    def metadata(self, value: Dict[str, Any]):
        self._metadata = value if value else {}
    
    # Helper Methods
    def is_active(self) -> bool:
        """Check if subscription is active."""
        return self._status == self.STATUS_ACTIVE
    
    def subscribes_to(self, event_type: str) -> bool:
        """Check if subscription includes event type."""
        return event_type in self._event_types or "*" in self._event_types
    
    def record_success(self, timestamp: float):
        """Record successful delivery."""
        self._total_deliveries += 1
        self._successful_deliveries += 1
        self._last_delivery_utc_ts = timestamp
        self._last_success_utc_ts = timestamp
        self._last_error = None
    
    def record_failure(self, timestamp: float, error: str):
        """Record failed delivery."""
        self._total_deliveries += 1
        self._failed_deliveries += 1
        self._last_delivery_utc_ts = timestamp
        self._last_failure_utc_ts = timestamp
        self._last_error = error
    
    def get_success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self._total_deliveries == 0:
            return 0.0
        return (self._successful_deliveries / self._total_deliveries) * 100
    
    def validate(self) -> tuple[bool, list[str]]:
        """Validate subscription data."""
        errors = []
        
        # Note: tenant_id is now inherited from BaseTenantUserModel (use property, not _tenant_id)
        if not self.tenant_id:
            errors.append("tenant_id is required")
        
        # Note: user_id is also inherited from BaseTenantUserModel
        if not self.user_id:
            errors.append("user_id is required")
        
        if not self._subscription_name:
            errors.append("subscription_name is required")
        
        if not self._url:
            errors.append("url is required")
        elif not self._url.startswith(("http://", "https://")):
            errors.append("url must start with http:// or https://")
        
        if not self._event_types:
            errors.append("event_types cannot be empty")
        
        if self._http_method not in ["POST", "PUT", "PATCH"]:
            errors.append("http_method must be POST, PUT, or PATCH")
        
        if self._timeout_seconds < 1 or self._timeout_seconds > 300:
            errors.append("timeout_seconds must be between 1 and 300")
        
        return (len(errors) == 0, errors)
