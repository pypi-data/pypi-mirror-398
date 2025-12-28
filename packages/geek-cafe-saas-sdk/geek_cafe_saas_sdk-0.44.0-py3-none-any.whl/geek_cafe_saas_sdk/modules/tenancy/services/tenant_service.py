"""
Geek Cafe, LLC
MIT License.  See Project Root for the license information.

TenantService for managing tenant organizations.
"""

from typing import Dict, Any, Optional, List
from boto3_assist.dynamodb.dynamodb import DynamoDB
from geek_cafe_saas_sdk.core.services.database_service import DatabaseService
from geek_cafe_saas_sdk.modules.users.services import UserService
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.lambda_handlers._base.decorators import service_method
from geek_cafe_saas_sdk.core.service_errors import ValidationError, NotFoundError, AccessDeniedError
from geek_cafe_saas_sdk.modules.tenancy.models import Tenant
from geek_cafe_saas_sdk.modules.users.models import User
from geek_cafe_saas_sdk.modules.tenancy.models import Subscription
from geek_cafe_saas_sdk.utilities.cognito_utility import CognitoUtility
from geek_cafe_saas_sdk.utilities.environment_variables import EnvironmentVariables
import datetime as dt


class TenantService(DatabaseService[Tenant]):
    """
    Service for tenant management operations.
    
    Handles CRUD operations for tenants, including creating tenants with
    primary users, managing tenant status, and coordinating with subscriptions.
    """

    def __init__(self, *, dynamodb: DynamoDB = None, table_name: str = None,
                 user_service: UserService = None, cognito_utility: CognitoUtility = None,
                 user_pool_id: str = None, enable_cognito: bool = True, request_context: Optional[Dict[str, str]] = None):
        super().__init__(dynamodb=dynamodb, table_name=table_name, request_context=request_context)
        # User service for creating primary users
        self.user_service = user_service or UserService(
            dynamodb=dynamodb, table_name=table_name, request_context=request_context
        )
        # Cognito integration (optional for testing)
        self.cognito_utility = cognito_utility
        self.user_pool_id = user_pool_id or EnvironmentVariables.get_cognito_user_pool()
        self.enable_cognito = enable_cognito

    @service_method("create")


    def create(self, payload: Dict[str, Any]) -> ServiceResult[Tenant]:
        """
        Create a new tenant.
        
        Args:
            payload: Tenant data (name, status, plan_tier, etc.)
            
        Returns:
            ServiceResult with Tenant
            
        Security:
            - Requires authentication
        """
        self.request_context.require_authentication()
        tenant_id = self.request_context.target_tenant_id
        user_id = self.request_context.target_user_id
        try:
            # Validate required fields
            required_fields = ['name']
            self._validate_required_fields(payload, required_fields)

            # Create tenant instance
            tenant = Tenant().map(payload)
            tenant.tenant_id = tenant.id or tenant_id  # Self-referential
            tenant.user_id = user_id
            tenant.created_by_id = user_id

            # Set defaults
            if not tenant.status:
                tenant.status = "active"
            if not tenant.plan_tier:
                tenant.plan_tier = "free"

            # Prepare for save
            tenant.prep_for_save()

            # Save to database
            return self._save_model(tenant)

        except Exception as e:
            return self._handle_service_exception(e, 'create_tenant')

    def create_with_user(self, user_payload: Dict[str, Any], 
                        tenant_payload: Optional[Dict[str, Any]] = None,
                        temp_password: Optional[str] = None,
                        send_invitation: bool = False) -> ServiceResult[Dict[str, Any]]:
        """
        Create tenant with primary user atomically (signup flow).
        
        This is the main signup flow - creates a new tenant and primary admin user
        together. The user becomes the tenant's primary contact.
        
        If Cognito is enabled, also creates the Cognito user with custom attributes.
        
        Args:
            user_payload: User data (email, first_name, last_name, etc.)
            tenant_payload: Optional tenant data (name, etc.). If not provided,
                          tenant name is derived from user info.
            temp_password: Optional temporary password for Cognito user
            send_invitation: If True, sends Cognito invitation email
            
        Returns:
            ServiceResult with dict containing:
            {
                "tenant": Tenant,
                "user": User,
                "cognito_user": dict (if Cognito enabled),
                "temp_password": str (if auto-generated and Cognito enabled)
            }
        """
        try:
            # Validate user fields
            required_user_fields = ['email', 'first_name', 'last_name']
            self._validate_required_fields(user_payload, required_user_fields)

            # Prepare tenant data
            if tenant_payload is None:
                tenant_payload = {}
            
            # Generate tenant name from user if not provided
            if 'name' not in tenant_payload:
                first_name = user_payload.get('first_name', 'User')
                last_name = user_payload.get('last_name', 'Organization')
                tenant_payload['name'] = f"{first_name} {last_name}'s Organization"

            # Create tenant first
            tenant = Tenant().map(tenant_payload)
            tenant.prep_for_save()
            
            # Set self-referential tenant_id
            tenant.tenant_id = tenant.id
            
            # Set defaults
            if not tenant.status:
                tenant.status = "active"
            if not tenant.plan_tier:
                tenant.plan_tier = "free"
            
            # Create default features for free tier
            if not tenant.features:
                tenant.features = {
                    "chat": True,
                    "events": True,
                    "groups": True,
                    "analytics": False,
                    "api_access": False
                }

            # Create primary user
            user = User().map(user_payload)
            user.tenant_id = tenant.id
            user.prep_for_save()
            
            # Set user as creator of themselves
            user.user_id = user.id
            user.created_by_id = user.id
            
            # Grant tenant admin role
            if 'tenant_admin' not in user.roles:
                user.roles = ['tenant_admin']
            
            # Set user status as active (they're signing up, not invited)
            user.status = "active"
            user.activated_utc_ts = dt.datetime.now(dt.UTC).timestamp()

            # Link tenant to primary user
            tenant.primary_contact_user_id = user.id
            tenant.created_by_id = user.id
            tenant.user_id = user.id

            # Save both (in future, could use TransactWrite for atomicity)
            tenant_result = self._save_model(tenant)
            if not tenant_result.success:
                return ServiceResult(
                    success=False,
                    message=f"Failed to create tenant: {tenant_result.message}",
                    error_code="TENANT_CREATION_FAILED"
                )

            # Save user
            user_result = self.user_service._save_model(user)
            if not user_result.success:
                # TODO: Rollback tenant creation (or use TransactWrite)
                return ServiceResult(
                    success=False,
                    message=f"Failed to create user: {user_result.message}",
                    error_code="USER_CREATION_FAILED"
                )

            # Create Cognito user if enabled
            cognito_response = None
            returned_temp_password = None
            
            if self.enable_cognito and self.user_pool_id:
                try:
                    # Initialize Cognito utility if not provided
                    cognito = self.cognito_utility or CognitoUtility()
                    
                    # Store password for return (before it's used)
                    if not send_invitation:
                        returned_temp_password = temp_password
                    
                    # Create Cognito user with custom attributes
                    cognito_response = cognito.admin_create_user(
                        user_pool_id=self.user_pool_id,
                        temp_password=temp_password,
                        user=user,
                        send_invitation=send_invitation
                    )
                    
                    # Extract cognito username (sub) from response
                    if cognito_response and 'User' in cognito_response:
                        cognito_user = cognito_response['User']
                        user.cognito_user_name = cognito_user.get('Username')
                        
                        # Update user in DynamoDB with Cognito username
                        self.user_service._save_model(user)
                        
                except Exception as cognito_error:
                    # Cognito creation failed - should we rollback?
                    # For now, log error and return partial success
                    return ServiceResult(
                        success=False,
                        message=f"User created in DynamoDB but Cognito creation failed: {str(cognito_error)}",
                        error_code="COGNITO_CREATION_FAILED",
                        data={
                            "tenant": tenant,
                            "user": user,
                            "cognito_error": str(cognito_error)
                        }
                    )

            # Return successful result
            result_data = {
                "tenant": tenant,
                "user": user
            }
            
            if cognito_response:
                result_data["cognito_user"] = cognito_response
            
            if returned_temp_password:
                result_data["temp_password"] = returned_temp_password
            
            return ServiceResult(
                success=True,
                data=result_data
            )

        except Exception as e:
            return self._handle_service_exception(e, 'create_tenant_with_user')

    @service_method("get_by_id")
    def get_by_id(self, tenant_id: str) -> ServiceResult[Tenant]:
        """
        Get tenant by ID with access control.
        
        Args:
            tenant_id: Tenant ID to retrieve
            
        Returns:
            ServiceResult with Tenant
            
        Security:
            - Requires authentication
        """
        self.request_context.require_authentication()
        tenant_id = tenant_id or self.request_context.target_tenant_id
        try:
            if tenant_id != self.request_context.authenticated_tenant_id:
                # TODO: admin and sharing permissions
                raise AccessDeniedError("You don't have access to this tenant")

            tenant = self._get_model_by_id(tenant_id, Tenant)

            if not tenant:
                raise NotFoundError(f"Tenant with ID {tenant_id} not found")

            # Check if deleted
            if tenant.is_deleted():
                raise NotFoundError(f"Tenant with ID {tenant_id} not found")

            return ServiceResult.success_result(tenant)

        except Exception as e:
            return self._handle_service_exception(e, 'get_tenant',
                                                 tenant_id=tenant_id)

    @service_method("update")
    def update(self, tenant_id: str,
               payload: Dict[str, Any]) -> ServiceResult[Tenant]:
        """
        Update tenant information.
        
        Args:
            tenant_id: Tenant ID to update
            payload: Fields to update
            
        Returns:
            ServiceResult with updated Tenant
            
        Security:
            - Requires authentication
        """
        self.request_context.require_authentication()
        user_id = self.request_context.target_user_id
        try:
            # Get existing tenant
            get_result = self.get_by_id(tenant_id)
            if not get_result.success:
                return get_result

            tenant = get_result.data

            # Update fields from payload
            tenant.map(payload)
            tenant.updated_by_id = user_id
            tenant.modified_utc_ts = dt.datetime.now(dt.UTC).timestamp()
            tenant.version += 1

            # Save updated tenant
            return self._save_model(tenant)

        except Exception as e:
            return self._handle_service_exception(e, 'update_tenant',
                                                 tenant_id=tenant_id)

    @service_method("list_by_status")


    def list_by_status(self, status: str,
                      limit: int = 50) -> ServiceResult[List[Tenant]]:
        """
        List tenants by status (for admin queries).
        
        Args:
            status: Tenant status (active|inactive|archived)
            tenant_id: Requesting tenant ID
            user_id: Requesting user ID
            limit: Maximum number of results
            
        Returns:
            ServiceResult with list of Tenants
        """
        try:
            # TODO: Add admin check - only admins should list all tenants

            # Create temp tenant for GSI1 query
            temp_tenant = Tenant()
            temp_tenant.status = status

            result = self._query_by_index(
                temp_tenant,
                "gsi1",
                ascending=False,
                limit=limit
            )

            if not result.success:
                return result

            # Filter out deleted tenants
            active_tenants = [t for t in result.data if not t.is_deleted()]

            return ServiceResult.success_result(active_tenants)

        except Exception as e:
            return self._handle_service_exception(e, 'list_tenants_by_status',
                                                 status=status, tenant_id=tenant_id)

    @service_method("list_all")


    def list_all(self, limit: int = 50) -> ServiceResult[List[Tenant]]:
        """
        List all tenants sorted by name (for admin queries).
        
        Args:
            tenant_id: Requesting tenant ID
            user_id: Requesting user ID
            limit: Maximum number of results
            
        Returns:
            ServiceResult with list of Tenants
        """
        try:
            # TODO: Add admin check - only admins should list all tenants

            # Create temp tenant for GSI2 query
            temp_tenant = Tenant()
            temp_tenant.name = ""  # This will be overridden by GSI2 PK

            # Need to manually set GSI2 PK for "all tenants" query
            # This is a workaround for the query pattern
            
            # For now, query by active status as a proxy
            return self.list_by_status("active", tenant_id, user_id, limit)

        except Exception as e:
            return self._handle_service_exception(e, 'list_all_tenants',
                                                 tenant_id=tenant_id)

    @service_method("deactivate")


    def deactivate(self, tenant_id: str) -> ServiceResult[Tenant]:
        """
        Deactivate a tenant (soft disable).
        
        Sets tenant status to 'inactive'. Optionally can cascade to disable users.
        
        Args:
            tenant_id: Tenant ID to deactivate
            
        Returns:
            ServiceResult with updated Tenant
        """
        try:
            # Get security context for audit trail
            user_id = self.request_context.target_user_id
            
            # Get tenant (tenant/user validation handled by get_by_id)
            get_result = self.get_by_id(tenant_id)
            if not get_result.success:
                return get_result

            tenant = get_result.data

            # Deactivate
            tenant.deactivate()
            tenant.updated_by_id = user_id
            tenant.modified_utc_ts = dt.datetime.now(dt.UTC).timestamp()
            tenant.version += 1

            # Save
            save_result = self._save_model(tenant)
            
            # TODO: Cascade to users - disable all users in tenant
            # This would be done in a separate method or background job

            return save_result

        except Exception as e:
            return self._handle_service_exception(e, 'deactivate_tenant',
                                                 tenant_id=tenant_id)

    @service_method("activate")


    def activate(self, tenant_id: str) -> ServiceResult[Tenant]:
        """
        Activate a tenant.
        
        Sets tenant status to 'active'.
        
        Args:
            tenant_id: Tenant ID to activate
            
        Returns:
            ServiceResult with updated Tenant
        """
        try:
            # Get security context for audit trail
            user_id = self.request_context.target_user_id
            
            # Get tenant (tenant/user validation handled by get_by_id)
            get_result = self.get_by_id(tenant_id)
            if not get_result.success:
                return get_result

            tenant = get_result.data

            # Activate
            tenant.activate()
            tenant.updated_by_id = user_id
            tenant.modified_utc_ts = dt.datetime.now(dt.UTC).timestamp()
            tenant.version += 1

            # Save
            return self._save_model(tenant)

        except Exception as e:
            return self._handle_service_exception(e, 'activate_tenant',
                                                 tenant_id=tenant_id)

    @service_method("get_user_count")


    def get_user_count(self) -> ServiceResult[int]:
        """
        Get count of users in tenant.
        
        Args:
            tenant_id: Tenant ID
            user_id: Requesting user ID
            
        Returns:
            ServiceResult with user count
        """
        try:
            # Query users by tenant
            users_result = self.user_service.get_users_by_tenant(
                 limit=1000  # TODO: Handle pagination for large counts
            )

            if not users_result.success:
                return ServiceResult(
                    success=False,
                    error="Failed to count users",
                    error_code="USER_COUNT_FAILED"
                )

            # Count active users
            active_users = [u for u in users_result.data if not u.is_deleted() and u.is_active()]
            count = len(active_users)

            return ServiceResult.success_result(count)

        except Exception as e:
            return self._handle_service_exception(e, 'get_user_count',
                                                 tenant_id=tenant_id)

    @service_method("can_add_user")


    def can_add_user(self) -> ServiceResult[bool]:
        """
        Check if tenant can add another user (based on subscription limits).
        
        Returns:
            ServiceResult with boolean (True if can add, False if at limit)
        """
        try:
            # Get security context
            tenant_id = self.request_context.target_tenant_id
            
            # Get tenant (tenant/user validation handled by get_by_id)
            tenant_result = self.get_by_id(tenant_id)
            if not tenant_result.success:
                return tenant_result

            tenant = tenant_result.data

            # If no user limit, can always add
            if tenant.max_users is None:
                return ServiceResult.success_result(True)

            # Get current user count
            count_result = self.get_user_count()
            if not count_result.success:
                return count_result

            current_count = count_result.data

            # Check if at limit
            can_add = current_count < tenant.max_users

            return ServiceResult.success_result(can_add)

        except Exception as e:
            return self._handle_service_exception(e, 'can_add_user',
                                                 tenant_id=tenant_id)

    @service_method("delete")


    def delete(self, tenant_id: str) -> ServiceResult[bool]:
        """
        Soft delete tenant.
        
        Args:
            tenant_id: Tenant ID to delete
            
        Returns:
            ServiceResult with boolean (True if deleted)
        """
        try:
            # Get security context for audit trail
            user_id = self.request_context.target_user_id
            
            # Get tenant (tenant/user validation handled by get_by_id)
            get_result = self.get_by_id(tenant_id)
            if not get_result.success:
                return ServiceResult(success=False, message=get_result.message,
                                   error_code=get_result.error_code)

            tenant = get_result.data

            # Soft delete
            tenant.deleted_utc_ts = dt.datetime.now(dt.UTC).timestamp()
            tenant.deleted_by_id = user_id
            tenant.updated_by_id = user_id
            tenant.modified_utc_ts = dt.datetime.now(dt.UTC).timestamp()

            # Save
            save_result = self._save_model(tenant)
            if not save_result.success:
                return ServiceResult(success=False, message=save_result.message,
                                   error_code=save_result.error_code)

            return ServiceResult.success_result(True)

        except Exception as e:
            return self._handle_service_exception(e, 'delete_tenant',
                                                 tenant_id=tenant_id)
