# User Service

from typing import Dict, Any, Optional, List
from boto3_assist.dynamodb.dynamodb import DynamoDB
from geek_cafe_saas_sdk.core.services.database_service import DatabaseService
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.core.service_errors import ValidationError, NotFoundError, AccessDeniedError
from geek_cafe_saas_sdk.lambda_handlers._base.decorators import service_method, require_params
from geek_cafe_saas_sdk.utilities.dynamodb_utils import build_projection_with_reserved_keywords
from geek_cafe_saas_sdk.modules.users.models import User
import datetime as dt


class UserService(DatabaseService[User]):


    @service_method("create")
    def create(self, **kwargs) -> ServiceResult[User]:
        """Create a new user. Security handled by _save_model."""
        # Validate required fields
        required_fields = ['email', 'first_name', 'last_name']
        self._validate_required_fields(kwargs, required_fields)
        
        # Get security context from request
        tenant_id = self.request_context.authenticated_tenant_id
        user_id = self.request_context.authenticated_user_id

        # Create user instance using map() approach
        user = User().map(kwargs)
        user.tenant_id = tenant_id
        user.user_id = user_id  # Set creator
        user.created_by_id = user_id

        # Prepare for save (sets ID and timestamps)
        user.prep_for_save()

        # Save to database
        return self._save_model(user)

    @service_method("get_by_id")
    def get_by_id(self, user_id: str) -> ServiceResult[User]:
        """Get user by ID. Security is automatic via _get_by_id."""
        user = self._get_by_id(user_id, User, include_deleted=True)

        
        if not user:
            raise NotFoundError(f"User with ID {user_id} not found")

        if user.is_deleted() and not self.request_context.is_admin():
            raise NotFoundError(f"User with ID {user_id} not found")

        return ServiceResult.success_result(user)

    @service_method("get_by_email")
    def get_by_email(self, email: str) -> ServiceResult[User]:
        """Get user by email using GSI1."""
        # Create a temporary user instance to get the GSI key
        temp_user = User()
        temp_user.email = email

        result = self._query_by_index(
            temp_user,
            "gsi1",
            ascending=False
        )

        if not result.success or not result.data:
            raise NotFoundError(f"User with email {email} not found")

        # Get the first (most recent) result
        user = result.data[0]

        # Check if deleted
        if user.is_deleted():
            raise NotFoundError(f"User with email {email} not found")

        # Security: verify user has access to this user's tenant
        tenant_id = self.request_context.authenticated_tenant_id
        if user.tenant_id != tenant_id:
            raise NotFoundError(f"User with email {email} not found")

        return ServiceResult.success_result(user)

    @service_method("get_users_by_tenant")
    def get_users_by_tenant(self, limit: int = 50) -> ServiceResult[List[User]]:
        """Get all users for a tenant using GSI2."""
        tenant_id = self.request_context.authenticated_tenant_id

        # Create a temporary user instance to get the GSI key
        temp_user = User()
        temp_user.tenant_id = tenant_id

        result = self._query_by_index(
            temp_user,
            "gsi2",
            ascending=False,  # Most recent first
            limit=limit
        )

        if not result.success:
            return result

        # Filter out deleted users and validate tenant access
        active_users = []
        for user in result.data:
            if not user.is_deleted() and user.tenant_id == tenant_id:
                active_users.append(user)

        return ServiceResult.success_result(active_users)

    @service_method("get_users_by_role")
    def get_users_by_role(self, role: str, limit: int = 50) -> ServiceResult[List[User]]:
        """Get users by role within a tenant using GSI3."""
        tenant_id = self.request_context.authenticated_tenant_id

        # Create a temporary user instance to get the GSI key
        temp_user = User()
        temp_user._roles = [role]  # Set the primary role

        result = self._query_by_index(
            temp_user,
            "gsi3",
            ascending=False,  # Most recent first
            limit=limit
        )

        if not result.success:
            return result

        # Filter out deleted users and validate tenant access
        active_users = []
        for user in result.data:
            if not user.is_deleted() and user.tenant_id == tenant_id and user.has_role(role):
                active_users.append(user)

        return ServiceResult.success_result(active_users)

    @service_method("restore_user")
    def restore_user(self, user_id: str) -> ServiceResult[User]:
        """Restore a soft-deleted user (admin only)."""
        tenant_id = self.request_context.authenticated_tenant_id
        authenticated_user_id = self.request_context.authenticated_user_id

        # Check permissions (admin only)
        if not self._is_admin_user(authenticated_user_id, tenant_id):
            raise AccessDeniedError("Access denied: insufficient permissions")

        # Get existing user (even if deleted) - skip security for admin restore
        user = self._get_by_id(user_id, User, include_deleted=True)

        if not user:
            raise NotFoundError(f"User with ID {user_id} not found")

        # Check if actually deleted
        if not user.is_deleted():
            return ServiceResult.success_result(user)  # Already active

        # Restore: clear deleted timestamp and metadata
        user.deleted_utc_ts = None
        user.deleted_by_id = None
        user.updated_by_id = authenticated_user_id
        user.prep_for_save()

        return self._save_model(user)

    @service_method("update")
    def update(self, user_id: str, updates: Dict[str, Any]) -> ServiceResult[User]:
        """Update user. Security is automatic via _get_by_id."""
        tenant_id = self.request_context.authenticated_tenant_id
        authenticated_user_id = self.request_context.authenticated_user_id

        # Get existing user with security check
        user = self._get_by_id(user_id, User)
        if not user:
            raise NotFoundError(f"User with ID {user_id} not found")

        # Additional check: only self or admin can update
        if not (authenticated_user_id == user_id or self._is_admin_user(authenticated_user_id, tenant_id)):
            raise AccessDeniedError("Access denied: insufficient permissions")

        # Prevent non-admins from updating roles
        if 'roles' in updates and not self._is_admin_user(authenticated_user_id, tenant_id):
            raise AccessDeniedError("Access denied: only admins can update roles")

        # Apply updates
        for field, value in updates.items():
            if hasattr(user, field) and field not in ['id', 'created_utc_ts', 'tenant_id', 'organizer_id']:
                if field == 'email':
                    user.email = value
                elif field == 'first_name':
                    user.first_name = value
                elif field == 'last_name':
                    user.last_name = value
                elif field == 'roles':
                    user.roles = value
                elif field == 'avatar':
                    user.avatar = value

        # Update metadata
        user.updated_by_id = user_id
        user.prep_for_save()  # Updates timestamp

        # Save updated user
        return self._save_model(user)

    @service_method("delete")
    def delete(self, user_id: str) -> ServiceResult[bool]:
        """Soft delete user. Security is automatic via _get_by_id."""
        tenant_id = self.request_context.authenticated_tenant_id
        authenticated_user_id = self.request_context.authenticated_user_id

        # Get existing user with security check (include deleted for idempotent delete)
        user = self._get_by_id(user_id, User, include_deleted=True)
        if not user:
            raise NotFoundError(f"User with ID {user_id} not found")

        # Check if already deleted - idempotent
        if user.is_deleted():
            return ServiceResult.success_result(True)

        # Check permissions (admin or self)
        if not (authenticated_user_id == user_id or self._is_admin_user(authenticated_user_id, tenant_id)):
            raise AccessDeniedError("Access denied: insufficient permissions")

        # Prevent deleting self
        if authenticated_user_id == user_id:
            raise ValidationError("Cannot delete your own account")

        # Soft delete: set deleted timestamp and metadata
        user.deleted_utc_ts = dt.datetime.now(dt.UTC).timestamp()
        user.deleted_by_id = authenticated_user_id
        user.prep_for_save()  # Updates timestamp

        # Save the updated user
        save_result = self._save_model(user)
        if save_result.success:
            return ServiceResult.success_result(True)
        else:
            return save_result

    def _is_admin_user(self, user_id: str, tenant_id: str) -> bool:
        """Check if user has admin role (placeholder - will be implemented when UserService is available)."""
        # For now, assume no admin privileges
        # This will be enhanced when we have user service integration
        return False
    
    @service_method("update_privacy_settings")
    def update_privacy_settings(
        self,
        user_id: str,
        profile_visibility: str = None,
        searchable_by_hosts: bool = None,
        show_full_name: bool = None,
        show_email: bool = None,
        show_avatar: bool = None
    ) -> ServiceResult[User]:
        """
        Update user privacy settings.
        
        Args:
            user_id: User ID to update privacy settings for
            profile_visibility: public | invite_only | private
            searchable_by_hosts: Whether hosts can find user in search
            show_full_name: Show full name vs initials
            show_email: Show email in profile
            show_avatar: Show avatar in profile
        
        Security:
            - Requires authentication
            - Users can only update their own privacy settings (or admins)
        """
        requesting_user = self.request_context.authenticated_user_id
        tenant_id = self.request_context.authenticated_tenant_id
        
        try:
            # Authorization: self or admin
            if requesting_user != user_id and not self._is_admin_user(requesting_user, tenant_id):
                raise AccessDeniedError("Can only update own privacy settings")
            
            # Get user with security check
            user = self._get_by_id(user_id, User)
            if not user:
                raise NotFoundError(f"User not found: {user_id}")
            
            # Update fields if provided
            if profile_visibility is not None:
                user.profile_visibility = profile_visibility  # Validates in setter
            
            if searchable_by_hosts is not None:
                user.searchable_by_hosts = searchable_by_hosts
            
            if show_full_name is not None:
                user.show_full_name = show_full_name
            
            if show_email is not None:
                user.show_email = show_email
            
            if show_avatar is not None:
                user.show_avatar = show_avatar
            
            # Set metadata
            user.privacy_updated_by_id = requesting_user
            user.updated_by_id = requesting_user
            
            # Save
            user.prep_for_save()
            return self._save_model(user)
            
        except Exception as e:
            return self._handle_service_exception(
                e, 'update_privacy_settings', user_id=user_id
            )
    
    @service_method("get_public_profile")
    def get_public_profile(self, user_id: str, requesting_host_id: str = None) -> ServiceResult[Dict]:
        """
        Get user's public profile respecting their privacy settings.
        
        Returns filtered user data based on:
        - Profile visibility setting
        - Individual field visibility (show_full_name, show_email, show_avatar)
        - Relationship with requesting host (Phase 2)
        
        Args:
            user_id: User to get profile for
            requesting_host_id: ID of host requesting profile (for Phase 2 relationship checking)
            
        Returns:
            Filtered user profile dictionary
            
        Security:
            - Requires authentication
            - Respects user privacy settings
        """
        try:
            user = self._get_by_id(user_id, User)
            if not user:
                raise NotFoundError(f"User not found: {user_id}")
            
            # Build public profile based on settings
            profile = {
                "user_id": user.id,
                "profile_visibility": user.profile_visibility,
            }
            
            # Add fields based on privacy settings
            if user.show_full_name:
                profile["name"] = user.full_name
            else:
                # Show first name + last initial
                if user.last_name:
                    profile["name"] = f"{user.first_name} {user.last_name[0]}."
                else:
                    profile["name"] = user.first_name
            
            if user.show_email:
                profile["email"] = user.email
            
            if user.show_avatar and user.avatar:
                profile["avatar"] = user.avatar
            
            # Add roles (always visible for now)
            profile["roles"] = user.roles
            
            return ServiceResult.success_result(profile)
            
        except Exception as e:
            return self._handle_service_exception(
                e, 'get_public_profile', user_id=user_id
            )
    
    # Host-User Relationship Management (Phase 2)
    def get_my_connections(self, status: Optional[str] = None) -> ServiceResult[List]:
        """
        Get current user's host connections.
        
        Convenience method that delegates to HostUserRelationshipService.
        
        Args:
            status: Optional filter by status (pending, connected, blocked, removed)
            
        Returns:
            ServiceResult with list of HostUserRelationship objects
            
        Security:
            - Requires authentication
            - Returns only connections for authenticated user
        """
        user_id = self.request_context.authenticated_user_id
        
        try:
            from geek_cafe_saas_sdk.modules.events.services import HostUserRelationshipService
            
            relationship_service = HostUserRelationshipService(
                dynamodb=self.dynamodb,
                table_name=self.table_name,
                request_context=self.request_context
            )
            
            # Delegate to relationship service and return result directly
            return relationship_service.get_user_connections(user_id, status)
            
        except Exception as e:
            return self._handle_service_exception(e, 'get_my_connections', status=status)
    
    def get_pending_connection_requests(self) -> ServiceResult[List]:
        """
        Get pending connection requests for current user.
        
        Convenience method that filters get_my_connections for pending status.
        
        Returns:
            ServiceResult with list of pending HostUserRelationship objects
            
        Security:
            - Requires authentication
            - Returns only pending requests for authenticated user
        """
        return self.get_my_connections(status="pending")
    
    def get_blocked_hosts(self) -> ServiceResult[List]:
        """
        Get list of hosts current user has blocked.
        
        Convenience method that filters get_my_connections for blocked status.
        
        Returns:
            ServiceResult with list of blocked HostUserRelationship objects
            
        Security:
            - Requires authentication
            - Returns only blocked relationships for authenticated user
        """
        return self.get_my_connections(status="blocked")
    
    # =========================================================================
    # User Discovery Methods (for sharing)
    # =========================================================================
    
    @service_method("search_users")
    def search_users(
        self,
        query: str,
        limit: int = 20
    ) -> ServiceResult[List[Dict[str, Any]]]:
        """
        Search for users within the same tenant by name or email.
        
        Respects user privacy settings:
        - Only returns users with searchable_by_hosts=True
        - Only returns users with profile_visibility != 'private'
        - Returns limited profile info based on user settings
        
        Args:
            query: Search query (name or email prefix, min 2 chars)
            limit: Maximum number of results (default: 20, max: 50)
            
        Returns:
            ServiceResult with list of user profile dicts
        """
        self.request_context.require_authentication()
        
        tenant_id = self.request_context.authenticated_tenant_id
        requesting_user_id = self.request_context.authenticated_user_id
        
        # Validate query
        if not query or len(query.strip()) < 2:
            raise ValidationError(
                "Search query must be at least 2 characters",
                "query"
            )
        
        query = query.strip().lower()
        limit = min(limit, 50)  # Cap at 50
        
        # Get all users in tenant
        result = self.get_users_by_tenant(limit=200)  # Get more to filter
        
        if not result.success:
            return result
        
        # Filter and search
        matching_users = []
        
        for user in result.data:
            # Skip self
            if user.id == requesting_user_id:
                continue
            
            # Skip non-searchable users
            if not user.searchable_by_hosts:
                continue
            
            # Skip private profiles
            if user.profile_visibility == "private":
                continue
            
            # Check if query matches name or email
            full_name = user.full_name.lower() if user.full_name else ""
            email = user.email.lower() if user.email else ""
            
            if query in full_name or query in email:
                # Build profile based on privacy settings
                profile = self._build_search_result_profile(user)
                matching_users.append(profile)
                
                if len(matching_users) >= limit:
                    break
        
        return ServiceResult.success_result(matching_users)
    
    @service_method("lookup_user_by_email")
    def lookup_user_by_email(
        self,
        email: str,
        cross_tenant: bool = False
    ) -> ServiceResult[Optional[Dict[str, Any]]]:
        """
        Look up a user by exact email address.
        
        Used for sharing - returns minimal info if user exists.
        
        Args:
            email: Exact email address to look up
            cross_tenant: If True, search across all tenants (requires privacy check)
            
        Returns:
            ServiceResult with user info dict or None if not found
            Dict contains: exists, user_id, display_name (if allowed)
        """
        self.request_context.require_authentication()
        
        if not email:
            raise ValidationError("email is required", "email")
        
        email = email.lower().strip()
        
        try:
            # Use existing get_by_email which uses GSI1
            result = self.get_by_email(email)
            
            if not result.success:
                # User not found
                return ServiceResult.success_result({
                    "exists": False,
                    "user_id": None,
                    "display_name": None
                })
            
            user = result.data
            
            # Check cross-tenant access
            if not cross_tenant:
                if user.tenant_id != self.request_context.authenticated_tenant_id:
                    # User exists but in different tenant - don't reveal
                    return ServiceResult.success_result({
                        "exists": False,
                        "user_id": None,
                        "display_name": None
                    })
            
            # Check privacy - don't reveal private users
            if user.profile_visibility == "private":
                return ServiceResult.success_result({
                    "exists": False,
                    "user_id": None,
                    "display_name": None
                })
            
            # Build response
            display_name = None
            if user.show_full_name:
                display_name = user.full_name
            elif user.first_name:
                display_name = f"{user.first_name} {user.last_name[0]}." if user.last_name else user.first_name
            
            return ServiceResult.success_result({
                "exists": True,
                "user_id": user.id,
                "display_name": display_name,
                "tenant_id": user.tenant_id if cross_tenant else None
            })
            
        except NotFoundError:
            return ServiceResult.success_result({
                "exists": False,
                "user_id": None,
                "display_name": None
            })
    
    def _build_search_result_profile(self, user: User) -> Dict[str, Any]:
        """Build a search result profile respecting privacy settings."""
        profile = {
            "user_id": user.id,
            "tenant_id": user.tenant_id,
        }
        
        # Name based on settings
        if user.show_full_name:
            profile["display_name"] = user.full_name
        else:
            if user.last_name:
                profile["display_name"] = f"{user.first_name} {user.last_name[0]}."
            else:
                profile["display_name"] = user.first_name
        
        # Email only if allowed
        if user.show_email:
            profile["email"] = user.email
        
        # Avatar only if allowed
        if user.show_avatar and user.avatar:
            profile["avatar"] = user.avatar
        
        return profile
