"""
Geek Cafe, LLC
MIT License. See Project Root for the license information.

TenantSharingSettings - Adjacent record for tenant sharing configuration.

This model stores sharing-related settings for a tenant as a separate
DynamoDB item, using the same partition key as the Tenant but a different
sort key. This allows for extensible tenant configuration without
cluttering the main Tenant model.
"""

from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey
from typing import List, Optional
from geek_cafe_saas_sdk.core.models.base_model import BaseModel


class TenantSharingSettings(BaseModel):
    """
    Sharing settings for a tenant.
    
    Stored as an adjacent record to the Tenant model:
    - pk: tenant#<tenant_id>
    - sk: settings#sharing
    
    This allows loading sharing settings independently from the main
    tenant record, following single-table design patterns.
    """
    
    def __init__(self):
        super().__init__()
        
        # Reference to parent tenant
        self._tenant_id: str | None = None
        
        # Cross-tenant sharing
        self._allow_cross_tenant_sharing: bool = True
        
        # Pending invite settings
        self._pending_invite_expiry_days: int = 7
        self._require_email_verification: bool = False
        
        # Notification settings
        self._notify_on_share: bool = True
        self._notify_on_share_accepted: bool = True
        self._notify_on_share_revoked: bool = False
        
        # Limits
        self._max_shares_per_resource: int | None = None  # None = unlimited
        self._max_pending_invites_per_user: int | None = None  # None = unlimited
        
        # Allowed permission levels
        self._allowed_permission_levels: List[str] = ["view", "download", "edit"]
        
        # Public link settings
        self._allow_public_links: bool = False
        self._public_link_expiry_days: int | None = 30
        self._require_password_for_public_links: bool = False
        
        self._setup_indexes()
    
    def _setup_indexes(self):
        """Setup DynamoDB indexes for tenant sharing settings."""
        
        # Primary index: Adjacent to Tenant
        # pk: tenant#<tenant_id>, sk: settings#sharing
        primary = DynamoDBIndex()
        primary.name = "primary"
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(
            ("tenant", self._tenant_id or self.id)
        )
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: DynamoDBKey.build_key(
            ("settings", "sharing")
        )
        self.indexes.add_primary(primary)
    
    # Properties - Identity
    
    @property
    def tenant_id(self) -> str | None:
        """Tenant ID this settings record belongs to."""
        return self._tenant_id
    
    @tenant_id.setter
    def tenant_id(self, value: str | None):
        self._tenant_id = value
        # Also set id for consistency
        if value:
            self.id = f"{value}:sharing"
    
    # Properties - Cross-tenant sharing
    
    @property
    def allow_cross_tenant_sharing(self) -> bool:
        """Whether users can share resources with users in other tenants."""
        return self._allow_cross_tenant_sharing
    
    @allow_cross_tenant_sharing.setter
    def allow_cross_tenant_sharing(self, value: bool):
        self._allow_cross_tenant_sharing = bool(value) if value is not None else True
    
    # Properties - Pending invite settings
    
    @property
    def pending_invite_expiry_days(self) -> int:
        """Days before pending invites expire (default: 7)."""
        return self._pending_invite_expiry_days
    
    @pending_invite_expiry_days.setter
    def pending_invite_expiry_days(self, value: int):
        if value is not None and value < 1:
            raise ValueError("pending_invite_expiry_days must be at least 1")
        self._pending_invite_expiry_days = value if value is not None else 7
    
    @property
    def require_email_verification(self) -> bool:
        """Whether email verification is required before share activates."""
        return self._require_email_verification
    
    @require_email_verification.setter
    def require_email_verification(self, value: bool):
        self._require_email_verification = bool(value) if value is not None else False
    
    # Properties - Notification settings
    
    @property
    def notify_on_share(self) -> bool:
        """Send email notification when a resource is shared."""
        return self._notify_on_share
    
    @notify_on_share.setter
    def notify_on_share(self, value: bool):
        self._notify_on_share = bool(value) if value is not None else True
    
    @property
    def notify_on_share_accepted(self) -> bool:
        """Send email notification when a pending share is accepted."""
        return self._notify_on_share_accepted
    
    @notify_on_share_accepted.setter
    def notify_on_share_accepted(self, value: bool):
        self._notify_on_share_accepted = bool(value) if value is not None else True
    
    @property
    def notify_on_share_revoked(self) -> bool:
        """Send email notification when a share is revoked."""
        return self._notify_on_share_revoked
    
    @notify_on_share_revoked.setter
    def notify_on_share_revoked(self, value: bool):
        self._notify_on_share_revoked = bool(value) if value is not None else False
    
    # Properties - Limits
    
    @property
    def max_shares_per_resource(self) -> int | None:
        """Maximum shares allowed per resource (None = unlimited)."""
        return self._max_shares_per_resource
    
    @max_shares_per_resource.setter
    def max_shares_per_resource(self, value: int | None):
        if value is not None and value < 1:
            raise ValueError("max_shares_per_resource must be at least 1 or None")
        self._max_shares_per_resource = value
    
    @property
    def max_pending_invites_per_user(self) -> int | None:
        """Maximum pending invites a user can have (None = unlimited)."""
        return self._max_pending_invites_per_user
    
    @max_pending_invites_per_user.setter
    def max_pending_invites_per_user(self, value: int | None):
        if value is not None and value < 1:
            raise ValueError("max_pending_invites_per_user must be at least 1 or None")
        self._max_pending_invites_per_user = value
    
    # Properties - Permission levels
    
    @property
    def allowed_permission_levels(self) -> List[str]:
        """Allowed permission levels for shares."""
        return self._allowed_permission_levels
    
    @allowed_permission_levels.setter
    def allowed_permission_levels(self, value: List[str]):
        valid_levels = {"view", "download", "edit"}
        if value is None:
            self._allowed_permission_levels = ["view", "download", "edit"]
        elif isinstance(value, list):
            # Validate all levels
            for level in value:
                if level not in valid_levels:
                    raise ValueError(f"Invalid permission level: {level}")
            self._allowed_permission_levels = value if value else ["view"]
        else:
            self._allowed_permission_levels = ["view", "download", "edit"]
    
    # Properties - Public link settings
    
    @property
    def allow_public_links(self) -> bool:
        """Whether public (unauthenticated) share links are allowed."""
        return self._allow_public_links
    
    @allow_public_links.setter
    def allow_public_links(self, value: bool):
        self._allow_public_links = bool(value) if value is not None else False
    
    @property
    def public_link_expiry_days(self) -> int | None:
        """Days before public links expire (None = never)."""
        return self._public_link_expiry_days
    
    @public_link_expiry_days.setter
    def public_link_expiry_days(self, value: int | None):
        if value is not None and value < 1:
            raise ValueError("public_link_expiry_days must be at least 1 or None")
        self._public_link_expiry_days = value
    
    @property
    def require_password_for_public_links(self) -> bool:
        """Whether public links require a password."""
        return self._require_password_for_public_links
    
    @require_password_for_public_links.setter
    def require_password_for_public_links(self, value: bool):
        self._require_password_for_public_links = bool(value) if value is not None else False
    
    @classmethod
    def default(cls, tenant_id: str) -> "TenantSharingSettings":
        """
        Create default sharing settings for a tenant.
        
        Used when settings don't exist yet (returns secure defaults).
        
        Args:
            tenant_id: The tenant ID
            
        Returns:
            TenantSharingSettings with default values
        """
        settings = cls()
        settings.tenant_id = tenant_id
        return settings
