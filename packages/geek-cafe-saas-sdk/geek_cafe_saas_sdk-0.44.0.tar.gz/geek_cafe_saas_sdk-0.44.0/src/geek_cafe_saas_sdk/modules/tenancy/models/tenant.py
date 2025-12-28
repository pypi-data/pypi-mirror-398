"""
Geek Cafe, LLC
MIT License.  See Project Root for the license information.

Tenant model for multi-tenant SaaS organizations.
"""

from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey
from typing import Dict, Any, Optional
from geek_cafe_saas_sdk.core.models.base_model import BaseModel


class Tenant(BaseModel):
    """
    Tenant/Organization model for multi-tenant SaaS.
    
    Represents a customer organization with multiple users and a subscription.
    Each tenant has a plan tier, status, and customizable feature flags.
    
    Key Features:
    - Multi-user support (one or many users per tenant)
    - Subscription management (linked via tenant_id)
    - Feature flags for plan differentiation
    - Primary contact tracking
    
    Access Patterns:
    - Get tenant by ID (primary key)
    - List tenants by status (GSI1)
    - List all tenants sorted by name (GSI2)
    """
    
    def __init__(self):
        super().__init__()
        
        # Basic info
        self._name: str | None = None
        self._status: str = "active"  # active|inactive|archived
        self._plan_tier: str = "free"  # free|basic|pro|enterprise
        
        # Relationships
        self._primary_contact_user_id: str | None = None
        
        # Limits & settings
        self._max_users: int | None = None  # Null = unlimited
        self._features: Dict[str, Any] = {}  # Feature flags per tenant
        
        # Access control settings
        self._allow_tenant_wide_access: bool = False  # If True, any user in tenant can access any resource
        
        # Metadata
        self._description: str | None = None
        self._website: str | None = None
        self._logo_url: str | None = None
        
        self._setup_indexes()
    
    def _setup_indexes(self):
        """Setup DynamoDB indexes for efficient tenant queries."""
        
        # Primary index: tenant by ID
        primary: DynamoDBIndex = DynamoDBIndex()
        primary.name = "primary"
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(("tenant", self.id))
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: DynamoDBKey.build_key(("tenant", self.id))
        self.indexes.add_primary(primary)
        
        # GSI1: Tenants by status (for admin queries - active, inactive, archived)
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi1"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(
            ("tenant_status", self.status)
        )
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
            ("ts", self.created_utc_ts)
        )
        self.indexes.add_secondary(gsi)
        
        # GSI2: All tenants sorted by name (for admin listing)
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi2"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(("tenant", "all"))
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
            ("name", self.name or ""),
            ("ts", self.created_utc_ts)
        )
        self.indexes.add_secondary(gsi)
        
        # GSI3: Tenants by plan tier (for analytics/reporting)
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi3"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(
            ("plan_tier", self.plan_tier)
        )
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
            ("ts", self.created_utc_ts)
        )
        self.indexes.add_secondary(gsi)
    
    # Name
    @property
    def name(self) -> str | None:
        """Tenant organization name."""
        return self._name
    
    @name.setter
    def name(self, value: str | None):
        self._name = value
    
    # Status
    @property
    def status(self) -> str:
        """Tenant status (active|inactive|archived)."""
        return self._status
    
    @status.setter
    def status(self, value: str):
        if value not in ["active", "inactive", "archived"]:
            raise ValueError(f"Invalid status: {value}. Must be active, inactive, or archived.")
        self._status = value
    
    # Plan Tier
    @property
    def plan_tier(self) -> str:
        """Subscription plan tier (free|basic|pro|enterprise)."""
        return self._plan_tier
    
    @plan_tier.setter
    def plan_tier(self, value: str):
        if value not in ["free", "basic", "pro", "enterprise"]:
            raise ValueError(f"Invalid plan_tier: {value}. Must be free, basic, pro, or enterprise.")
        self._plan_tier = value
    
    # Primary Contact User ID
    @property
    def primary_contact_user_id(self) -> str | None:
        """User ID of primary contact/admin."""
        return self._primary_contact_user_id
    
    @primary_contact_user_id.setter
    def primary_contact_user_id(self, value: str | None):
        self._primary_contact_user_id = value
    
    # Max Users
    @property
    def max_users(self) -> int | None:
        """Maximum users allowed (None = unlimited)."""
        return self._max_users
    
    @max_users.setter
    def max_users(self, value: int | None):
        if value is not None and value < 1:
            raise ValueError("max_users must be at least 1 or None for unlimited")
        self._max_users = value
    
    # Features
    @property
    def features(self) -> Dict[str, Any]:
        """
        Feature flags for tenant.
        
        Example:
        {
            "chat": True,
            "events": True,
            "analytics": False,
            "api_access": True,
            "custom_branding": True
        }
        """
        return self._features
    
    @features.setter
    def features(self, value: Dict[str, Any]):
        if value is None:
            self._features = {}
        elif isinstance(value, dict):
            self._features = value
        else:
            self._features = {}
    
    # Allow Tenant Wide Access
    @property
    def allow_tenant_wide_access(self) -> bool:
        """
        Whether any user in the tenant can access any resource in the tenant.
        
        When True (permissive mode):
            - Any authenticated user in the tenant can view/access resources
            - Useful for small teams or collaborative environments
            - Still respects EDIT/DELETE requiring ownership or admin
            
        When False (strict mode - default):
            - Users can only access resources they own or have been shared
            - More secure, prevents accidental data exposure
            - Recommended for larger organizations or sensitive data
        """
        return self._allow_tenant_wide_access
    
    @allow_tenant_wide_access.setter
    def allow_tenant_wide_access(self, value: bool):
        self._allow_tenant_wide_access = bool(value) if value is not None else False
    
    # Description
    @property
    def description(self) -> str | None:
        """Tenant description."""
        return self._description
    
    @description.setter
    def description(self, value: str | None):
        self._description = value
    
    # Website
    @property
    def website(self) -> str | None:
        """Tenant website URL."""
        return self._website
    
    @website.setter
    def website(self, value: str | None):
        self._website = value
    
    # Logo URL
    @property
    def logo_url(self) -> str | None:
        """Tenant logo URL."""
        return self._logo_url
    
    @logo_url.setter
    def logo_url(self, value: str | None):
        self._logo_url = value
    
    # Helper Methods
    
    def is_active(self) -> bool:
        """Check if tenant is active."""
        return self._status == "active"
    
    def is_inactive(self) -> bool:
        """Check if tenant is inactive."""
        return self._status == "inactive"
    
    def is_archived(self) -> bool:
        """Check if tenant is archived."""
        return self._status == "archived"
    
    def has_feature(self, feature_key: str) -> bool:
        """Check if tenant has a specific feature enabled."""
        return self._features.get(feature_key, False) is True
    
    def enable_feature(self, feature_key: str):
        """Enable a feature for this tenant."""
        self._features[feature_key] = True
    
    def disable_feature(self, feature_key: str):
        """Disable a feature for this tenant."""
        self._features[feature_key] = False
    
    def is_at_user_limit(self, current_user_count: int) -> bool:
        """Check if tenant is at maximum user limit."""
        if self._max_users is None:
            return False  # Unlimited
        return current_user_count >= self._max_users
    
    def activate(self):
        """Set tenant status to active."""
        self._status = "active"
    
    def deactivate(self):
        """Set tenant status to inactive."""
        self._status = "inactive"
    
    def archive(self):
        """Set tenant status to archived."""
        self._status = "archived"
