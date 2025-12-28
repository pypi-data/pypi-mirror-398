"""
Access Control Module - Centralized access validation.

This module provides a unified interface for checking resource access
that considers ownership, sharing, and admin privileges.

Components:
- AccessChecker: Main class for checking access
- AccessLevel: Enum of permission levels
- AccessResult: Result of access check
- IShareChecker: Protocol for share checking (dependency injection)
- NoOpShareChecker: No-op implementation for testing

Usage:
    from geek_cafe_saas_sdk.core.access import AccessChecker, AccessLevel
    
    checker = AccessChecker(request_context=ctx, share_checker=share_checker)
    result = checker.check_access(
        resource_id=file.id,
        resource_owner_id=file.owner_id,
        resource_tenant_id=file.tenant_id,
        required_permission=AccessLevel.VIEW
    )
    
    if result.granted:
        # Access allowed
        pass

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from .access_checker import (
    AccessChecker,
    AccessLevel,
    AccessResult,
    IShareChecker,
    NoOpShareChecker,
)
from .resource_share_checker import ResourceShareChecker

__all__ = [
    "AccessChecker",
    "AccessLevel",
    "AccessResult",
    "IShareChecker",
    "NoOpShareChecker",
    "ResourceShareChecker",
]
