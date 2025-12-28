"""
Geek Cafe, LLC
MIT License. See Project Root for the license information.

TenantSharingSettingsService - Service for managing tenant sharing settings.

This service handles CRUD operations for TenantSharingSettings, which are
stored as adjacent records to the Tenant model in DynamoDB.
"""

from typing import Dict, Any, Optional
from geek_cafe_saas_sdk.core.services.database_service import DatabaseService
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.core.service_errors import ValidationError, NotFoundError, AccessDeniedError
from geek_cafe_saas_sdk.lambda_handlers._base.decorators import service_method
from geek_cafe_saas_sdk.modules.tenancy.models.tenant_sharing_settings import TenantSharingSettings


class TenantSharingSettingsService(DatabaseService[TenantSharingSettings]):
    """
    Service for tenant sharing settings management.
    
    Handles CRUD operations for sharing settings, which control how
    resources can be shared within and across tenants.
    """
    
    @service_method("get")
    def get(self, tenant_id: Optional[str] = None) -> ServiceResult[TenantSharingSettings]:
        """
        Get sharing settings for a tenant.
        
        If settings don't exist, returns default settings (not persisted).
        
        Args:
            tenant_id: Tenant ID (defaults to current tenant from context)
            
        Returns:
            ServiceResult with TenantSharingSettings
        """
        self.request_context.require_authentication()
        
        # Use provided tenant_id or get from context
        target_tenant_id = tenant_id or self.request_context.target_tenant_id
        
        # Verify caller has access to this tenant's settings
        if not self._can_access_tenant_settings(target_tenant_id):
            raise AccessDeniedError("You do not have access to this tenant's settings")
        
        # Try to get existing settings
        settings = self._get_settings_by_tenant_id(target_tenant_id)
        
        if settings:
            return ServiceResult.success_result(settings)
        
        # Return defaults if no settings exist
        return ServiceResult.success_result(
            TenantSharingSettings.default(target_tenant_id)
        )
    
    @service_method("create")
    def create(self, tenant_id: Optional[str] = None, **kwargs) -> ServiceResult[TenantSharingSettings]:
        """
        Create sharing settings for a tenant.
        
        Args:
            tenant_id: Tenant ID (defaults to current tenant from context)
            **kwargs: Settings fields to set
            
        Returns:
            ServiceResult with created TenantSharingSettings
        """
        self.request_context.require_authentication()
        
        target_tenant_id = tenant_id or self.request_context.target_tenant_id
        
        # Only tenant admins can create settings
        if not self._is_tenant_admin(target_tenant_id):
            raise AccessDeniedError("Only tenant administrators can create sharing settings")
        
        # Check if settings already exist
        existing = self._get_settings_by_tenant_id(target_tenant_id)
        if existing:
            raise ValidationError(
                "Sharing settings already exist for this tenant. Use update instead.",
                "tenant_id"
            )
        
        # Create new settings
        settings = TenantSharingSettings()
        settings.tenant_id = target_tenant_id
        
        # Apply provided values
        self._apply_settings(settings, kwargs)
        
        # Save
        settings.prep_for_save()
        return self._save_model(settings)
    
    @service_method("update")
    def update(self, tenant_id: Optional[str] = None, **kwargs) -> ServiceResult[TenantSharingSettings]:
        """
        Update sharing settings for a tenant.
        
        Creates settings if they don't exist (upsert behavior).
        
        Args:
            tenant_id: Tenant ID (defaults to current tenant from context)
            **kwargs: Settings fields to update
            
        Returns:
            ServiceResult with updated TenantSharingSettings
        """
        self.request_context.require_authentication()
        
        target_tenant_id = tenant_id or self.request_context.target_tenant_id
        
        # Only tenant admins can update settings
        if not self._is_tenant_admin(target_tenant_id):
            raise AccessDeniedError("Only tenant administrators can update sharing settings")
        
        # Get existing or create new
        settings = self._get_settings_by_tenant_id(target_tenant_id)
        old_settings = None
        
        if settings:
            # Keep old for audit
            old_settings = self._get_settings_by_tenant_id(target_tenant_id)
        else:
            # Create new settings
            settings = TenantSharingSettings()
            settings.tenant_id = target_tenant_id
        
        # Apply updates
        self._apply_settings(settings, kwargs)
        
        # Save
        settings.prep_for_save()
        return self._save_model(settings, old_model=old_settings)
    
    @service_method("delete")
    def delete(self, tenant_id: Optional[str] = None) -> ServiceResult[bool]:
        """
        Delete sharing settings for a tenant (resets to defaults).
        
        Args:
            tenant_id: Tenant ID (defaults to current tenant from context)
            
        Returns:
            ServiceResult with success boolean
        """
        self.request_context.require_authentication()
        
        target_tenant_id = tenant_id or self.request_context.target_tenant_id
        
        # Only tenant admins can delete settings
        if not self._is_tenant_admin(target_tenant_id):
            raise AccessDeniedError("Only tenant administrators can delete sharing settings")
        
        # Get existing settings
        settings = self._get_settings_by_tenant_id(target_tenant_id)
        
        if not settings:
            # Already using defaults, nothing to delete
            return ServiceResult.success_result(True)
        
        # Delete the settings record
        return self._delete_model(settings)
    
    @service_method("get_by_id")
    def get_by_id(self, id: str) -> ServiceResult[TenantSharingSettings]:
        """
        Get sharing settings by tenant ID.
        
        For TenantSharingSettings, the ID is the tenant_id since there's
        only one settings record per tenant.
        
        Args:
            id: Tenant ID
            
        Returns:
            ServiceResult with TenantSharingSettings
        """
        return self.get(tenant_id=id)
    
    # Helper methods
    
    def _get_settings_by_tenant_id(self, tenant_id: str) -> Optional[TenantSharingSettings]:
        """
        Get settings by tenant ID using direct key lookup.
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            TenantSharingSettings if found, None otherwise
        """
        # Create a query model with the tenant_id to generate the correct key
        query_model = TenantSharingSettings()
        query_model.tenant_id = tenant_id
        
        # Get the primary key
        key = query_model.get_key("primary")
        
        # Query DynamoDB
        result = self.dynamodb.get(
            table_name=self.table_name,
            model=query_model
        )
        
        # Check if item was found (result contains 'Item' key when found)
        if not result or "Item" not in result:
            return None
        
        # Map result to model
        settings = TenantSharingSettings()
        settings.map(result.get("Item", {}))
        return settings
    
    def _can_access_tenant_settings(self, tenant_id: str) -> bool:
        """
        Check if current user can access tenant settings.
        
        Users can access settings for their own tenant.
        Platform admins can access any tenant's settings.
        
        Args:
            tenant_id: Tenant ID to check
            
        Returns:
            True if access allowed
        """
        # Platform admins can access any tenant
        if self.request_context.is_platform_admin():
            return True
        
        # Users can only access their own tenant's settings
        return self.request_context.target_tenant_id == tenant_id
    
    def _is_tenant_admin(self, tenant_id: str) -> bool:
        """
        Check if current user is an admin for the tenant.
        
        Args:
            tenant_id: Tenant ID to check
            
        Returns:
            True if user is tenant admin
        """
        # Platform admins have full access
        if self.request_context.is_platform_admin():
            return True
        
        # Must be in the same tenant
        if self.request_context.target_tenant_id != tenant_id:
            return False
        
        # Check if user is tenant admin
        return self.request_context.is_tenant_admin()
    
    def _apply_settings(self, settings: TenantSharingSettings, values: Dict[str, Any]) -> None:
        """
        Apply values to settings model.
        
        Only applies known/allowed fields.
        
        Args:
            settings: Settings model to update
            values: Values to apply
        """
        allowed_fields = [
            "allow_cross_tenant_sharing",
            "pending_invite_expiry_days",
            "require_email_verification",
            "notify_on_share",
            "notify_on_share_accepted",
            "notify_on_share_revoked",
            "max_shares_per_resource",
            "max_pending_invites_per_user",
            "allowed_permission_levels",
            "allow_public_links",
            "public_link_expiry_days",
            "require_password_for_public_links",
        ]
        
        for field in allowed_fields:
            if field in values:
                setattr(settings, field, values[field])
