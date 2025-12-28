# Event Attendee Service

from typing import Dict, Any, Optional, List
from boto3_assist.dynamodb.dynamodb import DynamoDB
from geek_cafe_saas_sdk.core.services.database_service import DatabaseService
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.lambda_handlers._base.decorators import service_method
from geek_cafe_saas_sdk.core.service_errors import ValidationError, NotFoundError, AccessDeniedError
from geek_cafe_saas_sdk.modules.events.models import EventAttendee, Event
from geek_cafe_saas_sdk.utilities.dynamodb_utils import build_projection_with_reserved_keywords
import datetime as dt


class EventAttendeeService(DatabaseService[EventAttendee]):
    """Service for EventAttendee database operations (RSVP tracking, invitations, check-in)."""

    def _can_host_invite_user(self, host_user_id: str, target_user_id: str) -> tuple[bool, str]:
        """
        Check if host can invite target user based on privacy settings AND relationships.
        
        Phase 1: Basic visibility checks (public, invite_only, private)
        Phase 2: Relationship and blocking enforcement (ACTIVE)
        
        Args:
            host_user_id: User attempting to invite
            target_user_id: User being invited
            
        Returns:
            (can_invite: bool, reason: str)
            reason can be: "public", "relationship_connected", "user_private", "blocked", 
                          "no_relationship", "privacy_restricted", "no_privacy_data"
        """
        from geek_cafe_saas_sdk.modules.users.services import UserService
        from geek_cafe_saas_sdk.modules.events.services import HostUserRelationshipService
        
        # Get user's privacy settings
        user_service = UserService(
            dynamodb=self.dynamodb,
            table_name=self.table_name,
            request_context=self.request_context
        )
        
        user_result = user_service.get_by_id(target_user_id)
        if not user_result.success:
            # User not found in database
            # For backwards compatibility: allow if user doesn't have privacy settings yet
            # This handles legacy data and test scenarios
            return (True, "no_privacy_data")
        
        user = user_result.data
        
        # Check if user has privacy fields (backwards compatibility)
        if not hasattr(user, 'profile_visibility') or not hasattr(user, 'searchable_by_hosts'):
            # No privacy fields = legacy user, allow invitation
            return (True, "no_privacy_data")
        
        # PHASE 2: Check for blocking (silent - happens first)
        relationship_service = HostUserRelationshipService(
            dynamodb=self.dynamodb,
            table_name=self.table_name,
            request_context=self.request_context
        )
        
        if relationship_service.is_user_blocked(host_user_id, target_user_id):
            # Silent block - return "not found" to preserve privacy
            return (False, "user_private")
        
        # Check privacy visibility
        if user.is_private() and not user.searchable_by_hosts:
            # Private users who are not searchable cannot be invited
            return (False, "user_private")
        
        # Public users can always be invited (unless blocked, which we already checked)
        if user.is_public():
            return (True, "public")
        
        # PHASE 2: For invite_only users, check relationship
        if user.is_invite_only():
            can_invite, reason = relationship_service.can_host_invite_user(host_user_id, target_user_id)
            
            if can_invite and reason == "connected":
                return (True, "relationship_connected")
            else:
                # No relationship = cannot invite invite_only user
                return (False, "no_relationship")
        
        return (False, "privacy_restricted")
    

    # Required abstract methods from DatabaseService
    @service_method("create")
    def create(self, **kwargs) -> ServiceResult[EventAttendee]:
        """Create method - delegates to invite() for EventAttendee.
        
        Security:
            - Requires authentication
        """
        self.request_context.require_authentication()
        user_id = self.request_context.target_user_id
        
        if 'event_id' not in kwargs:
            return ServiceResult.error_result("event_id is required", "VALIDATION_ERROR")
        
        event_id = kwargs.pop('event_id')
        invited_by = kwargs.pop('invited_by_user_id', user_id)
        
        return self.invite(
            event_id=event_id,
            user_id=kwargs.pop('user_id', user_id),
            invited_by_user_id=invited_by,
            **kwargs
        )

    @service_method("get_by_id")
    def get_by_id(self, attendee_id: str) -> ServiceResult[EventAttendee]:
        """Get method - attendee_id should be in format 'event_id:user_id'.
        
        Security:
            - Requires authentication
        """
        self.request_context.require_authentication()
        try:
            if ':' in attendee_id:
                event_id, attendee_user_id = attendee_id.split(':', 1)
            else:
                return ServiceResult.error_result("Invalid attendee_id format. Use 'event_id:user_id'", "VALIDATION_ERROR")
            
            return self.get_attendee(event_id, attendee_user_id)
        except Exception as e:
            return self._handle_service_exception(e, 'get_by_id', attendee_id=attendee_id)

    @service_method("update")
    def update(self, attendee_id: str, updates: Dict[str, Any]) -> ServiceResult[EventAttendee]:
        """Update method - updates attendee record.
        
        Security:
            - Requires authentication
        """
        self.request_context.require_authentication()
        user_id = self.request_context.target_user_id
        try:
            if ':' in attendee_id:
                event_id, attendee_user_id = attendee_id.split(':', 1)
            else:
                return ServiceResult.error_result("Invalid attendee_id format. Use 'event_id:user_id'", "VALIDATION_ERROR")
            
            # Get existing attendee
            result = self.get_attendee(event_id, attendee_user_id)
            if not result.success:
                return result
            
            attendee = result.data
            
            # Update fields
            for key, value in updates.items():
                if hasattr(attendee, key):
                    setattr(attendee, key, value)
            
            attendee.updated_by_id = user_id
            attendee.prep_for_save()
            return self._save_model(attendee)
            
        except Exception as e:
            return self._handle_service_exception(e, 'update', attendee_id=attendee_id)

    @service_method("delete")
    def delete(self, attendee_id: str) -> ServiceResult[bool]:
        """Delete method - soft deletes attendee.
        
        Security:
            - Requires authentication
        """
        self.request_context.require_authentication()
        try:
            if ':' in attendee_id:
                event_id, attendee_user_id = attendee_id.split(':', 1)
            else:
                return ServiceResult.error_result("Invalid attendee_id format. Use 'event_id:user_id'", "VALIDATION_ERROR")
            
            return self.remove_attendee(event_id, attendee_user_id)
            
        except Exception as e:
            return self._handle_service_exception(e, 'delete', attendee_id=attendee_id)

    @service_method("invite")
    def invite(self, event_id: str, **kwargs) -> ServiceResult[EventAttendee]:
        """
        Invite a user to an event (with privacy checks).
        
        Args:
            event_id: Event ID
            invitee_user_id: User ID to invite (optional, defaults to authenticated user)
            user_id: Alias for invitee_user_id (for backward compatibility)
            **kwargs: Additional fields (role, registration_data, etc.)
            
        Security:
            - Requires authentication
            - Respects user privacy settings
            - Inviter is determined from request_context
        """
        self.request_context.require_authentication()
        tenant_id = self.request_context.target_tenant_id
        invited_by_user_id = self.request_context.target_user_id
        
        # Get invitee user_id from kwargs (support both parameter names)
        invitee_user_id = kwargs.pop('invitee_user_id', None) or kwargs.pop('user_id', None) or invited_by_user_id
        
        # Privacy Check (Phase 1)
        try:
            can_invite, reason = self._can_host_invite_user(invited_by_user_id, invitee_user_id)
            if not can_invite:
                if reason == "user_private":
                    # Don't reveal user exists - privacy-preserving error
                    raise NotFoundError("User not found or unavailable")
                elif reason == "user_not_found":
                    raise NotFoundError("User not found")
                else:
                    raise AccessDeniedError(f"Cannot invite user: {reason}")
        except (NotFoundError, AccessDeniedError):
            raise  # Re-raise these specific errors
        except Exception as e:
            # Catch any other errors from privacy check
            return self._handle_service_exception(e, 'invite', event_id=event_id)
        
        # Check if already invited
        existing = self.get_attendee(event_id, invitee_user_id)
        if existing.success:
            return ServiceResult.error_result("User is already invited to this event", "ALREADY_INVITED")

        # Create attendee record
        attendee = EventAttendee()
        attendee.event_id = event_id
        attendee.user_id = invitee_user_id
        attendee.tenant_id = tenant_id
        attendee.rsvp_status = kwargs.get('rsvp_status', 'invited')
        attendee.role = kwargs.get('role', 'attendee')
        attendee.invited_at_utc_ts = dt.datetime.now(dt.UTC).timestamp()
        attendee.invited_by_user_id = kwargs.pop('invited_by_user_id', invited_by_user_id)
        attendee.created_by_id = invited_by_user_id
        attendee.owner_id = invited_by_user_id

        # Optional fields
        if 'registration_data' in kwargs:
            attendee.registration_data = kwargs['registration_data']
        if 'registration_notes' in kwargs:
            attendee.registration_notes = kwargs['registration_notes']
        if 'notification_preferences' in kwargs:
            attendee.notification_preferences = kwargs['notification_preferences']

        attendee.prep_for_save()
        return self._save_model(attendee)

    def update_rsvp(self, event_id: str, user_id: str,
                    rsvp_status: str, **kwargs) -> ServiceResult[EventAttendee]:
        """
        Update RSVP status for an attendee.
        
        Args:
            event_id: Event ID
            user_id: User ID
            rsvp_status: New RSVP status (accepted, declined, tentative)
            **kwargs: Additional fields (plus_one_count, etc.)
            
        Security:
            - Requires authentication
        """
        self.request_context.require_authentication()
        try:
            # Validate status
            if rsvp_status not in ['accepted', 'declined', 'tentative', 'wait_list']:
                raise ValidationError(f"Invalid RSVP status: {rsvp_status}")

            # Get existing attendee
            result = self.get_attendee(event_id, user_id)
            if not result.success:
                raise NotFoundError(f"Attendee not found for event {event_id}")

            attendee = result.data
            old_status = attendee.rsvp_status

            # Update status
            attendee.rsvp_status = rsvp_status
            attendee.responded_at_utc_ts = dt.datetime.now(dt.UTC).timestamp()
            attendee.updated_by_id = user_id

            # Update optional fields
            if 'plus_one_count' in kwargs:
                attendee.plus_one_count = kwargs['plus_one_count']
            if 'plus_one_names' in kwargs:
                attendee.plus_one_names = kwargs['plus_one_names']
            if 'registration_data' in kwargs:
                attendee.registration_data = kwargs['registration_data']
            if 'registration_notes' in kwargs:
                attendee.registration_notes = kwargs['registration_notes']

            attendee.prep_for_save()
            return self._save_model(attendee)

        except Exception as e:
            return self._handle_service_exception(e, 'update_rsvp', event_id=event_id, user_id=user_id)

    @service_method("add_host")
    def add_host(self, event_id: str, **kwargs) -> ServiceResult[EventAttendee]:
        """
        Add a host/co-organizer to an event.
        
        Args:
            event_id: Event ID
            host_user_id: User ID to make host (required in kwargs)
            role: 'organizer' or 'co_host'
            
        Security:
            - Requires authentication
            - Adder is determined from request_context
        """
        self.request_context.require_authentication()
        added_by_user_id = self.request_context.target_user_id
        
        try:
            host_user_id = kwargs.pop('host_user_id', None) or kwargs.pop('user_id', None)
            if not host_user_id:
                raise ValidationError("host_user_id is required")
            
            role = kwargs.get('role', 'co_host')
            if role not in ['organizer', 'co_host']:
                raise ValidationError(f"Invalid host role: {role}")

            # Check if already attendee
            result = self.get_attendee(event_id, host_user_id)
            
            if result.success:
                # Update existing attendee to host role
                attendee = result.data
                attendee.role = role
                attendee.rsvp_status = 'accepted'  # Hosts are auto-accepted
                attendee.updated_by_id = added_by_user_id
                attendee.prep_for_save()
                return self._save_model(attendee)
            else:
                # Create new host attendee
                return self.invite(
                    event_id=event_id,
                    invitee_user_id=host_user_id,
                    role=role,
                    rsvp_status='accepted'
                )

        except Exception as e:
            return self._handle_service_exception(e, 'add_host', event_id=event_id)

    def get_attendee(self, event_id: str, user_id: str, 
                    include_deleted: bool = False) -> ServiceResult[EventAttendee]:
        """Get a specific attendee record.
        
        Args:
            event_id: Event ID
            user_id: User ID
            include_deleted: If True, return deleted attendees as well
            
        Security:
            - Requires authentication
        """
        self.request_context.require_authentication()
        tenant_id = self.request_context.target_tenant_id
        try:
            # Use GSI1 to query by event, then filter by user_id
            # This is more efficient than scanning
            temp = EventAttendee()
            temp.event_id = event_id
            
            # Query by event using GSI1
            result = self._query_by_index(
                model=temp,
                index_name="gsi1",
                limit=100  # Should be small number per event
            )
            
            if not result.success:
                return result
            
            # Find the specific user's attendee record
            for attendee in result.data:
                if attendee.user_id == user_id and attendee.tenant_id == tenant_id:
                    # Return even if deleted if include_deleted is True
                    if not include_deleted and attendee.is_deleted():
                        return ServiceResult.error_result(f"Attendee not found", "NOT_FOUND")
                    return ServiceResult.success_result(attendee)
            
            return ServiceResult.error_result(f"Attendee not found", "NOT_FOUND")

        except Exception as e:
            return self._handle_service_exception(e, 'get_attendee', event_id=event_id, user_id=user_id)

    def list_by_event(self, event_id: str, 
                      rsvp_status: str = None, role: str = None,
                      limit: int = 100) -> ServiceResult[List[EventAttendee]]:
        """
        List all attendees for an event.
        
        Args:
            event_id: Event ID
            rsvp_status: Optional filter by RSVP status
            role: Optional filter by role
            limit: Max results
            
        Security:
            - Requires authentication
        """
        self.request_context.require_authentication()
        tenant_id = self.request_context.target_tenant_id
        try:
            temp = EventAttendee()
            temp.event_id = event_id
            # Leave role and rsvp_status as None to query across all values
            # (model defaults are now None, so GSI keys won't include them)
            if role:
                temp.role = role
            if rsvp_status:
                temp.rsvp_status = rsvp_status

            # Use helper method for query
            result = self._query_by_index(
                model=temp,
                index_name="gsi1",
                ascending=False,
                limit=limit
            )

            if not result.success:
                return result

            # Post-query filtering
            valid_attendees = []
            for attendee in result.data:
                # Tenant isolation and deleted check
                if attendee.tenant_id != tenant_id or attendee.is_deleted():
                    continue
                
                # Filter by RSVP status if specified (post-query for flexibility)
                if rsvp_status and attendee.rsvp_status != rsvp_status:
                    continue
                
                # Filter by role if specified (post-query for flexibility)
                if role and attendee.role != role:
                    continue
                
                valid_attendees.append(attendee)

            return ServiceResult.success_result(valid_attendees)

        except Exception as e:
            return self._handle_service_exception(e, 'list_by_event', event_id=event_id)

    def list_user_events(self, user_id: str,
                        rsvp_status: str = None, upcoming_only: bool = True,
                        limit: int = 50) -> ServiceResult[List[EventAttendee]]:
        """
        List events a user is attending/invited to.
        
        Args:
            user_id: User ID
            rsvp_status: Optional filter by RSVP status
            upcoming_only: Only future events
            limit: Max results
            
        Security:
            - Requires authentication
        """
        self.request_context.require_authentication()
        tenant_id = self.request_context.target_tenant_id
        try:
            temp = EventAttendee()
            temp.user_id = user_id
            # Leave rsvp_status as None to query across all values
            if rsvp_status:
                temp.rsvp_status = rsvp_status

            # Use helper method for query
            result = self._query_by_index(
                model=temp,
                index_name="gsi2",
                ascending=False,
                limit=limit
            )

            if not result.success:
                return result

            # Post-query filtering
            valid_attendees = []
            for attendee in result.data:
                # Tenant isolation and deleted check
                if attendee.tenant_id != tenant_id or attendee.is_deleted():
                    continue
                
                # Filter by RSVP status if specified
                if rsvp_status and attendee.rsvp_status != rsvp_status:
                    continue
                
                valid_attendees.append(attendee)

            return ServiceResult.success_result(valid_attendees)

        except Exception as e:
            return self._handle_service_exception(e, 'list_user_events', user_id=user_id)

    def list_hosts(self, event_id: str, limit: int = 20) -> ServiceResult[List[EventAttendee]]:
        """
        List all hosts (organizers and co-hosts) for an event.
        
        Args:
            event_id: Event ID
            limit: Max results
            
        Security:
            - Requires authentication
        """
        try:
            # Get organizers
            organizers = self.list_by_event(event_id, role="organizer", limit=limit)
            
            # Get co-hosts
            co_hosts = self.list_by_event(event_id, role="co_host", limit=limit)

            # Combine
            all_hosts = []
            if organizers.success:
                all_hosts.extend(organizers.data)
            if co_hosts.success:
                all_hosts.extend(co_hosts.data)

            return ServiceResult.success_result(all_hosts)

        except Exception as e:
            return self._handle_service_exception(e, 'list_hosts', event_id=event_id)

    def get_attendee_count(self, event_id: str,
                          rsvp_status: str = 'accepted') -> ServiceResult[int]:
        """
        Get count of attendees by RSVP status.
        
        Args:
            event_id: Event ID
            rsvp_status: RSVP status to count
            
        Security:
            - Requires authentication
        """
        try:
            result = self.list_by_event(event_id, rsvp_status=rsvp_status, limit=1000)
            if not result.success:
                return ServiceResult.error_result("Failed to count attendees", "COUNT_FAILED")

            count = len(result.data)
            
            # Add up +1 guests for accepted
            if rsvp_status == 'accepted':
                total_count = sum(a.total_attendee_count() for a in result.data)
                return ServiceResult.success_result(total_count)

            return ServiceResult.success_result(count)

        except Exception as e:
            return self._handle_service_exception(e, 'get_attendee_count', event_id=event_id)

    def _can_check_in_attendee(self, event: Event, checker_user_id: str, attendee_user_id: str) -> bool:
        """
        Check if checker_user_id has permission to check in attendee_user_id.
        
        Authorization Rules:
        1. Event owner can check-in anyone
        2. Event hosts (organizer, co_host) can check-in anyone
        3. Attendee can check themselves in
        4. Attendee can check in another attendee if they have can_check_in_others permission
        
        Args:
            event: Event model
            checker_user_id: User attempting to check in
            attendee_user_id: User being checked in
            
        Returns:
            bool: True if authorized, False otherwise
        """
        # Rule 1: Event owner
        if event.owner_id == checker_user_id:
            return True
        
        # Get checker's attendee record to check role and permissions
        checker_result = self.get_attendee(event.id, checker_user_id)
        
        if checker_result.success:
            checker_attendee = checker_result.data
            
            # Rule 2: Event hosts (organizer, co_host)
            if checker_attendee.is_host():
                return True
            
            # Rule 3: Self check-in
            if checker_user_id == attendee_user_id:
                return True
            
            # Rule 4: Has check-in permission for others
            if checker_attendee.can_check_in_others:
                return True
        
        return False

    @service_method("check_in")
    def check_in(self, event_id: str, attendee_user_id: str or None = None) -> ServiceResult[EventAttendee]:
        """
        Check in an attendee at the event.
        
        Args:
            event_id: Event ID
            attendee_user_id: Attendee user ID to check in (defaults to current user)
            
        Authorization Rules:
            1. Event owner can check-in anyone
            2. Event hosts can check-in anyone
            3. Attendee can check themselves in
            4. Attendee with can_check_in_others permission can check in anyone
            
        Security:
            - Requires authentication
            - Authorization checked via _can_check_in_attendee
        """
        self.request_context.require_authentication()
        checked_in_by_user_id = self.request_context.target_user_id
        attendee_user_id = attendee_user_id or checked_in_by_user_id
        
        try:
            # Get event to check ownership/permissions
            event = self._get_model_by_id(event_id, Event)
            if not event:
                raise NotFoundError(f"Event not found: {event_id}")
            
            # Get attendee being checked in
            result = self.get_attendee(event_id, attendee_user_id)
            if not result.success:
                raise NotFoundError(f"Attendee not found")

            attendee = result.data

            # Must be accepted to check in
            if not attendee.has_accepted():
                raise ValidationError("Only accepted attendees can check in")

            # Already checked in?
            if attendee.checked_in:
                return ServiceResult.error_result("Attendee already checked in", "ALREADY_CHECKED_IN")

            # AUTHORIZATION: Check if user has permission to check in this attendee
            if not self._can_check_in_attendee(event, checked_in_by_user_id, attendee_user_id):
                raise AccessDeniedError(
                    f"User {checked_in_by_user_id} does not have permission "
                    f"to check in attendee {attendee_user_id}"
                )

            # Perform check-in
            attendee.checked_in = True
            attendee.checked_in_at_utc_ts = dt.datetime.now(dt.UTC).timestamp()
            attendee.checked_in_by_user_id = checked_in_by_user_id
            attendee.updated_by_id = checked_in_by_user_id

            attendee.prep_for_save()
            return self._save_model(attendee)

        except Exception as e:
            return self._handle_service_exception(e, 'check_in', event_id=event_id, attendee_user_id=attendee_user_id)

    @service_method("grant_check_in_permission")
    def grant_check_in_permission(self, event_id: str, user_id: str) -> ServiceResult[EventAttendee]:
        """
        Grant an attendee permission to check in other attendees.
        
        Typically used for volunteers or staff helping with event check-ins.
        
        Args:
            event_id: Event ID
            user_id: User ID to grant permission to
            
        Security:
            - Requires authentication
            - Only event owner or hosts can grant this permission
        """
        self.request_context.require_authentication()
        granter_user_id = self.request_context.target_user_id
        
        try:
            # Get event to check ownership
            event = self._get_model_by_id(event_id, Event)
            if not event:
                raise NotFoundError(f"Event not found: {event_id}")
            
            # Check if granter has permission (must be owner or host)
            is_owner = event.owner_id == granter_user_id
            is_host = False
            
            if not is_owner:
                granter_result = self.get_attendee(event_id, granter_user_id)
                if granter_result.success:
                    is_host = granter_result.data.is_host()
            
            if not is_owner and not is_host:
                raise AccessDeniedError(
                    f"Only event owner or hosts can grant check-in permission"
                )
            
            # Get attendee to grant permission to
            result = self.get_attendee(event_id, user_id)
            if not result.success:
                raise NotFoundError(f"Attendee not found")
            
            attendee = result.data
            
            # Grant permission
            attendee.can_check_in_others = True
            attendee.updated_by_id = granter_user_id
            
            attendee.prep_for_save()
            return self._save_model(attendee)
            
        except Exception as e:
            return self._handle_service_exception(e, 'grant_check_in_permission', event_id=event_id, user_id=user_id)

    @service_method("promote_from_wait_list")


    def promote_from_wait_list(self, event_id: str, attendee_user_id: str or None = None) -> ServiceResult[EventAttendee]:
        """
        Promote an attendee from wait_list to accepted.
        
        Args:
            event_id: Event ID
            attendee_user_id: User ID on wait_list
            
        Security:
            - Requires authentication
            - Promoter is determined from request_context
        """
        self.request_context.require_authentication()
        promoted_by_user_id = self.request_context.target_user_id
        attendee_user_id = attendee_user_id or promoted_by_user_id
        try:
            # Get attendee
            result = self.get_attendee(event_id, attendee_user_id)
            if not result.success:
                raise NotFoundError(f"Attendee not found")

            attendee = result.data

            # Must be on wait_list
            if not attendee.is_on_wait_list():
                raise ValidationError("Attendee is not on wait_list")

            # Promote to accepted
            attendee.rsvp_status = 'accepted'
            attendee.responded_at_utc_ts = dt.datetime.now(dt.UTC).timestamp()
            attendee.updated_by_id = promoted_by_user_id

            attendee.prep_for_save()
            return self._save_model(attendee)

        except Exception as e:
            return self._handle_service_exception(e, 'promote_from_wait_list', event_id=event_id, attendee_user_id=attendee_user_id)

    @service_method("remove_attendee")
    def remove_attendee(self, event_id: str, user_id: str) -> ServiceResult[bool]:
        """
        Remove an attendee from an event (soft delete).
        
        Args:
            event_id: Event ID
            user_id: User ID to remove
            
        Security:
            - Requires authentication
        """
        self.request_context.require_authentication()
        removed_by_user_id = self.request_context.target_user_id
        try:
            # Get attendee
            result = self.get_attendee(event_id, user_id)
            if not result.success:
                raise NotFoundError(f"Attendee not found")

            attendee = result.data

            # Soft delete
            attendee.deleted_utc_ts = dt.datetime.now(dt.UTC).timestamp()
            attendee.deleted_by_id = removed_by_user_id
            attendee.updated_by_id = removed_by_user_id

            attendee.prep_for_save()
            save_result = self._save_model(attendee)
            
            return ServiceResult.success_result(save_result.success)

        except Exception as e:
            return self._handle_service_exception(e, 'remove_attendee', event_id=event_id, user_id=user_id)

    @service_method("bulk_invite")
    def bulk_invite(self, event_id: str, user_ids: List[str], **kwargs) -> ServiceResult[Dict[str, Any]]:
        """
        Invite multiple users to an event.
        
        Args:
            event_id: Event ID
            user_ids: List of user IDs to invite
            **kwargs: Additional fields applied to all invites
            
        Returns:
            Dict with 'invited_count', 'failed_count', 'successful', and 'failed' lists
            
        Security:
            - Requires authentication
            - Inviter is determined from request_context
        """
        self.request_context.require_authentication()
        
        try:
            successful = []
            failed = []

            for user_id in user_ids:
                result = self.invite(
                    event_id=event_id,
                    invitee_user_id=user_id,
                    **kwargs
                )

                if result.success:
                    successful.append({
                        'user_id': user_id,
                        'id': result.data.id
                    })
                else:
                    failed.append({
                        'user_id': user_id,
                        'error': result.error_message
                    })

            results = {
                'invited_count': len(successful),
                'failed_count': len(failed),
                'successful': successful,
                'failed': failed
            }

            return ServiceResult.success_result(results)

        except Exception as e:
            return self._handle_service_exception(e, 'bulk_invite', event_id=event_id)
