"""
Geek Cafe, LLC
MIT License.  See Project Root for the license information.

ChatChannel model for internal team messaging (Slack-like functionality).
"""

from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey
from boto3_assist.utilities.string_utility import StringUtility
import datetime as dt
from typing import List, Optional, Dict, Any
from geek_cafe_saas_sdk.core.models.base_tenant_user_model import BaseTenantUserModel


class ChatChannel(BaseTenantUserModel):
    """
    ChatChannel model for Slack-like team messaging.
    
    Optimized for high-volume, real-time messaging with symmetric membership.
    Messages are stored separately to avoid document size limits.
    
    Features:
    - Public channels (visible to all team members)
    - Private channels (invite-only)
    - Direct messages (1-on-1)
    - Member management
    - Channel settings (announcements-only, auto-join, etc.)
    - Archive/unarchive
    - Activity tracking
    
    Note: Messages are stored in separate ChatMessage documents.
    """

    def __init__(self):
        super().__init__()
        self._name: str | None = None
        self._description: str | None = None
        self._channel_type: str = "public"  # public, private, direct
        
        # Membership tracking (members stored as adjacent records)
        self._member_count: int = 0  # Cached count for display
        self._created_by: str | None = None
        
        # Activity tracking (no embedded messages)
        self._last_message_id: str | None = None
        self._last_message_at: float | None = None
        self._message_count: int = 0
        
        # Channel settings
        self._is_archived: bool = False
        self._is_default: bool = False  # Auto-join for new users
        self._is_announcement: bool = False  # Only admins can post
        
        # Metadata
        self._topic: str | None = None  # Channel topic/purpose
        self._icon: str | None = None  # Emoji or image URL
        
        # Sharding configuration (optional, for high-traffic channels)
        self._sharding_config: Dict[str, Any] | None = None
        
        self._setup_indexes()

    def _setup_indexes(self):
        """Setup DynamoDB indexes for efficient querying."""
        
        # Primary index: channels by ID
        primary: DynamoDBIndex = DynamoDBIndex()
        primary.name = "primary"
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(("channel", self.id))
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: DynamoDBKey.build_key(("channel", self.id))
        self.indexes.add_primary(primary)

        # GSI1: Query by tenant and type (list all public/private channels)
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi1"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(
            ("tenant", self.tenant_id),
            ("type", self.channel_type)
        )
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
            ("ts", self.last_message_at or self.created_utc_ts)
        )
        self.indexes.add_secondary(gsi)

        # GSI2: Query all channels by tenant (for admin views)
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi2"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(
            ("tenant", self.tenant_id)
        )
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
            ("model", "channel"),
            ("name", self.name)
        )
        self.indexes.add_secondary(gsi)

        # GSI3: Query default channels (auto-join for new users)
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi3"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(
            ("tenant", self.tenant_id),
            ("default", "1" if self.is_default else "0")
        )
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
            ("ts", self.created_utc_ts)
        )
        self.indexes.add_secondary(gsi)

        # GSI4: Query archived channels
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi4"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(
            ("tenant", self.tenant_id),
            ("archived", "1" if self.is_archived else "0")
        )
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
            ("ts", self.last_message_at or self.created_utc_ts)
        )
        self.indexes.add_secondary(gsi)

    # Name
    @property
    def name(self) -> str | None:
        return self._name

    @name.setter
    def name(self, value: str | None):
        self._name = value

    # Description
    @property
    def description(self) -> str | None:
        return self._description

    @description.setter
    def description(self, value: str | None):
        self._description = value

    # Channel Type
    @property
    def channel_type(self) -> str:
        return self._channel_type

    @channel_type.setter
    def channel_type(self, value: str | None):
        valid_types = ["public", "private", "direct"]
        if value in valid_types:
            self._channel_type = value
        else:
            self._channel_type = "public"  # default

    # Member Count (cached for display)
    @property
    def member_count(self) -> int:
        return self._member_count

    @member_count.setter
    def member_count(self, value: int | None):
        self._member_count = value if isinstance(value, int) else 0

    # Created By
    @property
    def created_by(self) -> str | None:
        return self._created_by

    @created_by.setter
    def created_by(self, value: str | None):
        self._created_by = value

    # Last Message ID
    @property
    def last_message_id(self) -> str | None:
        return self._last_message_id

    @last_message_id.setter
    def last_message_id(self, value: str | None):
        self._last_message_id = value

    # Last Message At
    @property
    def last_message_at(self) -> float | None:
        return self._last_message_at

    @last_message_at.setter
    def last_message_at(self, value: float | None):
        self._last_message_at = value

    # Message Count
    @property
    def message_count(self) -> int:
        return self._message_count

    @message_count.setter
    def message_count(self, value: int | None):
        self._message_count = value if value is not None else 0

    # Is Archived
    @property
    def is_archived(self) -> bool:
        return self._is_archived

    @is_archived.setter
    def is_archived(self, value: bool | None):
        self._is_archived = value if value is not None else False

    # Is Default
    @property
    def is_default(self) -> bool:
        return self._is_default

    @is_default.setter
    def is_default(self, value: bool | None):
        self._is_default = value if value is not None else False

    # Is Announcement
    @property
    def is_announcement(self) -> bool:
        return self._is_announcement

    @is_announcement.setter
    def is_announcement(self, value: bool | None):
        self._is_announcement = value if value is not None else False

    # Topic
    @property
    def topic(self) -> str | None:
        return self._topic

    @topic.setter
    def topic(self, value: str | None):
        self._topic = value

    # Icon
    @property
    def icon(self) -> str | None:
        return self._icon

    @icon.setter
    def icon(self, value: str | None):
        self._icon = value

    # Sharding Config
    @property
    def sharding_config(self) -> Dict[str, Any] | None:
        """
        Sharding configuration for high-traffic channels.
        
        Example:
        {
            "enabled": True,
            "bucket_span": "day",  # "day" or "hour"
            "shard_count": 4,      # 1, 2, 4, or 8
            "enabled_at": 1729123200.0
        }
        
        Returns:
            Sharding config dict or None if not sharded
        """
        return self._sharding_config

    @sharding_config.setter
    def sharding_config(self, value: Dict[str, Any] | None):
        if value is None:
            self._sharding_config = None
        elif isinstance(value, dict):
            self._sharding_config = value
        else:
            self._sharding_config = None

    # Helper Methods
    
    def increment_member_count(self):
        """Increment the cached member count."""
        self._member_count += 1
    
    def decrement_member_count(self):
        """Decrement the cached member count."""
        if self._member_count > 0:
            self._member_count -= 1

    def increment_message_count(self):
        """Increment the message count for this channel."""
        self._message_count += 1

    def update_last_message(self, message_id: str, timestamp: float):
        """
        Update the last message tracking.
        
        Args:
            message_id: ID of the last message
            timestamp: Timestamp of the message
        """
        self._last_message_id = message_id
        self._last_message_at = timestamp
        self.increment_message_count()
    
    def is_sharded(self) -> bool:
        """
        Check if this channel uses message sharding.
        
        Returns:
            True if sharding is enabled, False otherwise
        """
        return (self._sharding_config is not None 
                and self._sharding_config.get("enabled", False))
    
    def get_bucket_span(self) -> str | None:
        """
        Get the time bucket span for sharded messages.
        
        Returns:
            "day" or "hour" if sharded, None otherwise
        """
        if not self.is_sharded():
            return None
        return self._sharding_config.get("bucket_span", "day")
    
    def get_shard_count(self) -> int:
        """
        Get the number of shards per bucket.
        
        Returns:
            Shard count (1-8) if sharded, 1 otherwise
        """
        if not self.is_sharded():
            return 1
        return self._sharding_config.get("shard_count", 1)
