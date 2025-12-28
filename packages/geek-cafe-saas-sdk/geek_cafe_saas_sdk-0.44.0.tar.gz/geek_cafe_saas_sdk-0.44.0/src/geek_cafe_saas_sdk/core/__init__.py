# Core module for foundational classes and utilities

from .service_errors import ValidationError, AccessDeniedError, NotFoundError
from .service_result import ServiceResult
from .role_mapper import RoleMapper, IdentityRoleMapper, DictBasedRoleMapper
from .services_container import ServicesContainer
from .connection_pool import ConnectionPool, get_connection_pool, register_connection_factory, get_pooled_connection
from .request_context import RequestContext
from .system_request_context import SystemRequestContext
from .service_interfaces import (
    ISecurityService,
    IAuditService,
    IFeatureFlagService,
    IMetricsService,
    INotificationService,
    IStorageService,
    ICacheService
)
from .access import (
    AccessChecker,
    AccessLevel,
    AccessResult,
    IShareChecker,
    NoOpShareChecker,
    ResourceShareChecker,
)
from .tenant_settings import (
    TenantSettings,
    ITenantSettingsLoader,
    DefaultTenantSettingsLoader,
)

__all__ = [
    'ValidationError',
    'AccessDeniedError',
    'NotFoundError',
    'ServiceResult',
    'RoleMapper',
    'IdentityRoleMapper',
    'DictBasedRoleMapper',
    'ServicesContainer',
    'ConnectionPool',
    'get_connection_pool',
    'register_connection_factory',
    'get_pooled_connection',
    'RequestContext',
    'SystemRequestContext',
    'ISecurityService',
    'IAuditService',
    'IFeatureFlagService',
    'IMetricsService',
    'INotificationService',
    'IStorageService',
    'ICacheService',
    'AccessChecker',
    'AccessLevel',
    'AccessResult',
    'IShareChecker',
    'NoOpShareChecker',
    'ResourceShareChecker',
    'TenantSettings',
    'ITenantSettingsLoader',
    'DefaultTenantSettingsLoader',
]
