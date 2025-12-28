from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey
from boto3_assist.utilities.string_utility import StringUtility
import datetime as dt
from typing import List, Optional, Dict, Any
from geek_cafe_saas_sdk.core.models.base_tenant_model import BaseTenantModel


class User(BaseTenantModel):
    """
    User model for event scheduling system.

    Represents users with roles, tenant association, and profile information.
    """

    def __init__(self):
        super().__init__()
        self._email: str | None = None
        self._first_name: str | None = None
        self._last_name: str | None = None
        self._roles: List[str] = ["tenant_user"]
        self._avatar: str | None = None
        
        # Authentication & Identity
        self._cognito_user_name: str | None = None  # Cognito sub (unique ID)
        self._identity_provider: str = "cognito"  # Primary provider: cognito | google | office365 | facebook | saml
        self._federated_identities: List[Dict[str, Any]] = []  # All linked identities (source of truth)
        # Structure: [{"provider": "google", "user_id": "1234567890", "linked_at_utc_ts": 123.45, "primary": True}]
        
        # User status and lifecycle
        self._status: str = "active"  # active|invited|disabled
        self._invited_utc_ts: float | None = None
        self._activated_utc_ts: float | None = None
        self._disabled_utc_ts: float | None = None
        
        # Privacy & Visibility Controls (Phase 1)
        self._profile_visibility: str = "invite_only"  # public | invite_only | private
        self._searchable_by_hosts: bool = True  # Can hosts find this user in search?
        self._show_full_name: bool = True  # Show full name vs initials
        self._show_email: bool = False  # Show email in profile
        self._show_avatar: bool = True  # Show avatar in profile
        
        # Privacy metadata
        self._privacy_updated_at_utc_ts: float | None = None
        self._privacy_updated_by_id: str | None = None

        self._setup_indexes()

    def _setup_indexes(self):
        """Setup DynamoDB indexes for user queries."""

        # Primary index: users by ID
        primary: DynamoDBIndex = DynamoDBIndex()
        primary.name = "primary"
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(("user", self.id))
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: DynamoDBKey.build_key(("user", self.id))
        self.indexes.add_primary(primary)

        ## GSI: 1 - Users by email (for uniqueness and login)
        gsi1: DynamoDBIndex = DynamoDBIndex()
        gsi1.name = "gsi1"
        gsi1.partition_key.attribute_name = f"{gsi1.name}_pk"
        gsi1.partition_key.value = lambda: DynamoDBKey.build_key(("email", self.email))
        gsi1.sort_key.attribute_name = f"{gsi1.name}_sk"
        gsi1.sort_key.value = lambda: DynamoDBKey.build_key(("email", self.email))
        self.indexes.add_secondary(gsi1)

        ## GSI: 2 - Users by tenant
        gsi2: DynamoDBIndex = DynamoDBIndex()
        gsi2.name = "gsi2"
        gsi2.partition_key.attribute_name = f"{gsi2.name}_pk"
        gsi2.partition_key.value = lambda: DynamoDBKey.build_key(("tenant", self.tenant_id))
        gsi2.sort_key.attribute_name = f"{gsi2.name}_sk"
        gsi2.sort_key.value = lambda: DynamoDBKey.build_key(("ts", self.created_utc_ts))
        self.indexes.add_secondary(gsi2)

        ## GSI: 3 - Users by role (for admin queries)
        gsi3: DynamoDBIndex = DynamoDBIndex()
        gsi3.name = "gsi3"
        gsi3.partition_key.attribute_name = f"{gsi3.name}_pk"
        gsi3.partition_key.value = lambda: DynamoDBKey.build_key(("role", self.primary_role))
        gsi3.sort_key.attribute_name = f"{gsi3.name}_sk"
        gsi3.sort_key.value = lambda: DynamoDBKey.build_key(("tenant", self.tenant_id), ("ts", self.created_utc_ts))
        self.indexes.add_secondary(gsi3)

        ## GSI: 4 - All users (for admin listing)
        gsi4: DynamoDBIndex = DynamoDBIndex()
        gsi4.name = "gsi4"
        gsi4.partition_key.attribute_name = f"{gsi4.name}_pk"
        gsi4.partition_key.value = lambda: DynamoDBKey.build_key(("user", "all"))
        gsi4.sort_key.attribute_name = f"{gsi4.name}_sk"
        gsi4.sort_key.value = lambda: DynamoDBKey.build_key(("ts", self.created_utc_ts))
        self.indexes.add_secondary(gsi4)

    @property
    def email(self) -> str | None:
        """User's email address."""
        return self._email

    @email.setter
    def email(self, value: str | None):
        """Set email and ensure it's lowercase."""
        if value:
            self._email = value.lower()
        else:
            self._email = value

    @property
    def first_name(self) -> str | None:
        """User's first name."""
        return self._first_name

    @first_name.setter
    def first_name(self, value: str | None):
        self._first_name = value

    @property
    def last_name(self) -> str | None:
        """User's last name."""
        return self._last_name

    @last_name.setter
    def last_name(self, value: str | None):
        self._last_name = value

    @property
    def full_name(self) -> str:
        """User's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return ""

    @property
    def roles(self) -> List[str]:
        """User's roles."""
        return self._roles

    @roles.setter
    def roles(self, value: List[str]):
        """Set roles, ensuring it's always a list."""
        if value is None:
            self._roles = ["tenant_user"]
        elif isinstance(value, list):
            self._roles = value if value else ["tenant_user"]
        else:
            self._roles = ["tenant_user"]

    @property
    def primary_role(self) -> str:
        """Primary role (first in the list, or 'tenant_user' if empty)."""
        return self._roles[0] if self._roles else "tenant_user"

    @property
    def is_admin(self) -> bool:
        """Check if user has any admin role."""
        admin_roles = {"platform_admin", "tenant_admin"}
        return any(role in admin_roles for role in self._roles)

    @property
    def is_organizer(self) -> bool:
        """Check if user has organizer role."""
        return "tenant_organizer" in self._roles

    @property
    def avatar(self) -> str | None:
        """User's avatar URL."""
        return self._avatar

    @avatar.setter
    def avatar(self, value: str | None):
        self._avatar = value
    
    @property
    def cognito_user_name(self) -> str | None:
        """Cognito username (sub/UUID from Cognito User Pool)."""
        return self._cognito_user_name
    
    @cognito_user_name.setter
    def cognito_user_name(self, value: str | None):
        self._cognito_user_name = value
    
    @property
    def identity_provider(self) -> str:
        """Identity provider type (cognito, google, office365, etc.)."""
        return self._identity_provider
    
    @identity_provider.setter
    def identity_provider(self, value: str):
        """Set identity provider. Validates against known providers."""
        valid_providers = {"cognito", "google", "office365", "facebook", "saml", "oidc"}
        if value.lower() not in valid_providers:
            # Allow but warn - don't fail for future providers
            pass
        self._identity_provider = value.lower()
    
    @property
    def primary_external_user_id(self) -> str | None:
        """Get the primary external user ID from federated identities."""
        primary = self.get_primary_identity()
        return primary.get("user_id") if primary else None
    
    @property
    def federated_identities(self) -> List[Dict[str, Any]]:
        """List of linked federated identities."""
        return self._federated_identities
    
    @federated_identities.setter
    def federated_identities(self, value: List[Dict[str, Any]]):
        self._federated_identities = value if value else []
    
    def is_federated_user(self) -> bool:
        """Check if user authenticated via external IdP."""
        return self._identity_provider != "cognito"
    
    def get_primary_identity(self) -> Dict[str, Any] | None:
        """Get primary federated identity (first in list)."""
        return self._federated_identities[0] if self._federated_identities else None

    def has_role(self, role: str) -> bool:
        """Check if user has a specific role."""
        return role in self._roles

    def add_role(self, role: str):
        """Add a role to the user if not already present."""
        if role not in self._roles:
            self._roles.append(role)

    def remove_role(self, role: str):
        """Remove a role from the user."""
        if role in self._roles:
            self._roles.remove(role)
            # Ensure at least 'tenant_user' role remains
            if not self._roles:
                self._roles = ["tenant_user"]
    
    # Status
    @property
    def status(self) -> str:
        """User status (active|invited|disabled)."""
        return self._status
    
    @status.setter
    def status(self, value: str):
        # don't enforce valid status - let the business logic handle it
        self._status = value
    
    # Invited timestamp
    @property
    def invited_utc_ts(self) -> float | None:
        """Timestamp when user was invited."""
        return self._invited_utc_ts
    
    @invited_utc_ts.setter
    def invited_utc_ts(self, value: float | None):
        self._invited_utc_ts = value
    
    # Activated timestamp
    @property
    def activated_utc_ts(self) -> float | None:
        """Timestamp when user activated their account."""
        return self._activated_utc_ts
    
    @activated_utc_ts.setter
    def activated_utc_ts(self, value: float | None):
        self._activated_utc_ts = value
    
    # Disabled timestamp
    @property
    def disabled_utc_ts(self) -> float | None:
        """Timestamp when user was disabled."""
        return self._disabled_utc_ts
    
    @disabled_utc_ts.setter
    def disabled_utc_ts(self, value: float | None):
        self._disabled_utc_ts = value
    
    # Status helper methods
    def is_active(self) -> bool:
        """Check if user is active."""
        return self._status == "active"
    
    def is_invited(self) -> bool:
        """Check if user is in invited state (pending activation)."""
        return self._status == "invited"
    
    def is_disabled(self) -> bool:
        """Check if user is disabled."""
        return self._status == "disabled"
    
    def invite(self):
        """
        Mark user as invited (pending activation).
        
        Sets status to 'invited' and records invitation timestamp.
        Used for invite workflow where user must accept/activate.
        """
        self._status = "invited"
        self._invited_utc_ts = dt.datetime.now(dt.UTC).timestamp()
    
    def activate(self):
        """
        Activate an invited user.
        
        Sets status to 'active' and records activation timestamp.
        Called when user accepts invite or completes signup.
        """
        self._status = "active"
        self._activated_utc_ts = dt.datetime.now(dt.UTC).timestamp()
    
    def disable(self):
        """
        Disable user account.
        
        Sets status to 'disabled' and records disabled timestamp.
        Disabled users cannot log in or access the system.
        """
        self._status = "disabled"
        self._disabled_utc_ts = dt.datetime.now(dt.UTC).timestamp()
    
    def enable(self):
        """
        Re-enable a disabled user account.
        
        Sets status back to 'active'.
        """
        if self._status == "disabled":
            self._status = "active"
            self._disabled_utc_ts = None
    
    # Privacy & Visibility Properties
    @property
    def profile_visibility(self) -> str:
        """User's profile visibility setting (public | invite_only | private)."""
        return self._profile_visibility
    
    @profile_visibility.setter
    def profile_visibility(self, value: str):
        if value not in ["public", "invite_only", "private"]:
            raise ValueError(f"Invalid visibility: {value}. Must be public, invite_only, or private.")
        self._profile_visibility = value
        self._privacy_updated_at_utc_ts = dt.datetime.now(dt.UTC).timestamp()
    
    @property
    def searchable_by_hosts(self) -> bool:
        """Whether hosts can find this user in search."""
        return self._searchable_by_hosts
    
    @searchable_by_hosts.setter
    def searchable_by_hosts(self, value: bool):
        self._searchable_by_hosts = bool(value)
        self._privacy_updated_at_utc_ts = dt.datetime.now(dt.UTC).timestamp()
    
    @property
    def show_full_name(self) -> bool:
        """Whether to show full name vs initials."""
        return self._show_full_name
    
    @show_full_name.setter
    def show_full_name(self, value: bool):
        self._show_full_name = bool(value)
    
    @property
    def show_email(self) -> bool:
        """Whether to show email in profile."""
        return self._show_email
    
    @show_email.setter
    def show_email(self, value: bool):
        self._show_email = bool(value)
    
    @property
    def show_avatar(self) -> bool:
        """Whether to show avatar in profile."""
        return self._show_avatar
    
    @show_avatar.setter
    def show_avatar(self, value: bool):
        self._show_avatar = bool(value)
    
    @property
    def privacy_updated_at_utc_ts(self) -> float | None:
        """Timestamp when privacy settings were last updated."""
        return self._privacy_updated_at_utc_ts
    
    @privacy_updated_at_utc_ts.setter
    def privacy_updated_at_utc_ts(self, value: float | None):
        self._privacy_updated_at_utc_ts = value
    
    @property
    def privacy_updated_by_id(self) -> str | None:
        """User ID who last updated privacy settings."""
        return self._privacy_updated_by_id
    
    @privacy_updated_by_id.setter
    def privacy_updated_by_id(self, value: str | None):
        self._privacy_updated_by_id = value
    
    # Privacy helper methods
    def is_public(self) -> bool:
        """Check if user has public profile visibility."""
        return self._profile_visibility == "public"
    
    def is_private(self) -> bool:
        """Check if user has private profile visibility."""
        return self._profile_visibility == "private"
    
    def is_invite_only(self) -> bool:
        """Check if user has invite-only profile visibility."""
        return self._profile_visibility == "invite_only"

    