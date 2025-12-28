"""
Geek Cafe, LLC
MIT License. See Project Root for the license information.

TenantPrivacySettings - Adjacent record for tenant privacy configuration.

This model stores privacy-related settings for a tenant as a separate
DynamoDB item, using the same partition key as the Tenant but a different
sort key. This controls user discoverability and profile visibility.
"""

from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey
from typing import Optional
from geek_cafe_saas_sdk.core.models.base_model import BaseModel


class TenantPrivacySettings(BaseModel):
    """
    Privacy settings for a tenant.
    
    Stored as an adjacent record to the Tenant model:
    - pk: tenant#<tenant_id>
    - sk: settings#privacy
    
    Controls user discoverability, profile visibility defaults,
    and whether users can override tenant-level settings.
    """
    
    def __init__(self):
        super().__init__()
        
        # Reference to parent tenant
        self._tenant_id: str | None = None
        
        # User discoverability defaults
        self._users_searchable_by_default: bool = True
        self._default_profile_visibility: str = "invite_only"  # public | invite_only | private
        
        # User override permissions
        self._allow_user_privacy_override: bool = True
        
        # Profile field visibility defaults
        self._show_email_by_default: bool = False
        self._show_full_name_by_default: bool = True
        self._show_avatar_by_default: bool = True
        
        # Cross-tenant discovery
        self._allow_cross_tenant_user_lookup: bool = True
        self._allow_cross_tenant_user_search: bool = False  # More restrictive than lookup
        
        # Search restrictions
        self._require_exact_email_for_lookup: bool = True  # No partial email search
        self._min_search_query_length: int = 2  # Minimum chars for name search
        
        self._setup_indexes()
    
    def _setup_indexes(self):
        """Setup DynamoDB indexes for tenant privacy settings."""
        
        # Primary index: Adjacent to Tenant
        # pk: tenant#<tenant_id>, sk: settings#privacy
        primary = DynamoDBIndex()
        primary.name = "primary"
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(
            ("tenant", self._tenant_id or self.id)
        )
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: DynamoDBKey.build_key(
            ("settings", "privacy")
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
        if value:
            self.id = f"{value}:privacy"
    
    # Properties - User discoverability defaults
    
    @property
    def users_searchable_by_default(self) -> bool:
        """Whether new users are searchable by default."""
        return self._users_searchable_by_default
    
    @users_searchable_by_default.setter
    def users_searchable_by_default(self, value: bool):
        self._users_searchable_by_default = bool(value) if value is not None else True
    
    @property
    def default_profile_visibility(self) -> str:
        """Default profile visibility for new users (public|invite_only|private)."""
        return self._default_profile_visibility
    
    @default_profile_visibility.setter
    def default_profile_visibility(self, value: str):
        valid_values = {"public", "invite_only", "private"}
        if value not in valid_values:
            raise ValueError(f"Invalid profile visibility: {value}. Must be one of {valid_values}")
        self._default_profile_visibility = value
    
    # Properties - User override permissions
    
    @property
    def allow_user_privacy_override(self) -> bool:
        """Whether users can change their own privacy settings."""
        return self._allow_user_privacy_override
    
    @allow_user_privacy_override.setter
    def allow_user_privacy_override(self, value: bool):
        self._allow_user_privacy_override = bool(value) if value is not None else True
    
    # Properties - Profile field visibility defaults
    
    @property
    def show_email_by_default(self) -> bool:
        """Whether email is visible in profile by default."""
        return self._show_email_by_default
    
    @show_email_by_default.setter
    def show_email_by_default(self, value: bool):
        self._show_email_by_default = bool(value) if value is not None else False
    
    @property
    def show_full_name_by_default(self) -> bool:
        """Whether full name is visible in profile by default."""
        return self._show_full_name_by_default
    
    @show_full_name_by_default.setter
    def show_full_name_by_default(self, value: bool):
        self._show_full_name_by_default = bool(value) if value is not None else True
    
    @property
    def show_avatar_by_default(self) -> bool:
        """Whether avatar is visible in profile by default."""
        return self._show_avatar_by_default
    
    @show_avatar_by_default.setter
    def show_avatar_by_default(self, value: bool):
        self._show_avatar_by_default = bool(value) if value is not None else True
    
    # Properties - Cross-tenant discovery
    
    @property
    def allow_cross_tenant_user_lookup(self) -> bool:
        """Whether users from other tenants can look up users by exact email."""
        return self._allow_cross_tenant_user_lookup
    
    @allow_cross_tenant_user_lookup.setter
    def allow_cross_tenant_user_lookup(self, value: bool):
        self._allow_cross_tenant_user_lookup = bool(value) if value is not None else True
    
    @property
    def allow_cross_tenant_user_search(self) -> bool:
        """Whether users from other tenants can search for users by name."""
        return self._allow_cross_tenant_user_search
    
    @allow_cross_tenant_user_search.setter
    def allow_cross_tenant_user_search(self, value: bool):
        self._allow_cross_tenant_user_search = bool(value) if value is not None else False
    
    # Properties - Search restrictions
    
    @property
    def require_exact_email_for_lookup(self) -> bool:
        """Whether email lookup requires exact match (no partial search)."""
        return self._require_exact_email_for_lookup
    
    @require_exact_email_for_lookup.setter
    def require_exact_email_for_lookup(self, value: bool):
        self._require_exact_email_for_lookup = bool(value) if value is not None else True
    
    @property
    def min_search_query_length(self) -> int:
        """Minimum characters required for name search."""
        return self._min_search_query_length
    
    @min_search_query_length.setter
    def min_search_query_length(self, value: int):
        if value is not None and value < 1:
            raise ValueError("min_search_query_length must be at least 1")
        self._min_search_query_length = value if value is not None else 2
    
    @classmethod
    def default(cls, tenant_id: str) -> "TenantPrivacySettings":
        """
        Create default privacy settings for a tenant.
        
        Args:
            tenant_id: The tenant ID
            
        Returns:
            TenantPrivacySettings with default values
        """
        settings = cls()
        settings.tenant_id = tenant_id
        return settings
