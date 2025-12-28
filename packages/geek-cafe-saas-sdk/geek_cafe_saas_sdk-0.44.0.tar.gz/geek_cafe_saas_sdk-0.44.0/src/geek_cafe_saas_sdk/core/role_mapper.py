"""
Copyright 2024-2025 Geek Cafe
MIT License

Role Mapper Interface

Provides a standard interface for mapping external role names to internal role codes.
This is useful when integrating with existing authorization systems that use different
role naming conventions.

Example Usage:
    class AcmeRoleMapper(RoleMapper):
        '''Maps Acme Corp roles to internal role codes.'''
        
        ROLE_MAPPING = {
            "acme:admin": "tenant_admin",
            "acme:user": "tenant_user",
            "acme:manager": "tenant_organizer",
        }
        
        def map_role(self, external_role: str) -> str:
            if external_role not in self.ROLE_MAPPING:
                raise ValueError(f"Unknown role: {external_role}")
            return self.ROLE_MAPPING[external_role]
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class RoleMapper(ABC):
    """
    Abstract base class for mapping external role names to internal role codes.
    
    When integrating with existing systems, you may need to map their role names
    to the standard role codes used by this SDK. Implement this interface to
    provide that mapping.
    
    Standard Internal Role Codes:
        - "platform_admin": Platform-level administrator (highest privilege)
        - "tenant_admin": Tenant-level administrator
        - "tenant_organizer": Tenant organizer (can manage resources)
        - "tenant_user": Regular tenant user
    
    Example:
        >>> mapper = AcmeRoleMapper()
        >>> internal_role = mapper.map_role("acme:admin")
        >>> print(internal_role)  # "tenant_admin"
    """
    
    @abstractmethod
    def map_role(self, external_role: str) -> str:
        """
        Map a single external role name to an internal role code.
        
        Args:
            external_role: The role name from the external system
            
        Returns:
            The internal role code (e.g., "tenant_admin", "tenant_user")
            
        Raises:
            ValueError: If the role cannot be mapped
            
        Example:
            >>> mapper.map_role("acme:admin")
            "tenant_admin"
        """
        pass
    
    @abstractmethod
    def map_roles(self, external_roles: List[str]) -> List[str]:
        """
        Map multiple external role names to internal role codes.
        
        Args:
            external_roles: List of role names from the external system
            
        Returns:
            List of internal role codes
            
        Raises:
            ValueError: If any role cannot be mapped
            
        Example:
            >>> mapper.map_roles(["acme:admin", "acme:user"])
            ["tenant_admin", "tenant_user"]
        """
        pass
    
    @abstractmethod
    def reverse_map(self, internal_role: str) -> str:
        """
        Map an internal role code back to an external role name.
        
        This is useful when you need to display roles to users in their
        familiar format, or when communicating with external systems.
        
        Args:
            internal_role: The internal role code
            
        Returns:
            The external role name
            
        Raises:
            ValueError: If the internal role cannot be reverse mapped
            
        Example:
            >>> mapper.reverse_map("tenant_admin")
            "acme:admin"
        """
        pass


class IdentityRoleMapper(RoleMapper):
    """
    Default role mapper that returns roles unchanged.
    
    Use this when your external role names already match the internal role codes,
    or when you're building a greenfield application using the standard role codes.
    
    Example:
        >>> mapper = IdentityRoleMapper()
        >>> mapper.map_role("tenant_admin")
        "tenant_admin"
    """
    
    def map_role(self, external_role: str) -> str:
        """Return the role unchanged."""
        return external_role
    
    def map_roles(self, external_roles: List[str]) -> List[str]:
        """Return all roles unchanged."""
        return external_roles.copy()
    
    def reverse_map(self, internal_role: str) -> str:
        """Return the role unchanged."""
        return internal_role


class DictBasedRoleMapper(RoleMapper):
    """
    Convenience role mapper that uses a dictionary for mapping.
    
    This is a simple implementation that's suitable for most use cases.
    Just provide a dictionary mapping external roles to internal roles.
    
    Args:
        role_mapping: Dictionary mapping external role names to internal role codes
        
    Example:
        >>> mapping = {
        ...     "acme:global:admin": "platform_admin",
        ...     "acme:tenant:admin": "tenant_admin",
        ...     "acme:tenant:user": "tenant_user",
        ... }
        >>> mapper = DictBasedRoleMapper(mapping)
        >>> mapper.map_role("acme:tenant:admin")
        "tenant_admin"
    """
    
    def __init__(self, role_mapping: Dict[str, str]):
        """
        Initialize with a role mapping dictionary.
        
        Args:
            role_mapping: Dict mapping external role names to internal role codes
        """
        self._role_mapping = role_mapping
        self._reverse_mapping = {v: k for k, v in role_mapping.items()}
    
    def map_role(self, external_role: str) -> str:
        """Map external role to internal role code."""
        if external_role not in self._role_mapping:
            raise ValueError(
                f"Unknown external role: {external_role}. "
                f"Known roles: {list(self._role_mapping.keys())}"
            )
        return self._role_mapping[external_role]
    
    def map_roles(self, external_roles: List[str]) -> List[str]:
        """Map multiple external roles to internal role codes."""
        return [self.map_role(role) for role in external_roles]
    
    def reverse_map(self, internal_role: str) -> str:
        """Map internal role code back to external role name."""
        if internal_role not in self._reverse_mapping:
            raise ValueError(
                f"Unknown internal role: {internal_role}. "
                f"Known roles: {list(self._reverse_mapping.keys())}"
            )
        return self._reverse_mapping[internal_role]
