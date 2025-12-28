"""
resourceShare model for resource sharing and permissions.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey
from boto3_assist.utilities.string_utility import StringUtility
import datetime as dt
from typing import Optional, Dict, Any
from geek_cafe_saas_sdk.core.models.base_tenant_user_model import BaseTenantUserModel


class ResourceShare(BaseTenantUserModel):
    """
    resource sharing record with permissions.
    
    Manages access control for resources. Users can share resources with other users
    with specific permission levels and optional expiration.
    
    Access Patterns (DynamoDB Keys):
    - pk: share#{share_id}
    - sk: share#{share_id}
    - gsi1: Shares by resource_id
    - gsi2: Shares by shared_with_user_id
    - gsi3: Shares by owner_id
    - gsi4: Pending shares by shared_with_email (for invite flow)
    
    Permission Levels:
    - "view": Can view metadata only
    - "download": Can view and download
    - "edit": Can view, download, and modify metadata
    
    Status Values:
    - "active": Share is active and usable
    - "pending_acceptance": Invite sent, waiting for user to register/accept
    - "revoked": Share was revoked by owner
    - "expired": Share expired (by time or invite expiry)
    """

    def __init__(self, resource_type: str | None = None):
        super().__init__()
        
        # Identity
        self._share_id: str | None = None  # Unique share ID
        self._resource_id: str | None = None  # Shared resource
        self._resource_type: str | None = resource_type
        # Sharing Information        
        self._shared_with_user_id: str | None = None  # Recipient user ID
        self._shared_with_email: str | None = None  # Recipient email (for external shares)
        
        # Permissions
        self._permission_level: str = "view"  # "view", "download", "edit"
        self._can_re_share: bool = False  # Can recipient share with others?
        
        # Access Control
        self._access_token: str | None = None  # Token for external/unauthenticated access
        self._expires_at_ts: float | None = None  # Expiration timestamp
        
        # Invite fields (for pending shares)
        self._invite_token: str | None = None  # Secure token for claiming invite
        self._invite_expires_at_ts: float | None = None  # When invite expires
        self._invite_message: str | None = None  # Optional message from sharer
        self._claimed_at_ts: float | None = None  # When invite was claimed
        
        # Usage Tracking
        self._access_count: int = 0  # Number of times accessed
        self._last_accessed_at_ts: float | None = None  # Last access timestamp
        
        # State
        self._status: str = "active"  # "active", "pending_acceptance", "revoked", "expired"
        self._revoked_at_ts: float | None = None  # When revoked
        
        # Timestamps (inherited from BaseModel)
        # created_utc_ts
        
        # CRITICAL: Call _setup_indexes() as LAST line in __init__
        self._setup_indexes()
    
    def _setup_indexes(self):
        """Setup DynamoDB indexes for resource share queries."""
        
        # Primary index: Share by ID
        primary = DynamoDBIndex()
        primary.name = "primary"
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(("share", self.id))
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: DynamoDBKey.build_key(("share", self.id))
        self.indexes.add_primary(primary)
        
        # GSI1: Shares by resource
        gsi = DynamoDBIndex()
        gsi.name = "gsi1"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(("resource", self.resource_id))
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(("created", self.created_utc_ts))
        self.indexes.add_secondary(gsi)
        
        # GSI2: Shares by shared_with_user
        gsi = DynamoDBIndex()
        gsi.name = "gsi2"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(("shared_with", self.shared_with_user_id))
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(("resource_type", self.resource_type),("created", self.created_utc_ts))
        self.indexes.add_secondary(gsi)

        # GSI3: User Shares by type (shares I created)
        gsi = DynamoDBIndex()
        gsi.name = "gsi3"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(("owner", self.owner_id))
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(("resource_type", self.resource_type), ("created", self.created_utc_ts))
        self.indexes.add_secondary(gsi)
        
        # GSI4: Pending shares by email (for invite claim flow)
        gsi = DynamoDBIndex()
        gsi.name = "gsi4"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(("invite_email", self._query_index_shared_with_email()))
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(("status", self._query_index_status()), ("created", self.created_utc_ts))
        self.indexes.add_secondary(gsi)
    
    def _query_index_shared_with_email(self) -> str:
        """Helper for GSI4 partition key - returns empty string if not set."""
        return self._shared_with_email or ""
    
    def _query_index_status(self) -> str:
        """Helper for GSI4 sort key - returns empty string if not set."""
        return self._status or ""
    
    # Properties - Identity
    @property
    def share_id(self) -> str | None:
        """Unique share ID."""
        return self._share_id or self.id
    
    @share_id.setter
    def share_id(self, value: str | None):
        self._share_id = value
        if value:
            self.id = value
    
    @property
    def resource_id(self) -> str | None:
        """Shared resource ID."""
        return self._resource_id
    
    @resource_id.setter
    def resource_id(self, value: str | None):
        self._resource_id = value
    
    @property
    def resource_type(self) -> str | None:
        """Shared resource type."""
        return self._resource_type
    
    @resource_type.setter
    def resource_type(self, value: str | None):
        self._resource_type = value    
    
    @property
    def shared_with_user_id(self) -> str | None:
        """Recipient user ID."""
        return self._shared_with_user_id
    
    @shared_with_user_id.setter
    def shared_with_user_id(self, value: str | None):
        self._shared_with_user_id = value
    
    @property
    def shared_with_email(self) -> str | None:
        """Recipient email (for external shares)."""
        return self._shared_with_email
    
    @shared_with_email.setter
    def shared_with_email(self, value: str | None):
        self._shared_with_email = value
    
    # Properties - Permissions
    @property
    def permission_level(self) -> str:
        """Permission level: 'view', 'download', 'edit'."""
        return self._permission_level
    
    @permission_level.setter
    def permission_level(self, value: str):
        if value not in ["view", "download", "edit"]:
            raise ValueError(f"Invalid permission level: {value}. Must be 'view', 'download', or 'edit'")
        self._permission_level = value
    
    @property
    def can_re_share(self) -> bool:
        """Can recipient share with others?"""
        return self._can_re_share
    
    @can_re_share.setter
    def can_re_share(self, value: bool):
        self._can_re_share = bool(value)
    
    # Properties - Access Control
    @property
    def access_token(self) -> str | None:
        """Access token for public links."""
        return self._access_token
    
    @access_token.setter
    def access_token(self, value: str | None):
        self._access_token = value
    
    @property
    def expires_at_ts(self) -> float | None:
        """Expiration timestamp."""
        return self._expires_at_ts
    
    @expires_at_ts.setter
    def expires_at_ts(self, value: float | None):
        self._expires_at_ts = value
    
    # Properties - Usage Tracking
    @property
    def access_count(self) -> int:
        """Number of times accessed."""
        return self._access_count
    
    @access_count.setter
    def access_count(self, value: int):
        self._access_count = value if value is not None else 0
    
    @property
    def last_accessed_at_ts(self) -> float | None:
        """Last access timestamp."""
        return self._last_accessed_at_ts
    
    @last_accessed_at_ts.setter
    def last_accessed_at_ts(self, value: float | None):
        self._last_accessed_at_ts = value
    
    # Properties - State
    @property
    def status(self) -> str:
        """Share status: 'active', 'revoked', 'expired'."""
        return self._status
    
    @status.setter
    def status(self, value: str):
        valid_statuses = ["active", "pending_acceptance", "revoked", "expired"]
        if value not in valid_statuses:
            raise ValueError(f"Invalid status: {value}. Must be one of {valid_statuses}")
        self._status = value
    
    @property
    def revoked_at_ts(self) -> float | None:
        """When share was revoked."""
        return self._revoked_at_ts
    
    @revoked_at_ts.setter
    def revoked_at_ts(self, value: float | None):
        self._revoked_at_ts = value
    
    # Helper Methods
    def is_active(self) -> bool:
        """Check if share is active."""
        return self._status == "active"
    
    def is_revoked(self) -> bool:
        """Check if share is revoked."""
        return self._status == "revoked"
    
    def is_expired(self) -> bool:
        """Check if share is expired (by status or timestamp)."""
        if self._status == "expired":
            return True
        if self._expires_at_ts:
            return dt.datetime.now(dt.UTC).timestamp() > self._expires_at_ts
        return False
    
    def is_public_link(self) -> bool:
        """Check if this is a public link (has access token)."""
        return self._access_token is not None and self._access_token != ""
    
    def is_internal_share(self) -> bool:
        """Check if shared with another user (not public)."""
        return self._shared_with_user_id is not None and self._shared_with_user_id != ""
    
    def can_view(self) -> bool:
        """Check if share allows viewing."""
        return self._permission_level in ["view", "download", "edit"]
    
    def can_download(self) -> bool:
        """Check if share allows downloading."""
        return self._permission_level in ["download", "edit"]
    
    def can_edit(self) -> bool:
        """Check if share allows editing."""
        return self._permission_level == "edit"
    
    def increment_access_count(self):
        """Increment access count and update last accessed time."""
        self._access_count += 1
        self._last_accessed_at_ts = dt.datetime.now(dt.UTC).timestamp()
    
    def revoke(self):
        """Revoke the share."""
        self._status = "revoked"
        self._revoked_at_ts = dt.datetime.now(dt.UTC).timestamp()
    
    def mark_as_expired(self):
        """Mark share as expired."""
        self._status = "expired"
    
    def has_permission(self, required_level: str) -> bool:
        """
        Check if share has required permission level.
        
        Permission hierarchy: edit > download > view
        """
        hierarchy = {"view": 1, "download": 2, "edit": 3}
        current = hierarchy.get(self._permission_level, 0)
        required = hierarchy.get(required_level, 0)
        return current >= required
    
    def get_expires_at_datetime(self) -> dt.datetime | None:
        """Get expiration as datetime object."""
        if self._expires_at_ts:
            return dt.datetime.fromtimestamp(self._expires_at_ts, tz=dt.UTC)
        return None
    
    def get_revoked_at_datetime(self) -> dt.datetime | None:
        """Get revocation time as datetime object."""
        if self._revoked_at_ts:
            return dt.datetime.fromtimestamp(self._revoked_at_ts, tz=dt.UTC)
        return None
    
    # Properties - Invite fields
    
    @property
    def invite_token(self) -> str | None:
        """Secure token for claiming pending invite."""
        return self._invite_token
    
    @invite_token.setter
    def invite_token(self, value: str | None):
        self._invite_token = value
    
    @property
    def invite_expires_at_ts(self) -> float | None:
        """When the invite expires."""
        return self._invite_expires_at_ts
    
    @invite_expires_at_ts.setter
    def invite_expires_at_ts(self, value: float | None):
        self._invite_expires_at_ts = value
    
    @property
    def invite_message(self) -> str | None:
        """Optional message from the sharer."""
        return self._invite_message
    
    @invite_message.setter
    def invite_message(self, value: str | None):
        self._invite_message = value
    
    @property
    def claimed_at_ts(self) -> float | None:
        """When the invite was claimed."""
        return self._claimed_at_ts
    
    @claimed_at_ts.setter
    def claimed_at_ts(self, value: float | None):
        self._claimed_at_ts = value
    
    # Additional helper methods for invite flow
    
    def is_pending(self) -> bool:
        """Check if share is pending acceptance."""
        return self._status == "pending_acceptance"
    
    def is_invite_expired(self) -> bool:
        """Check if invite has expired."""
        if not self._invite_expires_at_ts:
            return False
        return dt.datetime.now(dt.UTC).timestamp() > self._invite_expires_at_ts
    
    def get_invite_expires_at_datetime(self) -> dt.datetime | None:
        """Get invite expiration as datetime object."""
        if self._invite_expires_at_ts:
            return dt.datetime.fromtimestamp(self._invite_expires_at_ts, tz=dt.UTC)
        return None
    
    def get_claimed_at_datetime(self) -> dt.datetime | None:
        """Get claim time as datetime object."""
        if self._claimed_at_ts:
            return dt.datetime.fromtimestamp(self._claimed_at_ts, tz=dt.UTC)
        return None
