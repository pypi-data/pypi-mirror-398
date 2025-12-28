"""
Copyright 2024-2025 Geek Cafe, LLC
MIT License. See Project Root for the license information.

Permission Registry for extensible permission definitions.
Allows applications to register custom permissions and roles.
"""

from typing import Dict, List, Optional, Set
from dataclasses import dataclass
import threading


@dataclass
class PermissionDefinition:
    """Definition of a permission."""
    code: str  # "events:read"
    name: str  # "Read Events"
    description: str
    category: str  # "events"
    is_system: bool = True


@dataclass
class RoleDefinition:
    """Definition of a role."""
    code: str  # "tenant_admin"
    name: str  # "Tenant Administrator"
    description: str
    permissions: List[str]  # Permission codes
    scope: str = "tenant"  # "global" or "tenant"
    inherits_from: List[str] = None  # Role codes
    level: int = 0
    is_system: bool = True
    is_assignable: bool = True
    
    def __post_init__(self):
        if self.inherits_from is None:
            self.inherits_from = []


class PermissionRegistry:
    """
    Singleton registry for permissions and roles.
    
    Allows applications to register custom permissions and roles
    that extend the base system. Provides in-memory lookup for
    fast permission resolution.
    
    Thread-safe for concurrent access.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._permissions: Dict[str, PermissionDefinition] = {}
        self._roles: Dict[str, RoleDefinition] = {}
        self._categories: Set[str] = set()
        self._lock = threading.Lock()
        
        # Register default permissions and roles
        self._register_defaults()
        self._initialized = True
    
    def _register_defaults(self):
        """Register default system permissions and roles."""
        
        # Platform Permissions
        self.register_permission(PermissionDefinition(
            code="platform:admin",
            name="Platform Admin",
            description="Full system access across all tenants",
            category="platform",
            is_system=True
        ))
        
        self.register_permission(PermissionDefinition(
            code="platform:support",
            name="Platform Support",
            description="Read-only access across tenants for support",
            category="platform",
            is_system=True
        ))
        
        # Tenant Permissions
        self.register_permission(PermissionDefinition(
            code="tenant:admin",
            name="Tenant Admin",
            description="Full administrative access within tenant",
            category="tenant",
            is_system=True
        ))
        
        self.register_permission(PermissionDefinition(
            code="tenant:read",
            name="Read Tenant",
            description="View tenant information",
            category="tenant",
            is_system=True
        ))
        
        self.register_permission(PermissionDefinition(
            code="tenant:write",
            name="Write Tenant",
            description="Modify tenant settings",
            category="tenant",
            is_system=True
        ))
        
        # User Permissions
        self.register_permission(PermissionDefinition(
            code="users:read",
            name="Read Users",
            description="View users in tenant",
            category="users",
            is_system=True
        ))
        
        self.register_permission(PermissionDefinition(
            code="users:write",
            name="Manage Users",
            description="Create, update, delete users",
            category="users",
            is_system=True
        ))
        
        # Profile Permissions
        self.register_permission(PermissionDefinition(
            code="profile:read_own",
            name="Read Own Profile",
            description="View own profile",
            category="profile",
            is_system=True
        ))
        
        self.register_permission(PermissionDefinition(
            code="profile:write_own",
            name="Write Own Profile",
            description="Update own profile",
            category="profile",
            is_system=True
        ))
        
        # Event Permissions
        self.register_permission(PermissionDefinition(
            code="events:read",
            name="Read Events",
            description="View events",
            category="events",
            is_system=True
        ))
        
        self.register_permission(PermissionDefinition(
            code="events:write",
            name="Write Events",
            description="Create and update events",
            category="events",
            is_system=True
        ))
        
        self.register_permission(PermissionDefinition(
            code="events:write_own",
            name="Write Own Events",
            description="Create and update own events only",
            category="events",
            is_system=True
        ))
        
        self.register_permission(PermissionDefinition(
            code="events:delete",
            name="Delete Events",
            description="Delete events",
            category="events",
            is_system=True
        ))
        
        self.register_permission(PermissionDefinition(
            code="events:admin",
            name="Event Admin",
            description="Full event management",
            category="events",
            is_system=True
        ))
        
        # Chat Permissions
        self.register_permission(PermissionDefinition(
            code="chat:read",
            name="Read Chat",
            description="View chat messages",
            category="chat",
            is_system=True
        ))
        
        self.register_permission(PermissionDefinition(
            code="chat:write",
            name="Send Messages",
            description="Send chat messages",
            category="chat",
            is_system=True
        ))
        
        self.register_permission(PermissionDefinition(
            code="chat:admin",
            name="Chat Admin",
            description="Manage channels and messages",
            category="chat",
            is_system=True
        ))
        
        # Community Permissions
        self.register_permission(PermissionDefinition(
            code="communities:read",
            name="Read Communities",
            description="View communities",
            category="communities",
            is_system=True
        ))
        
        self.register_permission(PermissionDefinition(
            code="communities:write",
            name="Write Communities",
            description="Create and update communities",
            category="communities",
            is_system=True
        ))
        
        self.register_permission(PermissionDefinition(
            code="communities:write_own",
            name="Write Own Communities",
            description="Create and update own communities only",
            category="communities",
            is_system=True
        ))
        
        self.register_permission(PermissionDefinition(
            code="communities:admin",
            name="Community Admin",
            description="Full community management",
            category="communities",
            is_system=True
        ))
        
        # Analytics Permissions
        self.register_permission(PermissionDefinition(
            code="analytics:read",
            name="View Analytics",
            description="View analytics and reports",
            category="analytics",
            is_system=True
        ))
        
        # Subscription Permissions
        self.register_permission(PermissionDefinition(
            code="subscriptions:read",
            name="Read Subscriptions",
            description="View subscription information",
            category="subscriptions",
            is_system=True
        ))
        
        self.register_permission(PermissionDefinition(
            code="subscriptions:write",
            name="Manage Subscriptions",
            description="Update subscription and billing",
            category="subscriptions",
            is_system=True
        ))
        
        # Register default roles
        self._register_default_roles()
    
    def _register_default_roles(self):
        """Register default system roles."""
        
        # Platform Admin
        self.register_role(RoleDefinition(
            code="platform_admin",
            name="Platform Administrator",
            description="Full system access across all tenants",
            permissions=["platform:admin"],
            scope="platform",
            level=1000,
            is_system=True,
            is_assignable=True
        ))
        
        # Platform Support
        self.register_role(RoleDefinition(
            code="platform_support",
            name="Platform Support",
            description="Read-only access for customer support",
            permissions=["platform:support", "tenant:read", "users:read"],
            scope="platform",
            level=500,
            is_system=True,
            is_assignable=True
        ))
        
        # Tenant Admin
        self.register_role(RoleDefinition(
            code="tenant_admin",
            name="Tenant Administrator",
            description="Full administrative access within tenant",
            permissions=[
                "tenant:admin", "tenant:read", "tenant:write",
                "users:read", "users:write",
                "events:admin", "chat:admin", "communities:admin",
                "analytics:read", "subscriptions:read", "subscriptions:write"
            ],
            scope="tenant",
            level=100,
            is_system=True,
            is_assignable=True
        ))
        
        # Event Organizer
        self.register_role(RoleDefinition(
            code="tenant_organizer",
            name="Event Organizer",
            description="Enhanced event and group management",
            permissions=[
                "events:admin", "communities:admin", "chat:write",
                "profile:read_own", "profile:write_own"
            ],
            scope="tenant",
            level=50,
            is_system=True,
            is_assignable=True
        ))
        
        # Tenant User
        self.register_role(RoleDefinition(
            code="tenant_user",
            name="Tenant User",
            description="Standard user with basic permissions",
            permissions=[
                "events:read", "events:write_own",
                "communities:read", "communities:write_own",
                "chat:read", "chat:write",
                "profile:read_own", "profile:write_own"
            ],
            scope="tenant",
            level=10,
            is_system=True,
            is_assignable=True
        ))
        
        # Viewer
        self.register_role(RoleDefinition(
            code="tenant_viewer",
            name="Viewer",
            description="Read-only access to tenant resources",
            permissions=[
                "events:read", "communities:read", "chat:read",
                "profile:read_own"
            ],
            scope="tenant",
            level=1,
            is_system=True,
            is_assignable=True
        ))
    
    def register_permission(self, permission: PermissionDefinition):
        """
        Register a new permission.
        
        Args:
            permission: Permission definition to register
        """
        with self._lock:
            self._permissions[permission.code] = permission
            self._categories.add(permission.category)
    
    def register_role(self, role: RoleDefinition):
        """
        Register a new role.
        
        Args:
            role: Role definition to register
        """
        with self._lock:
            self._roles[role.code] = role
    
    def get_permission(self, code: str) -> Optional[PermissionDefinition]:
        """Get permission by code."""
        return self._permissions.get(code)
    
    def get_role(self, code: str) -> Optional[RoleDefinition]:
        """Get role by code."""
        return self._roles.get(code)
    
    def get_all_permissions(self) -> List[PermissionDefinition]:
        """Get all registered permissions."""
        return list(self._permissions.values())
    
    def get_all_roles(self) -> List[RoleDefinition]:
        """Get all registered roles."""
        return list(self._roles.values())
    
    def get_permissions_by_category(self, category: str) -> List[PermissionDefinition]:
        """Get all permissions in a category."""
        return [p for p in self._permissions.values() if p.category == category]
    
    def get_roles_by_scope(self, scope: str) -> List[RoleDefinition]:
        """Get all roles by scope (global or tenant)."""
        return [r for r in self._roles.values() if r.scope == scope]
    
    def resolve_role_permissions(self, role_code: str, resolved: Set[str] = None) -> Set[str]:
        """
        Resolve all permissions for a role, including inherited.
        
        Args:
            role_code: Role code to resolve
            resolved: Set of already resolved permissions (for recursion)
            
        Returns:
            Set of permission codes
        """
        if resolved is None:
            resolved = set()
        
        role = self.get_role(role_code)
        if not role:
            return resolved
        
        # Add direct permissions
        resolved.update(role.permissions)
        
        # Recursively add inherited permissions
        for inherited_role in role.inherits_from:
            self.resolve_role_permissions(inherited_role, resolved)
        
        return resolved
    
    def get_permissions_for_roles(self, role_codes: List[str]) -> List[str]:
        """
        Get all unique permissions for a list of roles.
        
        Args:
            role_codes: List of role codes
            
        Returns:
            List of unique permission codes
        """
        all_perms = set()
        for role_code in role_codes:
            all_perms.update(self.resolve_role_permissions(role_code))
        return list(all_perms)


# Global singleton instance
permission_registry = PermissionRegistry()
