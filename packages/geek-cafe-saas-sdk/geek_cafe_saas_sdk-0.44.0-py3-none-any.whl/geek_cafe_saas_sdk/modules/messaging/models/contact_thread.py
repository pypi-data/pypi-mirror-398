"""
Geek Cafe, LLC
MIT License.  See Project Root for the license information.

ContactThread model for guest-initiated contact and support tickets.
"""

from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey
import datetime as dt
from typing import List, Optional, Dict, Any
from geek_cafe_saas_sdk.core.models.base_tenant_user_model import BaseTenantUserModel


class ContactThread(BaseTenantUserModel):
    """
    ContactThread model for contact forms, support tickets, and guest communications.
    
    Optimized for low-volume conversations with asymmetric access (guest sender vs staff responders).
    Supports status workflow, assignment, and notification tracking.
    
    Features:
    - Guest-initiated contact (no auth required to create)
    - Staff response and assignment tracking
    - Status workflow (open, in_progress, resolved, closed)
    - Priority levels
    - Email notification support
    - Inbox-based routing (support, sales, billing, etc.)
    - Embedded messages (suitable for ~100 messages max)
    """

    def __init__(self):
        super().__init__()
        self._subject: str | None = None
        self._status: str = "open"  # open, in_progress, resolved, closed
        self._priority: Optional[str] = "medium"  # low, medium, high, urgent
        
        # Sender information (guest or authenticated user)
        self._sender: Dict[str, Any] = {}  # {id, name, email, session_id}
        
        # Assignment and routing
        self._assigned_to: Optional[str] = None  # Staff user ID
        self._inbox_id: str = "support"  # support, sales, billing, etc.
        
        # Messages embedded in thread (suitable for low volume)
        self._messages: List[Dict[str, Any]] = []
        
        # Timestamps for workflow tracking
        self._first_response_at: float | None = None
        self._resolved_at: float | None = None
        self._last_message_at: float | None = None
        
        # Notification tracking
        self._guest_notified: bool = False
        self._notification_email: str | None = None
        
        # Metadata and tagging
        self._tags: List[str] = []
        self._source: str = "web"  # web, mobile, api, email
        self._is_archived: bool = False
        
        self._setup_indexes()
        
        # Mark initialization as complete
        object.__setattr__(self, '_initializing', False)

    def _setup_indexes(self):
        """Setup DynamoDB indexes for efficient querying."""
        
        # Primary index: threads by ID
        primary: DynamoDBIndex = DynamoDBIndex()
        primary.name = "primary"
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(("contact", self.id))
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: DynamoDBKey.build_key(("contact", self.id))
        self.indexes.add_primary(primary)

        # GSI1: Query by inbox and status (most common query)
        # Allows: "Show me all open tickets in support inbox"
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi1"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(
            ("inbox", self.inbox_id),
            ("status", self.status)
        )
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
            ("priority", self.priority),
            ("ts", self.created_utc_ts)
        )
        self.indexes.add_secondary(gsi)

        # GSI2: Query by tenant and status
        # Allows: "Show me all open tickets for this tenant"
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi2"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(
            ("tenant", self.tenant_id),
            ("status", self.status)
        )
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
            ("ts", self.last_message_at or self.created_utc_ts)
        )
        self.indexes.add_secondary(gsi)

        # GSI3: Query by assigned staff member
        # Allows: "Show me all tickets assigned to me"
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi3"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(
            ("assigned", self.assigned_to)
        )
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
            ("status", self.status),
            ("ts", self.last_message_at or self.created_utc_ts)
        )
        self.indexes.add_secondary(gsi)

        # GSI4: All threads by tenant (for admin views)
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi4"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(
            ("tenant", self.tenant_id)
        )
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
            ("model", "contact"),
            ("ts", self.created_utc_ts)
        )
        self.indexes.add_secondary(gsi)

        # GSI5: Query by sender email (find all contacts from same guest)
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi5"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(
            ("sender", self.sender.get("email") if self.sender else None)
        )
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
            ("ts", self.created_utc_ts)
        )
        self.indexes.add_secondary(gsi)

    # Subject
    @property
    def subject(self) -> str | None:
        return self._subject

    @subject.setter
    def subject(self, value: str | None):
        self._subject = value

    # Status
    @property
    def status(self) -> str:
        return self._status

    @status.setter
    def status(self, value: str | None):
        valid_statuses = ["open", "in_progress", "resolved", "closed"]
        if value in valid_statuses:
            self._status = value
            # Auto-set resolved_at when status changes to resolved
            if value == "resolved" and not self._resolved_at:
                self._resolved_at = dt.datetime.now(dt.UTC).timestamp()
        else:
            self._status = "open"  # default

    # Priority
    @property
    def priority(self) -> str:
        return self._priority

    @priority.setter
    def priority(self, value: str | None):
        valid_priorities = ["low", "medium", "high", "urgent", None]
        if value in valid_priorities:
            self._priority = value
        else:
            self._priority = "medium"  # default

    # Sender
    @property
    def sender(self) -> Dict[str, Any]:
        return self._sender

    @sender.setter
    def sender(self, value: Dict[str, Any] | None):
        self._sender = value if value else {}

    # Assigned To
    @property
    def assigned_to(self) -> str | None:
        return self._assigned_to

    @assigned_to.setter
    def assigned_to(self, value: str | None):
        self._assigned_to = value

    # Inbox ID
    @property
    def inbox_id(self) -> str:
        return self._inbox_id

    @inbox_id.setter
    def inbox_id(self, value: str | None):
        self._inbox_id = value if value else "support"

    # Messages
    @property
    def messages(self) -> List[Dict[str, Any]]:
        return self._messages

    @messages.setter
    def messages(self, value: List[Dict[str, Any]] | None):
        if value is None:
            self._messages = []
        elif isinstance(value, list):
            self._messages = value
        else:
            self._messages = []

    # First Response At
    @property
    def first_response_at(self) -> float | None:
        return self._first_response_at

    @first_response_at.setter
    def first_response_at(self, value: float | None):
        self._first_response_at = value

    # Resolved At
    @property
    def resolved_at(self) -> float | None:
        return self._resolved_at

    @resolved_at.setter
    def resolved_at(self, value: float | None):
        self._resolved_at = value

    # Last Message At
    @property
    def last_message_at(self) -> float | None:
        return self._last_message_at

    @last_message_at.setter
    def last_message_at(self, value: float | None):
        self._last_message_at = value

    # Guest Notified
    @property
    def guest_notified(self) -> bool:
        return self._guest_notified

    @guest_notified.setter
    def guest_notified(self, value: bool | None):
        self._guest_notified = value if value is not None else False

    # Notification Email
    @property
    def notification_email(self) -> str | None:
        return self._notification_email

    @notification_email.setter
    def notification_email(self, value: str | None):
        self._notification_email = value

    # Tags
    @property
    def tags(self) -> List[str]:
        return self._tags

    @tags.setter
    def tags(self, value: List[str] | None):
        if value is None:
            self._tags = []
        elif isinstance(value, list):
            self._tags = value
        else:
            self._tags = []

    # Source
    @property
    def source(self) -> str:
        return self._source

    @source.setter
    def source(self, value: str | None):
        self._source = value if value else "web"

    # Is Archived
    @property
    def is_archived(self) -> bool:
        return self._is_archived

    @is_archived.setter
    def is_archived(self, value: bool | None):
        self._is_archived = value if value is not None else False

    # Helper Methods
    
    def add_message(self, message: Dict[str, Any]):
        """
        Add a message to the contact thread.
        
        Args:
            message: Message dict with fields: content, sender_id, sender_name, is_staff_reply, etc.
        """
        if message not in self._messages:
            # Ensure message has timestamp
            if "created_at" not in message:
                message["created_at"] = dt.datetime.now(dt.UTC).timestamp()
            
            self._messages.append(message)
            self._last_message_at = message["created_at"]
            
            # Track first staff response
            if message.get("is_staff_reply") and not self._first_response_at:
                self._first_response_at = message["created_at"]

    def get_message_count(self) -> int:
        """Get total number of messages in thread."""
        return len(self._messages)

    def get_recent_messages(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get recent messages from the thread.
        
        Args:
            limit: Number of messages to return
            
        Returns:
            List of most recent messages, newest first
        """
        sorted_messages = sorted(
            self._messages,
            key=lambda m: m.get("created_at", 0),
            reverse=True
        )
        return sorted_messages[:limit]

    def assign(self, staff_user_id: str):
        """
        Assign this thread to a staff member.
        
        Args:
            staff_user_id: ID of the staff member to assign to
        """
        self.assigned_to = staff_user_id
        # Auto-change status to in_progress if currently open
        if self.status == "open":
            self.status = "in_progress"

    def resolve(self):
        """Mark this thread as resolved."""
        self.status = "resolved"
        self.resolved_at = dt.datetime.now(dt.UTC).timestamp()

    def reopen(self):
        """Reopen a resolved or closed thread."""
        self.status = "open"
        self.resolved_at = None

    def can_user_access(self, user_id: str, user_inboxes: List[str] = None) -> bool:
        """
        Check if a user can access this contact thread.
        
        Args:
            user_id: User ID to check
            user_inboxes: List of inbox IDs the user has access to (e.g., ["support-inbox", "sales-inbox"])
            
        Returns:
            True if user can access, False otherwise
        """
        # Check if user is the sender
        if self.sender and self.sender.get("id") == user_id:
            return True
        
        # Check if user is assigned to this thread
        if self.assigned_to == user_id:
            return True
        
        # Check if user has access to the inbox this thread belongs to
        if user_inboxes and self.inbox_id in user_inboxes:
            return True
        
        return False
