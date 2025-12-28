"""
ProjectActor model for project team members.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from typing import Optional
from boto3_assist.dynamodb.dynamodb_index import DynamoDBIndex, DynamoDBKey
from geek_cafe_saas_sdk.core.models.base_tenant_user_model import BaseTenantUserModel


class ActorStatus:
    """Actor status constants."""
    ACTIVE = "active"
    INVITED = "invited"
    REMOVED = "removed"
    
    ALL = [ACTIVE, INVITED, REMOVED]


class ProjectActor(BaseTenantUserModel):
    """
    ProjectActor model associating users with projects and roles.
    
    Represents a user's participation in a project with a specific role.
    
    Access Patterns (DynamoDB Keys):
    - pk: project#{project_id}
    - sk: actor#{actor_id}
    - gsi1_pk: tenant#{tenant_id}#user#{user_id}
    - gsi1_sk: project#{project_id}#role#{role_code}
    """

    def __init__(self):
        super().__init__()
        
        # Identity
        self._actor_id: str | None = None
        self._project_id: str | None = None
        
        # Role
        self._role_code: str | None = None  # References ActorRoleDefinition.code
        self._display_name: str | None = None  # Cached user display name
        
        # Status
        self._status: str = ActorStatus.ACTIVE
        
        # Optional fields
        self._allocation_percent: int | None = None  # Planned capacity (0-100)
        self._notes: str | None = None
        
        # Model metadata
        self.model_name = "project_actor"
        self.model_name_plural = "project_actors"
        
        # CRITICAL: Call _setup_indexes() as LAST line in __init__
        self._setup_indexes()
    
    def _setup_indexes(self):
        """Setup DynamoDB indexes for actor queries."""
        
        # Primary index: Actor within project (adjacency pattern)
        primary = DynamoDBIndex()
        primary.name = "primary"
        primary.partition_key.attribute_name = "pk"
        primary.partition_key.value = lambda: DynamoDBKey.build_key(("project", self.project_id))
        primary.sort_key.attribute_name = "sk"
        primary.sort_key.value = lambda: DynamoDBKey.build_key(("actor", self.id or ""))
        self.indexes.add_primary(primary)
        
        # GSI1: Projects by user (find all projects for a user)
        gsi = DynamoDBIndex()
        gsi.name = "gsi1"
        gsi.partition_key.attribute_name = f"{gsi.name}_pk"
        gsi.partition_key.value = lambda: DynamoDBKey.build_key(
            ("tenant", self.tenant_id),
            ("user", self.user_id),
        )
        gsi.sort_key.attribute_name = f"{gsi.name}_sk"
        gsi.sort_key.value = lambda: DynamoDBKey.build_key(
            ("project", self.project_id),
            ("role", self.role_code or ""),
        )
        self.indexes.add_secondary(gsi)
    
    # Properties - Identity
    @property
    def actor_id(self) -> str | None:
        """Unique actor ID."""
        return self._actor_id or self.id
    
    @actor_id.setter
    def actor_id(self, value: str | None):
        self._actor_id = value
        if value:
            self.id = value
    
    @property
    def project_id(self) -> str | None:
        """Project ID this actor belongs to."""
        return self._project_id
    
    @project_id.setter
    def project_id(self, value: str | None):
        self._project_id = value
    
    # Properties - Role
    @property
    def role_code(self) -> str | None:
        """Role code (references ActorRoleDefinition)."""
        return self._role_code
    
    @role_code.setter
    def role_code(self, value: str | None):
        self._role_code = value
    
    @property
    def display_name(self) -> str | None:
        """Cached display name for the user."""
        return self._display_name
    
    @display_name.setter
    def display_name(self, value: str | None):
        self._display_name = value
    
    # Properties - Status
    @property
    def status(self) -> str:
        """Actor status."""
        return self._status
    
    @status.setter
    def status(self, value: str):
        if value and value not in ActorStatus.ALL:
            raise ValueError(f"Invalid status: {value}. Must be one of {ActorStatus.ALL}")
        self._status = value or ActorStatus.ACTIVE
    
    # Properties - Optional
    @property
    def allocation_percent(self) -> int | None:
        """Planned capacity allocation (0-100)."""
        return self._allocation_percent
    
    @allocation_percent.setter
    def allocation_percent(self, value: int | None):
        if value is not None and (value < 0 or value > 100):
            raise ValueError("Allocation percent must be between 0 and 100")
        self._allocation_percent = value
    
    @property
    def notes(self) -> str | None:
        """Notes about this actor's involvement."""
        return self._notes
    
    @notes.setter
    def notes(self, value: str | None):
        self._notes = value
    
    # Helper Methods
    def is_active(self) -> bool:
        """Check if actor is active."""
        return self._status == ActorStatus.ACTIVE
    
    def is_invited(self) -> bool:
        """Check if actor is invited but not yet active."""
        return self._status == ActorStatus.INVITED
    
    def is_removed(self) -> bool:
        """Check if actor has been removed."""
        return self._status == ActorStatus.REMOVED
