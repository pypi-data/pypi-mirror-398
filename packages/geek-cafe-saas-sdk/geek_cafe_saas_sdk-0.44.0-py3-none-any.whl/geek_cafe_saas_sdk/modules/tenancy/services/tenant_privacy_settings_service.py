"""
Geek Cafe, LLC
MIT License. See Project Root for the license information.

TenantPrivacySettingsService - Service for managing tenant privacy settings.

This service handles CRUD operations for TenantPrivacySettings, which are
stored as adjacent records to the Tenant model in DynamoDB.
"""

from typing import Dict, Any, Optional
from geek_cafe_saas_sdk.core.services.database_service import DatabaseService
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.core.service_errors import ValidationError, NotFoundError, AccessDeniedError
from geek_cafe_saas_sdk.lambda_handlers._base.decorators import service_method
from geek_cafe_saas_sdk.modules.tenancy.models.tenant_privacy_settings import TenantPrivacySettings


class TenantPrivacySettingsService(DatabaseService[TenantPrivacySettings]):
    """
    Service for tenant privacy settings management.
    
    Handles CRUD operations for privacy settings, which control user
    discoverability and profile visibility within and across tenants.
    """
    
    @service_method("get")
    def get(self, tenant_id: Optional[str] = None) -> ServiceResult[TenantPrivacySettings]:
        """
        Get privacy settings for a tenant.
        
        If settings don't exist, returns default settings (not persisted).
        
        Args:
            tenant_id: Tenant ID (defaults to current tenant from context)
            
        Returns:
            ServiceResult with TenantPrivacySettings
        """
        self.request_context.require_authentication()
        
        target_tenant_id = tenant_id or self.request_context.target_tenant_id
        
        if not self._can_access_tenant_settings(target_tenant_id):
            raise AccessDeniedError("You do not have access to this tenant's settings")
        
        settings = self._get_settings_by_tenant_id(target_tenant_id)
        
        if settings:
            return ServiceResult.success_result(settings)
        
        return ServiceResult.success_result(
            TenantPrivacySettings.default(target_tenant_id)
        )
    
    @service_method("create")
    def create(self, tenant_id: Optional[str] = None, **kwargs) -> ServiceResult[TenantPrivacySettings]:
        """
        Create privacy settings for a tenant.
        
        Args:
            tenant_id: Tenant ID (defaults to current tenant from context)
            **kwargs: Settings fields to set
            
        Returns:
            ServiceResult with created TenantPrivacySettings
        """
        self.request_context.require_authentication()
        
        target_tenant_id = tenant_id or self.request_context.target_tenant_id
        
        if not self._is_tenant_admin(target_tenant_id):
            raise AccessDeniedError("Only tenant administrators can create privacy settings")
        
        existing = self._get_settings_by_tenant_id(target_tenant_id)
        if existing:
            raise ValidationError(
                "Privacy settings already exist for this tenant. Use update instead.",
                "tenant_id"
            )
        
        settings = TenantPrivacySettings()
        settings.tenant_id = target_tenant_id
        
        self._apply_settings(settings, kwargs)
        
        settings.prep_for_save()
        return self._save_model(settings)
    
    @service_method("update")
    def update(self, tenant_id: Optional[str] = None, **kwargs) -> ServiceResult[TenantPrivacySettings]:
        """
        Update privacy settings for a tenant.
        
        Creates settings if they don't exist (upsert behavior).
        
        Args:
            tenant_id: Tenant ID (defaults to current tenant from context)
            **kwargs: Settings fields to update
            
        Returns:
            ServiceResult with updated TenantPrivacySettings
        """
        self.request_context.require_authentication()
        
        target_tenant_id = tenant_id or self.request_context.target_tenant_id
        
        if not self._is_tenant_admin(target_tenant_id):
            raise AccessDeniedError("Only tenant administrators can update privacy settings")
        
        settings = self._get_settings_by_tenant_id(target_tenant_id)
        old_settings = None
        
        if settings:
            old_settings = self._get_settings_by_tenant_id(target_tenant_id)
        else:
            settings = TenantPrivacySettings()
            settings.tenant_id = target_tenant_id
        
        self._apply_settings(settings, kwargs)
        
        settings.prep_for_save()
        return self._save_model(settings, old_model=old_settings)
    
    @service_method("delete")
    def delete(self, tenant_id: Optional[str] = None) -> ServiceResult[bool]:
        """
        Delete privacy settings for a tenant (resets to defaults).
        
        Args:
            tenant_id: Tenant ID (defaults to current tenant from context)
            
        Returns:
            ServiceResult with success boolean
        """
        self.request_context.require_authentication()
        
        target_tenant_id = tenant_id or self.request_context.target_tenant_id
        
        if not self._is_tenant_admin(target_tenant_id):
            raise AccessDeniedError("Only tenant administrators can delete privacy settings")
        
        settings = self._get_settings_by_tenant_id(target_tenant_id)
        
        if not settings:
            return ServiceResult.success_result(True)
        
        return self._delete_model(settings)
    
    @service_method("get_by_id")
    def get_by_id(self, id: str) -> ServiceResult[TenantPrivacySettings]:
        """
        Get privacy settings by tenant ID.
        
        For TenantPrivacySettings, the ID is the tenant_id since there's
        only one settings record per tenant.
        
        Args:
            id: Tenant ID
            
        Returns:
            ServiceResult with TenantPrivacySettings
        """
        return self.get(tenant_id=id)
    
    # Helper methods
    
    def _get_settings_by_tenant_id(self, tenant_id: str) -> Optional[TenantPrivacySettings]:
        """Get settings by tenant ID using direct key lookup."""
        query_model = TenantPrivacySettings()
        query_model.tenant_id = tenant_id
        
        result = self.dynamodb.get(
            table_name=self.table_name,
            model=query_model
        )
        
        # Check if item was found (result contains 'Item' key when found)
        if not result or "Item" not in result:
            return None
        
        settings = TenantPrivacySettings()
        settings.map(result.get("Item", {}))
        return settings
    
    def _can_access_tenant_settings(self, tenant_id: str) -> bool:
        """Check if current user can access tenant settings."""
        if self.request_context.is_platform_admin():
            return True
        return self.request_context.target_tenant_id == tenant_id
    
    def _is_tenant_admin(self, tenant_id: str) -> bool:
        """Check if current user is an admin for the tenant."""
        if self.request_context.is_platform_admin():
            return True
        if self.request_context.target_tenant_id != tenant_id:
            return False
        return self.request_context.is_tenant_admin()
    
    def _apply_settings(self, settings: TenantPrivacySettings, values: Dict[str, Any]) -> None:
        """Apply values to settings model."""
        allowed_fields = [
            "users_searchable_by_default",
            "default_profile_visibility",
            "allow_user_privacy_override",
            "show_email_by_default",
            "show_full_name_by_default",
            "show_avatar_by_default",
            "allow_cross_tenant_user_lookup",
            "allow_cross_tenant_user_search",
            "require_exact_email_for_lookup",
            "min_search_query_length",
        ]
        
        for field in allowed_fields:
            if field in values:
                setattr(settings, field, values[field])
