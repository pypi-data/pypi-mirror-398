"""Host-User Relationship Service (Phase 2)."""

import datetime as dt
from typing import List
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.core.services.database_service import DatabaseService
from geek_cafe_saas_sdk.lambda_handlers._base.decorators import service_method
from geek_cafe_saas_sdk.core.service_errors import ValidationError, NotFoundError, AccessDeniedError
from geek_cafe_saas_sdk.modules.events.models import HostUserRelationship


class HostUserRelationshipService(DatabaseService[HostUserRelationship]):
    """Service for managing host-user relationships."""
    
    # Required abstract methods from DatabaseService
    @service_method("create")
    def create(self, **kwargs) -> ServiceResult[HostUserRelationship]:
        """Create method - delegates to request_connection()."""
        self.request_context.require_authentication()
        return self.request_connection(
            host_id=kwargs.get('host_id'),
            user_id=kwargs.get('user_id')
        )
    
    @service_method("get_by_id")
    def get_by_id(self, relationship_id: str) -> ServiceResult[HostUserRelationship]:
        """
        Get relationship by ID (host_id:user_id format).
        
        Security:
            - Requires authentication
            - Users can only view relationships they're part of
        """
        self.request_context.require_authentication()
        try:
            if ':' not in relationship_id:
                return ServiceResult.error_result("Invalid relationship_id format. Use 'host_id:user_id'", "VALIDATION_ERROR")
            
            host_id, user_id = relationship_id.split(':', 1)
            return self.get_relationship(host_id, user_id)
            
        except Exception as e:
            return self._handle_service_exception(e, 'get_by_id', relationship_id=relationship_id)
    
    @service_method("update")
    def update(self, relationship_id: str, updates: dict) -> ServiceResult[HostUserRelationship]:
        """
        Update relationship - mainly for notification preferences.
        
        Security:
            - Requires authentication
            - Only user can update their own relationships
        """
        self.request_context.require_authentication()
        requesting_user = self.request_context.target_user_id
        
        try:
            if ':' not in relationship_id:
                return ServiceResult.error_result("Invalid relationship_id format. Use 'host_id:user_id'", "VALIDATION_ERROR")
            
            host_id, user_id = relationship_id.split(':', 1)
            
            # Get existing relationship
            rel_result = self.get_relationship(host_id, user_id)
            if not rel_result.success:
                return rel_result
            
            relationship = rel_result.data
            
            # Authorization: only the user can update
            if requesting_user != user_id:
                raise AccessDeniedError("Can only update own relationships")
            
            # Update allowed fields
            if 'notification_preferences' in updates:
                relationship.notification_preferences = updates['notification_preferences']
            
            if 'notes' in updates:
                relationship.notes = updates['notes']
            
            relationship.updated_by_id = requesting_user
            relationship.prep_for_save()
            return self._save_model(relationship)
            
        except Exception as e:
            return self._handle_service_exception(e, 'update', relationship_id=relationship_id)
    
    @service_method("delete")
    def delete(self, relationship_id: str) -> ServiceResult[bool]:
        """Delete method - delegates to remove_connection()."""
        self.request_context.require_authentication()
        try:
            if ':' not in relationship_id:
                return ServiceResult.error_result("Invalid relationship_id format. Use 'host_id:user_id'", "VALIDATION_ERROR")
            
            host_id, user_id = relationship_id.split(':', 1)
            return self.remove_connection(user_id, host_id)
            
        except Exception as e:
            return self._handle_service_exception(e, 'delete', relationship_id=relationship_id)
    
    # Connection Management
    @service_method("request_connection")
    def request_connection(self, host_id: str, user_id: str) -> ServiceResult[HostUserRelationship]:
        """
        Host requests to connect with a user.
        
        Creates a pending relationship that user must approve.
        
        Security:
            - Requires authentication
            - host_id must match requesting user
        """
        self.request_context.require_authentication()
        requesting_user = self.request_context.target_user_id
        tenant_id = self.request_context.target_tenant_id
        
        try:
            # Authorization: must be the host making the request
            if requesting_user != host_id:
                raise AccessDeniedError("Can only request connections as yourself")
            
            # Check if relationship already exists
            existing_rel = self._get_relationship_internal(host_id, user_id)
            
            if existing_rel:
                if existing_rel.is_blocked():
                    # Silent - don't reveal user has blocked you
                    raise NotFoundError("User not found or unavailable")
                return ServiceResult.error_result("Connection already exists", "ALREADY_EXISTS")
            
            # Create pending relationship
            relationship = HostUserRelationship()
            relationship.tenant_id = tenant_id
            relationship.host_id = host_id
            relationship.user_id = user_id
            relationship.status = "pending"
            relationship.initiated_by = "host"
            relationship.initiated_at_utc_ts = dt.datetime.now(dt.UTC).timestamp()
            relationship.created_by_id = requesting_user
            relationship.owner_id = requesting_user
            
            relationship.prep_for_save()
            return self._save_model(relationship)
            
        except Exception as e:
            return self._handle_service_exception(e, 'request_connection', host_id=host_id, user_id=user_id)
    
    @service_method("approve_connection")
    def approve_connection(self, user_id: str, host_id: str) -> ServiceResult[HostUserRelationship]:
        """
        User approves a host's connection request.
        
        Security:
            - Requires authentication
            - user_id must match requesting user
        """
        self.request_context.require_authentication()
        requesting_user = self.request_context.target_user_id
        
        try:
            # Authorization: must be the user approving
            if requesting_user != user_id:
                raise AccessDeniedError("Can only approve connections to yourself")
            
            # Get pending relationship
            rel_result = self.get_relationship(host_id, user_id)
            if not rel_result.success:
                raise NotFoundError("Connection request not found")
            
            relationship = rel_result.data
            
            if not relationship.is_pending():
                return ServiceResult.error_result("Connection is not pending", "INVALID_STATE")
            
            # Approve connection
            relationship.status = "connected"
            relationship.connected_at_utc_ts = dt.datetime.now(dt.UTC).timestamp()
            relationship.updated_by_id = requesting_user
            
            relationship.prep_for_save()
            return self._save_model(relationship)
            
        except Exception as e:
            return self._handle_service_exception(e, 'approve_connection', user_id=user_id, host_id=host_id)
    
    @service_method("deny_connection")
    def deny_connection(self, user_id: str, host_id: str) -> ServiceResult[bool]:
        """
        User denies a host's connection request.
        
        Security:
            - Requires authentication
            - user_id must match requesting user
        """
        self.request_context.require_authentication()
        requesting_user = self.request_context.target_user_id
        
        try:
            # Authorization: must be the user denying
            if requesting_user != user_id:
                raise AccessDeniedError("Can only deny connections to yourself")
            
            # Get pending relationship
            rel_result = self.get_relationship(host_id, user_id)
            if not rel_result.success:
                return ServiceResult.success_result(True)  # Already gone
            
            relationship = rel_result.data
            
            if not relationship.is_pending():
                return ServiceResult.error_result("Connection is not pending", "INVALID_STATE")
            
            # Mark as removed
            relationship.status = "removed"
            relationship.removed_at_utc_ts = dt.datetime.now(dt.UTC).timestamp()
            relationship.updated_by_id = requesting_user
            
            relationship.prep_for_save()
            save_result = self._save_model(relationship)
            
            if save_result.success:
                return ServiceResult.success_result(True)
            return save_result
            
        except Exception as e:
            return self._handle_service_exception(e, 'deny_connection', user_id=user_id, host_id=host_id)
    
    # Blocking
    @service_method("block_host")
    def block_host(self, user_id: str, host_id: str, silent: bool = True) -> ServiceResult[HostUserRelationship]:
        """
        User blocks a host (silent by default).
        
        Silently blocked hosts cannot discover they're blocked.
        
        Security:
            - Requires authentication
            - user_id must match requesting user
        """
        self.request_context.require_authentication()
        requesting_user = self.request_context.target_user_id
        tenant_id = self.request_context.target_tenant_id
        
        try:
            # Authorization: must be the user blocking
            if requesting_user != user_id:
                raise AccessDeniedError("Can only block hosts from your own account")
            
            # Get or create relationship
            rel_result = self.get_relationship(host_id, user_id)
            
            if rel_result.success:
                relationship = rel_result.data
                # Already blocked?
                if relationship.is_blocked():
                    return ServiceResult.error_result("Host is already blocked", "ALREADY_BLOCKED")
            else:
                # Create new blocked relationship
                relationship = HostUserRelationship()
                relationship.tenant_id = tenant_id
                relationship.host_id = host_id
                relationship.user_id = user_id
                relationship.initiated_by = "user"
                relationship.initiated_at_utc_ts = dt.datetime.now(dt.UTC).timestamp()
                relationship.created_by_id = requesting_user
                relationship.owner_id = requesting_user
            
            # Block the host
            relationship.status = "blocked"
            relationship.blocked_at_utc_ts = dt.datetime.now(dt.UTC).timestamp()
            relationship.is_silent_block = silent
            relationship.updated_by_id = requesting_user
            
            relationship.prep_for_save()
            return self._save_model(relationship)
            
        except Exception as e:
            return self._handle_service_exception(e, 'block_host', user_id=user_id, host_id=host_id)
    
    @service_method("unblock_host")
    def unblock_host(self, user_id: str, host_id: str) -> ServiceResult[HostUserRelationship]:
        """
        User unblocks a host.
        
        Security:
            - Requires authentication
            - user_id must match requesting user
        """
        self.request_context.require_authentication()
        requesting_user = self.request_context.target_user_id
        
        try:
            # Authorization: must be the user unblocking
            if requesting_user != user_id:
                raise AccessDeniedError("Can only unblock hosts from your own account")
            
            # Get blocked relationship
            rel_result = self.get_relationship(host_id, user_id)
            if not rel_result.success:
                return ServiceResult.error_result("No relationship found to unblock", "NOT_FOUND")
            
            relationship = rel_result.data
            
            if not relationship.is_blocked():
                return ServiceResult.error_result("Host is not blocked", "NOT_BLOCKED")
            
            # Unblock - return to removed state
            relationship.status = "removed"
            relationship.removed_at_utc_ts = dt.datetime.now(dt.UTC).timestamp()
            relationship.updated_by_id = requesting_user
            
            relationship.prep_for_save()
            return self._save_model(relationship)
            
        except Exception as e:
            return self._handle_service_exception(e, 'unblock_host', user_id=user_id, host_id=host_id)
    
    # Private Helpers
    def _get_relationship_internal(self, host_id: str, user_id: str) -> HostUserRelationship | None:
        """Internal helper to get relationship. No authorization."""
        tenant_id = self.request_context.target_tenant_id
        
        # Create temp model to build the key
        temp_rel = HostUserRelationship()
        temp_rel.tenant_id = tenant_id
        temp_rel.host_id = host_id
        temp_rel.user_id = user_id
        
        # Get the primary key dict
        key = temp_rel.get_key("primary").key()
        
        # Get from database
        result = self.dynamodb.get(table_name=self.table_name, key=key)
        
        if not result or "Item" not in result:
            return None
        
        # Map to model
        relationship = HostUserRelationship()
        relationship.map(result["Item"])
        
        return relationship
    
    # Relationship Queries
    @service_method("get_relationship")
    def get_relationship(self, host_id: str, user_id: str) -> ServiceResult[HostUserRelationship]:
        """
        Get relationship between host and user.
        
        Security:
            - Requires authentication
            - Users can only view relationships they're part of
        """
        self.request_context.require_authentication()
        requesting_user = self.request_context.target_user_id
        tenant_id = self.request_context.target_tenant_id
        
        try:
            # Authorization: must be involved in the relationship
            if requesting_user not in [host_id, user_id]:
                raise AccessDeniedError("Can only view own relationships")
            
            # Get relationship
            relationship = self._get_relationship_internal(host_id, user_id)
            
            if not relationship:
                raise NotFoundError(f"Relationship not found")
            
            return ServiceResult.success_result(relationship)
            
        except Exception as e:
            return self._handle_service_exception(e, 'get_relationship', host_id=host_id, user_id=user_id)
    
    def is_user_blocked(self, host_id: str, user_id: str) -> bool:
        """
        Check if user has blocked host.
        
        Returns True if blocked, False otherwise.
        Does not require authorization (used by system).
        """
        try:
            relationship = self._get_relationship_internal(host_id, user_id)
            
            if not relationship:
                return False
            
            return relationship.is_blocked()
        except:
            return False
    
    def can_host_invite_user(self, host_id: str, user_id: str) -> tuple[bool, str]:
        """
        Check if host can invite user based on relationship.
        
        This checks ONLY the relationship status, not privacy settings.
        For full privacy + relationship check, use EventAttendeeService._can_host_invite_user()
        
        Does not require authorization (used by system).
        
        Returns:
            (can_invite: bool, reason: str)
        """
        try:
            relationship = self._get_relationship_internal(host_id, user_id)
            
            if not relationship:
                # No relationship exists
                return (False, "no_relationship")
            
            if relationship.is_blocked():
                return (False, "blocked")
            
            if relationship.is_connected():
                return (True, "connected")
            
            if relationship.is_pending():
                return (False, "pending")
            
            if relationship.is_removed():
                return (False, "removed")
            
            return (False, "unknown_status")
            
        except:
            return (False, "error")
    
    @service_method("get_user_connections")
    def get_user_connections(self, user_id: str, status: str = None) -> ServiceResult[List[HostUserRelationship]]:
        """
        Get all relationships for a user (hosts connected to this user).
        
        Security:
            - Requires authentication
            - user_id must match requesting user
        """
        self.request_context.require_authentication()
        requesting_user = self.request_context.target_user_id
        
        try:
            # Authorization: can only view own connections
            if requesting_user != user_id:
                raise AccessDeniedError("Can only view own connections")
            
            # Query by user (GSI1) using temp model
            tenant_id = self.request_context.target_tenant_id
            
            temp_rel = HostUserRelationship()
            temp_rel.tenant_id = tenant_id
            temp_rel.user_id = user_id
            
            if status:
                temp_rel.status = status
            
            # Query using GSI1
            results = self._query_by_index(temp_rel, "gsi1", limit=100)
            
            # Filter by status if provided (in case query returns more)
            if status:
                results = [r for r in results if r.status == status]
            
            return ServiceResult.success_result(results)
            
        except Exception as e:
            return self._handle_service_exception(e, 'get_user_connections', user_id=user_id)
    
    @service_method("get_host_connections")
    def get_host_connections(self, host_id: str, status: str = None) -> ServiceResult[List[HostUserRelationship]]:
        """
        Get all relationships for a host (users connected to this host).
        
        Security:
            - Requires authentication
            - host_id must match requesting user
        """
        self.request_context.require_authentication()
        requesting_user = self.request_context.target_user_id
        
        try:
            # Authorization: can only view own connections
            if requesting_user != host_id:
                raise AccessDeniedError("Can only view own connections")
            
            # Query by host using temp model
            tenant_id = self.request_context.target_tenant_id
            
            temp_rel = HostUserRelationship()
            temp_rel.tenant_id = tenant_id
            temp_rel.host_id = host_id
            
            # Query using primary index (partition key only gets all users for host)
            results = self._query_by_index(temp_rel, "primary", limit=100)
            
            # Filter by status if provided
            if status:
                results = [r for r in results if r.status == status]
            
            return ServiceResult.success_result(results)
            
        except Exception as e:
            return self._handle_service_exception(e, 'get_host_connections', host_id=host_id)
    
    # Notification Preferences
    @service_method("update_notification_preferences")
    def update_notification_preferences(
        self,
        user_id: str,
        host_id: str,
        preferences: dict
    ) -> ServiceResult[HostUserRelationship]:
        """
        Update notification preferences for this relationship.
        
        Security:
            - Requires authentication
            - user_id must match requesting user
        """
        self.request_context.require_authentication()
        requesting_user = self.request_context.target_user_id
        
        try:
            # Authorization: must be the user
            if requesting_user != user_id:
                raise AccessDeniedError("Can only update own notification preferences")
            
            # Get relationship
            rel_result = self.get_relationship(host_id, user_id)
            if not rel_result.success:
                raise NotFoundError("Relationship not found")
            
            relationship = rel_result.data
            
            # Update preferences
            relationship.notification_preferences = preferences
            relationship.updated_by_id = requesting_user
            
            relationship.prep_for_save()
            return self._save_model(relationship)
            
        except Exception as e:
            return self._handle_service_exception(e, 'update_notification_preferences', user_id=user_id, host_id=host_id)
    
    # Connection removal
    @service_method("remove_connection")
    def remove_connection(self, user_id: str, host_id: str) -> ServiceResult[bool]:
        """
        Remove/disconnect a relationship.
        
        Security:
            - Requires authentication
            - user_id must match requesting user
        """
        self.request_context.require_authentication()
        requesting_user = self.request_context.target_user_id
        
        try:
            # Authorization: must be the user
            if requesting_user != user_id:
                raise AccessDeniedError("Can only remove own connections")
            
            # Get relationship
            rel_result = self.get_relationship(host_id, user_id)
            if not rel_result.success:
                return ServiceResult.success_result(True)  # Already gone
            
            relationship = rel_result.data
            
            # Mark as removed
            relationship.status = "removed"
            relationship.removed_at_utc_ts = dt.datetime.now(dt.UTC).timestamp()
            relationship.updated_by_id = requesting_user
            
            relationship.prep_for_save()
            save_result = self._save_model(relationship)
            
            if save_result.success:
                return ServiceResult.success_result(True)
            return save_result
            
        except Exception as e:
            return self._handle_service_exception(e, 'remove_connection', user_id=user_id, host_id=host_id)
