"""
Geek Cafe, LLC
MIT License.  See Project Root for the license information.

ChatMessage model for individual messages in chat channels.
"""

from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey
import datetime as dt
from typing import List, Dict, Any
from geek_cafe_saas_sdk.core.models.base_tenant_user_model import BaseTenantUserModel


class ChatMessage(BaseTenantUserModel):
    """
    ChatMessage model for individual messages in chat channels.
    
    Stored separately from ChatChannel to avoid document size limits and enable:
    - Efficient pagination
    - Concurrent message posting
    - Message-level operations (edit, delete, react)
    - Threaded replies
    
    Features:
    - Message content with rich text support
    - Sender information
    - Threading support (parent message ID)
    - Reactions (emoji reactions)
    - Mentions (@user)
    - Attachments
    - Edit history
    - Read receipts (via separate model)
    """

    def __init__(self):
        super().__init__()
        self._channel_id: str | None = None
        self._content: str | None = None
        
        # Sender information
        self._sender_id: str | None = None
        self._sender_name: str | None = None
        
        # Threading support
        self._parent_message_id: str | None = None  # For threaded replies
        self._thread_count: int = 0  # Number of replies to this message
        
        # Reactions {emoji: [user_ids]}
        self._reactions: Dict[str, List[str]] = {}
        
        # Rich content
        self._attachments: List[Dict[str, Any]] = []  # URLs, images, files
        self._mentions: List[str] = []  # User IDs mentioned
        
        # Edit tracking
        self._edited_at: float | None = None
        self._edit_count: int = 0
        
        # Message type
        self._message_type: str = "message"  # message, system, announcement
        
        # Sharding configuration (runtime attribute, passed from channel)
        # Not persisted separately - computed from channel config at write time
        self._sharding_config: Dict[str, Any] | None = None
        
        self._setup_indexes()

    def _setup_indexes(self):
        """Setup DynamoDB indexes for efficient querying."""
        
        # Primary index: messages by ID
        primary: DynamoDBIndex = DynamoDBIndex()
        primary.name = "primary"
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(("msg", self.id))
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: DynamoDBKey.build_key(("msg", self.id))
        self.indexes.add_primary(primary)

        # GSI1: Query messages by channel (most common - pagination)
        # Allows: "Show me messages in this channel, paginated by time"
        # Supports optional sharding for high-traffic channels
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi1"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = self._compute_gsi1_pk  # Computed with optional sharding
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
            ("ts", self.created_utc_ts)
        )
        self.indexes.add_secondary(gsi)

        # GSI2: Query threaded replies by parent message
        # Allows: "Show me all replies to this message"
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi2"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(
            ("parent", self.parent_message_id)
        )
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
            ("ts", self.created_utc_ts)
        )
        self.indexes.add_secondary(gsi)

        # GSI3: Query messages by sender (user's message history)
        # Allows: "Show me all messages from this user"
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi3"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(
            ("sender", self.sender_id)
        )
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
            ("ts", self.created_utc_ts)
        )
        self.indexes.add_secondary(gsi)

        # GSI4: Query messages by tenant (for admin/analytics)
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi4"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(
            ("tenant", self.tenant_id)
        )
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
            ("model", "message"),
            ("ts", self.created_utc_ts)
        )
        self.indexes.add_secondary(gsi)

    # Channel ID
    @property
    def channel_id(self) -> str | None:
        return self._channel_id

    @channel_id.setter
    def channel_id(self, value: str | None):
        self._channel_id = value

    # Content
    @property
    def content(self) -> str | None:
        return self._content

    @content.setter
    def content(self, value: str | None):
        self._content = value

    # Sender ID
    @property
    def sender_id(self) -> str | None:
        return self._sender_id

    @sender_id.setter
    def sender_id(self, value: str | None):
        self._sender_id = value

    # Sender Name
    @property
    def sender_name(self) -> str | None:
        return self._sender_name

    @sender_name.setter
    def sender_name(self, value: str | None):
        self._sender_name = value

    # Parent Message ID
    @property
    def parent_message_id(self) -> str | None:
        return self._parent_message_id

    @parent_message_id.setter
    def parent_message_id(self, value: str | None):
        self._parent_message_id = value

    # Thread Count
    @property
    def thread_count(self) -> int:
        return self._thread_count

    @thread_count.setter
    def thread_count(self, value: int | None):
        self._thread_count = value if value is not None else 0

    # Reactions
    @property
    def reactions(self) -> Dict[str, List[str]]:
        return self._reactions

    @reactions.setter
    def reactions(self, value: Dict[str, List[str]] | None):
        if value is None:
            self._reactions = {}
        elif isinstance(value, dict):
            self._reactions = value
        else:
            self._reactions = {}

    # Attachments
    @property
    def attachments(self) -> List[Dict[str, Any]]:
        return self._attachments

    @attachments.setter
    def attachments(self, value: List[Dict[str, Any]] | None):
        if value is None:
            self._attachments = []
        elif isinstance(value, list):
            self._attachments = value
        else:
            self._attachments = []

    # Mentions
    @property
    def mentions(self) -> List[str]:
        return self._mentions

    @mentions.setter
    def mentions(self, value: List[str] | None):
        if value is None:
            self._mentions = []
        elif isinstance(value, list):
            self._mentions = value
        else:
            self._mentions = []

    # Edited At
    @property
    def edited_at(self) -> float | None:
        return self._edited_at

    @edited_at.setter
    def edited_at(self, value: float | None):
        self._edited_at = value

    # Edit Count
    @property
    def edit_count(self) -> int:
        return self._edit_count

    @edit_count.setter
    def edit_count(self, value: int | None):
        self._edit_count = value if value is not None else 0

    # Message Type
    @property
    def message_type(self) -> str:
        return self._message_type

    @message_type.setter
    def message_type(self, value: str | None):
        valid_types = ["message", "system", "announcement"]
        if value in valid_types:
            self._message_type = value
        else:
            self._message_type = "message"  # default

    # Helper Methods
    
    def add_reaction(self, emoji: str, user_id: str):
        """
        Add a reaction to this message.
        
        Args:
            emoji: Emoji to add (e.g., "👍", "❤️")
            user_id: User ID adding the reaction
        """
        if emoji not in self._reactions:
            self._reactions[emoji] = []
        
        if user_id not in self._reactions[emoji]:
            self._reactions[emoji].append(user_id)

    def remove_reaction(self, emoji: str, user_id: str):
        """
        Remove a reaction from this message.
        
        Args:
            emoji: Emoji to remove
            user_id: User ID removing the reaction
        """
        if emoji in self._reactions and user_id in self._reactions[emoji]:
            self._reactions[emoji].remove(user_id)
            
            # Clean up empty emoji lists
            if not self._reactions[emoji]:
                del self._reactions[emoji]

    def get_reaction_count(self, emoji: str) -> int:
        """
        Get the count of reactions for a specific emoji.
        
        Args:
            emoji: Emoji to count
            
        Returns:
            Number of users who reacted with this emoji
        """
        return len(self._reactions.get(emoji, []))

    def has_user_reacted(self, emoji: str, user_id: str) -> bool:
        """
        Check if a user has reacted with a specific emoji.
        
        Args:
            emoji: Emoji to check
            user_id: User ID to check
            
        Returns:
            True if user has reacted, False otherwise
        """
        return user_id in self._reactions.get(emoji, [])

    def add_mention(self, user_id: str):
        """
        Add a user mention to this message.
        
        Args:
            user_id: User ID to mention
        """
        if user_id not in self._mentions:
            self._mentions.append(user_id)

    def is_thread_parent(self) -> bool:
        """
        Check if this message is a parent of a thread.
        
        Returns:
            True if this message has replies, False otherwise
        """
        return self._thread_count > 0

    def is_thread_reply(self) -> bool:
        """
        Check if this message is a reply in a thread.
        
        Returns:
            True if this is a reply, False otherwise
        """
        return self._parent_message_id is not None

    def mark_as_edited(self):
        """Mark this message as edited."""
        self._edited_at = dt.datetime.now(dt.UTC).timestamp()
        self._edit_count += 1

    def increment_thread_count(self):
        """Increment the thread reply count."""
        self._thread_count += 1
    
    # Sharding Helper Methods
    
    def _compute_gsi1_pk(self) -> str:
        """
        Compute GSI1 partition key with optional bucketing/sharding.
        
        Strategy:
        - Normal channel: "channel#<id>"
        - Sharded channel: "channel#<id>#bucket#<yyyyMMdd>#shard#<n>"
        
        Returns:
            Partition key string for GSI1
        """
        base_key = ("channel", self.channel_id)
        
        # Check if sharding is enabled (requires channel config)
        if self._sharding_config and self._sharding_config.get("enabled"):
            bucket = self._get_time_bucket(
                self.created_utc_ts,
                self._sharding_config.get("bucket_span", "day")
            )
            shard = self._get_shard_index(
                self.id,
                self._sharding_config.get("shard_count", 1)
            )
            
            return DynamoDBKey.build_key(
                base_key,
                ("bucket", bucket),
                ("shard", str(shard))
            )
        
        # Default: no sharding
        return DynamoDBKey.build_key(base_key)
    
    @staticmethod
    def _get_time_bucket(timestamp: float, span: str) -> str:
        """
        Get time bucket string for partitioning messages.
        
        Args:
            timestamp: UTC timestamp
            span: "day" or "hour"
            
        Returns:
            Bucket string (yyyyMMdd or yyyyMMddHH)
        """
        from datetime import datetime, timezone
        dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        return dt.strftime("%Y%m%d" if span == "day" else "%Y%m%d%H")
    
    @staticmethod
    def _get_shard_index(message_id: str, shard_count: int) -> int:
        """
        Compute consistent shard index for message distribution.
        
        Uses MD5 hash of message_id for consistent distribution.
        
        Args:
            message_id: Message ID
            shard_count: Number of shards (1-8)
            
        Returns:
            Shard index (0 to shard_count-1)
        """
        if shard_count <= 1:
            return 0
        
        import hashlib
        h = hashlib.md5(message_id.encode()).hexdigest()
        return int(h[:8], 16) % shard_count
