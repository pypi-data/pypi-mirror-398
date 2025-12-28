"""
Notification Model - Multi-channel notification delivery system.

Supports email, SMS, in-app, push notifications with state tracking,
priority management, and retry logic.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from typing import Dict, List, Any
from geek_cafe_saas_sdk.core.models.base_tenant_user_model import BaseTenantUserModel
from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey


class Notification(BaseTenantUserModel):
    """
    Notification model for multi-channel message delivery.
    
    Handles state management (queued→sending→sent→delivered→failed),
    retry logic, priority, and channel-specific configuration.
    
    Channels supported:
    - email: Via SES, SendGrid, etc.
    - sms: Via Twilio, SNS, etc.
    - in_app: Browser/mobile app notifications
    - push: Mobile push notifications (FCM, APNS)
    
    States:
    - queued: Created, waiting to send
    - sending: Currently being sent
    - sent: Successfully sent to provider
    - delivered: Confirmed delivery (when available)
    - failed: Delivery failed
    - cancelled: Cancelled before sending
    """
    
    # Channel types
    CHANNEL_EMAIL = "email"
    CHANNEL_SMS = "sms"
    CHANNEL_IN_APP = "in_app"
    CHANNEL_PUSH = "push"
    CHANNEL_WEBHOOK = "webhook"
    
    # States
    STATE_QUEUED = "queued"
    STATE_SENDING = "sending"
    STATE_SENT = "sent"
    STATE_DELIVERED = "delivered"
    STATE_FAILED = "failed"
    STATE_CANCELLED = "cancelled"
    
    # Priority levels
    PRIORITY_LOW = "low"
    PRIORITY_NORMAL = "normal"
    PRIORITY_HIGH = "high"
    PRIORITY_URGENT = "urgent"
    
    def __init__(self):
        super().__init__()
        
        # Core fields
        self._notification_type: str = ""  # "welcome_email", "payment_receipt", "alert", etc.
        self._channel: str = self.CHANNEL_EMAIL  # Delivery channel
        self._state: str = self.STATE_QUEUED  # Current state
        self._priority: str = self.PRIORITY_NORMAL
        
        # Recipient
        self._recipient_id: str | None = None  # User ID receiving notification
        self._recipient_email: str | None = None
        self._recipient_phone: str | None = None
        self._recipient_device_token: str | None = None  # For push
        self._recipient_name: str | None = None
        
        # Content
        self._subject: str | None = None  # For email
        self._title: str | None = None  # For push/in-app
        self._body: str = ""  # Main content
        self._body_html: str | None = None  # HTML version for email
        self._template_id: str | None = None  # Template reference
        self._template_data: Dict[str, Any] = {}  # Template variables
        
        # Delivery configuration
        self._send_after_utc_ts: float | None = None  # Scheduled delivery
        self._expires_utc_ts: float | None = None  # Don't send after this time
        self._max_retries: int = 3
        self._retry_count: int = 0
        self._retry_delay_seconds: int = 300  # 5 minutes
        
        # Channel-specific config
        self._email_config: Dict[str, Any] = {}  # reply-to, cc, bcc, attachments
        self._sms_config: Dict[str, Any] = {}  # sender_id, message_type
        self._push_config: Dict[str, Any] = {}  # badge, sound, data
        self._webhook_config: Dict[str, Any] = {}  # url, method, headers
        
        # State tracking
        self._queued_utc_ts: float | None = None
        self._sent_utc_ts: float | None = None
        self._delivered_utc_ts: float | None = None
        self._failed_utc_ts: float | None = None
        self._read_utc_ts: float | None = None  # For in-app
        
        # Provider tracking
        self._provider: str | None = None  # "ses", "twilio", "fcm", etc.
        self._provider_message_id: str | None = None  # External ID
        self._provider_response: Dict[str, Any] = {}
        
        # Error tracking
        self._error_code: str | None = None
        self._error_message: str | None = None
        self._error_details: Dict[str, Any] = {}
        
        # Metadata
        self._triggered_by_event: str | None = None  # Event that triggered this
        self._related_resource_type: str | None = None  # "payment", "subscription", etc.
        self._related_resource_id: str | None = None
        self._campaign_id: str | None = None  # Marketing campaign tracking
        self._tags: List[str] = []
        self._metadata: Dict[str, Any] = {}
        
        # Setup indexes
        self._setup_indexes()
        
        # Mark initialization as complete
        object.__setattr__(self, '_initializing', False)
    
    def _setup_indexes(self):
        """Setup DynamoDB indexes for notification queries."""
        
        # Primary index: Notification by ID
        primary: DynamoDBIndex = DynamoDBIndex()
        primary.name = "primary"
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(("notification", self.id))
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: "metadata"
        self.indexes.add_primary(primary)
        
        # GSI1: Notifications by recipient (for user's notification list)
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi1"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(("recipient", self.recipient_id))
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(("queued", self.queued_utc_ts))
        self.indexes.add_secondary(gsi)
        
        # GSI2: Notifications by tenant and state (for processing queue)
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi2"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(("tenant", self.tenant_id))
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(("state", self.state), ("queued", self.queued_utc_ts))
        self.indexes.add_secondary(gsi)
    
    # ========================================================================
    # Core Properties
    # ========================================================================
    
    @property
    def notification_type(self) -> str:
        """Notification type identifier."""
        return self._notification_type
    
    @notification_type.setter
    def notification_type(self, value: str):
        self._notification_type = value
    
    @property
    def channel(self) -> str:
        """Delivery channel (email, sms, in_app, push, webhook)."""
        return self._channel
    
    @channel.setter
    def channel(self, value: str):
        self._channel = value
    
    @property
    def state(self) -> str:
        """Current state."""
        return self._state
    
    @state.setter
    def state(self, value: str):
        self._state = value
    
    @property
    def priority(self) -> str:
        """Priority level."""
        return self._priority
    
    @priority.setter
    def priority(self, value: str):
        self._priority = value
    
    # ========================================================================
    # Recipient Properties
    # ========================================================================
    
    @property
    def recipient_id(self) -> str | None:
        """User ID."""
        return self._recipient_id
    
    @recipient_id.setter
    def recipient_id(self, value: str | None):
        self._recipient_id = value
    
    @property
    def recipient_email(self) -> str | None:
        """Email address."""
        return self._recipient_email
    
    @recipient_email.setter
    def recipient_email(self, value: str | None):
        self._recipient_email = value
    
    @property
    def recipient_phone(self) -> str | None:
        """Phone number."""
        return self._recipient_phone
    
    @recipient_phone.setter
    def recipient_phone(self, value: str | None):
        self._recipient_phone = value
    
    @property
    def recipient_device_token(self) -> str | None:
        """Push notification device token."""
        return self._recipient_device_token
    
    @recipient_device_token.setter
    def recipient_device_token(self, value: str | None):
        self._recipient_device_token = value
    
    @property
    def recipient_name(self) -> str | None:
        """Recipient display name."""
        return self._recipient_name
    
    @recipient_name.setter
    def recipient_name(self, value: str | None):
        self._recipient_name = value
    
    # ========================================================================
    # Content Properties
    # ========================================================================
    
    @property
    def subject(self) -> str | None:
        """Email subject line."""
        return self._subject
    
    @subject.setter
    def subject(self, value: str | None):
        self._subject = value
    
    @property
    def title(self) -> str | None:
        """Push/in-app notification title."""
        return self._title
    
    @title.setter
    def title(self, value: str | None):
        self._title = value
    
    @property
    def body(self) -> str:
        """Main content body."""
        return self._body
    
    @body.setter
    def body(self, value: str):
        self._body = value
    
    @property
    def body_html(self) -> str | None:
        """HTML body for email."""
        return self._body_html
    
    @body_html.setter
    def body_html(self, value: str | None):
        self._body_html = value
    
    @property
    def template_id(self) -> str | None:
        """Template identifier."""
        return self._template_id
    
    @template_id.setter
    def template_id(self, value: str | None):
        self._template_id = value
    
    @property
    def template_data(self) -> Dict[str, Any]:
        """Template variables."""
        return self._template_data
    
    @template_data.setter
    def template_data(self, value: Dict[str, Any]):
        self._template_data = value if value else {}
    
    # ========================================================================
    # Delivery Configuration Properties
    # ========================================================================
    
    @property
    def send_after_utc_ts(self) -> float | None:
        """Scheduled send time."""
        return self._send_after_utc_ts
    
    @send_after_utc_ts.setter
    def send_after_utc_ts(self, value: float | None):
        self._send_after_utc_ts = value
    
    @property
    def expires_utc_ts(self) -> float | None:
        """Expiration time."""
        return self._expires_utc_ts
    
    @expires_utc_ts.setter
    def expires_utc_ts(self, value: float | None):
        self._expires_utc_ts = value
    
    @property
    def max_retries(self) -> int:
        """Maximum retry attempts."""
        return self._max_retries
    
    @max_retries.setter
    def max_retries(self, value: int):
        self._max_retries = value
    
    @property
    def retry_count(self) -> int:
        """Current retry count."""
        return self._retry_count
    
    @retry_count.setter
    def retry_count(self, value: int):
        self._retry_count = value
    
    @property
    def retry_delay_seconds(self) -> int:
        """Retry delay in seconds."""
        return self._retry_delay_seconds
    
    @retry_delay_seconds.setter
    def retry_delay_seconds(self, value: int):
        self._retry_delay_seconds = value
    
    # ========================================================================
    # Channel Config Properties
    # ========================================================================
    
    @property
    def email_config(self) -> Dict[str, Any]:
        """Email-specific configuration."""
        return self._email_config
    
    @email_config.setter
    def email_config(self, value: Dict[str, Any]):
        self._email_config = value if value else {}
    
    @property
    def sms_config(self) -> Dict[str, Any]:
        """SMS-specific configuration."""
        return self._sms_config
    
    @sms_config.setter
    def sms_config(self, value: Dict[str, Any]):
        self._sms_config = value if value else {}
    
    @property
    def push_config(self) -> Dict[str, Any]:
        """Push notification configuration."""
        return self._push_config
    
    @push_config.setter
    def push_config(self, value: Dict[str, Any]):
        self._push_config = value if value else {}
    
    @property
    def webhook_config(self) -> Dict[str, Any]:
        """Webhook configuration."""
        return self._webhook_config
    
    @webhook_config.setter
    def webhook_config(self, value: Dict[str, Any]):
        self._webhook_config = value if value else {}
    
    # ========================================================================
    # Timestamps
    # ========================================================================
    
    @property
    def queued_utc_ts(self) -> float | None:
        """When notification was queued."""
        return self._queued_utc_ts
    
    @queued_utc_ts.setter
    def queued_utc_ts(self, value: float | None):
        self._queued_utc_ts = value
    
    @property
    def sent_utc_ts(self) -> float | None:
        """When notification was sent."""
        return self._sent_utc_ts
    
    @sent_utc_ts.setter
    def sent_utc_ts(self, value: float | None):
        self._sent_utc_ts = value
    
    @property
    def delivered_utc_ts(self) -> float | None:
        """When notification was delivered."""
        return self._delivered_utc_ts
    
    @delivered_utc_ts.setter
    def delivered_utc_ts(self, value: float | None):
        self._delivered_utc_ts = value
    
    @property
    def failed_utc_ts(self) -> float | None:
        """When notification failed."""
        return self._failed_utc_ts
    
    @failed_utc_ts.setter
    def failed_utc_ts(self, value: float | None):
        self._failed_utc_ts = value
    
    @property
    def read_utc_ts(self) -> float | None:
        """When notification was read (in-app)."""
        return self._read_utc_ts
    
    @read_utc_ts.setter
    def read_utc_ts(self, value: float | None):
        self._read_utc_ts = value
    
    # ========================================================================
    # Provider Tracking
    # ========================================================================
    
    @property
    def provider(self) -> str | None:
        """Provider name."""
        return self._provider
    
    @provider.setter
    def provider(self, value: str | None):
        self._provider = value
    
    @property
    def provider_message_id(self) -> str | None:
        """Provider's message ID."""
        return self._provider_message_id
    
    @provider_message_id.setter
    def provider_message_id(self, value: str | None):
        self._provider_message_id = value
    
    @property
    def provider_response(self) -> Dict[str, Any]:
        """Provider's response data."""
        return self._provider_response
    
    @provider_response.setter
    def provider_response(self, value: Dict[str, Any]):
        self._provider_response = value if value else {}
    
    # ========================================================================
    # Error Tracking
    # ========================================================================
    
    @property
    def error_code(self) -> str | None:
        """Error code."""
        return self._error_code
    
    @error_code.setter
    def error_code(self, value: str | None):
        self._error_code = value
    
    @property
    def error_message(self) -> str | None:
        """Error message."""
        return self._error_message
    
    @error_message.setter
    def error_message(self, value: str | None):
        self._error_message = value
    
    @property
    def error_details(self) -> Dict[str, Any]:
        """Error details."""
        return self._error_details
    
    @error_details.setter
    def error_details(self, value: Dict[str, Any]):
        self._error_details = value if value else {}
    
    # ========================================================================
    # Metadata
    # ========================================================================
    
    @property
    def triggered_by_event(self) -> str | None:
        """Event that triggered this notification."""
        return self._triggered_by_event
    
    @triggered_by_event.setter
    def triggered_by_event(self, value: str | None):
        self._triggered_by_event = value
    
    @property
    def related_resource_type(self) -> str | None:
        """Related resource type."""
        return self._related_resource_type
    
    @related_resource_type.setter
    def related_resource_type(self, value: str | None):
        self._related_resource_type = value
    
    @property
    def related_resource_id(self) -> str | None:
        """Related resource ID."""
        return self._related_resource_id
    
    @related_resource_id.setter
    def related_resource_id(self, value: str | None):
        self._related_resource_id = value
    
    @property
    def campaign_id(self) -> str | None:
        """Campaign identifier."""
        return self._campaign_id
    
    @campaign_id.setter
    def campaign_id(self, value: str | None):
        self._campaign_id = value
    
    @property
    def tags(self) -> List[str]:
        """Tags for organization."""
        return self._tags
    
    @tags.setter
    def tags(self, value: List[str]):
        self._tags = value if value else []
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """Additional metadata."""
        return self._metadata
    
    @metadata.setter
    def metadata(self, value: Dict[str, Any]):
        self._metadata = value if value else {}
    
    # ========================================================================
    # Helper Methods
    # ========================================================================
    
    def is_queued(self) -> bool:
        """Check if notification is queued."""
        return self._state == self.STATE_QUEUED
    
    def is_sent(self) -> bool:
        """Check if notification was sent."""
        return self._state in [self.STATE_SENT, self.STATE_DELIVERED]
    
    def is_delivered(self) -> bool:
        """Check if notification was delivered."""
        return self._state == self.STATE_DELIVERED
    
    def is_failed(self) -> bool:
        """Check if notification failed."""
        return self._state == self.STATE_FAILED
    
    def is_cancelled(self) -> bool:
        """Check if notification was cancelled."""
        return self._state == self.STATE_CANCELLED
    
    def can_retry(self) -> bool:
        """Check if notification can be retried."""
        return (
            self._state == self.STATE_FAILED and
            self._retry_count < self._max_retries
        )
    
    def is_expired(self, current_ts: float) -> bool:
        """Check if notification has expired."""
        if not self._expires_utc_ts:
            return False
        return current_ts > self._expires_utc_ts
    
    def should_send_now(self, current_ts: float) -> bool:
        """Check if notification should be sent now."""
        if self._send_after_utc_ts:
            return current_ts >= self._send_after_utc_ts
        return True
    
    def mark_sent(self, timestamp: float, provider_id: str | None = None):
        """Mark notification as sent."""
        self._state = self.STATE_SENT
        self._sent_utc_ts = timestamp
        if provider_id:
            self._provider_message_id = provider_id
    
    def mark_delivered(self, timestamp: float):
        """Mark notification as delivered."""
        self._state = self.STATE_DELIVERED
        self._delivered_utc_ts = timestamp
    
    def mark_failed(self, timestamp: float, error_code: str, error_message: str):
        """Mark notification as failed."""
        self._state = self.STATE_FAILED
        self._failed_utc_ts = timestamp
        self._error_code = error_code
        self._error_message = error_message
        self._retry_count += 1
    
    def mark_read(self, timestamp: float):
        """Mark notification as read (for in-app)."""
        self._read_utc_ts = timestamp
    
    def cancel(self):
        """Cancel the notification."""
        if self._state == self.STATE_QUEUED:
            self._state = self.STATE_CANCELLED
    
    def get_recipient_address(self) -> str | None:
        """Get the appropriate recipient address based on channel."""
        if self._channel == self.CHANNEL_EMAIL:
            return self._recipient_email
        elif self._channel == self.CHANNEL_SMS:
            return self._recipient_phone
        elif self._channel == self.CHANNEL_PUSH:
            return self._recipient_device_token
        elif self._channel == self.CHANNEL_IN_APP:
            return self._recipient_id
        return None
    
    # ========================================================================
    # Validation
    # ========================================================================
    
    def validate(self) -> tuple[bool, list[str]]:
        """
        Validate notification data.
        
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []
        
        # Required fields
        if not self._notification_type:
            errors.append("notification_type is required")
        
        if not self._channel:
            errors.append("channel is required")
        
        if self._channel not in [
            self.CHANNEL_EMAIL,
            self.CHANNEL_SMS,
            self.CHANNEL_IN_APP,
            self.CHANNEL_PUSH,
            self.CHANNEL_WEBHOOK
        ]:
            errors.append(f"Invalid channel: {self._channel}")
        
        # Channel-specific validation
        if self._channel == self.CHANNEL_EMAIL:
            if not self._recipient_email:
                errors.append("recipient_email is required for email channel")
            if not self._subject and not self._template_id:
                errors.append("subject or template_id is required for email")
        
        elif self._channel == self.CHANNEL_SMS:
            if not self._recipient_phone:
                errors.append("recipient_phone is required for SMS channel")
        
        elif self._channel == self.CHANNEL_PUSH:
            if not self._recipient_device_token:
                errors.append("recipient_device_token is required for push channel")
            if not self._title and not self._template_id:
                errors.append("title or template_id is required for push")
        
        elif self._channel == self.CHANNEL_IN_APP:
            if not self._recipient_id:
                errors.append("recipient_id is required for in-app channel")
        
        elif self._channel == self.CHANNEL_WEBHOOK:
            if not self._webhook_config.get("url"):
                errors.append("webhook_config.url is required for webhook channel")
        
        # Content validation
        if not self._body and not self._template_id:
            errors.append("body or template_id is required")
        
        # Priority validation
        if self._priority not in [
            self.PRIORITY_LOW,
            self.PRIORITY_NORMAL,
            self.PRIORITY_HIGH,
            self.PRIORITY_URGENT
        ]:
            errors.append(f"Invalid priority: {self._priority}")
        
        # Retry validation
        if self._max_retries < 0:
            errors.append("max_retries must be >= 0")
        
        if self._retry_delay_seconds < 0:
            errors.append("retry_delay_seconds must be >= 0")
        
        return (len(errors) == 0, errors)
