"""
Services Package
Contains all service classes for Geek Cafe Services

NOTE: Services have been reorganized into domain-driven structure.
Import services directly from their domain modules:
  - geek_cafe_saas_sdk.modules.users.services
  - geek_cafe_saas_sdk.modules.tenancy.services
  - geek_cafe_saas_sdk.modules.communities.services
  - geek_cafe_saas_sdk.modules.events.services
  - geek_cafe_saas_sdk.modules.messaging.services
  - geek_cafe_saas_sdk.modules.voting.services
  - geek_cafe_saas_sdk.modules.analytics.services

Audit Logging:
  DatabaseService now includes automatic audit logging when configured.
  See geek_cafe_saas_sdk.core.audit for audit logger implementations.
"""

from .database_service import DatabaseService
from .feature_flag_service import (
    FeatureFlagService,
    FeatureFlag,
    FeatureFlagTarget,
    get_feature_flag_service,
    is_feature_enabled
)

__all__ = [
    'DatabaseService',
    'FeatureFlagService',
    'FeatureFlag',
    'FeatureFlagTarget',
    'get_feature_flag_service',
    'is_feature_enabled'
]
