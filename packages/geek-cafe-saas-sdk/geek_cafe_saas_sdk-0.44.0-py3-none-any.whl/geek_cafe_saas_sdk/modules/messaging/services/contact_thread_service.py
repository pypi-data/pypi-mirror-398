"""
Geek Cafe, LLC
MIT License.  See Project Root for the license information.

ContactThreadService for managing contact threads and support tickets.
"""

from typing import Dict, Any, Optional, List
from boto3_assist.dynamodb.dynamodb import DynamoDB
from geek_cafe_saas_sdk.core.services.database_service import DatabaseService
from geek_cafe_saas_sdk.core.service_result import ServiceResult
from geek_cafe_saas_sdk.lambda_handlers._base.decorators import service_method
from geek_cafe_saas_sdk.core.service_errors import ValidationError, NotFoundError, AccessDeniedError
from geek_cafe_saas_sdk.modules.messaging.models import ContactThread
import datetime as dt


class ContactThreadService(DatabaseService[ContactThread]):
    """Service for ContactThread database operations."""
    

    def _user_has_cross_tenant_access(self, user_context: Optional[Dict[str, str]]) -> bool:
        """
        Determine if user has cross-tenant access to contact threads.
        
        Users with cross-tenant access can see threads from any tenant:
        - Platform admins (roles contains "platform_admin")
        - Support staff (roles contains "support_staff" or "support_admin")
        - General admins (roles contains "admin")
        
        Args:
            user_context: User context from JWT containing roles
            
        Returns:
            True if user has cross-tenant access, False otherwise
        """
        if not user_context:
            return False
        
        roles = user_context.get("roles", "")
        
        cross_tenant_roles = [
            "platform_admin",
            "support_admin", 
            "support_staff",
            "admin"
        ]
        
        # Check if user has any cross-tenant role
        for role in cross_tenant_roles:
            if role in roles:
                return True
        
        return False

    @service_method("create")
    def create(self, payload: Dict[str, Any]) -> ServiceResult[ContactThread]:
        """
        Create a new contact thread from a payload.
        
        Args:
            payload: Contact thread data including subject, sender, initial_message
            
        Returns:
            ServiceResult with ContactThread
            
        Security:
            - Requires authentication
        """
        # Validate authentication
        self.request_context.require_authentication()
        
        # Get targets (auto-extracted)
        tenant_id = self.request_context.target_tenant_id
        user_id = self.request_context.target_user_id
        
        try:
            # Validate required fields
            required_fields = ['subject', 'sender']
            self._validate_required_fields(payload, required_fields)

            # Validate sender has required fields
            sender = payload.get('sender', {})
            if not sender.get('id'):
                raise ValidationError("Sender must have an 'id' field")

            # Create and map thread instance from the payload
            thread = ContactThread().map(payload)
            thread.tenant_id = tenant_id
            thread.user_id = user_id
            thread.created_by_id = user_id

            # Set defaults
            if not thread.status:
                thread.status = "open"
            if not thread.priority:
                thread.priority = "medium"
            if not thread.inbox_id:
                thread.inbox_id = "support"

            # Add initial message if provided
            if 'initial_message' in payload and payload['initial_message']:
                initial_msg = {
                    "id": f"msg_{dt.datetime.now(dt.UTC).timestamp()}",
                    "content": payload['initial_message'],
                    "sender_id": sender.get('id'),
                    "sender_name": sender.get('name', 'Guest'),
                    "is_staff_reply": False,
                    "created_at": dt.datetime.now(dt.UTC).timestamp()
                }
                thread.add_message(initial_msg)

            # Prepare for save (sets ID and timestamps)
            thread.prep_for_save()

            # Save to database
            return self._save_model(thread)

        except Exception as e:
            return self._handle_service_exception(e, 'create_contact_thread')

    @service_method("get_by_id")
    def get_by_id(self, thread_id: str, 
                  user_inboxes: List[str] = None) -> ServiceResult[ContactThread]:
        """
        Get contact thread by ID with access control.
        
        Args:
            thread_id: Thread ID
            user_inboxes: List of inbox IDs the user has access to
            
        Returns:
            ServiceResult with ContactThread
            
        Security:
            - Requires authentication
            - Validates tenant access
            - Validates inbox access
        """
        user_id = self.request_context.authenticated_user_id
        
        try:
            # Security is automatic via _get_by_id
            thread = self._get_by_id(thread_id, ContactThread)
            if not thread:
                raise NotFoundError(f"Contact thread with ID {thread_id} not found")

            # Check if user can access this thread
            if not thread.can_user_access(user_id, user_inboxes or []):
                raise AccessDeniedError("Access denied to this contact thread")

            return ServiceResult.success_result(thread)

        except Exception as e:
            return self._handle_service_exception(e, 'get_contact_thread', thread_id=thread_id)

    def list_by_inbox_and_status(self, inbox_id: str, status: str, 
                                  priority: str = None, limit: int = 50) -> ServiceResult[List[ContactThread]]:
        """
        List contact threads by inbox and status using GSI1.
        
        Supports role-based access control:
        - Admins/support staff see ALL threads in the inbox (cross-tenant access)
        - Regular users only see threads from their own tenant
        
        Args:
            inbox_id: Inbox ID (support, sales, etc.)
            status: Status filter (open, in_progress, resolved, closed)
            priority: Optional priority filter
            limit: Maximum number of results
            
        Returns:
            ServiceResult with list of ContactThreads
        """
        try:
            tenant_id = self.request_context.target_tenant_id
            
            # Create a temporary thread instance to get the GSI key
            temp_thread = ContactThread()
            temp_thread.inbox_id = inbox_id
            temp_thread.status = status
            if priority:
                temp_thread.priority = priority

            # Query by GSI1 (inbox + status), sorted by priority and timestamp
            result = self._query_by_index(
                temp_thread,
                "gsi1",
                ascending=False,  # Most recent first
                limit=limit
            )

            if not result.success:
                return result

            # Apply role-based filtering
            # For now, regular users only see their tenant's threads
            # TODO: Implement proper role checking using request_context
            active_threads = [
                t for t in result.data 
                if not t.is_deleted() and t.tenant_id == tenant_id
            ]

            return ServiceResult.success_result(active_threads)

        except Exception as e:
            return self._handle_service_exception(e, 'list_by_inbox_and_status',
                                                inbox_id=inbox_id, status=status)

    def list_by_tenant_and_status(self, status: str, 
                                   limit: int = 50) -> ServiceResult[List[ContactThread]]:
        """
        List contact threads by tenant and status using GSI2.
        
        Args:
            status: Status filter
            limit: Maximum number of results
            
        Returns:
            ServiceResult with list of ContactThreads
        """
        try:
            tenant_id = self.request_context.target_tenant_id
            
            temp_thread = ContactThread()
            temp_thread.tenant_id = tenant_id
            temp_thread.status = status

            result = self._query_by_index(
                temp_thread,
                "gsi2",
                ascending=False,
                limit=limit
            )

            if not result.success:
                return result

            # Filter out deleted threads
            active_threads = [t for t in result.data if not t.is_deleted()]
            return ServiceResult.success_result(active_threads)

        except Exception as e:
            return self._handle_service_exception(e, 'list_by_tenant_and_status',
                                                tenant_id=tenant_id, status=status)

    def list_by_assigned_user(self, assigned_to: str, 
                              *, status: str = None, priority: str = None, limit: int = 50) -> ServiceResult[List[ContactThread]]:
        """
        List contact threads assigned to a specific user using GSI3.
        
        Args:
            assigned_to: Staff user ID
            status: Optional status filter
            limit: Maximum number of results
            
        Returns:
            ServiceResult with list of ContactThreads
        """
        try:
            tenant_id = self.request_context.target_tenant_id
            
            temp_thread = ContactThread()
            temp_thread.assigned_to = assigned_to
            if status:
                temp_thread.status = status
            else:
                temp_thread.status = None
            
            if priority:
                temp_thread.priority = priority
            else:
                temp_thread.priority = None

            result = self._query_by_index(
                temp_thread,
                "gsi3",
                ascending=False,
                limit=limit
            )

            if not result.success:
                return result

            # Filter by tenant and exclude deleted threads
            active_threads = [
                t for t in result.data 
                if not t.is_deleted() and t.tenant_id == tenant_id
            ]

            return ServiceResult.success_result(active_threads)

        except Exception as e:
            return self._handle_service_exception(e, 'list_by_assigned_user',
                                                assigned_to=assigned_to, tenant_id=tenant_id)

    def list_by_sender_email(self, sender_email: str, 
                             limit: int = 50) -> ServiceResult[List[ContactThread]]:
        """
        List all contact threads from a specific sender email using GSI5.
        
        Args:
            sender_email: Sender's email address
            limit: Maximum number of results
            
        Returns:
            ServiceResult with list of ContactThreads
        """
        try:
            tenant_id = self.request_context.target_tenant_id
            
            temp_thread = ContactThread()
            temp_thread.sender = {"email": sender_email}

            result = self._query_by_index(
                temp_thread,
                "gsi5",
                ascending=False,
                limit=limit
            )

            if not result.success:
                return result

            # Filter by tenant and exclude deleted threads
            active_threads = [
                t for t in result.data 
                if not t.is_deleted() and t.tenant_id == tenant_id
            ]

            return ServiceResult.success_result(active_threads)

        except Exception as e:
            return self._handle_service_exception(e, 'list_by_sender_email',
                                                sender_email=sender_email, tenant_id=tenant_id)

    @service_method("add_message")
    def add_message(self, thread_id: str, 
                    message_data: Dict[str, Any], user_inboxes: List[str] = None) -> ServiceResult[ContactThread]:
        """
        Add a message to an existing contact thread.
        
        Args:
            thread_id: Thread ID
            message_data: Message data including content, sender_name, is_staff_reply
            user_inboxes: List of inbox IDs the user has access to
            
        Returns:
            ServiceResult with updated ContactThread
            
        Security:
            - Requires authentication
        """
        self.request_context.require_authentication()
        user_id = self.request_context.target_user_id
        try:
            # Get the thread
            thread_result = self.get_by_id(thread_id, user_inboxes)
            if not thread_result.success:
                return thread_result

            thread = thread_result.data

            # Create the message
            message = {
                "id": message_data.get("id", f"msg_{dt.datetime.now(dt.UTC).timestamp()}"),
                "content": message_data.get("content", ""),
                "sender_id": user_id,
                "sender_name": message_data.get("sender_name", ""),
                "is_staff_reply": message_data.get("is_staff_reply", False),
                "created_at": dt.datetime.now(dt.UTC).timestamp()
            }

            thread.add_message(message)

            # Update metadata
            thread.updated_by_id = user_id
            thread.prep_for_save()

            # Save the updated thread
            return self._save_model(thread)

        except Exception as e:
            return self._handle_service_exception(e, 'add_message_to_contact_thread',
                                                thread_id=thread_id)

    @service_method("assign_thread")
    def assign_thread(self, thread_id: str,
                      assigned_to: str, user_inboxes: List[str] = None) -> ServiceResult[ContactThread]:
        """
        Assign a contact thread to a staff member.
        
        Args:
            thread_id: Thread ID
            assigned_to: Staff user ID to assign to
            user_inboxes: List of inbox IDs the user has access to
            
        Returns:
            ServiceResult with updated ContactThread
            
        Security:
            - Requires authentication
        """
        self.request_context.require_authentication()
        user_id = self.request_context.target_user_id
        try:
            thread_result = self.get_by_id(thread_id, user_inboxes)
            if not thread_result.success:
                return thread_result

            thread = thread_result.data
            thread.assign(assigned_to)
            thread.updated_by_id = user_id
            thread.prep_for_save()

            return self._save_model(thread)

        except Exception as e:
            return self._handle_service_exception(e, 'assign_contact_thread',
                                                thread_id=thread_id, assigned_to=assigned_to)

    @service_method("update_status")
    def update_status(self, thread_id: str,
                      status: str, user_inboxes: List[str] = None) -> ServiceResult[ContactThread]:
        """
        Update the status of a contact thread.
        
        Args:
            thread_id: Thread ID
            status: New status (open, in_progress, resolved, closed)
            user_inboxes: List of inbox IDs the user has access to
            
        Returns:
            ServiceResult with updated ContactThread
            
        Security:
            - Requires authentication
        """
        self.request_context.require_authentication()
        user_id = self.request_context.target_user_id
        try:
            thread_result = self.get_by_id(thread_id, user_inboxes)
            if not thread_result.success:
                return thread_result

            thread = thread_result.data
            thread.status = status
            thread.updated_by_id = user_id
            thread.prep_for_save()

            return self._save_model(thread)

        except Exception as e:
            return self._handle_service_exception(e, 'update_contact_thread_status',
                                                thread_id=thread_id, status=status)

    @service_method("update")
    def update(self, thread_id: str,
               updates: Dict[str, Any], user_inboxes: List[str] = None) -> ServiceResult[ContactThread]:
        """
        Update contact thread with access control.
        
        Args:
            thread_id: Thread ID
            updates: Dictionary of fields to update
            user_inboxes: List of inbox IDs the user has access to
            
        Returns:
            ServiceResult with updated ContactThread
            
        Security:
            - Requires authentication
        """
        user_id = self.request_context.authenticated_user_id
        try:
            # Get existing thread with security check
            thread = self._get_by_id(thread_id, ContactThread)
            if not thread:
                raise NotFoundError(f"Contact thread with ID {thread_id} not found")

            # Check permissions
            if not thread.can_user_access(user_id, user_inboxes or []):
                raise AccessDeniedError("Access denied: insufficient permissions")

            old_thread = self._fetch_model_raw(thread_id, ContactThread)

            # Apply updates (limited fields)
            allowed_fields = ['subject', 'status', 'priority', 'assigned_to', 'tags', 'inbox_id']
            for field, value in updates.items():
                if field in allowed_fields and hasattr(thread, field):
                    setattr(thread, field, value)

            thread.updated_by_id = user_id
            thread.prep_for_save()

            return self._save_model(thread, old_model=old_thread)

        except Exception as e:
            return self._handle_service_exception(e, 'update_contact_thread', thread_id=thread_id)

    @service_method("delete")
    def delete(self, thread_id: str,
               user_inboxes: List[str] = None) -> ServiceResult[bool]:
        """
        Soft delete contact thread with access control.
        
        Args:
            thread_id: Thread ID
            user_inboxes: List of inbox IDs the user has access to
            
        Returns:
            ServiceResult with boolean success
            
        Security:
            - Requires authentication
        """
        user_id = self.request_context.authenticated_user_id
        try:
            # Get existing thread with security check
            thread = self._get_by_id(thread_id, ContactThread)
            if not thread:
                raise NotFoundError(f"Contact thread with ID {thread_id} not found")

            # Check if already deleted
            if thread.is_deleted():
                return ServiceResult.success_result(True)

            # Check permissions
            if not thread.can_user_access(user_id, user_inboxes or []):
                raise AccessDeniedError("Access denied: insufficient permissions")

            # Soft delete: set deleted timestamp and metadata
            thread.deleted_utc_ts = dt.datetime.now(dt.UTC).timestamp()
            thread.deleted_by_id = user_id
            thread.prep_for_save()

            # Save the updated thread
            save_result = self._save_model(thread)
            if save_result.success:
                return ServiceResult.success_result(True)
            else:
                return save_result

        except Exception as e:
            return self._handle_service_exception(e, 'delete_contact_thread', thread_id=thread_id)

    def _handle_service_exception(self, exception: Exception, operation: str, **context) -> ServiceResult:
        """
        Handle service exceptions with consistent error responses.
        
        Delegates to parent class for proper error code mapping.
        
        Args:
            exception: The exception that occurred
            operation: Name of the operation that failed
            **context: Additional context for debugging
            
        Returns:
            ServiceResult with error details
        """
        # Use parent's exception handler for proper error code mapping
        return super()._handle_service_exception(exception, operation, **context)
