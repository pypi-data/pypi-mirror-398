from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey
from typing import List
from geek_cafe_saas_sdk.core.models.base_tenant_user_model import BaseTenantUserModel


class Community(BaseTenantUserModel):
    """
    Community model for member-based organizing.
    
    Similar to Meetup groups - supports membership management,
    leadership structure, dues, and event organization.
    Represents communities with membership, moderation, and privacy controls.
    """

    def __init__(self):
        super().__init__()
        self._name: str | None = None
        self._description: str | None = None
        self._category: str | None = None
        self._privacy: str = "public"  # public, private
        self._tags: List[str] = []
        self._join_approval: str = "open"  # open, approval
        self._requires_dues: bool = False
        self._dues_monthly: float | None = None
        self._dues_yearly: float | None = None

        # Leadership (kept in-model for fast access)        
        self._co_owners: List[str] = []  # ~5-10 max
        self._moderators: List[str] = []  # ~10-20 max
        
        # Membership stats (cached/denormalized)
        self._member_count: int = 0  # Use CommunityMemberService for actual membership

        self._setup_indexes()

    def _setup_indexes(self):
        """Setup DynamoDB indexes for community queries."""

        # Primary index: communities by ID
        primary: DynamoDBIndex = DynamoDBIndex()
        primary.name = "primary"
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(("community", self.id))
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: DynamoDBKey.build_key(("community", self.id))
        self.indexes.add_primary(primary)

        ## GSI: 1 - Communities by owner
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi1"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(("user", self.owner_id))
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(("model", "community"), ("ts", self.created_utc_ts))
        self.indexes.add_secondary(gsi)

        ## GSI: 2 - Communities by privacy
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi2"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(("privacy", self.privacy))
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(("ts", self.created_utc_ts))
        self.indexes.add_secondary(gsi)

        ## GSI: 3 - Communities by category
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi3"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(("category", self.category))
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(("ts", self.created_utc_ts))
        self.indexes.add_secondary(gsi)

        ## GSI: 4 - Communities by tenant
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi4"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(("tenant", self.tenant_id))
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(("model", "community"), ("ts", self.created_utc_ts))
        self.indexes.add_secondary(gsi)

        ## GSI: 5 - All communities (for admin queries)
        gsi: DynamoDBIndex = DynamoDBIndex()
        gsi.name = "gsi5"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(("community", "all"))
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(("ts", self.created_utc_ts))
        self.indexes.add_secondary(gsi)

    @property
    def name(self) -> str | None:
        """Community name."""
        return self._name

    @name.setter
    def name(self, value: str | None):
        self._name = value

    @property
    def description(self) -> str | None:
        """Community description."""
        return self._description

    @description.setter
    def description(self, value: str | None):
        self._description = value

    @property
    def category(self) -> str | None:
        """Community category."""
        return self._category

    @category.setter
    def category(self, value: str | None):
        self._category = value

    @property
    def privacy(self) -> str:
        """Community privacy: public, private."""
        return self._privacy

    @privacy.setter
    def privacy(self, value: str | None):
        """Set privacy with validation."""
        if value in ["public", "private"]:
            self._privacy = value
        else:
            self._privacy = "public"  # default

    @property
    def tags(self) -> List[str]:
        """Community tags."""
        return self._tags

    @tags.setter
    def tags(self, value: List[str] | None):
        """Set tags, ensuring it's always a list."""
        if value is None:
            self._tags = []
        elif isinstance(value, list):
            # Limit to 5 tags, max 20 chars each
            self._tags = [tag[:20] for tag in value[:5]]
        else:
            self._tags = []

    @property
    def join_approval(self) -> str:
        """Join approval setting: open, approval."""
        return self._join_approval

    @join_approval.setter
    def join_approval(self, value: str | None):
        """Set join approval with validation."""
        if value in ["open", "approval"]:
            self._join_approval = value
        else:
            self._join_approval = "open"  # default

    @property
    def requires_dues(self) -> bool:
        """Whether the community requires dues."""
        return self._requires_dues

    @requires_dues.setter
    def requires_dues(self, value: bool):
        self._requires_dues = bool(value)

    @property
    def dues_monthly(self) -> float | None:
        """Monthly dues amount."""
        return self._dues_monthly

    @dues_monthly.setter
    def dues_monthly(self, value: float | None):
        if value is not None and value >= 0:
            self._dues_monthly = value
        else:
            self._dues_monthly = None

    @property
    def dues_yearly(self) -> float | None:
        """Yearly dues amount."""
        return self._dues_yearly

    @dues_yearly.setter
    def dues_yearly(self, value: float | None):
        if value is not None and value >= 0:
            self._dues_yearly = value
        else:
            self._dues_yearly = None    

    @property
    def co_owners(self) -> List[str]:
        """Co-owner user IDs."""
        return self._co_owners

    @co_owners.setter
    def co_owners(self, value: List[str] | None):
        """Set co-owners, ensuring it's always a list."""
        if value is None:
            self._co_owners = []
        elif isinstance(value, list):
            self._co_owners = value
        else:
            self._co_owners = []

    @property
    def moderators(self) -> List[str]:
        """Moderator user IDs."""
        return self._moderators

    @moderators.setter
    def moderators(self, value: List[str] | None):
        """Set moderators, ensuring it's always a list."""
        if value is None:
            self._moderators = []
        elif isinstance(value, list):
            self._moderators = value
        else:
            self._moderators = []

    @property
    def member_count(self) -> int:
        """Cached member count. Use CommunityMemberService.get_member_count() for real-time count."""
        return self._member_count
    
    @member_count.setter
    def member_count(self, value: int | None):
        """Set cached member count."""
        self._member_count = value if isinstance(value, int) and value >= 0 else 0

    def get_user_role(self, user_id: str) -> str:
        """
        Get the leadership role of a user in this community.
        
        Note: Only checks leadership roles (owner, co-owner, moderator).
        Use CommunityMemberService to check full membership.
        """
        if self.owner_id == user_id:
            return "owner"
        elif user_id in self.co_owners:
            return "co-owner"
        elif user_id in self.moderators:
            return "moderator"
        else:
            return "guest"  # Not in leadership - may still be a member

    def is_user_member(self, user_id: str) -> bool:
        """
        Check if user is a member (owner/co-owner/moderator).
        
        Note: For full membership check, use CommunityMemberService.is_member()
        This only checks leadership roles for quick access control.
        """
        return (self.owner_id == user_id or 
                user_id in self.co_owners or 
                user_id in self.moderators)

    def is_user_organizer(self, user_id: str) -> bool:
        """Check if user is an organizer (owner or co-owner)."""
        return self.owner_id == user_id or user_id in self.co_owners

    def is_user_moderator(self, user_id: str) -> bool:
        """Check if user is a moderator or organizer."""
        return self.is_user_organizer(user_id) or user_id in self.moderators

    def can_user_view(self, user_id: str) -> bool:
        """
        Check if a user can view this community.

        Basic implementation - privacy logic will be enhanced later.
        """
        if self.privacy == "public":
            return True
        elif self.privacy == "private":
            # Private communities: only members can see
            return self.is_user_member(user_id)
        return False

    def can_user_manage(self, user_id: str) -> bool:
        """Check if user can manage this community (organizers only)."""
        return self.is_user_organizer(user_id)

    def increment_member_count(self):
        """Increment cached member count."""
        self._member_count += 1
    
    def decrement_member_count(self):
        """Decrement cached member count."""
        if self._member_count > 0:
            self._member_count -= 1

    def add_moderator(self, user_id: str):
        """Add a user as moderator."""
        if user_id not in self._moderators:
            self._moderators.append(user_id)

    def remove_moderator(self, user_id: str):
        """Remove a user from moderators."""
        if user_id in self._moderators:
            self._moderators.remove(user_id)

    def add_co_owner(self, user_id: str):
        """Add a user as co-owner."""
        if user_id not in self._co_owners:
            self._co_owners.append(user_id)

    def remove_co_owner(self, user_id: str):
        """Remove a user from co-owners."""
        if user_id in self._co_owners:
            self._co_owners.remove(user_id)
