"""Host-User Relationship Model (Phase 2)."""


from geek_cafe_saas_sdk.core.models.base_tenant_user_model import BaseTenantUserModel


class HostUserRelationship(BaseTenantUserModel):
    """
    Tracks relationship between a host and a user (attendee).
    
    Inherits from BaseTenantUserModel where:
    - user_id (from base) = the attendee who owns/controls this relationship
    - host_id (this model) = the host trying to connect
    
    Supports:
    - User-controlled connections (invite_only enforcement)
    - Silent blocking (host doesn't know they're blocked)
    - Per-relationship notification preferences
    
    Relationship States:
    - pending: Host requested connection, user hasn't responded
    - connected: User approved connection
    - blocked: User blocked host (silent by default)
    - removed: Connection was removed/revoked
    """
    
    def __init__(self):
        super().__init__()
        
        # Core Relationship
        # user_id (from BaseTenantUserModel) = attendee who owns this relationship
        self._host_id: str = ""           # Host trying to connect to the user
        
        # Relationship State
        self._status: str = "pending"     # pending | connected | blocked | removed
        self._initiated_by: str = ""      # 'host' | 'user'
        self._initiated_at_utc_ts: float = 0.0
        
        # Connection timestamps
        self._connected_at_utc_ts: float | None = None
        self._blocked_at_utc_ts: float | None = None
        self._removed_at_utc_ts: float | None = None
        
        # Silent Blocking
        self._is_silent_block: bool = True  # Default: host doesn't know
        
        # Notification Preferences (per relationship)
        self._notification_preferences: dict = {
            "event_invitations": True,
            "event_updates": True,
            "event_reminders": True
        }
        
        # Metadata
        self._notes: str = ""  # User's private notes about this relationship
        
        self._setup_indexes()
    
    def _setup_indexes(self):
        """Setup DynamoDB indexes for efficient querying."""
        from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey
        
        # Primary: host_id:user_id
        primary = DynamoDBIndex()
        primary.name = "primary"
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(
            ("tenant", self.tenant_id),
            ("host", self.host_id)
        )
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: DynamoDBKey.build_key(("user", self.user_id))
        self.indexes.add_primary(primary)
        
        # GSI1: By user (find all hosts connected to this user)
        gsi1 = DynamoDBIndex()
        gsi1.name = "gsi1"
        gsi1.partition_key.attribute_name = "gsi1_pk"
        gsi1.partition_key.value = lambda: DynamoDBKey.build_key(
            ("tenant", self.tenant_id),
            ("user", self.user_id)
        )
        gsi1.sort_key.attribute_name = "gsi1_sk"
        gsi1.sort_key.value = lambda: DynamoDBKey.build_key(
            ("status", self.status),
            ("host", self.host_id)
        )
        self.indexes.add_secondary(gsi1)
        
        # GSI2: By status (admin queries)
        gsi2 = DynamoDBIndex()
        gsi2.name = "gsi2"
        gsi2.partition_key.attribute_name = "gsi2_pk"
        gsi2.partition_key.value = lambda: DynamoDBKey.build_key(
            ("tenant", self.tenant_id),
            ("status", self.status)
        )
        gsi2.sort_key.attribute_name = "gsi2_sk"
        gsi2.sort_key.value = lambda: DynamoDBKey.build_key(
            ("initiated", self.initiated_at_utc_ts)
        )
        self.indexes.add_secondary(gsi2)
    
    # Properties
    @property
    def id(self) -> str:
        """Composite ID: host_id:user_id."""
        return f"{self._host_id}:{self.user_id}" if self._host_id and self.user_id else ""
    
    @id.setter
    def id(self, value: str):
        """Parse composite ID into host_id and user_id."""
        if value and ":" in value:
            parts = value.split(":", 1)
            self._host_id = parts[0]
            self.user_id = parts[1]
    
    @property
    def host_id(self) -> str:
        """ID of the user acting as host."""
        return self._host_id
    
    @host_id.setter
    def host_id(self, value: str):
        self._host_id = value
    
    # user_id property is inherited from BaseTenantUserModel
    # It represents the attendee (the person who owns/controls this relationship)
    
    @property
    def status(self) -> str:
        """Relationship status: pending | connected | blocked | removed."""
        return self._status
    
    @status.setter
    def status(self, value: str):
        if value not in ["pending", "connected", "blocked", "removed"]:
            raise ValueError(f"Invalid status: {value}. Must be pending, connected, blocked, or removed.")
        self._status = value
    
    @property
    def initiated_by(self) -> str:
        """Who initiated the relationship: 'host' or 'user'."""
        return self._initiated_by
    
    @initiated_by.setter
    def initiated_by(self, value: str):
        if value not in ["host", "user", ""]:
            raise ValueError(f"Invalid initiator: {value}. Must be 'host' or 'user'.")
        self._initiated_by = value
    
    @property
    def initiated_at_utc_ts(self) -> float:
        """Timestamp when relationship was initiated."""
        return self._initiated_at_utc_ts
    
    @initiated_at_utc_ts.setter
    def initiated_at_utc_ts(self, value: float):
        self._initiated_at_utc_ts = value
    
    @property
    def connected_at_utc_ts(self) -> float | None:
        """Timestamp when relationship was connected/approved."""
        return self._connected_at_utc_ts
    
    @connected_at_utc_ts.setter
    def connected_at_utc_ts(self, value: float | None):
        self._connected_at_utc_ts = value
    
    @property
    def blocked_at_utc_ts(self) -> float | None:
        """Timestamp when user blocked the host."""
        return self._blocked_at_utc_ts
    
    @blocked_at_utc_ts.setter
    def blocked_at_utc_ts(self, value: float | None):
        self._blocked_at_utc_ts = value
    
    @property
    def removed_at_utc_ts(self) -> float | None:
        """Timestamp when relationship was removed."""
        return self._removed_at_utc_ts
    
    @removed_at_utc_ts.setter
    def removed_at_utc_ts(self, value: float | None):
        self._removed_at_utc_ts = value
    
    @property
    def is_silent_block(self) -> bool:
        """Whether the block is silent (host doesn't know)."""
        return self._is_silent_block
    
    @is_silent_block.setter
    def is_silent_block(self, value: bool):
        self._is_silent_block = bool(value)
    
    @property
    def notification_preferences(self) -> dict:
        """Per-relationship notification preferences."""
        return self._notification_preferences
    
    @notification_preferences.setter
    def notification_preferences(self, value: dict):
        self._notification_preferences = value
    
    @property
    def notes(self) -> str:
        """User's private notes about this relationship."""
        return self._notes
    
    @notes.setter
    def notes(self, value: str):
        self._notes = value
    
    # Helper Methods
    def is_pending(self) -> bool:
        """Check if relationship is pending approval."""
        return self._status == "pending"
    
    def is_connected(self) -> bool:
        """Check if relationship is active/connected."""
        return self._status == "connected"
    
    def is_blocked(self) -> bool:
        """Check if host is blocked."""
        return self._status == "blocked"
    
    def is_removed(self) -> bool:
        """Check if relationship was removed."""
        return self._status == "removed"
    
    def can_host_invite(self) -> bool:
        """Check if host can invite user based on relationship status."""
        return self._status == "connected"
